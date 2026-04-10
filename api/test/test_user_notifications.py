"""HTTP tests for UserNotifications (GET/PUT/DELETE /user/notifications)."""
import os
import tempfile
from http import HTTPStatus

import pytest

from db.models.api import ApiModel
from db.models.notification import NotificationModel
from db.models.user import UserModel
from conftest import UT_USER_EMAIL

_USER_NOTIFICATIONS_URL = "/user/notifications"

_UT_API_NAME = "ut_user_notifications"
_UT_API_LIBRARY = "ut_user_notifications_lib"
_UT_API_LIBRARY_VERSION = "v1.0.0"
_UT_API_CATEGORY = "ut_user_notifications_cat"
_UT_API_IMPLEMENTATION_FILE_FROM_ROW = 0
_UT_API_IMPLEMENTATION_FILE_TO_ROW = 42
_UT_API_TAGS = "ut_user_notifications_tags"
_UT_API_RAW_SPEC = "BASIL UT: user notifications."


def _get_user_by_email(client_db, email):
    return client_db.session.query(UserModel).filter(UserModel.email == email).one()


def _create_api(client_db, utilities, owner_email=UT_USER_EMAIL):
    user = _get_user_by_email(client_db, owner_email)
    raw_spec = tempfile.NamedTemporaryFile(mode="w", delete=False)
    raw_spec.write(_UT_API_RAW_SPEC)
    raw_spec.close()
    ut_api = ApiModel(
        _UT_API_NAME + "#" + utilities.generate_random_hex_string8(),
        _UT_API_LIBRARY,
        _UT_API_LIBRARY_VERSION,
        raw_spec.name,
        _UT_API_CATEGORY,
        utilities.generate_random_hex_string8(),
        raw_spec.name + "impl",
        _UT_API_IMPLEMENTATION_FILE_FROM_ROW,
        _UT_API_IMPLEMENTATION_FILE_TO_ROW,
        _UT_API_TAGS,
        user,
    )
    client_db.session.add(ut_api)
    client_db.session.commit()
    return ut_api, raw_spec.name


def _auth_query(auth_json):
    return {"user-id": auth_json["id"], "token": auth_json["token"]}


def _get_notifications(client, auth_json):
    return client.get(_USER_NOTIFICATIONS_URL, query_string=_auth_query(auth_json))


def _put_notifications(client, auth_json, api_id, notifications_flag):
    return client.put(
        _USER_NOTIFICATIONS_URL,
        json={
            "user-id": auth_json["id"],
            "token": auth_json["token"],
            "api-id": api_id,
            "notifications": notifications_flag,
        },
    )


def _delete_notifications(client, auth_json, notification_id=None):
    body = {
        "user-id": auth_json["id"],
        "token": auth_json["token"],
    }
    if notification_id is not None:
        body["id"] = notification_id
    return client.delete(_USER_NOTIFICATIONS_URL, json=body)


@pytest.fixture()
def owner_api(client_db, ut_user_db, utilities):
    """ApiModel owned by the default UT user."""
    ut_api, raw_path = _create_api(client_db, utilities, UT_USER_EMAIL)
    yield ut_api
    if os.path.isfile(raw_path):
        os.remove(raw_path)


def test_user_notifications_get_unauthorized_without_credentials(client):
    response = client.get(_USER_NOTIFICATIONS_URL)
    assert response.status_code == HTTPStatus.UNAUTHORIZED


def test_user_notifications_get_unauthorized_invalid_token(client, user_authentication):
    auth = user_authentication.json
    response = client.get(
        _USER_NOTIFICATIONS_URL,
        query_string={"user-id": auth["id"], "token": "invalid-token"},
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED


@pytest.mark.parametrize("omit_key", ["user-id", "token"])
def test_user_notifications_get_unauthorized_missing_auth_query_keys(
    client, user_authentication, omit_key
):
    qs = _auth_query(user_authentication.json)
    del qs[omit_key]
    response = client.get(_USER_NOTIFICATIONS_URL, query_string=qs)
    assert response.status_code == HTTPStatus.UNAUTHORIZED


def test_user_notifications_get_ok_empty_list(client, user_authentication):
    """Authenticated user with no matching notifications receives an empty list."""
    response = _get_notifications(client, user_authentication.json)
    assert response.status_code == HTTPStatus.OK
    assert response.get_json() == []


def test_user_notifications_get_includes_global_notification(
    client, client_db, user_authentication
):
    """Notifications with no api_id appear for any user until marked read."""
    auth = user_authentication.json
    note = NotificationModel(None, "INFO", "global title", "global body", "", "http://example.test")
    client_db.session.add(note)
    client_db.session.commit()
    note_id = note.id

    first = _get_notifications(client, auth)
    assert first.status_code == HTTPStatus.OK
    rows = first.get_json()
    assert any(n.get("id") == note_id and n.get("title") == "global title" for n in rows)

    del_resp = _delete_notifications(client, auth, notification_id=note_id)
    assert del_resp.status_code == HTTPStatus.OK

    second = _get_notifications(client, auth)
    assert second.status_code == HTTPStatus.OK
    assert not any(n.get("id") == note_id for n in second.get_json())


def test_user_notifications_get_owner_notification(
    client, client_db, user_authentication, owner_api
):
    """for_owners=1 notifications are listed when the user manages the API."""
    auth = user_authentication.json
    note = NotificationModel(owner_api, "INFO", "owner title", "owner body", "", "http://owner.test")
    note.for_owners = 1
    client_db.session.add(note)
    client_db.session.commit()
    note_id = note.id

    response = _get_notifications(client, auth)
    assert response.status_code == HTTPStatus.OK
    rows = response.get_json()
    assert any(n.get("id") == note_id for n in rows)


def test_user_notifications_get_subscribed_api_notification(
    client, client_db, user_authentication, owner_api
):
    """Non-owner notifications with empty user_ids require api_notifications subscription."""
    auth = user_authentication.json
    user = _get_user_by_email(client_db, UT_USER_EMAIL)
    user.api_notifications = str(owner_api.id)
    client_db.session.add(user)
    client_db.session.commit()

    note = NotificationModel(owner_api, "INFO", "sub title", "sub body", "", "http://sub.test")
    note.for_owners = 0
    note.user_ids = ""
    client_db.session.add(note)
    client_db.session.commit()
    note_id = note.id

    response = _get_notifications(client, auth)
    assert response.status_code == HTTPStatus.OK
    assert any(n.get("id") == note_id for n in response.get_json())


def test_user_notifications_get_targeted_by_user_ids(
    client, client_db, user_authentication, owner_api
):
    """Notification with user_ids containing this user is listed without subscription."""
    auth = user_authentication.json
    user = _get_user_by_email(client_db, UT_USER_EMAIL)
    user.api_notifications = ""
    client_db.session.add(user)
    client_db.session.commit()

    note = NotificationModel(owner_api, "INFO", "direct title", "direct body", "", "http://direct.test")
    note.for_owners = 0
    note.user_ids = f"[{user.id}]"
    client_db.session.add(note)
    client_db.session.commit()
    note_id = note.id

    response = _get_notifications(client, auth)
    assert response.status_code == HTTPStatus.OK
    assert any(n.get("id") == note_id for n in response.get_json())


@pytest.mark.parametrize("mandatory_field", ["api-id", "notifications", "token", "user-id"])
def test_user_notifications_put_missing_mandatory_fields(
    client, user_authentication, owner_api, mandatory_field
):
    auth = user_authentication.json
    body = {
        "api-id": owner_api.id,
        "notifications": 1,
        "user-id": auth["id"],
        "token": auth["token"],
    }
    del body[mandatory_field]
    response = client.put(_USER_NOTIFICATIONS_URL, json=body)
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_user_notifications_put_unauthorized(client, user_authentication, owner_api):
    auth = user_authentication.json
    response = client.put(
        _USER_NOTIFICATIONS_URL,
        json={
            "api-id": owner_api.id,
            "notifications": 1,
            "user-id": auth["id"],
            "token": "not-the-token",
        },
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED


def test_user_notifications_put_subscribe_and_unsubscribe(
    client, client_db, user_authentication, owner_api
):
    """PUT toggles UserModel.api_notifications for the given api id."""
    auth = user_authentication.json
    user = _get_user_by_email(client_db, UT_USER_EMAIL)
    assert user.api_notifications in (None, "")

    on = _put_notifications(client, auth, owner_api.id, 1)
    assert on.status_code == HTTPStatus.OK
    client_db.session.refresh(user)
    assert str(owner_api.id) in (user.api_notifications or "").replace(" ", "").split(",")

    off = _put_notifications(client, auth, owner_api.id, 0)
    assert off.status_code == HTTPStatus.OK
    client_db.session.refresh(user)
    assert str(owner_api.id) not in (user.api_notifications or "").replace(" ", "").split(",")


@pytest.mark.parametrize("mandatory_field", ["token", "user-id"])
def test_user_notifications_delete_missing_mandatory_fields(
    client, user_authentication, mandatory_field
):
    auth = user_authentication.json
    body = {"user-id": auth["id"], "token": auth["token"]}
    del body[mandatory_field]
    response = client.delete(_USER_NOTIFICATIONS_URL, json=body)
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_user_notifications_delete_unauthorized(client, user_authentication):
    auth = user_authentication.json
    response = client.delete(
        _USER_NOTIFICATIONS_URL,
        json={"user-id": auth["id"], "token": "wrong"},
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED


def test_user_notifications_delete_without_id_marks_matching_notifications_read(
    client, client_db, user_authentication, owner_api
):
    """DELETE without id marks notifications for subscribed APIs (and global) as read."""
    auth = user_authentication.json
    user = _get_user_by_email(client_db, UT_USER_EMAIL)
    user.api_notifications = str(owner_api.id)
    client_db.session.add(user)

    g = NotificationModel(None, "INFO", "g2", "b", "", "")
    a = NotificationModel(owner_api, "INFO", "a2", "b", "", "")
    a.for_owners = 0
    a.user_ids = ""
    client_db.session.add(g)
    client_db.session.add(a)
    client_db.session.commit()
    gid, aid = g.id, a.id

    before = _get_notifications(client, auth)
    assert before.status_code == HTTPStatus.OK
    ids_before = {n["id"] for n in before.get_json()}
    assert gid in ids_before
    assert aid in ids_before

    clear = _delete_notifications(client, auth, notification_id=None)
    assert clear.status_code == HTTPStatus.OK

    after = _get_notifications(client, auth)
    assert after.status_code == HTTPStatus.OK
    ids_after = {n["id"] for n in after.get_json()}
    assert gid not in ids_after
    assert aid not in ids_after
