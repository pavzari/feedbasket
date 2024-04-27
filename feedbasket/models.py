import logging
import time
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, field_validator

log = logging.getLogger(__name__)


class NewFeedForm(BaseModel):
    """New feed form data model."""

    feed_url: str
    feed_name: str
    feed_type: Optional[str] = None
    existing_tags: Optional[list[str] | str] = None
    icon_url: Optional[str] = None
    new_tag: Optional[str] = None

    @field_validator("existing_tags", mode="after")
    def existing_tags_to_list(cls, value):
        if isinstance(value, str):
            return [value]
        elif isinstance(value, list):
            return value
        else:
            return None


class Feed(BaseModel):
    """Represents an existing feed in the database.
    Matches the schema of the 'feeds' table."""

    feed_id: int
    feed_url: str
    feed_name: str | None  #!
    last_updated: datetime | None
    feed_type: str | None
    icon_url: str | None  #!
    etag_header: str | None
    last_modified_header: str | None
    parsing_error_count: int
    created_at: datetime


class NewFeedEntry(BaseModel):
    """Model for creating new feed entries in the database.
    Maps to the fields required for inserting into the 'entries' table.
    Includes validators for parsing dates and replacing empty strings with None."""

    entry_title: str
    entry_url: str
    author: str | None
    summary: str | None
    content: str | None
    published_date: datetime | None
    updated_date: datetime | None
    cleaned_content: str | None

    @staticmethod
    def parse_date(value):
        try:
            return datetime.fromtimestamp(time.mktime(value))
        except (ValueError, TypeError):
            log.info("Could not parse date.")
            return None

    @field_validator("updated_date", mode="before")
    def parse_updated_date(cls, value):
        return cls.parse_date(value)

    @field_validator("author", "summary", "content", "cleaned_content", mode="before")
    def replace_empty_str_with_none(cls, value):
        if value == "":
            return None
        return value


class FeedEntry(BaseModel):
    """Represents an existing feed entry in the database.
    Matches the schema of the 'entries' table."""

    entry_id: int
    entry_title: str
    entry_url: str
    author: str | None
    summary: str | None
    content: str | None
    published_date: datetime | None
    updated_date: datetime | None
    cleaned_content: str | None
    is_favourite: bool
    created_at: datetime
    feed_id: int
