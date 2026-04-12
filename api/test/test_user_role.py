"""HTTP tests for UserRole (PUT /user/role)."""
from http import HTTPStatus

import pytest

from db.models.user import UserModel

_USER_ROLE_URL = "/user/role"

_UT_ADMIN_USER_NAME = "ut_role_admin_name"
_UT_ADMIN_USER_EMAIL = "ut_role_admin_email"
_UT_ADMIN_USER_PASSWORD = "ut_role_admin_password"
_UT_ADMIN_USER_ROLE = "ADMIN"


@pytest.fixture(scope="module")
def ut_admin_user_db(client_db):
    dbi = client_db
    ut_admin = UserModel(
        _UT_ADMIN_USER_NAME,
        _UT_ADMIN_USER_EMAIL,
        _UT_ADMIN_USER_PASSWORD,
        _UT_ADMIN_USER_ROLE,
    )
    dbi.session.add(ut_admin)
    dbi.session.commit()
    yield ut_admin


@pytest.fixture(scope="module")
def admin_authentication(client, ut_admin_user_db):
    return client.post(
        "/user/login",
        json={"email": _UT_ADMIN_USER_EMAIL, "password": _UT_ADMIN_USER_PASSWORD},
    )


def _put_user_role(client, user_id, token, target_user_id, target_role):
    return client.put(
        _USER_ROLE_URL,
        json={
            "user-id": user_id,
            "token": token,
            "target-user": {"id": target_user_id, "role": target_role},
        },
    )


def _auth_fields(auth_response):
    data = auth_response.json
    return data["id"], data["token"]


def _get_user_role(client_db, user_id):
    user = client_db.session.query(UserModel).filter(UserModel.id == user_id).one()
    return user.role


def test_put_ok_change_role_to_admin(
    client, admin_authentication, ut_reader_user_db, client_db
):
    """Admin can change another user's role to ADMIN."""
    uid, token = _auth_fields(admin_authentication)
    response = _put_user_role(client, uid, token, ut_reader_user_db.id, "ADMIN")
    assert response.status_code == HTTPStatus.OK
    assert response.get_json() is True
    assert _get_user_role(client_db, ut_reader_user_db.id) == "ADMIN"

    _put_user_role(client, uid, token, ut_reader_user_db.id, "USER")


def test_put_ok_change_role_to_guest(
    client, admin_authentication, ut_reader_user_db, client_db
):
    """Admin can change another user's role to GUEST."""
    uid, token = _auth_fields(admin_authentication)
    response = _put_user_role(client, uid, token, ut_reader_user_db.id, "GUEST")
    assert response.status_code == HTTPStatus.OK
    assert response.get_json() is True
    assert _get_user_role(client_db, ut_reader_user_db.id) == "GUEST"

    _put_user_role(client, uid, token, ut_reader_user_db.id, "USER")


def test_put_ok_change_role_to_user(
    client, admin_authentication, ut_reader_user_db, client_db
):
    """Admin can change another user's role to USER."""
    uid, token = _auth_fields(admin_authentication)
    _put_user_role(client, uid, token, ut_reader_user_db.id, "GUEST")

    response = _put_user_role(client, uid, token, ut_reader_user_db.id, "USER")
    assert response.status_code == HTTPStatus.OK
    assert response.get_json() is True
    assert _get_user_role(client_db, ut_reader_user_db.id) == "USER"


def test_put_bad_request_invalid_role(client, admin_authentication, ut_reader_user_db):
    """Reject roles not in [ADMIN, GUEST, USER]."""
    uid, token = _auth_fields(admin_authentication)
    response = _put_user_role(client, uid, token, ut_reader_user_db.id, "SUPERADMIN")
    assert response.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.parametrize("missing_field", ["token", "user-id", "target-user"])
def test_put_bad_request_missing_top_level_fields(
    client, admin_authentication, ut_reader_user_db, missing_field
):
    """Omitting any top-level mandatory field returns 400."""
    uid, token = _auth_fields(admin_authentication)
    body = {
        "user-id": uid,
        "token": token,
        "target-user": {"id": ut_reader_user_db.id, "role": "USER"},
    }
    del body[missing_field]
    response = client.put(_USER_ROLE_URL, json=body)
    assert response.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.parametrize("missing_field", ["id", "role"])
def test_put_bad_request_missing_target_user_fields(
    client, admin_authentication, ut_reader_user_db, missing_field
):
    """Omitting a mandatory target-user sub-field returns 400."""
    uid, token = _auth_fields(admin_authentication)
    target = {"id": ut_reader_user_db.id, "role": "USER"}
    del target[missing_field]
    response = client.put(
        _USER_ROLE_URL,
        json={"user-id": uid, "token": token, "target-user": target},
    )
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_put_unauthorized_invalid_token(
    client, admin_authentication, ut_reader_user_db
):
    """Invalid token returns 401."""
    uid, _ = _auth_fields(admin_authentication)
    response = _put_user_role(
        client, uid, "not-a-valid-token", ut_reader_user_db.id, "ADMIN"
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED


def test_put_unauthorized_non_admin_user(
    client, user_authentication, ut_reader_user_db
):
    """A USER-role account cannot change roles (only ADMIN can)."""
    uid, token = _auth_fields(user_authentication)
    response = _put_user_role(client, uid, token, ut_reader_user_db.id, "ADMIN")
    assert response.status_code == HTTPStatus.UNAUTHORIZED


def test_put_unauthorized_reader_user(
    client, reader_authentication, ut_user_db
):
    """Another USER-role account also cannot change roles."""
    uid, token = _auth_fields(reader_authentication)
    response = _put_user_role(client, uid, token, ut_user_db.id, "GUEST")
    assert response.status_code == HTTPStatus.UNAUTHORIZED


def test_put_not_found_target_user(client, admin_authentication):
    """Changing role of a non-existent user returns 404."""
    uid, token = _auth_fields(admin_authentication)
    response = _put_user_role(client, uid, token, 999_999, "USER")
    assert response.status_code == HTTPStatus.NOT_FOUND
