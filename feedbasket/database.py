from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import asyncpg

from feedbasket import config

if TYPE_CHECKING:
    from aiosql.queries import Queries
    from litestar import Litestar

log = logging.getLogger(__name__)


async def init_db(app: Litestar, queries: Queries) -> None:
    await create_db_pool(app)
    # await create_schema(app, queries)
    await add_feeds(app, queries)


async def create_db_pool(app: Litestar) -> None:
    if not config.PG_URI:
        raise ValueError("Postgres URI not specified.")

    app.state.pool = await asyncpg.create_pool(
        config.PG_URI, min_size=config.PG_POOL_MIN, max_size=config.PG_POOL_MAX
    )


async def create_schema(app: Litestar, queries: Queries) -> None:
    pool = app.state.pool
    async with pool.acquire() as conn:
        await queries.create_schema(conn)


async def add_feeds(app: Litestar, queries: Queries) -> None:
    pool = app.state.pool

    with open("feeds.txt") as file:
        feed_urls = [line.strip() for line in file]

    async with pool.acquire() as conn:
        for feed in feed_urls:
            await queries.insert_default_feeds(conn, feed_url=feed)

    # async with pool.acquire() as conn:
    #     for feed in config.DEFAULT_FEEDS:
    #         await queries.insert_default_feeds(conn, feed_url=feed)


async def close_db_pool(app: Litestar) -> None:
    await app.state.pool.close()
    log.info("Connection to database closed.")
