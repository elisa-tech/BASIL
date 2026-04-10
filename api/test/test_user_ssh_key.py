"""HTTP tests for UserSshKey (GET/POST/DELETE /user/ssh-key)."""
import os
import time
from http import HTTPStatus

import pytest

import api as basil_api
from conftest import UT_READER_USER_EMAIL
from db.models.ssh_key import SshKeyModel
from db.models.user import UserModel

_USER_SSH_KEY_URL = "/user/ssh-key"
_UT_PREFIX = "ut_ssh_key_"


def _auth_query(auth_json):
    return {"user-id": auth_json["id"], "token": auth_json["token"]}


def _auth_json_body(auth_json):
    return {"user-id": auth_json["id"], "token": auth_json["token"]}


def _get_ssh_keys(client, auth_json):
    return client.get(_USER_SSH_KEY_URL, query_string=_auth_query(auth_json))


def _delete_ssh_key(client, auth_json, key_id):
    body = {**_auth_json_body(auth_json), "id": key_id}
    return client.delete(_USER_SSH_KEY_URL, json=body)


def _ssh_key_file_path(key_id):
    return os.path.join(basil_api.SSH_KEYS_PATH, str(key_id))


def _remove_ssh_key_file(key_id):
    path = _ssh_key_file_path(key_id)
    if os.path.isfile(path):
        os.remove(path)


def _insert_ssh_key(client_db, user, title, key_material="ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQC ut-test"):
    db_user = client_db.session.get(UserModel, user.id)
    row = SshKeyModel(title, key_material, db_user)
    client_db.session.add(row)
    client_db.session.commit()
    return row


def _delete_ssh_key_row(client_db, key_id):
    row = client_db.session.query(SshKeyModel).filter(SshKeyModel.id == key_id).one_or_none()
    if row is not None:
        client_db.session.delete(row)
        client_db.session.commit()


def _get_user_by_email(client_db, email):
    return client_db.session.query(UserModel).filter(UserModel.email == email).one()


def test_user_ssh_key_get_unauthorized_without_credentials(client):
    response = client.get(_USER_SSH_KEY_URL)
    assert response.status_code == HTTPStatus.UNAUTHORIZED


def test_user_ssh_key_get_unauthorized_invalid_token(client, user_authentication):
    auth = user_authentication.json
    response = client.get(
        _USER_SSH_KEY_URL,
        query_string={"user-id": auth["id"], "token": "invalid-token"},
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED


@pytest.mark.parametrize("omit_key", ["user-id", "token"])
def test_user_ssh_key_get_unauthorized_missing_auth_query_keys(
    client, user_authentication, omit_key
):
    qs = _auth_query(user_authentication.json)
    del qs[omit_key]
    response = client.get(_USER_SSH_KEY_URL, query_string=qs)
    assert response.status_code == HTTPStatus.UNAUTHORIZED


def test_user_ssh_key_get_ok_empty(client, user_authentication, client_db, ut_user_db):
    """No rows for this user: API returns an empty list."""
    existing = (
        client_db.session.query(SshKeyModel)
        .filter(SshKeyModel.created_by_id == ut_user_db.id)
        .all()
    )
    for row in existing:
        _remove_ssh_key_file(row.id)
        client_db.session.delete(row)
    client_db.session.commit()

    auth = user_authentication.json
    response = _get_ssh_keys(client, auth)
    assert response.status_code == HTTPStatus.OK
    assert response.get_json() == []


def test_user_ssh_key_get_ok_ordered_newest_first(
    client, user_authentication, client_db, ut_user_db, utilities
):
    suffix = utilities.generate_random_hex_string8()
    t1 = f"{_UT_PREFIX}a_{suffix}"
    t2 = f"{_UT_PREFIX}b_{suffix}"
    k1 = _insert_ssh_key(client_db, ut_user_db, t1)
    time.sleep(0.05)
    k2 = _insert_ssh_key(client_db, ut_user_db, t2)
    try:
        auth = user_authentication.json
        response = _get_ssh_keys(client, auth)
        assert response.status_code == HTTPStatus.OK
        rows = response.get_json()
        ids = [r["id"] for r in rows if r["title"] in (t1, t2)]
        assert ids == [k2.id, k1.id]
        for r in rows:
            if r["id"] == k2.id:
                assert "created_at" in r
    finally:
        _delete_ssh_key_row(client_db, k2.id)
        _delete_ssh_key_row(client_db, k1.id)


@pytest.mark.parametrize("mandatory_field", ["title", "ssh_key"])
def test_user_ssh_key_post_missing_mandatory_fields(client, user_authentication, mandatory_field):
    auth = user_authentication.json
    body = {
        **_auth_json_body(auth),
        "title": f"{_UT_PREFIX}x",
        "ssh_key": "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQC x",
    }
    del body[mandatory_field]
    response = client.post(_USER_SSH_KEY_URL, json=body)
    assert response.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.parametrize("strip_empty", ["title", "ssh_key"])
def test_user_ssh_key_post_rejects_blank_title_or_key_after_strip(
    client, user_authentication, strip_empty
):
    auth = user_authentication.json
    body = {
        **_auth_json_body(auth),
        "title": f"{_UT_PREFIX}t",
        "ssh_key": "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQC x",
    }
    body[strip_empty] = "   "
    response = client.post(_USER_SSH_KEY_URL, json=body)
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_user_ssh_key_delete_missing_id(client, user_authentication):
    auth = user_authentication.json
    response = client.delete(
        _USER_SSH_KEY_URL,
        json={**_auth_json_body(auth)},
    )
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_user_ssh_key_delete_unauthorized(client, user_authentication):
    auth = user_authentication.json
    response = client.delete(
        _USER_SSH_KEY_URL,
        json={"user-id": auth["id"], "token": "bad-token", "id": 1},
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED


def test_user_ssh_key_delete_not_found(client, user_authentication):
    auth = user_authentication.json
    response = _delete_ssh_key(client, auth, 2**30)
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_user_ssh_key_delete_forbidden_when_not_owner(
    client, user_authentication, client_db, utilities, ut_reader_user_db
):
    reader = _get_user_by_email(client_db, UT_READER_USER_EMAIL)
    suffix = utilities.generate_random_hex_string8()
    row = _insert_ssh_key(client_db, reader, f"{_UT_PREFIX}reader_{suffix}")
    try:
        auth = user_authentication.json
        response = _delete_ssh_key(client, auth, row.id)
        assert response.status_code == HTTPStatus.UNAUTHORIZED
    finally:
        _remove_ssh_key_file(row.id)
        _delete_ssh_key_row(client_db, row.id)


def test_user_ssh_key_delete_ok_removes_row_and_file(
    client, user_authentication, client_db, ut_user_db, utilities
):
    suffix = utilities.generate_random_hex_string8()
    title = f"{_UT_PREFIX}del_{suffix}"
    row = _insert_ssh_key(client_db, ut_user_db, title)
    path = _ssh_key_file_path(row.id)
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write("ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQC test-key\n")
        os.chmod(path, 0o600)

        auth = user_authentication.json
        response = _delete_ssh_key(client, auth, row.id)
        assert response.status_code == HTTPStatus.OK
        assert response.get_json() is True

        still = (
            client_db.session.query(SshKeyModel).filter(SshKeyModel.id == row.id).one_or_none()
        )
        assert still is None
        assert not os.path.isfile(path)
    finally:
        _remove_ssh_key_file(row.id)
        _delete_ssh_key_row(client_db, row.id)
