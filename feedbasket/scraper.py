import asyncio
import logging
import time
from datetime import datetime
from typing import Optional

import aiosql
import feedparser
from aiohttp import ClientConnectorError, ClientResponseError, ClientSession
from asyncpg import Pool
from pydantic import BaseModel, validator

from feedbasket import config
from feedbasket.decorators import RetryLimitError, retry
from feedbasket.readability import extract_content_readability

import threading

log = logging.getLogger(__name__)


class Feed(BaseModel):
    feed_id: int
    feed_url: str
    feed_name: str | None
    last_updated: datetime | None
    feed_type: str | None
    feed_tags: list[str] | None
    icon_url: str | None
    etag_header: str | None
    last_modified_header: str | None
    parsing_error_count: int
    created_at: datetime


class FeedEntry(BaseModel):
    entry_id: Optional[int] = None
    entry_title: str
    entry_url: str
    author: str | None
    description: str | None
    summary: str | None
    content: str | None
    published_date: datetime | None
    updated_date: datetime | None
    cleaned_content: Optional[str] = None
    # created_at: datetime

    @staticmethod
    def parse_date(value):
        try:
            return datetime.fromtimestamp(time.mktime(value))
        except (ValueError, TypeError):
            log.info("Could not parse date.")
            return None

    @validator("published_date", pre=True, always=True)
    def parse_published_date(cls, value):
        return cls.parse_date(value)

    @validator("updated_date", pre=True, always=True)
    def parse_updated_date(cls, value):
        return cls.parse_date(value)


class FeedScraper:
    def __init__(self, pool: Pool, queries: aiosql.from_path):
        self._pool = pool
        self._queries = queries
        log.info("Feed scraper initialized.")

    async def _update_feed(
        self, entries: list[FeedEntry], feed_url: str, feed_id: int
    ) -> None:
        log.info(f"Updating feed: {feed_url}")
        async with self._pool.acquire() as conn:
            for entry in entries:
                await self._queries.insert_entry(
                    conn,
                    feed_id=feed_id,
                    entry_title=entry.entry_title,
                    entry_url=entry.entry_url,
                    author=entry.author,
                    summary=entry.summary,
                    content=entry.content,
                    description=entry.description,
                    cleaned_content=entry.cleaned_content,
                    published_date=entry.published_date,
                    updated_date=entry.updated_date,
                )
        log.info(f"Updated feed: {feed_url}")

    async def _update_feed_metadata(
        self,
        feed_url: str,
        etag_header: str,
        last_modified_header: str,
        last_updated: datetime,
    ) -> None:
        log.info(f"Updating feed metadata: {feed_url}")
        async with self._pool.acquire() as conn:
            await self._queries.update_feed_meta(
                conn,
                feed_url=feed_url,
                etag_header=etag_header,
                last_modified_header=last_modified_header,
                last_updated=last_updated,
            )

    async def _update_feed_error_count(self, feed_id: int) -> None:
        async with self._pool.acquire() as conn:
            await self._queries.update_feed_error_count(conn, feed_id=feed_id)

    def _parse_feed(self, feed_xml: str, last_updated: datetime) -> list[FeedEntry]:
        feed_data = feedparser.parse(feed_xml)
        entries = []

        for entry in feed_data.entries:
            try:
                published = entry.get("published_parsed", entry.get("updated_parsed"))
                published_datetime = datetime.fromtimestamp(time.mktime(published))
            except (ValueError, TypeError):
                log.debug("Skipping entry: invalid publication date.")
                continue

            # skip if last_updated is not None and published before last fetch
            if last_updated is not None and published_datetime < last_updated:
                log.debug("Skipping duplicate entry.")
                continue

            # cleaned_content = await extract_content_readability(entry.get("link"))
            cleaned_content = None

            entries.append(
                FeedEntry(
                    entry_title=entry.get("title"),
                    entry_url=entry.get("link"),
                    author=entry.get("author"),
                    published_date=published,
                    updated_date=entry.get("updated_parsed"),
                    cleaned_content=cleaned_content,
                    description=entry.get("description"),
                    summary=entry.get("summary"),
                    content=(
                        entry.get("content")[0].get("value")
                        if entry.get("content")
                        else None
                    ),
                ),
            )
        return entries

    @retry(ClientResponseError, ClientConnectorError, asyncio.TimeoutError)
    async def _fetch_feed(
        self, session: ClientSession, feed: Feed
    ) -> Optional[tuple] | None:
        log.info(f"Attempting to fetch: {feed.feed_url}")

        headers = {"User-Agent": config.USER_AGENT}

        if feed.etag_header:
            headers["If-None-Match"] = feed.etag_header
        if feed.last_modified_header:
            headers["If-Modified-Since"] = feed.last_modified_header

        async with session.get(
            feed.feed_url,
            raise_for_status=True,
            timeout=config.GET_TIMEOUT,
            headers=headers,
        ) as response:

            if response.status == 304:
                log.info(f"No updates to: {feed.feed_url}")
                return

            etag_header = response.headers.get("ETag")
            last_modified_header = response.headers.get("Last-Modified")
            feed_xml = await response.text()

            return feed_xml, etag_header, last_modified_header

    async def _scrape_feed(self, session: ClientSession, feed: Feed) -> None:
        try:
            feed_data = await self._fetch_feed(session, feed)
            if not feed_data:
                return
            feed_xml, etag_header, last_modified_header = feed_data
        except RetryLimitError:
            log.error(f"Could not fetch feed: {feed.feed_url}")
            await self._update_feed_error_count(feed.feed_id)
            return

        log.debug(f"Parsing feed: {feed.feed_url}")
        loop = asyncio.get_event_loop()
        entries = await loop.run_in_executor(
            None, self._parse_feed, feed_xml, feed.last_updated
        )
        # entries = self._parse_feed(feed_xml, feed.last_updated)
        # what if entries is empty? Do we want to update feed and metadata?
        if not entries:
            return

        await self._update_feed(entries, feed.feed_url, feed.feed_id)
        await self._update_feed_metadata(
            feed.feed_url,
            etag_header,
            last_modified_header,
            last_updated=datetime.now(),
        )
        # asyncio.create_task(self._update_feed(entries, feed.feed_url, feed.feed_id))
        # asyncio.create_task(
        #     self._update_feed_metadata(
        #         feed.feed_url,
        #         etag_header,
        #         last_modified_header,
        #         last_updated=datetime.now(),
        #     )
        # )

    async def run_scraper(self) -> None:
        async with self._pool.acquire() as conn:
            feeds = [Feed(**feed) for feed in await self._queries.get_feeds(conn)]

        if not feeds:
            log.info("No feeds to scrape.")
            return

        start_time = time.monotonic()
        async with ClientSession() as session:
            tasks = [self._scrape_feed(session, feed) for feed in feeds]
            await asyncio.gather(*tasks)
        print("time: ", time.monotonic() - start_time)
