-- name: create-schema#
DROP TABLE IF EXISTS feed_tags;
DROP TABLE IF EXISTS tags;
DROP TABLE IF EXISTS entries;
DROP TABLE IF EXISTS feeds;

CREATE TABLE IF NOT EXISTS feeds (
    feed_id SERIAL PRIMARY KEY,
    feed_url TEXT UNIQUE NOT NULL,
    feed_name TEXT, -- NOT NULL
    last_updated TIMESTAMPTZ,
    feed_type TEXT,
    icon_url TEXT,
    etag_header TEXT,
    muted BOOLEAN DEFAULT FALSE,
    last_modified_header TEXT,
    parsing_error_count INT DEFAULT 0, 
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS entries (
    entry_id SERIAL PRIMARY KEY,
    entry_title TEXT NOT NULL,
    entry_url TEXT UNIQUE NOT NULL,
    author TEXT,
    summary TEXT,
    content TEXT,
    published_date TIMESTAMPTZ,
    updated_date TIMESTAMPTZ,
    cleaned_content TEXT,
    is_favourite BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    feed_id INT REFERENCES feeds (feed_id)
    -- viewed BOOLEAN,
    -- icon_url TEXT,
    -- updated TIMESTAMP,
);

CREATE TABLE IF NOT EXISTS tags (
    tag_id SERIAL PRIMARY KEY,
    tag_name TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS feed_tags (
    feed_id INT REFERENCES feeds (feed_id),
    tag_id INT REFERENCES tags (tag_id),
    PRIMARY KEY (feed_id, tag_id)
);

-- CREATE TABLE users (
--     user_id SERIAL PRIMARY KEY,
--     email TEXT UNIQUE NOT NULL,
--     password TEXT UNIQUE NOT NULL
-- );
