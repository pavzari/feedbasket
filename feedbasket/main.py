import asyncio
import logging
import contextlib

import aiosql
import asyncpg
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from feedbasket.config import FETCH_INTERVAL_SEC, LOG_LEVEL
from feedbasket.database import close_db_pool, create_db_pool, create_schema
from feedbasket.scraper import FeedScraper
from feedbasket.filters import display_publication_date


logging.basicConfig(level=LOG_LEVEL)
log = logging.getLogger(__name__)


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI) -> None:
    await create_db_pool(app)
    await create_schema(app, queries)
    asyncio.create_task(scrape_feeds(app.state.pool))
    yield
    await close_db_pool(app)


app = FastAPI(lifespan=lifespan)
queries = aiosql.from_path("./feedbasket/sql", "asyncpg")
templates = Jinja2Templates(directory="./feedbasket/templates")
templates.env.filters["display_publication_date"] = display_publication_date


async def scrape_feeds(db_pool: asyncpg.Pool) -> None:
    """Fetch and parse the feeds periodically."""
    scraper = FeedScraper(db_pool, queries)
    await asyncio.sleep(3)
    while True:
        await scraper.run_scraper()
        await asyncio.sleep(FETCH_INTERVAL_SEC)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    async with request.app.state.pool.acquire() as conn:
        feeds = await queries.get_entries(conn)
    context = {
        "request": request,
        "entries": feeds,
    }
    return templates.TemplateResponse("index.html", context)
