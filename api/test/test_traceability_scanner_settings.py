"""HTTP tests for TraceabilityScannerSettings (/traceability-scanner/settings)."""
import os
import shutil
from http import HTTPStatus

import pytest

from api_utils import get_user_config_folder_path


_SETTINGS_URL = "/traceability-scanner/settings"

_VALID_CONFIG = "api: []\n"
_INVALID_YAML = "api: [\ninvalid: {{\n"


def _auth_query(auth_json):
    return {"user-id": auth_json["id"], "token": auth_json["token"]}


def _auth_body(auth_json, content=_VALID_CONFIG):
    return {"user-id": auth_json["id"], "token": auth_json["token"], "content": content}


def _ensure_config_dir(user):
    """Create the user .config directory and return its path."""
    config_dir = get_user_config_folder_path(user)
    os.makedirs(config_dir, exist_ok=True)
    return config_dir


def _write_config_file(config_dir, content=_VALID_CONFIG):
    """Write a config.yaml in the given directory and return its path."""
    filepath = os.path.join(config_dir, "config.yaml")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    return filepath


def _remove_config_dir(config_dir):
    """Remove the whole config directory if present."""
    if os.path.isdir(config_dir):
        shutil.rmtree(config_dir)


@pytest.fixture()
def config_dir(ut_user_db):
    """Provide a clean .config directory that is torn down after the test."""
    d = _ensure_config_dir(ut_user_db)
    yield d
    _remove_config_dir(d)


# ------------------------------------------------------------------
# GET /traceability-scanner/settings
# ------------------------------------------------------------------


class TestGetSettings:
    def test_get_missing_fields_returns_bad_request(self, client):
        response = client.get(_SETTINGS_URL)
        assert response.status_code == HTTPStatus.BAD_REQUEST

    @pytest.mark.parametrize("omit_key", ["user-id", "token"])
    def test_get_missing_single_field_returns_bad_request(
        self, client, user_authentication, omit_key
    ):
        qs = _auth_query(user_authentication.json)
        del qs[omit_key]
        response = client.get(_SETTINGS_URL, query_string=qs)
        assert response.status_code == HTTPStatus.BAD_REQUEST

    def test_get_unauthorized_invalid_token(self, client, user_authentication):
        auth = user_authentication.json
        response = client.get(
            _SETTINGS_URL,
            query_string={"user-id": auth["id"], "token": "invalid-token"},
        )
        assert response.status_code == HTTPStatus.UNAUTHORIZED

    def test_get_creates_default_config_when_none_exists(
        self, client, user_authentication, ut_user_db
    ):
        config_dir = _ensure_config_dir(ut_user_db)
        config_path = os.path.join(config_dir, "config.yaml")
        if os.path.exists(config_path):
            os.remove(config_path)
        _remove_config_dir(config_dir)

        try:
            auth = user_authentication.json
            response = client.get(_SETTINGS_URL, query_string=_auth_query(auth))
            assert response.status_code == HTTPStatus.OK
            data = response.get_json()
            assert data["content"] == "api: []\n"
        finally:
            _remove_config_dir(config_dir)

    def test_get_returns_existing_config(
        self, client, user_authentication, config_dir
    ):
        custom_config = "api:\n  - name: my-repo\n"
        _write_config_file(config_dir, custom_config)

        auth = user_authentication.json
        response = client.get(_SETTINGS_URL, query_string=_auth_query(auth))
        assert response.status_code == HTTPStatus.OK
        data = response.get_json()
        assert data["content"] == custom_config

    def test_get_returns_ok_with_content_key(
        self, client, user_authentication, config_dir
    ):
        _write_config_file(config_dir)

        auth = user_authentication.json
        response = client.get(_SETTINGS_URL, query_string=_auth_query(auth))
        assert response.status_code == HTTPStatus.OK
        data = response.get_json()
        assert "content" in data


# ------------------------------------------------------------------
# PUT /traceability-scanner/settings
# ------------------------------------------------------------------


class TestPutSettings:
    def test_put_missing_fields_returns_bad_request(self, client):
        response = client.put(_SETTINGS_URL, json={})
        assert response.status_code == HTTPStatus.BAD_REQUEST

    @pytest.mark.parametrize("omit_key", ["user-id", "token", "content"])
    def test_put_missing_single_field_returns_bad_request(
        self, client, user_authentication, omit_key
    ):
        body = _auth_body(user_authentication.json)
        del body[omit_key]
        response = client.put(_SETTINGS_URL, json=body)
        assert response.status_code == HTTPStatus.BAD_REQUEST

    def test_put_unauthorized_invalid_token(self, client, user_authentication):
        auth = user_authentication.json
        response = client.put(
            _SETTINGS_URL,
            json={"user-id": auth["id"], "token": "invalid-token", "content": _VALID_CONFIG},
        )
        assert response.status_code == HTTPStatus.UNAUTHORIZED

    def test_put_invalid_yaml_returns_bad_request(
        self, client, user_authentication, config_dir
    ):
        auth = user_authentication.json
        body = _auth_body(auth, content=_INVALID_YAML)
        response = client.put(_SETTINGS_URL, json=body)
        assert response.status_code == HTTPStatus.BAD_REQUEST

    def test_put_valid_config_returns_ok(
        self, client, user_authentication, config_dir
    ):
        auth = user_authentication.json
        body = _auth_body(auth)
        response = client.put(_SETTINGS_URL, json=body)
        assert response.status_code == HTTPStatus.OK
        data = response.get_json()
        assert data["content"] == _VALID_CONFIG

    def test_put_writes_config_to_disk(
        self, client, user_authentication, config_dir
    ):
        new_config = "api:\n  - name: written-repo\n"
        auth = user_authentication.json
        body = _auth_body(auth, content=new_config)
        response = client.put(_SETTINGS_URL, json=body)
        assert response.status_code == HTTPStatus.OK

        config_path = os.path.join(config_dir, "config.yaml")
        assert os.path.isfile(config_path)
        with open(config_path, "r", encoding="utf-8") as f:
            disk_content = f.read()
        assert disk_content == new_config

    def test_put_then_get_returns_same_content(
        self, client, user_authentication, config_dir
    ):
        new_config = "api:\n  - name: roundtrip-repo\n"
        auth = user_authentication.json

        put_response = client.put(_SETTINGS_URL, json=_auth_body(auth, content=new_config))
        assert put_response.status_code == HTTPStatus.OK

        get_response = client.get(_SETTINGS_URL, query_string=_auth_query(auth))
        assert get_response.status_code == HTTPStatus.OK
        assert get_response.get_json()["content"] == new_config

    def test_put_overwrites_existing_config(
        self, client, user_authentication, config_dir
    ):
        _write_config_file(config_dir, "api: []\n")

        updated_config = "api:\n  - name: updated-repo\n"
        auth = user_authentication.json
        body = _auth_body(auth, content=updated_config)
        response = client.put(_SETTINGS_URL, json=body)
        assert response.status_code == HTTPStatus.OK

        config_path = os.path.join(config_dir, "config.yaml")
        with open(config_path, "r", encoding="utf-8") as f:
            disk_content = f.read()
        assert disk_content == updated_config

    def test_put_empty_string_content_returns_bad_request(
        self, client, user_authentication, config_dir
    ):
        auth = user_authentication.json
        body = _auth_body(auth, content="")
        response = client.put(_SETTINGS_URL, json=body)
        assert response.status_code == HTTPStatus.BAD_REQUEST
