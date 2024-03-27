import asyncio
import contextlib
import logging

import aiosql
import asyncpg
from fastapi import FastAPI, Form, Header, Request
from fastapi.responses import HTMLResponse, Response, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from feedbasket import config
from feedbasket.database import close_db_pool, init_db
from feedbasket.feedfinder import find_feed_url
from feedbasket.filters import display_feed_url, display_pub_date
from feedbasket.models import Feed, FeedEntry
from feedbasket.scraper import FeedScraper

logging.basicConfig(level=config.LOG_LEVEL)
log = logging.getLogger(__name__)


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db(app, queries)
    asyncio.create_task(scrape_feeds(app.state.pool))
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
    await asyncio.sleep(1)
    scraper = FeedScraper(db_pool, queries)
    while True:
        await scraper.run_scraper()
        await asyncio.sleep(config.FETCH_INTERVAL_SEC)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    async with request.app.state.pool.acquire() as conn:
        entry_count = await queries.get_entry_count(conn)
        entries = [FeedEntry(**entry) for entry in await queries.get_entries(conn)]
        tags_feeds = await queries.get_tags_feeds(conn)
        context = {
            "request": request,
            "entries": entries,
            "entry_count": entry_count,
            "tags_feeds": tags_feeds,
        }
    return templates.TemplateResponse("index.html", context)


@app.get("/feeds", response_class=HTMLResponse)
async def get_feeds(request: Request):
    async with request.app.state.pool.acquire() as conn:
        feed_count = await queries.get_feed_count(conn)
        inactive_feeds = await queries.get_inactive_feed_count(conn)
        unreachable_feeds = await queries.get_unreachable_feed_count(conn)
        feeds = [Feed(**entry) for entry in await queries.get_feeds(conn)]
        context = {
            "request": request,
            "feeds": feeds,
            "feed_count": feed_count,
            "inactive_feeds": inactive_feeds,
            "unreachable_feeds": unreachable_feeds,
        }
    return templates.TemplateResponse("feeds.html", context)


@app.post("/feeds/find", response_class=HTMLResponse)
async def verify_feed(request: Request, url: str = Form(...)):
    # pip install python-multipart
    # error if feed not found or the url is not valid.
    if not find_feed_url(url):
        return "Feed could not be found. Try base URL instead???"

    feed_url, feed_name = find_feed_url(url)

    async with request.app.state.pool.acquire() as conn:
        tags = await queries.get_all_tags(conn)

    context = {
        "request": request,
        "feed_url": feed_url,
        "feed_name": feed_name,
        "tags": tags,
    }
    return templates.TemplateResponse("add_feed.html", context)


@app.post("/feeds/add", response_class=HTMLResponse)
async def save_feed(
    request: Request,
    feed_url: str = Form(...),
    feed_name: str = Form(...),
    feed_type: str = Form(None),
    icon_url: str = Form(None),
    new_tag: str = Form(None),
    tags: list[str] = Form(None),
):
    # Extract form data from request object.
    # Error if feed already exists.
    # Handle single/multiple tags and also case sensitivity.

    print("CHECKBOXES: ", tags)
    print("NEW TAG: ", new_tag)

    db_pool = request.app.state.pool

    async with db_pool.acquire() as conn:
        await queries.add_feed(conn, feed_url, feed_name, feed_type, icon_url)

        # add tags: combine checkeckboxes and new tag if present.
        all_tags = []
        if tags:
            all_tags.extend(tags)

        if new_tag:
            all_tags.append(new_tag.lower())

        if all_tags:
            for tag in all_tags:
                await queries.add_new_tag(conn, tag_name=tag)
                await queries.create_feed_tag_relationship(
                    conn, feed_url=feed_url, tag_name=tag
                )

    scraper = FeedScraper(db_pool, queries)
    # asyncio.create_task(scraper.run_scraper(feed_url))
    # wait for scrape to finish before redirect, otherwise new entries are not displayed.
    await scraper.run_scraper(feed_url)

    print(feed_url, feed_name, all_tags)
    # use htmx here as well because otherwise need to redirect to home (or is this something I want?)
    # trigger fetch here for the feed in the background.

    # redirect to home
    return RedirectResponse(url="/", status_code=303)


@app.post("/favourites/{entry_id}", response_class=HTMLResponse)
async def mark_as_favorites(request: Request, entry_id: int):
    async with request.app.state.pool.acquire() as conn:
        await queries.mark_as_favourite(conn, entry_id)
    return f'<button hx-delete="/favourites/{entry_id}" hx-swap="outerHTML">Remove from Favorites</button>'


@app.delete("/favourites/{entry_id}", response_class=HTMLResponse)
async def unmark_as_favorites(
    response: Response,
    request: Request,
    entry_id: int,
    hx_current_url: str = Header(...),
):
    async with request.app.state.pool.acquire() as conn:
        await queries.unmark_as_favourite(conn, entry_id)
    if "favourites" in hx_current_url:
        response.headers["HX-Retarget"] = "closest #feed-entry"
        return ""
    return f'<button hx-post="/favourites/{entry_id}" hx-swap="outerHTML">Add to Favourites</button>'


@app.get("/favourites", response_class=HTMLResponse)
async def get_favourites(request: Request):
    async with request.app.state.pool.acquire() as conn:
        fav_count = await queries.get_favourite_count(conn)
        entries = [FeedEntry(**entry) for entry in await queries.get_favourites(conn)]
        context = {
            "request": request,
            "entries": entries,
            "fav_count": fav_count,
        }
    return templates.TemplateResponse("favourites.html", context)
