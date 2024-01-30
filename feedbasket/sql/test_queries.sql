-- name: create-entries-table#
DROP TABLE IF EXISTS entries;
CREATE TABLE IF NOT EXISTS entries (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    link VARCHAR(255) NOT NULL,
    description TEXT,
    etag TEXT,
    last_modified TEXT
    )

-- name: insert-entry!
INSERT INTO entries
(title, link, description)
VALUES (:title, :link, :description)

-- name: get-entries
SELECT * FROM entries
LIMIT 20;
