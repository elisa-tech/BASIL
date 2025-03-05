ALTER TABLE users ADD COLUMN username VARCHAR(100) DEFAULT '';
ALTER TABLE users ADD COLUMN reset_pwd VARCHAR(100) DEFAULT '';
ALTER TABLE users ADD COLUMN reset_token VARCHAR(100) DEFAULT '';
UPDATE users SET username = substr(email, 1, instr(email, '@') - 1);