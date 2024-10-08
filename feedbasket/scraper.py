from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import TYPE_CHECKING

import feedparser
from aiohttp import ClientConnectorError, ClientResponseError, ClientSession

from feedbasket import config
from feedbasket.decorators import RetryLimitError, retry
from feedbasket.models import Feed, NewFeedEntry

if TYPE_CHECKING:
    from aiosql.queries import Queries
    from asyncpg import Connection, Pool


# from feedbasket.readability import extract_content_readability


log = logging.getLogger(__name__)


class FeedScraper:
    def __init__(self, pool: Pool, queries: Queries):
        self._pool = pool
        self._queries = queries
        log.info("Feed scraper initialized.")

    async def _update_feed(
        self, entries: list[NewFeedEntry], feed_url: str, feed_id: int
    ) -> None:
        log.info(f"Updating feed: {feed_url}")
        async with self._pool.acquire() as conn:
            for entry in entries:
                await self._queries.insert_entry(
                    conn,
                    feed_id=feed_id,
                    **entry.model_dump(),
                )
        log.debug(f"Updated feed: {feed_url}")

    async def _update_feed_metadata(
        self,
        feed_url: str,
        etag_header: str,
        last_modified_header: str,
        last_updated: datetime | None,
    ) -> None:
        log.debug(f"Updating feed metadata: {feed_url}")
        async with self._pool.acquire() as conn:
            await self._queries.update_feed_meta(
                conn,
                feed_url=feed_url,
                etag_header=etag_header,
                last_modified_header=last_modified_header,
                last_updated=last_updated,
                parsing_error_count=0,  # reset parsing error count
            )

    async def _update_feed_error_count(self, feed_id: int) -> None:
        async with self._pool.acquire() as conn:
            await self._queries.update_feed_error_count(conn, feed_id=feed_id)

    def _parse_feed(
        self, feed_xml: str, last_updated: datetime | None
    ) -> list[NewFeedEntry]:
        feed_data = feedparser.parse(feed_xml)
        current_datetime_utc = datetime.now(UTC)

        # Some feeds have incorrect published date that does not match the lastest entry date.
        # Can't use it to skip parsing the entries if server also ignores the etag and last-modified headers.

        # if feed_published := feed_data.feed.get("updated_parsed"):
        #     feed_published_datetime = datetime.fromtimestamp(
        #         time.mktime(feed_published)
        #     )
        #     if last_updated and feed_published_datetime < last_updated:
        #         log.debug(f"Skipping feed: no new entries. {feed_data.feed.link}")
        #         return

        #     if (
        #         current_datetime_utc - feed_published_datetime
        #     ).days > config.SKIP_OLDER_THAN_DAYS:
        #         log.debug(f"Skipping feed: too old., {feed_data.feed.link}")
        #         return

        entries = []
        for entry in feed_data.entries:
            try:
                published = entry.get("published_parsed", entry.get("updated_parsed"))
                published_datetime = datetime.fromtimestamp(time.mktime(published), UTC)
            except (ValueError, TypeError):
                log.debug("Skipping entry: invalid/no publication date.")
                continue

            age_in_days = (current_datetime_utc - published_datetime).days
            if age_in_days > config.SKIP_OLDER_THAN_DAYS:
                log.debug(
                    f"Skipping entry: older than {config.SKIP_OLDER_THAN_DAYS} days."
                )
                continue

            # Skip if last_updated is not None and published before last fetch: for feeds that ignore etag/last_modified
            if last_updated and published_datetime < last_updated:
                log.debug("Skipping entry: duplicate.")
                continue

            # cleaned_content = await extract_content_readability(entry.get("link"))
            cleaned_content = None

            entries.append(
                NewFeedEntry(
                    entry_title=entry.get("title"),
                    entry_url=entry.get("link"),
                    author=entry.get("author"),
                    published_date=published_datetime,
                    updated_date=entry.get("updated_parsed"),
                    cleaned_content=cleaned_content,
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
    async def _fetch_feed(self, session: ClientSession, feed: Feed) -> tuple | None:
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

        loop = asyncio.get_running_loop()
        entries = await loop.run_in_executor(
            None, self._parse_feed, feed_xml, feed.last_updated
        )

        last_updated = feed.last_updated
        if entries:
            await self._update_feed(entries, feed.feed_url, feed.feed_id)
            last_updated = datetime.now(UTC)

        # Update etag/last-modified to prevent parsing the feed again. Last_updated unchanged if no entries.
        await self._update_feed_metadata(
            feed.feed_url,
            etag_header,
            last_modified_header,
            last_updated,
        )

    async def _get_all_feeds(self, conn: Connection) -> AsyncIterator[Feed]:
        # Append _cursor to query name to access cursor object.
        async with self._queries.get_all_feeds_cursor(conn) as cursor:
            async for feed in cursor:
                yield Feed(**feed)

    async def run(self, url: str | None = None) -> None:
        start = time.perf_counter()
        count = 0

        async with self._pool.acquire() as conn:
            async with ClientSession() as session:
                if url:
                    feed = Feed(**await self._queries.get_feed_by_url(conn, url))
                    count = 1
                    await self._scrape_feed(session, feed)
                else:
                    async for feed in self._get_all_feeds(conn):
                        count += 1
                        await self._scrape_feed(session, feed)

        log.info(f"Scraping time: {time.perf_counter() - start}, Feed count: {count}")
