import logging
from contextlib import asynccontextmanager

import aiosql
import aiosqlite
import asyncpg
from fastapi import FastAPI

from feedbasket import config

log = logging.getLogger(__name__)


class SQLiteConnection:
    """AIOSQLite connection."""

    def __init__(self, db_path: str):
        self._db_path = db_path

    @asynccontextmanager
    async def acquire(self):
        async with aiosqlite.connect(self._db_path) as conn:
            conn.row_factory = aiosqlite.Row
            yield conn
            await conn.commit()


async def init_db(app: FastAPI, queries: aiosql.from_path) -> None:
    await create_db_pool(app)
    # await create_schema(app, queries)
    await add_feeds(app, queries)


async def create_db_pool(app: FastAPI) -> None:
    if config.DB_ENGINE == "postgresql":
        app.state.pool = await asyncpg.create_pool(
            config.PG_URI, min_size=config.PG_POOL_MIN, max_size=config.PG_POOL_MAX
        )
    elif config.DB_ENGINE == "sqlite":
        app.state.pool = SQLiteConnection(config.SQLITE_PATH)
    else:
        raise ValueError(f"Unsupported database engine: {config.DB_ENGINE}")


# async def create_db_pool(app: FastAPI) -> None:
#     log.info("Connecting to %s.", config.DB_URI)
#     app.state.pool = await asyncpg.create_pool(
#         config.DB_URI,
#         min_size=config.DB_POOL_MIN,
#         max_size=config.DB_POOL_MAX,
#     )
#     log.info("Connection established.")


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
    # if isinstance(app.state.pool, PostgresConnection):
    #     await app.state.pool._pool.close()
    await app.state.pool.close()
    log.info("Connection to database closed.")
