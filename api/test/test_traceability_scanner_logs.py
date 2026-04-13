"""HTTP tests for TraceabilityScannerLogs (/traceability-scanner/logs)."""
import os
from http import HTTPStatus

import pytest

import api as basil_api

LOGS_URL = "/traceability-scanner/logs"


def _user_config_dir(user_id):
    return os.path.join(basil_api.USER_FILES_BASE_DIR, str(user_id), ".config")


def _auth_query(auth_json, scan_id):
    return {"user-id": auth_json["id"], "token": auth_json["token"], "scan-id": scan_id}


def _auth_body(auth_json, scan_id):
    return {"user-id": auth_json["id"], "token": auth_json["token"], "scan-id": scan_id}


def _create_log_file(config_dir, scan_id, content="log line 1\nlog line 2\n"):
    os.makedirs(config_dir, exist_ok=True)
    path = os.path.join(config_dir, scan_id)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path


def _remove_if_exists(path):
    if os.path.isfile(path):
        os.remove(path)


@pytest.fixture()
def config_dir(ut_user_db):
    d = _user_config_dir(ut_user_db.id)
    os.makedirs(d, exist_ok=True)
    created_files = []
    yield d, created_files
    for p in created_files:
        _remove_if_exists(p)


# ------------------------------------------------------------------
# GET tests
#
# NOTE: The GET handler reads query params through get_query_string_args()
# which only forwards keys listed in its permitted_keys whitelist.
# "scan-id" is NOT in that whitelist, so it is always stripped from
# request_data, causing the mandatory-fields check to fail with 400.
# The tests below document this current behaviour.
# ------------------------------------------------------------------


class TestGetLogs:
    def test_get_missing_mandatory_fields_no_scan_id(self, client, user_authentication):
        auth = user_authentication.json
        qs = {"user-id": auth["id"], "token": auth["token"]}
        response = client.get(LOGS_URL, query_string=qs)
        assert response.status_code == HTTPStatus.BAD_REQUEST

    @pytest.mark.parametrize("omit_key", ["user-id", "token"])
    def test_get_missing_auth_field(self, client, user_authentication, omit_key):
        qs = _auth_query(user_authentication.json, "some-scan-id")
        del qs[omit_key]
        response = client.get(LOGS_URL, query_string=qs)
        assert response.status_code == HTTPStatus.BAD_REQUEST

    def test_get_no_credentials(self, client):
        response = client.get(LOGS_URL, query_string={"scan-id": "x"})
        assert response.status_code == HTTPStatus.BAD_REQUEST

    def test_get_scan_id_stripped_by_query_string_parser(self, client, user_authentication):
        """scan-id is not in get_query_string_args permitted_keys,
        so any GET always returns 400 regardless of valid auth + scan-id."""
        auth = user_authentication.json
        qs = _auth_query(auth, "valid-scan-id")
        response = client.get(LOGS_URL, query_string=qs)
        assert response.status_code == HTTPStatus.BAD_REQUEST


# ------------------------------------------------------------------
# DELETE tests
# ------------------------------------------------------------------


class TestDeleteLogs:
    def test_delete_missing_mandatory_fields(self, client, user_authentication):
        auth = user_authentication.json
        body = {"user-id": auth["id"], "token": auth["token"]}
        response = client.delete(LOGS_URL, json=body)
        assert response.status_code == HTTPStatus.BAD_REQUEST

    @pytest.mark.parametrize("omit_key", ["user-id", "token", "scan-id"])
    def test_delete_missing_single_field(self, client, user_authentication, omit_key):
        body = _auth_body(user_authentication.json, "some-scan-id")
        del body[omit_key]
        response = client.delete(LOGS_URL, json=body)
        assert response.status_code in (HTTPStatus.BAD_REQUEST, HTTPStatus.UNAUTHORIZED)

    def test_delete_unauthorized_invalid_token(self, client, user_authentication):
        auth = user_authentication.json
        body = {"user-id": auth["id"], "token": "invalid-token", "scan-id": "some-scan"}
        response = client.delete(LOGS_URL, json=body)
        assert response.status_code == HTTPStatus.UNAUTHORIZED

    @pytest.mark.parametrize("bad_scan_id", ["", "../etc/passwd", "foo/bar", "/absolute"])
    def test_delete_invalid_scan_id(self, client, user_authentication, bad_scan_id):
        body = _auth_body(user_authentication.json, bad_scan_id)
        response = client.delete(LOGS_URL, json=body)
        assert response.status_code == HTTPStatus.BAD_REQUEST

    def test_delete_not_found(self, client, user_authentication, utilities):
        scan_id = f"nonexistent_{utilities.generate_random_hex_string8()}.log"
        body = _auth_body(user_authentication.json, scan_id)
        response = client.delete(LOGS_URL, json=body)
        assert response.status_code == HTTPStatus.NOT_FOUND

    def test_delete_ok(self, client, user_authentication, config_dir, utilities):
        d, tracked = config_dir
        scan_id = f"scan_{utilities.generate_random_hex_string8()}.log"
        path = _create_log_file(d, scan_id)

        body = _auth_body(user_authentication.json, scan_id)
        response = client.delete(LOGS_URL, json=body)
        assert response.status_code == HTTPStatus.OK
        data = response.get_json()
        assert data["status"] == "success"
        assert not os.path.exists(path)

    def test_delete_removes_file_from_disk(self, client, user_authentication, config_dir, utilities):
        d, tracked = config_dir
        scan_id = f"scan_{utilities.generate_random_hex_string8()}.log"
        path = _create_log_file(d, scan_id, "to-be-deleted")
        assert os.path.isfile(path)

        body = _auth_body(user_authentication.json, scan_id)
        response = client.delete(LOGS_URL, json=body)
        assert response.status_code == HTTPStatus.OK
        assert not os.path.isfile(path)
