BEGIN;

-- Utility DO block to drop and recreate an FK with ON DELETE CASCADE
-- Parameters (inline): target_table, target_column, referenced_table, referenced_column
-- Note: All tables are assumed to be under the 'public' schema

-- apis.created_by_id -> users(id)
DO $$
DECLARE
    fk_name text;
BEGIN
    SELECT tc.constraint_name INTO fk_name
    FROM information_schema.table_constraints tc
    JOIN information_schema.key_column_usage kcu
      ON tc.constraint_name = kcu.constraint_name AND tc.table_schema = kcu.table_schema
    JOIN information_schema.constraint_column_usage ccu
      ON ccu.constraint_name = tc.constraint_name AND ccu.constraint_schema = tc.table_schema
    WHERE tc.constraint_type = 'FOREIGN KEY'
      AND tc.table_schema = 'public'
      AND tc.table_name = 'apis'
      AND kcu.column_name = 'created_by_id';

    IF fk_name IS NOT NULL THEN
        EXECUTE format('ALTER TABLE %I DROP CONSTRAINT %I', 'apis', fk_name);
        EXECUTE format('ALTER TABLE %I ADD CONSTRAINT %I FOREIGN KEY (%I) REFERENCES %I(%I) ON DELETE CASCADE',
                       'apis', fk_name, 'created_by_id', 'users', 'id');
    END IF;
END$$;

-- apis.edited_by_id -> users(id)
DO $$
DECLARE fk_name text; BEGIN
    SELECT tc.constraint_name INTO fk_name FROM information_schema.table_constraints tc
    JOIN information_schema.key_column_usage kcu
      ON tc.constraint_name = kcu.constraint_name AND tc.table_schema = kcu.table_schema
    WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_schema = 'public'
      AND tc.table_name = 'apis' AND kcu.column_name = 'edited_by_id';
    IF fk_name IS NOT NULL THEN
        EXECUTE format('ALTER TABLE %I DROP CONSTRAINT %I', 'apis', fk_name);
        EXECUTE format('ALTER TABLE %I ADD CONSTRAINT %I FOREIGN KEY (%I) REFERENCES %I(%I) ON DELETE CASCADE',
                       'apis', fk_name, 'edited_by_id', 'users', 'id');
    END IF;
END$$;

-- apis_history.created_by_id -> users(id)
DO $$
DECLARE fk_name text; BEGIN
    SELECT tc.constraint_name INTO fk_name FROM information_schema.table_constraints tc
    JOIN information_schema.key_column_usage kcu
      ON tc.constraint_name = kcu.constraint_name AND tc.table_schema = kcu.table_schema
    WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_schema = 'public'
      AND tc.table_name = 'apis_history' AND kcu.column_name = 'created_by_id';
    IF fk_name IS NOT NULL THEN
        EXECUTE format('ALTER TABLE %I DROP CONSTRAINT %I', 'apis_history', fk_name);
        EXECUTE format('ALTER TABLE %I ADD CONSTRAINT %I FOREIGN KEY (%I) REFERENCES %I(%I) ON DELETE CASCADE',
                       'apis_history', fk_name, 'created_by_id', 'users', 'id');
    END IF;
END$$;

-- apis_history.edited_by_id -> users(id)
DO $$
DECLARE fk_name text; BEGIN
    SELECT tc.constraint_name INTO fk_name FROM information_schema.table_constraints tc
    JOIN information_schema.key_column_usage kcu
      ON tc.constraint_name = kcu.constraint_name AND tc.table_schema = kcu.table_schema
    WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_schema = 'public'
      AND tc.table_name = 'apis_history' AND kcu.column_name = 'edited_by_id';
    IF fk_name IS NOT NULL THEN
        EXECUTE format('ALTER TABLE %I DROP CONSTRAINT %I', 'apis_history', fk_name);
        EXECUTE format('ALTER TABLE %I ADD CONSTRAINT %I FOREIGN KEY (%I) REFERENCES %I(%I) ON DELETE CASCADE',
                       'apis_history', fk_name, 'edited_by_id', 'users', 'id');
    END IF;
END$$;

-- document_mapping_api.* -> apis/documents/users
DO $$ DECLARE fk_name text; BEGIN
    SELECT tc.constraint_name INTO fk_name FROM information_schema.table_constraints tc
    JOIN information_schema.key_column_usage kcu ON tc.constraint_name=kcu.constraint_name AND tc.table_schema=kcu.table_schema
    WHERE tc.constraint_type='FOREIGN KEY' AND tc.table_schema='public' AND tc.table_name='document_mapping_api' AND kcu.column_name='api_id';
    IF fk_name IS NOT NULL THEN
      EXECUTE 'ALTER TABLE document_mapping_api DROP CONSTRAINT '||quote_ident(fk_name);
      EXECUTE 'ALTER TABLE document_mapping_api ADD CONSTRAINT '||quote_ident(fk_name)||' FOREIGN KEY (api_id) REFERENCES apis(id) ON DELETE CASCADE';
    END IF;
END$$;

DO $$ DECLARE fk_name text; BEGIN
    SELECT tc.constraint_name INTO fk_name FROM information_schema.table_constraints tc
    JOIN information_schema.key_column_usage kcu ON tc.constraint_name=kcu.constraint_name AND tc.table_schema=kcu.table_schema
    WHERE tc.constraint_type='FOREIGN KEY' AND tc.table_schema='public' AND tc.table_name='document_mapping_api' AND kcu.column_name='document_id';
    IF fk_name IS NOT NULL THEN
      EXECUTE 'ALTER TABLE document_mapping_api DROP CONSTRAINT '||quote_ident(fk_name);
      EXECUTE 'ALTER TABLE document_mapping_api ADD CONSTRAINT '||quote_ident(fk_name)||' FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE';
    END IF;
END$$;

DO $$ DECLARE fk_name text; BEGIN
    SELECT tc.constraint_name INTO fk_name FROM information_schema.table_constraints tc
    JOIN information_schema.key_column_usage kcu ON tc.constraint_name=kcu.constraint_name AND tc.table_schema=kcu.table_schema
    WHERE tc.constraint_type='FOREIGN KEY' AND tc.table_schema='public' AND tc.table_name='document_mapping_api' AND kcu.column_name='created_by_id';
    IF fk_name IS NOT NULL THEN
      EXECUTE 'ALTER TABLE document_mapping_api DROP CONSTRAINT '||quote_ident(fk_name);
      EXECUTE 'ALTER TABLE document_mapping_api ADD CONSTRAINT '||quote_ident(fk_name)||' FOREIGN KEY (created_by_id) REFERENCES users(id) ON DELETE CASCADE';
    END IF;
END$$;

DO $$ DECLARE fk_name text; BEGIN
    SELECT tc.constraint_name INTO fk_name FROM information_schema.table_constraints tc
    JOIN information_schema.key_column_usage kcu ON tc.constraint_name=kcu.constraint_name AND tc.table_schema=kcu.table_schema
    WHERE tc.constraint_type='FOREIGN KEY' AND tc.table_schema='public' AND tc.table_name='document_mapping_api' AND kcu.column_name='edited_by_id';
    IF fk_name IS NOT NULL THEN
      EXECUTE 'ALTER TABLE document_mapping_api DROP CONSTRAINT '||quote_ident(fk_name);
      EXECUTE 'ALTER TABLE document_mapping_api ADD CONSTRAINT '||quote_ident(fk_name)||' FOREIGN KEY (edited_by_id) REFERENCES users(id) ON DELETE CASCADE';
    END IF;
END$$;

-- document_mapping_api_history.*
DO $$ DECLARE fk_name text; BEGIN
    SELECT tc.constraint_name INTO fk_name FROM information_schema.table_constraints tc
    JOIN information_schema.key_column_usage kcu ON tc.constraint_name=kcu.constraint_name AND tc.table_schema=kcu.table_schema
    WHERE tc.constraint_type='FOREIGN KEY' AND tc.table_schema='public' AND tc.table_name='document_mapping_api_history' AND kcu.column_name='api_id';
    IF fk_name IS NOT NULL THEN
      EXECUTE 'ALTER TABLE document_mapping_api_history DROP CONSTRAINT '||quote_ident(fk_name);
      EXECUTE 'ALTER TABLE document_mapping_api_history ADD CONSTRAINT '||quote_ident(fk_name)||' FOREIGN KEY (api_id) REFERENCES apis(id) ON DELETE CASCADE';
    END IF;
END$$;

DO $$ DECLARE fk_name text; BEGIN
    SELECT tc.constraint_name INTO fk_name FROM information_schema.table_constraints tc
    JOIN information_schema.key_column_usage kcu ON tc.constraint_name=kcu.constraint_name AND tc.table_schema=kcu.table_schema
    WHERE tc.constraint_type='FOREIGN KEY' AND tc.table_schema='public' AND tc.table_name='document_mapping_api_history' AND kcu.column_name='document_id';
    IF fk_name IS NOT NULL THEN
      EXECUTE 'ALTER TABLE document_mapping_api_history DROP CONSTRAINT '||quote_ident(fk_name);
      EXECUTE 'ALTER TABLE document_mapping_api_history ADD CONSTRAINT '||quote_ident(fk_name)||' FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE';
    END IF;
END$$;

DO $$ DECLARE fk_name text; BEGIN
    SELECT tc.constraint_name INTO fk_name FROM information_schema.table_constraints tc
    JOIN information_schema.key_column_usage kcu ON tc.constraint_name=kcu.constraint_name AND tc.table_schema=kcu.table_schema
    WHERE tc.constraint_type='FOREIGN KEY' AND tc.table_schema='public' AND tc.table_name='document_mapping_api_history' AND kcu.column_name='created_by_id';
    IF fk_name IS NOT NULL THEN
      EXECUTE 'ALTER TABLE document_mapping_api_history DROP CONSTRAINT '||quote_ident(fk_name);
      EXECUTE 'ALTER TABLE document_mapping_api_history ADD CONSTRAINT '||quote_ident(fk_name)||' FOREIGN KEY (created_by_id) REFERENCES users(id) ON DELETE CASCADE';
    END IF;
END$$;

DO $$ DECLARE fk_name text; BEGIN
    SELECT tc.constraint_name INTO fk_name FROM information_schema.table_constraints tc
    JOIN information_schema.key_column_usage kcu ON tc.constraint_name=kcu.constraint_name AND tc.table_schema=kcu.table_schema
    WHERE tc.constraint_type='FOREIGN KEY' AND tc.table_schema='public' AND tc.table_name='document_mapping_api_history' AND kcu.column_name='edited_by_id';
    IF fk_name IS NOT NULL THEN
      EXECUTE 'ALTER TABLE document_mapping_api_history DROP CONSTRAINT '||quote_ident(fk_name);
      EXECUTE 'ALTER TABLE document_mapping_api_history ADD CONSTRAINT '||quote_ident(fk_name)||' FOREIGN KEY (edited_by_id) REFERENCES users(id) ON DELETE CASCADE';
    END IF;
END$$;

-- Many more tables follow the same pattern

-- documents.created_by_id / edited_by_id
DO $$ DECLARE fk_name text; BEGIN
  SELECT tc.constraint_name INTO fk_name FROM information_schema.table_constraints tc
  JOIN information_schema.key_column_usage kcu ON tc.constraint_name=kcu.constraint_name AND tc.table_schema=kcu.table_schema
  WHERE tc.constraint_type='FOREIGN KEY' AND tc.table_schema='public' AND tc.table_name='documents' AND kcu.column_name='created_by_id';
  IF fk_name IS NOT NULL THEN
    EXECUTE 'ALTER TABLE documents DROP CONSTRAINT '||quote_ident(fk_name);
    EXECUTE 'ALTER TABLE documents ADD CONSTRAINT '||quote_ident(fk_name)||' FOREIGN KEY (created_by_id) REFERENCES users(id) ON DELETE CASCADE';
  END IF;
END$$;

DO $$ DECLARE fk_name text; BEGIN
  SELECT tc.constraint_name INTO fk_name FROM information_schema.table_constraints tc
  JOIN information_schema.key_column_usage kcu ON tc.constraint_name=kcu.constraint_name AND tc.table_schema=kcu.table_schema
  WHERE tc.constraint_type='FOREIGN KEY' AND tc.table_schema='public' AND tc.table_name='documents' AND kcu.column_name='edited_by_id';
  IF fk_name IS NOT NULL THEN
    EXECUTE 'ALTER TABLE documents DROP CONSTRAINT '||quote_ident(fk_name);
    EXECUTE 'ALTER TABLE documents ADD CONSTRAINT '||quote_ident(fk_name)||' FOREIGN KEY (edited_by_id) REFERENCES users(id) ON DELETE CASCADE';
  END IF;
END$$;

-- documents_history.created_by_id / edited_by_id
DO $$ DECLARE fk_name text; BEGIN
  SELECT tc.constraint_name INTO fk_name FROM information_schema.table_constraints tc
  JOIN information_schema.key_column_usage kcu ON tc.constraint_name=kcu.constraint_name AND tc.table_schema=kcu.table_schema
  WHERE tc.constraint_type='FOREIGN KEY' AND tc.table_schema='public' AND tc.table_name='documents_history' AND kcu.column_name='created_by_id';
  IF fk_name IS NOT NULL THEN
    EXECUTE 'ALTER TABLE documents_history DROP CONSTRAINT '||quote_ident(fk_name);
    EXECUTE 'ALTER TABLE documents_history ADD CONSTRAINT '||quote_ident(fk_name)||' FOREIGN KEY (created_by_id) REFERENCES users(id) ON DELETE CASCADE';
  END IF;
END$$;

DO $$ DECLARE fk_name text; BEGIN
  SELECT tc.constraint_name INTO fk_name FROM information_schema.table_constraints tc
  JOIN information_schema.key_column_usage kcu ON tc.constraint_name=kcu.constraint_name AND tc.table_schema=kcu.table_schema
  WHERE tc.constraint_type='FOREIGN KEY' AND tc.table_schema='public' AND tc.table_name='documents_history' AND kcu.column_name='edited_by_id';
  IF fk_name IS NOT NULL THEN
    EXECUTE 'ALTER TABLE documents_history DROP CONSTRAINT '||quote_ident(fk_name);
    EXECUTE 'ALTER TABLE documents_history ADD CONSTRAINT '||quote_ident(fk_name)||' FOREIGN KEY (edited_by_id) REFERENCES users(id) ON DELETE CASCADE';
  END IF;
END$$;

-- justifications.* -> users
DO $$ DECLARE fk_name text; BEGIN
  SELECT tc.constraint_name INTO fk_name FROM information_schema.table_constraints tc
  JOIN information_schema.key_column_usage kcu ON tc.constraint_name=kcu.constraint_name AND tc.table_schema=kcu.table_schema
  WHERE tc.constraint_type='FOREIGN KEY' AND tc.table_schema='public' AND tc.table_name='justifications' AND kcu.column_name='created_by_id';
  IF fk_name IS NOT NULL THEN
    EXECUTE 'ALTER TABLE justifications DROP CONSTRAINT '||quote_ident(fk_name);
    EXECUTE 'ALTER TABLE justifications ADD CONSTRAINT '||quote_ident(fk_name)||' FOREIGN KEY (created_by_id) REFERENCES users(id) ON DELETE CASCADE';
  END IF;
END$$;

DO $$ DECLARE fk_name text; BEGIN
  SELECT tc.constraint_name INTO fk_name FROM information_schema.table_constraints tc
  JOIN information_schema.key_column_usage kcu ON tc.constraint_name=kcu.constraint_name AND tc.table_schema=kcu.table_schema
  WHERE tc.constraint_type='FOREIGN KEY' AND tc.table_schema='public' AND tc.table_name='justifications' AND kcu.column_name='edited_by_id';
  IF fk_name IS NOT NULL THEN
    EXECUTE 'ALTER TABLE justifications DROP CONSTRAINT '||quote_ident(fk_name);
    EXECUTE 'ALTER TABLE justifications ADD CONSTRAINT '||quote_ident(fk_name)||' FOREIGN KEY (edited_by_id) REFERENCES users(id) ON DELETE CASCADE';
  END IF;
END$$;

-- justifications_history.* -> users
DO $$ DECLARE fk_name text; BEGIN
  SELECT tc.constraint_name INTO fk_name FROM information_schema.table_constraints tc
  JOIN information_schema.key_column_usage kcu ON tc.constraint_name=kcu.constraint_name AND tc.table_schema=kcu.table_schema
  WHERE tc.constraint_type='FOREIGN KEY' AND tc.table_schema='public' AND tc.table_name='justifications_history' AND kcu.column_name='created_by_id';
  IF fk_name IS NOT NULL THEN
    EXECUTE 'ALTER TABLE justifications_history DROP CONSTRAINT '||quote_ident(fk_name);
    EXECUTE 'ALTER TABLE justifications_history ADD CONSTRAINT '||quote_ident(fk_name)||' FOREIGN KEY (created_by_id) REFERENCES users(id) ON DELETE CASCADE';
  END IF;
END$$;

DO $$ DECLARE fk_name text; BEGIN
  SELECT tc.constraint_name INTO fk_name FROM information_schema.table_constraints tc
  JOIN information_schema.key_column_usage kcu ON tc.constraint_name=kcu.constraint_name AND tc.table_schema=kcu.table_schema
  WHERE tc.constraint_type='FOREIGN KEY' AND tc.table_schema='public' AND tc.table_name='justifications_history' AND kcu.column_name='edited_by_id';
  IF fk_name IS NOT NULL THEN
    EXECUTE 'ALTER TABLE justifications_history DROP CONSTRAINT '||quote_ident(fk_name);
    EXECUTE 'ALTER TABLE justifications_history ADD CONSTRAINT '||quote_ident(fk_name)||' FOREIGN KEY (edited_by_id) REFERENCES users(id) ON DELETE CASCADE';
  END IF;
END$$;

-- sw_requirements.* -> users
DO $$ DECLARE fk_name text; BEGIN
  SELECT tc.constraint_name INTO fk_name FROM information_schema.table_constraints tc
  JOIN information_schema.key_column_usage kcu ON tc.constraint_name=kcu.constraint_name AND tc.table_schema=kcu.table_schema
  WHERE tc.constraint_type='FOREIGN KEY' AND tc.table_schema='public' AND tc.table_name='sw_requirements' AND kcu.column_name='created_by_id';
  IF fk_name IS NOT NULL THEN
    EXECUTE 'ALTER TABLE sw_requirements DROP CONSTRAINT '||quote_ident(fk_name);
    EXECUTE 'ALTER TABLE sw_requirements ADD CONSTRAINT '||quote_ident(fk_name)||' FOREIGN KEY (created_by_id) REFERENCES users(id) ON DELETE CASCADE';
  END IF;
END$$;

DO $$ DECLARE fk_name text; BEGIN
  SELECT tc.constraint_name INTO fk_name FROM information_schema.table_constraints tc
  JOIN information_schema.key_column_usage kcu ON tc.constraint_name=kcu.constraint_name AND tc.table_schema=kcu.table_schema
  WHERE tc.constraint_type='FOREIGN KEY' AND tc.table_schema='public' AND tc.table_name='sw_requirements' AND kcu.column_name='edited_by_id';
  IF fk_name IS NOT NULL THEN
    EXECUTE 'ALTER TABLE sw_requirements DROP CONSTRAINT '||quote_ident(fk_name);
    EXECUTE 'ALTER TABLE sw_requirements ADD CONSTRAINT '||quote_ident(fk_name)||' FOREIGN KEY (edited_by_id) REFERENCES users(id) ON DELETE CASCADE';
  END IF;
END$$;

-- sw_requirements_history.* -> users
DO $$ DECLARE fk_name text; BEGIN
  SELECT tc.constraint_name INTO fk_name FROM information_schema.table_constraints tc
  JOIN information_schema.key_column_usage kcu ON tc.constraint_name=kcu.constraint_name AND tc.table_schema=kcu.table_schema
  WHERE tc.constraint_type='FOREIGN KEY' AND tc.table_schema='public' AND tc.table_name='sw_requirements_history' AND kcu.column_name='created_by_id';
  IF fk_name IS NOT NULL THEN
    EXECUTE 'ALTER TABLE sw_requirements_history DROP CONSTRAINT '||quote_ident(fk_name);
    EXECUTE 'ALTER TABLE sw_requirements_history ADD CONSTRAINT '||quote_ident(fk_name)||' FOREIGN KEY (created_by_id) REFERENCES users(id) ON DELETE CASCADE';
  END IF;
END$$;

DO $$ DECLARE fk_name text; BEGIN
  SELECT tc.constraint_name INTO fk_name FROM information_schema.table_constraints tc
  JOIN information_schema.key_column_usage kcu ON tc.constraint_name=kcu.constraint_name AND tc.table_schema=kcu.table_schema
  WHERE tc.constraint_type='FOREIGN KEY' AND tc.table_schema='public' AND tc.table_name='sw_requirements_history' AND kcu.column_name='edited_by_id';
  IF fk_name IS NOT NULL THEN
    EXECUTE 'ALTER TABLE sw_requirements_history DROP CONSTRAINT '||quote_ident(fk_name);
    EXECUTE 'ALTER TABLE sw_requirements_history ADD CONSTRAINT '||quote_ident(fk_name)||' FOREIGN KEY (edited_by_id) REFERENCES users(id) ON DELETE CASCADE';
  END IF;
END$$;

-- sw_requirement_mapping_api.* -> apis/sw_requirements/users
DO $$ DECLARE fk_name text; BEGIN
  SELECT tc.constraint_name INTO fk_name FROM information_schema.table_constraints tc
  JOIN information_schema.key_column_usage kcu ON tc.constraint_name=kcu.constraint_name AND tc.table_schema=kcu.table_schema
  WHERE tc.constraint_type='FOREIGN KEY' AND tc.table_schema='public' AND tc.table_name='sw_requirement_mapping_api' AND kcu.column_name='api_id';
  IF fk_name IS NOT NULL THEN
    EXECUTE 'ALTER TABLE sw_requirement_mapping_api DROP CONSTRAINT '||quote_ident(fk_name);
    EXECUTE 'ALTER TABLE sw_requirement_mapping_api ADD CONSTRAINT '||quote_ident(fk_name)||' FOREIGN KEY (api_id) REFERENCES apis(id) ON DELETE CASCADE';
  END IF;
END$$;

DO $$ DECLARE fk_name text; BEGIN
  SELECT tc.constraint_name INTO fk_name FROM information_schema.table_constraints tc
  JOIN information_schema.key_column_usage kcu ON tc.constraint_name=kcu.constraint_name AND tc.table_schema=kcu.table_schema
  WHERE tc.constraint_type='FOREIGN KEY' AND tc.table_schema='public' AND tc.table_name='sw_requirement_mapping_api' AND kcu.column_name='sw_requirement_id';
  IF fk_name IS NOT NULL THEN
    EXECUTE 'ALTER TABLE sw_requirement_mapping_api DROP CONSTRAINT '||quote_ident(fk_name);
    EXECUTE 'ALTER TABLE sw_requirement_mapping_api ADD CONSTRAINT '||quote_ident(fk_name)||' FOREIGN KEY (sw_requirement_id) REFERENCES sw_requirements(id) ON DELETE CASCADE';
  END IF;
END$$;

DO $$ DECLARE fk_name text; BEGIN
  SELECT tc.constraint_name INTO fk_name FROM information_schema.table_constraints tc
  JOIN information_schema.key_column_usage kcu ON tc.constraint_name=kcu.constraint_name AND tc.table_schema=kcu.table_schema
  WHERE tc.constraint_type='FOREIGN KEY' AND tc.table_schema='public' AND tc.table_name='sw_requirement_mapping_api' AND kcu.column_name='created_by_id';
  IF fk_name IS NOT NULL THEN
    EXECUTE 'ALTER TABLE sw_requirement_mapping_api DROP CONSTRAINT '||quote_ident(fk_name);
    EXECUTE 'ALTER TABLE sw_requirement_mapping_api ADD CONSTRAINT '||quote_ident(fk_name)||' FOREIGN KEY (created_by_id) REFERENCES users(id) ON DELETE CASCADE';
  END IF;
END$$;

DO $$ DECLARE fk_name text; BEGIN
  SELECT tc.constraint_name INTO fk_name FROM information_schema.table_constraints tc
  JOIN information_schema.key_column_usage kcu ON tc.constraint_name=kcu.constraint_name AND tc.table_schema=kcu.table_schema
  WHERE tc.constraint_type='FOREIGN KEY' AND tc.table_schema='public' AND tc.table_name='sw_requirement_mapping_api' AND kcu.column_name='edited_by_id';
  IF fk_name IS NOT NULL THEN
    EXECUTE 'ALTER TABLE sw_requirement_mapping_api DROP CONSTRAINT '||quote_ident(fk_name);
    EXECUTE 'ALTER TABLE sw_requirement_mapping_api ADD CONSTRAINT '||quote_ident(fk_name)||' FOREIGN KEY (edited_by_id) REFERENCES users(id) ON DELETE CASCADE';
  END IF;
END$$;

-- sw_requirement_mapping_sw_requirement.* -> mapping_api/self/sw_requirements/users
DO $$ DECLARE fk_name text; BEGIN
  SELECT tc.constraint_name INTO fk_name FROM information_schema.table_constraints tc
  JOIN information_schema.key_column_usage kcu ON tc.constraint_name=kcu.constraint_name AND tc.table_schema=kcu.table_schema
  WHERE tc.constraint_type='FOREIGN KEY' AND tc.table_schema='public' AND tc.table_name='sw_requirement_mapping_sw_requirement' AND kcu.column_name='sw_requirement_mapping_api_id';
  IF fk_name IS NOT NULL THEN
    EXECUTE 'ALTER TABLE sw_requirement_mapping_sw_requirement DROP CONSTRAINT '||quote_ident(fk_name);
    EXECUTE 'ALTER TABLE sw_requirement_mapping_sw_requirement ADD CONSTRAINT '||quote_ident(fk_name)||' FOREIGN KEY (sw_requirement_mapping_api_id) REFERENCES sw_requirement_mapping_api(id) ON DELETE CASCADE';
  END IF;
END$$;

DO $$ DECLARE fk_name text; BEGIN
  SELECT tc.constraint_name INTO fk_name FROM information_schema.table_constraints tc
  JOIN information_schema.key_column_usage kcu ON tc.constraint_name=kcu.constraint_name AND tc.table_schema=kcu.table_schema
  WHERE tc.constraint_type='FOREIGN KEY' AND tc.table_schema='public' AND tc.table_name='sw_requirement_mapping_sw_requirement' AND kcu.column_name='sw_requirement_mapping_sw_requirement_id';
  IF fk_name IS NOT NULL THEN
    EXECUTE 'ALTER TABLE sw_requirement_mapping_sw_requirement DROP CONSTRAINT '||quote_ident(fk_name);
    EXECUTE 'ALTER TABLE sw_requirement_mapping_sw_requirement ADD CONSTRAINT '||quote_ident(fk_name)||' FOREIGN KEY (sw_requirement_mapping_sw_requirement_id) REFERENCES sw_requirement_mapping_sw_requirement(id) ON DELETE CASCADE';
  END IF;
END$$;

DO $$ DECLARE fk_name text; BEGIN
  SELECT tc.constraint_name INTO fk_name FROM information_schema.table_constraints tc
  JOIN information_schema.key_column_usage kcu ON tc.constraint_name=kcu.constraint_name AND tc.table_schema=kcu.table_schema
  WHERE tc.constraint_type='FOREIGN KEY' AND tc.table_schema='public' AND tc.table_name='sw_requirement_mapping_sw_requirement' AND kcu.column_name='sw_requirement_id';
  IF fk_name IS NOT NULL THEN
    EXECUTE 'ALTER TABLE sw_requirement_mapping_sw_requirement DROP CONSTRAINT '||quote_ident(fk_name);
    EXECUTE 'ALTER TABLE sw_requirement_mapping_sw_requirement ADD CONSTRAINT '||quote_ident(fk_name)||' FOREIGN KEY (sw_requirement_id) REFERENCES sw_requirements(id) ON DELETE CASCADE';
  END IF;
END$$;

DO $$ DECLARE fk_name text; BEGIN
  SELECT tc.constraint_name INTO fk_name FROM information_schema.table_constraints tc
  JOIN information_schema.key_column_usage kcu ON tc.constraint_name=kcu.constraint_name AND tc.table_schema=kcu.table_schema
  WHERE tc.constraint_type='FOREIGN KEY' AND tc.table_schema='public' AND tc.table_name='sw_requirement_mapping_sw_requirement' AND kcu.column_name='created_by_id';
  IF fk_name IS NOT NULL THEN
    EXECUTE 'ALTER TABLE sw_requirement_mapping_sw_requirement DROP CONSTRAINT '||quote_ident(fk_name);
    EXECUTE 'ALTER TABLE sw_requirement_mapping_sw_requirement ADD CONSTRAINT '||quote_ident(fk_name)||' FOREIGN KEY (created_by_id) REFERENCES users(id) ON DELETE CASCADE';
  END IF;
END$$;

DO $$ DECLARE fk_name text; BEGIN
  SELECT tc.constraint_name INTO fk_name FROM information_schema.table_constraints tc
  JOIN information_schema.key_column_usage kcu ON tc.constraint_name=kcu.constraint_name AND tc.table_schema=kcu.table_schema
  WHERE tc.constraint_type='FOREIGN KEY' AND tc.table_schema='public' AND tc.table_name='sw_requirement_mapping_sw_requirement' AND kcu.column_name='edited_by_id';
  IF fk_name IS NOT NULL THEN
    EXECUTE 'ALTER TABLE sw_requirement_mapping_sw_requirement DROP CONSTRAINT '||quote_ident(fk_name);
    EXECUTE 'ALTER TABLE sw_requirement_mapping_sw_requirement ADD CONSTRAINT '||quote_ident(fk_name)||' FOREIGN KEY (edited_by_id) REFERENCES users(id) ON DELETE CASCADE';
  END IF;
END$$;

-- test_specification_mapping_sw_requirement.* -> mapping_api/mapping_sw_requirement/test_specifications/users
DO $$ DECLARE fk_name text; BEGIN
  SELECT tc.constraint_name INTO fk_name FROM information_schema.table_constraints tc
  JOIN information_schema.key_column_usage kcu ON tc.constraint_name=kcu.constraint_name AND tc.table_schema=kcu.table_schema
  WHERE tc.constraint_type='FOREIGN KEY' AND tc.table_schema='public' AND tc.table_name='test_specification_mapping_sw_requirement' AND kcu.column_name='sw_requirement_mapping_api_id';
  IF fk_name IS NOT NULL THEN
    EXECUTE 'ALTER TABLE test_specification_mapping_sw_requirement DROP CONSTRAINT '||quote_ident(fk_name);
    EXECUTE 'ALTER TABLE test_specification_mapping_sw_requirement ADD CONSTRAINT '||quote_ident(fk_name)||' FOREIGN KEY (sw_requirement_mapping_api_id) REFERENCES sw_requirement_mapping_api(id) ON DELETE CASCADE';
  END IF;
END$$;

DO $$ DECLARE fk_name text; BEGIN
  SELECT tc.constraint_name INTO fk_name FROM information_schema.table_constraints tc
  JOIN information_schema.key_column_usage kcu ON tc.constraint_name=kcu.constraint_name AND tc.table_schema=kcu.table_schema
  WHERE tc.constraint_type='FOREIGN KEY' AND tc.table_schema='public' AND tc.table_name='test_specification_mapping_sw_requirement' AND kcu.column_name='sw_requirement_mapping_sw_requirement_id';
  IF fk_name IS NOT NULL THEN
    EXECUTE 'ALTER TABLE test_specification_mapping_sw_requirement DROP CONSTRAINT '||quote_ident(fk_name);
    EXECUTE 'ALTER TABLE test_specification_mapping_sw_requirement ADD CONSTRAINT '||quote_ident(fk_name)||' FOREIGN KEY (sw_requirement_mapping_sw_requirement_id) REFERENCES sw_requirement_mapping_sw_requirement(id) ON DELETE CASCADE';
  END IF;
END$$;

DO $$ DECLARE fk_name text; BEGIN
  SELECT tc.constraint_name INTO fk_name FROM information_schema.table_constraints tc
  JOIN information_schema.key_column_usage kcu ON tc.constraint_name=kcu.constraint_name AND tc.table_schema=kcu.table_schema
  WHERE tc.constraint_type='FOREIGN KEY' AND tc.table_schema='public' AND tc.table_name='test_specification_mapping_sw_requirement' AND kcu.column_name='test_specification_id';
  IF fk_name IS NOT NULL THEN
    EXECUTE 'ALTER TABLE test_specification_mapping_sw_requirement DROP CONSTRAINT '||quote_ident(fk_name);
    EXECUTE 'ALTER TABLE test_specification_mapping_sw_requirement ADD CONSTRAINT '||quote_ident(fk_name)||' FOREIGN KEY (test_specification_id) REFERENCES test_specifications(id) ON DELETE CASCADE';
  END IF;
END$$;

DO $$ DECLARE fk_name text; BEGIN
  SELECT tc.constraint_name INTO fk_name FROM information_schema.table_constraints tc
  JOIN information_schema.key_column_usage kcu ON tc.constraint_name=kcu.constraint_name AND tc.table_schema=kcu.table_schema
  WHERE tc.constraint_type='FOREIGN KEY' AND tc.table_schema='public' AND tc.table_name='test_specification_mapping_sw_requirement' AND kcu.column_name='created_by_id';
  IF fk_name IS NOT NULL THEN
    EXECUTE 'ALTER TABLE test_specification_mapping_sw_requirement DROP CONSTRAINT '||quote_ident(fk_name);
    EXECUTE 'ALTER TABLE test_specification_mapping_sw_requirement ADD CONSTRAINT '||quote_ident(fk_name)||' FOREIGN KEY (created_by_id) REFERENCES users(id) ON DELETE CASCADE';
  END IF;
END$$;

DO $$ DECLARE fk_name text; BEGIN
  SELECT tc.constraint_name INTO fk_name FROM information_schema.table_constraints tc
  JOIN information_schema.key_column_usage kcu ON tc.constraint_name=kcu.constraint_name AND tc.table_schema=kcu.table_schema
  WHERE tc.constraint_type='FOREIGN KEY' AND tc.table_schema='public' AND tc.table_name='test_specification_mapping_sw_requirement' AND kcu.column_name='edited_by_id';
  IF fk_name IS NOT NULL THEN
    EXECUTE 'ALTER TABLE test_specification_mapping_sw_requirement DROP CONSTRAINT '||quote_ident(fk_name);
    EXECUTE 'ALTER TABLE test_specification_mapping_sw_requirement ADD CONSTRAINT '||quote_ident(fk_name)||' FOREIGN KEY (edited_by_id) REFERENCES users(id) ON DELETE CASCADE';
  END IF;
END$$;

-- test_case_mapping_test_specification.* -> mapping_api/mapping_sw_requirement/test_cases/users
DO $$ DECLARE fk_name text; BEGIN
  SELECT tc.constraint_name INTO fk_name FROM information_schema.table_constraints tc
  JOIN information_schema.key_column_usage kcu ON tc.constraint_name=kcu.constraint_name AND tc.table_schema=kcu.table_schema
  WHERE tc.constraint_type='FOREIGN KEY' AND tc.table_schema='public' AND tc.table_name='test_case_mapping_test_specification' AND kcu.column_name='test_specification_mapping_api_id';
  IF fk_name IS NOT NULL THEN
    EXECUTE 'ALTER TABLE test_case_mapping_test_specification DROP CONSTRAINT '||quote_ident(fk_name);
    EXECUTE 'ALTER TABLE test_case_mapping_test_specification ADD CONSTRAINT '||quote_ident(fk_name)||' FOREIGN KEY (test_specification_mapping_api_id) REFERENCES test_specification_mapping_api(id) ON DELETE CASCADE';
  END IF;
END$$;

DO $$ DECLARE fk_name text; BEGIN
  SELECT tc.constraint_name INTO fk_name FROM information_schema.table_constraints tc
  JOIN information_schema.key_column_usage kcu ON tc.constraint_name=kcu.constraint_name AND tc.table_schema=kcu.table_schema
  WHERE tc.constraint_type='FOREIGN KEY' AND tc.table_schema='public' AND tc.table_name='test_case_mapping_test_specification' AND kcu.column_name='test_specification_mapping_sw_requirement_id';
  IF fk_name IS NOT NULL THEN
    EXECUTE 'ALTER TABLE test_case_mapping_test_specification DROP CONSTRAINT '||quote_ident(fk_name);
    EXECUTE 'ALTER TABLE test_case_mapping_test_specification ADD CONSTRAINT '||quote_ident(fk_name)||' FOREIGN KEY (test_specification_mapping_sw_requirement_id) REFERENCES test_specification_mapping_sw_requirement(id) ON DELETE CASCADE';
  END IF;
END$$;

DO $$ DECLARE fk_name text; BEGIN
  SELECT tc.constraint_name INTO fk_name FROM information_schema.table_constraints tc
  JOIN information_schema.key_column_usage kcu ON tc.constraint_name=kcu.constraint_name AND tc.table_schema=kcu.table_schema
  WHERE tc.constraint_type='FOREIGN KEY' AND tc.table_schema='public' AND tc.table_name='test_case_mapping_test_specification' AND kcu.column_name='test_case_id';
  IF fk_name IS NOT NULL THEN
    EXECUTE 'ALTER TABLE test_case_mapping_test_specification DROP CONSTRAINT '||quote_ident(fk_name);
    EXECUTE 'ALTER TABLE test_case_mapping_test_specification ADD CONSTRAINT '||quote_ident(fk_name)||' FOREIGN KEY (test_case_id) REFERENCES test_cases(id) ON DELETE CASCADE';
  END IF;
END$$;

DO $$ DECLARE fk_name text; BEGIN
  SELECT tc.constraint_name INTO fk_name FROM information_schema.table_constraints tc
  JOIN information_schema.key_column_usage kcu ON tc.constraint_name=kcu.constraint_name AND tc.table_schema=kcu.table_schema
  WHERE tc.constraint_type='FOREIGN KEY' AND tc.table_schema='public' AND tc.table_name='test_case_mapping_test_specification' AND kcu.column_name='created_by_id';
  IF fk_name IS NOT NULL THEN
    EXECUTE 'ALTER TABLE test_case_mapping_test_specification DROP CONSTRAINT '||quote_ident(fk_name);
    EXECUTE 'ALTER TABLE test_case_mapping_test_specification ADD CONSTRAINT '||quote_ident(fk_name)||' FOREIGN KEY (created_by_id) REFERENCES users(id) ON DELETE CASCADE';
  END IF;
END$$;

DO $$ DECLARE fk_name text; BEGIN
  SELECT tc.constraint_name INTO fk_name FROM information_schema.table_constraints tc
  JOIN information_schema.key_column_usage kcu ON tc.constraint_name=kcu.constraint_name AND tc.table_schema=kcu.table_schema
  WHERE tc.constraint_type='FOREIGN KEY' AND tc.table_schema='public' AND tc.table_name='test_case_mapping_test_specification' AND kcu.column_name='edited_by_id';
  IF fk_name IS NOT NULL THEN
    EXECUTE 'ALTER TABLE test_case_mapping_test_specification DROP CONSTRAINT '||quote_ident(fk_name);
    EXECUTE 'ALTER TABLE test_case_mapping_test_specification ADD CONSTRAINT '||quote_ident(fk_name)||' FOREIGN KEY (edited_by_id) REFERENCES users(id) ON DELETE CASCADE';
  END IF;
END$$;

-- test_cases_history.* -> users
DO $$ DECLARE fk_name text; BEGIN
  SELECT tc.constraint_name INTO fk_name FROM information_schema.table_constraints tc
  JOIN information_schema.key_column_usage kcu ON tc.constraint_name=kcu.constraint_name AND tc.table_schema=kcu.table_schema
  WHERE tc.constraint_type='FOREIGN KEY' AND tc.table_schema='public' AND tc.table_name='test_cases_history' AND kcu.column_name='created_by_id';
  IF fk_name IS NOT NULL THEN
    EXECUTE 'ALTER TABLE test_cases_history DROP CONSTRAINT '||quote_ident(fk_name);
    EXECUTE 'ALTER TABLE test_cases_history ADD CONSTRAINT '||quote_ident(fk_name)||' FOREIGN KEY (created_by_id) REFERENCES users(id) ON DELETE CASCADE';
  END IF;
END$$;

DO $$ DECLARE fk_name text; BEGIN
  SELECT tc.constraint_name INTO fk_name FROM information_schema.table_constraints tc
  JOIN information_schema.key_column_usage kcu ON tc.constraint_name=kcu.constraint_name AND tc.table_schema=kcu.table_schema
  WHERE tc.constraint_type='FOREIGN KEY' AND tc.table_schema='public' AND tc.table_name='test_cases_history' AND kcu.column_name='edited_by_id';
  IF fk_name IS NOT NULL THEN
    EXECUTE 'ALTER TABLE test_cases_history DROP CONSTRAINT '||quote_ident(fk_name);
    EXECUTE 'ALTER TABLE test_cases_history ADD CONSTRAINT '||quote_ident(fk_name)||' FOREIGN KEY (edited_by_id) REFERENCES users(id) ON DELETE CASCADE';
  END IF;
END$$;

-- test_specifications.* -> users (and history)
DO $$ DECLARE fk_name text; BEGIN
  SELECT tc.constraint_name INTO fk_name FROM information_schema.table_constraints tc
  JOIN information_schema.key_column_usage kcu ON tc.constraint_name=kcu.constraint_name AND tc.table_schema=kcu.table_schema
  WHERE tc.constraint_type='FOREIGN KEY' AND tc.table_schema='public' AND tc.table_name='test_specifications' AND kcu.column_name='created_by_id';
  IF fk_name IS NOT NULL THEN
    EXECUTE 'ALTER TABLE test_specifications DROP CONSTRAINT '||quote_ident(fk_name);
    EXECUTE 'ALTER TABLE test_specifications ADD CONSTRAINT '||quote_ident(fk_name)||' FOREIGN KEY (created_by_id) REFERENCES users(id) ON DELETE CASCADE';
  END IF;
END$$;

DO $$ DECLARE fk_name text; BEGIN
  SELECT tc.constraint_name INTO fk_name FROM information_schema.table_constraints tc
  JOIN information_schema.key_column_usage kcu ON tc.constraint_name=kcu.constraint_name AND tc.table_schema=kcu.table_schema
  WHERE tc.constraint_type='FOREIGN KEY' AND tc.table_schema='public' AND tc.table_name='test_specifications' AND kcu.column_name='edited_by_id';
  IF fk_name IS NOT NULL THEN
    EXECUTE 'ALTER TABLE test_specifications DROP CONSTRAINT '||quote_ident(fk_name);
    EXECUTE 'ALTER TABLE test_specifications ADD CONSTRAINT '||quote_ident(fk_name)||' FOREIGN KEY (edited_by_id) REFERENCES users(id) ON DELETE CASCADE';
  END IF;
END$$;

DO $$ DECLARE fk_name text; BEGIN
  SELECT tc.constraint_name INTO fk_name FROM information_schema.table_constraints tc
  JOIN information_schema.key_column_usage kcu ON tc.constraint_name=kcu.constraint_name AND tc.table_schema=kcu.table_schema
  WHERE tc.constraint_type='FOREIGN KEY' AND tc.table_schema='public' AND tc.table_name='test_specifications_history' AND kcu.column_name='created_by_id';
  IF fk_name IS NOT NULL THEN
    EXECUTE 'ALTER TABLE test_specifications_history DROP CONSTRAINT '||quote_ident(fk_name);
    EXECUTE 'ALTER TABLE test_specifications_history ADD CONSTRAINT '||quote_ident(fk_name)||' FOREIGN KEY (created_by_id) REFERENCES users(id) ON DELETE CASCADE';
  END IF;
END$$;

DO $$ DECLARE fk_name text; BEGIN
  SELECT tc.constraint_name INTO fk_name FROM information_schema.table_constraints tc
  JOIN information_schema.key_column_usage kcu ON tc.constraint_name=kcu.constraint_name AND tc.table_schema=kcu.table_schema
  WHERE tc.constraint_type='FOREIGN KEY' AND tc.table_schema='public' AND tc.table_name='test_specifications_history' AND kcu.column_name='edited_by_id';
  IF fk_name IS NOT NULL THEN
    EXECUTE 'ALTER TABLE test_specifications_history DROP CONSTRAINT '||quote_ident(fk_name);
    EXECUTE 'ALTER TABLE test_specifications_history ADD CONSTRAINT '||quote_ident(fk_name)||' FOREIGN KEY (edited_by_id) REFERENCES users(id) ON DELETE CASCADE';
  END IF;
END$$;

-- test_runs.* -> apis/test_run_configs/users
DO $$ DECLARE fk_name text; BEGIN
  SELECT tc.constraint_name INTO fk_name FROM information_schema.table_constraints tc
  JOIN information_schema.key_column_usage kcu ON tc.constraint_name=kcu.constraint_name AND tc.table_schema=kcu.table_schema
  WHERE tc.constraint_type='FOREIGN KEY' AND tc.table_schema='public' AND tc.table_name='test_runs' AND kcu.column_name='api_id';
  IF fk_name IS NOT NULL THEN
    EXECUTE 'ALTER TABLE test_runs DROP CONSTRAINT '||quote_ident(fk_name);
    EXECUTE 'ALTER TABLE test_runs ADD CONSTRAINT '||quote_ident(fk_name)||' FOREIGN KEY (api_id) REFERENCES apis(id) ON DELETE CASCADE';
  END IF;
END$$;

DO $$ DECLARE fk_name text; BEGIN
  SELECT tc.constraint_name INTO fk_name FROM information_schema.table_constraints tc
  JOIN information_schema.key_column_usage kcu ON tc.constraint_name=kcu.constraint_name AND tc.table_schema=kcu.table_schema
  WHERE tc.constraint_type='FOREIGN KEY' AND tc.table_schema='public' AND tc.table_name='test_runs' AND kcu.column_name='test_run_config_id';
  IF fk_name IS NOT NULL THEN
    EXECUTE 'ALTER TABLE test_runs DROP CONSTRAINT '||quote_ident(fk_name);
    EXECUTE 'ALTER TABLE test_runs ADD CONSTRAINT '||quote_ident(fk_name)||' FOREIGN KEY (test_run_config_id) REFERENCES test_run_configs(id) ON DELETE CASCADE';
  END IF;
END$$;

DO $$ DECLARE fk_name text; BEGIN
  SELECT tc.constraint_name INTO fk_name FROM information_schema.table_constraints tc
  JOIN information_schema.key_column_usage kcu ON tc.constraint_name=kcu.constraint_name AND tc.table_schema=kcu.table_schema
  WHERE tc.constraint_type='FOREIGN KEY' AND tc.table_schema='public' AND tc.table_name='test_runs' AND kcu.column_name='created_by_id';
  IF fk_name IS NOT NULL THEN
    EXECUTE 'ALTER TABLE test_runs DROP CONSTRAINT '||quote_ident(fk_name);
    EXECUTE 'ALTER TABLE test_runs ADD CONSTRAINT '||quote_ident(fk_name)||' FOREIGN KEY (created_by_id) REFERENCES users(id) ON DELETE CASCADE';
  END IF;
END$$;

-- test_run_configs.* -> ssh_keys/users
DO $$ DECLARE fk_name text; BEGIN
  SELECT tc.constraint_name INTO fk_name FROM information_schema.table_constraints tc
  JOIN information_schema.key_column_usage kcu ON tc.constraint_name=kcu.constraint_name AND tc.table_schema=kcu.table_schema
  WHERE tc.constraint_type='FOREIGN KEY' AND tc.table_schema='public' AND tc.table_name='test_run_configs' AND kcu.column_name='ssh_key_id';
  IF fk_name IS NOT NULL THEN
    EXECUTE 'ALTER TABLE test_run_configs DROP CONSTRAINT '||quote_ident(fk_name);
    EXECUTE 'ALTER TABLE test_run_configs ADD CONSTRAINT '||quote_ident(fk_name)||' FOREIGN KEY (ssh_key_id) REFERENCES ssh_keys(id) ON DELETE CASCADE';
  END IF;
END$$;

DO $$ DECLARE fk_name text; BEGIN
  SELECT tc.constraint_name INTO fk_name FROM information_schema.table_constraints tc
  JOIN information_schema.key_column_usage kcu ON tc.constraint_name=kcu.constraint_name AND tc.table_schema=kcu.table_schema
  WHERE tc.constraint_type='FOREIGN KEY' AND tc.table_schema='public' AND tc.table_name='test_run_configs' AND kcu.column_name='created_by_id';
  IF fk_name IS NOT NULL THEN
    EXECUTE 'ALTER TABLE test_run_configs DROP CONSTRAINT '||quote_ident(fk_name);
    EXECUTE 'ALTER TABLE test_run_configs ADD CONSTRAINT '||quote_ident(fk_name)||' FOREIGN KEY (created_by_id) REFERENCES users(id) ON DELETE CASCADE';
  END IF;
END$$;

-- document_mapping_document.* -> document_mapping_api/document_mapping_document/documents/users
DO $$ DECLARE fk_name text; BEGIN
  SELECT tc.constraint_name INTO fk_name FROM information_schema.table_constraints tc
  JOIN information_schema.key_column_usage kcu ON tc.constraint_name=kcu.constraint_name AND tc.table_schema=kcu.table_schema
  WHERE tc.constraint_type='FOREIGN KEY' AND tc.table_schema='public' AND tc.table_name='document_mapping_document' AND kcu.column_name='document_mapping_api_id';
  IF fk_name IS NOT NULL THEN
    EXECUTE 'ALTER TABLE document_mapping_document DROP CONSTRAINT '||quote_ident(fk_name);
    EXECUTE 'ALTER TABLE document_mapping_document ADD CONSTRAINT '||quote_ident(fk_name)||' FOREIGN KEY (document_mapping_api_id) REFERENCES document_mapping_api(id) ON DELETE CASCADE';
  END IF;
END$$;

DO $$ DECLARE fk_name text; BEGIN
  SELECT tc.constraint_name INTO fk_name FROM information_schema.table_constraints tc
  JOIN information_schema.key_column_usage kcu ON tc.constraint_name=kcu.constraint_name AND tc.table_schema=kcu.table_schema
  WHERE tc.constraint_type='FOREIGN KEY' AND tc.table_schema='public' AND tc.table_name='document_mapping_document' AND kcu.column_name='document_mapping_document_id';
  IF fk_name IS NOT NULL THEN
    EXECUTE 'ALTER TABLE document_mapping_document DROP CONSTRAINT '||quote_ident(fk_name);
    EXECUTE 'ALTER TABLE document_mapping_document ADD CONSTRAINT '||quote_ident(fk_name)||' FOREIGN KEY (document_mapping_document_id) REFERENCES document_mapping_document(id) ON DELETE CASCADE';
  END IF;
END$$;

DO $$ DECLARE fk_name text; BEGIN
  SELECT tc.constraint_name INTO fk_name FROM information_schema.table_constraints tc
  JOIN information_schema.key_column_usage kcu ON tc.constraint_name=kcu.constraint_name AND tc.table_schema=kcu.table_schema
  WHERE tc.constraint_type='FOREIGN KEY' AND tc.table_schema='public' AND tc.table_name='document_mapping_document' AND kcu.column_name='document_id';
  IF fk_name IS NOT NULL THEN
    EXECUTE 'ALTER TABLE document_mapping_document DROP CONSTRAINT '||quote_ident(fk_name);
    EXECUTE 'ALTER TABLE document_mapping_document ADD CONSTRAINT '||quote_ident(fk_name)||' FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE';
  END IF;
END$$;

DO $$ DECLARE fk_name text; BEGIN
  SELECT tc.constraint_name INTO fk_name FROM information_schema.table_constraints tc
  JOIN information_schema.key_column_usage kcu ON tc.constraint_name=kcu.constraint_name AND tc.table_schema=kcu.table_schema
  WHERE tc.constraint_type='FOREIGN KEY' AND tc.table_schema='public' AND tc.table_name='document_mapping_document' AND kcu.column_name='created_by_id';
  IF fk_name IS NOT NULL THEN
    EXECUTE 'ALTER TABLE document_mapping_document DROP CONSTRAINT '||quote_ident(fk_name);
    EXECUTE 'ALTER TABLE document_mapping_document ADD CONSTRAINT '||quote_ident(fk_name)||' FOREIGN KEY (created_by_id) REFERENCES users(id) ON DELETE CASCADE';
  END IF;
END$$;

DO $$ DECLARE fk_name text; BEGIN
  SELECT tc.constraint_name INTO fk_name FROM information_schema.table_constraints tc
  JOIN information_schema.key_column_usage kcu ON tc.constraint_name=kcu.constraint_name AND tc.table_schema=kcu.table_schema
  WHERE tc.constraint_type='FOREIGN KEY' AND tc.table_schema='public' AND tc.table_name='document_mapping_document' AND kcu.column_name='edited_by_id';
  IF fk_name IS NOT NULL THEN
    EXECUTE 'ALTER TABLE document_mapping_document DROP CONSTRAINT '||quote_ident(fk_name);
    EXECUTE 'ALTER TABLE document_mapping_document ADD CONSTRAINT '||quote_ident(fk_name)||' FOREIGN KEY (edited_by_id) REFERENCES users(id) ON DELETE CASCADE';
  END IF;
END$$;

-- document_mapping_document_history.* -> mapping_api/mapping_document/documents/users
DO $$ DECLARE fk_name text; BEGIN
  SELECT tc.constraint_name INTO fk_name FROM information_schema.table_constraints tc
  JOIN information_schema.key_column_usage kcu ON tc.constraint_name=kcu.constraint_name AND tc.table_schema=kcu.table_schema
  WHERE tc.constraint_type='FOREIGN KEY' AND tc.table_schema='public' AND tc.table_name='document_mapping_document_history' AND kcu.column_name='document_mapping_api_id';
  IF fk_name IS NOT NULL THEN
    EXECUTE 'ALTER TABLE document_mapping_document_history DROP CONSTRAINT '||quote_ident(fk_name);
    EXECUTE 'ALTER TABLE document_mapping_document_history ADD CONSTRAINT '||quote_ident(fk_name)||' FOREIGN KEY (document_mapping_api_id) REFERENCES document_mapping_api(id) ON DELETE CASCADE';
  END IF;
END$$;

DO $$ DECLARE fk_name text; BEGIN
  SELECT tc.constraint_name INTO fk_name FROM information_schema.table_constraints tc
  JOIN information_schema.key_column_usage kcu ON tc.constraint_name=kcu.constraint_name AND tc.table_schema=kcu.table_schema
  WHERE tc.constraint_type='FOREIGN KEY' AND tc.table_schema='public' AND tc.table_name='document_mapping_document_history' AND kcu.column_name='document_mapping_document_id';
  IF fk_name IS NOT NULL THEN
    EXECUTE 'ALTER TABLE document_mapping_document_history DROP CONSTRAINT '||quote_ident(fk_name);
    EXECUTE 'ALTER TABLE document_mapping_document_history ADD CONSTRAINT '||quote_ident(fk_name)||' FOREIGN KEY (document_mapping_document_id) REFERENCES document_mapping_document(id) ON DELETE CASCADE';
  END IF;
END$$;

DO $$ DECLARE fk_name text; BEGIN
  SELECT tc.constraint_name INTO fk_name FROM information_schema.table_constraints tc
  JOIN information_schema.key_column_usage kcu ON tc.constraint_name=kcu.constraint_name AND tc.table_schema=kcu.table_schema
  WHERE tc.constraint_type='FOREIGN KEY' AND tc.table_schema='public' AND tc.table_name='document_mapping_document_history' AND kcu.column_name='document_id';
  IF fk_name IS NOT NULL THEN
    EXECUTE 'ALTER TABLE document_mapping_document_history DROP CONSTRAINT '||quote_ident(fk_name);
    EXECUTE 'ALTER TABLE document_mapping_document_history ADD CONSTRAINT '||quote_ident(fk_name)||' FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE';
  END IF;
END$$;

DO $$ DECLARE fk_name text; BEGIN
  SELECT tc.constraint_name INTO fk_name FROM information_schema.table_constraints tc
  JOIN information_schema.key_column_usage kcu ON tc.constraint_name=kcu.constraint_name AND tc.table_schema=kcu.table_schema
  WHERE tc.constraint_type='FOREIGN KEY' AND tc.table_schema='public' AND tc.table_name='document_mapping_document_history' AND kcu.column_name='created_by_id';
  IF fk_name IS NOT NULL THEN
    EXECUTE 'ALTER TABLE document_mapping_document_history DROP CONSTRAINT '||quote_ident(fk_name);
    EXECUTE 'ALTER TABLE document_mapping_document_history ADD CONSTRAINT '||quote_ident(fk_name)||' FOREIGN KEY (created_by_id) REFERENCES users(id) ON DELETE CASCADE';
  END IF;
END$$;

DO $$ DECLARE fk_name text; BEGIN
  SELECT tc.constraint_name INTO fk_name FROM information_schema.table_constraints tc
  JOIN information_schema.key_column_usage kcu ON tc.constraint_name=kcu.constraint_name AND tc.table_schema=kcu.table_schema
  WHERE tc.constraint_type='FOREIGN KEY' AND tc.table_schema='public' AND tc.table_name='document_mapping_document_history' AND kcu.column_name='edited_by_id';
  IF fk_name IS NOT NULL THEN
    EXECUTE 'ALTER TABLE document_mapping_document_history DROP CONSTRAINT '||quote_ident(fk_name);
    EXECUTE 'ALTER TABLE document_mapping_document_history ADD CONSTRAINT '||quote_ident(fk_name)||' FOREIGN KEY (edited_by_id) REFERENCES users(id) ON DELETE CASCADE';
  END IF;
END$$;

-- api_* mapping tables
DO $$ DECLARE fk_name text; BEGIN
  SELECT tc.constraint_name INTO fk_name FROM information_schema.table_constraints tc
  JOIN information_schema.key_column_usage kcu ON tc.constraint_name=kcu.constraint_name AND tc.table_schema=kcu.table_schema
  WHERE tc.constraint_type='FOREIGN KEY' AND tc.table_schema='public' AND tc.table_name='test_case_mapping_api' AND kcu.column_name='api_id';
  IF fk_name IS NOT NULL THEN
    EXECUTE 'ALTER TABLE test_case_mapping_api DROP CONSTRAINT '||quote_ident(fk_name);
    EXECUTE 'ALTER TABLE test_case_mapping_api ADD CONSTRAINT '||quote_ident(fk_name)||' FOREIGN KEY (api_id) REFERENCES apis(id) ON DELETE CASCADE';
  END IF;
END$$;

DO $$ DECLARE fk_name text; BEGIN
  SELECT tc.constraint_name INTO fk_name FROM information_schema.table_constraints tc
  JOIN information_schema.key_column_usage kcu ON tc.constraint_name=kcu.constraint_name AND tc.table_schema=kcu.table_schema
  WHERE tc.constraint_type='FOREIGN KEY' AND tc.table_schema='public' AND tc.table_name='test_case_mapping_api' AND kcu.column_name='test_case_id';
  IF fk_name IS NOT NULL THEN
    EXECUTE 'ALTER TABLE test_case_mapping_api DROP CONSTRAINT '||quote_ident(fk_name);
    EXECUTE 'ALTER TABLE test_case_mapping_api ADD CONSTRAINT '||quote_ident(fk_name)||' FOREIGN KEY (test_case_id) REFERENCES test_cases(id) ON DELETE CASCADE';
  END IF;
END$$;

-- api_test_specification
DO $$ DECLARE fk_name text; BEGIN
  SELECT tc.constraint_name INTO fk_name FROM information_schema.table_constraints tc
  JOIN information_schema.key_column_usage kcu ON tc.constraint_name=kcu.constraint_name AND tc.table_schema=kcu.table_schema
  WHERE tc.constraint_type='FOREIGN KEY' AND tc.table_schema='public' AND tc.table_name='test_specification_mapping_api' AND kcu.column_name='api_id';
  IF fk_name IS NOT NULL THEN
    EXECUTE 'ALTER TABLE test_specification_mapping_api DROP CONSTRAINT '||quote_ident(fk_name);
    EXECUTE 'ALTER TABLE test_specification_mapping_api ADD CONSTRAINT '||quote_ident(fk_name)||' FOREIGN KEY (api_id) REFERENCES apis(id) ON DELETE CASCADE';
  END IF;
END$$;

DO $$ DECLARE fk_name text; BEGIN
  SELECT tc.constraint_name INTO fk_name FROM information_schema.table_constraints tc
  JOIN information_schema.key_column_usage kcu ON tc.constraint_name=kcu.constraint_name AND tc.table_schema=kcu.table_schema
  WHERE tc.constraint_type='FOREIGN KEY' AND tc.table_schema='public' AND tc.table_name='test_specification_mapping_api' AND kcu.column_name='test_specification_id';
  IF fk_name IS NOT NULL THEN
    EXECUTE 'ALTER TABLE test_specification_mapping_api DROP CONSTRAINT '||quote_ident(fk_name);
    EXECUTE 'ALTER TABLE test_specification_mapping_api ADD CONSTRAINT '||quote_ident(fk_name)||' FOREIGN KEY (test_specification_id) REFERENCES test_specifications(id) ON DELETE CASCADE';
  END IF;
END$$;

-- api_justification
DO $$ DECLARE fk_name text; BEGIN
  SELECT tc.constraint_name INTO fk_name FROM information_schema.table_constraints tc
  JOIN information_schema.key_column_usage kcu ON tc.constraint_name=kcu.constraint_name AND tc.table_schema=kcu.table_schema
  WHERE tc.constraint_type='FOREIGN KEY' AND tc.table_schema='public' AND tc.table_name='justification_mapping_api' AND kcu.column_name='api_id';
  IF fk_name IS NOT NULL THEN
    EXECUTE 'ALTER TABLE justification_mapping_api DROP CONSTRAINT '||quote_ident(fk_name);
    EXECUTE 'ALTER TABLE justification_mapping_api ADD CONSTRAINT '||quote_ident(fk_name)||' FOREIGN KEY (api_id) REFERENCES apis(id) ON DELETE CASCADE';
  END IF;
END$$;

DO $$ DECLARE fk_name text; BEGIN
  SELECT tc.constraint_name INTO fk_name FROM information_schema.table_constraints tc
  JOIN information_schema.key_column_usage kcu ON tc.constraint_name=kcu.constraint_name AND tc.table_schema=kcu.table_schema
  WHERE tc.constraint_type='FOREIGN KEY' AND tc.table_schema='public' AND tc.table_name='justification_mapping_api' AND kcu.column_name='justification_id';
  IF fk_name IS NOT NULL THEN
    EXECUTE 'ALTER TABLE justification_mapping_api DROP CONSTRAINT '||quote_ident(fk_name);
    EXECUTE 'ALTER TABLE justification_mapping_api ADD CONSTRAINT '||quote_ident(fk_name)||' FOREIGN KEY (justification_id) REFERENCES justifications(id) ON DELETE CASCADE';
  END IF;
END$$;

-- comments.created_by_id
DO $$ DECLARE fk_name text; BEGIN
  SELECT tc.constraint_name INTO fk_name FROM information_schema.table_constraints tc
  JOIN information_schema.key_column_usage kcu ON tc.constraint_name=kcu.constraint_name AND tc.table_schema=kcu.table_schema
  WHERE tc.constraint_type='FOREIGN KEY' AND tc.table_schema='public' AND tc.table_name='comments' AND kcu.column_name='created_by_id';
  IF fk_name IS NOT NULL THEN
    EXECUTE 'ALTER TABLE comments DROP CONSTRAINT '||quote_ident(fk_name);
    EXECUTE 'ALTER TABLE comments ADD CONSTRAINT '||quote_ident(fk_name)||' FOREIGN KEY (created_by_id) REFERENCES users(id) ON DELETE CASCADE';
  END IF;
END$$;

-- notifications.api_id
DO $$ DECLARE fk_name text; BEGIN
  SELECT tc.constraint_name INTO fk_name FROM information_schema.table_constraints tc
  JOIN information_schema.key_column_usage kcu ON tc.constraint_name=kcu.constraint_name AND tc.table_schema=kcu.table_schema
  WHERE tc.constraint_type='FOREIGN KEY' AND tc.table_schema='public' AND tc.table_name='notifications' AND kcu.column_name='api_id';
  IF fk_name IS NOT NULL THEN
    EXECUTE 'ALTER TABLE notifications DROP CONSTRAINT '||quote_ident(fk_name);
    EXECUTE 'ALTER TABLE notifications ADD CONSTRAINT '||quote_ident(fk_name)||' FOREIGN KEY (api_id) REFERENCES apis(id) ON DELETE CASCADE';
  END IF;
END$$;

-- ssh_keys.created_by_id
DO $$ DECLARE fk_name text; BEGIN
  SELECT tc.constraint_name INTO fk_name FROM information_schema.table_constraints tc
  JOIN information_schema.key_column_usage kcu ON tc.constraint_name=kcu.constraint_name AND tc.table_schema=kcu.table_schema
  WHERE tc.constraint_type='FOREIGN KEY' AND tc.table_schema='public' AND tc.table_name='ssh_keys' AND kcu.column_name='created_by_id';
  IF fk_name IS NOT NULL THEN
    EXECUTE 'ALTER TABLE ssh_keys DROP CONSTRAINT '||quote_ident(fk_name);
    EXECUTE 'ALTER TABLE ssh_keys ADD CONSTRAINT '||quote_ident(fk_name)||' FOREIGN KEY (created_by_id) REFERENCES users(id) ON DELETE CASCADE';
  END IF;
END$$;

-- sw_requirement_mapping_api_history.* -> users
DO $$ DECLARE fk_name text; BEGIN
  SELECT tc.constraint_name INTO fk_name FROM information_schema.table_constraints tc
  JOIN information_schema.key_column_usage kcu ON tc.constraint_name=kcu.constraint_name AND tc.table_schema=kcu.table_schema
  WHERE tc.constraint_type='FOREIGN KEY' AND tc.table_schema='public' AND tc.table_name='sw_requirement_mapping_api_history' AND kcu.column_name='created_by_id';
  IF fk_name IS NOT NULL THEN
    EXECUTE 'ALTER TABLE sw_requirement_mapping_api_history DROP CONSTRAINT '||quote_ident(fk_name);
    EXECUTE 'ALTER TABLE sw_requirement_mapping_api_history ADD CONSTRAINT '||quote_ident(fk_name)||' FOREIGN KEY (created_by_id) REFERENCES users(id) ON DELETE CASCADE';
  END IF;
END$$;

DO $$ DECLARE fk_name text; BEGIN
  SELECT tc.constraint_name INTO fk_name FROM information_schema.table_constraints tc
  JOIN information_schema.key_column_usage kcu ON tc.constraint_name=kcu.constraint_name AND tc.table_schema=kcu.table_schema
  WHERE tc.constraint_type='FOREIGN KEY' AND tc.table_schema='public' AND tc.table_name='sw_requirement_mapping_api_history' AND kcu.column_name='edited_by_id';
  IF fk_name IS NOT NULL THEN
    EXECUTE 'ALTER TABLE sw_requirement_mapping_api_history DROP CONSTRAINT '||quote_ident(fk_name);
    EXECUTE 'ALTER TABLE sw_requirement_mapping_api_history ADD CONSTRAINT '||quote_ident(fk_name)||' FOREIGN KEY (edited_by_id) REFERENCES users(id) ON DELETE CASCADE';
  END IF;
END$$;

-- sw_requirement_mapping_sw_requirement_history.* -> users
DO $$ DECLARE fk_name text; BEGIN
  SELECT tc.constraint_name INTO fk_name FROM information_schema.table_constraints tc
  JOIN information_schema.key_column_usage kcu ON tc.constraint_name=kcu.constraint_name AND tc.table_schema=kcu.table_schema
  WHERE tc.constraint_type='FOREIGN KEY' AND tc.table_schema='public' AND tc.table_name='sw_requirement_mapping_sw_requirement_history' AND kcu.column_name='created_by_id';
  IF fk_name IS NOT NULL THEN
    EXECUTE 'ALTER TABLE sw_requirement_mapping_sw_requirement_history DROP CONSTRAINT '||quote_ident(fk_name);
    EXECUTE 'ALTER TABLE sw_requirement_mapping_sw_requirement_history ADD CONSTRAINT '||quote_ident(fk_name)||' FOREIGN KEY (created_by_id) REFERENCES users(id) ON DELETE CASCADE';
  END IF;
END$$;

DO $$ DECLARE fk_name text; BEGIN
  SELECT tc.constraint_name INTO fk_name FROM information_schema.table_constraints tc
  JOIN information_schema.key_column_usage kcu ON tc.constraint_name=kcu.constraint_name AND tc.table_schema=kcu.table_schema
  WHERE tc.constraint_type='FOREIGN KEY' AND tc.table_schema='public' AND tc.table_name='sw_requirement_mapping_sw_requirement_history' AND kcu.column_name='edited_by_id';
  IF fk_name IS NOT NULL THEN
    EXECUTE 'ALTER TABLE sw_requirement_mapping_sw_requirement_history DROP CONSTRAINT '||quote_ident(fk_name);
    EXECUTE 'ALTER TABLE sw_requirement_mapping_sw_requirement_history ADD CONSTRAINT '||quote_ident(fk_name)||' FOREIGN KEY (edited_by_id) REFERENCES users(id) ON DELETE CASCADE';
  END IF;
END$$;

-- test_case_mapping_api_history.* -> users
DO $$ DECLARE fk_name text; BEGIN
  SELECT tc.constraint_name INTO fk_name FROM information_schema.table_constraints tc
  JOIN information_schema.key_column_usage kcu ON tc.constraint_name=kcu.constraint_name AND tc.table_schema=kcu.table_schema
  WHERE tc.constraint_type='FOREIGN KEY' AND tc.table_schema='public' AND tc.table_name='test_case_mapping_api_history' AND kcu.column_name='created_by_id';
  IF fk_name IS NOT NULL THEN
    EXECUTE 'ALTER TABLE test_case_mapping_api_history DROP CONSTRAINT '||quote_ident(fk_name);
    EXECUTE 'ALTER TABLE test_case_mapping_api_history ADD CONSTRAINT '||quote_ident(fk_name)||' FOREIGN KEY (created_by_id) REFERENCES users(id) ON DELETE CASCADE';
  END IF;
END$$;

DO $$ DECLARE fk_name text; BEGIN
  SELECT tc.constraint_name INTO fk_name FROM information_schema.table_constraints tc
  JOIN information_schema.key_column_usage kcu ON tc.constraint_name=kcu.constraint_name AND tc.table_schema=kcu.table_schema
  WHERE tc.constraint_type='FOREIGN KEY' AND tc.table_schema='public' AND tc.table_name='test_case_mapping_api_history' AND kcu.column_name='edited_by_id';
  IF fk_name IS NOT NULL THEN
    EXECUTE 'ALTER TABLE test_case_mapping_api_history DROP CONSTRAINT '||quote_ident(fk_name);
    EXECUTE 'ALTER TABLE test_case_mapping_api_history ADD CONSTRAINT '||quote_ident(fk_name)||' FOREIGN KEY (edited_by_id) REFERENCES users(id) ON DELETE CASCADE';
  END IF;
END$$;

-- test_specification_mapping_api_history.* -> users
DO $$ DECLARE fk_name text; BEGIN
  SELECT tc.constraint_name INTO fk_name FROM information_schema.table_constraints tc
  JOIN information_schema.key_column_usage kcu ON tc.constraint_name=kcu.constraint_name AND tc.table_schema=kcu.table_schema
  WHERE tc.constraint_type='FOREIGN KEY' AND tc.table_schema='public' AND tc.table_name='test_specification_mapping_api_history' AND kcu.column_name='created_by_id';
  IF fk_name IS NOT NULL THEN
    EXECUTE 'ALTER TABLE test_specification_mapping_api_history DROP CONSTRAINT '||quote_ident(fk_name);
    EXECUTE 'ALTER TABLE test_specification_mapping_api_history ADD CONSTRAINT '||quote_ident(fk_name)||' FOREIGN KEY (created_by_id) REFERENCES users(id) ON DELETE CASCADE';
  END IF;
END$$;

DO $$ DECLARE fk_name text; BEGIN
  SELECT tc.constraint_name INTO fk_name FROM information_schema.table_constraints tc
  JOIN information_schema.key_column_usage kcu ON tc.constraint_name=kcu.constraint_name AND tc.table_schema=kcu.table_schema
  WHERE tc.constraint_type='FOREIGN KEY' AND tc.table_schema='public' AND tc.table_name='test_specification_mapping_api_history' AND kcu.column_name='edited_by_id';
  IF fk_name IS NOT NULL THEN
    EXECUTE 'ALTER TABLE test_specification_mapping_api_history DROP CONSTRAINT '||quote_ident(fk_name);
    EXECUTE 'ALTER TABLE test_specification_mapping_api_history ADD CONSTRAINT '||quote_ident(fk_name)||' FOREIGN KEY (edited_by_id) REFERENCES users(id) ON DELETE CASCADE';
  END IF;
END$$;

COMMIT;


