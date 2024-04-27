import logging
from urllib.parse import unquote, urljoin

import feedparser
import requests
from bs4 import BeautifulSoup

from feedbasket import config

log = logging.getLogger(__name__)

FeedMetadata = tuple[str, str, str | None, str | None]


def get_feed_metadata(feed_data: feedparser.FeedParserDict):
    feed_name = feed_data.feed.get("title")
    feed_type = feed_data.get("version")
    icon_url = feed_data.feed.get("icon")
    return feed_name, feed_type, icon_url


def get_feed_content(url: str) -> requests.Response | None:
    try:
        response = requests.get(
            url, timeout=config.GET_TIMEOUT, headers={"User-Agent": config.USER_AGENT}
        )
        response.raise_for_status()

        if not response.ok:
            log.error(
                "Failed to retrieve feed: %s, status code: %s",
                url,
                response.status_code,
            )
            return None
        return response

    except requests.exceptions.RequestException as e:
        log.error(f"Failed to retrieve: {url}: {e}")
        return None


def find_feed(url: str) -> FeedMetadata | None:
    """Attempt to find a feed URL from a webpage URL.
    Returns tuple with feed metadata or None if no feed found."""

    # Assume provided URL is a feed URL:

    url = url.strip() if url.startswith("http") else ("https://" + url.strip())
    response = get_feed_content(url)
    if not response:
        return None

    feed_data = feedparser.parse(response.content)
    mime = response.headers.get("Content-Type", "").split(";")[0]

    if not feed_data.bozo and mime.endswith("xml"):
        feed_meta = get_feed_metadata(feed_data)
        return url, *feed_meta

    soup = BeautifulSoup(response.content, "lxml")

    # Find page title in <meta> tags or <title>:

    #  feed_title = None

    #  OG_TAGS = ["og:title", "og:site_name"]  # "og:description"]

    #  for tag in OG_TAGS:
    #      og_tag = soup.find("meta", property=tag)
    #      if og_tag:
    #          feed_title = og_tag.text.strip()
    #          break

    #  if not feed_title:
    #      title_tag = soup.find("title")
    #      if title_tag:
    #          feed_title = title_tag.text.strip()

    # Search for RSS/Atom feed in <link> tags:

    FEED_LINK_MIME_TYPES = [
        "application/rss+xml",
        "application/atom+xml",
        "application/x.atom+xml",
        "application/x-atom+xml",
        "application/atom",
        "application/rss",
        "application/rdf",
    ]

    # "text/atom+xml",
    # "text/rss+xml",
    # "text/rdf+xml",
    # "text/atom",
    # "text/rss",
    # "text/rdf",
    # "text/xml",

    for type in FEED_LINK_MIME_TYPES:
        link = soup.find("link", type=type, href=True)
        links = soup.findAll("link", type=type, href=True)
        print("multiple feeds:", links)
        if link:
            feed_url = unquote(urljoin(url, link["href"])).strip()
            if response := get_feed_content(feed_url):
                feed_data = feedparser.parse(response.content)
                feed_meta = get_feed_metadata(feed_data)
                return feed_url, *feed_meta

    # Try common feed paths:

    COMMON_FEED_PATHS = [
        "/feed",
        "/rss",
        "/feed.xml",
        "/rss.xml",
        "/feed.atom",
        "/atom.xml",
        "/index.xml",
        "/blog.xml",
    ]
    for path in COMMON_FEED_PATHS:
        feed_url = unquote(urljoin(url, path)).strip()
        if response := get_feed_content(feed_url):
            mime = response.headers.get("Content-Type", "").split(";")[0]
            if mime.endswith("xml"):
                feed_data = feedparser.parse(response.content)
                feed_meta = get_feed_metadata(feed_data)
                return feed_url, *feed_meta

    log.error(f"Failed to find feed: {url}")
    return None
