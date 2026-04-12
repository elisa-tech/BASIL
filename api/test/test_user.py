"""HTTP tests for User (GET/PUT /user) and UserEnable (PUT /user/enable)."""
import base64
from http import HTTPStatus

import pytest

from conftest import (
    UT_USER_EMAIL,
    UT_USER_PASSWORD,
)
from db.models.user import UserModel

_USER_URL = "/user"
_USER_ENABLE_URL = "/user/enable"

_UT_ADMIN_USER_NAME = "ut_user_admin_name"
_UT_ADMIN_USER_EMAIL = "ut_user_admin_email"
_UT_ADMIN_USER_PASSWORD = "ut_user_admin_password"
_UT_ADMIN_USER_ROLE = "ADMIN"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _auth_fields(auth_response):
    data = auth_response.json
    return data["id"], data["token"]


def _get_users(client, user_id, token):
    return client.get(
        _USER_URL,
        query_string={"user-id": user_id, "token": token},
    )


def _put_user(client, user_id, token, **extra):
    body = {"user-id": user_id, "token": token, **extra}
    return client.put(_USER_URL, json=body)


def _put_user_enable(client, user_id, token, target_user_id, enabled):
    return client.put(
        _USER_ENABLE_URL,
        json={
            "user-id": user_id,
            "token": token,
            "target-user": {"id": target_user_id, "enabled": enabled},
        },
    )


def _get_user_by_id(client_db, user_id):
    client_db.session.expire_all()
    return client_db.session.query(UserModel).filter(UserModel.id == user_id).one()


def _cleanup_user(client_db, username):
    user = (
        client_db.session.query(UserModel)
        .filter(UserModel.username == username)
        .one_or_none()
    )
    if user is not None:
        client_db.session.delete(user)
        client_db.session.commit()


def _fresh_login(client, email, password):
    """Perform a fresh login and return (user_id, token)."""
    resp = client.post("/user/login", json={"email": email, "password": password})
    assert resp.status_code == HTTPStatus.OK
    data = resp.get_json()
    return data["id"], data["token"]


# ---------------------------------------------------------------------------
# Module-scoped fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def ut_admin_user_db(client_db):
    ut_admin = UserModel(
        _UT_ADMIN_USER_NAME,
        _UT_ADMIN_USER_EMAIL,
        _UT_ADMIN_USER_PASSWORD,
        _UT_ADMIN_USER_ROLE,
    )
    client_db.session.add(ut_admin)
    client_db.session.commit()
    yield ut_admin


@pytest.fixture(scope="module")
def admin_authentication(client, ut_admin_user_db):
    return client.post(
        "/user/login",
        json={"email": _UT_ADMIN_USER_EMAIL, "password": _UT_ADMIN_USER_PASSWORD},
    )


# ===================================================================
# GET /user  (admin: list users)
# ===================================================================

# -- Missing fields --

@pytest.mark.parametrize("missing_field", ["user-id", "token"])
def test_get_users_bad_request_missing_field(
    client, admin_authentication, missing_field
):
    uid, token = _auth_fields(admin_authentication)
    qs = {"user-id": uid, "token": token}
    del qs[missing_field]
    response = client.get(_USER_URL, query_string=qs)
    assert response.status_code == HTTPStatus.BAD_REQUEST


# -- Unauthorized --

def test_get_users_unauthorized_invalid_token(client, admin_authentication):
    uid, _ = _auth_fields(admin_authentication)
    response = _get_users(client, uid, "not-a-valid-token")
    assert response.status_code == HTTPStatus.UNAUTHORIZED


def test_get_users_unauthorized_non_admin(client, user_authentication):
    """Only ADMIN users can list all users."""
    uid, token = _auth_fields(user_authentication)
    response = _get_users(client, uid, token)
    assert response.status_code == HTTPStatus.UNAUTHORIZED


def test_get_users_unauthorized_reader(client, reader_authentication):
    uid, token = _auth_fields(reader_authentication)
    response = _get_users(client, uid, token)
    assert response.status_code == HTTPStatus.UNAUTHORIZED


# -- Successful GET --

def test_get_users_ok_returns_list(client, admin_authentication):
    uid, token = _auth_fields(admin_authentication)
    response = _get_users(client, uid, token)
    assert response.status_code == HTTPStatus.OK
    data = response.get_json()
    assert isinstance(data, list)


def test_get_users_ok_excludes_requesting_admin(client, admin_authentication):
    """The requesting admin should not appear in the returned list."""
    uid, token = _auth_fields(admin_authentication)
    response = _get_users(client, uid, token)
    assert response.status_code == HTTPStatus.OK
    returned_ids = [u["id"] for u in response.get_json()]
    assert uid not in returned_ids


def test_get_users_ok_includes_other_users(
    client, admin_authentication, ut_user_db, ut_reader_user_db
):
    uid, token = _auth_fields(admin_authentication)
    response = _get_users(client, uid, token)
    assert response.status_code == HTTPStatus.OK
    returned_ids = [u["id"] for u in response.get_json()]
    assert ut_user_db.id in returned_ids
    assert ut_reader_user_db.id in returned_ids


def test_get_users_ok_response_has_full_data_fields(client, admin_authentication, ut_user_db):
    """Each user dict should contain full_data fields (email, created_at, updated_at)."""
    uid, token = _auth_fields(admin_authentication)
    response = _get_users(client, uid, token)
    assert response.status_code == HTTPStatus.OK
    data = response.get_json()
    assert len(data) > 0
    for user_dict in data:
        assert "id" in user_dict
        assert "username" in user_dict
        assert "email" in user_dict
        assert "role" in user_dict
        assert "enabled" in user_dict
        assert "created_at" in user_dict
        assert "updated_at" in user_dict


def test_get_users_ok_sorted_by_role_and_username(client, admin_authentication, ut_user_db):
    uid, token = _auth_fields(admin_authentication)
    response = _get_users(client, uid, token)
    assert response.status_code == HTTPStatus.OK
    data = response.get_json()
    pairs = [(u["role"], u["username"]) for u in data]
    assert pairs == sorted(pairs)


# ===================================================================
# PUT /user  (edit own username or password)
# ===================================================================

# -- Missing fields --

@pytest.mark.parametrize("missing_field", ["user-id", "token"])
def test_put_user_bad_request_missing_field(client, user_authentication, missing_field):
    uid, token = _auth_fields(user_authentication)
    body = {"user-id": uid, "token": token, "username": "newname1"}
    del body[missing_field]
    response = client.put(_USER_URL, json=body)
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_put_user_bad_request_no_changes(client, user_authentication):
    """PUT without username or password returns 400."""
    uid, token = _auth_fields(user_authentication)
    response = _put_user(client, uid, token)
    assert response.status_code == HTTPStatus.BAD_REQUEST


# -- Unauthorized --

def test_put_user_unauthorized_invalid_token(client, user_authentication):
    uid, _ = _auth_fields(user_authentication)
    response = _put_user(client, uid, "not-a-valid-token", username="anything")
    assert response.status_code == HTTPStatus.UNAUTHORIZED


# -- Edit username: validation --

@pytest.mark.parametrize("bad_username", ["ab", "x", ""])
def test_put_user_bad_request_username_too_short(client, user_authentication, bad_username):
    uid, token = _auth_fields(user_authentication)
    response = _put_user(client, uid, token, username=bad_username)
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_put_user_bad_request_username_with_space(client, user_authentication):
    uid, token = _auth_fields(user_authentication)
    response = _put_user(client, uid, token, username="user name")
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_put_user_bad_request_username_duplicate(
    client, user_authentication, ut_reader_user_db
):
    """Cannot change to a username already in use."""
    uid, token = _auth_fields(user_authentication)
    response = _put_user(client, uid, token, username=ut_reader_user_db.username)
    assert response.status_code == HTTPStatus.BAD_REQUEST


# -- Edit password: validation --

@pytest.mark.parametrize("bad_password", ["ab", "x", ""])
def test_put_user_bad_request_password_too_short(client, user_authentication, bad_password):
    uid, token = _auth_fields(user_authentication)
    response = _put_user(client, uid, token, password=bad_password)
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_put_user_bad_request_password_with_space(client, user_authentication):
    uid, token = _auth_fields(user_authentication)
    response = _put_user(client, uid, token, password="pass word")
    assert response.status_code == HTTPStatus.BAD_REQUEST


# -- Edit username: success (uses fresh login to avoid stale token) --

def test_put_user_ok_change_username(client, client_db, ut_user_db, utilities):
    uid, token = _fresh_login(client, UT_USER_EMAIL, UT_USER_PASSWORD)
    suffix = utilities.generate_random_hex_string8()
    new_username = f"renamed_{suffix}"
    response = _put_user(client, uid, token, username=new_username)
    assert response.status_code == HTTPStatus.OK
    data = response.get_json()
    assert data["result"] == "success"
    assert "username" in data["message"].lower() or "login" in data["message"].lower()

    updated = _get_user_by_id(client_db, uid)
    assert updated.username == new_username

    uid2, token2 = _fresh_login(client, UT_USER_EMAIL, UT_USER_PASSWORD)
    restore = _put_user(client, uid2, token2, username="ut_user_name")
    assert restore.status_code == HTTPStatus.OK
    restored = _get_user_by_id(client_db, uid2)
    assert restored.username == "ut_user_name"


# -- Edit password: success (uses fresh login to avoid stale token) --

def test_put_user_ok_change_password(client, client_db, ut_user_db):
    uid, token = _fresh_login(client, UT_USER_EMAIL, UT_USER_PASSWORD)
    new_password = "new_password_1234"
    response = _put_user(client, uid, token, password=new_password)
    assert response.status_code == HTTPStatus.OK
    data = response.get_json()
    assert data["result"] == "success"
    assert "password" in data["message"].lower() or "login" in data["message"].lower()

    updated = _get_user_by_id(client_db, uid)
    expected_encoded = base64.b64encode(new_password.encode("utf-8")).decode("utf-8")
    assert updated.pwd == expected_encoded

    uid2, token2 = _fresh_login(client, UT_USER_EMAIL, new_password)
    restore = _put_user(client, uid2, token2, password=UT_USER_PASSWORD)
    assert restore.status_code == HTTPStatus.OK
    restored = _get_user_by_id(client_db, uid2)
    original_encoded = base64.b64encode(UT_USER_PASSWORD.encode("utf-8")).decode("utf-8")
    assert restored.pwd == original_encoded


# ===================================================================
# PUT /user/enable  (admin: enable/disable user)
# ===================================================================

# -- Missing fields --

@pytest.mark.parametrize("missing_field", ["token", "user-id", "target-user"])
def test_enable_bad_request_missing_top_level_field(
    client, admin_authentication, ut_reader_user_db, missing_field
):
    uid, token = _auth_fields(admin_authentication)
    body = {
        "user-id": uid,
        "token": token,
        "target-user": {"id": ut_reader_user_db.id, "enabled": 1},
    }
    del body[missing_field]
    response = client.put(_USER_ENABLE_URL, json=body)
    assert response.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.parametrize("missing_field", ["id", "enabled"])
def test_enable_bad_request_missing_target_user_field(
    client, admin_authentication, ut_reader_user_db, missing_field
):
    uid, token = _auth_fields(admin_authentication)
    target = {"id": ut_reader_user_db.id, "enabled": 1}
    del target[missing_field]
    response = client.put(
        _USER_ENABLE_URL,
        json={"user-id": uid, "token": token, "target-user": target},
    )
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_enable_bad_request_non_numeric_enabled(
    client, admin_authentication, ut_reader_user_db
):
    uid, token = _auth_fields(admin_authentication)
    response = _put_user_enable(client, uid, token, ut_reader_user_db.id, "abc")
    assert response.status_code == HTTPStatus.BAD_REQUEST


# -- Unauthorized --

def test_enable_unauthorized_invalid_token(
    client, admin_authentication, ut_reader_user_db
):
    uid, _ = _auth_fields(admin_authentication)
    response = _put_user_enable(
        client, uid, "not-a-valid-token", ut_reader_user_db.id, 1
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED


def test_enable_unauthorized_non_admin(client, user_authentication, ut_reader_user_db):
    uid, token = _auth_fields(user_authentication)
    response = _put_user_enable(client, uid, token, ut_reader_user_db.id, 0)
    assert response.status_code == HTTPStatus.UNAUTHORIZED


def test_enable_unauthorized_reader(client, reader_authentication, ut_user_db):
    uid, token = _auth_fields(reader_authentication)
    response = _put_user_enable(client, uid, token, ut_user_db.id, 0)
    assert response.status_code == HTTPStatus.UNAUTHORIZED


# -- Not Found --

def test_enable_not_found_target_user(client, admin_authentication):
    uid, token = _auth_fields(admin_authentication)
    response = _put_user_enable(client, uid, token, 999_999, 0)
    assert response.status_code == HTTPStatus.NOT_FOUND


# -- Successful enable/disable --

def test_enable_ok_disable_user(
    client, admin_authentication, ut_reader_user_db, client_db
):
    uid, token = _auth_fields(admin_authentication)
    response = _put_user_enable(client, uid, token, ut_reader_user_db.id, 0)
    assert response.status_code == HTTPStatus.OK
    assert response.get_json() is True

    updated = _get_user_by_id(client_db, ut_reader_user_db.id)
    assert updated.enabled == 0

    _put_user_enable(client, uid, token, ut_reader_user_db.id, 1)


def test_enable_ok_enable_user(
    client, admin_authentication, ut_reader_user_db, client_db
):
    uid, token = _auth_fields(admin_authentication)
    _put_user_enable(client, uid, token, ut_reader_user_db.id, 0)

    response = _put_user_enable(client, uid, token, ut_reader_user_db.id, 1)
    assert response.status_code == HTTPStatus.OK
    assert response.get_json() is True

    updated = _get_user_by_id(client_db, ut_reader_user_db.id)
    assert updated.enabled == 1


def test_enable_ok_disabled_user_cannot_authenticate(
    client, client_db, admin_authentication, utilities
):
    """A disabled user should not be able to perform authenticated actions."""
    suffix = utilities.generate_random_hex_string8()
    username = f"disable_test_{suffix}"
    email = f"disable_test_{suffix}@example.com"
    password = "testpass1234"

    signin_resp = client.post(
        "/user/signin",
        json={"username": username, "email": email, "password": password},
    )
    assert signin_resp.status_code == HTTPStatus.CREATED
    try:
        target_id = signin_resp.get_json()["id"]

        admin_uid, admin_token = _auth_fields(admin_authentication)
        _put_user_enable(client, admin_uid, admin_token, target_id, 0)

        login_resp = client.post(
            "/user/login",
            json={"email": email, "password": password},
        )
        assert login_resp.status_code == HTTPStatus.UNAUTHORIZED

        _put_user_enable(client, admin_uid, admin_token, target_id, 1)
    finally:
        _cleanup_user(client_db, username)
