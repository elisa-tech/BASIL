"""HTTP tests for UserFileDownload (/user/files/download)."""
import io
import os
import tarfile
from http import HTTPStatus

import pytest

from api_utils import iter_user_folder_tarball
from user_files_test_helpers import (
    USER_FILE_DOWNLOAD_URL,
    UT_PREFIX,
    auth_query,
    create_folder,
    get_download,
    post_file,
    remove_if_exists,
    remove_user_files_dir_if_exists,
    user_files_dir,
)


def _content_disposition(response):
    return response.headers.get("Content-Disposition", "")


def test_user_file_download_get_unauthorized_without_credentials(client):
    assert client.get(USER_FILE_DOWNLOAD_URL).status_code == HTTPStatus.UNAUTHORIZED


def test_user_file_download_get_bad_request_without_filename(client, user_authentication):
    """Logged-in requests still require filename."""
    auth = user_authentication.json
    assert client.get(
        USER_FILE_DOWNLOAD_URL, query_string=auth_query(auth)
    ).status_code == HTTPStatus.BAD_REQUEST


def test_user_file_download_get_unauthorized_invalid_token(client, user_authentication):
    auth = user_authentication.json
    response = client.get(
        USER_FILE_DOWNLOAD_URL,
        query_string={"user-id": auth["id"], "token": "invalid-token", "filename": f"{UT_PREFIX}x.txt"},
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED


@pytest.mark.parametrize("omit_key", ["user-id", "token"])
def test_user_file_download_get_unauthorized_missing_auth_query_keys(
    client, user_authentication, omit_key
):
    qs = {**auth_query(user_authentication.json), "filename": f"{UT_PREFIX}a.txt"}
    del qs[omit_key]
    response = client.get(USER_FILE_DOWNLOAD_URL, query_string=qs)
    assert response.status_code == HTTPStatus.UNAUTHORIZED


def test_user_file_download_get_not_found_when_user_dir_missing(
    client, user_authentication, ut_user_db
):
    remove_user_files_dir_if_exists(ut_user_db.id)
    auth = user_authentication.json
    name = f"{UT_PREFIX}nodir_{auth['id']}.txt"
    response = get_download(client, auth, name)
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_user_file_download_get_not_found(client, user_authentication, utilities):
    auth = user_authentication.json
    name = f"{UT_PREFIX}nodl_{utilities.generate_random_hex_string8()}.txt"
    response = get_download(client, auth, name)
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_user_file_download_get_bad_request_empty_filename(client, user_authentication):
    auth = user_authentication.json
    response = get_download(client, auth, "")
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_user_file_download_get_path_traversal_blocked(client, user_authentication):
    auth = user_authentication.json
    response = get_download(client, auth, "../../etc/passwd")
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_user_file_download_cannot_use_another_users_id(
    client, user_authentication, reader_authentication, utilities
):
    """A valid token cannot be paired with another user's id to read their files."""
    owner = user_authentication.json
    other = reader_authentication.json
    name = f"{UT_PREFIX}other_{utilities.generate_random_hex_string8()}.txt"
    owner_path = os.path.join(user_files_dir(owner["id"]), name)

    try:
        assert post_file(client, owner, name, "owner-secret").status_code == HTTPStatus.CREATED
        response = client.get(
            USER_FILE_DOWNLOAD_URL,
            query_string={
                "user-id": owner["id"],
                "token": other["token"],
                "filename": name,
            },
        )
        assert response.status_code == HTTPStatus.UNAUTHORIZED
        assert b"owner-secret" not in response.data
    finally:
        remove_if_exists(owner_path)


def test_user_file_download_cannot_read_another_users_file_by_relative_path(
    client, user_authentication, reader_authentication, utilities
):
    """Relative paths must stay inside the logged-in user's files directory."""
    owner = user_authentication.json
    other = reader_authentication.json
    name = f"{UT_PREFIX}cross_{utilities.generate_random_hex_string8()}.txt"
    owner_path = os.path.join(user_files_dir(owner["id"]), name)

    try:
        assert post_file(client, owner, name, "owner-secret").status_code == HTTPStatus.CREATED
        os.makedirs(user_files_dir(other["id"]), exist_ok=True)
        response = get_download(client, other, f"../{owner['id']}/{name}")
        assert response.status_code == HTTPStatus.BAD_REQUEST
        assert b"owner-secret" not in response.data
    finally:
        remove_if_exists(owner_path)


def test_user_file_download_get_ok_file(client, user_authentication, utilities):
    auth = user_authentication.json
    name = f"{UT_PREFIX}dl_{utilities.generate_random_hex_string8()}.txt"
    content = "download-me"
    path = os.path.join(user_files_dir(auth["id"]), name)
    try:
        posted = post_file(client, auth, name, content)
        assert posted.status_code == HTTPStatus.CREATED
        response = get_download(client, auth, name)
        assert response.status_code == HTTPStatus.OK
        assert response.data == content.encode("utf-8")
        disposition = _content_disposition(response)
        assert "attachment" in disposition
        assert name in disposition
    finally:
        remove_if_exists(path)


def test_user_file_download_get_ok_for_guest(client, guest_authentication, utilities):
    """Guests cannot upload, but they can still download existing files."""
    auth = guest_authentication.json
    name = f"{UT_PREFIX}guest_dl_{utilities.generate_random_hex_string8()}.txt"
    content = "guest-can-download"
    path = os.path.join(user_files_dir(auth["id"]), name)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        response = get_download(client, auth, name)
        assert response.status_code == HTTPStatus.OK
        assert response.data == content.encode("utf-8")
    finally:
        remove_if_exists(path)


def test_user_file_download_get_ok_empty_file(
    client, user_authentication, utilities, ut_user_files_dir
):
    """Empty files are downloadable even though content GET treats them as missing."""
    auth = user_authentication.json
    name = f"{UT_PREFIX}dlempty_{utilities.generate_random_hex_string8()}.txt"
    path = os.path.join(ut_user_files_dir, name)
    try:
        with open(path, "w", encoding="utf-8"):
            pass
        response = get_download(client, auth, name)
        assert response.status_code == HTTPStatus.OK
        assert response.data == b""
        assert name in _content_disposition(response)
    finally:
        remove_if_exists(path)


def test_user_file_download_get_nested_file(client, user_authentication, utilities):
    auth = user_authentication.json
    suffix = utilities.generate_random_hex_string8()
    nested = f"{UT_PREFIX}dlnest_{suffix}/sub/deep.txt"
    base = user_files_dir(auth["id"])
    top_dir = os.path.join(base, f"{UT_PREFIX}dlnest_{suffix}")

    try:
        post_file(client, auth, nested, "deep-download")
        response = get_download(client, auth, nested)
        assert response.status_code == HTTPStatus.OK
        assert response.data == b"deep-download"
        assert "deep.txt" in _content_disposition(response)
    finally:
        remove_if_exists(top_dir)


def test_user_file_download_get_ok_folder_tarball(client, user_authentication, utilities):
    auth = user_authentication.json
    suffix = utilities.generate_random_hex_string8()
    folder = f"{UT_PREFIX}dltar_{suffix}"
    nested = f"{folder}/inside.txt"
    hidden_name = ".secret.txt"
    base = user_files_dir(auth["id"])
    folder_path = os.path.join(base, folder)
    hidden_path = os.path.join(folder_path, hidden_name)

    try:
        assert create_folder(client, auth, folder).status_code == HTTPStatus.CREATED
        assert post_file(client, auth, nested, "inside-content").status_code == HTTPStatus.CREATED
        with open(hidden_path, "w", encoding="utf-8") as f:
            f.write("hidden")

        response = get_download(client, auth, folder)
        assert response.status_code == HTTPStatus.OK
        disposition = _content_disposition(response)
        assert "attachment" in disposition
        assert f"{os.path.basename(folder)}.tar.gz" in disposition
        assert "gzip" in (response.content_type or "")

        with tarfile.open(fileobj=io.BytesIO(response.data), mode="r:gz") as tar:
            names = tar.getnames()
            assert folder in names
            assert f"{folder}/inside.txt" in names
            assert f"{folder}/{hidden_name}" not in names
            member = tar.extractfile(f"{folder}/inside.txt")
            assert member is not None
            assert member.read() == b"inside-content"
    finally:
        remove_if_exists(folder_path)


def test_user_file_download_get_ok_empty_folder_tarball(client, user_authentication, utilities):
    auth = user_authentication.json
    suffix = utilities.generate_random_hex_string8()
    folder = f"{UT_PREFIX}dlemptyfolder_{suffix}"
    folder_path = os.path.join(user_files_dir(auth["id"]), folder)

    try:
        assert create_folder(client, auth, folder).status_code == HTTPStatus.CREATED
        response = get_download(client, auth, folder)
        assert response.status_code == HTTPStatus.OK
        with tarfile.open(fileobj=io.BytesIO(response.data), mode="r:gz") as tar:
            names = tar.getnames()
            assert folder in names
    finally:
        remove_if_exists(folder_path)


def test_user_file_download_get_nested_folder_tarball(client, user_authentication, utilities):
    auth = user_authentication.json
    suffix = utilities.generate_random_hex_string8()
    top = f"{UT_PREFIX}dlnestfolder_{suffix}"
    nested_folder = f"{top}/sub"
    nested_file = f"{nested_folder}/deep.txt"
    top_dir = os.path.join(user_files_dir(auth["id"]), top)

    try:
        post_file(client, auth, nested_file, "nested-folder-file")
        response = get_download(client, auth, nested_folder)
        assert response.status_code == HTTPStatus.OK
        assert "sub.tar.gz" in _content_disposition(response)
        with tarfile.open(fileobj=io.BytesIO(response.data), mode="r:gz") as tar:
            names = tar.getnames()
            assert "sub" in names
            assert "sub/deep.txt" in names
            member = tar.extractfile("sub/deep.txt")
            assert member is not None
            assert member.read() == b"nested-folder-file"
    finally:
        remove_if_exists(top_dir)


def test_iter_user_folder_tarball_streams_valid_archive(tmp_path):
    folder = tmp_path / "pack"
    folder.mkdir()
    (folder / "a.txt").write_bytes(b"x" * 4000)
    (folder / ".hidden").write_text("nope")
    chunks = list(iter_user_folder_tarball(str(folder), "pack", chunk_size=256))
    assert len(chunks) > 1
    assert all(isinstance(chunk, (bytes, bytearray)) for chunk in chunks)
    with tarfile.open(fileobj=io.BytesIO(b"".join(chunks)), mode="r:gz") as tar:
        names = tar.getnames()
        assert "pack/a.txt" in names
        assert "pack/.hidden" not in names
        member = tar.extractfile("pack/a.txt")
        assert member is not None
        assert member.read() == b"x" * 4000
