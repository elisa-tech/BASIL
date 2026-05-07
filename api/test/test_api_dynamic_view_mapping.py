import os
import pytest
import tempfile
from http import HTTPStatus

from db.models.user import UserModel
from db.models.api import ApiModel
from db.models.sw_requirement import SwRequirementModel
from db.models.api_sw_requirement import ApiSwRequirementModel
from db.models.test_specification import TestSpecificationModel
from db.models.api_test_specification import ApiTestSpecificationModel
from db.models.test_case import TestCaseModel
from db.models.api_test_case import ApiTestCaseModel
from db.models.justification import JustificationModel
from db.models.api_justification import ApiJustificationModel
from db.models.document import DocumentModel
from db.models.api_document import ApiDocumentModel
from conftest import UT_USER_EMAIL


_DYNAMIC_VIEW_URL = "/mapping/api/dynamic-view"

_UT_API_NAME = "ut_api"
_UT_API_LIBRARY = "ut_api_library"
_UT_API_LIBRARY_VERSION = "v1.0.0"
_UT_API_CATEGORY = "ut_api_category"
_UT_API_IMPLEMENTATION_FILE_FROM_ROW = 0
_UT_API_IMPLEMENTATION_FILE_TO_ROW = 42
_UT_API_TAGS = "ut_api_tags"

_UT_SECTION_A = "Section Alpha for mapping."
_UT_SECTION_B = "Section Beta for mapping."
_UT_RAW_SPEC = f"BASIL UT: {_UT_SECTION_A} {_UT_SECTION_B} End."
_UT_RAW_RESTRICTED_SPEC = (
    'BASIL UT: "Reader" user is not able to read this API.'
    f" Used for {_DYNAMIC_VIEW_URL}."
)

_ALL_WORK_ITEM_KEYS = [
    "sw_requirements",
    "test_specifications",
    "test_cases",
    "justifications",
    "documents",
]


def _create_api_with_spec(client_db, utilities, raw_spec_content):
    user = client_db.session.query(UserModel).filter(UserModel.email == UT_USER_EMAIL).one()

    raw_spec = tempfile.NamedTemporaryFile(mode="w", delete=False)
    raw_spec.write(raw_spec_content)
    raw_spec.close()

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
    client_db.session.add(ut_api)
    client_db.session.commit()
    return ut_api, raw_spec.name, user


@pytest.fixture()
def api_db(client_db, ut_user_db, utilities):
    """Create an Api whose specification can be read (no mappings)."""
    ut_api, spec_path, _ = _create_api_with_spec(client_db, utilities, _UT_RAW_SPEC)
    yield ut_api
    if os.path.isfile(spec_path):
        os.remove(spec_path)


@pytest.fixture()
def restricted_api_db(client_db, ut_user_db, ut_reader_user_db, utilities):
    """Create an Api with read restriction for the 'reader' user."""
    ut_api, spec_path, _ = _create_api_with_spec(client_db, utilities, _UT_RAW_RESTRICTED_SPEC)
    ut_api.read_denials = f"[{ut_reader_user_db.id}]"
    client_db.session.commit()
    yield ut_api
    if os.path.isfile(spec_path):
        os.remove(spec_path)


@pytest.fixture()
def api_missing_spec_db(client_db, ut_user_db, utilities):
    """Create an Api whose raw_specification_url points to a nonexistent file."""
    user = client_db.session.query(UserModel).filter(UserModel.email == UT_USER_EMAIL).one()
    ut_api = ApiModel(
        _UT_API_NAME + "#" + utilities.generate_random_hex_string8(),
        _UT_API_LIBRARY,
        _UT_API_LIBRARY_VERSION,
        "/tmp/basil_ut_nonexistent_spec_" + utilities.generate_random_hex_string8(),
        _UT_API_CATEGORY,
        utilities.generate_random_hex_string8(),
        "stub.impl",
        _UT_API_IMPLEMENTATION_FILE_FROM_ROW,
        _UT_API_IMPLEMENTATION_FILE_TO_ROW,
        _UT_API_TAGS,
        user,
    )
    client_db.session.add(ut_api)
    client_db.session.commit()
    yield ut_api


@pytest.fixture()
def mapped_api_db(client_db, ut_user_db, utilities):
    """Create an Api with one mapping of each work-item type on _UT_SECTION_A."""
    ut_api, spec_path, user = _create_api_with_spec(client_db, utilities, _UT_RAW_SPEC)
    offset_a = _UT_RAW_SPEC.find(_UT_SECTION_A)

    sr = SwRequirementModel(
        f"SR #{utilities.generate_random_hex_string8()}",
        "SW shall work.", user,
    )
    client_db.session.add(sr)
    client_db.session.flush()
    client_db.session.add(ApiSwRequirementModel(ut_api, sr, _UT_SECTION_A, offset_a, 0, user))

    ts = TestSpecificationModel(
        f"TS #{utilities.generate_random_hex_string8()}",
        "preconditions", "test desc", "expected", user,
    )
    client_db.session.add(ts)
    client_db.session.flush()
    client_db.session.add(ApiTestSpecificationModel(ut_api, ts, _UT_SECTION_A, offset_a, 0, user))

    tc = TestCaseModel(
        "repo", "path/to/test.py",
        f"TC #{utilities.generate_random_hex_string8()}",
        "test case desc", user,
    )
    client_db.session.add(tc)
    client_db.session.flush()
    client_db.session.add(ApiTestCaseModel(ut_api, tc, _UT_SECTION_A, offset_a, 0, user))

    j = JustificationModel("justification desc", user)
    client_db.session.add(j)
    client_db.session.flush()
    client_db.session.add(ApiJustificationModel(ut_api, j, _UT_SECTION_A, offset_a, 0, user))

    doc = DocumentModel(
        f"Doc #{utilities.generate_random_hex_string8()}",
        "document desc", "file", "", "", "", -1, -1, user,
    )
    client_db.session.add(doc)
    client_db.session.flush()
    client_db.session.add(ApiDocumentModel(ut_api, doc, _UT_SECTION_A, offset_a, 0, user))

    client_db.session.commit()

    yield ut_api
    if os.path.isfile(spec_path):
        os.remove(spec_path)


@pytest.fixture()
def multi_snippet_api_db(client_db, ut_user_db, utilities):
    """Create an Api where the same SW requirement is mapped to two different sections."""
    ut_api, spec_path, user = _create_api_with_spec(client_db, utilities, _UT_RAW_SPEC)
    offset_a = _UT_RAW_SPEC.find(_UT_SECTION_A)
    offset_b = _UT_RAW_SPEC.find(_UT_SECTION_B)

    sr = SwRequirementModel(
        f"SR #{utilities.generate_random_hex_string8()}",
        "Shared requirement.", user,
    )
    client_db.session.add(sr)
    client_db.session.flush()
    client_db.session.add(ApiSwRequirementModel(ut_api, sr, _UT_SECTION_A, offset_a, 10, user))
    client_db.session.add(ApiSwRequirementModel(ut_api, sr, _UT_SECTION_B, offset_b, 20, user))
    client_db.session.commit()

    yield ut_api
    if os.path.isfile(spec_path):
        os.remove(spec_path)


def test_login(user_authentication):
    assert user_authentication.status_code == HTTPStatus.OK


# --- GET: auth & error handling ---


def test_get_unauthorized_ok(client, api_db):
    """GET without credentials on a non-restricted Api succeeds."""
    response = client.get(_DYNAMIC_VIEW_URL, query_string={"api-id": api_db.id})
    assert response.status_code == HTTPStatus.OK


def test_get_unauthorized_fail(client, restricted_api_db):
    """GET without credentials on a restricted Api is rejected."""
    response = client.get(_DYNAMIC_VIEW_URL, query_string={"api-id": restricted_api_db.id})
    assert response.status_code == HTTPStatus.UNAUTHORIZED


def test_get_authorized_restricted_fail(client, reader_authentication, restricted_api_db):
    """GET as the denied reader on a restricted Api is rejected."""
    get_query = {
        "user-id": reader_authentication.json["id"],
        "token": reader_authentication.json["token"],
        "api-id": restricted_api_db.id,
    }
    response = client.get(_DYNAMIC_VIEW_URL, query_string=get_query)
    assert response.status_code == HTTPStatus.UNAUTHORIZED


def test_get_authorized_restricted_ok(client, user_authentication, restricted_api_db):
    """GET as the Api author on a restricted Api succeeds."""
    get_query = {
        "user-id": user_authentication.json["id"],
        "token": user_authentication.json["token"],
        "api-id": restricted_api_db.id,
    }
    response = client.get(_DYNAMIC_VIEW_URL, query_string=get_query)
    assert response.status_code == HTTPStatus.OK


@pytest.mark.usefixtures("api_db")
def test_get_missing_api_id(client, user_authentication):
    """GET without api-id returns BAD_REQUEST."""
    get_query = {
        "user-id": user_authentication.json["id"],
        "token": user_authentication.json["token"],
    }
    response = client.get(_DYNAMIC_VIEW_URL, query_string=get_query)
    assert response.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.usefixtures("api_db")
def test_get_nonexistent_api(client_db, client, user_authentication):
    """GET with a non-existent api-id returns NOT_FOUND."""
    non_existent_id = 42000
    assert client_db.session.query(ApiModel).get(non_existent_id) is None

    get_query = {
        "user-id": user_authentication.json["id"],
        "token": user_authentication.json["token"],
        "api-id": non_existent_id,
    }
    response = client.get(_DYNAMIC_VIEW_URL, query_string=get_query)
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_get_missing_specification_file(client, user_authentication, api_missing_spec_db):
    """GET when the raw specification file does not exist returns NOT_FOUND."""
    get_query = {
        "user-id": user_authentication.json["id"],
        "token": user_authentication.json["token"],
        "api-id": api_missing_spec_db.id,
    }
    response = client.get(_DYNAMIC_VIEW_URL, query_string=get_query)
    assert response.status_code == HTTPStatus.NOT_FOUND


# --- GET: response structure ---


def test_get_returns_specification_text(client, api_db):
    """Response contains the full specification string."""
    response = client.get(_DYNAMIC_VIEW_URL, query_string={"api-id": api_db.id})
    assert response.status_code == HTTPStatus.OK
    assert response.json["specification"] == _UT_RAW_SPEC


def test_get_empty_api_has_all_keys(client, api_db):
    """An Api with no mappings returns empty lists for every work-item type."""
    response = client.get(_DYNAMIC_VIEW_URL, query_string={"api-id": api_db.id})
    assert response.status_code == HTTPStatus.OK

    data = response.json
    assert "specification" in data
    for key in _ALL_WORK_ITEM_KEYS:
        assert key in data, f"missing key '{key}'"
        assert data[key] == []


# --- GET: with mappings ---


def test_get_mapped_returns_all_types(client, mapped_api_db):
    """An Api with one mapping of each type returns exactly one group per type."""
    response = client.get(_DYNAMIC_VIEW_URL, query_string={"api-id": mapped_api_db.id})
    assert response.status_code == HTTPStatus.OK

    data = response.json
    assert len(data["sw_requirements"]) == 1
    assert len(data["test_specifications"]) == 1
    assert len(data["test_cases"]) == 1
    assert len(data["justifications"]) == 1
    assert len(data["documents"]) == 1


def test_get_mapped_group_has_snippets(client, mapped_api_db):
    """Each work-item group contains a 'snippets' list with at least one entry."""
    response = client.get(_DYNAMIC_VIEW_URL, query_string={"api-id": mapped_api_db.id})
    assert response.status_code == HTTPStatus.OK

    data = response.json
    for key in _ALL_WORK_ITEM_KEYS:
        for group in data[key]:
            assert "snippets" in group
            assert len(group["snippets"]) >= 1


def test_get_mapped_snippet_fields(client, mapped_api_db):
    """Snippets carry section, offset, relation_id, coverage, covered, and match."""
    response = client.get(_DYNAMIC_VIEW_URL, query_string={"api-id": mapped_api_db.id})
    assert response.status_code == HTTPStatus.OK

    expected_snippet_keys = {"section", "offset", "relation_id", "coverage", "covered", "match", "__tablename__"}
    data = response.json
    for key in _ALL_WORK_ITEM_KEYS:
        for group in data[key]:
            for snippet in group["snippets"]:
                assert expected_snippet_keys.issubset(snippet.keys()), (
                    f"snippet in '{key}' missing keys: {expected_snippet_keys - snippet.keys()}"
                )


def test_get_mapped_snippet_match_flag(client, mapped_api_db):
    """Snippets whose section text matches the specification at the given offset have match=True."""
    response = client.get(_DYNAMIC_VIEW_URL, query_string={"api-id": mapped_api_db.id})
    assert response.status_code == HTTPStatus.OK

    data = response.json
    for key in _ALL_WORK_ITEM_KEYS:
        for group in data[key]:
            for snippet in group["snippets"]:
                assert snippet["section"] == _UT_SECTION_A
                assert snippet["match"] is True


def test_get_mapped_sr_group_has_work_item(client, mapped_api_db):
    """SW-requirement groups contain the 'sw_requirement' dict with at least a title."""
    response = client.get(_DYNAMIC_VIEW_URL, query_string={"api-id": mapped_api_db.id})
    assert response.status_code == HTTPStatus.OK

    sr_groups = response.json["sw_requirements"]
    assert len(sr_groups) == 1
    assert "sw_requirement" in sr_groups[0]
    assert "title" in sr_groups[0]["sw_requirement"]


def test_get_mapped_ts_group_has_work_item(client, mapped_api_db):
    """Test-specification groups contain the 'test_specification' dict."""
    response = client.get(_DYNAMIC_VIEW_URL, query_string={"api-id": mapped_api_db.id})
    assert response.status_code == HTTPStatus.OK

    ts_groups = response.json["test_specifications"]
    assert len(ts_groups) == 1
    assert "test_specification" in ts_groups[0]
    assert "title" in ts_groups[0]["test_specification"]


def test_get_mapped_tc_group_has_work_item(client, mapped_api_db):
    """Test-case groups contain the 'test_case' dict."""
    response = client.get(_DYNAMIC_VIEW_URL, query_string={"api-id": mapped_api_db.id})
    assert response.status_code == HTTPStatus.OK

    tc_groups = response.json["test_cases"]
    assert len(tc_groups) == 1
    assert "test_case" in tc_groups[0]
    assert "title" in tc_groups[0]["test_case"]


def test_get_mapped_justification_group_has_work_item(client, mapped_api_db):
    """Justification groups contain the 'justification' dict."""
    response = client.get(_DYNAMIC_VIEW_URL, query_string={"api-id": mapped_api_db.id})
    assert response.status_code == HTTPStatus.OK

    j_groups = response.json["justifications"]
    assert len(j_groups) == 1
    assert "justification" in j_groups[0]


def test_get_mapped_document_group_has_work_item(client, mapped_api_db):
    """Document groups contain the 'document' dict."""
    response = client.get(_DYNAMIC_VIEW_URL, query_string={"api-id": mapped_api_db.id})
    assert response.status_code == HTTPStatus.OK

    doc_groups = response.json["documents"]
    assert len(doc_groups) == 1
    assert "document" in doc_groups[0]
    assert "title" in doc_groups[0]["document"]


# --- GET: deduplication ---


def test_get_multi_snippet_deduplication(client, multi_snippet_api_db):
    """Two mappings of the same SW requirement produce one group with two snippets."""
    response = client.get(_DYNAMIC_VIEW_URL, query_string={"api-id": multi_snippet_api_db.id})
    assert response.status_code == HTTPStatus.OK

    sr_groups = response.json["sw_requirements"]
    assert len(sr_groups) == 1
    snippets = sr_groups[0]["snippets"]
    assert len(snippets) == 2

    sections = {s["section"] for s in snippets}
    assert sections == {_UT_SECTION_A, _UT_SECTION_B}


def test_get_multi_snippet_coverage_values(client, multi_snippet_api_db):
    """Each snippet in a deduplicated group retains its own coverage value."""
    response = client.get(_DYNAMIC_VIEW_URL, query_string={"api-id": multi_snippet_api_db.id})
    assert response.status_code == HTTPStatus.OK

    snippets = response.json["sw_requirements"][0]["snippets"]
    coverages = {s["section"]: s["coverage"] for s in snippets}
    assert coverages[_UT_SECTION_A] == 10
    assert coverages[_UT_SECTION_B] == 20


# --- GET: SR children on matching snippets ---


def test_get_sr_snippet_has_children_keys(client, mapped_api_db):
    """Matching SR snippets carry children keys for nested work items."""
    response = client.get(_DYNAMIC_VIEW_URL, query_string={"api-id": mapped_api_db.id})
    assert response.status_code == HTTPStatus.OK

    sr_groups = response.json["sw_requirements"]
    for group in sr_groups:
        for snippet in group["snippets"]:
            if snippet["match"]:
                assert "sw_requirements" in snippet
                assert "test_specifications" in snippet
                assert "test_cases" in snippet
