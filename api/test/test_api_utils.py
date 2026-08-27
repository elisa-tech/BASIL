import os
import pytest
import sys
from db.models.user import UserModel

_ADMIN_SETTINGS_URL = "/admin/settings"

# Admin user constants
UT_ADMIN_USER_NAME = "admin-username"
UT_ADMIN_USER_EMAIL = "admin-email"
UT_ADMIN_USER_PASSWORD = "admin_dummy_password"
UT_ADMIN_USER_ROLE = "ADMIN"

currentdir = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(1, os.path.dirname(currentdir))

from api_utils import (
    LINK_BASIL_INSTANCE_HTML_MESSAGE,
    add_html_link_to_email_body,
    combine_tmt_path,
    load_settings
)


@pytest.fixture(scope="module")
def ut_admin_user_db(client_db):
    """Create an admin user for testing"""
    dbi = client_db

    # Create admin user
    ut_admin_user = UserModel(UT_ADMIN_USER_NAME, UT_ADMIN_USER_EMAIL, UT_ADMIN_USER_PASSWORD, UT_ADMIN_USER_ROLE)
    dbi.session.add(ut_admin_user)
    dbi.session.commit()

    yield ut_admin_user


@pytest.fixture(scope="module")
def admin_authentication(client, ut_admin_user_db):
    """Authenticate as admin user"""
    authentication = client.post(
        "/user/login", json={"email": UT_ADMIN_USER_EMAIL, "password": UT_ADMIN_USER_PASSWORD}
    )
    return authentication


def update_settings(client, admin_authentication, settings_content):
    """Update settings"""
    response = client.put(
        _ADMIN_SETTINGS_URL,
        json={
            "user-id": admin_authentication.json["id"],
            "token": admin_authentication.json["token"],
            "content": settings_content,
        },
    )
    assert response.status_code == 200
    return response


def test_add_html_link_to_email_body(client, admin_authentication):
    settings_content = "dummy: value"
    update_settings(client, admin_authentication, settings_content)
    initial_body = None
    settings, settings_last_modified = load_settings(None, None)
    body = add_html_link_to_email_body(settings=settings, body=initial_body)
    assert body == ""
    assert LINK_BASIL_INSTANCE_HTML_MESSAGE not in body

    settings_content = "dummy: value"
    update_settings(client, admin_authentication, settings_content)
    initial_body = ""
    settings, settings_last_modified = load_settings(None, None)
    body = add_html_link_to_email_body(settings=settings, body=initial_body)
    assert body == ""
    assert LINK_BASIL_INSTANCE_HTML_MESSAGE not in body

    settings_content = """
app_url: "https://www.google.com"
"""
    update_settings(client, admin_authentication, settings_content)
    settings, settings_last_modified = load_settings(None, None)
    initial_body = "Hello, world!"
    body = add_html_link_to_email_body(settings=settings, body=initial_body)
    assert body != ""
    assert LINK_BASIL_INSTANCE_HTML_MESSAGE in body


@pytest.mark.parametrize(
    "repository, relative_path, expected",
    [
        (
            "/BASIL-API",
            "/api/user-files/2/tmt/tmt-dummy-test",
            "/BASIL-API/api/user-files/2/tmt/tmt-dummy-test",
        ),
        (
            "/BASIL-API",
            "api/user-files/2/tmt/tmt-dummy-test",
            "/BASIL-API/api/user-files/2/tmt/tmt-dummy-test",
        ),
        (
            "/opt/basil",
            "examples/tmt/local/tmt-dummy-test.fmf",
            "/opt/basil/examples/tmt/local/tmt-dummy-test.fmf",
        ),
        ("/repo", "", "/repo"),
        ("", "tests/foo.fmf", "tests/foo.fmf"),
        ("/repo/", "/nested/test", "/repo/nested/test"),
        (None, "/api/user-files/2/test", "api/user-files/2/test"),
    ],
)
def test_combine_tmt_path(repository, relative_path, expected):
    assert combine_tmt_path(repository, relative_path) == expected


def test_combine_tmt_path_does_not_drop_repository_when_relative_is_absolute():
    """os.path.join discards repository when relative_path is absolute; combine_tmt_path must not."""
    repository = "/BASIL-API"
    relative_path = "/api/user-files/2/tmt/tmt-dummy-test"
    assert os.path.join(repository, relative_path) == relative_path
    assert combine_tmt_path(repository, relative_path) == (
        "/BASIL-API/api/user-files/2/tmt/tmt-dummy-test"
    )
