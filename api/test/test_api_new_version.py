"""HTTP tests for ApiNewVersion (POST /apis/new-version)."""
import os
from http import HTTPStatus

import pytest

from db.models.api import ApiModel
from db.models.api_sw_requirement import ApiSwRequirementModel
from db.models.sw_requirement import SwRequirementModel
from db.models.user import UserModel

_NEW_VERSION_URL = "/apis/new-version"
_APIS_URL = "/apis"


def _auth_dict(user_authentication):
    return {"id": user_authentication.json["id"], "token": user_authentication.json["token"]}


def _create_api_via_http(client, auth, utilities, library="test_lib_new_version", library_version="1"):
    """Register a new software component via POST /apis; return (response, chosen api name)."""
    api_name = f"test_api_new_version_{utilities.generate_random_hex_string8()}"
    payload = {
        "user-id": auth["id"],
        "token": auth["token"],
        "action": "add",
        "api": api_name,
        "category": "test_category_nv",
        "library": library,
        "library-version": library_version,
        "raw-specification-url": os.path.realpath(__file__),
        "tags": "nv_tag",
        "implementation-file": "",
        "implementation-file-from-row": 0,
        "implementation-file-to-row": 1,
    }
    response = client.post(_APIS_URL, json=payload)
    return response, api_name


def _post_new_version(client, auth, api_id, new_version):
    return client.post(
        _NEW_VERSION_URL,
        json={
            "user-id": auth["id"],
            "token": auth["token"],
            "api-id": api_id,
            "new-version": new_version,
        },
    )


def test_api_new_version_post_created(client, user_authentication, utilities):
    """Successful POST creates a new row with the requested library version and copies metadata."""
    auth = _auth_dict(user_authentication)
    created, api_name = _create_api_via_http(client, auth, utilities)
    assert created.status_code == HTTPStatus.CREATED

    listed = client.get(_APIS_URL)
    assert listed.status_code == HTTPStatus.OK
    apis = listed.get_json()["apis"]
    src = next(a for a in apis if a["api"] == api_name)
    src_id = src["id"]

    response = _post_new_version(client, auth, src_id, "2.0.0")
    assert response.status_code == HTTPStatus.CREATED
    body = response.get_json()
    assert body["library_version"] == "2.0.0"
    assert body["api"] == src["api"]
    assert body["library"] == src["library"]
    assert body["raw_specification_url"] == src["raw_specification_url"]
    assert body["category"] == src["category"]
    assert body["tags"] == src["tags"]
    assert body["id"] != src_id


def test_api_new_version_post_clones_api_sw_requirement_mappings(
    client, client_db, user_authentication, utilities
):
    """Work items linked to the source API are forked onto the new version (ApiSwRequirement)."""
    auth = _auth_dict(user_authentication)
    created, api_name = _create_api_via_http(client, auth, utilities)
    assert created.status_code == HTTPStatus.CREATED

    listed = client.get(_APIS_URL)
    src = next(a for a in listed.get_json()["apis"] if a["api"] == api_name)
    src_id = src["id"]

    user = client_db.session.query(UserModel).filter(UserModel.id == auth["id"]).one()
    sr = SwRequirementModel(
        f"SR_NV_{utilities.generate_random_hex_string8()}",
        "new version clone SR",
        user,
    )
    client_db.session.add(sr)
    client_db.session.flush()
    mapping = ApiSwRequirementModel(
        client_db.session.query(ApiModel).filter(ApiModel.id == src_id).one(),
        sr,
        "sec",
        0,
        10,
        user,
    )
    client_db.session.add(mapping)
    client_db.session.commit()

    response = _post_new_version(client, auth, src_id, "v-next")
    assert response.status_code == HTTPStatus.CREATED
    new_id = response.get_json()["id"]

    old_count = (
        client_db.session.query(ApiSwRequirementModel)
        .filter(ApiSwRequirementModel.api_id == src_id)
        .count()
    )
    new_count = (
        client_db.session.query(ApiSwRequirementModel)
        .filter(ApiSwRequirementModel.api_id == new_id)
        .count()
    )
    assert old_count == 1
    assert new_count == 1


def test_api_new_version_post_conflict_when_version_exists(client, user_authentication, utilities):
    """Second POST targeting an already used (api, library, library_version) returns 409 CONFLICT."""
    auth = _auth_dict(user_authentication)
    created, api_name = _create_api_via_http(client, auth, utilities)
    assert created.status_code == HTTPStatus.CREATED

    listed = client.get(_APIS_URL)
    src = next(a for a in listed.get_json()["apis"] if a["api"] == api_name)

    first = _post_new_version(client, auth, src["id"], "9.9.9")
    assert first.status_code == HTTPStatus.CREATED

    conflict = _post_new_version(client, auth, src["id"], "9.9.9")
    assert conflict.status_code == HTTPStatus.CONFLICT


def test_api_new_version_post_bad_request_missing_new_version(client, user_authentication, utilities):
    """Inner handler requires new-version in addition to decorator fields."""
    auth = _auth_dict(user_authentication)
    created, api_name = _create_api_via_http(client, auth, utilities)
    assert created.status_code == HTTPStatus.CREATED

    listed = client.get(_APIS_URL)
    src = next(a for a in listed.get_json()["apis"] if a["api"] == api_name)

    response = client.post(
        _NEW_VERSION_URL,
        json={
            "user-id": auth["id"],
            "token": auth["token"],
            "api-id": src["id"],
        },
    )
    assert response.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.parametrize("mandatory_field", ["api-id", "token", "user-id"])
def test_api_new_version_post_bad_request_missing_decorator_fields(
    client, user_authentication, mandatory_field
):
    """Permission decorator requires api-id, user-id, and token."""
    auth = _auth_dict(user_authentication)
    payload = {
        "user-id": auth["id"],
        "token": auth["token"],
        "api-id": 1,
        "new-version": "1",
    }
    del payload[mandatory_field]
    response = client.post(_NEW_VERSION_URL, json=payload)
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_api_new_version_post_not_found_unknown_api_id(client, user_authentication):
    """Nonexistent api-id yields Sw component not found (404)."""
    auth = _auth_dict(user_authentication)
    response = _post_new_version(client, auth, 999_999, "1.0.1")
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_api_new_version_post_unauthorized_read_denied(
    client, client_db, user_authentication, reader_authentication, utilities
):
    """User listed in read_denials cannot call the endpoint even though it only requires read."""
    auth = _auth_dict(user_authentication)
    created, api_name = _create_api_via_http(client, auth, utilities)
    assert created.status_code == HTTPStatus.CREATED

    listed = client.get(_APIS_URL)
    src = next(a for a in listed.get_json()["apis"] if a["api"] == api_name)

    api_row = client_db.session.query(ApiModel).filter(ApiModel.id == src["id"]).one()
    reader_id = reader_authentication.json["id"]
    api_row.read_denials = f"[{reader_id}]"
    client_db.session.commit()

    blocked = _post_new_version(
        client,
        {"id": reader_id, "token": reader_authentication.json["token"]},
        src["id"],
        "blocked-version",
    )
    assert blocked.status_code == HTTPStatus.UNAUTHORIZED
