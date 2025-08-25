ALTER TABLE apis ADD COLUMN write_permission_requests TEXT DEFAULT '';
ALTER TABLE apis_history ADD COLUMN write_permission_requests TEXT DEFAULT '';
ALTER TABLE notifications ADD COLUMN for_owners INTEGER DEFAULT 0;
ALTER TABLE notifications ADD COLUMN user_ids TEXT DEFAULT '';
UPDATE notifications SET read_by = '[' || REPLACE(read_by, ',', '][') || ']';
