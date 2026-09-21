"""HTTP tests for UserAvatar (/user/avatar)."""
import base64
import os
from http import HTTPStatus

import pytest

import api as basil_api
from api_utils import (
    USER_AVATAR_BUILTIN_NAMES,
    USER_AVATAR_CONFIG_FILENAME,
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


def test_user_avatar_corrupted_config_returns_default(client, clean_avatar):
    config_dir = user_config_dir(clean_avatar["id"])
    os.makedirs(config_dir, exist_ok=True)
    with open(os.path.join(config_dir, USER_AVATAR_CONFIG_FILENAME), "w", encoding="utf-8") as f:
        f.write("{not json")
    response = client.get(USER_AVATAR_URL, query_string=auth_query(clean_avatar))
    assert response.status_code == HTTPStatus.OK
    assert response.get_json() == {"type": "default"}


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
