"""HTTP tests for GET /apis/history (ApiHistory)."""
import os
import tempfile
from http import HTTPStatus

import pytest

from db.models.api import ApiModel
from db.models.user import UserModel
from conftest import UT_USER_EMAIL

_API_HISTORY_URL = "/apis/history"
_APIS_URL = "/apis"

_UT_API_NAME = "ut_api_history"
_UT_API_LIBRARY = "ut_api_history_library"
_UT_API_LIBRARY_VERSION = "v1.0.0"
_UT_API_CATEGORY = "ut_api_history_category"
_UT_API_IMPLEMENTATION_FILE_FROM_ROW = 0
_UT_API_IMPLEMENTATION_FILE_TO_ROW = 42
_UT_API_TAGS = "ut_api_history_tags"

_UNMATCHING_API_ID = 9_999_999


def _auth_query(user_authentication):
    """Build query string dict with auth fields from a login response."""
    return {
        "user-id": user_authentication.json["id"],
        "token": user_authentication.json["token"],
    }


def _get_api_history(client, user_authentication, api_id):
    """GET /apis/history with auth and api-id as query string parameters."""
    qs = {**_auth_query(user_authentication), "api-id": api_id}
    return client.get(_API_HISTORY_URL, query_string=qs)


def _create_api_via_orm(client_db, utilities):
    """Insert an ApiModel directly via ORM; returns (raw_spec_path, api_row)."""
    user = client_db.session.query(UserModel).filter(UserModel.email == UT_USER_EMAIL).one()

    raw_spec = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt")
    raw_spec.write("BASIL UT: API History raw specification content.")
    raw_spec.close()

    ut_api = ApiModel(
        _UT_API_NAME + "#" + utilities.generate_random_hex_string8(),
        _UT_API_LIBRARY,
        _UT_API_LIBRARY_VERSION,
        raw_spec.name,
        _UT_API_CATEGORY,
        utilities.generate_random_hex_string8(),
        raw_spec.name + "_impl",
        _UT_API_IMPLEMENTATION_FILE_FROM_ROW,
        _UT_API_IMPLEMENTATION_FILE_TO_ROW,
        _UT_API_TAGS,
        user,
    )
    client_db.session.add(ut_api)
    client_db.session.commit()
    return raw_spec.name, ut_api


def _create_api_via_http(client, user_authentication, utilities):
    """Create an API via POST /apis; returns (response, api_name)."""
    auth = _auth_query(user_authentication)
    api_name = f"ut_api_history_http_{utilities.generate_random_hex_string8()}"
    payload = {
        "user-id": auth["user-id"],
        "token": auth["token"],
        "action": "add",
        "api": api_name,
        "category": _UT_API_CATEGORY,
        "library": _UT_API_LIBRARY,
        "library-version": _UT_API_LIBRARY_VERSION,
        "raw-specification-url": os.path.realpath(__file__),
        "tags": _UT_API_TAGS,
        "implementation-file": "",
        "implementation-file-from-row": _UT_API_IMPLEMENTATION_FILE_FROM_ROW,
        "implementation-file-to-row": _UT_API_IMPLEMENTATION_FILE_TO_ROW,
    }
    response = client.post(_APIS_URL, json=payload)
    return response, api_name


def _update_api_via_http(client, user_authentication, api_id, api_name, overrides=None):
    """PUT /apis to modify an existing API, creating a new history version."""
    auth = _auth_query(user_authentication)
    payload = {
        "user-id": auth["user-id"],
        "token": auth["token"],
        "api-id": api_id,
        "api": api_name,
        "category": "modified_category",
        "default-view": "",
        "checksum": "",
        "library": _UT_API_LIBRARY,
        "library-version": _UT_API_LIBRARY_VERSION,
        "raw-specification-url": os.path.realpath(__file__),
        "tags": "modified_tags",
        "implementation-file": "",
        "implementation-file-from-row": 0,
        "implementation-file-to-row": 1,
        "last_coverage": "0",
    }
    if overrides:
        payload.update(overrides)
    return client.put(_APIS_URL, json=payload)


def _assert_history_entry_shape(entry):
    """Verify that a single history entry has the expected top-level keys."""
    assert isinstance(entry, dict)
    assert "version" in entry
    assert "object" in entry
    assert "mapping" in entry
    assert "created_at" in entry
    assert isinstance(entry["object"], dict)
    assert isinstance(entry["mapping"], dict)


# -- Fixtures ----------------------------------------------------------------

@pytest.fixture()
def api_via_orm(client_db, ut_user_db, utilities):
    """Create an API via ORM (triggers after_insert -> history version 1)."""
    raw_spec_path, ut_api = _create_api_via_orm(client_db, utilities)
    yield ut_api

    if os.path.isfile(raw_spec_path):
        os.remove(raw_spec_path)


@pytest.fixture()
def api_via_http(client, user_authentication, utilities):
    """Create an API via HTTP POST and return its id."""
    response, api_name = _create_api_via_http(client, user_authentication, utilities)
    assert response.status_code == HTTPStatus.CREATED

    listed = client.get(_APIS_URL)
    assert listed.status_code == HTTPStatus.OK
    api = next(a for a in listed.get_json()["apis"] if a["api"] == api_name)
    yield api["id"]


@pytest.fixture()
def api_with_two_versions(client, user_authentication, utilities):
    """Create an API and update it once, producing history versions 1 and 2."""
    response, api_name = _create_api_via_http(client, user_authentication, utilities)
    assert response.status_code == HTTPStatus.CREATED

    listed = client.get(_APIS_URL)
    api = next(a for a in listed.get_json()["apis"] if a["api"] == api_name)
    api_id = api["id"]

    put_resp = _update_api_via_http(
        client, user_authentication, api_id, api_name,
        overrides={"tags": "modified_tags", "category": "modified_category"},
    )
    assert put_resp.status_code == HTTPStatus.OK

    yield api_id


# -- Tests: missing / bad request fields ------------------------------------

def test_api_history_missing_api_id(client, user_authentication):
    """api-id is mandatory via the permission decorator; omitting it returns 400."""
    qs = _auth_query(user_authentication)
    response = client.get(_API_HISTORY_URL, query_string=qs)
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_api_history_no_credentials(client, api_via_http):
    """Without user-id and token the request is treated as a guest access."""
    qs = {"api-id": api_via_http}
    response = client.get(_API_HISTORY_URL, query_string=qs)
    assert response.status_code in (HTTPStatus.OK, HTTPStatus.UNAUTHORIZED)


# -- Tests: not-found API ---------------------------------------------------

def test_api_history_not_found_api_id(client, user_authentication):
    """Nonexistent api-id returns 404."""
    response = _get_api_history(client, user_authentication, _UNMATCHING_API_ID)
    assert response.status_code == HTTPStatus.NOT_FOUND


# -- Tests: successful history retrieval with a single version ---------------

def test_api_history_single_version_orm(client, user_authentication, api_via_orm):
    """After ORM insert, history has exactly one entry at version '1'."""
    response = _get_api_history(client, user_authentication, api_via_orm.id)
    assert response.status_code == HTTPStatus.OK
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) == 1
    _assert_history_entry_shape(data[0])
    assert data[0]["version"] == "1"


def test_api_history_single_version_http(client, user_authentication, api_via_http):
    """After HTTP POST, history has exactly one entry at version '1'."""
    response = _get_api_history(client, user_authentication, api_via_http)
    assert response.status_code == HTTPStatus.OK
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) == 1
    _assert_history_entry_shape(data[0])
    assert data[0]["version"] == "1"


def test_api_history_single_version_object_fields(client, user_authentication, api_via_http):
    """The first history entry's object contains the expected API fields."""
    response = _get_api_history(client, user_authentication, api_via_http)
    assert response.status_code == HTTPStatus.OK
    data = response.get_json()
    entry = data[0]
    obj = entry["object"]
    assert "api" in obj
    assert "library" in obj
    assert "library_version" in obj
    assert "created_by" in obj


def test_api_history_single_version_mapping_is_empty(client, user_authentication, api_via_http):
    """ApiHistory has no mapping component, so mapping dict should be empty."""
    response = _get_api_history(client, user_authentication, api_via_http)
    assert response.status_code == HTTPStatus.OK
    data = response.get_json()
    assert data[0]["mapping"] == {}


# -- Tests: multiple history versions ----------------------------------------

def test_api_history_two_versions(client, user_authentication, api_with_two_versions):
    """After one update, history returns two entries (newest first)."""
    response = _get_api_history(client, user_authentication, api_with_two_versions)
    assert response.status_code == HTTPStatus.OK
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) == 2
    for entry in data:
        _assert_history_entry_shape(entry)


def test_api_history_two_versions_ordering(client, user_authentication, api_with_two_versions):
    """History entries are returned newest first (version '2' before '1')."""
    response = _get_api_history(client, user_authentication, api_with_two_versions)
    data = response.get_json()
    assert data[0]["version"] == "2"
    assert data[1]["version"] == "1"


def test_api_history_two_versions_diff_fields(client, user_authentication, api_with_two_versions):
    """The second (newest) history entry only contains changed fields in its object."""
    response = _get_api_history(client, user_authentication, api_with_two_versions)
    data = response.get_json()
    newest = data[0]
    assert "edited_by" in newest["object"]
    assert "api" in newest["object"] or "category" in newest["object"] or "tags" in newest["object"]


# -- Tests: permission enforcement ------------------------------------------

def test_api_history_unauthorized_read_denied(
    client, client_db, user_authentication, reader_authentication, utilities
):
    """A user listed in read_denials cannot access the history."""
    response, api_name = _create_api_via_http(client, user_authentication, utilities)
    assert response.status_code == HTTPStatus.CREATED

    listed = client.get(_APIS_URL)
    api = next(a for a in listed.get_json()["apis"] if a["api"] == api_name)
    api_id = api["id"]

    api_row = client_db.session.query(ApiModel).filter(ApiModel.id == api_id).one()
    reader_id = reader_authentication.json["id"]
    api_row.read_denials = f"[{reader_id}]"
    client_db.session.commit()

    qs = {
        "user-id": reader_id,
        "token": reader_authentication.json["token"],
        "api-id": api_id,
    }
    blocked = client.get(_API_HISTORY_URL, query_string=qs)
    assert blocked.status_code == HTTPStatus.UNAUTHORIZED


# -- Tests: permission fields are resolved to usernames ----------------------

def test_api_history_permission_fields_resolved_to_usernames(
    client, user_authentication, api_via_http
):
    """Permission fields in history entries are resolved from user IDs to usernames."""
    response = _get_api_history(client, user_authentication, api_via_http)
    assert response.status_code == HTTPStatus.OK
    data = response.get_json()
    entry = data[0]
    obj = entry["object"]

    permission_fields = [
        "delete_permissions", "edit_permissions", "manage_permissions",
        "read_denials", "write_permissions",
    ]
    for field in permission_fields:
        if field in obj:
            assert not obj[field].startswith("[") or obj[field] == "", (
                f"Permission field '{field}' should contain usernames, not raw IDs"
            )
