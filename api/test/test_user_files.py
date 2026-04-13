"""HTTP tests for UserFiles (/user/files)."""
import os
from http import HTTPStatus

import pytest

from user_files_test_helpers import (
    USER_FILES_URL,
    UT_PREFIX,
    auth_json_body,
    auth_query,
    delete_file,
    get_files,
    post_file,
    remove_if_exists,
    user_files_dir,
)


def test_user_files_get_unauthorized_without_credentials(client):
    response = client.get(USER_FILES_URL)
    assert response.status_code == HTTPStatus.UNAUTHORIZED


def test_user_files_get_unauthorized_invalid_token(client, user_authentication):
    auth = user_authentication.json
    response = client.get(
        USER_FILES_URL,
        query_string={"user-id": auth["id"], "token": "invalid-token"},
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED


@pytest.mark.parametrize("omit_key", ["user-id", "token"])
def test_user_files_get_unauthorized_missing_auth_query_keys(
    client, user_authentication, omit_key
):
    qs = auth_query(user_authentication.json)
    del qs[omit_key]
    response = client.get(USER_FILES_URL, query_string=qs)
    assert response.status_code == HTTPStatus.UNAUTHORIZED


def test_user_files_get_ok_empty_directory(client, user_authentication, ut_user_files_dir):
    """New or empty user folder returns an empty list."""
    auth = user_authentication.json
    for name in os.listdir(ut_user_files_dir):
        if not name.startswith("."):
            remove_if_exists(os.path.join(ut_user_files_dir, name))

    response = get_files(client, auth)
    assert response.status_code == HTTPStatus.OK
    assert response.get_json() == []


def test_user_files_get_lists_non_hidden_files_sorted(
    client, user_authentication, ut_user_files_dir, utilities
):
    auth = user_authentication.json
    suffix = utilities.generate_random_hex_string8()
    a_name = f"{UT_PREFIX}a_{suffix}.txt"
    b_name = f"{UT_PREFIX}b_{suffix}.txt"
    a_path = os.path.join(ut_user_files_dir, a_name)
    b_path = os.path.join(ut_user_files_dir, b_name)
    hidden_path = os.path.join(ut_user_files_dir, f".hidden_{suffix}")

    try:
        with open(a_path, "w", encoding="utf-8") as f:
            f.write("a")
        with open(b_path, "w", encoding="utf-8") as f:
            f.write("b")
        with open(hidden_path, "w", encoding="utf-8") as f:
            f.write("h")

        response = get_files(client, auth)
        assert response.status_code == HTTPStatus.OK
        rows = response.get_json()
        names = [os.path.basename(r["filepath"]) for r in rows]
        assert a_name in names and b_name in names
        assert f".hidden_{suffix}" not in names
        assert names == sorted(names)
    finally:
        remove_if_exists(a_path)
        remove_if_exists(b_path)
        remove_if_exists(hidden_path)


def test_user_files_get_filter_query(client, user_authentication, ut_user_files_dir, utilities):
    auth = user_authentication.json
    suffix = utilities.generate_random_hex_string8()
    match_name = f"{UT_PREFIX}match_alpha_{suffix}.txt"
    other_name = f"{UT_PREFIX}other_beta_{suffix}.txt"
    m_path = os.path.join(ut_user_files_dir, match_name)
    o_path = os.path.join(ut_user_files_dir, other_name)

    try:
        with open(m_path, "w", encoding="utf-8") as f:
            f.write("x")
        with open(o_path, "w", encoding="utf-8") as f:
            f.write("y")

        response = get_files(client, auth, extra_query={"filter": "alpha"})
        assert response.status_code == HTTPStatus.OK
        names = [os.path.basename(r["filepath"]) for r in response.get_json()]
        assert match_name in names
        assert other_name not in names
    finally:
        remove_if_exists(m_path)
        remove_if_exists(o_path)


@pytest.mark.parametrize("mandatory_field", ["filename", "filecontent"])
def test_user_files_post_missing_mandatory_fields(client, user_authentication, mandatory_field):
    auth = user_authentication.json
    body = {
        **auth_json_body(auth),
        "filename": f"{UT_PREFIX}x.txt",
        "filecontent": "body",
    }
    del body[mandatory_field]
    response = client.post(USER_FILES_URL, json=body)
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_user_files_post_unauthorized(client, user_authentication):
    auth = user_authentication.json
    response = client.post(
        USER_FILES_URL,
        json={
            **auth_json_body(auth),
            "filename": f"{UT_PREFIX}n.txt",
            "filecontent": "c",
            "token": "wrong-token",
        },
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED


def test_user_files_post_rejects_leading_dot_filename(client, user_authentication):
    auth = user_authentication.json
    response = post_file(client, auth, ".secret", "x")
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_user_files_post_rejects_empty_filename_or_content(client, user_authentication):
    auth = user_authentication.json
    r1 = post_file(client, auth, "", "content")
    assert r1.status_code == HTTPStatus.BAD_REQUEST
    r2 = post_file(client, auth, f"{UT_PREFIX}empty.txt", "")
    assert r2.status_code == HTTPStatus.BAD_REQUEST


def test_user_files_post_conflict_when_file_exists(
    client, user_authentication, ut_user_files_dir, utilities
):
    auth = user_authentication.json
    name = f"{UT_PREFIX}dup_{utilities.generate_random_hex_string8()}.txt"
    path = os.path.join(ut_user_files_dir, name)
    try:
        first = post_file(client, auth, name, "one")
        assert first.status_code == HTTPStatus.CREATED
        second = post_file(client, auth, name, "two")
        assert second.status_code == HTTPStatus.CONFLICT
    finally:
        remove_if_exists(path)


def test_user_files_post_created(client, user_authentication, utilities):
    auth = user_authentication.json
    name = f"{UT_PREFIX}new_{utilities.generate_random_hex_string8()}.txt"
    path = user_files_dir(auth["id"])
    fpath = os.path.join(path, name)
    try:
        response = post_file(client, auth, name, "hello")
        assert response.status_code == HTTPStatus.CREATED
        data = response.get_json()
        assert data["filepath"] == fpath
        assert "updated_at" in data
        assert os.path.isfile(fpath)
        with open(fpath, encoding="utf-8") as f:
            assert f.read() == "hello"
    finally:
        remove_if_exists(fpath)


@pytest.mark.parametrize("mandatory_field", ["filename"])
def test_user_files_delete_missing_mandatory_fields(client, user_authentication, mandatory_field):
    auth = user_authentication.json
    body = {**auth_json_body(auth), "filename": f"{UT_PREFIX}x.txt"}
    del body[mandatory_field]
    response = client.delete(USER_FILES_URL, json=body)
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_user_files_delete_unauthorized(client, user_authentication):
    auth = user_authentication.json
    response = client.delete(
        USER_FILES_URL,
        json={"user-id": auth["id"], "token": "bad", "filename": f"{UT_PREFIX}x.txt"},
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED


def test_user_files_delete_not_found_when_missing_file(
    client, user_authentication, utilities
):
    auth = user_authentication.json
    name = f"{UT_PREFIX}missing_{utilities.generate_random_hex_string8()}.txt"
    response = delete_file(client, auth, name)
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_user_files_delete_ok(client, user_authentication, utilities):
    auth = user_authentication.json
    name = f"{UT_PREFIX}del_{utilities.generate_random_hex_string8()}.txt"
    path = os.path.join(user_files_dir(auth["id"]), name)
    try:
        created = post_file(client, auth, name, "to-delete")
        assert created.status_code == HTTPStatus.CREATED
        resp = delete_file(client, auth, name)
        assert resp.status_code == HTTPStatus.OK
        body = resp.get_json()
        assert body["filepath"] == path
        assert not os.path.exists(path)
    finally:
        remove_if_exists(path)
