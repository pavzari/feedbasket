from datetime import datetime, timezone
from urllib.parse import urlparse

import tldextract


def display_pub_date(entry_date: datetime | None) -> str:
    """Format the publication date to be more readable."""
    if entry_date is None:
        return ""

    delta = datetime.now(timezone.utc) - entry_date

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
    """Shorten feed source URL"""
    extracted = tldextract.extract(url)
    main_domain = extracted.domain + "." + extracted.suffix
    return main_domain


def extract_main_url(feed_url: str) -> str:
    """Get main website URL from feed URL"""
    parsed_url = urlparse(feed_url)
    main_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
    return main_url
