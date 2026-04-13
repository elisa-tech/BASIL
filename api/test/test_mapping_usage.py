"""HTTP tests for GET /mapping/usage (MappingUsage)."""
import os
import tempfile
from http import HTTPStatus

import pytest

from conftest import UT_USER_EMAIL
from db.models.api import ApiModel
from db.models.api_document import ApiDocumentModel
from db.models.api_justification import ApiJustificationModel
from db.models.api_sw_requirement import ApiSwRequirementModel
from db.models.api_test_case import ApiTestCaseModel
from db.models.api_test_specification import ApiTestSpecificationModel
from db.models.document import DocumentModel
from db.models.justification import JustificationModel
from db.models.sw_requirement import SwRequirementModel
from db.models.sw_requirement_test_case import SwRequirementTestCaseModel
from db.models.test_case import TestCaseModel
from db.models.test_specification import TestSpecificationModel
from db.models.user import UserModel

_MAPPING_USAGE_URL = "/mapping/usage"

_UT_API_NAME = "ut_api"
_UT_API_LIBRARY = "ut_api_library"
_UT_API_LIBRARY_VERSION = "v1.0.0"
_UT_API_CATEGORY = "ut_api_category"
_UT_API_IMPLEMENTATION_FILE_FROM_ROW = 0
_UT_API_IMPLEMENTATION_FILE_TO_ROW = 42
_UT_API_TAGS = "ut_api_tags"

_UT_SPEC_SECTION = "BASIL UT mapping usage section."
_UT_RAW_SPEC = f"BASIL UT: {_UT_SPEC_SECTION} for /mapping/usage."

_UNMATCHING_ID = 9_999_999

_UT_TC_REPOSITORY = "https://github.com/example/repo"


def _ut_user(client_db):
    return client_db.session.query(UserModel).filter(UserModel.email == UT_USER_EMAIL).one()


def _create_api(client_db, utilities):
    """Create a committed ApiModel; returns (api, raw_spec_path)."""
    user = _ut_user(client_db)
    raw_spec = tempfile.NamedTemporaryFile(mode="w", delete=False)
    raw_spec.write(_UT_RAW_SPEC)
    raw_spec.close()
    ut_api = ApiModel(
        f"{_UT_API_NAME}#{utilities.generate_random_hex_string8()}",
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
    client_db.session.add(ut_api)
    client_db.session.commit()
    return ut_api, raw_spec.name


def _remove_raw_spec(path):
    if path and os.path.isfile(path):
        os.remove(path)


def _get_mapping_usage(client, *, work_item_type, wi_id):
    return client.get(
        _MAPPING_USAGE_URL,
        query_string={"work_item_type": work_item_type, "id": wi_id},
    )


def _assert_mapping_usage_ok(response, expected_api_ids):
    assert response.status_code == HTTPStatus.OK
    body = response.get_json()
    assert isinstance(body, dict)
    assert "api" in body
    apis = body["api"]
    assert isinstance(apis, list)
    found_ids = {x["id"] for x in apis}
    assert found_ids == set(expected_api_ids)
    for row in apis:
        assert set(row.keys()) == {"id", "api", "library", "library_version"}


@pytest.fixture
def api_only_db(client_db, utilities, ut_user_db):
    ut_api, raw_path = _create_api(client_db, utilities)
    yield ut_api, raw_path
    _remove_raw_spec(raw_path)


@pytest.fixture
def api_sw_requirement_db(client_db, utilities, ut_user_db):
    ut_api, raw_path = _create_api(client_db, utilities)
    user = _ut_user(client_db)
    ut_sr = SwRequirementModel(
        f"SR #{utilities.generate_random_hex_string8()}",
        "description for mapping usage UT",
        user,
    )
    offset = _UT_RAW_SPEC.find(_UT_SPEC_SECTION)
    mapping = ApiSwRequirementModel(ut_api, ut_sr, _UT_SPEC_SECTION, offset, 0, user)
    client_db.session.add(ut_sr)
    client_db.session.add(mapping)
    client_db.session.commit()
    yield ut_api, ut_sr, raw_path
    _remove_raw_spec(raw_path)


@pytest.fixture
def api_document_db(client_db, utilities, ut_user_db):
    ut_api, raw_path = _create_api(client_db, utilities)
    user = _ut_user(client_db)
    ut_doc = DocumentModel(
        f"doc #{utilities.generate_random_hex_string8()}",
        "unit test document",
        "file",
        "relates-to",
        raw_path,
        _UT_SPEC_SECTION,
        _UT_RAW_SPEC.find(_UT_SPEC_SECTION),
        0,
        user,
    )
    mapping = ApiDocumentModel(
        ut_api,
        ut_doc,
        _UT_SPEC_SECTION,
        _UT_RAW_SPEC.find(_UT_SPEC_SECTION),
        0,
        user,
    )
    client_db.session.add(ut_doc)
    client_db.session.add(mapping)
    client_db.session.commit()
    yield ut_api, ut_doc, raw_path
    _remove_raw_spec(raw_path)


@pytest.fixture
def api_justification_db(client_db, utilities, ut_user_db):
    ut_api, raw_path = _create_api(client_db, utilities)
    user = _ut_user(client_db)
    ut_j = JustificationModel("justification for mapping usage UT", user)
    mapping = ApiJustificationModel(
        ut_api,
        ut_j,
        _UT_SPEC_SECTION,
        _UT_RAW_SPEC.find(_UT_SPEC_SECTION),
        0,
        user,
    )
    client_db.session.add(ut_j)
    client_db.session.add(mapping)
    client_db.session.commit()
    yield ut_api, ut_j, raw_path
    _remove_raw_spec(raw_path)


@pytest.fixture
def api_test_specification_db(client_db, utilities, ut_user_db):
    ut_api, raw_path = _create_api(client_db, utilities)
    user = _ut_user(client_db)
    ut_ts = TestSpecificationModel(
        f"TS #{utilities.generate_random_hex_string8()}",
        None,
        "test description",
        "expected",
        user,
    )
    mapping = ApiTestSpecificationModel(
        ut_api,
        ut_ts,
        _UT_SPEC_SECTION,
        _UT_RAW_SPEC.find(_UT_SPEC_SECTION),
        0,
        user,
    )
    client_db.session.add(ut_ts)
    client_db.session.add(mapping)
    client_db.session.commit()
    yield ut_api, ut_ts, raw_path
    _remove_raw_spec(raw_path)


@pytest.fixture
def api_test_case_db(client_db, utilities, ut_user_db):
    ut_api, raw_path = _create_api(client_db, utilities)
    user = _ut_user(client_db)
    ut_tc = TestCaseModel(
        _UT_TC_REPOSITORY,
        f"tests/test_{utilities.generate_random_hex_string8()}.py",
        f"TC #{utilities.generate_random_hex_string8()}",
        "test case for mapping usage",
        user,
    )
    mapping = ApiTestCaseModel(
        ut_api,
        ut_tc,
        _UT_SPEC_SECTION,
        _UT_RAW_SPEC.find(_UT_SPEC_SECTION),
        0,
        user,
    )
    client_db.session.add(ut_tc)
    client_db.session.add(mapping)
    client_db.session.commit()
    yield ut_api, ut_tc, raw_path
    _remove_raw_spec(raw_path)


@pytest.fixture
def api_sr_tc_indirect_db(client_db, utilities, ut_user_db):
    """Test case mapped only under ApiSwRequirement (no ApiTestCase row)."""
    ut_api, raw_path = _create_api(client_db, utilities)
    user = _ut_user(client_db)
    ut_sr = SwRequirementModel(
        f"SR #{utilities.generate_random_hex_string8()}",
        "SR for indirect TC usage",
        user,
    )
    offset = _UT_RAW_SPEC.find(_UT_SPEC_SECTION)
    api_sr = ApiSwRequirementModel(ut_api, ut_sr, _UT_SPEC_SECTION, offset, 0, user)
    ut_tc = TestCaseModel(
        _UT_TC_REPOSITORY,
        f"tests/test_{utilities.generate_random_hex_string8()}.py",
        f"TC #{utilities.generate_random_hex_string8()}",
        "indirect TC",
        user,
    )
    sr_tc = SwRequirementTestCaseModel(api_sr, None, ut_tc, 75, user)
    client_db.session.add(ut_sr)
    client_db.session.add(api_sr)
    client_db.session.add(ut_tc)
    client_db.session.add(sr_tc)
    client_db.session.commit()
    yield ut_api, ut_tc, raw_path
    _remove_raw_spec(raw_path)


def test_mapping_usage_missing_work_item_type(client):
    response = client.get(_MAPPING_USAGE_URL, query_string={"id": 1})
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_mapping_usage_missing_id(client):
    response = client.get(_MAPPING_USAGE_URL, query_string={"work_item_type": "document"})
    assert response.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.parametrize(
    "work_item_type",
    ("sw-requirement", "document", "justification", "test-specification", "test-case"),
)
def test_mapping_usage_unknown_id_returns_empty_api_list(client, work_item_type):
    response = _get_mapping_usage(client, work_item_type=work_item_type, wi_id=_UNMATCHING_ID)
    assert response.status_code == HTTPStatus.OK
    assert response.get_json() == {"api": []}


def test_mapping_usage_sw_requirement_finds_api(client, api_sw_requirement_db):
    ut_api, ut_sr, _ = api_sw_requirement_db
    response = _get_mapping_usage(client, work_item_type="sw-requirement", wi_id=ut_sr.id)
    _assert_mapping_usage_ok(response, [ut_api.id])


def test_mapping_usage_document_finds_api(client, api_document_db):
    ut_api, ut_doc, _ = api_document_db
    response = _get_mapping_usage(client, work_item_type="document", wi_id=ut_doc.id)
    _assert_mapping_usage_ok(response, [ut_api.id])


def test_mapping_usage_justification_finds_api(client, api_justification_db):
    ut_api, ut_j, _ = api_justification_db
    response = _get_mapping_usage(client, work_item_type="justification", wi_id=ut_j.id)
    _assert_mapping_usage_ok(response, [ut_api.id])


def test_mapping_usage_test_specification_finds_api(client, api_test_specification_db):
    ut_api, ut_ts, _ = api_test_specification_db
    response = _get_mapping_usage(client, work_item_type="test-specification", wi_id=ut_ts.id)
    _assert_mapping_usage_ok(response, [ut_api.id])


def test_mapping_usage_test_case_direct_mapping_finds_api(client, api_test_case_db):
    ut_api, ut_tc, _ = api_test_case_db
    response = _get_mapping_usage(client, work_item_type="test-case", wi_id=ut_tc.id)
    _assert_mapping_usage_ok(response, [ut_api.id])


def test_mapping_usage_test_case_indirect_under_sw_requirement_finds_api(client, api_sr_tc_indirect_db):
    ut_api, ut_tc, _ = api_sr_tc_indirect_db
    response = _get_mapping_usage(client, work_item_type="test-case", wi_id=ut_tc.id)
    _assert_mapping_usage_ok(response, [ut_api.id])


def test_mapping_usage_no_match_when_only_api_exists(client, api_only_db):
    ut_api, _ = api_only_db
    response = _get_mapping_usage(client, work_item_type="sw-requirement", wi_id=_UNMATCHING_ID)
    assert response.status_code == HTTPStatus.OK
    assert response.get_json() == {"api": []}
    # ensure the created API is not spuriously listed
    assert ut_api.id not in {x["id"] for x in response.get_json().get("api", [])}
