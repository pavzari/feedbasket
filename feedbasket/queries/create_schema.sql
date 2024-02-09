-- Feeds 
-- Entries
-- Users
-- Tags?
DROP TABLE IF EXISTS feeds;
CREATE TABLE IF NOT EXISTS feeds (
    feed_id SERIAL PRIMARY KEY,
    feed_url TEXT UNIQUE NOT NULL,
    feed_name TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_fetched TIMESTAMP,
    feed_type TEXT,
    feed_tags TEXT,
    icon_url TEXT,
    etag_header TEXT,
    modified_header TEXT
);

CREATE TABLE entries (
    entry_id SERIAL PRIMARY KEY,
    entry_title TEXT NOT NULL,
    entry_url TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    publication_date TIMESTAMP,
    -- updated TIMESTAMP,
    last_fetched_at TIMESTAMP
    content_short TEXT,
    content_full TEXT,
    author TEXT,

    is_favourite BOOLEAN,
    viewed BOOLEAN,

    feed_id INT REFERENCES feeds (feed_id)
    -- icon_url TEXT to display next to entry.
);

CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    password TEXT UNIQUE NOT NULL
);
