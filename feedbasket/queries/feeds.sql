-- name: insert-default-feeds!
INSERT INTO feeds
(feed_url)
VALUES (:feed_url)
ON CONFLICT (feed_url) DO NOTHING;

-- name: update-feed-meta!
UPDATE feeds
SET etag_header = :etag_header,
    last_modified_header = :last_modified_header,
    last_updated = :last_updated,
    parsing_error_count = :parsing_error_count
WHERE feed_url = :feed_url;

-- name: get-all-feeds
SELECT * FROM feeds;

-- name: get-single-feed^
SELECT * FROM feeds
WHERE feed_id = :feed_id;

-- name: get_feed_by_url
SELECT * FROM feeds
WHERE feed_url = :feed_url;

-- name: update-feed-error-count!
UPDATE feeds
SET parsing_error_count = parsing_error_count + 1
WHERE feed_id = :feed_id;

-- name: add-feed!
INSERT INTO feeds
(feed_url, feed_name, feed_type, icon_url)
VALUES (:feed_url, :feed_name, :feed_type, :icon_url)
ON CONFLICT (feed_url) DO NOTHING;

--name: check-feed-exists
SELECT EXISTS(SELECT 1
    FROM feeds 
    WHERE feed_url = :feed_url
);

-- name: get-feed-count$
SELECT COUNT(*) FROM feeds;

-- name: get-unreachable-feed-count$
SELECT COUNT(*) 
FROM feeds
WHERE parsing_error_count >= 5;

-- name: get-inactive-feed-count$
SELECT (
    SELECT COUNT(*)
    FROM feeds
    WHERE last_updated < (CURRENT_DATE - INTERVAL '60 days')
    ) + (
    SELECT COUNT(*)
    FROM feeds
    WHERE last_updated IS NULL
    )
AS inactive_count;

-- SELECT COUNT(*)
-- FROM feeds
-- WHERE last_updated < (CURRENT_DATE - INTERVAL '60 days');

