"""HTTP tests for UserFileFolder (/user/files/folder)."""
import os
from http import HTTPStatus

from user_files_test_helpers import (
    USER_FILE_FOLDER_URL,
    UT_PREFIX,
    auth_json_body,
    create_folder,
    remove_if_exists,
    user_files_dir,
)


def test_user_file_folder_post_unauthorized(client, user_authentication):
    auth = user_authentication.json
    response = client.post(
        USER_FILE_FOLDER_URL,
        json={"user-id": auth["id"], "token": "bad", "foldername": "test"},
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED


def test_user_file_folder_post_missing_foldername(client, user_authentication):
    auth = user_authentication.json
    body = auth_json_body(auth)
    response = client.post(USER_FILE_FOLDER_URL, json=body)
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_user_file_folder_post_empty_foldername(client, user_authentication):
    auth = user_authentication.json
    response = create_folder(client, auth, "")
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_user_file_folder_post_dot_foldername(client, user_authentication):
    auth = user_authentication.json
    response = create_folder(client, auth, ".hidden")
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_user_file_folder_post_created(client, user_authentication, utilities):
    auth = user_authentication.json
    suffix = utilities.generate_random_hex_string8()
    name = f"{UT_PREFIX}folder_{suffix}"
    base = user_files_dir(auth["id"])
    folder_path = os.path.join(base, name)

    try:
        response = create_folder(client, auth, name)
        assert response.status_code == HTTPStatus.CREATED
        data = response.get_json()
        assert data["name"] == name
        assert data["type"] == "directory"
        assert data["relative_path"] == name
        assert os.path.isdir(folder_path)
    finally:
        remove_if_exists(folder_path)


def test_user_file_folder_post_nested(client, user_authentication, utilities):
    """Creating nested folders (e.g. 'a/b/c') should work."""
    auth = user_authentication.json
    suffix = utilities.generate_random_hex_string8()
    name = f"{UT_PREFIX}nest_{suffix}/sub/deep"
    base = user_files_dir(auth["id"])
    top_dir = os.path.join(base, f"{UT_PREFIX}nest_{suffix}")

    try:
        response = create_folder(client, auth, name)
        assert response.status_code == HTTPStatus.CREATED
        assert response.get_json()["type"] == "directory"
        assert os.path.isdir(os.path.join(base, name))
    finally:
        remove_if_exists(top_dir)


def test_user_file_folder_post_conflict(client, user_authentication, utilities):
    auth = user_authentication.json
    suffix = utilities.generate_random_hex_string8()
    name = f"{UT_PREFIX}dup_{suffix}"
    base = user_files_dir(auth["id"])

    try:
        first = create_folder(client, auth, name)
        assert first.status_code == HTTPStatus.CREATED
        second = create_folder(client, auth, name)
        assert second.status_code == HTTPStatus.CONFLICT
    finally:
        remove_if_exists(os.path.join(base, name))


def test_user_file_folder_post_path_traversal_blocked(client, user_authentication):
    auth = user_authentication.json
    response = create_folder(client, auth, "../../escape")
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_user_file_folder_post_nested_dot_blocked(client, user_authentication, utilities):
    """Folder paths where the leaf starts with a dot should be rejected."""
    auth = user_authentication.json
    suffix = utilities.generate_random_hex_string8()
    response = create_folder(client, auth, f"parent_{suffix}/.secret")
    assert response.status_code == HTTPStatus.BAD_REQUEST
