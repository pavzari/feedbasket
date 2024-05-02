import asyncio
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated

import aiosql
from asyncpg.pool import Pool
from jinja2 import Environment, FileSystemLoader
from litestar import Controller, Litestar, Response, get, post, put, delete
from litestar.contrib.htmx.request import HTMXRequest
from litestar.contrib.htmx.response import HTMXTemplate, ClientRedirect
from litestar.status_codes import HTTP_303_SEE_OTHER
from litestar.contrib.jinja import JinjaTemplateEngine
from litestar.datastructures import State
from litestar.enums import RequestEncodingType
from litestar.params import Body
from litestar.response import Redirect, Template
from litestar.static_files import create_static_files_router
from litestar.template.config import TemplateConfig
from litestar.logging import LoggingConfig

from feedbasket import config
from feedbasket.database import close_db_pool, init_db
from feedbasket.feedfinder import find_feed
from feedbasket.filters import display_feed_url, display_pub_date, extract_main_url
from feedbasket.models import Feed, FeedEntry, NewFeedForm
from feedbasket.scraper import FeedScraper


jinja_env = Environment(loader=FileSystemLoader(Path(__file__).parent / "templates"))
jinja_env.filters.update(
    {
        "display_pub_date": display_pub_date,
        "display_feed_url": display_feed_url,
        "extract_main_url": extract_main_url,
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


class SubscriptionsController(Controller):
    path = "/subscriptions"

    @get()
    async def get_feeds(self, state: State) -> Template:
        async with state.pool.acquire() as conn:
            feed_count = await queries.get_feed_count(conn)
            inactive_feeds = await queries.get_inactive_feed_count(conn)
            unreachable_feeds = await queries.get_unreachable_feed_count(conn)
            feeds = [Feed(**entry) for entry in await queries.get_all_feeds(conn)]
            context = {
                "feeds": feeds,
                "feed_count": feed_count,
                "inactive_feeds": inactive_feeds,
                "unreachable_feeds": unreachable_feeds,
            }

        return Template("subscriptions.html", context=context)

    @post(path="/find")
    async def find_feed(
        self,
        state: State,
        data: Annotated[dict, Body(media_type=RequestEncodingType.URL_ENCODED)],
    ) -> Template | Response:
        response = find_feed(data["url"])
        if not response:
            return Response(content="feed could not be found.")

        # TODO: multiple feeds available
        feed_url, feed_name, feed_type, icon_url = response

        async with state.pool.acquire() as conn:
            check = await queries.check_feed_exists(conn, feed_url=feed_url)
            if check[0]["exists"]:
                return Response(content="You already follow this feed.")

            tags = await queries.get_all_tags(conn)
            print(tags)
            context = {
                "feed_url": feed_url,
                "feed_name": feed_name,
                "feed_type": feed_type,
                "icon_url": icon_url,
                "tags": tags,
            }

        return Template("feed_add.html", context=context)

    @post(path="/add")
    async def add_new_feed(
        self,
        state: State,
        data: Annotated[NewFeedForm, Body(media_type=RequestEncodingType.URL_ENCODED)],
    ) -> Redirect:
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

    @get(path="/{feed_id:int}/edit")
    async def view_feed_info(self, feed_id: int, state: State) -> Template:
        async with state.pool.acquire() as conn:
            feed = await queries.get_single_feed(conn, feed_id=feed_id)
            latest = await queries.get_latest_entry_date(conn, feed_id=feed_id)
            all_tags = [tag["tag_name"] for tag in await queries.get_all_tags(conn)]
            assigned_tags = [
                tag["tag_name"]
                for tag in await queries.get_feed_tags(conn, feed_id=feed_id)
            ]
            if not assigned_tags:
                available_tags = all_tags
            else:
                available_tags = [tag for tag in all_tags if tag not in assigned_tags]

            context = {
                "feed": Feed(**feed),
                "assigned_tags": assigned_tags if assigned_tags else None,
                "available_tags": available_tags if available_tags else None,
                "latest_entry_date": latest["published_date"] if latest else None,
            }
        return Template("feed_info.html", context=context)

    @post(path="/{feed_id:int}/edit")
    async def edit_feed(
        self,
        feed_id: int,
        state: State,
        data: Annotated[dict, Body(media_type=RequestEncodingType.URL_ENCODED)],
    ) -> Redirect:
        # {'feed_name': 'The Verge -  All Posts', 'new_tag': '', 'assigned_tags': ['tag_1', 'tag_3'], 'available_tags': 'tag_2'}
        print(data)

        # combine checkeckboxes and new tag if present.
        # TODO: lowercase! feed_tag_relationship by feed_id vs feed_url! feed_name:
        # required form input.
        all_tags = []
        if data.get("assigned_tags"):
            all_tags.extend(data["assigned_tags"])

        if data.get("available_tags"):
            all_tags.extend(data["available_tags"])

        if data["new_tag"]:
            all_tags.append(data["new_tag"].lower())

        async with state.pool.acquire() as conn:
            if all_tags:
                for tag in all_tags:
                    await queries.add_new_tag(conn, tag_name=tag)
                    await queries.create_feed_tag_relationship(
                        conn, feed_url=data.feed_url, tag_name=tag
                    )
            await queries.update_feed_name(conn, feed_id, data["feed_name"])
            await queries.delete_unused_tags(conn)

        return Redirect(path="/{feed_id:int}/edit")

    @post(path="/toggle-mute-feed/{feed_id:int}")
    async def toggle_mute_feed(
        self,
        feed_id: int,
        state: State,
        data: Annotated[
            dict[str, bool], Body(media_type=RequestEncodingType.URL_ENCODED)
        ],
    ) -> None:
        # TODO: confirmation modal.
        async with state.pool.acquire() as conn:
            await queries.toggle_mute_feed(
                conn, feed_id=feed_id, muted=data["mute-feed"]
            )

    @delete(path="/{feed_id:int}/unsubscribe", status_code=HTTP_303_SEE_OTHER)
    async def unsubscribe(self, state: State, feed_id: int) -> ClientRedirect:
        async with state.pool.acquire() as conn:
            await queries.delete_entries_unsubscribe(conn, feed_id)
            await queries.favourites_unsubscribe(conn, feed_id)
            await queries.feed_unsubscribe(conn, feed_id)
            await queries.delete_unused_tags(conn)
        return ClientRedirect(redirect_to="/subscriptions")


logging_config = LoggingConfig(
    root={"level": config.LOG_LEVEL, "handlers": ["console"]},
    formatters={
        "standard": {"format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"}
    },
)

app = Litestar(
    lifespan=[lifespan],
    request_class=HTMXRequest,
    route_handlers=[
        FavouritesController,
        SubscriptionsController,
        index,
        create_static_files_router(path="/static", directories=["./feedbasket/static"]),
    ],
    template_config=template_config,
    logging_config=logging_config,
)
