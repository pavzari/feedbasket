-- name: get-all-tags
SELECT tag_name FROM tags;

-- name: get-feed-tags
SELECT tag_name FROM feed_tags
JOIN tags on feed_tags.tag_id = tags.tag_id
WHERE feed_id = :feed_id;

-- name: add-new-tag!
INSERT INTO tags
(tag_name)
VALUES (:tag_name)
ON CONFLICT (tag_name) DO NOTHING;

-- name: create-feed-tag-relationship!
INSERT INTO feed_tags (feed_id, tag_id)
SELECT
    :feed_id,
    tag_id
FROM tags
WHERE tag_name = :tag_name
ON CONFLICT DO NOTHING;

-- name: remove-feed-tag-relationship!
DELETE FROM feed_tags
WHERE feed_id = :feed_id
  AND tag_id = (
    SELECT tag_id
    FROM tags
    WHERE tag_name = :tag_name
  );

-- name: get-tags-feeds
SELECT tag_name, feed_url FROM feed_tags
JOIN tags ON feed_tags.tag_id = tags.tag_id
JOIN feeds ON feed_tags.feed_id = feeds.feed_id;

-- name: delete-unused-tags!
DELETE FROM tags
WHERE tag_id NOT IN (
    SELECT tag_id
    FROM feed_tags
);
