import asyncio
import contextlib
import logging

import aiosql
import asyncpg
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from feedbasket import config
from feedbasket.database import (
    close_db_pool,
    create_db_pool,
    create_schema,
    add_default_feeds,
)
from feedbasket.filters import display_feed_url, display_pub_date
from feedbasket.scraper import FeedScraper

logging.basicConfig(level=config.LOG_LEVEL)
log = logging.getLogger(__name__)


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI) -> None:
    await create_db_pool(app)
    await create_schema(app, queries)
    await add_default_feeds(app, queries)
    asyncio.create_task(scrape_feeds(app.state.pool))
    yield
    await close_db_pool(app)


app = FastAPI(lifespan=lifespan)
queries = aiosql.from_path("./feedbasket/queries", "asyncpg")
templates = Jinja2Templates(directory="./feedbasket/templates")

app.mount("/static", StaticFiles(directory="./feedbasket/static"), name="static")
templates.env.filters["display_pub_date"] = display_pub_date
templates.env.filters["display_feed_url"] = display_feed_url


async def scrape_feeds(db_pool: asyncpg.Pool) -> None:
    """Fetch and parse the feeds periodically."""
    scraper = FeedScraper(db_pool, queries)
    while True:
        await scraper.run_scraper()
        await asyncio.sleep(config.FETCH_INTERVAL_SEC)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    async with request.app.state.pool.acquire() as conn:
        entries = await queries.get_entries(conn)
    context = {
        "request": request,
        "entries": entries,
    }
    return templates.TemplateResponse("index.html", context)
