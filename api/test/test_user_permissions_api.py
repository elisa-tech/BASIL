"""HTTP tests for UserPermissionsApi (GET/PUT /user/permissions/api)."""
import os
import tempfile
from http import HTTPStatus

import pytest

from db.models.api import ApiModel
from db.models.user import UserModel
from conftest import UT_USER_EMAIL

_USER_PERMISSIONS_API_URL = "/user/permissions/api"

_UT_API_NAME = "ut_user_permissions_api"
_UT_API_LIBRARY = "ut_user_permissions_library"
_UT_API_LIBRARY_VERSION = "v1.0.0"
_UT_API_CATEGORY = "ut_user_permissions_category"
_UT_API_IMPLEMENTATION_FILE_FROM_ROW = 0
_UT_API_IMPLEMENTATION_FILE_TO_ROW = 42
_UT_API_TAGS = "ut_user_permissions_tags"
_UT_API_RAW_SPEC = "BASIL UT: user permissions API."


def _get_user_by_email(client_db, email):
    return client_db.session.query(UserModel).filter(UserModel.email == email).one()


def _create_api(client_db, utilities, owner_email=UT_USER_EMAIL):
    user = _get_user_by_email(client_db, owner_email)
    raw_spec = tempfile.NamedTemporaryFile(mode="w", delete=False)
    raw_spec.write(_UT_API_RAW_SPEC)
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
    return ut_api.id, raw_spec.name


@pytest.fixture()
def owner_api_id(client_db, ut_user_db, utilities):
    """ApiModel owned by the default UT user (has manage permissions)."""
    api_id, raw_path = _create_api(client_db, utilities, UT_USER_EMAIL)
    yield api_id
    if os.path.isfile(raw_path):
        os.remove(raw_path)


def _get_user_permissions(client, api_id, user_id, token, search=None):
    qs = {
        "api-id": api_id,
        "user-id": user_id,
        "token": token,
    }
    if search is not None:
        qs["search"] = search
    return client.get(_USER_PERMISSIONS_API_URL, query_string=qs)


def _put_user_permissions(client, api_id, user_id, token, permissions):
    return client.put(
        _USER_PERMISSIONS_API_URL,
        json={
            "api-id": api_id,
            "user-id": user_id,
            "token": token,
            "permissions": permissions,
        },
    )


def test_user_permissions_get_ok(client, user_authentication, owner_api_id, ut_reader_user_db):
    """Owner with manage permission receives other enabled non-guest users with permission strings."""
    auth = user_authentication.json
    api_id = owner_api_id
    response = _get_user_permissions(client, api_id, auth["id"], auth["token"])
    assert response.status_code == HTTPStatus.OK
    data = response.get_json()
    assert isinstance(data, list)
    reader_rows = [u for u in data if u["id"] == ut_reader_user_db.id]
    assert len(reader_rows) == 1
    reader = reader_rows[0]
    assert reader["username"] == ut_reader_user_db.username
    assert "permissions" in reader
    assert "r" in reader["permissions"]
    assert reader["write_permission_request"] in (0, 1)


def test_user_permissions_get_search(client, user_authentication, owner_api_id, ut_reader_user_db):
    """Optional search narrows users by username or email substring."""
    auth = user_authentication.json
    api_id = owner_api_id
    hit = _get_user_permissions(
        client, api_id, auth["id"], auth["token"], search=ut_reader_user_db.username[:6]
    )
    assert hit.status_code == HTTPStatus.OK
    assert any(u["id"] == ut_reader_user_db.id for u in hit.get_json())

    miss = _get_user_permissions(
        client, api_id, auth["id"], auth["token"], search="___no_such_user___"
    )
    assert miss.status_code == HTTPStatus.OK
    assert miss.get_json() == []


@pytest.mark.parametrize("mandatory_field", ["api-id", "token", "user-id"])
def test_user_permissions_get_missing_mandatory_fields(
    client, user_authentication, owner_api_id, mandatory_field
):
    auth = user_authentication.json
    qs = {
        "api-id": owner_api_id,
        "user-id": auth["id"],
        "token": auth["token"],
    }
    del qs[mandatory_field]
    response = client.get(_USER_PERMISSIONS_API_URL, query_string=qs)
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_user_permissions_get_unauthorized_invalid_token(client, user_authentication, owner_api_id):
    auth = user_authentication.json
    response = _get_user_permissions(
        client, owner_api_id, auth["id"], "not-a-valid-token-for-this-user"
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED


def test_user_permissions_get_not_found_api(client, user_authentication):
    auth = user_authentication.json
    response = _get_user_permissions(client, 999_999, auth["id"], auth["token"])
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_user_permissions_get_forbidden_without_manage(client, reader_authentication, owner_api_id):
    """Reader has read but not manage on another user's API."""
    auth = reader_authentication.json
    response = _get_user_permissions(client, owner_api_id, auth["id"], auth["token"])
    assert response.status_code == HTTPStatus.FORBIDDEN


def test_user_permissions_get_write_permission_request_flag(
    client, client_db, user_authentication, owner_api_id, ut_reader_user_db
):
    """write_permission_request is 1 when the API lists a pending request for a USER-role account."""
    auth = user_authentication.json
    api = client_db.session.query(ApiModel).filter(ApiModel.id == owner_api_id).one()
    api.write_permission_requests = f"[{ut_reader_user_db.id}]"
    client_db.session.add(api)
    client_db.session.commit()

    response = _get_user_permissions(client, owner_api_id, auth["id"], auth["token"])
    assert response.status_code == HTTPStatus.OK
    reader_rows = [u for u in response.get_json() if u["id"] == ut_reader_user_db.id]
    assert len(reader_rows) == 1
    assert reader_rows[0]["write_permission_request"] == 1


@pytest.mark.parametrize("mandatory_field", ["api-id", "token", "user-id", "permissions"])
def test_user_permissions_put_missing_mandatory_fields(
    client, user_authentication, owner_api_id, mandatory_field
):
    auth = user_authentication.json
    body = {
        "api-id": owner_api_id,
        "user-id": auth["id"],
        "token": auth["token"],
        "permissions": [],
    }
    del body[mandatory_field]
    response = client.put(_USER_PERMISSIONS_API_URL, json=body)
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_user_permissions_put_unauthorized(client, user_authentication, owner_api_id):
    auth = user_authentication.json
    response = client.put(
        _USER_PERMISSIONS_API_URL,
        json={
            "api-id": owner_api_id,
            "user-id": auth["id"],
            "token": "invalid-token",
            "permissions": [],
        },
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED


def test_user_permissions_put_not_found_api(client, user_authentication):
    auth = user_authentication.json
    response = _put_user_permissions(client, 999_999, auth["id"], auth["token"], [])
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_user_permissions_put_forbidden_without_manage(client, reader_authentication, owner_api_id):
    auth = reader_authentication.json
    response = _put_user_permissions(
        client, owner_api_id, auth["id"], auth["token"], []
    )
    assert response.status_code == HTTPStatus.FORBIDDEN


def test_user_permissions_put_not_found_target_user(client, user_authentication, owner_api_id):
    auth = user_authentication.json
    response = _put_user_permissions(
        client,
        owner_api_id,
        auth["id"],
        auth["token"],
        [{"id": 999_999, "permissions": "r"}],
    )
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_user_permissions_put_ok_empty_permissions(client, user_authentication, owner_api_id):
    auth = user_authentication.json
    response = _put_user_permissions(
        client, owner_api_id, auth["id"], auth["token"], []
    )
    assert response.status_code == HTTPStatus.OK
    assert response.get_json() is True


def test_user_permissions_put_grants_write_and_reflected_in_get(
    client, user_authentication, owner_api_id, ut_reader_user_db
):
    """PUT updates write_permissions; GET reports combined permissions for the target user."""
    auth = user_authentication.json
    put = _put_user_permissions(
        client,
        owner_api_id,
        auth["id"],
        auth["token"],
        [{"id": ut_reader_user_db.id, "permissions": "rw"}],
    )
    assert put.status_code == HTTPStatus.OK

    get_resp = _get_user_permissions(client, owner_api_id, auth["id"], auth["token"])
    assert get_resp.status_code == HTTPStatus.OK
    reader_rows = [u for u in get_resp.get_json() if u["id"] == ut_reader_user_db.id]
    assert len(reader_rows) == 1
    perms = reader_rows[0]["permissions"]
    assert "r" in perms
    assert "w" in perms
