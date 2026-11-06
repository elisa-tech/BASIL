BEGIN;

-- comment_mentions: users referenced from a comment (CommentMentionModel).
-- Assumes tables `comments` and `users` already exist (public schema).
-- CREATE TABLE IF NOT EXISTS so this is a no-op when init_db create_all already built the table.

CREATE TABLE IF NOT EXISTS comment_mentions (
    id SERIAL NOT NULL,
    comment_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    PRIMARY KEY (id),
    CONSTRAINT uq_comment_mentions_comment_user UNIQUE (comment_id, user_id),
    FOREIGN KEY (comment_id) REFERENCES comments (id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);

COMMIT;
