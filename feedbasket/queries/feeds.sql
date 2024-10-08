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

-- name: get_feeds_with_tags
SELECT
    f.feed_id,
    f.feed_url,
    f.feed_name,
    f.last_updated,
    f.feed_type,
    f.icon_url,
    f.etag_header,
    f.muted,
    f.last_modified_header,
    f.parsing_error_count,
    f.created_at,
    ARRAY_AGG(t.tag_name) AS tags
FROM
    feeds f
    LEFT JOIN feed_tags ft ON f.feed_id = ft.feed_id
    LEFT JOIN tags t ON ft.tag_id = t.tag_id
GROUP BY
    f.feed_id;

-- name: get-feed-by-id^
SELECT * FROM feeds
WHERE feed_id = :feed_id;

-- name: get_feed_by_url^
SELECT * FROM feeds
WHERE feed_url = :feed_url;

-- name: update-feed-error-count!
UPDATE feeds
SET parsing_error_count = parsing_error_count + 1
WHERE feed_id = :feed_id;

-- name: update-feed-name!
UPDATE feeds
SET feed_name = :feed_name
WHERE feed_id = :feed_id;

-- name: toggle-mute-feed!
UPDATE feeds
SET muted = :muted
WHERE feed_id = :feed_id;

-- name: add-feed<!
INSERT INTO feeds
(feed_url, feed_name, feed_type, icon_url)
VALUES (:feed_url, :feed_name, :feed_type, :icon_url)
ON CONFLICT (feed_url) DO NOTHING
RETURNING feed_id;

--name: check-feed-exists
SELECT EXISTS (
    SELECT 1
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

-- name: feed-unsubscribe!
DELETE FROM feeds
WHERE feed_id = :feed_id;

-- name: delete-entries-unsubscribe!
DELETE FROM entries
WHERE feed_id = :feed_id
AND is_favourite = FALSE;

-- name: favourites-unsubscribe!
UPDATE entries
SET feed_id = NULL
WHERE feed_id = :feed_id
AND is_favourite = TRUE;
