"""Tests for TestRunPluginPresets (GET /mapping/api/test-run-plugins-presets)."""

import os
import tempfile
from http import HTTPStatus

import pytest

from conftest import UT_USER_EMAIL
from db.models.api import ApiModel
from db.models.user import UserModel

_PRESETS_URL = "/mapping/api/test-run-plugins-presets"

_UT_API_NAME = "ut_trpp_api"
_UT_API_LIBRARY = "ut_trpp_library"
_UT_API_LIBRARY_VERSION = "v1.0.0"
_UT_API_CATEGORY = "ut_trpp_category"
_UT_API_SPEC = "BASIL UT: spec section for test run plugin presets."

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

_YAML_SINGLE_PLUGIN = """\
tmt:
  - name: only-one
"""

_YAML_NO_NAME_KEY = """\
tmt:
  - value: "no-name-entry"
  - name: has-name
"""

_YAML_PLUGIN_NOT_A_LIST = """\
tmt:
  scalar_key: scalar_value
"""


def _write_spec_tempfile(spec_content: str) -> str:
    raw_spec = tempfile.NamedTemporaryFile(mode="w", delete=False)
    raw_spec.write(spec_content)
    raw_spec.close()
    return raw_spec.name


def _make_api_model(raw_spec_path: str, user, utilities) -> ApiModel:
    return ApiModel(
        _UT_API_NAME + "#" + utilities.generate_random_hex_string8(),
        _UT_API_LIBRARY,
        _UT_API_LIBRARY_VERSION,
        raw_spec_path,
        _UT_API_CATEGORY,
        utilities.generate_random_hex_string8(),
        raw_spec_path + "impl",
        0,
        42,
        "trpp_tag",
        user,
    )


def _auth_qs(auth_response, api_id, **extra):
    qs = {
        "user-id": auth_response.json["id"],
        "token": auth_response.json["token"],
        "api-id": api_id,
    }
    qs.update(extra)
    return qs


def _get_presets(client, auth_response, api_id, plugin, **extra):
    return client.get(
        _PRESETS_URL,
        query_string=_auth_qs(auth_response, api_id, plugin=plugin, **extra),
    )


def _seed_preset_file(content: str):
    """Write *content* to the preset YAML file used by the API."""
    from api import TESTRUN_PRESET_FILEPATH
    os.makedirs(os.path.dirname(TESTRUN_PRESET_FILEPATH), exist_ok=True)
    with open(TESTRUN_PRESET_FILEPATH, "w") as f:
        f.write(content)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def ut_api_db(client_db, ut_user_db, utilities):
    user = client_db.session.query(UserModel).filter(
        UserModel.email == UT_USER_EMAIL,
    ).one()
    raw_path = _write_spec_tempfile(_UT_API_SPEC)
    ut_api = _make_api_model(raw_path, user, utilities)
    client_db.session.add(ut_api)
    client_db.session.commit()
    yield ut_api
    if os.path.isfile(raw_path):
        os.remove(raw_path)


@pytest.fixture(autouse=True)
def _clean_preset_file():
    """Remove the preset file before and after every test so tests are independent."""
    from api import TESTRUN_PRESET_FILEPATH
    yield
    if os.path.exists(TESTRUN_PRESET_FILEPATH):
        os.remove(TESTRUN_PRESET_FILEPATH)


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------

def test_login(user_authentication):
    assert user_authentication.status_code == HTTPStatus.OK


# ---------------------------------------------------------------------------
# GET – unauthorized / bad-request
# ---------------------------------------------------------------------------

def test_get_guest_allowed_by_default(client, ut_api_db):
    """Guest (no auth) gets read access when there are no read denials."""
    response = client.get(
        _PRESETS_URL,
        query_string={"api-id": ut_api_db.id, "plugin": "tmt"},
    )
    assert response.status_code == HTTPStatus.OK


def test_get_guest_denied_with_read_denials(client, client_db, ut_api_db):
    """Guest is denied when any read_denials are set on the API."""
    ut_api_db.read_denials = "[0]"
    client_db.session.commit()
    response = client.get(
        _PRESETS_URL,
        query_string={"api-id": ut_api_db.id, "plugin": "tmt"},
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED
    ut_api_db.read_denials = ""
    client_db.session.commit()


def test_get_missing_plugin(client, user_authentication, ut_api_db):
    response = client.get(
        _PRESETS_URL,
        query_string=_auth_qs(user_authentication, ut_api_db.id),
    )
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_get_missing_api_id(client, user_authentication, ut_api_db):
    response = client.get(
        _PRESETS_URL,
        query_string={
            "user-id": user_authentication.json["id"],
            "token": user_authentication.json["token"],
            "plugin": "tmt",
        },
    )
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_get_nonexistent_api_id(client, user_authentication):
    response = client.get(
        _PRESETS_URL,
        query_string={
            "user-id": user_authentication.json["id"],
            "token": user_authentication.json["token"],
            "api-id": 999999,
            "plugin": "tmt",
        },
    )
    assert response.status_code == HTTPStatus.NOT_FOUND


# ---------------------------------------------------------------------------
# GET – no preset file on disk
# ---------------------------------------------------------------------------

def test_get_returns_empty_list_when_no_file(client, user_authentication, ut_api_db):
    response = _get_presets(client, user_authentication, ut_api_db.id, "tmt")
    assert response.status_code == HTTPStatus.OK
    assert response.json == []


# ---------------------------------------------------------------------------
# GET – preset file present, various contents
# ---------------------------------------------------------------------------

def test_get_returns_names_for_matching_plugin(client, user_authentication, ut_api_db):
    _seed_preset_file(_VALID_YAML_CONTENT)
    response = _get_presets(client, user_authentication, ut_api_db.id, "tmt")
    assert response.status_code == HTTPStatus.OK
    assert response.json == ["preset-a", "preset-b"]


def test_get_returns_names_for_another_plugin(client, user_authentication, ut_api_db):
    _seed_preset_file(_VALID_YAML_CONTENT)
    response = _get_presets(client, user_authentication, ut_api_db.id, "lava")
    assert response.status_code == HTTPStatus.OK
    assert response.json == ["preset-c"]


def test_get_returns_empty_for_unknown_plugin(client, user_authentication, ut_api_db):
    _seed_preset_file(_VALID_YAML_CONTENT)
    response = _get_presets(client, user_authentication, ut_api_db.id, "nonexistent")
    assert response.status_code == HTTPStatus.OK
    assert response.json == []


def test_get_single_preset(client, user_authentication, ut_api_db):
    _seed_preset_file(_YAML_SINGLE_PLUGIN)
    response = _get_presets(client, user_authentication, ut_api_db.id, "tmt")
    assert response.status_code == HTTPStatus.OK
    assert response.json == ["only-one"]


def test_get_skips_entries_without_name_key(client, user_authentication, ut_api_db):
    _seed_preset_file(_YAML_NO_NAME_KEY)
    response = _get_presets(client, user_authentication, ut_api_db.id, "tmt")
    assert response.status_code == HTTPStatus.OK
    assert response.json == ["has-name"]


def test_get_plugin_value_not_a_list(client, user_authentication, ut_api_db):
    """When the plugin key maps to a non-list value the endpoint returns an empty list."""
    _seed_preset_file(_YAML_PLUGIN_NOT_A_LIST)
    response = _get_presets(client, user_authentication, ut_api_db.id, "tmt")
    assert response.status_code == HTTPStatus.OK
    assert response.json == []
