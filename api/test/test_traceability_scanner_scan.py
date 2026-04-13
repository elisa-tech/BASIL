"""HTTP tests for TraceabilityScannerScan (/traceability-scanner/scan)."""
import os
import shutil
from http import HTTPStatus
from unittest.mock import patch

import pytest

from api_utils import get_user_config_folder_path


_SCAN_URL = "/traceability-scanner/scan"


def _auth_query(auth_json):
    return {"user-id": auth_json["id"], "token": auth_json["token"]}


def _auth_json_body(auth_json):
    return {"user-id": auth_json["id"], "token": auth_json["token"]}


def _ensure_config_dir(user):
    """Create the user .config directory and return its path."""
    config_dir = get_user_config_folder_path(user)
    os.makedirs(config_dir, exist_ok=True)
    return config_dir


def _write_config_file(config_dir, content="api: []\n"):
    """Write a config.yaml in the given directory."""
    filepath = os.path.join(config_dir, "config.yaml")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    return filepath


def _create_log_file(config_dir, name="20250101_120000.log"):
    """Create a dummy .log file and return its path."""
    path = os.path.join(config_dir, name)
    with open(path, "w", encoding="utf-8") as f:
        f.write("log content\n")
    return path


def _remove_config_dir(config_dir):
    """Remove the whole config directory if present."""
    if os.path.isdir(config_dir):
        shutil.rmtree(config_dir)


# ----------------------------------------------------------------
# GET /traceability-scanner/scan
# ----------------------------------------------------------------


class TestTraceabilityScannerScanGet:
    def test_get_missing_fields_returns_bad_request(self, client):
        response = client.get(_SCAN_URL)
        assert response.status_code == HTTPStatus.BAD_REQUEST

    @pytest.mark.parametrize("omit_key", ["user-id", "token"])
    def test_get_missing_single_field_returns_bad_request(
        self, client, user_authentication, omit_key
    ):
        qs = _auth_query(user_authentication.json)
        del qs[omit_key]
        response = client.get(_SCAN_URL, query_string=qs)
        assert response.status_code == HTTPStatus.BAD_REQUEST

    def test_get_unauthorized_invalid_token(self, client, user_authentication):
        auth = user_authentication.json
        response = client.get(
            _SCAN_URL,
            query_string={"user-id": auth["id"], "token": "invalid-token"},
        )
        assert response.status_code == HTTPStatus.UNAUTHORIZED

    def test_get_no_config_file_returns_empty_list(
        self, client, user_authentication, ut_user_db
    ):
        config_dir = _ensure_config_dir(ut_user_db)
        config_path = os.path.join(config_dir, "config.yaml")
        existed = os.path.exists(config_path)
        if existed:
            os.rename(config_path, config_path + ".bak")
        try:
            auth = user_authentication.json
            response = client.get(_SCAN_URL, query_string=_auth_query(auth))
            assert response.status_code == HTTPStatus.OK
            data = response.get_json()
            assert data["content"] == []
        finally:
            if existed:
                os.rename(config_path + ".bak", config_path)

    def test_get_with_config_returns_log_files(
        self, client, user_authentication, ut_user_db
    ):
        config_dir = _ensure_config_dir(ut_user_db)
        _write_config_file(config_dir)
        log_path = _create_log_file(config_dir, "20250101_000000.log")
        try:
            auth = user_authentication.json
            response = client.get(_SCAN_URL, query_string=_auth_query(auth))
            assert response.status_code == HTTPStatus.OK
            data = response.get_json()
            assert "20250101_000000.log" in data["content"]
        finally:
            if os.path.isfile(log_path):
                os.remove(log_path)

    def test_get_ignores_non_log_files(
        self, client, user_authentication, ut_user_db
    ):
        config_dir = _ensure_config_dir(ut_user_db)
        _write_config_file(config_dir)
        non_log = os.path.join(config_dir, "notes.txt")
        log_path = _create_log_file(config_dir, "20250202_000000.log")
        try:
            with open(non_log, "w") as f:
                f.write("not a log")
            auth = user_authentication.json
            response = client.get(_SCAN_URL, query_string=_auth_query(auth))
            assert response.status_code == HTTPStatus.OK
            data = response.get_json()
            assert "notes.txt" not in data["content"]
            assert "20250202_000000.log" in data["content"]
        finally:
            if os.path.isfile(non_log):
                os.remove(non_log)
            if os.path.isfile(log_path):
                os.remove(log_path)


# ----------------------------------------------------------------
# POST /traceability-scanner/scan
# ----------------------------------------------------------------


class TestTraceabilityScannerScanPost:
    def test_post_missing_fields_returns_bad_request(self, client):
        response = client.post(_SCAN_URL, json={})
        assert response.status_code == HTTPStatus.BAD_REQUEST

    @pytest.mark.parametrize("omit_key", ["user-id", "token"])
    def test_post_missing_single_field_returns_bad_request(
        self, client, user_authentication, omit_key
    ):
        body = _auth_json_body(user_authentication.json)
        del body[omit_key]
        response = client.post(_SCAN_URL, json=body)
        assert response.status_code == HTTPStatus.BAD_REQUEST

    def test_post_unauthorized_invalid_token(self, client, user_authentication):
        auth = user_authentication.json
        response = client.post(
            _SCAN_URL,
            json={"user-id": auth["id"], "token": "invalid-token"},
        )
        assert response.status_code == HTTPStatus.UNAUTHORIZED

    def test_post_no_config_file_returns_bad_request(
        self, client, user_authentication, ut_user_db
    ):
        config_dir = _ensure_config_dir(ut_user_db)
        config_path = os.path.join(config_dir, "config.yaml")
        existed = os.path.exists(config_path)
        if existed:
            os.rename(config_path, config_path + ".bak")
        try:
            auth = user_authentication.json
            response = client.post(_SCAN_URL, json=_auth_json_body(auth))
            assert response.status_code == HTTPStatus.BAD_REQUEST
        finally:
            if existed:
                os.rename(config_path + ".bak", config_path)

    @patch("api.get_user_traceability_scanner_config", return_value=None)
    def test_post_config_unreadable_returns_bad_request(
        self, mock_config, client, user_authentication, ut_user_db
    ):
        config_dir = _ensure_config_dir(ut_user_db)
        _write_config_file(config_dir)
        try:
            auth = user_authentication.json
            response = client.post(_SCAN_URL, json=_auth_json_body(auth))
            assert response.status_code == HTTPStatus.BAD_REQUEST
        finally:
            pass

    @patch("api.subprocess.Popen")
    def test_post_success_returns_created(
        self, mock_popen, client, user_authentication, ut_user_db
    ):
        config_dir = _ensure_config_dir(ut_user_db)
        _write_config_file(config_dir, "api: []\n")
        try:
            auth = user_authentication.json
            response = client.post(_SCAN_URL, json=_auth_json_body(auth))
            assert response.status_code == HTTPStatus.CREATED
            data = response.get_json()
            assert data["status"] == "success"
            assert data["logfile"].endswith(".log")
            mock_popen.assert_called_once()
            call_args = mock_popen.call_args
            cmd = call_args[0][0]
            assert "repos_scanner.py" in cmd
            assert str(ut_user_db.id) in cmd
        finally:
            for f in os.listdir(config_dir):
                if f.endswith(".log"):
                    os.remove(os.path.join(config_dir, f))

    @patch("api.subprocess.Popen")
    def test_post_creates_log_file_on_disk(
        self, mock_popen, client, user_authentication, ut_user_db
    ):
        config_dir = _ensure_config_dir(ut_user_db)
        _write_config_file(config_dir, "api: []\n")
        try:
            auth = user_authentication.json
            response = client.post(_SCAN_URL, json=_auth_json_body(auth))
            assert response.status_code == HTTPStatus.CREATED
            logfile = response.get_json()["logfile"]
            log_path = os.path.join(config_dir, logfile)
            assert os.path.isfile(log_path)
            with open(log_path, "r") as f:
                content = f.read()
            assert "Starting traceability scan" in content
            assert "Configuration:" in content
        finally:
            for f in os.listdir(config_dir):
                if f.endswith(".log"):
                    os.remove(os.path.join(config_dir, f))

    @patch("api.subprocess.Popen")
    def test_post_logfile_name_contains_timestamp_format(
        self, mock_popen, client, user_authentication, ut_user_db
    ):
        config_dir = _ensure_config_dir(ut_user_db)
        _write_config_file(config_dir, "api: []\n")
        try:
            auth = user_authentication.json
            response = client.post(_SCAN_URL, json=_auth_json_body(auth))
            assert response.status_code == HTTPStatus.CREATED
            logfile = response.get_json()["logfile"]
            stem = logfile.removesuffix(".log")
            parts = stem.split("_")
            assert len(parts) == 2
            assert len(parts[0]) == 8  # YYYYMMDD
            assert len(parts[1]) == 6  # HHMMSS
        finally:
            for f in os.listdir(config_dir):
                if f.endswith(".log"):
                    os.remove(os.path.join(config_dir, f))
