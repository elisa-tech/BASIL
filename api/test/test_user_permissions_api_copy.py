"""HTTP tests for UserPermissionsApiCopy (PUT /user/permissions/copy)."""
import os
import tempfile
from http import HTTPStatus

import pytest

from db.models.api import ApiModel
from db.models.user import UserModel
from conftest import UT_USER_EMAIL, UT_READER_USER_EMAIL

_COPY_URL = "/user/permissions/copy"

_UT_API_NAME = "ut_copy_perms_api"
_UT_API_LIBRARY = "ut_copy_perms_library"
_UT_API_LIBRARY_VERSION = "v1.0.0"
_UT_API_CATEGORY = "ut_copy_perms_category"
_UT_API_IMPLEMENTATION_FILE_FROM_ROW = 0
_UT_API_IMPLEMENTATION_FILE_TO_ROW = 42
_UT_API_TAGS = "ut_copy_perms_tags"
_UT_API_RAW_SPEC = "BASIL UT: user permissions copy."


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


def _put_copy(client, api_id, copy_to, user_id, token):
    return client.put(
        _COPY_URL,
        json={
            "api-id": api_id,
            "copy-to": copy_to,
            "user-id": user_id,
            "token": token,
        },
    )


@pytest.fixture()
def source_api(client_db, ut_user_db, utilities):
    """API owned by the default UT user (has manage permissions)."""
    api_id, raw_path = _create_api(client_db, utilities, UT_USER_EMAIL)
    yield api_id
    if os.path.isfile(raw_path):
        os.remove(raw_path)


@pytest.fixture()
def target_api(client_db, ut_user_db, utilities):
    """Another API owned by the default UT user (has manage permissions)."""
    api_id, raw_path = _create_api(client_db, utilities, UT_USER_EMAIL)
    yield api_id
    if os.path.isfile(raw_path):
        os.remove(raw_path)


@pytest.fixture()
def target_apis(client_db, ut_user_db, utilities):
    """Two additional APIs owned by the default UT user."""
    created = []
    for _ in range(2):
        api_id, raw_path = _create_api(client_db, utilities, UT_USER_EMAIL)
        created.append((api_id, raw_path))
    yield [api_id for api_id, _ in created]
    for _, raw_path in created:
        if os.path.isfile(raw_path):
            os.remove(raw_path)


@pytest.fixture()
def reader_owned_api(client_db, ut_reader_user_db, utilities):
    """API owned by the reader user (default UT user does NOT have manage)."""
    api_id, raw_path = _create_api(client_db, utilities, UT_READER_USER_EMAIL)
    yield api_id
    if os.path.isfile(raw_path):
        os.remove(raw_path)


# --- Mandatory fields ---


@pytest.mark.parametrize("mandatory_field", ["api-id", "copy-to", "token", "user-id"])
def test_copy_missing_mandatory_fields(
    client, user_authentication, source_api, mandatory_field
):
    auth = user_authentication.json
    body = {
        "api-id": source_api,
        "copy-to": [],
        "user-id": auth["id"],
        "token": auth["token"],
    }
    del body[mandatory_field]
    response = client.put(_COPY_URL, json=body)
    assert response.status_code == HTTPStatus.BAD_REQUEST


# --- Authentication / authorisation ---


def test_copy_unauthorized_invalid_token(client, user_authentication, source_api):
    auth = user_authentication.json
    response = _put_copy(client, source_api, [], auth["id"], "not-a-valid-token")
    assert response.status_code == HTTPStatus.UNAUTHORIZED


def test_copy_source_api_not_found(client, user_authentication):
    auth = user_authentication.json
    response = _put_copy(client, 999_999, [], auth["id"], auth["token"])
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_copy_forbidden_no_manage_on_source(
    client, reader_authentication, source_api
):
    """Reader has no manage permission on an API owned by another user."""
    auth = reader_authentication.json
    response = _put_copy(client, source_api, [], auth["id"], auth["token"])
    assert response.status_code == HTTPStatus.FORBIDDEN


def test_copy_target_api_not_found(client, user_authentication, source_api):
    auth = user_authentication.json
    response = _put_copy(client, source_api, [999_999], auth["id"], auth["token"])
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_copy_forbidden_no_manage_on_target(
    client, user_authentication, source_api, reader_owned_api
):
    """User has manage on source but not on the target owned by reader."""
    auth = user_authentication.json
    response = _put_copy(
        client, source_api, [reader_owned_api], auth["id"], auth["token"]
    )
    assert response.status_code == HTTPStatus.FORBIDDEN


# --- Successful operations ---


def test_copy_empty_copy_to_list(client, user_authentication, source_api):
    auth = user_authentication.json
    response = _put_copy(client, source_api, [], auth["id"], auth["token"])
    assert response.status_code == HTTPStatus.OK
    assert response.get_json() is True


def test_copy_permissions_applied_to_target(
    client, client_db, user_authentication, source_api, target_api, ut_reader_user_db
):
    """Permissions from the source API are copied onto the target API."""
    src = client_db.session.query(ApiModel).filter(ApiModel.id == source_api).one()
    src.write_permissions = f"[{ut_reader_user_db.id}]"
    src.edit_permissions = f"[{ut_reader_user_db.id}]"
    src.delete_permissions = f"[{ut_reader_user_db.id}]"
    src.read_denials = f"[{ut_reader_user_db.id}]"
    client_db.session.add(src)
    client_db.session.commit()

    auth = user_authentication.json
    response = _put_copy(
        client, source_api, [target_api], auth["id"], auth["token"]
    )
    assert response.status_code == HTTPStatus.OK
    assert response.get_json() is True

    client_db.session.expire_all()
    tgt = client_db.session.query(ApiModel).filter(ApiModel.id == target_api).one()
    assert tgt.write_permissions == src.write_permissions
    assert tgt.edit_permissions == src.edit_permissions
    assert tgt.delete_permissions == src.delete_permissions
    assert tgt.manage_permissions == src.manage_permissions
    assert tgt.read_denials == src.read_denials


def test_copy_permissions_applied_to_multiple_targets(
    client, client_db, user_authentication, source_api, target_apis, ut_reader_user_db
):
    """Permissions are copied to every API listed in copy-to."""
    src = client_db.session.query(ApiModel).filter(ApiModel.id == source_api).one()
    src.write_permissions = f"[{ut_reader_user_db.id}]"
    client_db.session.add(src)
    client_db.session.commit()

    auth = user_authentication.json
    response = _put_copy(
        client, source_api, target_apis, auth["id"], auth["token"]
    )
    assert response.status_code == HTTPStatus.OK
    assert response.get_json() is True

    client_db.session.expire_all()
    for tid in target_apis:
        tgt = client_db.session.query(ApiModel).filter(ApiModel.id == tid).one()
        assert tgt.write_permissions == src.write_permissions
        assert tgt.manage_permissions == src.manage_permissions
        assert tgt.edit_permissions == src.edit_permissions
        assert tgt.delete_permissions == src.delete_permissions
        assert tgt.read_denials == src.read_denials
