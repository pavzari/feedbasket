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
SELECT * FROM entries
ORDER BY published_date DESC;

-- name: mark-as-favourite
UPDATE entries
SET is_favourite = TRUE
WHERE entry_id = :entry_id

-- name: unmark-as-favourite
UPDATE entries
SET is_favourite = FALSE
WHERE entry_id = :entry_id

-- name: get-favourite-entries
SELECT * FROM entries
WHERE is_favourite = TRUE
ORDER BY published_date DESC