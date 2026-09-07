BEGIN;

-- SPDX author signature: unique identity used as Person.name in SBOM exports.
-- Each existing user gets a distinct UUID; new users receive one in UserModel.__init__.

ALTER TABLE users ADD COLUMN IF NOT EXISTS spdx_signature VARCHAR(255);

UPDATE users
SET spdx_signature = gen_random_uuid()::text
WHERE spdx_signature IS NULL OR btrim(spdx_signature) = '';

ALTER TABLE users ALTER COLUMN spdx_signature SET NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS users_spdx_signature_key ON users (spdx_signature);

COMMIT;
