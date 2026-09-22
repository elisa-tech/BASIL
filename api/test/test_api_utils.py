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
    fuzzy_path_match,
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


# ---------------------------------------------------------------------------
# fuzzy_path_match – used to search the user files
# ---------------------------------------------------------------------------

def score_of(query, text):
    match = fuzzy_path_match(query, text)
    assert match is not None, f"{query!r} should match {text!r}"
    return match[0]


@pytest.mark.parametrize(
    "query, text, expected_indices",
    [
        # a literal substring is matched where it appears
        ("req", "specs/requirements.yaml", [6, 7, 8]),
        # the query can match a folder name, not only the entry name
        ("specs", "specs/requirements.yaml", [0, 1, 2, 3, 4]),
        # the whole relative path is searched, so folder and name can both hit
        ("specsreq", "specs/requirements.yaml", [0, 1, 2, 3, 4, 6, 7, 8]),
        # scattered characters match as long as they keep their order; the
        # match is tightened to the right, so the "s" lands on the last one of
        # "specs" rather than the first
        ("srq", "specs/requirements.yaml", [4, 6, 8]),
        # matching is case insensitive both ways
        ("REQ", "specs/requirements.yaml", [6, 7, 8]),
        ("req", "specs/REQUIREMENTS.yaml", [6, 7, 8]),
    ],
)
def test_fuzzy_path_match_indices(query, text, expected_indices):
    match = fuzzy_path_match(query, text)
    assert match is not None
    assert match[1] == expected_indices


@pytest.mark.parametrize(
    "query, text",
    [
        ("zzz", "specs/requirements.yaml"),
        ("qer", "specs/requirements.yaml"),  # right characters, wrong order
        ("requirementss", "specs/requirements.yaml"),
        ("", "specs/requirements.yaml"),
    ],
)
def test_fuzzy_path_match_returns_none_when_it_does_not_match(query, text):
    assert fuzzy_path_match(query, text) is None


def test_fuzzy_path_match_groups_the_matched_characters():
    """The match is tightened so the highlighted characters sit together: "kreq"
    must land on the "k" of kernel plus "req" of requirements, not on four
    characters spread over "kernel"."""
    match = fuzzy_path_match("kreq", "specs/kernel/requirements.yaml")
    assert match is not None
    assert match[1] == [6, 13, 14, 15]


def test_fuzzy_path_match_ranks_a_literal_match_above_a_scattered_one():
    assert score_of("req", "specs/requirements.yaml") > score_of("req", "specs/rocket/equipment.yaml")


def test_fuzzy_path_match_ranks_the_entry_name_above_its_folders():
    assert score_of("report", "docs/report.md") > score_of("report", "report/docs.md")


def test_fuzzy_path_match_ranks_a_word_start_above_a_match_inside_a_word():
    assert score_of("test", "docs/test_plan.md") > score_of("test", "docs/latest_plan.md")
