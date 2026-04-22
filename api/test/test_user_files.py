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
    move_file,
    post_file,
    remove_if_exists,
    user_files_dir,
)


# ---------------------------------------------------------------------------
# GET /user/files – auth
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# GET /user/files – listing
# ---------------------------------------------------------------------------

def test_user_files_get_ok_empty_directory(client, user_authentication, ut_user_files_dir):
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
        names = [r["name"] for r in rows]
        assert a_name in names and b_name in names
        assert f".hidden_{suffix}" not in names
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
        names = [r["name"] for r in response.get_json()]
        assert match_name in names
        assert other_name not in names
    finally:
        remove_if_exists(m_path)
        remove_if_exists(o_path)


def test_user_files_get_returns_type_field(client, user_authentication, ut_user_files_dir, utilities):
    auth = user_authentication.json
    suffix = utilities.generate_random_hex_string8()
    file_name = f"{UT_PREFIX}typed_{suffix}.txt"
    dir_name = f"{UT_PREFIX}dir_{suffix}"
    f_path = os.path.join(ut_user_files_dir, file_name)
    d_path = os.path.join(ut_user_files_dir, dir_name)

    try:
        with open(f_path, "w", encoding="utf-8") as f:
            f.write("c")
        os.makedirs(d_path, exist_ok=True)

        response = get_files(client, auth)
        assert response.status_code == HTTPStatus.OK
        rows = response.get_json()
        types = {r["name"]: r["type"] for r in rows}
        assert types.get(file_name) == "file"
        assert types.get(dir_name) == "directory"
    finally:
        remove_if_exists(f_path)
        remove_if_exists(d_path)


def test_user_files_get_directories_sorted_first(client, user_authentication, ut_user_files_dir, utilities):
    auth = user_authentication.json
    suffix = utilities.generate_random_hex_string8()
    file_name = f"{UT_PREFIX}aaa_{suffix}.txt"
    dir_name = f"{UT_PREFIX}zzz_dir_{suffix}"
    f_path = os.path.join(ut_user_files_dir, file_name)
    d_path = os.path.join(ut_user_files_dir, dir_name)

    try:
        with open(f_path, "w", encoding="utf-8") as f:
            f.write("c")
        os.makedirs(d_path, exist_ok=True)

        response = get_files(client, auth)
        assert response.status_code == HTTPStatus.OK
        rows = response.get_json()
        relevant = [r for r in rows if r["name"] in (file_name, dir_name)]
        assert len(relevant) == 2
        assert relevant[0]["type"] == "directory"
        assert relevant[1]["type"] == "file"
    finally:
        remove_if_exists(f_path)
        remove_if_exists(d_path)


# ---------------------------------------------------------------------------
# GET /user/files – nested path param
# ---------------------------------------------------------------------------

def test_user_files_get_with_path_param(client, user_authentication, ut_user_files_dir, utilities):
    auth = user_authentication.json
    suffix = utilities.generate_random_hex_string8()
    sub_dir = f"{UT_PREFIX}sub_{suffix}"
    sub_path = os.path.join(ut_user_files_dir, sub_dir)
    file_name = f"nested_{suffix}.txt"
    file_path = os.path.join(sub_path, file_name)

    try:
        os.makedirs(sub_path, exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("nested content")

        response = get_files(client, auth, extra_query={"path": sub_dir})
        assert response.status_code == HTTPStatus.OK
        rows = response.get_json()
        names = [r["name"] for r in rows]
        assert file_name in names
    finally:
        remove_if_exists(sub_path)


def test_user_files_get_path_not_found(client, user_authentication, utilities):
    auth = user_authentication.json
    response = get_files(client, auth, extra_query={"path": f"nonexistent_{utilities.generate_random_hex_string8()}"})
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_user_files_get_path_traversal_blocked(client, user_authentication):
    auth = user_authentication.json
    response = get_files(client, auth, extra_query={"path": "../"})
    assert response.status_code == HTTPStatus.BAD_REQUEST


# ---------------------------------------------------------------------------
# GET /user/files – recursive
# ---------------------------------------------------------------------------

def test_user_files_get_recursive(client, user_authentication, ut_user_files_dir, utilities):
    auth = user_authentication.json
    suffix = utilities.generate_random_hex_string8()
    sub_dir = f"{UT_PREFIX}rec_{suffix}"
    sub_path = os.path.join(ut_user_files_dir, sub_dir)
    root_file = f"{UT_PREFIX}root_{suffix}.txt"
    nested_file = f"nested_{suffix}.txt"

    try:
        os.makedirs(sub_path, exist_ok=True)
        with open(os.path.join(ut_user_files_dir, root_file), "w") as f:
            f.write("root")
        with open(os.path.join(sub_path, nested_file), "w") as f:
            f.write("nested")

        response = get_files(client, auth, extra_query={"recursive": "true"})
        assert response.status_code == HTTPStatus.OK
        rows = response.get_json()
        names = [r["name"] for r in rows]
        assert root_file in names
        assert nested_file in names
        for r in rows:
            assert r["type"] == "file"
    finally:
        remove_if_exists(os.path.join(ut_user_files_dir, root_file))
        remove_if_exists(sub_path)


# ---------------------------------------------------------------------------
# POST /user/files
# ---------------------------------------------------------------------------

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
        assert data["name"] == name
        assert data["type"] == "file"
        assert "updated_at" in data
        assert os.path.isfile(fpath)
        with open(fpath, encoding="utf-8") as f:
            assert f.read() == "hello"
    finally:
        remove_if_exists(fpath)


def test_user_files_post_creates_nested_directories(client, user_authentication, utilities):
    """Upload to a nested path should auto-create intermediate folders."""
    auth = user_authentication.json
    suffix = utilities.generate_random_hex_string8()
    nested = f"{UT_PREFIX}nested_{suffix}/sub/file.txt"
    base = user_files_dir(auth["id"])
    top_dir = os.path.join(base, f"{UT_PREFIX}nested_{suffix}")

    try:
        response = post_file(client, auth, nested, "nested content")
        assert response.status_code == HTTPStatus.CREATED
        data = response.get_json()
        assert data["name"] == "file.txt"
        assert data["relative_path"] == nested
        assert os.path.isfile(os.path.join(base, nested))
    finally:
        remove_if_exists(top_dir)


def test_user_files_post_path_traversal_blocked(client, user_authentication):
    auth = user_authentication.json
    response = post_file(client, auth, "../../evil.txt", "bad")
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_user_files_post_nested_dot_filename_blocked(client, user_authentication, utilities):
    """Filenames with dot basename are rejected even inside nested paths."""
    auth = user_authentication.json
    suffix = utilities.generate_random_hex_string8()
    response = post_file(client, auth, f"folder_{suffix}/.hidden", "x")
    assert response.status_code == HTTPStatus.BAD_REQUEST


# ---------------------------------------------------------------------------
# DELETE /user/files
# ---------------------------------------------------------------------------

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


def test_user_files_delete_directory(client, user_authentication, ut_user_files_dir, utilities):
    """DELETE should recursively remove a directory."""
    auth = user_authentication.json
    suffix = utilities.generate_random_hex_string8()
    dir_name = f"{UT_PREFIX}deldir_{suffix}"
    dir_path = os.path.join(ut_user_files_dir, dir_name)
    sub_file = os.path.join(dir_path, "child.txt")

    try:
        os.makedirs(dir_path, exist_ok=True)
        with open(sub_file, "w") as f:
            f.write("child")

        resp = delete_file(client, auth, dir_name)
        assert resp.status_code == HTTPStatus.OK
        assert not os.path.exists(dir_path)
    finally:
        remove_if_exists(dir_path)


def test_user_files_delete_path_traversal_blocked(client, user_authentication):
    auth = user_authentication.json
    response = delete_file(client, auth, "../../etc")
    assert response.status_code == HTTPStatus.BAD_REQUEST


# ---------------------------------------------------------------------------
# PUT /user/files – move / rename
# ---------------------------------------------------------------------------

def test_user_files_move_unauthorized(client, user_authentication):
    auth = user_authentication.json
    response = client.put(
        USER_FILES_URL,
        json={"user-id": auth["id"], "token": "bad", "source": "a.txt", "destination": "b.txt"},
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED


@pytest.mark.parametrize("missing", ["source", "destination"])
def test_user_files_move_missing_fields(client, user_authentication, missing):
    auth = user_authentication.json
    body = {**auth_json_body(auth), "source": "a.txt", "destination": "b.txt"}
    del body[missing]
    response = client.put(USER_FILES_URL, json=body)
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_user_files_move_source_not_found(client, user_authentication, utilities):
    auth = user_authentication.json
    suffix = utilities.generate_random_hex_string8()
    response = move_file(client, auth, f"no_{suffix}.txt", f"new_{suffix}.txt")
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_user_files_move_rename_file(client, user_authentication, utilities):
    auth = user_authentication.json
    suffix = utilities.generate_random_hex_string8()
    old_name = f"{UT_PREFIX}mv_old_{suffix}.txt"
    new_name = f"{UT_PREFIX}mv_new_{suffix}.txt"
    base = user_files_dir(auth["id"])

    try:
        post_file(client, auth, old_name, "moveme")
        resp = move_file(client, auth, old_name, new_name)
        assert resp.status_code == HTTPStatus.OK
        data = resp.get_json()
        assert data["name"] == new_name
        assert not os.path.exists(os.path.join(base, old_name))
        assert os.path.isfile(os.path.join(base, new_name))
    finally:
        remove_if_exists(os.path.join(base, old_name))
        remove_if_exists(os.path.join(base, new_name))


def test_user_files_move_into_subfolder(client, user_authentication, utilities):
    auth = user_authentication.json
    suffix = utilities.generate_random_hex_string8()
    file_name = f"{UT_PREFIX}mv_{suffix}.txt"
    dest_dir = f"{UT_PREFIX}dest_{suffix}"
    base = user_files_dir(auth["id"])

    try:
        post_file(client, auth, file_name, "content")
        resp = move_file(client, auth, file_name, f"{dest_dir}/{file_name}")
        assert resp.status_code == HTTPStatus.OK
        assert os.path.isfile(os.path.join(base, dest_dir, file_name))
        assert not os.path.exists(os.path.join(base, file_name))
    finally:
        remove_if_exists(os.path.join(base, file_name))
        remove_if_exists(os.path.join(base, dest_dir))


def test_user_files_move_conflict_when_destination_exists(client, user_authentication, utilities):
    auth = user_authentication.json
    suffix = utilities.generate_random_hex_string8()
    a = f"{UT_PREFIX}a_{suffix}.txt"
    b = f"{UT_PREFIX}b_{suffix}.txt"
    base = user_files_dir(auth["id"])

    try:
        post_file(client, auth, a, "aaa")
        post_file(client, auth, b, "bbb")
        resp = move_file(client, auth, a, b)
        assert resp.status_code == HTTPStatus.CONFLICT
    finally:
        remove_if_exists(os.path.join(base, a))
        remove_if_exists(os.path.join(base, b))


def test_user_files_move_path_traversal_blocked(client, user_authentication, utilities):
    auth = user_authentication.json
    suffix = utilities.generate_random_hex_string8()
    name = f"{UT_PREFIX}tr_{suffix}.txt"
    base = user_files_dir(auth["id"])

    try:
        post_file(client, auth, name, "x")
        resp = move_file(client, auth, name, f"../../{name}")
        assert resp.status_code == HTTPStatus.BAD_REQUEST
    finally:
        remove_if_exists(os.path.join(base, name))


def test_user_files_move_empty_fields(client, user_authentication):
    auth = user_authentication.json
    resp = move_file(client, auth, "", "something.txt")
    assert resp.status_code == HTTPStatus.BAD_REQUEST
    resp2 = move_file(client, auth, "something.txt", "")
    assert resp2.status_code == HTTPStatus.BAD_REQUEST


def test_user_files_move_directory(client, user_authentication, ut_user_files_dir, utilities):
    """PUT should be able to rename/move directories too."""
    auth = user_authentication.json
    suffix = utilities.generate_random_hex_string8()
    old_dir = f"{UT_PREFIX}olddir_{suffix}"
    new_dir = f"{UT_PREFIX}newdir_{suffix}"

    try:
        os.makedirs(os.path.join(ut_user_files_dir, old_dir), exist_ok=True)
        with open(os.path.join(ut_user_files_dir, old_dir, "child.txt"), "w") as f:
            f.write("hi")

        resp = move_file(client, auth, old_dir, new_dir)
        assert resp.status_code == HTTPStatus.OK
        assert resp.get_json()["type"] == "directory"
        assert os.path.isdir(os.path.join(ut_user_files_dir, new_dir))
        assert not os.path.exists(os.path.join(ut_user_files_dir, old_dir))
    finally:
        remove_if_exists(os.path.join(ut_user_files_dir, old_dir))
        remove_if_exists(os.path.join(ut_user_files_dir, new_dir))
