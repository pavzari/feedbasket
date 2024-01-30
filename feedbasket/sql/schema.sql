-- Feeds 
-- Entries
-- Users

-- Categories - folder
-- Tags? 

CREATE TABLE feeds (
    feed_id SERIAL PRIMARY KEY,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    name TEXT NOT NULL,
    url TEXT UNIQUE NOT NULL,
    last_fetched TIMESTAMP

    feed_type TEXT,
    folder TEXT,
    icon_url TEXT, -- favicon
    entries_count INT,--- Type?

    etag TEXT,
    modified_header TEXT, -- timestamp?
    -- user_id UUID REFERENCES users (user_id)


)

CREATE TABLE entries (
    entry_id SERIAL PRIMARY KEY,
    feed_id INT REFERENCES feeds (feed_id)
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    title TEXT NOT NULL,
    url TEXT UNIQUE NOT NULL,
    last_fetched_at TIMESTAMP

    publication_date TIMESTAMP,
    -- updated TIMESTAMP,

    content_short TEXT,
    content_full TEXT,
    author TEXT,

    favourite BOOLEAN,
    viewed BOOLEAN,

    -- icon_url TEXT to display next to entry.

)

CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    password TEXT UNIQUE NOT NULL
)
