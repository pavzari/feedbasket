from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlparse

import tldextract
from jinja2 import Environment, FileSystemLoader
from litestar.contrib.jinja import JinjaTemplateEngine
from litestar.template.config import TemplateConfig
from tzlocal import get_localzone


def display_pub_date(entry_date: datetime | None) -> str:
    """Format the publication date to be more readable."""
    if entry_date is None:
        return ""

    delta = datetime.now(UTC) - entry_date

    if delta.total_seconds() < 60:
        return f"{delta.seconds}s ago"
    elif delta.total_seconds() < 3600:
        minutes = delta.seconds // 60
        return f"{minutes}min ago"
    elif delta.days == 0:
        hours = delta.seconds // 3600
        return f"{hours}h ago"
    elif delta.days < 365:
        return f"{delta.days} day{'s' if delta.days > 1 else ''} ago"
    else:
        return entry_date.strftime("%b %Y")


# def display_feed_url(feed_url: str) -> str:
#    """Extract the main site URL from a feed URL."""
#    parsed_url = urlparse(feed_url)
#    return parsed_url.netloc.replace("www.", "")


def display_feed_url(url: str) -> str:
    """Shorten feed source URL."""
    extracted = tldextract.extract(url)
    return extracted.domain + "." + extracted.suffix


def display_main_url(feed_url: str) -> str:
    """Get main website URL from feed URL."""
    parsed_url = urlparse(feed_url)
    return f"{parsed_url.scheme}://{parsed_url.netloc}"


def convert_utc_to_local(utc_datetime: datetime) -> datetime:
    local_tz = get_localzone()
    _utc_datetime = utc_datetime.replace(tzinfo=UTC)
    return _utc_datetime.astimezone(local_tz)


jinja_env = Environment(loader=FileSystemLoader(Path(__file__).parent / "templates"))
jinja_env.filters.update(
    {
        "display_pub_date": display_pub_date,
        "display_feed_url": display_feed_url,
        "display_main_url": display_main_url,
        "utc_to_local": convert_utc_to_local,
    }
)

template_config = TemplateConfig(
    engine=JinjaTemplateEngine.from_environment(jinja_env),
)
