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
    "user"     TEXT      NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    rating     DOUBLE PRECISION NOT NULL DEFAULT 0.0
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
    id              SERIAL PRIMARY KEY,
    post_id         INTEGER   NOT NULL REFERENCES post (id) ON DELETE CASCADE,
    "user"          TEXT      NOT NULL,
    text            TEXT      NOT NULL,
    created_at      TIMESTAMP NOT NULL DEFAULT NOW(),

    -- sentiment analysis
    sentiment       TEXT,
    sentiment_score DOUBLE PRECISION
);

-- ============================
-- Optional test data
-- ============================
-- INSERT INTO post (image_path, text, "user")
-- VALUES
--   ('posts/example.jpg', 'Nice image', 'alice');

-- INSERT INTO comment (post_id, "user", text, sentiment, sentiment_score)
-- VALUES
--   (1, 'bob', 'Looks great!', 'positive', 0.98);

-- ============================
-- Done
-- ============================
