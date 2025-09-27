import logging
import os
import pytest
import shutil
import tempfile
import time
import threading
from http import HTTPStatus
from db.models.user import UserModel
from db.models.api import ApiModel
from db.models.test_case import TestCaseModel
from db.models.api_test_case import ApiTestCaseModel
from db.models.test_run import TestRunModel
from db.models.test_run_config import TestRunConfigModel
from conftest import UT_USER_EMAIL

# BASIL project root path - full path
BASIL_PROJECT_ROOT = "/BASIL-API"

# Test file paths relative to project root
TMT_PASSING_TEST_PATH = "examples/tmt/local/tmt-dummy-test"
TMT_FAILING_TEST_PATH = "examples/tmt/local/tmt-dummy-failing-test"

_UT_API_NAME = "ut_tmt_api"
_UT_API_LIBRARY = "ut_tmt_library"
_UT_API_LIBRARY_VERSION = "v1.0.0"
_UT_API_CATEGORY = "ut_tmt_category"
_UT_API_IMPLEMENTATION_FILE_FROM_ROW = 0
_UT_API_IMPLEMENTATION_FILE_TO_ROW = 42
_UT_API_TAGS = "tmt,test,infrastructure"

_UT_API_SPEC_CONTENT = """
# TMT Test Infrastructure API Specification

## Section 1: Test Execution
The API shall support TMT test execution framework.

## Section 2: Test Configuration
The API shall provide configurable test environments.

## Section 3: Container Support
The API shall support container-based test execution.

## Section 4: Test Results
The API shall capture and report test results.
"""

# Test timeout in seconds
TEST_TIMEOUT_SECONDS = 10 * 60

# Set up logging for test execution tracking
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class TestTimeoutError(Exception):
    """Exception raised when a test exceeds the timeout"""

    pass


def timeout_handler(test_function, timeout_seconds, *args, **kwargs):
    """
    Run a test function with a timeout.
    Raises TestTimeoutError if the test exceeds the timeout.
    """
    result = [None]
    exception = [None]

    def target():
        try:
            result[0] = test_function(*args, **kwargs)
        except Exception as e:
            exception[0] = e

    thread = threading.Thread(target=target)
    thread.daemon = True
    thread.start()
    thread.join(timeout=timeout_seconds)

    if thread.is_alive():
        # Thread is still running, test timed out
        raise TestTimeoutError(f"Test timed out after {timeout_seconds} seconds")

    if exception[0]:
        raise exception[0]

    return result[0]


def get_test_case_model(client_db, utilities, title_suffix="", test_path=""):
    """Helper to create a test case model for TMT tests"""
    user = client_db.session.query(UserModel).filter(UserModel.email == UT_USER_EMAIL).one()
    return TestCaseModel(
        repository=BASIL_PROJECT_ROOT,
        relative_path=test_path,
        title=f"TMT Test Case {title_suffix}#{utilities.generate_random_hex_string8()}",
        description=f"TMT test case for {test_path}",
        created_by=user,
    )


def get_test_run_config_model(client_db, utilities):
    """Helper to create a TMT test run config model with specified settings"""
    user = client_db.session.query(UserModel).filter(UserModel.email == UT_USER_EMAIL).one()
    return TestRunConfigModel(
        plugin="tmt",
        plugin_preset="",
        plugin_vars="",
        title="local test run config",
        git_repo_ref="",
        context_vars="plan_type=local",
        environment_vars="",
        provision_type="container",
        provision_guest="",
        provision_guest_port="",
        ssh_key=None,
        created_by=user,
    )


def create_tmt_test_setup(client_db, utilities, test_case_title_suffix, test_path, section_name, section_coverage):
    """Shared helper to create TMT test setup - reduces fixture duplication"""
    user = client_db.session.query(UserModel).filter(UserModel.email == UT_USER_EMAIL).one()

    # Create raw API specification file
    raw_spec = tempfile.NamedTemporaryFile(mode="w", delete=False)
    raw_spec.write(_UT_API_SPEC_CONTENT)
    raw_spec.close()

    # Create API
    ut_api = ApiModel(
        _UT_API_NAME + "#" + utilities.generate_random_hex_string8(),
        _UT_API_LIBRARY,
        _UT_API_LIBRARY_VERSION,
        raw_spec.name,
        _UT_API_CATEGORY,
        utilities.generate_random_hex_string8(),
        raw_spec.name + "impl",
        _UT_API_IMPLEMENTATION_FILE_FROM_ROW,
        _UT_API_IMPLEMENTATION_FILE_TO_ROW,
        _UT_API_TAGS,
        user,
    )

    # Create Test Case
    test_case = get_test_case_model(client_db, utilities, test_case_title_suffix, test_path)

    # Create Test Run Config
    test_run_config = get_test_run_config_model(client_db, utilities)

    # Add all entities to session
    entities = [ut_api, test_case, test_run_config]
    for entity in entities:
        client_db.session.add(entity)
    client_db.session.commit()

    # Create API-Test Case mapping (assign to snippet of API reference document)
    api_tc_mapping = ApiTestCaseModel(
        ut_api,
        test_case,
        section_name,  # Section from API spec
        _UT_API_SPEC_CONTENT.find(section_name),  # Offset
        section_coverage,  # Coverage percentage
        user,
    )

    client_db.session.add(api_tc_mapping)
    client_db.session.commit()

    return {
        "api": ut_api,
        "test_case": test_case,
        "test_run_config": test_run_config,
        "api_tc_mapping": api_tc_mapping,
        "raw_spec_path": raw_spec.name,
        "user": user,
    }


@pytest.fixture()
def tmt_test_setup_passing(client_db, ut_user_db, utilities):
    """Create test setup for TMT passing test"""
    test_data = create_tmt_test_setup(
        client_db, utilities, "Passing", TMT_PASSING_TEST_PATH, "## Section 1: Test Execution", 95
    )

    yield test_data

    # Cleanup: remove the raw_spec tempfile
    if os.path.isfile(test_data["raw_spec_path"]):
        os.remove(test_data["raw_spec_path"])


@pytest.fixture()
def tmt_test_setup_failing(client_db, ut_user_db, utilities):
    """Create test setup for TMT failing test"""
    test_data = create_tmt_test_setup(
        client_db, utilities, "Failing", TMT_FAILING_TEST_PATH, "## Section 2: Test Configuration", 90
    )

    yield test_data

    # Cleanup: remove the raw_spec tempfile
    if os.path.isfile(test_data["raw_spec_path"]):
        os.remove(test_data["raw_spec_path"])


def test_tmt_test_case_setup(tmt_test_setup_passing):
    """Test that the TMT test case setup is correct"""
    test_data = tmt_test_setup_passing

    # Verify API setup
    assert test_data["api"].api.startswith(_UT_API_NAME)
    assert test_data["api"].library == _UT_API_LIBRARY

    # Verify Test Case setup
    test_case = test_data["test_case"]
    assert test_case.repository == BASIL_PROJECT_ROOT
    assert test_case.relative_path == TMT_PASSING_TEST_PATH
    assert "TMT Test Case" in test_case.title

    # Verify Test Run Config setup
    config = test_data["test_run_config"]
    assert config.plugin == "tmt"
    assert config.plugin_preset == ""
    assert config.plugin_vars == ""
    assert config.title == "local test run config"
    assert config.git_repo_ref == ""
    assert config.context_vars == "plan_type=local"
    assert config.environment_vars == ""
    assert config.provision_type == "container"
    assert config.provision_guest == ""
    assert config.provision_guest_port == ""
    assert config.ssh_key is None

    # Verify API-Test Case mapping
    mapping = test_data["api_tc_mapping"]
    assert mapping.api_id == test_data["api"].id
    assert mapping.test_case_id == test_case.id
    assert "Test Execution" in mapping.section
    assert mapping.coverage == 95

    # NOTE: Test Run is now created via API call, not in setup
    logger.info("✅ TMT test setup validation passed")


def test_tmt_files_exist():
    """Test that the TMT test files exist in the expected locations"""
    passing_test_path = os.path.join(BASIL_PROJECT_ROOT, TMT_PASSING_TEST_PATH)
    failing_test_path = os.path.join(BASIL_PROJECT_ROOT, TMT_FAILING_TEST_PATH)

    assert os.path.exists(passing_test_path), f"Passing test file not found: {passing_test_path}"
    assert os.path.exists(failing_test_path), f"Failing test file not found: {failing_test_path}"

    # Verify file contents contain expected FMF metadata
    with open(passing_test_path, "r") as f:
        passing_content = f.read()
        assert "summary:" in passing_content
        assert "test:" in passing_content
        assert "framework: shell" in passing_content
        assert "exit 1" not in passing_content  # Should not have exit 1

    with open(failing_test_path, "r") as f:
        failing_content = f.read()
        assert "summary:" in failing_content
        assert "test:" in passing_content
        assert "framework: shell" in failing_content
        assert "exit 1" in failing_content  # Should have exit 1 to cause failure

    logger.info("✅ TMT test files validation passed")


def create_test_run_via_api(test_data, client, user_authentication, title, notes):
    """Helper function to create a test run via BASIL API endpoint"""
    logger.info(f"🔄 Creating Test Run via BASIL API endpoint /mapping/api/test-runs: {title}")

    test_run_payload = {
        "api-id": test_data["api"].id,
        "mapped_to_type": test_data["api_tc_mapping"].__tablename__,
        "mapped_to_id": test_data["api_tc_mapping"].id,
        "title": title,
        "notes": notes,
        "test-run-config": {
            "id": test_data["test_run_config"].id,
            "plugin": "tmt",
            "plugin_preset": "",
            "plugin_vars": "",
            "title": "local test run config",
            "git_repo_ref": "",
            "context_vars": "plan_type=local",
            "environment_vars": "",
            "provision_type": "container",
            "provision_guest": "",
            "provision_guest_port": "",
            "ssh_key": "",
        },
        "user-id": user_authentication.json["id"],
        "token": user_authentication.json["token"],
    }

    logger.info(f"📤 Sending test run request: {test_run_payload}")
    response = client.post("/mapping/api/test-runs", json=test_run_payload)

    if response.status_code != HTTPStatus.CREATED and response.status_code != HTTPStatus.OK:
        pytest.fail(f"Failed to create test run via API: {response.status_code} - {response.data}")

    test_run_response = response.get_json()
    test_run_id = test_run_response["id"]
    logger.info(f"✅ Test Run created via API with ID: {test_run_id}")

    return test_run_id


def monitor_test_run(test_run, test_data, client_db, expected_result):
    """Shared function to monitor a test run execution and validate results"""
    logger.info("🚀 Starting TMT test execution monitoring")
    logger.info(f"📋 Test run: {test_run.title}")
    logger.info(f"📁 Test file: {test_data['test_case'].relative_path}")
    logger.info("🏗️  API will automatically start TestRunner and create containers...")
    logger.info(f"⏱️  Monitoring for completion (max {TEST_TIMEOUT_SECONDS} seconds)")

    if expected_result == "fail":
        logger.warning("⚠️  This test should FAIL (contains 'exit 1')")

    # Initial state should be 'created'
    client_db.session.refresh(test_run)
    assert test_run.status == "created", f"Expected 'created' status but got '{test_run.status}'"
    logger.info(f"📊 Initial status: {test_run.status}")

    # Monitor the database row for status changes
    start_time = time.time()
    last_status = test_run.status
    poll_count = 0

    while time.time() - start_time < TEST_TIMEOUT_SECONDS:
        client_db.session.refresh(test_run)
        poll_count += 1
        elapsed_time = int(time.time() - start_time)

        # Show progress every 30 seconds or on status change
        if poll_count % 15 == 0 or test_run.status != last_status:  # Every 30 seconds (15 * 2 sec sleep)
            logger.info(f"⏱️  [{elapsed_time}s] Polling database... Current status: {test_run.status}")

        if test_run.status != last_status:
            logger.info(f"📊 Status changed: {last_status} → {test_run.status}")
            last_status = test_run.status

            if test_run.status == "running":
                logger.info("🏃 TMT test execution started! Containers are being created...")

        # Check if test completed
        if test_run.status == "completed":
            result_emoji = "✅" if expected_result == "pass" else "❌"
            logger.info(f"{result_emoji} Test completed with result: {test_run.result}")
            if test_run.log:
                logger.info(f"📝 Test log (first 500 chars): {test_run.log[:500]}...")
            else:
                logger.warning("⚠️  No test log available")

            # Verify test result matches expectation
            assert (
                test_run.result == expected_result
            ), f"Expected '{expected_result}' result but got '{test_run.result}'"

            result_msg = "passed" if expected_result == "pass" else "failed correctly"
            logger.info(f"✅ Test result validation passed ({result_msg})")
            return

        elif test_run.status == "error":
            logger.error("❌ Test run failed with error status")
            if test_run.log:
                logger.error(f"📝 Error log: {test_run.log}")
            pytest.fail(f"Test run failed with error status. Log: {test_run.log}")

        # Wait a bit before checking again
        time.sleep(2)

    # If we get here, test timed out
    logger.error(f"⏰ Test execution timed out after {TEST_TIMEOUT_SECONDS} seconds")
    logger.error(f"📊 Final status: {test_run.status}")
    if test_run.log:
        logger.error(f"📝 Final log: {test_run.log}")
    raise TestTimeoutError(f"Test run did not complete within {TEST_TIMEOUT_SECONDS} seconds")


@pytest.mark.skipif(not shutil.which("tmt"), reason="TMT binary not found - skipping real TMT execution tests")
def test_tmt_passing_test_execution(tmt_test_setup_passing, client_db, client, user_authentication):
    """Test that the TMT passing test executes and passes - API handles TestRunner automatically"""
    test_data = tmt_test_setup_passing

    # Create Test Run via API endpoint
    test_run_id = create_test_run_via_api(
        test_data, client, user_authentication, "TMT Passing Test Run", "Test run for TMT passing test case via API"
    )

    # Fetch the created test run from database for monitoring
    test_run = client_db.session.query(TestRunModel).filter(TestRunModel.id == test_run_id).one()

    # Monitor test execution and validate it passes
    def run_monitoring():
        monitor_test_run(test_run, test_data, client_db, "pass")

    # Run the monitoring with timeout
    try:
        timeout_handler(run_monitoring, TEST_TIMEOUT_SECONDS + 10)  # Extra buffer for monitoring
        logger.info("✅ TMT passing test execution monitored successfully")
    except TestTimeoutError:
        pytest.fail(f"TMT passing test monitoring timed out after {TEST_TIMEOUT_SECONDS} seconds")


@pytest.mark.skipif(not shutil.which("tmt"), reason="TMT binary not found - skipping real TMT execution tests")
def test_tmt_failing_test_execution(tmt_test_setup_failing, client_db, client, user_authentication):
    """Test that the TMT failing test executes and fails - API handles TestRunner automatically"""
    test_data = tmt_test_setup_failing

    # Create Test Run via API endpoint
    test_run_id = create_test_run_via_api(
        test_data, client, user_authentication, "TMT Failing Test Run", "Test run for TMT failing test case via API"
    )

    # Fetch the created test run from database for monitoring
    test_run = client_db.session.query(TestRunModel).filter(TestRunModel.id == test_run_id).one()

    # Monitor test execution and validate it fails
    def run_monitoring():
        monitor_test_run(test_run, test_data, client_db, "fail")

    # Run the monitoring with timeout
    try:
        timeout_handler(run_monitoring, TEST_TIMEOUT_SECONDS + 10)  # Extra buffer for monitoring
        logger.info("✅ TMT failing test execution monitored successfully")
    except TestTimeoutError:
        pytest.fail(f"TMT failing test monitoring timed out after {TEST_TIMEOUT_SECONDS} seconds")


def test_tmt_test_runner_environment_variables(tmt_test_setup_passing):
    """Test that test data is properly set up for TMT environment variables"""
    test_data = tmt_test_setup_passing
    test_run = test_data["test_run"]

    # Verify that test data contains all the information needed for TMT environment variables
    # (The API will automatically use this data to set environment variables when TestRunner runs)

    expected_data = {
        "test_run.uid": test_run.uid,
        "test_case.id": test_data["test_case"].id,
        "test_case.title": test_data["test_case"].title,
        "api.api": test_data["api"].api,
        "api.library": test_data["api"].library,
        "api.library_version": test_data["api"].library_version,
        "test_run.mapping_to": test_run.mapping_to,
        "test_run.mapping_id": test_run.mapping_id,
        "test_case.relative_path": test_data["test_case"].relative_path,
        "test_case.repository": test_data["test_case"].repository,
    }

    logger.info("📋 Verifying test data for TMT environment variables:")
    for data_name, value in expected_data.items():
        assert value is not None, f"Test data {data_name} is None"
        assert str(value).strip() != "", f"Test data {data_name} is empty"
        logger.info(f"   ✅ {data_name}: {value}")

    # Verify TMT-specific test case setup
    assert test_data["test_case"].repository == BASIL_PROJECT_ROOT
    assert test_data["test_case"].relative_path in [TMT_PASSING_TEST_PATH, TMT_FAILING_TEST_PATH]

    logger.info("✅ TMT test data validation passed - API will use this to set environment variables")


def test_tmt_plugin_validation(tmt_test_setup_passing):
    """Test TMT plugin configuration validation"""
    test_data = tmt_test_setup_passing
    test_run_config = test_data["test_run_config"]

    # Verify the test run config has valid TMT settings for container provision
    assert test_run_config.plugin == "tmt"
    assert test_run_config.provision_type == "container"
    assert test_run_config.context_vars == "plan_type=local"

    logger.info("📋 Verifying TMT configuration:")
    logger.info(f"   ✅ Plugin: {test_run_config.plugin}")
    logger.info(f"   ✅ Provision type: {test_run_config.provision_type}")
    logger.info(f"   ✅ Context vars: {test_run_config.context_vars}")
    logger.info(f"   ✅ Plugin preset: '{test_run_config.plugin_preset}'")
    logger.info(f"   ✅ Plugin vars: '{test_run_config.plugin_vars}'")
    logger.info(f"   ✅ Environment vars: '{test_run_config.environment_vars}'")

    # For container provision, these fields should be empty/None
    assert test_run_config.provision_guest == ""
    assert test_run_config.provision_guest_port == ""
    assert test_run_config.ssh_key is None

    logger.info("✅ TMT plugin configuration validation passed - API will validate when TestRunner starts")


def test_tmt_command_generation(tmt_test_setup_passing):
    """Test that test data will generate correct TMT command structure"""
    test_data = tmt_test_setup_passing
    test_run_config = test_data["test_run_config"]

    # Verify test data contains all components needed for TMT command generation
    # (The API will use this data to generate the actual TMT command when TestRunner runs)

    logger.info("📋 Verifying test data for TMT command generation:")

    # Plugin type should be TMT
    assert test_run_config.plugin == "tmt", f"Expected 'tmt' plugin but got '{test_run_config.plugin}'"
    logger.info(f"   ✅ Plugin: {test_run_config.plugin}")

    # Provision type should be container
    assert test_run_config.provision_type == "container", "Expected 'container' provision type"
    logger.info(f"   ✅ Provision type: {test_run_config.provision_type}")

    # Context vars should include plan_type=local
    assert "plan_type=local" in test_run_config.context_vars, "Context vars should include plan_type=local"
    logger.info(f"   ✅ Context vars: {test_run_config.context_vars}")

    # Test Case and API are properly configured for TMT
    test_case = test_data["test_case"]
    assert test_case.repository == BASIL_PROJECT_ROOT
    assert test_case.relative_path == TMT_PASSING_TEST_PATH
    logger.info(f"   ✅ Test case path: {test_case.relative_path}")


if __name__ == "__main__":
    # For manual testing/debugging
    pytest.main([__file__ + "::test_tmt_passing_test_execution", "-v", "-s"])
