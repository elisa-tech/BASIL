"""HTTP tests for UserFileContent (/user/files/content)."""
import os
from http import HTTPStatus

import pytest

from user_files_test_helpers import (
    USER_FILE_CONTENT_URL,
    UT_PREFIX,
    auth_json_body,
    auth_query,
    get_content,
    post_file,
    put_content,
    remove_if_exists,
    remove_user_files_dir_if_exists,
    user_files_dir,
)


def test_user_file_content_get_bad_request_without_filename(client, user_authentication):
    """Mandatory filename is validated before auth; missing filename yields 400."""
    assert client.get(USER_FILE_CONTENT_URL).status_code == HTTPStatus.BAD_REQUEST
    auth = user_authentication.json
    assert client.get(
        USER_FILE_CONTENT_URL, query_string=auth_query(auth)
    ).status_code == HTTPStatus.BAD_REQUEST


def test_user_file_content_get_unauthorized_invalid_token(client, user_authentication):
    auth = user_authentication.json
    response = client.get(
        USER_FILE_CONTENT_URL,
        query_string={"user-id": auth["id"], "token": "invalid-token", "filename": f"{UT_PREFIX}x.txt"},
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED


@pytest.mark.parametrize("omit_key", ["user-id", "token"])
def test_user_file_content_get_unauthorized_missing_auth_query_keys(
    client, user_authentication, omit_key
):
    qs = {**auth_query(user_authentication.json), "filename": f"{UT_PREFIX}a.txt"}
    del qs[omit_key]
    response = client.get(USER_FILE_CONTENT_URL, query_string=qs)
    assert response.status_code == HTTPStatus.UNAUTHORIZED


def test_user_file_content_get_not_found_when_user_dir_missing(client, user_authentication, ut_user_db):
    """API creates the user folder but returns 404 when the requested file does not exist."""
    remove_user_files_dir_if_exists(ut_user_db.id)
    auth = user_authentication.json
    name = f"{UT_PREFIX}nodir_{auth['id']}.txt"
    response = get_content(client, auth, name)
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_user_file_content_get_not_found(client, user_authentication, utilities):
    auth = user_authentication.json
    name = f"{UT_PREFIX}nocontent_{utilities.generate_random_hex_string8()}.txt"
    response = get_content(client, auth, name)
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_user_file_content_get_not_found_when_file_empty(client, user_authentication, utilities, ut_user_files_dir):
    """Empty file content is falsy in the handler and is treated as not found."""
    auth = user_authentication.json
    name = f"{UT_PREFIX}empty_{utilities.generate_random_hex_string8()}.txt"
    path = os.path.join(ut_user_files_dir, name)
    try:
        with open(path, "w", encoding="utf-8"):
            pass
        response = get_content(client, auth, name)
        assert response.status_code == HTTPStatus.NOT_FOUND
    finally:
        remove_if_exists(path)


def test_user_file_content_get_ok(client, user_authentication, utilities):
    auth = user_authentication.json
    name = f"{UT_PREFIX}read_{utilities.generate_random_hex_string8()}.txt"
    content = "file-content-line"
    path = os.path.join(user_files_dir(auth["id"]), name)
    try:
        posted = post_file(client, auth, name, content)
        assert posted.status_code == HTTPStatus.CREATED
        response = get_content(client, auth, name)
        assert response.status_code == HTTPStatus.OK
        data = response.get_json()
        assert data["filecontent"] == content
        assert data["filepath"] == path
        assert "updated_at" in data
    finally:
        remove_if_exists(path)


def test_user_file_content_get_nested_file(client, user_authentication, utilities):
    """Content of a file in a nested folder should be accessible via relative path."""
    auth = user_authentication.json
    suffix = utilities.generate_random_hex_string8()
    nested = f"{UT_PREFIX}cnt_{suffix}/sub/deep.txt"
    base = user_files_dir(auth["id"])
    top_dir = os.path.join(base, f"{UT_PREFIX}cnt_{suffix}")

    try:
        post_file(client, auth, nested, "deep content")
        response = get_content(client, auth, nested)
        assert response.status_code == HTTPStatus.OK
        assert response.get_json()["filecontent"] == "deep content"
    finally:
        remove_if_exists(top_dir)


def test_user_file_content_get_path_traversal_blocked(client, user_authentication):
    auth = user_authentication.json
    response = get_content(client, auth, "../../etc/passwd")
    assert response.status_code == HTTPStatus.BAD_REQUEST


# ---------------------------------------------------------------------------
# PUT /user/files/content
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("mandatory_field", ["filename", "filecontent"])
def test_user_file_content_put_missing_mandatory_fields(client, user_authentication, mandatory_field):
    auth = user_authentication.json
    body = {
        **auth_json_body(auth),
        "filename": f"{UT_PREFIX}p.txt",
        "filecontent": "z",
    }
    del body[mandatory_field]
    response = client.put(USER_FILE_CONTENT_URL, json=body)
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_user_file_content_put_unauthorized(client, user_authentication):
    auth = user_authentication.json
    response = client.put(
        USER_FILE_CONTENT_URL,
        json={
            **auth_json_body(auth),
            "filename": f"{UT_PREFIX}p.txt",
            "filecontent": "z",
            "token": "invalid",
        },
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED


def test_user_file_content_put_not_found_when_user_dir_missing(client, user_authentication, ut_user_db, utilities):
    remove_user_files_dir_if_exists(ut_user_db.id)
    auth = user_authentication.json
    name = f"{UT_PREFIX}put_nodir_{utilities.generate_random_hex_string8()}.txt"
    response = put_content(client, auth, name, "new")
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_user_file_content_put_not_found_when_file_missing(client, user_authentication, utilities):
    auth = user_authentication.json
    name = f"{UT_PREFIX}noput_{utilities.generate_random_hex_string8()}.txt"
    response = put_content(client, auth, name, "new")
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_user_file_content_put_bad_request_empty_filename_or_content(
    client, user_authentication, utilities
):
    auth = user_authentication.json
    name = f"{UT_PREFIX}putbad_{utilities.generate_random_hex_string8()}.txt"
    path = os.path.join(user_files_dir(auth["id"]), name)
    try:
        assert post_file(client, auth, name, "seed").status_code == HTTPStatus.CREATED
        r1 = put_content(client, auth, "", "x")
        assert r1.status_code == HTTPStatus.BAD_REQUEST
        r2 = put_content(client, auth, name, "")
        assert r2.status_code == HTTPStatus.BAD_REQUEST
    finally:
        remove_if_exists(path)


def test_user_file_content_put_updates_content(client, user_authentication, utilities):
    auth = user_authentication.json
    name = f"{UT_PREFIX}put_{utilities.generate_random_hex_string8()}.txt"
    path = os.path.join(user_files_dir(auth["id"]), name)
    try:
        assert post_file(client, auth, name, "original").status_code == HTTPStatus.CREATED
        response = put_content(client, auth, name, "updated")
        assert response.status_code == HTTPStatus.OK
        data = response.get_json()
        assert data["filecontent"] == "updated"
        assert data["filepath"] == path
        assert "updated_at" in data
        with open(path, encoding="utf-8") as f:
            assert f.read() == "updated"
    finally:
        remove_if_exists(path)


def test_user_file_content_put_nested_file(client, user_authentication, utilities):
    """PUT should work for files in nested directories."""
    auth = user_authentication.json
    suffix = utilities.generate_random_hex_string8()
    nested = f"{UT_PREFIX}putcnt_{suffix}/sub/deep.txt"
    base = user_files_dir(auth["id"])
    top_dir = os.path.join(base, f"{UT_PREFIX}putcnt_{suffix}")

    try:
        post_file(client, auth, nested, "original")
        response = put_content(client, auth, nested, "updated-deep")
        assert response.status_code == HTTPStatus.OK
        assert response.get_json()["filecontent"] == "updated-deep"
    finally:
        remove_if_exists(top_dir)


def test_user_file_content_put_path_traversal_blocked(client, user_authentication, utilities):
    auth = user_authentication.json
    suffix = utilities.generate_random_hex_string8()
    name = f"{UT_PREFIX}tr_{suffix}.txt"
    base = user_files_dir(auth["id"])

    try:
        post_file(client, auth, name, "x")
        response = put_content(client, auth, f"../../{name}", "hacked")
        assert response.status_code == HTTPStatus.BAD_REQUEST
    finally:
        remove_if_exists(os.path.join(base, name))
