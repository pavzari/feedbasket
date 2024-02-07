-- name: create-entries-table#

-- DROP TABLE IF EXISTS feeds;
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
    etag TEXT,
    modified_header TEXT
);

DROP TABLE IF EXISTS entries;
CREATE TABLE IF NOT EXISTS entries (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    link VARCHAR(255) NOT NULL,
    published_date TIMESTAMP,
    description TEXT
);

-- name: insert-entry!
INSERT INTO entries
(title, link, description, published_date)
VALUES (:title, :link, :description, :published_date);

-- name: insert-default-feeds!
INSERT INTO feeds
(feed_url)
VALUES
(:feed_url);

-- name: update-feed-info!
UPDATE feeds
SET etag = :etag,
    modified_header = :modified_header,
    last_fetched = :last_fetched
WHERE feed_url = :feed_url;

-- name: get-feeds
SELECT * FROM feeds;

-- name: get-entries
SELECT * FROM entries
ORDER BY published_date DESC;