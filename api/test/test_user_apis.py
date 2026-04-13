"""HTTP tests for UserApis (GET /user/apis)."""
import os
import tempfile
from http import HTTPStatus

import pytest

from db.models.api import ApiModel
from db.models.user import UserModel
from conftest import UT_USER_EMAIL

_USER_APIS_URL = "/user/apis"

_UT_API_NAME = "ut_user_apis_api"
_UT_API_LIBRARY = "ut_user_apis_library"
_UT_API_LIBRARY_VERSION = "v1.0.0"
_UT_API_CATEGORY = "ut_user_apis_category"
_UT_API_IMPLEMENTATION_FILE_FROM_ROW = 0
_UT_API_IMPLEMENTATION_FILE_TO_ROW = 42
_UT_API_TAGS = "ut_user_apis_tags"
_UT_API_RAW_SPEC = "BASIL UT: user apis."

_FIELDS_REMOVED_FROM_RESPONSE = [
    "raw_specification_url",
    "category",
    "checksum",
    "default_view",
    "implementation_file",
    "implementation_file_from_row",
    "implementation_file_to_row",
    "edited_by",
    "last_coverage",
    "tags",
    "created_by",
]


def _get_user_by_email(client_db, email):
    return client_db.session.query(UserModel).filter(UserModel.email == email).one()


def _create_api(client_db, utilities, owner_email=UT_USER_EMAIL, suffix=None):
    user = _get_user_by_email(client_db, owner_email)
    raw_spec = tempfile.NamedTemporaryFile(mode="w", delete=False)
    raw_spec.write(_UT_API_RAW_SPEC)
    raw_spec.close()
    api_name = _UT_API_NAME + "#" + (suffix or utilities.generate_random_hex_string8())
    ut_api = ApiModel(
        api_name,
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


def _get_user_apis(client, api_id, user_id, token, search=None):
    qs = {
        "api-id": api_id,
        "user-id": user_id,
        "token": token,
    }
    if search is not None:
        qs["search"] = search
    return client.get(_USER_APIS_URL, query_string=qs)


@pytest.fixture()
def owner_api(client_db, ut_user_db, utilities):
    """Primary API owned by the default UT user (has manage permissions)."""
    ut_api, raw_path = _create_api(client_db, utilities, UT_USER_EMAIL)
    yield ut_api
    if os.path.isfile(raw_path):
        os.remove(raw_path)


@pytest.fixture()
def second_owner_api(client_db, ut_user_db, utilities):
    """Another API owned by the same UT user so it shows up in the result list."""
    ut_api, raw_path = _create_api(client_db, utilities, UT_USER_EMAIL)
    yield ut_api
    if os.path.isfile(raw_path):
        os.remove(raw_path)


# ---- Missing mandatory fields ----

@pytest.mark.parametrize("mandatory_field", ["api-id", "token", "user-id"])
def test_get_missing_mandatory_fields(
    client, user_authentication, owner_api, mandatory_field
):
    auth = user_authentication.json
    qs = {
        "api-id": owner_api.id,
        "user-id": auth["id"],
        "token": auth["token"],
    }
    del qs[mandatory_field]
    response = client.get(_USER_APIS_URL, query_string=qs)
    assert response.status_code == HTTPStatus.BAD_REQUEST


# ---- Unauthorized ----

def test_get_unauthorized_invalid_token(client, user_authentication, owner_api):
    auth = user_authentication.json
    response = _get_user_apis(
        client, owner_api.id, auth["id"], "not-a-valid-token"
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED


def test_get_unauthorized_no_manage_permission(
    client, reader_authentication, owner_api
):
    """Reader user has no manage permission on another user's API."""
    auth = reader_authentication.json
    response = _get_user_apis(client, owner_api.id, auth["id"], auth["token"])
    assert response.status_code == HTTPStatus.UNAUTHORIZED


# ---- Not found ----

def test_get_not_found_api(client, user_authentication):
    auth = user_authentication.json
    response = _get_user_apis(client, 999_999, auth["id"], auth["token"])
    assert response.status_code == HTTPStatus.NOT_FOUND


# ---- Successful GET ----

def test_get_ok_returns_other_owned_apis(
    client, user_authentication, owner_api, second_owner_api
):
    """Querying against owner_api should return second_owner_api (but not owner_api itself)."""
    auth = user_authentication.json
    response = _get_user_apis(client, owner_api.id, auth["id"], auth["token"])
    assert response.status_code == HTTPStatus.OK
    data = response.get_json()
    assert isinstance(data, list)
    returned_ids = [a["id"] for a in data]
    assert second_owner_api.id in returned_ids
    assert owner_api.id not in returned_ids


def test_get_ok_excludes_queried_api(
    client, user_authentication, owner_api
):
    """The API being queried should never appear in results."""
    auth = user_authentication.json
    response = _get_user_apis(client, owner_api.id, auth["id"], auth["token"])
    assert response.status_code == HTTPStatus.OK
    returned_ids = [a["id"] for a in response.get_json()]
    assert owner_api.id not in returned_ids


def test_get_ok_response_shape(
    client, user_authentication, owner_api, second_owner_api
):
    """Each returned API dict should have `selected` and not contain stripped fields."""
    auth = user_authentication.json
    response = _get_user_apis(client, owner_api.id, auth["id"], auth["token"])
    assert response.status_code == HTTPStatus.OK
    data = response.get_json()
    for api_dict in data:
        assert "selected" in api_dict
        assert api_dict["selected"] in (0, 1)
        for field in _FIELDS_REMOVED_FROM_RESPONSE:
            assert field not in api_dict


def test_get_ok_selected_flag_matching_permissions(
    client, client_db, user_authentication, owner_api, second_owner_api
):
    """When both APIs have identical permission strings, selected should be 1."""
    auth = user_authentication.json
    response = _get_user_apis(client, owner_api.id, auth["id"], auth["token"])
    assert response.status_code == HTTPStatus.OK
    second = [a for a in response.get_json() if a["id"] == second_owner_api.id]
    assert len(second) == 1
    assert second[0]["selected"] == 1


def test_get_ok_selected_flag_mismatched_permissions(
    client, client_db, user_authentication, owner_api, second_owner_api
):
    """When permission strings differ, selected should be 0."""
    second_api = client_db.session.query(ApiModel).filter(
        ApiModel.id == second_owner_api.id
    ).one()
    second_api.write_permissions = "[999]"
    client_db.session.add(second_api)
    client_db.session.commit()

    auth = user_authentication.json
    response = _get_user_apis(client, owner_api.id, auth["id"], auth["token"])
    assert response.status_code == HTTPStatus.OK
    second = [a for a in response.get_json() if a["id"] == second_owner_api.id]
    assert len(second) == 1
    assert second[0]["selected"] == 0


# ---- Search filtering ----

def test_get_search_by_api_name(
    client, user_authentication, owner_api, second_owner_api
):
    """Search by a substring of the API name should return matching results."""
    auth = user_authentication.json
    response = _get_user_apis(
        client, owner_api.id, auth["id"], auth["token"],
        search=second_owner_api.api[:10],
    )
    assert response.status_code == HTTPStatus.OK
    assert any(a["id"] == second_owner_api.id for a in response.get_json())


def test_get_search_by_library(
    client, user_authentication, owner_api, second_owner_api
):
    """Search by library name should return matching results."""
    auth = user_authentication.json
    response = _get_user_apis(
        client, owner_api.id, auth["id"], auth["token"],
        search=_UT_API_LIBRARY,
    )
    assert response.status_code == HTTPStatus.OK
    assert any(a["id"] == second_owner_api.id for a in response.get_json())


def test_get_search_no_match(
    client, user_authentication, owner_api, second_owner_api
):
    """A search term that matches nothing should return an empty list."""
    auth = user_authentication.json
    response = _get_user_apis(
        client, owner_api.id, auth["id"], auth["token"],
        search="___absolutely_no_match___",
    )
    assert response.status_code == HTTPStatus.OK
    assert response.get_json() == []


def test_get_ok_empty_when_no_other_apis(
    client, client_db, user_authentication, utilities
):
    """When the user owns only one API, the result list should be empty."""
    sole_api, raw_path = _create_api(client_db, utilities, UT_USER_EMAIL)
    try:
        auth = user_authentication.json
        response = _get_user_apis(client, sole_api.id, auth["id"], auth["token"])
        assert response.status_code == HTTPStatus.OK
        returned_ids = [a["id"] for a in response.get_json()]
        assert sole_api.id not in returned_ids
    finally:
        if os.path.isfile(raw_path):
            os.remove(raw_path)
