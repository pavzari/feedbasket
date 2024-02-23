-- name: create-entries-table#
DROP TABLE IF EXISTS feeds CASCADE;
CREATE TABLE IF NOT EXISTS feeds (
    feed_id SERIAL PRIMARY KEY,
    feed_url TEXT UNIQUE NOT NULL,
    feed_name TEXT,
    last_fetched TIMESTAMP,
    feed_type TEXT,
    feed_tags TEXT,
    icon_url TEXT,
    etag_header TEXT,
    modified_header TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

DROP TABLE IF EXISTS entries;
CREATE TABLE IF NOT EXISTS entries (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    link VARCHAR(255) NOT NULL,
    published_date TIMESTAMP,
    updated_date TIMESTAMP,
    author TEXT,
    summary TEXT,
    content TEXT,
    description TEXT,
    is_favourite BOOLEAN,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    feed_id INT REFERENCES feeds (feed_id)
);

-- name: insert-entry!
INSERT INTO entries
(title, link, description, published_date, author, summary, content, feed_id) 
VALUES (:title, :link, :description, :published_date, :author, :summary, :content, :feed_id);

-- name: insert-default-feeds!
INSERT INTO feeds
(feed_url)
VALUES (:feed_url)
ON CONFLICT (feed_url) DO NOTHING;

-- name: update-feed-meta!
UPDATE feeds
SET etag_header = :etag_header,
    modified_header = :modified_header,
    last_fetched = :last_fetched
WHERE feed_url = :feed_url;

-- name: get-feeds
SELECT * FROM feeds;

-- name: get-entries
SELECT * FROM entries
ORDER BY published_date DESC;