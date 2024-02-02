import asyncio
import logging
from datetime import datetime
from time import mktime

import aiosql
import feedparser
from aiohttp import ClientConnectorError, ClientResponseError, ClientSession
from asyncpg import Pool
from pydantic import BaseModel, HttpUrl, validator

from feedbasket.config import DEFAULT_FEEDS, GET_TIMEOUT, USER_AGENT


class FeedEntry(BaseModel):
    title: str
    link: HttpUrl
    description: str
    published_date: datetime

    @validator("published_date", pre=True, always=True)
    def parse_published_date(cls, value):
        return datetime.fromtimestamp(mktime(value))


class FeedScraper:
    def __init__(self, pool: Pool, queries: aiosql.from_path):
        self._log = logging.getLogger(__name__)
        self._pool = pool
        self._queries = queries
        self._log.info("Feed scraper initialized.")

    async def _insert_into_db(self, entries, url):
        self._log.info(f"Updating feed: {url}")
        async with self._pool.acquire() as conn:
            for entry in entries:

                await self._queries.insert_entry(
                    conn,
                    title=entry.title,
                    link=entry.link,
                    description=entry.description,
                    published_date=entry.published_date,
                    # title=entry["title"],
                    # link=entry["link"],
                    # description=entry["description"],
                    # published_date=entry["published_date"],
                )
        self._log.info(f"Updated feed: {url}")

    def _parse_feed(self, feed_data):
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
            # {
            #     "title": entry.get("title", ""),
            #     "link": entry.get("link", ""),
            #     "description": entry.get("description", ""),
            #     "published_date": entry.get("published_parsed", " "),
            # }
        # )
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
                url, raise_for_status=True, timeout=GET_TIMEOUT, headers=headers
            ) as response:

                # if response.status == 304:
                #     self._log.info("No updates to: %s", url)
                #     return

                feed_data = feedparser.parse(await response.text())
                self._log.info("Fetched XML: %s", url)
                entries = self._parse_feed(feed_data)
                await self._insert_into_db(entries, url)

                # headers["etag"] = response.headers.get("ETag")
                # headers["last_modified"] = response.headers.get("Last-Modified")
                # await self._update_feed_info_in_db(url, headers)

        except (ClientResponseError, ClientConnectorError, asyncio.TimeoutError):
            self._log.error("Could not fetch feed: %s", url)

    # async def _update_feed_info_in_db(self, url, headers):
    #     async with self._pool.acquire() as conn:
    #         await self._queries.update_feed_info(conn, url, headers)

    async def run_scraper(self):

        # get the feeds from the feeds table:
        # assign them to the self._feeds variable

        # async with self._pool.acquire() as conn:
        #     feeds = await self._queries.get_feeds(conn)

        #     if not feeds:
        #         self._log.info("No feeds found. Using default feeds.")
        #         self._feeds = DEFAULT_FEEDS (read from feeds.csv here or call that function.)

        async with ClientSession() as session:
            tasks = [self._fetch_and_insert(session, feed) for feed in DEFAULT_FEEDS]
            await asyncio.gather(*tasks)


# if __name__ == "__main__":
#     start_time = time.time()
#     scraper = FeedScraper(DB_URL)
#     asyncio.run(scraper.run_scraper())
#     print("--- %s seconds ---" % (time.time() - start_time))
