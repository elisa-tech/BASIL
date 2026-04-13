"""Tests for UserResetPassword (/user/reset-password)."""

import base64
from http import HTTPStatus

import pytest
from conftest import UT_USER_EMAIL
from db.models.user import UserModel


_USER_RESET_PASSWORD_URL = "/user/reset-password"


def _patch_email_notifier_send(monkeypatch, send_returns: bool = True):
    """Stub api.EmailNotifier (api.py module) so send_email returns send_returns."""

    class _EmailNotifierStub:
        def __init__(self, *args, **kwargs):
            pass

        def send_email(self, *args, **kwargs):
            return send_returns

    monkeypatch.setattr("api.EmailNotifier", _EmailNotifierStub)


def _user_by_email(client_db, email: str) -> UserModel:
    return client_db.session.query(UserModel).filter(UserModel.email == email).one()


def test_user_reset_password_post_created(client, client_db, ut_user_db, monkeypatch):
    """POST with a known user generates reset fields and returns 201 when email sends."""
    _patch_email_notifier_send(monkeypatch, True)

    response = client.post(_USER_RESET_PASSWORD_URL, json={"email": UT_USER_EMAIL})
    assert response.status_code == HTTPStatus.CREATED
    data = response.get_json()
    assert data["result"] == "success"
    assert "sent" in data["message"].lower()

    client_db.session.expire_all()
    user_after = _user_by_email(client_db, UT_USER_EMAIL)
    assert user_after.reset_token
    assert user_after.reset_pwd


@pytest.mark.parametrize(
    "payload",
    (
        {},
        {"wrong": "field"},
    ),
)
def test_user_reset_password_post_bad_request_missing_email(client, payload):
    """POST without mandatory email returns 400."""
    response = client.post(_USER_RESET_PASSWORD_URL, json=payload)
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_user_reset_password_post_not_found_user(client, monkeypatch):
    """POST for an unknown email returns 404."""
    _patch_email_notifier_send(monkeypatch, True)
    response = client.post(
        _USER_RESET_PASSWORD_URL,
        json={"email": "not_registered_user@example.com"},
    )
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_user_reset_password_post_precondition_failed_when_email_not_sent(
    client, ut_user_db, monkeypatch
):
    """POST returns 412 when the notifier cannot send email."""
    _patch_email_notifier_send(monkeypatch, False)
    response = client.post(_USER_RESET_PASSWORD_URL, json={"email": UT_USER_EMAIL})
    assert response.status_code == HTTPStatus.PRECONDITION_FAILED


@pytest.mark.parametrize(
    "query_string",
    (
        None,
        {"email": UT_USER_EMAIL},
        {"reset_token": "only_token"},
    ),
)
def test_user_reset_password_get_bad_request_missing_fields(client, query_string):
    """GET without both email and reset_token returns 400."""
    kwargs = {}
    if query_string is not None:
        kwargs["query_string"] = query_string
    response = client.get(_USER_RESET_PASSWORD_URL, **kwargs)
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_user_reset_password_get_not_found_wrong_token(client, client_db, ut_user_db, monkeypatch):
    """GET with non-matching token returns 404."""
    _patch_email_notifier_send(monkeypatch, True)
    user = _user_by_email(client_db, UT_USER_EMAIL)
    prev_token, prev_reset_pwd = user.reset_token, user.reset_pwd
    user.reset_token = "expected_token"
    user.reset_pwd = base64.b64encode(b"tmp_pass_xx").decode("utf-8")
    client_db.session.add(user)
    client_db.session.commit()

    response = client.get(
        _USER_RESET_PASSWORD_URL,
        query_string={"email": UT_USER_EMAIL, "reset_token": "wrong_token"},
    )
    assert response.status_code == HTTPStatus.NOT_FOUND

    user.reset_token = prev_token
    user.reset_pwd = prev_reset_pwd
    client_db.session.add(user)
    client_db.session.commit()


def test_user_reset_password_get_ok_applies_reset_and_clears_fields(
    client, client_db, ut_user_db, monkeypatch
):
    """GET with matching email and token copies reset password, clears token fields, returns 200."""
    _patch_email_notifier_send(monkeypatch, True)
    user = _user_by_email(client_db, UT_USER_EMAIL)
    original_pwd = user.pwd
    new_encoded = base64.b64encode(b"replacement_pass_12").decode("utf-8")
    token = "unit_test_reset_token_abc"
    user.reset_pwd = new_encoded
    user.reset_token = token
    client_db.session.add(user)
    client_db.session.commit()

    response = client.get(
        _USER_RESET_PASSWORD_URL,
        query_string={"email": UT_USER_EMAIL, "reset_token": token},
    )
    assert response.status_code == HTTPStatus.OK
    data = response.get_json()
    assert data["result"] == "success"

    client_db.session.expire_all()
    user = _user_by_email(client_db, UT_USER_EMAIL)
    assert user.pwd == new_encoded
    assert user.reset_pwd == ""
    assert user.reset_token == ""

    user.pwd = original_pwd
    user.reset_pwd = ""
    user.reset_token = ""
    client_db.session.add(user)
    client_db.session.commit()


def test_user_reset_password_get_precondition_failed_when_email_not_sent(
    client, client_db, ut_user_db, monkeypatch
):
    """GET returns 412 when confirmation email cannot be sent after reset."""
    _patch_email_notifier_send(monkeypatch, False)
    user = _user_by_email(client_db, UT_USER_EMAIL)
    original_pwd = user.pwd
    new_encoded = base64.b64encode(b"other_tmp_pass_9").decode("utf-8")
    token = "unit_test_reset_token_def"
    user.reset_pwd = new_encoded
    user.reset_token = token
    client_db.session.add(user)
    client_db.session.commit()

    response = client.get(
        _USER_RESET_PASSWORD_URL,
        query_string={"email": UT_USER_EMAIL, "reset_token": token},
    )
    assert response.status_code == HTTPStatus.PRECONDITION_FAILED

    client_db.session.expire_all()
    user = _user_by_email(client_db, UT_USER_EMAIL)
    user.pwd = original_pwd
    user.reset_pwd = ""
    user.reset_token = ""
    client_db.session.add(user)
    client_db.session.commit()
