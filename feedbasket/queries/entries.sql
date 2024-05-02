-- name: insert-entry!
INSERT INTO entries (
    entry_title,
    entry_url,
    published_date,
    updated_date,
    author,
    summary,
    content,
    feed_id,
    cleaned_content
) VALUES (
    :entry_title,
    :entry_url,
    :published_date,
    :updated_date,
    :author,
    :summary,
    :content,
    :feed_id,
    :cleaned_content )
ON CONFLICT (entry_url) DO NOTHING;

-- name: get-entries
SELECT
    e.entry_id,
    e.entry_title,
    e.entry_url,
    e.author,
    e.summary,
    e.content,
    e.published_date,
    e.updated_date,
    e.cleaned_content,
    e.is_favourite,
    e.created_at,
    e.feed_id
FROM entries e
LEFT JOIN feeds f ON e.feed_id = f.feed_id
WHERE f.muted = FALSE or f.muted is null
ORDER BY e.published_date DESC;

-- name: mark-as-favourite!
UPDATE entries
SET is_favourite = TRUE
WHERE entry_id = :entry_id

-- name: unmark-as-favourite!
UPDATE entries
SET is_favourite = FALSE
WHERE entry_id = :entry_id

-- name: get-favourites
SELECT * FROM entries
WHERE is_favourite = TRUE
ORDER BY published_date DESC

-- name: get-entry-count$
SELECT COUNT(*) FROM entries;

-- name: get-favourite-count$
SELECT COUNT(*) FROM entries
WHERE is_favourite = TRUE;

-- name: get-latest-entry-date^
SELECT published_date FROM entries
WHERE feed_id = :feed_id
ORDER BY published_date DESC
LIMIT 1;
