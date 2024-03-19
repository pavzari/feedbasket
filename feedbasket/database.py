import logging

import aiosql
import asyncpg
from fastapi import FastAPI

from feedbasket import config

log = logging.getLogger(__name__)


async def init_db(app: FastAPI, queries: aiosql.from_path) -> None:
    await create_db_pool(app)
    await create_schema(app, queries)
    await add_feeds(app, queries)


async def create_db_pool(app: FastAPI) -> None:
    log.info("Connecting to %s.", config.DB_URI)
    app.state.pool = await asyncpg.create_pool(
        config.DB_URI,
        min_size=config.DB_POOL_MIN,
        max_size=config.DB_POOL_MAX,
    )
    log.info("Connection established.")


async def create_schema(app: FastAPI, queries: aiosql.from_path) -> None:
    pool = app.state.pool
    async with pool.acquire() as conn:
        await queries.create_schema(conn)


async def add_feeds(app: FastAPI, queries: aiosql.from_path) -> None:
    pool = app.state.pool

    with open("feeds.txt") as file:
        feed_urls = [line.strip() for line in file]

    async with pool.acquire() as conn:
        for feed in feed_urls:
            await queries.insert_default_feeds(conn, feed_url=feed)

    # async with pool.acquire() as conn:
    #     for feed in config.DEFAULT_FEEDS:
    #         await queries.insert_default_feeds(conn, feed_url=feed)


async def close_db_pool(app: FastAPI) -> None:
    await app.state.pool.close()
    log.info("Connection to database closed.")
