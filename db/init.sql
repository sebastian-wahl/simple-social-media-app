-- ===========================================================
-- init.sql - Initial Postgres setup for development/testing
-- Runs ONLY on first database startup.
-- ===========================================================

-- ============================
-- Drop existing tables (dev only)
-- ============================
DROP TABLE IF EXISTS post_tag_link CASCADE;
DROP TABLE IF EXISTS comment CASCADE;
DROP TABLE IF EXISTS post CASCADE;
DROP TABLE IF EXISTS tag CASCADE;

-- ============================
-- Create tables (SQLModel alignment)
-- ============================

CREATE TABLE post
(
    id         SERIAL PRIMARY KEY,
    image_path TEXT      NOT NULL,
    text       TEXT      NOT NULL,
    "user"     TEXT      NOT NULL,              -- matches Post.user
    toe_rating INTEGER   NOT NULL CHECK (toe_rating BETWEEN 1 AND 5),
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE tag
(
    id   SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL
);

-- link_model: PostTagLink
CREATE TABLE post_tag_link
(
    post_id INTEGER NOT NULL REFERENCES post (id) ON DELETE CASCADE,
    tag_id  INTEGER NOT NULL REFERENCES tag (id) ON DELETE CASCADE,
    PRIMARY KEY (post_id, tag_id)
);

CREATE TABLE comment
(
    id         SERIAL PRIMARY KEY,
    post_id    INTEGER   NOT NULL REFERENCES post (id) ON DELETE CASCADE,
    "user"     TEXT      NOT NULL,             -- matches Comment.user
    text       TEXT      NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- ============================
-- Optional test data
-- ============================
-- INSERT INTO post (image_path, text, "user", toe_rating)
-- VALUES
--     ('test1.jpg', 'Hello World', 'alice', 5),
--     ('test2.jpg', 'Second post', 'bob', 3);

-- INSERT INTO tag (name) VALUES ('test'), ('blue'), ('common');

-- INSERT INTO post_tag_link (post_id, tag_id)
-- VALUES (1, 1), (1, 2), (2, 3);

-- INSERT INTO comment (post_id, "user", text)
-- VALUES (1, 'alice', 'Nice post!');

-- ============================
-- Done
-- ============================
