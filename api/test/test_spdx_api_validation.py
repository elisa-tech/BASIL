import json
import logging
import os
import pytest
import tempfile
import subprocess
from http import HTTPStatus
from db.models.user import UserModel
from db.models.api import ApiModel
from db.models.sw_requirement import SwRequirementModel
from db.models.api_sw_requirement import ApiSwRequirementModel
from db.models.sw_requirement_sw_requirement import SwRequirementSwRequirementModel
from db.models.test_specification import TestSpecificationModel
from db.models.sw_requirement_test_specification import SwRequirementTestSpecificationModel
from db.models.test_case import TestCaseModel
from db.models.test_specification_test_case import TestSpecificationTestCaseModel
from db.models.sw_requirement_test_case import SwRequirementTestCaseModel
from db.models.api_test_specification import ApiTestSpecificationModel
from db.models.api_test_case import ApiTestCaseModel
from db.models.justification import JustificationModel
from db.models.api_justification import ApiJustificationModel
from db.models.document import DocumentModel
from db.models.api_document import ApiDocumentModel
from db.models.test_run import TestRunModel
from db.models.test_run_config import TestRunConfigModel
from conftest import UT_USER_EMAIL

_SPDX_API_URL = "/spdx/apis"

_UT_API_NAME = "ut_spdx_api"
_UT_API_LIBRARY = "ut_spdx_library"
_UT_API_LIBRARY_VERSION = "v1.0.0"
_UT_API_CATEGORY = "ut_spdx_category"
_UT_API_IMPLEMENTATION_FILE_FROM_ROW = 0
_UT_API_IMPLEMENTATION_FILE_TO_ROW = 42
_UT_API_TAGS = "spdx,validation,test"

_UT_API_SPEC_CONTENT = """
# API Specification for SPDX Testing

## Section 1: Authentication
The API shall provide secure authentication mechanisms.

## Section 2: Data Processing
The API shall process data according to specifications.

## Section 3: Error Handling
The API shall handle errors gracefully.

## Section 4: Performance
The API shall meet performance requirements.

## Section 5: Documentation
The API shall provide comprehensive documentation.
"""

# Test data constants
_UT_TEST_SPEC_TITLE = "UT SPDX Test Specification"
_UT_TEST_SPEC_PRECONDITIONS = "System ready for testing"
_UT_TEST_SPEC_DESCRIPTION = "Comprehensive test description for SPDX validation"
_UT_TEST_SPEC_EXPECTED_BEHAVIOR = "Expected behavior for SPDX compliance"

_UT_TEST_CASE_TITLE = "UT SPDX Test Case"
_UT_TEST_CASE_DESCRIPTION = "Test case for SPDX validation"
_UT_TEST_CASE_REPOSITORY = "https://github.com/test/repo"
_UT_TEST_CASE_RELATIVE_PATH = "test/case.py"

_UT_JUSTIFICATION_DESCRIPTION = "Justification for SPDX test requirements"

_UT_DOCUMENT_TITLE = "SPDX Reference Document"
_UT_DOCUMENT_DESCRIPTION = "Reference documentation for SPDX compliance"
_UT_DOCUMENT_URL = "https://spdx.dev/specification"


logger = logging.getLogger(__name__)


def get_sw_requirement_model(client_db, utilities, title_suffix=""):
    """Helper to create a SW requirement model"""
    user = client_db.session.query(UserModel).filter(UserModel.email == UT_USER_EMAIL).one()
    return SwRequirementModel(
        f"SPDX SW req {title_suffix}#{utilities.generate_random_hex_string8()}",
        f"Software requirement for SPDX validation {title_suffix}.",
        user,
    )


def get_test_specification_model(client_db, utilities, title_suffix=""):
    """Helper to create a test specification model"""
    user = client_db.session.query(UserModel).filter(UserModel.email == UT_USER_EMAIL).one()
    return TestSpecificationModel(
        f"{_UT_TEST_SPEC_TITLE} {title_suffix}#{utilities.generate_random_hex_string8()}",
        _UT_TEST_SPEC_PRECONDITIONS,
        _UT_TEST_SPEC_DESCRIPTION,
        _UT_TEST_SPEC_EXPECTED_BEHAVIOR,
        user,
    )


def get_test_case_model(client_db, utilities, title_suffix=""):
    """Helper to create a test case model"""
    user = client_db.session.query(UserModel).filter(UserModel.email == UT_USER_EMAIL).one()
    return TestCaseModel(
        _UT_TEST_CASE_REPOSITORY,
        _UT_TEST_CASE_RELATIVE_PATH,
        f"{_UT_TEST_CASE_TITLE} {title_suffix}#{utilities.generate_random_hex_string8()}",
        _UT_TEST_CASE_DESCRIPTION,
        user,
    )


def get_justification_model(client_db, utilities, title_suffix=""):
    """Helper to create a justification model"""
    user = client_db.session.query(UserModel).filter(UserModel.email == UT_USER_EMAIL).one()
    return JustificationModel(
        f"{_UT_JUSTIFICATION_DESCRIPTION} {title_suffix}#{utilities.generate_random_hex_string8()}", user
    )


def get_document_model(client_db, utilities, title_suffix=""):
    """Helper to create a document model"""
    user = client_db.session.query(UserModel).filter(UserModel.email == UT_USER_EMAIL).one()
    return DocumentModel(
        f"{_UT_DOCUMENT_TITLE} {title_suffix}#{utilities.generate_random_hex_string8()}",
        _UT_DOCUMENT_DESCRIPTION,
        "file",
        "DESCRIBES",
        _UT_DOCUMENT_URL,
        "Document section",
        0,
        0,
        user,
    )


def get_test_run_config_model(client_db, utilities):
    """Helper to create a test run config model"""
    user = client_db.session.query(UserModel).filter(UserModel.email == UT_USER_EMAIL).one()
    return TestRunConfigModel(
        "tmt",  # plugin
        "",  # plugin_preset
        "",  # plugin_vars
        f"SPDX Test Config #{utilities.generate_random_hex_string8()}",  # title
        "main",  # git_repo_ref
        "",  # context_vars
        "",  # environment_vars
        "container",  # provision_type
        "",  # provision_guest
        "1234",  # provision_guest_port
        None,  # ssh_key
        user,  # created_by
    )


def get_test_run_model(client_db, utilities, test_run_config, api_id, mapping_to, mapping_id):
    """Helper to create a test run model"""
    user = client_db.session.query(UserModel).filter(UserModel.email == UT_USER_EMAIL).one()
    api = client_db.session.query(ApiModel).filter(ApiModel.id == api_id).one()
    return TestRunModel(
        api,  # api
        f"SPDX Test Run #{utilities.generate_random_hex_string8()}",  # title
        "Test run for SPDX validation",  # notes
        test_run_config,  # test_run_config
        mapping_to,  # mapping_to
        mapping_id,  # mapping_id
        user,  # created_by
    )


def check_latest_jsonld_file(user_id: int = 0):
    """Helper to check the latest jsonld file"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    jsonld_file = os.path.join(current_dir, "..", "public", "spdx_export", f"{user_id}", "latest.jsonld")
    logger.info(f"Checking for latest jsonld file: {jsonld_file}")
    if os.path.isfile(jsonld_file):
        logger.info(f"Latest jsonld file found: {jsonld_file}")
        return jsonld_file
    return None


@pytest.fixture()
def clear_latest_jsonld_file(user_authentication):
    """Helper to clear the latest jsonld file"""
    jsonld_file = check_latest_jsonld_file(user_id=user_authentication.json['id'])
    if jsonld_file:
        logger.info(f"Clearing latest jsonld file: {jsonld_file}")
        os.remove(jsonld_file)


@pytest.fixture()
def comprehensive_spdx_test_data(client_db, ut_user_db, utilities):
    """Create comprehensive test data with all types of work items"""

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

    # Create Software Requirements
    sw_req_1 = get_sw_requirement_model(client_db, utilities, "Authentication")
    sw_req_2 = get_sw_requirement_model(client_db, utilities, "DataProcessing")
    sw_req_3 = get_sw_requirement_model(client_db, utilities, "ErrorHandling")

    # Create Test Specifications
    test_spec_1 = get_test_specification_model(client_db, utilities, "Auth")
    test_spec_2 = get_test_specification_model(client_db, utilities, "Data")

    # Create Test Cases
    test_case_1 = get_test_case_model(client_db, utilities, "AuthTest")
    test_case_2 = get_test_case_model(client_db, utilities, "DataTest")
    test_case_3 = get_test_case_model(client_db, utilities, "ErrorTest")

    # Create Justifications
    justification_1 = get_justification_model(client_db, utilities, "Compliance")
    justification_2 = get_justification_model(client_db, utilities, "Performance")

    # Create Documents
    document_1 = get_document_model(client_db, utilities, "AuthDoc")
    document_2 = get_document_model(client_db, utilities, "APIDoc")

    # Create Test Run Config and Test Runs
    test_run_config = get_test_run_config_model(client_db, utilities)

    # Add all entities to session
    entities = [
        ut_api,
        sw_req_1,
        sw_req_2,
        sw_req_3,
        test_spec_1,
        test_spec_2,
        test_case_1,
        test_case_2,
        test_case_3,
        justification_1,
        justification_2,
        document_1,
        document_2,
        test_run_config,
    ]

    for entity in entities:
        client_db.session.add(entity)
    client_db.session.commit()

    # Create API-SW Requirement mappings
    api_sr_mapping_1 = ApiSwRequirementModel(
        ut_api,
        sw_req_1,
        "## Section 1: Authentication",
        _UT_API_SPEC_CONTENT.find("## Section 1: Authentication"),
        95,
        user,
    )
    # Duplicate mapping against the same section (different SW requirement)
    # to validate snippet/CreationInfo deduplication
    api_sr_mapping_auth_dup = ApiSwRequirementModel(
        ut_api,
        sw_req_3,
        "## Section 1: Authentication",
        _UT_API_SPEC_CONTENT.find("## Section 1: Authentication"),
        80,
        user,
    )
    api_sr_mapping_2 = ApiSwRequirementModel(
        ut_api,
        sw_req_2,
        "## Section 2: Data Processing",
        _UT_API_SPEC_CONTENT.find("## Section 2: Data Processing"),
        90,
        user,
    )

    # Create SW Requirement to SW Requirement mapping (nested requirements)
    sr_sr_mapping = SwRequirementSwRequirementModel(api_sr_mapping_1, None, sw_req_3, 85, user)

    # Create API-Test Specification mappings
    api_ts_mapping_1 = ApiTestSpecificationModel(
        ut_api,
        test_spec_1,
        "## Section 3: Error Handling",
        _UT_API_SPEC_CONTENT.find("## Section 3: Error Handling"),
        88,
        user,
    )
    api_ts_mapping_2 = ApiTestSpecificationModel(
        ut_api,
        test_spec_2,
        "## Section 4: Performance",
        _UT_API_SPEC_CONTENT.find("## Section 4: Performance"),
        92,
        user,
    )

    # Create SW Requirement-Test Specification mappings
    # sr_ts_mapping: sw_req_2 -> test_spec_1 (via api_sw_requirement mapping)
    sr_ts_mapping = SwRequirementTestSpecificationModel(api_sr_mapping_2, None, test_spec_1, 87, user)

    # Create Test Specification-Test Case mappings
    ts_tc_mapping_1 = TestSpecificationTestCaseModel(api_ts_mapping_1, None, test_case_1, 90, user)
    ts_tc_mapping_2 = TestSpecificationTestCaseModel(api_ts_mapping_2, None, test_case_2, 93, user)

    # Create SW Requirement-Test Case mappings
    sr_tc_mapping = SwRequirementTestCaseModel(api_sr_mapping_1, None, test_case_3, 89, user)

    # Add all mappings to session first so sr_sr_mapping gets an id before being used below
    pre_mappings = [
        api_sr_mapping_1,
        api_sr_mapping_auth_dup,
        api_sr_mapping_2,
        sr_sr_mapping,
        api_ts_mapping_1,
        api_ts_mapping_2,
        sr_ts_mapping,
        ts_tc_mapping_1,
        ts_tc_mapping_2,
        sr_tc_mapping,
    ]
    for mapping in pre_mappings:
        client_db.session.add(mapping)
    client_db.session.flush()

    # Create sub-requirement -> test specification mapping (via sw_requirement_sw_requirement mapping)
    # This tests that nested SW requirements also export their child test specifications
    sr_sr_ts_mapping = SwRequirementTestSpecificationModel(None, sr_sr_mapping, test_spec_2, 75, user)

    # Create API-Test Case mappings
    api_tc_mapping = ApiTestCaseModel(
        ut_api,
        test_case_1,
        "## Section 5: Documentation",
        _UT_API_SPEC_CONTENT.find("## Section 5: Documentation"),
        91,
        user,
    )

    # Create API-Justification mappings
    api_j_mapping_1 = ApiJustificationModel(
        ut_api,
        justification_1,
        "Authentication mechanisms",
        _UT_API_SPEC_CONTENT.find("secure authentication"),
        94,
        user,
    )
    api_j_mapping_2 = ApiJustificationModel(
        ut_api,
        justification_2,
        "Performance requirements",
        _UT_API_SPEC_CONTENT.find("performance requirements"),
        96,
        user,
    )

    # Create API-Document mappings
    api_doc_mapping_1 = ApiDocumentModel(
        ut_api,
        document_1,
        "comprehensive documentation",
        _UT_API_SPEC_CONTENT.find("comprehensive documentation"),
        97,
        user,
    )
    api_doc_mapping_2 = ApiDocumentModel(
        ut_api, document_2, "API Specification", _UT_API_SPEC_CONTENT.find("API Specification"), 98, user
    )

    # Add remaining mappings and commit
    mappings = [
        sr_sr_ts_mapping,
        api_tc_mapping,
        api_j_mapping_1,
        api_j_mapping_2,
        api_doc_mapping_1,
        api_doc_mapping_2,
    ]

    for mapping in mappings:
        client_db.session.add(mapping)
    client_db.session.commit()

    # Create Test Runs for different mappings
    test_run_1 = get_test_run_model(
        client_db, utilities, test_run_config, ut_api.id, ts_tc_mapping_1.__tablename__, ts_tc_mapping_1.id
    )
    test_run_2 = get_test_run_model(
        client_db, utilities, test_run_config, ut_api.id, sr_tc_mapping.__tablename__, sr_tc_mapping.id
    )

    client_db.session.add(test_run_1)
    client_db.session.add(test_run_2)
    client_db.session.commit()

    test_data = {
        "api": ut_api,
        "sw_requirements": [sw_req_1, sw_req_2, sw_req_3],
        "test_specifications": [test_spec_1, test_spec_2],
        "test_cases": [test_case_1, test_case_2, test_case_3],
        "justifications": [justification_1, justification_2],
        "documents": [document_1, document_2],
        "test_runs": [test_run_1, test_run_2],
        "test_run_config": test_run_config,
        "mappings": {
            "api_sr": [api_sr_mapping_1, api_sr_mapping_2],
            "sr_sr": [sr_sr_mapping],
            "api_ts": [api_ts_mapping_1, api_ts_mapping_2],
            "sr_ts": [sr_ts_mapping],
            "sr_sr_ts": [sr_sr_ts_mapping],
            "ts_tc": [ts_tc_mapping_1, ts_tc_mapping_2],
            "sr_tc": [sr_tc_mapping],
            "api_tc": [api_tc_mapping],
            "api_j": [api_j_mapping_1, api_j_mapping_2],
            "api_doc": [api_doc_mapping_1, api_doc_mapping_2],
        },
    }

    yield test_data

    # Cleanup: remove the raw_spec tempfile
    if os.path.isfile(raw_spec.name):
        os.remove(raw_spec.name)


def test_spdx_api_export_and_validation(client, user_authentication, comprehensive_spdx_test_data):
    """Test SPDX API export with comprehensive work items and validate using spdx3-validate"""

    test_data = comprehensive_spdx_test_data
    api = test_data["api"]

    # Make API call to generate SPDX
    response = client.get(
        _SPDX_API_URL,
        query_string={
            "api-id": api.id,
            "user-id": user_authentication.json["id"],
            "token": user_authentication.json["token"],
            "filename": "latest.jsonld"
        },
    )

    # Check that SPDX export was successful
    assert response.status_code == HTTPStatus.OK

    assert check_latest_jsonld_file(user_id=user_authentication.json["id"]) is not None

    # Save the SPDX content to a temporary file for validation
    spdx_content = response.data

    # Verify it's valid JSON-LD
    try:
        spdx_data = json.loads(spdx_content)
        assert "@context" in spdx_data
        assert "@graph" in spdx_data
        graph_elements = spdx_data["@graph"]
        assert len(graph_elements) > 0
        print(f"✓ Generated valid JSON-LD with {len(spdx_data['@graph'])} elements")
    except json.JSONDecodeError:
        pytest.fail("Generated SPDX is not valid JSON")

    # Save to temporary file for spdx3-validate
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonld", delete=False) as temp_file:
        temp_file.write(spdx_content.decode("utf-8"))
        temp_file_path = temp_file.name

    try:
        # Run spdx3-validate on the generated file
        print(f"Running spdx3-validate on {temp_file_path}")
        result = subprocess.run(
            ["spdx3-validate", "--json", temp_file_path, "--spdx-version", "auto"],
            capture_output=True,
            text=True,
            timeout=60,  # 60 second timeout
        )

        print(f"spdx3-validate exit code: {result.returncode}")
        if result.stdout:
            print(f"STDOUT: {result.stdout}")
        if result.stderr:
            print(f"STDERR: {result.stderr}")

        # Check validation results
        if result.returncode == 0:
            print("✓ SPDX validation passed successfully")
            assert True, "SPDX validation successful"
        else:
            print("✗ SPDX validation failed")
            # Don't fail the test immediately - let's analyze what went wrong
            validation_errors = result.stderr or result.stdout
            print(f"Validation errors: {validation_errors}")

            # You can add specific assertions here based on expected validation issues
            # For now, we'll record the failure but continue
            pytest.fail(f"SPDX validation failed with errors: {validation_errors}")

    except subprocess.TimeoutExpired:
        pytest.fail("spdx3-validate timed out after 60 seconds")
    except FileNotFoundError:
        pytest.skip("spdx3-validate not found - skipping validation test")
    finally:
        # Cleanup temporary file
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)

    """Test that the generated SPDX contains expected elements from our test data"""

    # Count different types of elements
    element_types = {}
    for element in graph_elements:
        element_type = element.get("type", "Unknown")
        element_types[element_type] = element_types.get(element_type, 0) + 1

    print(f"Generated SPDX element types: {element_types}")

    # Verify we have expected element types
    expected_types = [
        "Annotation",
        "Person",
        "CreationInfo",
        "SpdxDocument",
        "software_File",
        "software_Snippet",
        "Relationship",
        "Tool",
    ]
    for expected_type in expected_types:
        if expected_type not in element_types:
            print(f"Warning: Expected element type '{expected_type}' not found")

    # Verify we have files (representing our work items)
    files = [e for e in graph_elements if e.get("type") == "software_File"]
    assert len(files) > 0, "Should have File elements representing work items"

    # Verify we have relationships
    relationships = [e for e in graph_elements if e.get("type") == "Relationship"]
    assert len(relationships) > 0, "Should have Relationship elements"

    # Verify we have snippets (representing mappings to spec sections)
    snippets = [e for e in graph_elements if e.get("type") == "software_Snippet"]
    assert len(snippets) > 0, "Should have Snippet elements representing spec mappings"

    print(
        f"✓ SPDX structure validation passed: {len(files)} files, "
        f"{len(relationships)} relationships, {len(snippets)} snippets"
    )

    # Verify beginIntegerRange correctness (regression for issue #290)
    # Every snippet byte range must respect the SPDX PositiveIntegerRange minimum of 1
    for snippet in snippets:
        byte_range = snippet.get("software_byteRange", {})
        begin = byte_range.get("beginIntegerRange")
        end = byte_range.get("endIntegerRange")
        assert begin is not None, f"Snippet {snippet.get('spdxId')} is missing beginIntegerRange"
        assert end is not None, f"Snippet {snippet.get('spdxId')} is missing endIntegerRange"
        assert begin >= 1, (
            f"Snippet {snippet.get('spdxId')} has beginIntegerRange={begin}, "
            "must be >= 1 per SPDX PositiveIntegerRange spec"
        )
        assert end >= begin, (
            f"Snippet {snippet.get('spdxId')} has endIntegerRange={end} < beginIntegerRange={begin}"
        )

    # The test fixture maps sections at different offsets in the spec, so the
    # resulting beginIntegerRange values must NOT all be identical (if they were
    # all 1, the bug from issue #290 would be present again).
    begin_values = {s["software_byteRange"]["beginIntegerRange"] for s in snippets}
    assert len(begin_values) > 1, (
        f"All snippets share the same beginIntegerRange={begin_values}; "
        "expected distinct values for sections at different offsets (issue #290 regression)"
    )
    print(f"✓ Snippet byteRange validation passed: beginIntegerRange values = {sorted(begin_values)}")

    """Test that all types of work items are represented in the SPDX output"""

    # Extract all spdxId values to check for our work items
    spdx_comments = [element.get("comment", "") for element in graph_elements if "comment" in element]

    # Check for different work item types by examining spdxId patterns
    work_item_patterns = {
        "Software Requirement": 0,
        "Test Specification": 0,
        "Test Case": 0,
        "Justification": 0,
        "Document ID": 0,
        "Test Run": 0,
        "Software Component id": 0,
        "Snippet": 0,
    }

    for spdx_comment in spdx_comments:
        for pattern in work_item_patterns.keys():
            if pattern.lower() in spdx_comment.lower():
                work_item_patterns[pattern] += 1

    print(f"Work item representation in SPDX: {work_item_patterns}")

    # Verify that we have representation of our main work items
    # Note: Actual counts may vary based on SPDX implementation
    assert work_item_patterns["Software Requirement"] == 3, "Should have 3 SW Requirements in SPDX"
    assert work_item_patterns["Test Specification"] == 2, "Should have 2 Test Specifications in SPDX"
    assert work_item_patterns["Test Case"] == 3, "Should have 3 Test Cases in SPDX"
    assert work_item_patterns["Justification"] == 2, "Should have 2 Justifications in SPDX"
    assert work_item_patterns["Document ID"] == 2, "Should have 2 Documents in SPDX"
    assert work_item_patterns["Test Run"] == 2, "Should have 1 Test Run in SPDX"
    assert work_item_patterns["Software Component id"] == 1, "Should have 1 API representation in SPDX"
    assert work_item_patterns["Snippet"] == 9, "Should have 3 Snippets in SPDX"

    print("✓ Work item coverage validation passed")


def test_spdx_sw_requirement_children_exported(client, user_authentication, comprehensive_spdx_test_data):
    """Verify that test specifications and test cases linked to SW requirements
    are exported as SPDX relationships (regression test for bug where
    requirement -> test specification children were missing from the SPDX output)."""

    test_data = comprehensive_spdx_test_data
    api = test_data["api"]
    sw_req_2 = test_data["sw_requirements"][1]
    sw_req_1 = test_data["sw_requirements"][0]
    sw_req_3 = test_data["sw_requirements"][2]
    test_spec_1 = test_data["test_specifications"][0]
    test_spec_2 = test_data["test_specifications"][1]
    test_case_3 = test_data["test_cases"][2]

    response = client.get(
        _SPDX_API_URL,
        query_string={
            "api-id": api.id,
            "user-id": user_authentication.json["id"],
            "token": user_authentication.json["token"],
            "filename": "latest.jsonld",
        },
    )
    assert response.status_code == HTTPStatus.OK

    spdx_data = json.loads(response.data)
    graph = spdx_data["@graph"]

    relationships = [e for e in graph if e.get("type") == "Relationship"]

    def spdx_id_for_sr(sr):
        return f"spdx:file:basil:software-requirement:{sr.id}"

    def spdx_id_for_ts(ts):
        return f"spdx:file:basil:test-specification:{ts.id}"

    def spdx_id_for_tc(tc):
        return f"spdx:file:basil:test-case:{tc.id}"

    def has_relationship(from_id, to_id, rel_type):
        for rel in relationships:
            if rel.get("from") == from_id and rel.get("relationshipType") == rel_type:
                if to_id in rel.get("to", []):
                    return True
        return False

    # Bug 2 regression: sw_req_2 -> test_spec_1 (via api_sw_requirement mapping sr_ts_mapping)
    assert has_relationship(
        spdx_id_for_sr(sw_req_2), spdx_id_for_ts(test_spec_1), "hasSpecification"
    ), (
        f"Missing hasSpecification relationship: SW Requirement {sw_req_2.id} -> "
        f"Test Specification {test_spec_1.id}. "
        "SW requirements directly mapped to the API must export their child test specifications."
    )

    # Bug 2 regression: sw_req_1 -> test_case_3 (via api_sw_requirement mapping sr_tc_mapping)
    assert has_relationship(
        spdx_id_for_sr(sw_req_1), spdx_id_for_tc(test_case_3), "hasTest"
    ), (
        f"Missing hasTest relationship: SW Requirement {sw_req_1.id} -> "
        f"Test Case {test_case_3.id}. "
        "SW requirements directly mapped to the API must export their child test cases."
    )

    # Bug 1 regression: sw_req_3 (sub-requirement) -> test_spec_2 (via sw_requirement_sw_requirement mapping)
    assert has_relationship(
        spdx_id_for_sr(sw_req_3), spdx_id_for_ts(test_spec_2), "hasSpecification"
    ), (
        f"Missing hasSpecification relationship: sub-SW Requirement {sw_req_3.id} -> "
        f"Test Specification {test_spec_2.id}. "
        "Nested (sub) SW requirements must export their child test specifications."
    )

    print("✓ SW Requirement -> Test Specification/Case relationship export regression test passed")


def _export_and_parse(client, user_authentication, api):
    """Shared helper: trigger an SPDX export and return the parsed @graph list."""
    response = client.get(
        _SPDX_API_URL,
        query_string={
            "api-id": api.id,
            "user-id": user_authentication.json["id"],
            "token": user_authentication.json["token"],
            "filename": "latest.jsonld",
        },
    )
    assert response.status_code == HTTPStatus.OK
    return json.loads(response.data)["@graph"]


def _external_identifiers_for(graph, spdx_id):
    """Return the externalIdentifier list for the element with the given spdxId."""
    for element in graph:
        if element.get("spdxId") == spdx_id:
            return element.get("externalIdentifier", [])
    return []


def _assert_external_identifier(graph, spdx_id, expected_identifier, expected_comment_fragment):
    """Assert that the SPDX element carries the expected ExternalIdentifier."""
    ext_ids = _external_identifiers_for(graph, spdx_id)
    assert len(ext_ids) == 1, (
        f"Element {spdx_id} should have exactly 1 externalIdentifier, got {ext_ids}"
    )
    ei = ext_ids[0]
    assert ei["type"] == "ExternalIdentifier"
    assert ei["externalIdentifierType"] == "other"
    assert ei["identifier"] == expected_identifier, (
        f"Expected identifier '{expected_identifier}', got '{ei['identifier']}'"
    )
    assert expected_comment_fragment in ei.get("comment", ""), (
        f"Expected comment containing '{expected_comment_fragment}', got '{ei.get('comment')}'"
    )


def test_spdx_external_identifier_api(client, user_authentication, comprehensive_spdx_test_data):
    """ExternalIdentifier on the software_File element for each API uses
    basil:<tablename>:<id> as identifier."""
    test_data = comprehensive_spdx_test_data
    api = test_data["api"]
    graph = _export_and_parse(client, user_authentication, api)

    spdx_id = f"spdx:file:basil:api:{api.id}"
    _assert_external_identifier(
        graph,
        spdx_id,
        expected_identifier=f"basil:{api.__tablename__}:{api.id}",
        expected_comment_fragment=str(api.id),
    )
    print(f"✓ ExternalIdentifier for API {api.id} validated")


def test_spdx_external_identifier_sw_requirements(client, user_authentication, comprehensive_spdx_test_data):
    """ExternalIdentifier on each SW Requirement software_File uses
    basil:sw_requirements:<id> as identifier."""
    test_data = comprehensive_spdx_test_data
    api = test_data["api"]
    graph = _export_and_parse(client, user_authentication, api)

    for sr in test_data["sw_requirements"]:
        spdx_id = f"spdx:file:basil:software-requirement:{sr.id}"
        _assert_external_identifier(
            graph,
            spdx_id,
            expected_identifier=f"basil:{sr.__tablename__}:{sr.id}",
            expected_comment_fragment=str(sr.id),
        )
    print(f"✓ ExternalIdentifier for {len(test_data['sw_requirements'])} SW Requirements validated")


def test_spdx_external_identifier_test_specifications(client, user_authentication, comprehensive_spdx_test_data):
    """ExternalIdentifier on each Test Specification software_File uses
    basil:test_specifications:<id> as identifier."""
    test_data = comprehensive_spdx_test_data
    api = test_data["api"]
    graph = _export_and_parse(client, user_authentication, api)

    for ts in test_data["test_specifications"]:
        spdx_id = f"spdx:file:basil:test-specification:{ts.id}"
        _assert_external_identifier(
            graph,
            spdx_id,
            expected_identifier=f"basil:{ts.__tablename__}:{ts.id}",
            expected_comment_fragment=str(ts.id),
        )
    print(f"✓ ExternalIdentifier for {len(test_data['test_specifications'])} Test Specifications validated")


def test_spdx_external_identifier_test_cases(client, user_authentication, comprehensive_spdx_test_data):
    """ExternalIdentifier on each Test Case software_File uses
    basil:test_cases:<id> as identifier."""
    test_data = comprehensive_spdx_test_data
    api = test_data["api"]
    graph = _export_and_parse(client, user_authentication, api)

    for tc in test_data["test_cases"]:
        spdx_id = f"spdx:file:basil:test-case:{tc.id}"
        _assert_external_identifier(
            graph,
            spdx_id,
            expected_identifier=f"basil:{tc.__tablename__}:{tc.id}",
            expected_comment_fragment=str(tc.id),
        )
    print(f"✓ ExternalIdentifier for {len(test_data['test_cases'])} Test Cases validated")


def test_spdx_external_identifier_justifications(client, user_authentication, comprehensive_spdx_test_data):
    """ExternalIdentifier on each Justification software_File uses
    basil:justifications:<id> as identifier."""
    test_data = comprehensive_spdx_test_data
    api = test_data["api"]
    graph = _export_and_parse(client, user_authentication, api)

    for js in test_data["justifications"]:
        spdx_id = f"spdx:file:basil:justification:{js.id}"
        _assert_external_identifier(
            graph,
            spdx_id,
            expected_identifier=f"basil:{js.__tablename__}:{js.id}",
            expected_comment_fragment=str(js.id),
        )
    print(f"✓ ExternalIdentifier for {len(test_data['justifications'])} Justifications validated")


def test_spdx_external_identifier_documents(client, user_authentication, comprehensive_spdx_test_data):
    """ExternalIdentifier on each Document software_File uses
    basil:documents:<id> as identifier."""
    test_data = comprehensive_spdx_test_data
    api = test_data["api"]
    graph = _export_and_parse(client, user_authentication, api)

    for doc in test_data["documents"]:
        spdx_id = f"spdx:file:basil:document:{doc.id}"
        _assert_external_identifier(
            graph,
            spdx_id,
            expected_identifier=f"basil:{doc.__tablename__}:{doc.id}",
            expected_comment_fragment=str(doc.id),
        )
    print(f"✓ ExternalIdentifier for {len(test_data['documents'])} Documents validated")


def test_spdx_external_identifier_test_runs(client, user_authentication, comprehensive_spdx_test_data):
    """ExternalIdentifier on each Test Run software_File uses
    basil:test_runs:<id> as identifier."""
    test_data = comprehensive_spdx_test_data
    api = test_data["api"]
    graph = _export_and_parse(client, user_authentication, api)

    for tr in test_data["test_runs"]:
        spdx_id = f"spdx:file:basil:test-run:{tr.id}"
        _assert_external_identifier(
            graph,
            spdx_id,
            expected_identifier=f"basil:{tr.__tablename__}:{tr.id}",
            expected_comment_fragment=str(tr.id),
        )
    print(f"✓ ExternalIdentifier for {len(test_data['test_runs'])} Test Runs validated")


def test_spdx_annotation_version_injected(client, user_authentication, comprehensive_spdx_test_data):
    """Every Annotation.statement in the SPDX output must carry
    'basil:annotationVersion': '2.0'."""
    test_data = comprehensive_spdx_test_data
    api = test_data["api"]
    graph = _export_and_parse(client, user_authentication, api)

    annotations = [e for e in graph if e.get("type") == "Annotation"]
    assert len(annotations) > 0, "Expected at least one Annotation in the SPDX output"

    for annotation in annotations:
        statement_raw = annotation.get("statement", "{}")
        try:
            statement = json.loads(statement_raw)
        except json.JSONDecodeError:
            pytest.fail(f"Annotation {annotation.get('spdxId')} has non-JSON statement: {statement_raw}")

        assert statement.get("basil:annotationVersion") == "2.0", (
            f"Annotation {annotation.get('spdxId')} is missing 'basil:annotationVersion': '2.0'. "
            f"Statement keys: {list(statement.keys())}"
        )
    print(f"✓ basil:annotationVersion validated on {len(annotations)} annotations")


def test_spdx_entity_annotations_have_no_id_or_title(client, user_authentication, comprehensive_spdx_test_data):
    """Entity Annotation.statement must not contain 'id' or 'title' fields —
    those are now represented via ExternalIdentifier on the element."""
    test_data = comprehensive_spdx_test_data
    api = test_data["api"]
    graph = _export_and_parse(client, user_authentication, api)

    entity_annotation_id_prefixes = (
        "spdx:annotation:basil:api:",
        "spdx:annotation:basil:software-requirement:",
        "spdx:annotation:basil:test-specification:",
        "spdx:annotation:basil:test-case:",
        "spdx:annotation:basil:document:",
        "spdx:annotation:basil:justification:",
        "spdx:annotation:basil:test-run:",
    )

    entity_annotations = [
        e for e in graph
        if e.get("type") == "Annotation"
        and any(e.get("spdxId", "").startswith(p) for p in entity_annotation_id_prefixes)
    ]
    assert len(entity_annotations) > 0, "Expected at least one entity Annotation in the SPDX output"

    for annotation in entity_annotations:
        statement = json.loads(annotation.get("statement", "{}"))
        assert "id" not in statement, (
            f"Annotation {annotation.get('spdxId')} still contains 'id' in statement. "
            "It should have been moved to ExternalIdentifier."
        )
        assert "title" not in statement, (
            f"Annotation {annotation.get('spdxId')} still contains 'title' in statement. "
            "It should have been moved to ExternalIdentifier."
        )
    print(f"✓ No 'id'/'title' in {len(entity_annotations)} entity annotation statements")


def test_spdx_snippet_annotations_stripped(client, user_authentication, comprehensive_spdx_test_data):
    """Snippet Annotation.statement must not contain 'offset', 'section', or 'coverage' —
    offset/section are encoded in software_byteRange; coverage in Relationship.completeness."""
    test_data = comprehensive_spdx_test_data
    api = test_data["api"]
    graph = _export_and_parse(client, user_authentication, api)

    snippet_annotations = [
        e for e in graph
        if e.get("type") == "Annotation"
        and e.get("spdxId", "").startswith("spdx:annotation:snippet:")
    ]
    assert len(snippet_annotations) > 0, "Expected at least one snippet Annotation in the SPDX output"

    for annotation in snippet_annotations:
        statement = json.loads(annotation.get("statement", "{}"))
        for redundant_key in ("offset", "section", "coverage"):
            assert redundant_key not in statement, (
                f"Snippet annotation {annotation.get('spdxId')} still contains '{redundant_key}'. "
                "This field is already represented in a dedicated SPDX property."
            )
    print(f"✓ No redundant fields in {len(snippet_annotations)} snippet annotation statements")


if __name__ == "__main__":
    # For manual testing/debugging
    pytest.main([__file__ + "::test_spdx_api_export_and_validation", "-v", "-s"])
