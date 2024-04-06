-- name: create-schema#
DROP TABLE IF EXISTS feed_tags;
DROP TABLE IF EXISTS tags;
DROP TABLE IF EXISTS entries;
DROP TABLE IF EXISTS feeds;

-- -- DROP TABLE IF EXISTS feeds CASCADE;
-- CREATE TABLE IF NOT EXISTS feeds (
--     feed_id SERIAL PRIMARY KEY,
--     feed_url TEXT UNIQUE NOT NULL,
--     feed_name TEXT, -- NOT NULL
--     last_updated TIMESTAMP,
--     feed_type TEXT,
--     icon_url TEXT,
--     etag_header TEXT,
--     last_modified_header TEXT,
--     parsing_error_count INT DEFAULT 0, 
--     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
-- );

-- -- DROP TABLE IF EXISTS entries;
-- CREATE TABLE entries (
--     entry_id SERIAL PRIMARY KEY,
--     entry_title TEXT NOT NULL,
--     entry_url TEXT UNIQUE NOT NULL,
--     author TEXT,
--     summary TEXT,
--     content TEXT,
--     published_date TIMESTAMP,
--     updated_date TIMESTAMP,
--     cleaned_content TEXT,
--     is_favourite BOOLEAN DEFAULT FALSE,
--     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
--     feed_id INT REFERENCES feeds (feed_id)

--     -- viewed BOOLEAN,
--     -- icon_url TEXT,
--     -- updated TIMESTAMP,
-- );

-- -- DROP TABLE IF EXISTS tags CASCADE;
-- CREATE TABLE IF NOT EXISTS tags (
--     tag_id SERIAL PRIMARY KEY,
--     tag_name TEXT UNIQUE NOT NULL
-- );

-- -- DROP TABLE IF EXISTS feed_tags;
-- CREATE TABLE IF NOT EXISTS feed_tags (
--     feed_id INT REFERENCES feeds (feed_id),
--     tag_id INT REFERENCES tags (tag_id),
--     PRIMARY KEY (feed_id, tag_id)
-- );

-- CREATE TABLE users (
--     user_id SERIAL PRIMARY KEY,
--     email TEXT UNIQUE NOT NULL,
--     password TEXT UNIQUE NOT NULL
-- );

-- SQLITE: schema
CREATE TABLE IF NOT EXISTS feeds (
    feed_id INTEGER PRIMARY KEY AUTOINCREMENT,
    feed_url TEXT UNIQUE NOT NULL,
    feed_name TEXT,
    last_updated TIMESTAMP,
    feed_type TEXT,
    icon_url TEXT,
    etag_header TEXT,
    last_modified_header TEXT,
    parsing_error_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE entries (
    entry_id INTEGER PRIMARY KEY AUTOINCREMENT,
    entry_title TEXT NOT NULL,
    entry_url TEXT UNIQUE NOT NULL,
    author TEXT,
    summary TEXT,
    content TEXT,
    published_date TIMESTAMP,
    updated_date TIMESTAMP,
    cleaned_content TEXT,
    is_favourite BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    feed_id INTEGER REFERENCES feeds (feed_id)
);

CREATE TABLE IF NOT EXISTS tags (
    tag_id INTEGER PRIMARY KEY AUTOINCREMENT,
    tag_name TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS feed_tags (
    feed_id INTEGER REFERENCES feeds (feed_id),
    tag_id INTEGER REFERENCES tags (tag_id),
    PRIMARY KEY (feed_id, tag_id)
);