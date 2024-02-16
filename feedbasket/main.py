import asyncio
import contextlib
import logging

import aiosql
import asyncpg
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from feedbasket import config
from feedbasket.database import (
    add_default_feeds,
    close_db_pool,
    create_db_pool,
    create_schema,
)
from feedbasket.filters import display_feed_url, display_pub_date
from feedbasket.scraper import FeedScraper
from feedbasket.feedfinder import find_feed_url

logging.basicConfig(level=config.LOG_LEVEL)
log = logging.getLogger(__name__)


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    await create_db_pool(app)
    # await create_schema(app, queries)
    # await add_default_feeds(app, queries)
    # asyncio.create_task(scrape_feeds(app.state.pool))
    yield
    await close_db_pool(app)


app = FastAPI(lifespan=lifespan)
queries = aiosql.from_path("./feedbasket/queries", "asyncpg")
templates = Jinja2Templates(directory="./feedbasket/templates")

app.mount("/static", StaticFiles(directory="feedbasket/static"), name="static")
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


# pip install python-multipart


@app.post("/find-feed", response_class=HTMLResponse)
async def verify_feed(request: Request, url: str = Form(...)):

    if not find_feed_url(url):
        return "Feed could not be found. Please try again."
    # form should remain the same but with an error message displayed

    feed_url, feed_name = find_feed_url(url)

    context = {
        "request": request,
        "feed_url": feed_url,
        "feed_name": feed_name,
    }
    return templates.TemplateResponse("add_feed.html", context)


@app.post("/add-feed", response_class=HTMLResponse)
async def save_feed(
    feed_url: str = Form(...), feed_name: str = Form(...), category: str = Form(...)
):
    print(feed_url, feed_name, category)
    # Save the feed to the database
    # use htmx here as well because otherwise need to redirect to home (or is this something I want?)
    # trigger fetch here for the feed in the background.
    return "Feed saved successfully!"
