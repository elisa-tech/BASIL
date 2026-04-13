import os
import tempfile
import pytest
from http import HTTPStatus

from db.models.user import UserModel
from db.models.api import ApiModel
from conftest import UT_USER_EMAIL

_TEST_RUN_CONFIGS_URL = "/mapping/api/test-run-configs"

_UT_API_NAME = "ut_trc_api"
_UT_API_LIBRARY = "ut_trc_library"
_UT_API_LIBRARY_VERSION = "v1.0.0"
_UT_API_CATEGORY = "ut_trc_category"
_UT_API_SPEC = "BASIL UT: spec section for test run config."


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
        "trc_tag",
        user,
    )


def _auth_fields(auth_json):
    return {"user-id": auth_json["id"], "token": auth_json["token"]}


def _base_tmt_config_data(auth_json, utilities, **overrides):
    data = {
        "id": "",
        "title": f"UT TMT Config {utilities.generate_random_hex_string8()}",
        "plugin": "tmt",
        "plugin_preset": "",
        "environment_vars": "VAR1=val1",
        "git_repo_ref": "main",
        "context_vars": "distro=fedora",
        "provision_type": "container",
        "provision_guest": "",
        "provision_guest_port": "",
        "ssh_key": "",
        **_auth_fields(auth_json),
    }
    data.update(overrides)
    return data


@pytest.fixture()
def ut_api_db(client_db, ut_user_db, utilities):
    user = client_db.session.query(UserModel).filter(UserModel.email == UT_USER_EMAIL).one()
    raw_path = _write_spec_tempfile(_UT_API_SPEC)
    ut_api = _make_api_model(raw_path, user, utilities)
    client_db.session.add(ut_api)
    client_db.session.commit()
    yield ut_api
    if os.path.isfile(raw_path):
        os.remove(raw_path)


# --- Authentication ---


def test_login(user_authentication):
    assert user_authentication.status_code == HTTPStatus.OK


# --- GET ---


def test_get_unauthorized(client, ut_api_db):
    response = client.get(
        _TEST_RUN_CONFIGS_URL,
        query_string={"user-id": 0, "token": "invalid"},
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED


def test_get_empty_list(client, user_authentication, ut_api_db):
    response = client.get(
        _TEST_RUN_CONFIGS_URL,
        query_string=_auth_fields(user_authentication.json),
    )
    assert response.status_code == HTTPStatus.OK
    assert isinstance(response.json, list)


def test_get_returns_created_config(client, user_authentication, ut_api_db, utilities):
    post_data = _base_tmt_config_data(user_authentication.json, utilities)
    post_resp = client.post(_TEST_RUN_CONFIGS_URL, json=post_data)
    assert post_resp.status_code == HTTPStatus.CREATED

    get_resp = client.get(
        _TEST_RUN_CONFIGS_URL,
        query_string=_auth_fields(user_authentication.json),
    )
    assert get_resp.status_code == HTTPStatus.OK
    configs = get_resp.json
    assert isinstance(configs, list)
    assert any(c["id"] == post_resp.json["id"] for c in configs)


def test_get_search_filter(client, user_authentication, ut_api_db, utilities):
    unique_marker = f"SEARCHABLE-{utilities.generate_random_hex_string8()}"
    post_data = _base_tmt_config_data(
        user_authentication.json, utilities, title=unique_marker,
    )
    post_resp = client.post(_TEST_RUN_CONFIGS_URL, json=post_data)
    assert post_resp.status_code == HTTPStatus.CREATED

    get_resp = client.get(
        _TEST_RUN_CONFIGS_URL,
        query_string={**_auth_fields(user_authentication.json), "search": unique_marker},
    )
    assert get_resp.status_code == HTTPStatus.OK
    configs = get_resp.json
    assert len(configs) == 1
    assert configs[0]["title"] == unique_marker


def test_get_search_no_match(client, user_authentication, ut_api_db):
    get_resp = client.get(
        _TEST_RUN_CONFIGS_URL,
        query_string={**_auth_fields(user_authentication.json), "search": "NONEXISTENT_TERM_XYZ"},
    )
    assert get_resp.status_code == HTTPStatus.OK
    assert get_resp.json == []


# --- POST ---


def test_post_unauthorized(client, ut_api_db, utilities):
    post_data = {
        "id": "",
        "title": "unauthorized config",
        "plugin": "tmt",
        "plugin_preset": "",
        "environment_vars": "",
        "git_repo_ref": "",
        "context_vars": "",
        "provision_type": "container",
        "provision_guest": "",
        "provision_guest_port": "",
        "ssh_key": "",
        "user-id": 0,
        "token": "invalid",
    }
    response = client.post(_TEST_RUN_CONFIGS_URL, json=post_data)
    assert response.status_code == HTTPStatus.UNAUTHORIZED


@pytest.mark.parametrize(
    "missing_field",
    ["title", "plugin", "environment_vars", "git_repo_ref", "plugin_preset"],
)
def test_post_missing_mandatory_fields(client, user_authentication, ut_api_db, utilities, missing_field):
    post_data = _base_tmt_config_data(user_authentication.json, utilities)
    del post_data[missing_field]
    response = client.post(_TEST_RUN_CONFIGS_URL, json=post_data)
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_post_empty_title(client, user_authentication, ut_api_db, utilities):
    post_data = _base_tmt_config_data(user_authentication.json, utilities, title="")
    response = client.post(_TEST_RUN_CONFIGS_URL, json=post_data)
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_post_tmt_container_ok(client, user_authentication, ut_api_db, utilities):
    post_data = _base_tmt_config_data(user_authentication.json, utilities)
    response = client.post(_TEST_RUN_CONFIGS_URL, json=post_data)
    assert response.status_code == HTTPStatus.CREATED
    assert isinstance(response.json, dict)
    assert response.json["plugin"] == "tmt"
    assert response.json["title"] == post_data["title"]
    assert response.json["provision_type"] == "container"


def test_post_tmt_missing_tmt_fields(client, user_authentication, ut_api_db, utilities):
    post_data = _base_tmt_config_data(user_authentication.json, utilities)
    del post_data["provision_type"]
    response = client.post(_TEST_RUN_CONFIGS_URL, json=post_data)
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_post_tmt_connect_missing_guest_info(client, user_authentication, ut_api_db, utilities):
    post_data = _base_tmt_config_data(
        user_authentication.json, utilities,
        provision_type="connect",
        provision_guest="",
        provision_guest_port="",
        ssh_key="",
    )
    response = client.post(_TEST_RUN_CONFIGS_URL, json=post_data)
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_post_tmt_connect_invalid_ssh_key(client, user_authentication, ut_api_db, utilities):
    post_data = _base_tmt_config_data(
        user_authentication.json, utilities,
        provision_type="connect",
        provision_guest="192.168.1.1",
        provision_guest_port="22",
        ssh_key="99999",
    )
    response = client.post(_TEST_RUN_CONFIGS_URL, json=post_data)
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_post_tmt_preset_skips_provision_type_check(client, user_authentication, ut_api_db, utilities):
    post_data = _base_tmt_config_data(
        user_authentication.json, utilities,
        plugin_preset="my_preset",
        provision_type="",
    )
    response = client.post(_TEST_RUN_CONFIGS_URL, json=post_data)
    assert response.status_code == HTTPStatus.CREATED
    assert response.json["plugin_preset"] == "my_preset"


def test_post_existing_id_returns_config(client, user_authentication, ut_api_db, utilities):
    post_data = _base_tmt_config_data(user_authentication.json, utilities)
    create_resp = client.post(_TEST_RUN_CONFIGS_URL, json=post_data)
    assert create_resp.status_code == HTTPStatus.CREATED
    config_id = create_resp.json["id"]

    lookup_data = _base_tmt_config_data(user_authentication.json, utilities, id=config_id)
    lookup_resp = client.post(_TEST_RUN_CONFIGS_URL, json=lookup_data)
    assert lookup_resp.status_code == HTTPStatus.OK
    assert lookup_resp.json["id"] == config_id


def test_post_nonexistent_id_returns_bad_request(client, user_authentication, ut_api_db, utilities):
    post_data = _base_tmt_config_data(user_authentication.json, utilities, id=999999)
    response = client.post(_TEST_RUN_CONFIGS_URL, json=post_data)
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_post_invalid_id_format(client, user_authentication, ut_api_db, utilities):
    post_data = _base_tmt_config_data(user_authentication.json, utilities, id="not_a_number")
    response = client.post(_TEST_RUN_CONFIGS_URL, json=post_data)
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_post_gitlab_ci_ok(client, user_authentication, ut_api_db, utilities):
    post_data = _base_tmt_config_data(
        user_authentication.json, utilities,
        plugin="gitlab_ci",
        job="build_job",
        private_token="glpat-xxxx",
        project_id="12345",
        stage="test",
        trigger_token="trig-xxxx",
        url="https://gitlab.example.com",
    )
    response = client.post(_TEST_RUN_CONFIGS_URL, json=post_data)
    assert response.status_code == HTTPStatus.CREATED
    assert response.json["plugin"] == "gitlab_ci"


def test_post_gitlab_ci_missing_fields(client, user_authentication, ut_api_db, utilities):
    post_data = _base_tmt_config_data(
        user_authentication.json, utilities,
        plugin="gitlab_ci",
    )
    response = client.post(_TEST_RUN_CONFIGS_URL, json=post_data)
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_post_github_actions_ok(client, user_authentication, ut_api_db, utilities):
    post_data = _base_tmt_config_data(
        user_authentication.json, utilities,
        plugin="github_actions",
        job="test-job",
        private_token="ghp_xxxx",
        url="https://api.github.com",
        workflow_id="ci.yml",
    )
    response = client.post(_TEST_RUN_CONFIGS_URL, json=post_data)
    assert response.status_code == HTTPStatus.CREATED
    assert response.json["plugin"] == "github_actions"


def test_post_github_actions_missing_fields(client, user_authentication, ut_api_db, utilities):
    post_data = _base_tmt_config_data(
        user_authentication.json, utilities,
        plugin="github_actions",
    )
    response = client.post(_TEST_RUN_CONFIGS_URL, json=post_data)
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_post_testing_farm_ok(client, user_authentication, ut_api_db, utilities):
    post_data = _base_tmt_config_data(
        user_authentication.json, utilities,
        plugin="testing_farm",
        arch="x86_64",
        compose="Fedora-40",
        private_token="tf-xxxx",
        url="https://api.testing-farm.io",
    )
    response = client.post(_TEST_RUN_CONFIGS_URL, json=post_data)
    assert response.status_code == HTTPStatus.CREATED
    assert response.json["plugin"] == "testing_farm"


def test_post_testing_farm_missing_fields(client, user_authentication, ut_api_db, utilities):
    post_data = _base_tmt_config_data(
        user_authentication.json, utilities,
        plugin="testing_farm",
    )
    response = client.post(_TEST_RUN_CONFIGS_URL, json=post_data)
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_post_lava_ok(client, user_authentication, ut_api_db, utilities):
    post_data = _base_tmt_config_data(
        user_authentication.json, utilities,
        plugin="LAVA",
        job="lava-job.yaml",
        private_token="lava-xxxx",
        url="https://lava.example.com",
    )
    response = client.post(_TEST_RUN_CONFIGS_URL, json=post_data)
    assert response.status_code == HTTPStatus.CREATED
    assert response.json["plugin"] == "LAVA"


def test_post_lava_missing_fields(client, user_authentication, ut_api_db, utilities):
    post_data = _base_tmt_config_data(
        user_authentication.json, utilities,
        plugin="LAVA",
    )
    response = client.post(_TEST_RUN_CONFIGS_URL, json=post_data)
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_post_response_fields(client, user_authentication, ut_api_db, utilities):
    post_data = _base_tmt_config_data(user_authentication.json, utilities)
    response = client.post(_TEST_RUN_CONFIGS_URL, json=post_data)
    assert response.status_code == HTTPStatus.CREATED
    config = response.json
    expected_keys = {
        "id", "plugin", "plugin_preset", "plugin_vars", "title",
        "git_repo_ref", "context_vars", "environment_vars",
        "provision_type", "provision_guest", "provision_guest_port",
        "ssh_key", "created_by",
    }
    assert expected_keys.issubset(set(config.keys()))


def test_post_multiple_configs_returned_by_get(client, user_authentication, ut_api_db, utilities):
    ids = []
    for _ in range(3):
        post_data = _base_tmt_config_data(user_authentication.json, utilities)
        resp = client.post(_TEST_RUN_CONFIGS_URL, json=post_data)
        assert resp.status_code == HTTPStatus.CREATED
        ids.append(resp.json["id"])

    get_resp = client.get(
        _TEST_RUN_CONFIGS_URL,
        query_string=_auth_fields(user_authentication.json),
    )
    assert get_resp.status_code == HTTPStatus.OK
    returned_ids = [c["id"] for c in get_resp.json]
    for config_id in ids:
        assert config_id in returned_ids


def test_get_configs_belong_to_user(client, user_authentication, reader_authentication, ut_api_db, utilities):
    post_data = _base_tmt_config_data(user_authentication.json, utilities)
    post_resp = client.post(_TEST_RUN_CONFIGS_URL, json=post_data)
    assert post_resp.status_code == HTTPStatus.CREATED
    config_id = post_resp.json["id"]

    reader_get = client.get(
        _TEST_RUN_CONFIGS_URL,
        query_string=_auth_fields(reader_authentication.json),
    )
    assert reader_get.status_code == HTTPStatus.OK
    reader_ids = [c["id"] for c in reader_get.json]
    assert config_id not in reader_ids
