"""Tests for AdminTestRunPluginsPresets (GET and PUT /admin/test-run-plugins-presets)."""

import os
from http import HTTPStatus

import pytest

from db.models.user import UserModel

_PRESETS_URL = "/admin/test-run-plugins-presets"

_PRESET_FILEPATH = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    os.pardir, "configs", "testrun_plugin_presets.yaml",
)

UT_ADMIN_USER_NAME = "preset_admin_username"
UT_ADMIN_USER_EMAIL = "preset_admin_email"
UT_ADMIN_USER_PASSWORD = "preset_admin_password"
UT_ADMIN_USER_ROLE = "ADMIN"

_VALID_YAML_CONTENT = """\
tmt:
  - name: preset-a
    value: "alpha"
  - name: preset-b
    value: "beta"
lava:
  - name: preset-c
    value: "gamma"
"""

_UPDATED_YAML_CONTENT = """\
tmt:
  - name: preset-x
    value: "x-ray"
"""


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def ut_admin_user_db(client_db):
    dbi = client_db
    ut_admin_user = UserModel(
        UT_ADMIN_USER_NAME, UT_ADMIN_USER_EMAIL,
        UT_ADMIN_USER_PASSWORD, UT_ADMIN_USER_ROLE,
    )
    dbi.session.add(ut_admin_user)
    dbi.session.commit()
    yield ut_admin_user


@pytest.fixture(scope="module")
def admin_authentication(client, ut_admin_user_db):
    return client.post(
        "/user/login",
        json={"email": UT_ADMIN_USER_EMAIL, "password": UT_ADMIN_USER_PASSWORD},
    )


@pytest.fixture(autouse=True)
def _clean_preset_file():
    if os.path.exists(_PRESET_FILEPATH):
        os.remove(_PRESET_FILEPATH)
    yield
    if os.path.exists(_PRESET_FILEPATH):
        os.remove(_PRESET_FILEPATH)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _auth_qs(auth_response):
    """Return the query-string dict needed for GET requests."""
    return {
        "user-id": auth_response.json["id"],
        "token": auth_response.json["token"],
    }


def _auth_body(auth_response, **extra):
    """Return the JSON body dict needed for PUT requests."""
    payload = {
        "user-id": auth_response.json["id"],
        "token": auth_response.json["token"],
    }
    payload.update(extra)
    return payload


def _put_presets(client, auth_response, content):
    return client.put(
        _PRESETS_URL,
        json=_auth_body(auth_response, content=content),
    )


def _get_presets(client, auth_response):
    return client.get(_PRESETS_URL, query_string=_auth_qs(auth_response))


# ---------------------------------------------------------------------------
# GET tests
# ---------------------------------------------------------------------------

class TestGetPresets:
    def test_get_returns_empty_when_no_file(self, client, admin_authentication):
        response = _get_presets(client, admin_authentication)
        assert response.status_code == HTTPStatus.OK
        assert response.json["content"] == ""

    def test_get_returns_file_content_after_put(self, client, admin_authentication):
        put_resp = _put_presets(client, admin_authentication, _VALID_YAML_CONTENT)
        assert put_resp.status_code == HTTPStatus.OK

        response = _get_presets(client, admin_authentication)
        assert response.status_code == HTTPStatus.OK
        assert response.json["content"] == _VALID_YAML_CONTENT

    def test_get_missing_token_returns_bad_request(self, client, admin_authentication):
        response = client.get(
            _PRESETS_URL,
            query_string={"user-id": admin_authentication.json["id"]},
        )
        assert response.status_code == HTTPStatus.BAD_REQUEST

    def test_get_missing_user_id_returns_bad_request(self, client, admin_authentication):
        response = client.get(
            _PRESETS_URL,
            query_string={"token": admin_authentication.json["token"]},
        )
        assert response.status_code == HTTPStatus.BAD_REQUEST

    def test_get_no_params_returns_bad_request(self, client):
        response = client.get(_PRESETS_URL)
        assert response.status_code == HTTPStatus.BAD_REQUEST

    def test_get_invalid_token_returns_unauthorized(self, client, admin_authentication):
        response = client.get(
            _PRESETS_URL,
            query_string={
                "user-id": admin_authentication.json["id"],
                "token": "invalid_token",
            },
        )
        assert response.status_code == HTTPStatus.UNAUTHORIZED

    def test_get_non_admin_user_returns_unauthorized(
        self, client, user_authentication,
    ):
        response = _get_presets(client, user_authentication)
        assert response.status_code == HTTPStatus.UNAUTHORIZED


# ---------------------------------------------------------------------------
# PUT tests
# ---------------------------------------------------------------------------

class TestPutPresets:
    def test_put_valid_yaml_returns_ok(self, client, admin_authentication):
        response = _put_presets(client, admin_authentication, _VALID_YAML_CONTENT)
        assert response.status_code == HTTPStatus.OK
        assert response.json["content"] == _VALID_YAML_CONTENT

    def test_put_overwrites_previous_content(self, client, admin_authentication):
        _put_presets(client, admin_authentication, _VALID_YAML_CONTENT)

        response = _put_presets(client, admin_authentication, _UPDATED_YAML_CONTENT)
        assert response.status_code == HTTPStatus.OK
        assert response.json["content"] == _UPDATED_YAML_CONTENT

        get_resp = _get_presets(client, admin_authentication)
        assert get_resp.json["content"] == _UPDATED_YAML_CONTENT

    def test_put_invalid_yaml_returns_bad_request(self, client, admin_authentication):
        invalid_yaml = "key: [invalid yaml {{{"
        response = _put_presets(client, admin_authentication, invalid_yaml)
        assert response.status_code == HTTPStatus.BAD_REQUEST

    def test_put_missing_content_returns_bad_request(self, client, admin_authentication):
        response = client.put(
            _PRESETS_URL,
            json=_auth_body(admin_authentication),
        )
        assert response.status_code == HTTPStatus.BAD_REQUEST

    def test_put_missing_token_returns_bad_request(self, client, admin_authentication):
        response = client.put(
            _PRESETS_URL,
            json={
                "user-id": admin_authentication.json["id"],
                "content": _VALID_YAML_CONTENT,
            },
        )
        assert response.status_code == HTTPStatus.BAD_REQUEST

    def test_put_missing_user_id_returns_bad_request(self, client, admin_authentication):
        response = client.put(
            _PRESETS_URL,
            json={
                "token": admin_authentication.json["token"],
                "content": _VALID_YAML_CONTENT,
            },
        )
        assert response.status_code == HTTPStatus.BAD_REQUEST

    def test_put_invalid_token_returns_unauthorized(self, client, admin_authentication):
        response = client.put(
            _PRESETS_URL,
            json={
                "user-id": admin_authentication.json["id"],
                "token": "invalid_token",
                "content": _VALID_YAML_CONTENT,
            },
        )
        assert response.status_code == HTTPStatus.UNAUTHORIZED

    def test_put_non_admin_user_returns_unauthorized(
        self, client, user_authentication,
    ):
        response = _put_presets(client, user_authentication, _VALID_YAML_CONTENT)
        assert response.status_code == HTTPStatus.UNAUTHORIZED

    def test_put_empty_yaml_returns_ok(self, client, admin_authentication):
        response = _put_presets(client, admin_authentication, "dummy: value")
        assert response.status_code == HTTPStatus.OK
