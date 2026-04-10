"""HTTP tests for small, high-value routes flagged as uncovered in htmlcov (api/api.py).

These endpoints are cheap to exercise: no heavy fixtures, mostly GET, and they add
direct line coverage for Version, Library, CustomActions, TestingSupportInitDb, and
AIHealthCheck.
"""
import os
from http import HTTPStatus
from pathlib import Path

import pytest

from api import api as api_module

_VERSION_URL = "/version"
_LIBRARIES_URL = "/libraries"
_CUSTOM_ACTIONS_URL = "/custom-actions"
_TEST_SUPPORT_INIT_DB_URL = "/test-support/init-db"
_AI_HEALTH_CHECK_URL = "/ai/health-check"


def _expected_version_from_pyproject():
    pyproject = Path(__file__).resolve().parents[2] / "pyproject.toml"
    for line in pyproject.read_text(encoding="utf-8").splitlines():
        if line.strip().startswith("version = "):
            return line.split("=", 1)[1].strip().strip('"')
    raise AssertionError("version not found in pyproject.toml")


def test_version_get_returns_project_version(client):
    """GET /version — no auth; reads API_VERSION from pyproject at import time."""
    response = client.get(_VERSION_URL)
    assert response.status_code == HTTPStatus.OK
    body = response.get_json()
    assert isinstance(body, dict)
    assert "version" in body
    assert body["version"] == _expected_version_from_pyproject()


def test_libraries_get_returns_sorted_distinct_libraries(client, user_authentication):
    """GET /libraries — distinct library names from ApiModel rows (no permission decorator)."""
    new_api = {
        "user-id": user_authentication.json["id"],
        "token": user_authentication.json["token"],
        "action": "add",
        "api": "test_api_misc_libraries",
        "category": "test_category",
        "library": "test_library_misc",
        "library-version": "1",
        "raw-specification-url": os.path.realpath(__file__),
        "tags": "tag1",
        "implementation-file": "",
        "implementation-file-from-row": 0,
        "implementation-file-to-row": 1,
    }
    post = client.post("/apis", json=new_api)
    assert post.status_code == HTTPStatus.CREATED

    response = client.get(_LIBRARIES_URL)
    assert response.status_code == HTTPStatus.OK
    data = response.get_json()
    assert isinstance(data, list)
    assert "test_library_misc" in data
    assert data == sorted(data)


def test_custom_actions_get_ok(client, user_authentication):
    """GET /custom-actions — requires user-id + token query params."""
    response = client.get(
        _CUSTOM_ACTIONS_URL,
        query_string={
            "user-id": user_authentication.json["id"],
            "token": user_authentication.json["token"],
        },
    )
    assert response.status_code == HTTPStatus.OK
    body = response.get_json()
    assert isinstance(body, dict)


def test_custom_actions_get_unauthorized_without_credentials(client):
    response = client.get(_CUSTOM_ACTIONS_URL)
    assert response.status_code == HTTPStatus.UNAUTHORIZED


@pytest.mark.skipif(
    not api_module.app.config.get("TESTING", False),
    reason="TestingSupportInitDb only re-inits DB when app TESTING is True",
)
def test_testing_support_init_db_get_ok(client):
    """GET /test-support/init-db — only calls init_db when TESTING (see conftest BASIL_TESTING)."""
    response = client.get(_TEST_SUPPORT_INIT_DB_URL)
    assert response.status_code == HTTPStatus.OK
    assert response.get_json() is True


def test_ai_health_check_get(client):
    """GET /ai/health-check — exercises AIPrompter path; outcome depends on admin AI settings."""
    response = client.get(_AI_HEALTH_CHECK_URL)
    assert response.status_code in (
        HTTPStatus.OK,
        HTTPStatus.NOT_FOUND,
        HTTPStatus.PRECONDITION_FAILED,
    )
