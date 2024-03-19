-- name: insert-default-feeds!
INSERT INTO feeds
(feed_url)
VALUES (:feed_url)
ON CONFLICT (feed_url) DO NOTHING;

-- name: update-feed-meta!
UPDATE feeds
SET etag_header = :etag_header,
    last_modified_header = :last_modified_header,
    last_updated = :last_updated
WHERE feed_url = :feed_url;

-- name: get-feeds
SELECT * FROM feeds;

-- name: update-feed-error-count!
UPDATE feeds
SET parsing_error_count = parsing_error_count + 1
WHERE feed_id = :feed_id;

