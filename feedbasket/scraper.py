import asyncio
import logging
import time
from datetime import datetime
from time import mktime

from typing import Optional

import aiosql
import feedparser
from aiohttp import ClientConnectorError, ClientResponseError, ClientSession
from asyncpg import Pool
from pydantic import BaseModel, validator

from feedbasket import config
from feedbasket.readability import extract_content_readability

log = logging.getLogger(__name__)


class Feed(BaseModel):
    feed_id: int
    feed_url: str
    feed_name: str | None
    last_fetched: datetime | None
    feed_type: str | None
    feed_tags: list[str] | None  # separate table?
    icon_url: str | None
    etag_header: str | None
    modified_header: str | None
    created_at: datetime
    updated_at: datetime


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
    cleaned_content: str | None
    # created_at: datetime
    # updated_at: datetime

    @staticmethod
    def parse_date(value):
        try:
            return datetime.fromtimestamp(mktime(value))
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
                    entry_title=entry.entry_title,
                    entry_url=entry.entry_url,
                    author=entry.author,
                    description=entry.description,
                    summary=entry.summary,
                    content=entry.content,
                    cleaned_content=entry.cleaned_content,
                    published_date=entry.published_date,
                    updated_date=entry.updated_date,
                    feed_id=feed_id,
                    # unpacking ? **
                )
        log.info(f"Updated feed: {feed_url}")

    async def _parse_feed(self, feed_xml: str) -> list[FeedEntry]:
        feed_data = feedparser.parse(feed_xml)
        entries = []
        for entry in feed_data.entries:

            # call readability on link
            # entry_url = entry.get("link")
            # cleaned_content = await extract_content_readability(entry_url)

            entry_url = entry.get("link")
            loop = asyncio.get_running_loop()
            cleaned_content = await loop.run_in_executor(
                None, extract_content_readability, entry_url
            )

            cleaned_content = None
            entries.append(
                FeedEntry(
                    entry_title=entry.get("title"),
                    entry_url=entry.get("link"),
                    author=entry.get("author"),
                    published_date=entry.get(
                        "published_parsed", entry.get("updated_parsed")
                    ),
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

    async def _fetch_feed(self, session: ClientSession, feed: Feed) -> None:
        log.info("Attempting to fetch: %s", feed.feed_url)

        headers = {"User-Agent": config.USER_AGENT}

        if feed.etag_header:
            headers["If-None-Match"] = feed.etag_header
        if feed.modified_header:
            headers["If-Modified-Since"] = feed.modified_header

        try:
            async with session.get(
                feed.feed_url,
                raise_for_status=True,
                timeout=config.GET_TIMEOUT,
                headers=headers,
            ) as response:

                if response.status == 304:
                    log.info("No updates to: %s", feed.feed_url)
                    return

                etag_header = response.headers.get("ETag")
                modified_header = response.headers.get("Last-Modified")
                feed_xml = await response.text()
                log.info("Fetched XML: %s", feed.feed_url)

                entries = await self._parse_feed(feed_xml)
                # loop = asyncio.get_event_loop()
                # entries = await loop.run_in_executor(None, self._parse_feed, feed_xml)

                await self._update_feed(entries, feed.feed_url, feed.feed_id)

                await self._update_feed_metadata(
                    feed.feed_url,
                    etag_header,
                    modified_header,
                    last_fetched=datetime.now(),
                )

        except (ClientResponseError, ClientConnectorError, asyncio.TimeoutError):
            log.error("Could not fetch feed: %s", feed.feed_url)

    async def _update_feed_metadata(
        self, feed_url, etag_header, modified_header, last_fetched
    ) -> None:
        log.info("Updating feed metadata: %s", feed_url)
        async with self._pool.acquire() as conn:
            await self._queries.update_feed_meta(
                conn,
                feed_url=feed_url,
                etag_header=etag_header,
                modified_header=modified_header,
                last_fetched=last_fetched,
            )

    async def run_scraper(self) -> None:
        async with self._pool.acquire() as conn:
            feeds = [Feed(**feed) for feed in await self._queries.get_feeds(conn)]

        if not feeds:
            log.info("No feeds found.")
            return

        start_time = time.monotonic()
        async with ClientSession() as session:
            tasks = [self._fetch_feed(session, feed) for feed in feeds]
            await asyncio.gather(*tasks)
            print("time: ", time.monotonic() - start_time)
