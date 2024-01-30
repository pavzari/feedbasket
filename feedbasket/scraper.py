import asyncio
import logging
import time

import aiosql
import asyncpg
import feedparser
from aiohttp import ClientConnectorError, ClientResponseError, ClientSession

DEFAULT_FEEDS = [
    "https://feeds.arstechnica.com/arstechnica/features.xml",
    "https://pluralistic.net/feed/",
    "https://www.theatlantic.com/feed/best-of/",
    "https://www.quantamagazine.org/feed",
    "https://www.reddit.com/r/python/top.rss",
    "https://lobste.rs/top/rss",
    "https://hnrss.org/best",
    "https://en.wikipedia.org/w/api.php?action=featuredfeed&feed=featured&feedformat=atom",
    "https://www.openculture.com/feed/rss2",
    "https://publicdomainreview.org/rss.xml",
    "https://www.eff.org/rss/updates.xml",
    "https://www.theverge.com/features/rss/index.xml",
    "https://www.bbc.com/culture/feed.rss",
    "https://blog.opensource.org/feed/",
    "https://www.technologyreview.com/feed/",
    "https://simonwillison.net/atom/everything/",
]

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36"
DB_URL = "postgresql://pav:password@localhost/rss"
TIMEOUT = 5
POOL_MIN = 5
POOL_MAX = 20

logging.basicConfig(level="DEBUG")


class FeedScraper:
    def __init__(self, dburl, feeds=None):
        self._log = logging.getLogger(__name__)
        self._feeds = feeds or DEFAULT_FEEDS
        self._dburl = dburl
        self._dbpool = None
        self._queries = aiosql.from_path("sql/test_queries.sql", "asyncpg")

    async def _insert_into_db(self, entries, url):
        self._log.info(f"Inserting into db: {url}")
        async with self._dbpool.acquire() as conn:
            for entry in entries:
                await self._queries.insert_entry(
                    conn,
                    title=entry["title"],
                    link=entry["link"],
                    description=entry["description"],
                )
        self._log.info(f"INSERTED: {url}")

    def _parse_feed(self, feed_data):
        entries = []
        for entry in feed_data.entries:
            entries.append(
                {
                    "title": entry.get("title", ""),
                    "link": entry.get("link", ""),
                    "description": entry.get("description", ""),
                }
            )
        return entries

    async def _fetch_and_insert(self, session, url):
        self._log.info("Attempting to fetch: %s", url)

        headers = {"User-Agent": USER_AGENT}

        # if etag:
        #     headers["If-None-Match"] = etag
        # if last_modified:
        #     headers["If-Modified-Since"] = last_modified

        try:
            async with session.get(
                url, raise_for_status=True, timeout=TIMEOUT, headers=headers
            ) as response:
                # if response.status == 304:
                #     self._log.info("No updates to: %s", url)
                #     return

                feed_data = feedparser.parse(await response.text())
                self._log.info("Fetched XML for: %s", url)
                entries = self._parse_feed(feed_data)
                await self._insert_into_db(entries, url)

                # headers["etag"] = response.headers.get("ETag")
                # headers["last_modified"] = response.headers.get("Last-Modified")
                # await self._update_feed_info_in_db(url, headers)

        except (ClientResponseError, ClientConnectorError, asyncio.TimeoutError):
            self._log.error("Could not fetch feed: %s", url)

    async def _init_db(self):
        if self._dbpool is None:
            self._dbpool = await asyncpg.create_pool(
                self._dburl, min_size=POOL_MIN, max_size=POOL_MAX
            )

        async with self._dbpool.acquire() as conn:
            await self._queries.create_entries_table(conn)

    async def run_scraper(self):
        await self._init_db()

        async with ClientSession() as session:
            tasks = [self._fetch_and_insert(session, feed) for feed in self._feeds]
            await asyncio.gather(*tasks)


if __name__ == "__main__":
    start_time = time.time()
    scraper = FeedScraper(DB_URL)
    asyncio.run(scraper.run_scraper())
    print("--- %s seconds ---" % (time.time() - start_time))
