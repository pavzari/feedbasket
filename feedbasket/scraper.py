import asyncio
import logging
from datetime import datetime
from time import mktime

import aiosql
import feedparser
from aiohttp import ClientConnectorError, ClientResponseError, ClientSession
from asyncpg import Pool
from pydantic import BaseModel, validator

from feedbasket import config

log = logging.getLogger(__name__)


class Feed(BaseModel):
    feed_id: int
    feed_url: str
    feed_name: str | None
    created_at: datetime
    updated_at: datetime
    last_fetched: datetime | None
    feed_type: str | None
    feed_tags: list[str] | None  # separate table?
    icon_url: str | None
    etag_header: str | None
    modified_header: str | None


class FeedEntry(BaseModel):
    title: str
    link: str
    description: str
    published_date: datetime | None

    @validator("published_date", pre=True, always=True)
    def parse_published_date(cls, value):
        try:
            return datetime.fromtimestamp(mktime(value))
        except (ValueError, TypeError):
            log.info("Could not parse date")


class FeedScraper:
    def __init__(self, pool: Pool, queries: aiosql.from_path):
        self._pool = pool
        self._queries = queries
        log.info("Feed scraper initialized.")

    async def _update_feed(self, entries: list[FeedEntry], url) -> None:
        log.info(f"Updating feed: {url}")
        async with self._pool.acquire() as conn:
            for entry in entries:
                await self._queries.insert_entry(
                    conn,
                    title=entry.title,
                    link=entry.link,
                    description=entry.description,
                    published_date=entry.published_date,  # unpacking ? **
                )
        log.info(f"Updated feed: {url}")

    def _parse_feed(self, feed_data: feedparser.FeedParserDict) -> list[FeedEntry]:
        entries = []
        for entry in feed_data.entries:
            entries.append(
                FeedEntry(
                    title=entry.get("title", ""),
                    link=entry.get("link", ""),
                    description=entry.get("description", ""),
                    published_date=entry.get("published_parsed", " "),
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

                feed_data = feedparser.parse(await response.text())
                log.info("Fetched XML: %s", feed.feed_url)
                entries = self._parse_feed(feed_data)
                await self._update_feed(entries, feed.feed_url)

                etag_header = response.headers.get("ETag")
                modified_header = response.headers.get("Last-Modified")
                last_fetched = datetime.now()

                await self._update_feed_metadata(
                    feed.feed_url, etag_header, modified_header, last_fetched
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

        async with ClientSession() as session:
            tasks = [self._fetch_feed(session, feed) for feed in feeds]
            await asyncio.gather(*tasks)
