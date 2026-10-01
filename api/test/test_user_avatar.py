"""HTTP tests for UserAvatar (/user/avatar)."""
import base64
import io
import json
import os
from http import HTTPStatus

import pytest

import api as basil_api
import api_utils
from api_utils import (
    USER_AVATAR_BUILTIN_NAMES,
    USER_AVATAR_CONFIG_FILENAME,
    USER_AVATAR_MAX_REQUEST_SIZE,
    USER_AVATAR_MAX_SIZE,
    get_image_type,
)

USER_AVATAR_URL = "/user/avatar"

# 1x1 transparent PNG
PNG_CONTENT = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
)


def auth_query(auth_json):
    return {"user-id": auth_json["id"], "token": auth_json["token"]}


def data_url(content, mime="image/png"):
    return f"data:{mime};base64,{base64.b64encode(content).decode('ascii')}"


def user_config_dir(user_id):
    return os.path.join(basil_api.USER_FILES_BASE_DIR, str(user_id), ".config")


@pytest.fixture()
def clean_avatar(client, user_authentication):
    """Reset the avatar of the UT user before and after each test"""
    body = auth_query(user_authentication.json)
    client.delete(USER_AVATAR_URL, json=body)
    yield user_authentication.json
    client.delete(USER_AVATAR_URL, json=body)


@pytest.fixture()
def clean_reader_avatar(client, reader_authentication):
    """Reset the avatar of the UT reader user before and after each test"""
    body = auth_query(reader_authentication.json)
    client.delete(USER_AVATAR_URL, json=body)
    yield reader_authentication.json
    client.delete(USER_AVATAR_URL, json=body)


def put_avatar(client, auth_json, **fields):
    return client.put(USER_AVATAR_URL, json={**auth_query(auth_json), **fields})


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

def test_user_avatar_get_unauthorized_invalid_token(client, user_authentication):
    auth = user_authentication.json
    response = client.get(USER_AVATAR_URL, query_string={"user-id": auth["id"], "token": "invalid-token"})
    assert response.status_code == HTTPStatus.UNAUTHORIZED


def test_user_avatar_put_unauthorized_invalid_token(client, user_authentication):
    auth = user_authentication.json
    response = client.put(USER_AVATAR_URL, json={"user-id": auth["id"], "token": "invalid-token",
                                                 "type": "builtin", "name": USER_AVATAR_BUILTIN_NAMES[0]})
    assert response.status_code == HTTPStatus.UNAUTHORIZED


@pytest.mark.parametrize("omit_key", ["user-id", "token", "type"])
def test_user_avatar_put_missing_fields(client, clean_avatar, omit_key):
    body = {**auth_query(clean_avatar), "type": "builtin", "name": USER_AVATAR_BUILTIN_NAMES[0]}
    del body[omit_key]
    response = client.put(USER_AVATAR_URL, json=body)
    assert response.status_code == HTTPStatus.BAD_REQUEST


# ---------------------------------------------------------------------------
# Default and builtin avatars
# ---------------------------------------------------------------------------

def test_user_avatar_default(client, clean_avatar):
    response = client.get(USER_AVATAR_URL, query_string=auth_query(clean_avatar))
    assert response.status_code == HTTPStatus.OK
    assert response.get_json() == {"type": "default"}


@pytest.mark.parametrize("name", USER_AVATAR_BUILTIN_NAMES)
def test_user_avatar_builtin(client, clean_avatar, name):
    response = put_avatar(client, clean_avatar, type="builtin", name=name)
    assert response.status_code == HTTPStatus.OK
    assert response.get_json() == {"type": "builtin", "name": name}

    response = client.get(USER_AVATAR_URL, query_string=auth_query(clean_avatar))
    assert response.get_json() == {"type": "builtin", "name": name}


def test_user_avatar_builtin_unknown_name(client, clean_avatar):
    response = put_avatar(client, clean_avatar, type="builtin", name="not-an-avatar")
    assert response.status_code == HTTPStatus.BAD_REQUEST

    response = client.get(USER_AVATAR_URL, query_string=auth_query(clean_avatar))
    assert response.get_json() == {"type": "default"}


def test_user_avatar_unknown_type(client, clean_avatar):
    response = put_avatar(client, clean_avatar, type="gravatar")
    assert response.status_code == HTTPStatus.BAD_REQUEST


# ---------------------------------------------------------------------------
# Uploaded avatars
# ---------------------------------------------------------------------------

def test_user_avatar_custom_png(client, clean_avatar):
    response = put_avatar(client, clean_avatar, type="custom", data=data_url(PNG_CONTENT))
    assert response.status_code == HTTPStatus.OK
    assert response.get_json() == {"type": "custom", "data": data_url(PNG_CONTENT)}

    config_dir = user_config_dir(clean_avatar["id"])
    assert os.path.isfile(os.path.join(config_dir, "avatar.png"))
    assert os.path.isfile(os.path.join(config_dir, USER_AVATAR_CONFIG_FILENAME))

    response = client.get(USER_AVATAR_URL, query_string=auth_query(clean_avatar))
    assert response.get_json() == {"type": "custom", "data": data_url(PNG_CONTENT)}


def test_user_avatar_custom_mime_is_detected_from_content(client, clean_avatar):
    """The declared mime type is ignored: the stored type comes from the file content"""
    response = put_avatar(client, clean_avatar, type="custom", data=data_url(PNG_CONTENT, mime="image/jpeg"))
    assert response.status_code == HTTPStatus.OK
    assert response.get_json()["data"].startswith("data:image/png;base64,")


@pytest.mark.parametrize("data", [
    "not a data url",
    "data:image/png;base64,***",
    "data:image/png;base64,",
    data_url(b"<svg xmlns='http://www.w3.org/2000/svg'><script>alert(1)</script></svg>", mime="image/svg+xml"),
    data_url(b"just some text", mime="text/plain"),
], ids=["not-data-url", "invalid-base64", "empty", "svg", "text"])
def test_user_avatar_custom_invalid(client, clean_avatar, data):
    response = put_avatar(client, clean_avatar, type="custom", data=data)
    assert response.status_code == HTTPStatus.BAD_REQUEST

    response = client.get(USER_AVATAR_URL, query_string=auth_query(clean_avatar))
    assert response.get_json() == {"type": "default"}


def test_user_avatar_custom_too_big(client, clean_avatar):
    content = PNG_CONTENT + b"\0" * USER_AVATAR_MAX_SIZE
    response = put_avatar(client, clean_avatar, type="custom", data=data_url(content))
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_user_avatar_builtin_replaces_custom(client, clean_avatar):
    put_avatar(client, clean_avatar, type="custom", data=data_url(PNG_CONTENT))
    response = put_avatar(client, clean_avatar, type="builtin", name=USER_AVATAR_BUILTIN_NAMES[0])
    assert response.status_code == HTTPStatus.OK
    assert not os.path.exists(os.path.join(user_config_dir(clean_avatar["id"]), "avatar.png"))


def test_user_avatar_delete(client, clean_avatar):
    put_avatar(client, clean_avatar, type="custom", data=data_url(PNG_CONTENT))
    response = client.delete(USER_AVATAR_URL, json=auth_query(clean_avatar))
    assert response.status_code == HTTPStatus.OK
    assert response.get_json() == {"type": "default"}

    config_dir = user_config_dir(clean_avatar["id"])
    assert not os.path.exists(os.path.join(config_dir, "avatar.png"))
    assert not os.path.exists(os.path.join(config_dir, USER_AVATAR_CONFIG_FILENAME))


def test_user_avatar_custom_replaces_custom_of_other_type(client, clean_avatar):
    gif_content = b"GIF89a" + b"\0" * 8
    put_avatar(client, clean_avatar, type="custom", data=data_url(PNG_CONTENT))
    response = put_avatar(client, clean_avatar, type="custom", data=data_url(gif_content, mime="image/gif"))
    assert response.status_code == HTTPStatus.OK

    config_dir = user_config_dir(clean_avatar["id"])
    assert os.path.isfile(os.path.join(config_dir, "avatar.gif"))
    assert not os.path.exists(os.path.join(config_dir, "avatar.png"))


@pytest.mark.parametrize("new_avatar", [
    {"type": "builtin", "name": USER_AVATAR_BUILTIN_NAMES[1]},
    {"type": "custom", "data": data_url(b"GIF89a" + b"\0" * 8, mime="image/gif")},
], ids=["builtin", "custom"])
def test_user_avatar_failed_write_keeps_previous_avatar(client, clean_avatar, monkeypatch, new_avatar):
    """If the new avatar cannot be written, the previous one is still there"""
    put_avatar(client, clean_avatar, type="custom", data=data_url(PNG_CONTENT))

    def failing_write(path, content):
        raise OSError("No space left on device")

    monkeypatch.setattr(api_utils, "write_file_atomically", failing_write)
    with pytest.raises(OSError):
        put_avatar(client, clean_avatar, **new_avatar)
    monkeypatch.undo()

    response = client.get(USER_AVATAR_URL, query_string=auth_query(clean_avatar))
    assert response.get_json() == {"type": "custom", "data": data_url(PNG_CONTENT)}


def test_user_avatar_no_temporary_files_left(client, clean_avatar):
    put_avatar(client, clean_avatar, type="custom", data=data_url(PNG_CONTENT))
    put_avatar(client, clean_avatar, type="builtin", name=USER_AVATAR_BUILTIN_NAMES[0])
    config_dir = user_config_dir(clean_avatar["id"])
    assert not [f for f in os.listdir(config_dir) if f.endswith(".tmp")]


def test_user_avatar_corrupted_config_returns_default(client, clean_avatar):
    config_dir = user_config_dir(clean_avatar["id"])
    os.makedirs(config_dir, exist_ok=True)
    with open(os.path.join(config_dir, USER_AVATAR_CONFIG_FILENAME), "w", encoding="utf-8") as f:
        f.write("{not json")
    response = client.get(USER_AVATAR_URL, query_string=auth_query(clean_avatar))
    assert response.status_code == HTTPStatus.OK
    assert response.get_json() == {"type": "default"}


# ---------------------------------------------------------------------------
# Request size
# ---------------------------------------------------------------------------

def test_user_avatar_put_request_too_big(client, clean_avatar):
    """Big requests are rejected before the body is parsed"""
    body = json.dumps({**auth_query(clean_avatar), "type": "custom",
                       "data": "A" * USER_AVATAR_MAX_REQUEST_SIZE})
    response = client.put(USER_AVATAR_URL, data=body, content_type="application/json")
    assert response.status_code == HTTPStatus.REQUEST_ENTITY_TOO_LARGE

    response = client.get(USER_AVATAR_URL, query_string=auth_query(clean_avatar))
    assert response.get_json() == {"type": "default"}


def test_user_avatar_put_request_without_content_length(client, clean_avatar):
    """Chunked requests have no Content-Length, so their size cannot be checked upfront"""
    body = json.dumps({**auth_query(clean_avatar), "type": "builtin", "name": USER_AVATAR_BUILTIN_NAMES[0]})
    response = client.put(USER_AVATAR_URL, input_stream=io.BytesIO(body.encode("utf-8")),
                          content_type="application/json", headers={"Transfer-Encoding": "chunked"})
    assert response.status_code == HTTPStatus.LENGTH_REQUIRED


def test_user_avatar_put_max_size_image_fits_in_request(client, clean_avatar):
    """An image of the maximum allowed size is not rejected by the request size limit"""
    content = PNG_CONTENT + b"\0" * (USER_AVATAR_MAX_SIZE - len(PNG_CONTENT))
    response = put_avatar(client, clean_avatar, type="custom", data=data_url(content))
    assert response.status_code == HTTPStatus.OK


# ---------------------------------------------------------------------------
# Avatar of other users
# ---------------------------------------------------------------------------

def other_user_query(auth_json, target_user_id):
    return {**auth_query(auth_json), "target-user-id": target_user_id}


def test_user_avatar_get_other_user(client, clean_avatar, clean_reader_avatar):
    put_avatar(client, clean_reader_avatar, type="builtin", name=USER_AVATAR_BUILTIN_NAMES[2])

    response = client.get(USER_AVATAR_URL, query_string=other_user_query(clean_avatar, clean_reader_avatar["id"]))
    assert response.status_code == HTTPStatus.OK
    assert response.get_json() == {"type": "builtin", "name": USER_AVATAR_BUILTIN_NAMES[2]}

    # The avatar of the current user is not affected
    response = client.get(USER_AVATAR_URL, query_string=auth_query(clean_avatar))
    assert response.get_json() == {"type": "default"}


def test_user_avatar_get_other_user_custom(client, clean_avatar, clean_reader_avatar):
    put_avatar(client, clean_reader_avatar, type="custom", data=data_url(PNG_CONTENT))
    response = client.get(USER_AVATAR_URL, query_string=other_user_query(clean_avatar, clean_reader_avatar["id"]))
    assert response.status_code == HTTPStatus.OK
    assert response.get_json() == {"type": "custom", "data": data_url(PNG_CONTENT)}


def test_user_avatar_get_other_user_by_username(client, clean_avatar, clean_reader_avatar):
    """Work items only carry the username of their creator"""
    put_avatar(client, clean_reader_avatar, type="builtin", name=USER_AVATAR_BUILTIN_NAMES[3])
    query = {**auth_query(clean_avatar), "target-username": clean_reader_avatar["username"]}
    response = client.get(USER_AVATAR_URL, query_string=query)
    assert response.status_code == HTTPStatus.OK
    assert response.get_json() == {"type": "builtin", "name": USER_AVATAR_BUILTIN_NAMES[3]}


def test_user_avatar_get_other_user_by_username_not_found(client, clean_avatar):
    query = {**auth_query(clean_avatar), "target-username": "no_such_user_for_avatar"}
    response = client.get(USER_AVATAR_URL, query_string=query)
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_user_avatar_get_other_user_id_wins_over_username(client, clean_avatar, clean_reader_avatar):
    put_avatar(client, clean_reader_avatar, type="builtin", name=USER_AVATAR_BUILTIN_NAMES[3])
    query = {**other_user_query(clean_avatar, clean_avatar["id"]), "target-username": clean_reader_avatar["username"]}
    response = client.get(USER_AVATAR_URL, query_string=query)
    assert response.status_code == HTTPStatus.OK
    assert response.get_json() == {"type": "default"}


def test_user_avatar_get_other_user_unauthorized(client, clean_reader_avatar):
    response = client.get(USER_AVATAR_URL, query_string={"user-id": clean_reader_avatar["id"],
                                                         "token": "invalid-token",
                                                         "target-user-id": clean_reader_avatar["id"]})
    assert response.status_code == HTTPStatus.UNAUTHORIZED


def test_user_avatar_get_other_user_not_found(client, clean_avatar):
    response = client.get(USER_AVATAR_URL, query_string=other_user_query(clean_avatar, 999999))
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_user_avatar_get_other_user_invalid_id(client, clean_avatar):
    response = client.get(USER_AVATAR_URL, query_string=other_user_query(clean_avatar, "not-a-number"))
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_user_avatar_get_does_not_create_user_folder():
    """Reading the avatar of a user without files does not create folders for that user"""
    class UserWithoutFiles:
        id = 987654

    assert api_utils.get_user_avatar(UserWithoutFiles()) == {"type": "default"}
    assert not os.path.exists(os.path.join(basil_api.USER_FILES_BASE_DIR, str(UserWithoutFiles.id)))


def test_user_avatar_other_user_cannot_be_modified(client, clean_avatar, clean_reader_avatar):
    """PUT and DELETE only act on the user identified by user-id and token"""
    put_avatar(client, clean_reader_avatar, type="builtin", name=USER_AVATAR_BUILTIN_NAMES[3])
    put_avatar(client, clean_avatar, type="builtin", name=USER_AVATAR_BUILTIN_NAMES[0],
               **{"target-user-id": clean_reader_avatar["id"]})
    client.delete(USER_AVATAR_URL, json={**auth_query(clean_avatar), "target-user-id": clean_reader_avatar["id"]})

    response = client.get(USER_AVATAR_URL, query_string=auth_query(clean_reader_avatar))
    assert response.get_json() == {"type": "builtin", "name": USER_AVATAR_BUILTIN_NAMES[3]}


# ---------------------------------------------------------------------------
# Guests can see avatars but cannot change theirs
# ---------------------------------------------------------------------------

def remove_avatar_files(user_id):
    config_dir = user_config_dir(user_id)
    if not os.path.isdir(config_dir):
        return
    for filename in os.listdir(config_dir):
        if filename == USER_AVATAR_CONFIG_FILENAME or os.path.splitext(filename)[0] == "avatar":
            os.remove(os.path.join(config_dir, filename))


@pytest.fixture()
def clean_guest_avatar(guest_authentication):
    """Remove the avatar files of the UT guest user before and after each test,
    since guests cannot reset their avatar through the API"""
    remove_avatar_files(guest_authentication.json["id"])
    yield guest_authentication.json
    remove_avatar_files(guest_authentication.json["id"])


@pytest.mark.parametrize("fields", [
    {"type": "builtin", "name": USER_AVATAR_BUILTIN_NAMES[0]},
    {"type": "custom", "data": data_url(PNG_CONTENT)},
])
def test_user_avatar_put_forbidden_for_guest(client, clean_guest_avatar, fields):
    response = put_avatar(client, clean_guest_avatar, **fields)
    assert response.status_code == HTTPStatus.FORBIDDEN

    response = client.get(USER_AVATAR_URL, query_string=auth_query(clean_guest_avatar))
    assert response.get_json() == {"type": "default"}


def test_user_avatar_delete_forbidden_for_guest(client, clean_guest_avatar):
    config_dir = user_config_dir(clean_guest_avatar["id"])
    os.makedirs(config_dir, exist_ok=True)
    with open(os.path.join(config_dir, USER_AVATAR_CONFIG_FILENAME), "w", encoding="utf-8") as f:
        json.dump({"type": "builtin", "name": USER_AVATAR_BUILTIN_NAMES[1]}, f)

    response = client.delete(USER_AVATAR_URL, json=auth_query(clean_guest_avatar))
    assert response.status_code == HTTPStatus.FORBIDDEN

    response = client.get(USER_AVATAR_URL, query_string=auth_query(clean_guest_avatar))
    assert response.get_json() == {"type": "builtin", "name": USER_AVATAR_BUILTIN_NAMES[1]}


def test_user_avatar_guest_can_see_the_avatar_of_other_users(client, clean_guest_avatar, clean_reader_avatar):
    put_avatar(client, clean_reader_avatar, type="builtin", name=USER_AVATAR_BUILTIN_NAMES[2])
    query = other_user_query(clean_guest_avatar, clean_reader_avatar["id"])
    response = client.get(USER_AVATAR_URL, query_string=query)
    assert response.status_code == HTTPStatus.OK
    assert response.get_json() == {"type": "builtin", "name": USER_AVATAR_BUILTIN_NAMES[2]}


# ---------------------------------------------------------------------------
# Image type detection
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("content, expected", [
    (PNG_CONTENT, "png"),
    (b"\xff\xd8\xff\xe0" + b"\0" * 8, "jpeg"),
    (b"GIF89a" + b"\0" * 8, "gif"),
    (b"RIFF\0\0\0\0WEBPVP8 ", "webp"),
    (b"<svg></svg>", None),
    (b"", None),
])
def test_get_image_type(content, expected):
    assert get_image_type(content) == expected
