"""HTTP tests for TestCaseImport (/import/test-cases)."""
import json
import os
from http import HTTPStatus

import pytest

from user_files_test_helpers import (
    auth_json_body,
    remove_if_exists,
    remove_user_files_dir_if_exists,
)

_IMPORT_TEST_CASES_URL = "/import/test-cases"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _auth_body(auth_json, **extra):
    return {**auth_json_body(auth_json), **extra}


def _post_import(client, auth_json, file_name):
    body = _auth_body(auth_json, file_name=file_name)
    return client.post(_IMPORT_TEST_CASES_URL, json=body)


def _put_import(client, auth_json, items, **extra):
    body = _auth_body(auth_json, items=items, **extra)
    return client.put(_IMPORT_TEST_CASES_URL, json=body)


def _make_valid_tc_json(repository="https://github.com/example/repo",
                        test_cases=None):
    if test_cases is None:
        test_cases = [
            {
                "id": 1,
                "name": "tests/test_example.py",
                "summary": "Example test case",
                "description": "A test case used for unit testing",
            },
            {
                "name": "tests/test_another.py",
                "summary": "Another test case",
                "description": "Second test case for UT",
            },
        ]
    return {"repository": repository, "test_cases": test_cases}


def _write_json_user_file(ut_user_files_dir, filename, data):
    """Write a JSON structure into a file inside the user-files directory."""
    path = os.path.join(ut_user_files_dir, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f)
    return path


# ===================================================================
# POST /import/test-cases  — parse a JSON file from user-files
# ===================================================================


class TestPostMissingFields:
    """POST must reject requests with missing mandatory fields."""

    @pytest.mark.parametrize("omit_field", ["file_name", "user-id", "token"])
    def test_missing_mandatory_field(self, client, user_authentication, omit_field):
        auth = user_authentication.json
        body = _auth_body(auth, file_name="some_file.json")
        del body[omit_field]
        response = client.post(_IMPORT_TEST_CASES_URL, json=body)
        assert response.status_code == HTTPStatus.BAD_REQUEST


class TestPostAuth:
    """POST must reject unauthorized requests."""

    def test_unauthorized_invalid_token(self, client, user_authentication):
        auth = user_authentication.json
        body = _auth_body(auth, file_name="f.json")
        body["token"] = "invalid-token"
        response = client.post(_IMPORT_TEST_CASES_URL, json=body)
        assert response.status_code == HTTPStatus.UNAUTHORIZED


class TestPostUserDirNotFound:
    """POST returns 404 when the user-files directory does not exist."""

    def test_user_dir_not_found(self, client, user_authentication, ut_user_db):
        remove_user_files_dir_if_exists(ut_user_db.id)
        auth = user_authentication.json
        response = _post_import(client, auth, "nonexistent.json")
        assert response.status_code == HTTPStatus.NOT_FOUND


class TestPostFileNotFound:
    """POST returns 404 when the requested file does not exist in user-files."""

    def test_file_not_found(self, client, user_authentication, ut_user_files_dir, utilities):
        auth = user_authentication.json
        name = f"ut_tc_import_missing_{utilities.generate_random_hex_string8()}.json"
        response = _post_import(client, auth, name)
        assert response.status_code == HTTPStatus.NOT_FOUND


class TestPostInvalidJson:
    """POST returns 400 when the file is not valid JSON."""

    def test_invalid_json(self, client, user_authentication, ut_user_files_dir, utilities):
        auth = user_authentication.json
        name = f"ut_tc_import_bad_{utilities.generate_random_hex_string8()}.json"
        path = os.path.join(ut_user_files_dir, name)
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write("not-json-{{{")
            response = _post_import(client, auth, name)
            assert response.status_code == HTTPStatus.BAD_REQUEST
        finally:
            remove_if_exists(path)


class TestPostMissingJsonFields:
    """POST returns 412 when top-level mandatory JSON fields are absent."""

    @pytest.mark.parametrize("missing_key", ["repository", "test_cases"])
    def test_missing_json_mandatory_field(
        self, client, user_authentication, ut_user_files_dir, utilities, missing_key
    ):
        auth = user_authentication.json
        name = f"ut_tc_import_mf_{utilities.generate_random_hex_string8()}.json"
        data = _make_valid_tc_json()
        del data[missing_key]
        path = _write_json_user_file(ut_user_files_dir, name, data)
        try:
            response = _post_import(client, auth, name)
            assert response.status_code == HTTPStatus.PRECONDITION_FAILED
        finally:
            remove_if_exists(path)


class TestPostSuccess:
    """POST parses a valid JSON file and returns test cases."""

    def test_valid_file_returns_test_cases(
        self, client, user_authentication, ut_user_files_dir, utilities
    ):
        auth = user_authentication.json
        name = f"ut_tc_import_ok_{utilities.generate_random_hex_string8()}.json"
        tc_data = _make_valid_tc_json()
        path = _write_json_user_file(ut_user_files_dir, name, tc_data)
        try:
            response = _post_import(client, auth, name)
            assert response.status_code == HTTPStatus.CREATED
            payload = response.get_json()
            tcs = payload["test_cases"]
            assert len(tcs) == 2

            assert tcs[0]["id"] == 1
            assert tcs[0]["repository"] == tc_data["repository"]
            assert tcs[0]["relative_path"] == "tests/test_example.py"
            assert tcs[0]["title"] == "Example test case"
            assert tcs[0]["description"] == "A test case used for unit testing"

            assert tcs[1]["id"] == 1
            assert tcs[1]["repository"] == tc_data["repository"]
            assert tcs[1]["relative_path"] == "tests/test_another.py"
            assert tcs[1]["title"] == "Another test case"
        finally:
            remove_if_exists(path)

    def test_test_cases_without_mandatory_content_are_skipped(
        self, client, user_authentication, ut_user_files_dir, utilities
    ):
        """Test cases missing description/name/summary are silently dropped."""
        auth = user_authentication.json
        name = f"ut_tc_import_skip_{utilities.generate_random_hex_string8()}.json"
        tc_data = _make_valid_tc_json(
            test_cases=[
                {"name": "tests/ok.py", "summary": "ok", "description": "ok"},
                {"name": "tests/bad.py", "summary": "missing description field"},
                {"summary": "missing name", "description": "desc"},
                {"name": "n", "description": "missing summary"},
            ]
        )
        path = _write_json_user_file(ut_user_files_dir, name, tc_data)
        try:
            response = _post_import(client, auth, name)
            assert response.status_code == HTTPStatus.CREATED
            tcs = response.get_json()["test_cases"]
            assert len(tcs) == 1
            assert tcs[0]["relative_path"] == "tests/ok.py"
        finally:
            remove_if_exists(path)

    def test_id_defaults_to_index_when_absent(
        self, client, user_authentication, ut_user_files_dir, utilities
    ):
        auth = user_authentication.json
        name = f"ut_tc_import_idx_{utilities.generate_random_hex_string8()}.json"
        tc_data = _make_valid_tc_json(
            test_cases=[
                {"name": "a.py", "summary": "A", "description": "a"},
                {"name": "b.py", "summary": "B", "description": "b"},
            ]
        )
        path = _write_json_user_file(ut_user_files_dir, name, tc_data)
        try:
            response = _post_import(client, auth, name)
            assert response.status_code == HTTPStatus.CREATED
            tcs = response.get_json()["test_cases"]
            assert tcs[0]["id"] == 0
            assert tcs[1]["id"] == 1
        finally:
            remove_if_exists(path)

    def test_id_from_json_is_preserved(
        self, client, user_authentication, ut_user_files_dir, utilities
    ):
        auth = user_authentication.json
        name = f"ut_tc_import_cid_{utilities.generate_random_hex_string8()}.json"
        tc_data = _make_valid_tc_json(
            test_cases=[
                {"id": 42, "name": "c.py", "summary": "C", "description": "c"},
            ]
        )
        path = _write_json_user_file(ut_user_files_dir, name, tc_data)
        try:
            response = _post_import(client, auth, name)
            assert response.status_code == HTTPStatus.CREATED
            tcs = response.get_json()["test_cases"]
            assert tcs[0]["id"] == 42
        finally:
            remove_if_exists(path)

    def test_empty_test_cases_array(
        self, client, user_authentication, ut_user_files_dir, utilities
    ):
        auth = user_authentication.json
        name = f"ut_tc_import_empty_{utilities.generate_random_hex_string8()}.json"
        tc_data = _make_valid_tc_json(test_cases=[])
        path = _write_json_user_file(ut_user_files_dir, name, tc_data)
        try:
            response = _post_import(client, auth, name)
            assert response.status_code == HTTPStatus.CREATED
            assert response.get_json()["test_cases"] == []
        finally:
            remove_if_exists(path)


# ===================================================================
# PUT /import/test-cases  — persist selected test cases into the DB
# ===================================================================


class TestPutMissingFields:
    """PUT must reject requests with missing mandatory fields."""

    def test_missing_items_field(self, client, user_authentication):
        auth = user_authentication.json
        body = _auth_body(auth)
        response = client.put(_IMPORT_TEST_CASES_URL, json=body)
        assert response.status_code == HTTPStatus.BAD_REQUEST


class TestPutAuth:
    """PUT must reject unauthorized / un-authenticated requests."""

    def test_unauthorized_invalid_token(self, client, user_authentication):
        auth = user_authentication.json
        body = _auth_body(auth, items=[])
        body["token"] = "invalid-token"
        response = client.put(_IMPORT_TEST_CASES_URL, json=body)
        assert response.status_code == HTTPStatus.UNAUTHORIZED

    def test_unauthorized_missing_credentials(self, client):
        body = {"items": []}
        response = client.put(_IMPORT_TEST_CASES_URL, json=body)
        assert response.status_code == HTTPStatus.UNAUTHORIZED


class TestPutSuccess:
    """PUT creates test cases in the database."""

    def test_creates_test_cases(self, client, user_authentication):
        auth = user_authentication.json
        items = [
            {
                "repository": "https://github.com/example/repo",
                "relative_path": "tests/test_a.py",
                "title": "TC A",
                "description": "Description A",
            },
            {
                "repository": "https://github.com/example/repo",
                "relative_path": "tests/test_b.py",
                "title": "TC B",
                "description": "Description B",
            },
        ]
        response = _put_import(client, auth, items)
        assert response.status_code == HTTPStatus.OK
        tcs = response.get_json()["test_cases"]
        assert len(tcs) == 2
        assert tcs[0]["repository"] == items[0]["repository"]
        assert tcs[0]["relative_path"] == items[0]["relative_path"]
        assert tcs[0]["title"] == items[0]["title"]
        assert tcs[0]["description"] == items[0]["description"]
        assert tcs[1]["title"] == items[1]["title"]

    def test_skips_items_missing_mandatory_keys(self, client, user_authentication):
        auth = user_authentication.json
        items = [
            {
                "repository": "https://github.com/example/repo",
                "relative_path": "tests/good.py",
                "title": "Good",
                "description": "Valid item",
            },
            {"repository": "https://github.com/example/repo", "title": "Bad"},
            {"relative_path": "tests/bad.py", "description": "Missing repo and title"},
        ]
        response = _put_import(client, auth, items)
        assert response.status_code == HTTPStatus.OK
        tcs = response.get_json()["test_cases"]
        assert len(tcs) == 1
        assert tcs[0]["title"] == "Good"

    def test_empty_items_returns_empty_list(self, client, user_authentication):
        auth = user_authentication.json
        response = _put_import(client, auth, items=[])
        assert response.status_code == HTTPStatus.OK
        assert response.get_json()["test_cases"] == []
