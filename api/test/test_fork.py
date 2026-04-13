import pytest
from http import HTTPStatus
from db.models.user import UserModel
from db.models.api import ApiModel
from db.models.sw_requirement import SwRequirementModel
from db.models.test_specification import TestSpecificationModel
from db.models.test_case import TestCaseModel
from db.models.document import DocumentModel
from db.models.justification import JustificationModel
from db.models.api_sw_requirement import ApiSwRequirementModel
from db.models.api_test_specification import ApiTestSpecificationModel
from db.models.api_test_case import ApiTestCaseModel
from db.models.api_document import ApiDocumentModel
from db.models.api_justification import ApiJustificationModel
from db.models.sw_requirement_sw_requirement import SwRequirementSwRequirementModel
from db.models.sw_requirement_test_specification import SwRequirementTestSpecificationModel
from db.models.sw_requirement_test_case import SwRequirementTestCaseModel
from db.models.document_document import DocumentDocumentModel
from db.models.test_specification_test_case import TestSpecificationTestCaseModel
from conftest import UT_USER_EMAIL

_FORK_API_SR_URL = '/fork/api/sw-requirement'
_FORK_SR_SR_URL = '/fork/sw-requirement/sw-requirement'
_FORK_API_DOC_URL = '/fork/api/document'
_FORK_DOC_DOC_URL = '/fork/document/document'
_FORK_API_TS_URL = '/fork/api/test-specification'
_FORK_SR_TS_URL = '/fork/sw-requirement/test-specification'
_FORK_API_TC_URL = '/fork/api/test-case'
_FORK_SR_TC_URL = '/fork/sw-requirement/test-case'
_FORK_TS_TC_URL = '/fork/test-specification/test-case'
_FORK_API_J_URL = '/fork/api/justification'

_ALL_FORK_URLS = [
    _FORK_API_SR_URL,
    _FORK_SR_SR_URL,
    _FORK_API_DOC_URL,
    _FORK_DOC_DOC_URL,
    _FORK_API_TS_URL,
    _FORK_SR_TS_URL,
    _FORK_API_TC_URL,
    _FORK_SR_TC_URL,
    _FORK_TS_TC_URL,
    _FORK_API_J_URL,
]

UNMATCHING_ID = 99999

_UT_API_NAME = 'ut_fork_api'
_UT_API_LIBRARY = 'ut_fork_library'
_UT_API_LIBRARY_VERSION = 'v1.0.0'
_UT_API_CATEGORY = 'ut_fork_category'
_UT_API_IMPLEMENTATION_FILE_FROM_ROW = 0
_UT_API_IMPLEMENTATION_FILE_TO_ROW = 42
_UT_API_TAGS = 'ut_fork_tags'


def _get_user(client_db):
    return client_db.session.query(UserModel).filter(
        UserModel.email == UT_USER_EMAIL
    ).one()


def _create_api(client_db, utilities):
    user = _get_user(client_db)
    ut_api = ApiModel(
        _UT_API_NAME + '#' + utilities.generate_random_hex_string8(),
        _UT_API_LIBRARY, _UT_API_LIBRARY_VERSION, 'stub.md',
        _UT_API_CATEGORY, utilities.generate_random_hex_string8(), 'stub.impl',
        _UT_API_IMPLEMENTATION_FILE_FROM_ROW, _UT_API_IMPLEMENTATION_FILE_TO_ROW,
        _UT_API_TAGS, user
    )
    client_db.session.add(ut_api)
    client_db.session.commit()
    return ut_api


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def api_sr_mapping(client_db, ut_user_db, utilities):
    """API -> SwRequirement mapping."""
    user = _get_user(client_db)
    api = _create_api(client_db, utilities)
    sr = SwRequirementModel(
        f'SR #{utilities.generate_random_hex_string8()}', 'Fork test SR', user
    )
    mapping = ApiSwRequirementModel(api, sr, 'section', 0, 50, user)
    client_db.session.add(sr)
    client_db.session.add(mapping)
    client_db.session.commit()
    yield api, sr, mapping


@pytest.fixture()
def sr_sr_mapping(client_db, ut_user_db, utilities):
    """API -> SwRequirement -> SwRequirement mapping."""
    user = _get_user(client_db)
    api = _create_api(client_db, utilities)
    parent_sr = SwRequirementModel(
        f'Parent SR #{utilities.generate_random_hex_string8()}', 'Parent SR', user
    )
    api_sr = ApiSwRequirementModel(api, parent_sr, 'section', 0, 50, user)
    child_sr = SwRequirementModel(
        f'Child SR #{utilities.generate_random_hex_string8()}', 'Child SR', user
    )
    sr_sr = SwRequirementSwRequirementModel(
        sw_requirement_mapping_api=api_sr,
        sw_requirement_mapping_sw_requirement=None,
        sw_requirement=child_sr,
        coverage=50,
        created_by=user
    )
    client_db.session.add(parent_sr)
    client_db.session.add(api_sr)
    client_db.session.add(child_sr)
    client_db.session.add(sr_sr)
    client_db.session.commit()
    yield api, api_sr, sr_sr


@pytest.fixture()
def api_doc_mapping(client_db, ut_user_db, utilities):
    """API -> Document mapping."""
    user = _get_user(client_db)
    api = _create_api(client_db, utilities)
    doc = DocumentModel(
        f'Doc #{utilities.generate_random_hex_string8()}', 'Fork test doc',
        'file', 'relates-to', 'stub.md', 'section', 0, 0, user
    )
    mapping = ApiDocumentModel(api, doc, 'section', 0, 50, user)
    client_db.session.add(doc)
    client_db.session.add(mapping)
    client_db.session.commit()
    yield api, doc, mapping


@pytest.fixture()
def doc_doc_mapping(client_db, ut_user_db, utilities):
    """API -> Document -> Document mapping."""
    user = _get_user(client_db)
    api = _create_api(client_db, utilities)
    parent_doc = DocumentModel(
        f'Parent Doc #{utilities.generate_random_hex_string8()}', 'Parent doc',
        'file', 'relates-to', 'stub.md', 'section', 0, 0, user
    )
    api_doc = ApiDocumentModel(api, parent_doc, 'section', 0, 50, user)
    child_doc = DocumentModel(
        f'Child Doc #{utilities.generate_random_hex_string8()}', 'Child doc',
        'file', 'relates-to', 'stub.md', 'section', 0, 0, user
    )
    doc_doc = DocumentDocumentModel(
        document_mapping_api=api_doc,
        document_mapping_document=None,
        document=child_doc,
        section='nested section',
        offset=0,
        coverage=50,
        created_by=user
    )
    client_db.session.add(parent_doc)
    client_db.session.add(api_doc)
    client_db.session.add(child_doc)
    client_db.session.add(doc_doc)
    client_db.session.commit()
    yield api, api_doc, doc_doc


@pytest.fixture()
def api_ts_mapping(client_db, ut_user_db, utilities):
    """API -> TestSpecification mapping."""
    user = _get_user(client_db)
    api = _create_api(client_db, utilities)
    ts = TestSpecificationModel(
        f'TS #{utilities.generate_random_hex_string8()}', 'preconditions',
        'test description', 'expected behavior', user
    )
    mapping = ApiTestSpecificationModel(api, ts, 'section', 0, 50, user)
    client_db.session.add(ts)
    client_db.session.add(mapping)
    client_db.session.commit()
    yield api, ts, mapping


@pytest.fixture()
def sr_ts_mapping(client_db, ut_user_db, utilities):
    """API -> SwRequirement -> TestSpecification mapping."""
    user = _get_user(client_db)
    api = _create_api(client_db, utilities)
    sr = SwRequirementModel(
        f'SR #{utilities.generate_random_hex_string8()}', 'SR for TS', user
    )
    api_sr = ApiSwRequirementModel(api, sr, 'section', 0, 50, user)
    ts = TestSpecificationModel(
        f'TS #{utilities.generate_random_hex_string8()}', 'preconditions',
        'test description', 'expected behavior', user
    )
    sr_ts = SwRequirementTestSpecificationModel(
        sw_requirement_mapping_api=api_sr,
        sw_requirement_mapping_sw_requirement=None,
        test_specification=ts,
        coverage=50,
        created_by=user
    )
    client_db.session.add(sr)
    client_db.session.add(api_sr)
    client_db.session.add(ts)
    client_db.session.add(sr_ts)
    client_db.session.commit()
    yield api, api_sr, sr_ts


@pytest.fixture()
def api_tc_mapping(client_db, ut_user_db, utilities):
    """API -> TestCase mapping."""
    user = _get_user(client_db)
    api = _create_api(client_db, utilities)
    tc = TestCaseModel(
        'https://github.com/example/repo', 'tests/test_example.py',
        f'TC #{utilities.generate_random_hex_string8()}', 'test case desc', user
    )
    mapping = ApiTestCaseModel(api, tc, 'section', 0, 50, user)
    client_db.session.add(tc)
    client_db.session.add(mapping)
    client_db.session.commit()
    yield api, tc, mapping


@pytest.fixture()
def sr_tc_mapping(client_db, ut_user_db, utilities):
    """API -> SwRequirement -> TestCase mapping."""
    user = _get_user(client_db)
    api = _create_api(client_db, utilities)
    sr = SwRequirementModel(
        f'SR #{utilities.generate_random_hex_string8()}', 'SR for TC', user
    )
    api_sr = ApiSwRequirementModel(api, sr, 'section', 0, 50, user)
    tc = TestCaseModel(
        'https://github.com/example/repo', 'tests/test_example.py',
        f'TC #{utilities.generate_random_hex_string8()}', 'test case desc', user
    )
    sr_tc = SwRequirementTestCaseModel(
        sw_requirement_mapping_api=api_sr,
        sw_requirement_mapping_sw_requirement=None,
        test_case=tc,
        coverage=50,
        created_by=user
    )
    client_db.session.add(sr)
    client_db.session.add(api_sr)
    client_db.session.add(tc)
    client_db.session.add(sr_tc)
    client_db.session.commit()
    yield api, api_sr, sr_tc


@pytest.fixture()
def ts_tc_mapping_via_api(client_db, ut_user_db, utilities):
    """API -> TestSpecification -> TestCase mapping."""
    user = _get_user(client_db)
    api = _create_api(client_db, utilities)
    ts = TestSpecificationModel(
        f'TS #{utilities.generate_random_hex_string8()}', 'preconditions',
        'test description', 'expected behavior', user
    )
    api_ts = ApiTestSpecificationModel(api, ts, 'section', 0, 50, user)
    tc = TestCaseModel(
        'https://github.com/example/repo', 'tests/test_example.py',
        f'TC #{utilities.generate_random_hex_string8()}', 'test case desc', user
    )
    ts_tc = TestSpecificationTestCaseModel(
        test_specification_mapping_api=api_ts,
        test_specification_mapping_sw_requirement=None,
        test_case=tc,
        coverage=50,
        created_by=user
    )
    client_db.session.add(ts)
    client_db.session.add(api_ts)
    client_db.session.add(tc)
    client_db.session.add(ts_tc)
    client_db.session.commit()
    yield api, api_ts, ts_tc


@pytest.fixture()
def ts_tc_mapping_via_sr(client_db, ut_user_db, utilities):
    """API -> SwRequirement -> TestSpecification -> TestCase mapping."""
    user = _get_user(client_db)
    api = _create_api(client_db, utilities)
    sr = SwRequirementModel(
        f'SR #{utilities.generate_random_hex_string8()}', 'SR for TS-TC', user
    )
    api_sr = ApiSwRequirementModel(api, sr, 'section', 0, 50, user)
    ts = TestSpecificationModel(
        f'TS #{utilities.generate_random_hex_string8()}', 'preconditions',
        'test description', 'expected behavior', user
    )
    sr_ts = SwRequirementTestSpecificationModel(
        sw_requirement_mapping_api=api_sr,
        sw_requirement_mapping_sw_requirement=None,
        test_specification=ts,
        coverage=50,
        created_by=user
    )
    tc = TestCaseModel(
        'https://github.com/example/repo', 'tests/test_example.py',
        f'TC #{utilities.generate_random_hex_string8()}', 'test case desc', user
    )
    ts_tc = TestSpecificationTestCaseModel(
        test_specification_mapping_api=None,
        test_specification_mapping_sw_requirement=sr_ts,
        test_case=tc,
        coverage=50,
        created_by=user
    )
    client_db.session.add(sr)
    client_db.session.add(api_sr)
    client_db.session.add(ts)
    client_db.session.add(sr_ts)
    client_db.session.add(tc)
    client_db.session.add(ts_tc)
    client_db.session.commit()
    yield api, sr_ts, ts_tc


@pytest.fixture()
def api_j_mapping(client_db, ut_user_db, utilities):
    """API -> Justification mapping."""
    user = _get_user(client_db)
    api = _create_api(client_db, utilities)
    justification = JustificationModel('Fork test justification', user)
    mapping = ApiJustificationModel(api, justification, 'section', 0, 50, user)
    client_db.session.add(justification)
    client_db.session.add(mapping)
    client_db.session.commit()
    yield api, justification, mapping


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

def test_login(user_authentication):
    """Ensure the test user is logged in."""
    assert user_authentication.status_code == HTTPStatus.OK


# ---------------------------------------------------------------------------
# Common error handling (parametrized across all fork URLs)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize('url', _ALL_FORK_URLS)
def test_fork_missing_mandatory_fields(client, user_authentication, url):
    """POST without relation-id returns BAD_REQUEST."""
    response = client.post(url, json={
        'user-id': user_authentication.json['id'],
        'token': user_authentication.json['token']
    })
    assert response.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.parametrize('url', _ALL_FORK_URLS)
def test_fork_unexisting_relation_id(client, user_authentication, url):
    """POST with a non-existent relation-id returns NOT_FOUND."""
    response = client.post(url, json={
        'relation-id': UNMATCHING_ID,
        'user-id': user_authentication.json['id'],
        'token': user_authentication.json['token']
    })
    assert response.status_code == HTTPStatus.NOT_FOUND


# ---------------------------------------------------------------------------
# Happy-path tests
# ---------------------------------------------------------------------------

def test_fork_api_sw_requirement_ok(client, user_authentication, api_sr_mapping):
    """Fork a Sw Requirement mapped to an API."""
    api, sr, mapping = api_sr_mapping
    original_sr_id = sr.id

    response = client.post(_FORK_API_SR_URL, json={
        'relation-id': mapping.id,
        'user-id': user_authentication.json['id'],
        'token': user_authentication.json['token']
    })
    assert response.status_code == HTTPStatus.CREATED
    assert isinstance(response.json, dict)
    assert response.json.get('relation_id') == mapping.id
    assert response.json['sw_requirement']['id'] != original_sr_id


def test_fork_sr_sr_ok(client, user_authentication, sr_sr_mapping):
    """Fork a Sw Requirement mapped to another Sw Requirement."""
    api, api_sr, sr_sr = sr_sr_mapping
    original_sr_id = sr_sr.sw_requirement_id

    response = client.post(_FORK_SR_SR_URL, json={
        'relation-id': sr_sr.id,
        'user-id': user_authentication.json['id'],
        'token': user_authentication.json['token']
    })
    assert response.status_code == HTTPStatus.CREATED
    assert isinstance(response.json, dict)
    assert response.json.get('relation_id') == sr_sr.id
    assert response.json['sw_requirement']['id'] != original_sr_id


def test_fork_api_document_ok(client, user_authentication, api_doc_mapping):
    """Fork a Document mapped to an API."""
    api, doc, mapping = api_doc_mapping
    original_doc_id = doc.id

    response = client.post(_FORK_API_DOC_URL, json={
        'relation-id': mapping.id,
        'user-id': user_authentication.json['id'],
        'token': user_authentication.json['token']
    })
    assert response.status_code == HTTPStatus.CREATED
    assert isinstance(response.json, dict)
    assert response.json.get('relation_id') == mapping.id
    assert response.json['document']['id'] != original_doc_id


def test_fork_document_document_ok(client, user_authentication, doc_doc_mapping):
    """Fork a Document mapped to another Document."""
    api, api_doc, doc_doc = doc_doc_mapping
    original_doc_id = doc_doc.document_id

    response = client.post(_FORK_DOC_DOC_URL, json={
        'relation-id': doc_doc.id,
        'user-id': user_authentication.json['id'],
        'token': user_authentication.json['token']
    })
    assert response.status_code == HTTPStatus.CREATED
    assert isinstance(response.json, dict)
    assert response.json.get('relation_id') == doc_doc.id
    assert response.json['document']['id'] != original_doc_id


def test_fork_api_test_specification_ok(client, user_authentication, api_ts_mapping):
    """Fork a Test Specification mapped to an API."""
    api, ts, mapping = api_ts_mapping
    original_ts_id = ts.id

    response = client.post(_FORK_API_TS_URL, json={
        'relation-id': mapping.id,
        'user-id': user_authentication.json['id'],
        'token': user_authentication.json['token']
    })
    assert response.status_code == HTTPStatus.CREATED
    assert isinstance(response.json, dict)
    assert response.json.get('relation_id') == mapping.id
    assert response.json['test_specification']['id'] != original_ts_id


def test_fork_sr_test_specification_ok(client, user_authentication, sr_ts_mapping):
    """Fork a Test Specification mapped to a Sw Requirement."""
    api, api_sr, sr_ts = sr_ts_mapping
    original_ts_id = sr_ts.test_specification_id

    response = client.post(_FORK_SR_TS_URL, json={
        'relation-id': sr_ts.id,
        'user-id': user_authentication.json['id'],
        'token': user_authentication.json['token']
    })
    assert response.status_code == HTTPStatus.CREATED
    assert isinstance(response.json, dict)
    assert response.json.get('relation_id') == sr_ts.id
    assert response.json['test_specification']['id'] != original_ts_id


def test_fork_api_test_case_ok(client, user_authentication, api_tc_mapping):
    """Fork a Test Case mapped to an API."""
    api, tc, mapping = api_tc_mapping
    original_tc_id = tc.id

    response = client.post(_FORK_API_TC_URL, json={
        'relation-id': mapping.id,
        'user-id': user_authentication.json['id'],
        'token': user_authentication.json['token']
    })
    assert response.status_code == HTTPStatus.CREATED
    assert isinstance(response.json, dict)
    assert response.json.get('relation_id') == mapping.id
    assert response.json['test_case']['id'] != original_tc_id


def test_fork_sr_test_case_ok(client, user_authentication, sr_tc_mapping):
    """Fork a Test Case mapped to a Sw Requirement."""
    api, api_sr, sr_tc = sr_tc_mapping
    original_tc_id = sr_tc.test_case_id

    response = client.post(_FORK_SR_TC_URL, json={
        'relation-id': sr_tc.id,
        'user-id': user_authentication.json['id'],
        'token': user_authentication.json['token']
    })
    assert response.status_code == HTTPStatus.CREATED
    assert isinstance(response.json, dict)
    assert response.json.get('relation_id') == sr_tc.id
    assert response.json['test_case']['id'] != original_tc_id


def test_fork_ts_test_case_via_api_ok(client, user_authentication, ts_tc_mapping_via_api):
    """Fork a Test Case mapped to a Test Specification (parent mapped to API)."""
    api, api_ts, ts_tc = ts_tc_mapping_via_api
    original_tc_id = ts_tc.test_case_id

    response = client.post(_FORK_TS_TC_URL, json={
        'relation-id': ts_tc.id,
        'user-id': user_authentication.json['id'],
        'token': user_authentication.json['token']
    })
    assert response.status_code == HTTPStatus.CREATED
    assert isinstance(response.json, dict)
    assert response.json.get('relation_id') == ts_tc.id
    assert response.json['test_case']['id'] != original_tc_id


def test_fork_ts_test_case_via_sr_ok(client, user_authentication, ts_tc_mapping_via_sr):
    """Fork a Test Case mapped to a Test Specification (parent mapped to Sw Requirement)."""
    api, sr_ts, ts_tc = ts_tc_mapping_via_sr
    original_tc_id = ts_tc.test_case_id

    response = client.post(_FORK_TS_TC_URL, json={
        'relation-id': ts_tc.id,
        'user-id': user_authentication.json['id'],
        'token': user_authentication.json['token']
    })
    assert response.status_code == HTTPStatus.CREATED
    assert isinstance(response.json, dict)
    assert response.json.get('relation_id') == ts_tc.id
    assert response.json['test_case']['id'] != original_tc_id


def test_fork_api_justification_ok(client, user_authentication, api_j_mapping):
    """Fork a Justification mapped to an API."""
    api, justification, mapping = api_j_mapping
    original_j_id = justification.id

    response = client.post(_FORK_API_J_URL, json={
        'relation-id': mapping.id,
        'user-id': user_authentication.json['id'],
        'token': user_authentication.json['token']
    })
    assert response.status_code == HTTPStatus.CREATED
    assert isinstance(response.json, dict)
    assert response.json.get('relation_id') == mapping.id
    assert response.json['justification']['id'] != original_j_id
