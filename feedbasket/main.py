import logging
from contextlib import asynccontextmanager

import aiosql
import asyncpg
from fastapi import FastAPI, Request

log = logging.getLogger(__name__)
logging.basicConfig(level="DEBUG")

queries = aiosql.from_path("sql/test_queries.sql", "asyncpg")


@asynccontextmanager
async def lifespan(app: FastAPI) -> None:
    # from settings.py?
    log.info("Connecting to PostgreSQL.")
    app.state.pool = await asyncpg.create_pool(
        "postgresql://pav:password@localhost/rss",
        min_size=5,
        max_size=20,
    )
    log.info("Connection established.")
    yield
    log.info("Closing connection to db.")
    await app.state.pool.close()


app = FastAPI(lifespan=lifespan)


@app.get("/")
async def get_feeds(request: Request):
    # pool = request.app.state.pool
    async with request.app.state.pool.acquire() as conn:
        feeds = await queries.get_entries(conn)
    return feeds
