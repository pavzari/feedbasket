-- name: get-all-tags
SELECT tag_name FROM tags;

-- name: add-new-tag!
INSERT INTO tags
(tag_name)
VALUES (:tag_name)
ON CONFLICT (tag_name) DO NOTHING;

-- name: create-feed-tag-relationship!
INSERT INTO feed_tags (feed_id, tag_id)
SELECT
    (SELECT feed_id FROM feeds WHERE feed_url = :feed_url),
    tag_id
FROM tags
WHERE tag_name = :tag_name
ON CONFLICT DO NOTHING;

-- name: get-tags-feeds
SELECT tag_name, feed_url FROM feed_tags
JOIN tags ON feed_tags.tag_id = tags.tag_id
JOIN feeds ON feed_tags.feed_id = feeds.feed_id;
