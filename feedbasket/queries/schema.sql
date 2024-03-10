-- name: create-schema#
DROP TABLE IF EXISTS feeds CASCADE;
CREATE TABLE IF NOT EXISTS feeds (
    feed_id SERIAL PRIMARY KEY,
    feed_url TEXT UNIQUE NOT NULL,
    feed_name TEXT, -- NOT NULL
    last_updated TIMESTAMP,
    feed_type TEXT,
    feed_tags TEXT, -- Category?
    icon_url TEXT,
    etag_header TEXT,
    last_modified_header TEXT,
    parsing_error_count INT DEFAULT 0, 
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

DROP TABLE IF EXISTS entries;
CREATE TABLE entries (
    entry_id SERIAL PRIMARY KEY,
    entry_title TEXT NOT NULL,
    entry_url TEXT UNIQUE NOT NULL,
    published_date TIMESTAMP,
    updated_date TIMESTAMP,
    author TEXT,
    summary TEXT,
    content TEXT,
    description TEXT,
    cleaned_content TEXT,
    is_favourite BOOLEAN,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    feed_id INT REFERENCES feeds (feed_id)

    -- viewed BOOLEAN,
    -- icon_url TEXT,
    -- updated TIMESTAMP,
);

-- CREATE TABLE users (
--     user_id SERIAL PRIMARY KEY,
--     email TEXT UNIQUE NOT NULL,
--     password TEXT UNIQUE NOT NULL
-- );
