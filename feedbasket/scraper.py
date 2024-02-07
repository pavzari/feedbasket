import asyncio
import logging
from datetime import datetime
from time import mktime
from typing import Optional

import aiosql
import feedparser
from aiohttp import ClientConnectorError, ClientResponseError, ClientSession
from asyncpg import Pool
from pydantic import BaseModel, HttpUrl, validator

from feedbasket.config import GET_TIMEOUT, USER_AGENT


log = logging.getLogger(__name__)


class Feed(BaseModel):
    feed_id: int
    feed_url: str
    feed_name: Optional[str]
    created_at: datetime
    updated_at: datetime
    last_fetched: Optional[datetime]
    feed_type: Optional[str]
    feed_tags: Optional[list[str]]
    icon_url: Optional[str]
    etag: Optional[str]
    modified_header: Optional[str]  # Optional vs None?


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

    async def _insert_into_db(self, entries: list[FeedEntry], url):
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

    async def _fetch_and_insert(self, session: ClientSession, feed: Feed):
        # print(feed)
        log.info("Attempting to fetch: %s", feed.feed_url)

        headers = {"User-Agent": USER_AGENT}

        if feed.etag:
            headers["If-None-Match"] = feed.etag
        if feed.modified_header:
            headers["If-Modified-Since"] = feed.modified_header

        #  print(headers)

        try:
            async with session.get(
                feed.feed_url,
                raise_for_status=True,
                timeout=GET_TIMEOUT,
                headers=headers,
            ) as response:

                if response.status == 304:
                    log.info("No updates to: %s", feed.feed_url)
                    return

                feed_data = feedparser.parse(await response.text())
                log.info("Fetched XML: %s", feed.feed_url)
                entries = self._parse_feed(feed_data)
                await self._insert_into_db(entries, feed.feed_url)  # rename function.

                etag = response.headers.get("ETag")
                modified_header = response.headers.get("Last-Modified")
                last_fetched = datetime.now()

                async with self._pool.acquire() as conn:
                    await self._queries.update_feed_info(
                        conn,
                        feed_url=feed.feed_url,
                        etag=etag,
                        modified_header=modified_header,
                        last_fetched=last_fetched,
                    )

        except (ClientResponseError, ClientConnectorError, asyncio.TimeoutError):
            log.error("Could not fetch feed: %s", feed.feed_url)

    # async def _update_feed_info_in_db(self, url, headers):
    #     async with self._pool.acquire() as conn:
    #         await self._queries.update_feed_info(conn, url, headers)

    async def run_scraper(self):

        async with self._pool.acquire() as conn:
            feeds = [Feed(**feed) for feed in await self._queries.get_feeds(conn)]

        if not feeds:
            log.info("No feeds found.")

        async with ClientSession() as session:
            tasks = [self._fetch_and_insert(session, feed) for feed in feeds]
            await asyncio.gather(*tasks)


# if __name__ == "__main__":
#     start_time = time.time()
#     scraper = FeedScraper(DB_URL)
#     asyncio.run(scraper.run_scraper())
#     print("--- %s seconds ---" % (time.time() - start_time))
