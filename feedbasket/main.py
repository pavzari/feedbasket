import asyncio
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated

import aiosql
from asyncpg.pool import Pool
from jinja2 import Environment, FileSystemLoader
from litestar import Controller, Litestar, Response, get, post, put
from litestar.contrib.htmx.request import HTMXRequest
from litestar.contrib.htmx.response import HTMXTemplate
from litestar.contrib.jinja import JinjaTemplateEngine
from litestar.datastructures import State
from litestar.enums import RequestEncodingType
from litestar.params import Body
from litestar.response import Redirect, Template
from litestar.static_files import create_static_files_router
from litestar.template.config import TemplateConfig

from feedbasket import config
from feedbasket.database import close_db_pool, init_db
from feedbasket.feedfinder import find_feed
from feedbasket.filters import display_feed_url, display_pub_date
from feedbasket.models import Feed, FeedEntry, NewFeedForm
from feedbasket.scraper import FeedScraper

jinja_env = Environment(loader=FileSystemLoader(Path(__file__).parent / "templates"))
jinja_env.filters.update(
    {
        "display_pub_date": display_pub_date,
        "display_feed_url": display_feed_url,
    }
)
template_config = TemplateConfig(
    engine=JinjaTemplateEngine.from_environment(jinja_env),
)

queries = aiosql.from_path("./feedbasket/queries", "asyncpg")


@asynccontextmanager
async def lifespan(app: Litestar):
    await init_db(app, queries)
    asyncio.create_task(scrape_feeds(app.state.pool))
    yield
    await close_db_pool(app)


async def scrape_feeds(db_pool: Pool) -> None:
    """Fetch and parse the feeds periodically."""
    await asyncio.sleep(1)
    scraper = FeedScraper(db_pool, queries)
    while True:
        await scraper.run_scraper()
        await asyncio.sleep(config.FETCH_INTERVAL_SEC)


@get("/")
async def index(state: State) -> Template:
    async with state.pool.acquire() as conn:
        entry_count = await queries.get_entry_count(conn)
        entries = [FeedEntry(**entry) for entry in await queries.get_entries(conn)]
        tags_feeds = await queries.get_tags_feeds(conn)
        context = {
            "entries": entries,
            "entry_count": entry_count,
            "tags_feeds": tags_feeds,
        }
    return Template(template_name="index.html", context=context)


class FavouritesController(Controller):
    path = "/favourites"

    @post(path="/{entry_id:int}")
    async def mark_as_favorite(self, state: State, entry_id: int) -> Template:
        async with state.pool.acquire() as conn:
            await queries.mark_as_favourite(conn, entry_id)
        return Template(
            "svg_star_filled.html", context={"entry": {"entry_id": entry_id}}
        )

    @put(path="/{entry_id:int}")
    async def unmark_as_favorite(
        self,
        state: State,
        entry_id: int,
        request: HTMXRequest,
    ) -> Response | Template:
        print(request.htmx.current_url)

        async with state.pool.acquire() as conn:
            await queries.unmark_as_favourite(conn, entry_id)

        if request.htmx.current_url and "favourites" in request.htmx.current_url:
            # return HTMXTemplate(content="", re_target="closest #feed-entry") ??
            return Response(content="", headers={"HX-RETARGET": "closest #feed-entry"})

        return HTMXTemplate(
            template_name="svg_star_empty.html",
            context={"entry": {"entry_id": entry_id}},
        )

    @get()
    async def get_favourites(self, state: State) -> Template:
        async with state.pool.acquire() as conn:
            fav_count = await queries.get_favourite_count(conn)
            entries = [
                FeedEntry(**entry) for entry in await queries.get_favourites(conn)
            ]
            context = {
                "entries": entries,
                "fav_count": fav_count,
            }
        return Template("favourites.html", context=context)


class ManageFeedsController(Controller):
    path = "/feeds"

    @get()
    async def get_feeds(self, state: State) -> Template:
        async with state.pool.acquire() as conn:
            feed_count = await queries.get_feed_count(conn)
            inactive_feeds = await queries.get_inactive_feed_count(conn)
            unreachable_feeds = await queries.get_unreachable_feed_count(conn)
            feeds = [Feed(**entry) for entry in await queries.get_feeds(conn)]
            context = {
                "feeds": feeds,
                "feed_count": feed_count,
                "inactive_feeds": inactive_feeds,
                "unreachable_feeds": unreachable_feeds,
            }

        return Template("feeds.html", context=context)

    @post(path="/find")
    async def find_feed(
        self,
        state: State,
        data: Annotated[dict, Body(media_type=RequestEncodingType.URL_ENCODED)],
    ) -> Template:
        # error if feed not found or the url is not valid.
        if not find_feed(data["url"]):
            return Response(content="Feed could not be found. Try base URL instead???")

        feed_url, feed_name, feed_type = find_feed(data["url"])

        async with state.pool.acquire() as conn:
            tags = await queries.get_all_tags(conn)
            context = {
                "feed_url": feed_url,
                "feed_name": feed_name,
                "tags": tags,
                "feed_type": feed_type,
            }

        return Template("add_feed.html", context=context)

    @post(path="/add")
    async def add_new_feed(
        self,
        state: State,
        data: Annotated[NewFeedForm, Body(media_type=RequestEncodingType.URL_ENCODED)],
    ) -> Redirect:
        # Error if feed already exists.
        # Handle single/multiple tags and also case sensitivity.

        async with state.pool.acquire() as conn:
            await queries.add_feed(
                conn,
                feed_url=data.feed_url,
                feed_name=data.feed_name,
                feed_type=data.feed_type,
                icon_url=data.icon_url,
            )

            # combine checkeckboxes and new tag if present.
            all_tags = []
            if data.existing_tags:
                all_tags.extend(data.existing_tags)

            if data.new_tag:
                all_tags.append(data.new_tag.lower())

            if all_tags:
                for tag in all_tags:
                    await queries.add_new_tag(conn, tag_name=tag)
                    await queries.create_feed_tag_relationship(
                        conn, feed_url=data.feed_url, tag_name=tag
                    )

        scraper = FeedScraper(state.pool, queries)
        await scraper.run_scraper(data.feed_url)

        return Redirect(path="/")


app = Litestar(
    lifespan=[lifespan],
    request_class=HTMXRequest,
    route_handlers=[
        FavouritesController,
        ManageFeedsController,
        index,
        create_static_files_router(path="/static", directories=["./feedbasket/static"]),
    ],
    template_config=template_config,
)
