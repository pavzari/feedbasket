import logging

import aiosql
import asyncpg
from fastapi import FastAPI

from feedbasket.config import DB_POOL_MAX, DB_POOL_MIN, DB_URI

log = logging.getLogger(__name__)


async def create_db_pool(app: FastAPI) -> None:
    log.info("Connecting to %s.", DB_URI)
    app.state.pool = await asyncpg.create_pool(
        DB_URI,
        min_size=DB_POOL_MIN,
        max_size=DB_POOL_MAX,
    )
    log.info("Connection established.")


async def close_db_pool(app: FastAPI) -> None:
    await app.state.pool.close()
    log.info("Connection to database closed.")


async def create_schema(app: FastAPI, queries: aiosql.from_path) -> None:
    pool = app.state.pool
    async with pool.acquire() as conn:
        await queries.create_entries_table(conn)
