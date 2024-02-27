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
