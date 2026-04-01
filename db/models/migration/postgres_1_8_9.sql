BEGIN;

-- comments: align schema with CommentModel (todo, done, done_by_id, done_at)
-- Assumes table `comments` and `users` already exist (public schema).

ALTER TABLE comments ADD COLUMN IF NOT EXISTS todo BOOLEAN NOT NULL DEFAULT false;
ALTER TABLE comments ADD COLUMN IF NOT EXISTS done BOOLEAN NOT NULL DEFAULT false;
ALTER TABLE comments ADD COLUMN IF NOT EXISTS done_by_id INTEGER;
ALTER TABLE comments ADD COLUMN IF NOT EXISTS done_at TIMESTAMP WITHOUT TIME ZONE;

ALTER TABLE comments ALTER COLUMN done_by_id DROP NOT NULL;
ALTER TABLE comments ALTER COLUMN done_at DROP NOT NULL;

-- comments.created_by_id -> users(id) ON DELETE CASCADE
DO $$
DECLARE
    fk_name text;
BEGIN
    SELECT tc.constraint_name INTO fk_name
    FROM information_schema.table_constraints tc
    JOIN information_schema.key_column_usage kcu
      ON tc.constraint_name = kcu.constraint_name AND tc.table_schema = kcu.table_schema
    WHERE tc.constraint_type = 'FOREIGN KEY'
      AND tc.table_schema = 'public'
      AND tc.table_name = 'comments'
      AND kcu.column_name = 'created_by_id';

    IF fk_name IS NOT NULL THEN
        EXECUTE 'ALTER TABLE comments DROP CONSTRAINT ' || quote_ident(fk_name);
        EXECUTE 'ALTER TABLE comments ADD CONSTRAINT ' || quote_ident(fk_name)
            || ' FOREIGN KEY (created_by_id) REFERENCES users(id) ON DELETE CASCADE';
    END IF;
END$$;

-- comments.done_by_id -> users(id) ON DELETE CASCADE
DO $$
DECLARE
    fk_name text;
BEGIN
    SELECT tc.constraint_name INTO fk_name
    FROM information_schema.table_constraints tc
    JOIN information_schema.key_column_usage kcu
      ON tc.constraint_name = kcu.constraint_name AND tc.table_schema = kcu.table_schema
    WHERE tc.constraint_type = 'FOREIGN KEY'
      AND tc.table_schema = 'public'
      AND tc.table_name = 'comments'
      AND kcu.column_name = 'done_by_id';

    IF fk_name IS NOT NULL THEN
        EXECUTE 'ALTER TABLE comments DROP CONSTRAINT ' || quote_ident(fk_name);
        EXECUTE 'ALTER TABLE comments ADD CONSTRAINT ' || quote_ident(fk_name)
            || ' FOREIGN KEY (done_by_id) REFERENCES users(id) ON DELETE CASCADE';
    ELSE
        EXECUTE 'ALTER TABLE comments ADD CONSTRAINT comments_done_by_id_fkey '
            || 'FOREIGN KEY (done_by_id) REFERENCES users(id) ON DELETE CASCADE';
    END IF;
END$$;

COMMIT;
