import os
import sys

import pytest

# Add parent directory to path for imports
currentdir = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(1, os.path.dirname(currentdir))

from testrun_tmt import TestRunnerTmtPlugin


class MockUser:
    def __init__(self, user_id, username="test_user"):
        self.id = str(user_id)
        self.username = username


class MockTestCase:
    def __init__(self, repository, relative_path, test_case_id=1):
        self.id = test_case_id
        self.repository = repository
        self.relative_path = relative_path
        self.title = f"Test Case {test_case_id}"


class MockApi:
    def __init__(self):
        self.api = "test_api"
        self.library = "test_library"
        self.library_version = "1.0.0"


class MockMapping:
    def __init__(self, test_case):
        self.test_case = test_case


class MockTestRun:
    def __init__(self, user, test_case, uid="test-run-001"):
        self.uid = uid
        self.id = 1
        self.title = "Test Run"
        self.created_by = user
        self.api = MockApi()
        self.mapping_to = "test_case_mapping"
        self.mapping_id = 1


class MockRunner:
    def __init__(self, user, test_case, config=None):
        self.db_test_run = MockTestRun(user, test_case)
        self.mapping = MockMapping(test_case)
        self.config = config or {
            "id": 1,
            "title": "Test Config",
            "provision_type": "container",
            "context_vars": "plan_type=local",
            "git_repo_ref": "",
            "basil_test_repo_path": test_case.repository,
            "basil_test_relative_path": test_case.relative_path,
        }
        self.STATUS_CREATED = "created"
        self.STATUS_ERROR = "error"
        self.RESULT_PASS = "pass"
        self.RESULT_FAIL = "fail"
        self.ssh_keys_dir = "/tmp/ssh_keys"  # Mock SSH keys directory

    def publish(self):
        """Mock publish method to update database (no-op for testing)"""
        pass


class TestTMTValidation:
    """Test TMT path validation for user folder access restrictions"""

    @pytest.fixture
    def basil_root_path(self):
        """Get the BASIL project root path"""
        # Calculate BASIL path (same logic as in testrun_tmt.py)
        current_file = os.path.abspath(__file__)
        return os.path.dirname(os.path.dirname(os.path.dirname(current_file)))

    @pytest.fixture
    def user_x(self):
        """Create user X with ID 100"""
        return MockUser(user_id=100, username="user_x")

    @pytest.fixture
    def user_y(self):
        """Create user Y with ID 200"""
        return MockUser(user_id=200, username="user_y")

    def test_user_cannot_access_other_user_folder(self, basil_root_path, user_x, user_y):
        """Test that User X cannot access User Y's folder"""

        # Create test case that points to User Y's folder
        user_y_test_path = os.path.join(basil_root_path, "api", "user-files", str(user_y.id))
        test_case = MockTestCase(repository=user_y_test_path, relative_path="test.fmf")

        # Create config with plan_type=local context
        config = {
            "id": 1,
            "title": "Test Config",
            "provision_type": "container",
            "context": {"plan_type": "local"},
            "git_repo_ref": "",
            "env": {
                "basil_test_repo_path": test_case.repository,
                "basil_test_relative_path": test_case.relative_path,
            },
        }

        # Create runner for User X trying to access User Y's files
        runner = MockRunner(user_x, test_case, config)

        # Attempt to create TMT plugin should fail validation
        with pytest.raises(SystemExit) as exc_info:
            TestRunnerTmtPlugin(runner=runner)

        # Should exit with validation error code (7)
        assert exc_info.value.code == 7

    def test_user_cannot_access_other_user_folder_with_path_traversal(self, basil_root_path, user_x, user_y):
        """Test that User X cannot access User Y's folder using ../ path traversal"""

        # Create test case with path traversal attempt
        user_x_path = os.path.join(basil_root_path, "api", "user-files", str(user_x.id))
        test_case = MockTestCase(
            repository=user_x_path,
            relative_path=f"../../{user_y.id}/malicious_test.fmf",  # Try to access user Y's folder
        )

        config = {
            "id": 1,
            "title": "Test Config",
            "provision_type": "container",
            "context": {"plan_type": "local"},
            "git_repo_ref": "",
            "env": {
                "basil_test_repo_path": test_case.repository,
                "basil_test_relative_path": test_case.relative_path,
            },
        }

        runner = MockRunner(user_x, test_case, config)

        # Should fail validation due to path traversal outside allowed directories
        with pytest.raises(SystemExit) as exc_info:
            TestRunnerTmtPlugin(runner=runner)

        assert exc_info.value.code == 7

    def test_user_can_access_own_folder(self, basil_root_path, user_x):
        """Test that User X can access their own folder"""

        # Create test case in User X's own folder
        user_x_path = os.path.join(basil_root_path, "api", "user-files", str(user_x.id))
        test_case = MockTestCase(repository=user_x_path, relative_path="valid_test.fmf")

        config = {
            "id": 1,
            "title": "Test Config",
            "provision_type": "container",
            "context": {"plan_type": "local"},
            "git_repo_ref": "",
            "env": {
                "basil_test_repo_path": test_case.repository,
                "basil_test_relative_path": test_case.relative_path,
            },
        }

        runner = MockRunner(user_x, test_case, config)

        # Should succeed - no exception raised
        try:
            plugin = TestRunnerTmtPlugin(runner=runner)
            assert plugin is not None
        except SystemExit:
            pytest.fail("User should be able to access their own folder")

    def test_user_can_access_basil_examples(self, basil_root_path, user_x):
        """Test that any user can access BASIL example files"""

        # Create test case pointing to BASIL examples/tmt/local
        basil_examples_path = os.path.join(basil_root_path, "examples", "tmt", "local")
        test_case = MockTestCase(repository=basil_examples_path, relative_path="tmt-dummy-test.fmf")

        config = {
            "id": 1,
            "title": "Test Config",
            "provision_type": "container",
            "context": {"plan_type": "local"},
            "git_repo_ref": "",
            "env": {
                "basil_test_repo_path": test_case.repository,
                "basil_test_relative_path": test_case.relative_path,
            },
        }

        runner = MockRunner(user_x, test_case, config)

        # Should succeed - examples are accessible to all users
        try:
            plugin = TestRunnerTmtPlugin(runner=runner)
            assert plugin is not None
        except SystemExit:
            pytest.fail("User should be able to access BASIL examples")

    def test_user_can_access_basil_examples_failing_test(self, basil_root_path, user_x):
        """Test that any user can access BASIL failing example test"""

        # Create test case pointing to BASIL failing example
        basil_examples_path = os.path.join(basil_root_path, "examples", "tmt", "local")
        test_case = MockTestCase(repository=basil_examples_path, relative_path="tmt-dummy-failing-test.fmf")

        config = {
            "id": 1,
            "title": "Test Config",
            "provision_type": "container",
            "context": {"plan_type": "local"},
            "git_repo_ref": "",
            "env": {
                "basil_test_repo_path": test_case.repository,
                "basil_test_relative_path": test_case.relative_path,
            },
        }

        runner = MockRunner(user_x, test_case, config)

        # Should succeed
        try:
            plugin = TestRunnerTmtPlugin(runner=runner)
            assert plugin is not None
        except SystemExit:
            pytest.fail("User should be able to access BASIL failing example")

    def test_validation_fails_with_missing_repo_path(self, user_x):
        """Test validation fails when basil_test_repo_path is missing"""

        test_case = MockTestCase(repository="", relative_path="test.fmf")

        config = {
            "id": 1,
            "title": "Test Config",
            "provision_type": "container",
            "context": {"plan_type": "local"},
            "git_repo_ref": "",
            "env": {
                "basil_test_repo_path": "",  # Empty repo path
                "basil_test_relative_path": test_case.relative_path,
            },
        }

        runner = MockRunner(user_x, test_case, config)

        with pytest.raises(SystemExit) as exc_info:
            TestRunnerTmtPlugin(runner=runner)

        assert exc_info.value.code == 7

    def test_validation_fails_with_missing_relative_path(self, basil_root_path, user_x):
        """Test validation fails when basil_test_relative_path is missing"""

        user_x_path = os.path.join(basil_root_path, "api", "user-files", str(user_x.id))
        test_case = MockTestCase(repository=user_x_path, relative_path="")

        config = {
            "id": 1,
            "title": "Test Config",
            "provision_type": "container",
            "context": {"plan_type": "local"},
            "git_repo_ref": "",
            "env": {
                "basil_test_repo_path": test_case.repository,
                "basil_test_relative_path": "",  # Empty relative path
            },
        }

        runner = MockRunner(user_x, test_case, config)

        with pytest.raises(SystemExit) as exc_info:
            TestRunnerTmtPlugin(runner=runner)

        assert exc_info.value.code == 7

    def test_validation_passes_without_plan_type_local(self, basil_root_path, user_x, user_y):
        """Test that validation is skipped when plan_type=local is not in context"""

        # Create test case that would normally fail (accessing other user's folder)
        user_y_test_path = os.path.join(basil_root_path, "api", "user-files", str(user_y.id))
        test_case = MockTestCase(repository=user_y_test_path, relative_path="test.fmf")

        config = {
            "id": 1,
            "title": "Test Config",
            "provision_type": "container",
            "context": {"plan_type": "remote"},  # Not local, so validation should be skipped
            "git_repo_ref": "",
            "env": {
                "basil_test_repo_path": test_case.repository,
                "basil_test_relative_path": test_case.relative_path,
            },
        }

        runner = MockRunner(user_x, test_case, config)

        # Should succeed because validation is only for plan_type=local
        try:
            plugin = TestRunnerTmtPlugin(runner=runner)
            assert plugin is not None
        except SystemExit:
            pytest.fail("Validation should be skipped when not using plan_type=local")

    def test_absolute_path_resolution_prevents_traversal(self, basil_root_path, user_x):
        """Test that os.path.abspath prevents directory traversal attacks"""

        user_x_path = os.path.join(basil_root_path, "api", "user-files", str(user_x.id))

        # Attempt traversal with relative paths
        test_case = MockTestCase(
            repository=user_x_path, relative_path="../../../etc/passwd"  # Attempt to access system files
        )

        config = {
            "id": 1,
            "title": "Test Config",
            "provision_type": "container",
            "context": {"plan_type": "local"},
            "git_repo_ref": "",
            "env": {
                "basil_test_repo_path": test_case.repository,
                "basil_test_relative_path": test_case.relative_path,
            },
        }

        runner = MockRunner(user_x, test_case, config)

        # Should fail validation due to path outside allowed directories
        with pytest.raises(SystemExit) as exc_info:
            TestRunnerTmtPlugin(runner=runner)

        assert exc_info.value.code == 7
