ALTER TABLE test_run_configs ADD COLUMN plugin VARCHAR(20) DEFAULT 'tmt';
ALTER TABLE test_run_configs ADD COLUMN plugin_preset VARCHAR(50) DEFAULT '';
ALTER TABLE test_run_configs ADD COLUMN plugin_vars VARCHAR DEFAULT '';
ALTER TABLE test_runs ADD COLUMN report VARCHAR DEFAULT '';
ALTER TABLE test_runs ADD COLUMN fixes VARCHAR DEFAULT '';
ALTER TABLE test_runs RENAME COLUMN note TO notes;