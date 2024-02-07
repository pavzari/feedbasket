-- Feeds 
-- Entries
-- Users

-- Categories - folder
-- Tags? 

CREATE TABLE feeds (
    feed_id SERIAL PRIMARY KEY,
    feed_url TEXT UNIQUE NOT NULL,

    feed_name TEXT NOT NULL,

    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    last_fetched TIMESTAMP,

    feed_type TEXT,
    feed_tags TEXT, -- tag?
    icon_url TEXT, -- favicon?

    etag TEXT,
    modified_header TEXT,
    
    -- user_id UUID REFERENCES users (user_id)
)

CREATE TABLE entries (
    entry_id SERIAL PRIMARY KEY,
    entry_title TEXT NOT NULL,
    entry_url TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
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

)

CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    password TEXT UNIQUE NOT NULL
)
