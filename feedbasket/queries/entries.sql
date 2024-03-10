-- name: insert-entry!
INSERT INTO entries (
    entry_title,
    entry_url,
    description,
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
    :description,
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