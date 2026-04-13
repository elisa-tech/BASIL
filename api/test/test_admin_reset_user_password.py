"""HTTP tests for AdminResetUserPassword (PUT /admin/reset-user-password)."""
from http import HTTPStatus

import pytest

from db.models.user import UserModel

_ADMIN_RESET_URL = "/admin/reset-user-password"

_UT_ADMIN_USER_NAME = "ut_admin_reset_pw_name"
_UT_ADMIN_USER_EMAIL = "ut_admin_reset_pw_email"
_UT_ADMIN_USER_PASSWORD = "ut_admin_reset_pw_password"
_UT_ADMIN_USER_ROLE = "ADMIN"

_UT_TARGET_USER_NAME = "ut_reset_target_name"
_UT_TARGET_USER_EMAIL = "ut_reset_target_email"
_UT_TARGET_USER_PASSWORD = "ut_reset_target_password"


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
def ut_target_user_db(client_db):
    """A dedicated user whose password will be reset during tests."""
    target = UserModel(
        _UT_TARGET_USER_NAME,
        _UT_TARGET_USER_EMAIL,
        _UT_TARGET_USER_PASSWORD,
        "USER",
    )
    client_db.session.add(target)
    client_db.session.commit()
    yield target


@pytest.fixture(scope="module")
def admin_authentication(client, ut_admin_user_db):
    return client.post(
        "/user/login",
        json={"email": _UT_ADMIN_USER_EMAIL, "password": _UT_ADMIN_USER_PASSWORD},
    )


def _auth_fields(auth_response):
    data = auth_response.json
    return data["id"], data["token"]


def _put_admin_reset_password(client, user_id, token, target_user_id, new_password):
    return client.put(
        _ADMIN_RESET_URL,
        json={
            "user-id": user_id,
            "token": token,
            "target-user": {"id": target_user_id, "password": new_password},
        },
    )


def _get_user_by_id(client_db, user_id):
    client_db.session.expire_all()
    return client_db.session.query(UserModel).filter(UserModel.id == user_id).one()


# -- Success -------------------------------------------------------------------


def test_put_ok_resets_password(
    client, admin_authentication, ut_target_user_db, client_db
):
    """Admin can reset another user's password."""
    uid, token = _auth_fields(admin_authentication)
    target_id = ut_target_user_db.id

    response = _put_admin_reset_password(
        client, uid, token, target_id, "brand_new_password"
    )
    assert response.status_code == HTTPStatus.OK
    assert response.get_json() is True

    updated = _get_user_by_id(client_db, target_id)
    assert updated.pwd == "brand_new_password"

    _put_admin_reset_password(
        client, uid, token, target_id, _UT_TARGET_USER_PASSWORD
    )


# -- Bad Request (missing fields) ---------------------------------------------


@pytest.mark.parametrize("missing_field", ["token", "user-id", "target-user"])
def test_put_bad_request_missing_top_level_fields(
    client, admin_authentication, ut_reader_user_db, missing_field
):
    """Omitting any top-level mandatory field returns 400."""
    uid, token = _auth_fields(admin_authentication)
    body = {
        "user-id": uid,
        "token": token,
        "target-user": {"id": ut_reader_user_db.id, "password": "x"},
    }
    del body[missing_field]
    response = client.put(_ADMIN_RESET_URL, json=body)
    assert response.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.parametrize("missing_field", ["id", "password"])
def test_put_bad_request_missing_target_user_fields(
    client, admin_authentication, ut_reader_user_db, missing_field
):
    """Omitting a mandatory target-user sub-field returns 400."""
    uid, token = _auth_fields(admin_authentication)
    target = {"id": ut_reader_user_db.id, "password": "x"}
    del target[missing_field]
    response = client.put(
        _ADMIN_RESET_URL,
        json={"user-id": uid, "token": token, "target-user": target},
    )
    assert response.status_code == HTTPStatus.BAD_REQUEST


# -- Unauthorized --------------------------------------------------------------


def test_put_unauthorized_invalid_token(
    client, admin_authentication, ut_reader_user_db
):
    """Invalid token returns 401."""
    uid, _ = _auth_fields(admin_authentication)
    response = _put_admin_reset_password(
        client, uid, "not-a-valid-token", ut_reader_user_db.id, "x"
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED


def test_put_unauthorized_non_admin_user(
    client, user_authentication, ut_reader_user_db
):
    """A USER-role account cannot reset passwords (only ADMIN can)."""
    uid, token = _auth_fields(user_authentication)
    response = _put_admin_reset_password(
        client, uid, token, ut_reader_user_db.id, "x"
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED


def test_put_unauthorized_reader_user(
    client, reader_authentication, ut_user_db
):
    """Another USER-role account also cannot reset passwords."""
    uid, token = _auth_fields(reader_authentication)
    response = _put_admin_reset_password(
        client, uid, token, ut_user_db.id, "x"
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED


# -- Not Found -----------------------------------------------------------------


def test_put_not_found_target_user(client, admin_authentication):
    """Resetting password of a non-existent user returns 404."""
    uid, token = _auth_fields(admin_authentication)
    response = _put_admin_reset_password(
        client, uid, token, 999_999, "x"
    )
    assert response.status_code == HTTPStatus.NOT_FOUND
