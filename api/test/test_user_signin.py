"""Tests for UserSignin (POST /user/signin)."""

from http import HTTPStatus

import pytest
from conftest import UT_USER_NAME
from db.models.user import UserModel

_USER_SIGNIN_URL = "/user/signin"


def _signin_payload(username="newuser1", email="newuser1@example.com", password="pass1234"):
    return {"username": username, "email": email, "password": password}


def _cleanup_user(client_db, username):
    user = client_db.session.query(UserModel).filter(UserModel.username == username).one_or_none()
    if user is not None:
        client_db.session.delete(user)
        client_db.session.commit()


def test_user_signin_post_created(client, client_db, utilities):
    """POST with valid data creates a new user and returns 201."""
    suffix = utilities.generate_random_hex_string8()
    username = f"user{suffix}"
    email = f"user{suffix}@example.com"
    payload = _signin_payload(username=username, email=email)
    try:
        response = client.post(_USER_SIGNIN_URL, json=payload)
        assert response.status_code == HTTPStatus.CREATED
        data = response.get_json()
        assert "id" in data
        assert "token" in data
    finally:
        _cleanup_user(client_db, username)


def test_user_signin_post_created_returns_correct_data(client, client_db, utilities):
    """Returned data contains id, email (username), and token."""
    suffix = utilities.generate_random_hex_string8()
    username = f"data{suffix}"
    email = f"data{suffix}@example.com"
    payload = _signin_payload(username=username, email=email)
    try:
        response = client.post(_USER_SIGNIN_URL, json=payload)
        assert response.status_code == HTTPStatus.CREATED
        data = response.get_json()
        assert data["email"] == username
        assert isinstance(data["id"], int)
        assert len(data["token"]) > 0
    finally:
        _cleanup_user(client_db, username)


@pytest.mark.parametrize("missing_field", ["username", "email", "password"])
def test_user_signin_post_bad_request_missing_field(client, missing_field):
    """POST without a mandatory field returns 400."""
    payload = _signin_payload()
    del payload[missing_field]
    response = client.post(_USER_SIGNIN_URL, json=payload)
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_user_signin_post_bad_request_empty_payload(client):
    """POST with empty JSON returns 400."""
    response = client.post(_USER_SIGNIN_URL, json={})
    assert response.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.parametrize(
    "username",
    (
        "ab",
        "x",
        "",
    ),
)
def test_user_signin_post_bad_request_username_too_short(client, username):
    """POST with a username shorter than 4 chars returns 400."""
    payload = _signin_payload(username=username)
    response = client.post(_USER_SIGNIN_URL, json=payload)
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_user_signin_post_bad_request_username_with_space(client):
    """POST with a username containing a space returns 400."""
    payload = _signin_payload(username="user name")
    response = client.post(_USER_SIGNIN_URL, json=payload)
    assert response.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.parametrize(
    "email",
    (
        "not-an-email",
        "missing@tld",
        "@no-local.com",
        "",
    ),
)
def test_user_signin_post_bad_request_invalid_email(client, email):
    """POST with an invalid email returns 400."""
    payload = _signin_payload(email=email)
    response = client.post(_USER_SIGNIN_URL, json=payload)
    assert response.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.parametrize(
    "password",
    (
        "ab",
        "x",
        "",
    ),
)
def test_user_signin_post_bad_request_password_too_short(client, password):
    """POST with a password shorter than 4 chars returns 400."""
    payload = _signin_payload(password=password)
    response = client.post(_USER_SIGNIN_URL, json=payload)
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_user_signin_post_bad_request_password_with_space(client):
    """POST with a password containing a space returns 400."""
    payload = _signin_payload(password="pass word")
    response = client.post(_USER_SIGNIN_URL, json=payload)
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_user_signin_post_bad_request_duplicate_username(client, ut_user_db):
    """POST with an already-used username returns 400."""
    payload = _signin_payload(username=UT_USER_NAME, email="unique@example.com")
    response = client.post(_USER_SIGNIN_URL, json=payload)
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert "username" in response.get_json().lower()


def test_user_signin_post_bad_request_duplicate_email(client, client_db, ut_user_db, utilities):
    """POST with an already-used email returns 400."""
    suffix = utilities.generate_random_hex_string8()
    username = f"dupemail{suffix}"
    real_email = f"dupemail{suffix}@example.com"
    payload_first = _signin_payload(username=username, email=real_email)
    first = client.post(_USER_SIGNIN_URL, json=payload_first)
    assert first.status_code == HTTPStatus.CREATED

    try:
        payload_dup = _signin_payload(username=f"other{suffix}", email=real_email)
        response = client.post(_USER_SIGNIN_URL, json=payload_dup)
        assert response.status_code == HTTPStatus.BAD_REQUEST
        assert "email" in response.get_json().lower()
    finally:
        _cleanup_user(client_db, username)


def test_user_signin_post_bad_request_username_exceeds_max_length(client):
    """POST with a username exceeding the DB column max length returns 400."""
    long_username = "u" * 101
    payload = _signin_payload(username=long_username, email="longuser@example.com")
    response = client.post(_USER_SIGNIN_URL, json=payload)
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_user_signin_post_bad_request_email_exceeds_max_length(client):
    """POST with an email exceeding the DB column max length returns 400."""
    long_email = "a" * 247 + "@test.com"
    payload = _signin_payload(username="longmail", email=long_email)
    response = client.post(_USER_SIGNIN_URL, json=payload)
    assert response.status_code == HTTPStatus.BAD_REQUEST
