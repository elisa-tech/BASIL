import os
import pytest
import tempfile
from http import HTTPStatus

from db.models.user import UserModel
from db.models.api import ApiModel
from conftest import UT_USER_EMAIL


_MAPPING_API_SPECIFICATIONS_URL = "/mapping/api/specifications"

_UT_API_NAME = "ut_api"
_UT_API_LIBRARY = "ut_api_library"
_UT_API_LIBRARY_VERSION = "v1.0.0"
_UT_API_CATEGORY = "ut_api_category"
_UT_API_IMPLEMENTATION_FILE_FROM_ROW = 0
_UT_API_IMPLEMENTATION_FILE_TO_ROW = 42
_UT_API_TAGS = "ut_api_tags"

_UT_API_RAW_SPEC = (
    f"BASIL UT: Full specification content."
    f" Used for {_MAPPING_API_SPECIFICATIONS_URL}."
)
_UT_API_RAW_RESTRICTED_SPEC = (
    'BASIL UT: "Reader" user is not able to read this API.'
    f" Used for {_MAPPING_API_SPECIFICATIONS_URL}."
)

_ALL_MAPPING_KEYS = ["documents", "test_cases", "test_specifications", "sw_requirements", "justifications"]


def _create_api_with_spec(client_db, utilities, raw_spec_content):
    user = client_db.session.query(UserModel).filter(UserModel.email == UT_USER_EMAIL).one()

    raw_spec = tempfile.NamedTemporaryFile(mode="w", delete=False)
    raw_spec.write(raw_spec_content)
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


@pytest.fixture()
def api_db(client_db, ut_user_db, utilities):
    """Create an Api whose specification can be read."""
    ut_api, spec_path = _create_api_with_spec(client_db, utilities, _UT_API_RAW_SPEC)
    yield ut_api
    if os.path.isfile(spec_path):
        os.remove(spec_path)


@pytest.fixture()
def restricted_api_db(client_db, ut_user_db, ut_reader_user_db, utilities):
    """Create an Api with read restriction for the 'reader' user."""
    ut_api, spec_path = _create_api_with_spec(client_db, utilities, _UT_API_RAW_RESTRICTED_SPEC)
    ut_api.read_denials = f"[{ut_reader_user_db.id}]"
    client_db.session.commit()
    yield ut_api
    if os.path.isfile(spec_path):
        os.remove(spec_path)


@pytest.fixture()
def api_missing_spec_db(client_db, ut_user_db, utilities):
    """Create an Api whose raw_specification_url points to a nonexistent file."""
    user = client_db.session.query(UserModel).filter(UserModel.email == UT_USER_EMAIL).one()
    ut_api = ApiModel(
        _UT_API_NAME + "#" + utilities.generate_random_hex_string8(),
        _UT_API_LIBRARY,
        _UT_API_LIBRARY_VERSION,
        "/tmp/basil_ut_nonexistent_spec_" + utilities.generate_random_hex_string8(),
        _UT_API_CATEGORY,
        utilities.generate_random_hex_string8(),
        "stub.impl",
        _UT_API_IMPLEMENTATION_FILE_FROM_ROW,
        _UT_API_IMPLEMENTATION_FILE_TO_ROW,
        _UT_API_TAGS,
        user,
    )
    client_db.session.add(ut_api)
    client_db.session.commit()
    yield ut_api


def test_login(user_authentication):
    assert user_authentication.status_code == HTTPStatus.OK


# --- GET ---


def test_get_unauthorized_ok(client, api_db):
    """GET without credentials on a non-restricted Api succeeds."""
    response = client.get(_MAPPING_API_SPECIFICATIONS_URL, query_string={"api-id": api_db.id})
    assert response.status_code == HTTPStatus.OK
    assert "mapped" in response.json
    assert "unmapped" in response.json


def test_get_unauthorized_fail(client, restricted_api_db):
    """GET without credentials on a restricted Api is rejected."""
    response = client.get(_MAPPING_API_SPECIFICATIONS_URL, query_string={"api-id": restricted_api_db.id})
    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert "mapped" not in response.json
    assert "unmapped" not in response.json


def test_get_authorized_restricted_fail(client, reader_authentication, restricted_api_db):
    """GET as the denied reader on a restricted Api is rejected."""
    get_query = {
        "user-id": reader_authentication.json["id"],
        "token": reader_authentication.json["token"],
        "api-id": restricted_api_db.id,
    }
    response = client.get(_MAPPING_API_SPECIFICATIONS_URL, query_string=get_query)
    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert "mapped" not in response.json
    assert "unmapped" not in response.json


def test_get_authorized_restricted_ok(client, user_authentication, restricted_api_db):
    """GET as the Api author on a restricted Api succeeds."""
    get_query = {
        "user-id": user_authentication.json["id"],
        "token": user_authentication.json["token"],
        "api-id": restricted_api_db.id,
    }
    response = client.get(_MAPPING_API_SPECIFICATIONS_URL, query_string=get_query)
    assert response.status_code == HTTPStatus.OK
    assert "mapped" in response.json
    assert "unmapped" in response.json


@pytest.mark.usefixtures("api_db")
def test_get_incorrect_request(client, user_authentication):
    """GET without api-id returns BAD_REQUEST."""
    get_query = {
        "user-id": user_authentication.json["id"],
        "token": user_authentication.json["token"],
    }
    response = client.get(_MAPPING_API_SPECIFICATIONS_URL, query_string=get_query)
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert "mapped" not in response.json
    assert "unmapped" not in response.json


@pytest.mark.usefixtures("api_db")
def test_get_missing_api(client_db, client, user_authentication):
    """GET with a non-existent api-id returns NOT_FOUND."""
    non_existent_id = 42000
    assert client_db.session.query(ApiModel).get(non_existent_id) is None

    get_query = {
        "user-id": user_authentication.json["id"],
        "token": user_authentication.json["token"],
        "api-id": non_existent_id,
    }
    response = client.get(_MAPPING_API_SPECIFICATIONS_URL, query_string=get_query)
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert "mapped" not in response.json
    assert "unmapped" not in response.json


def test_get_missing_specification_file(client, user_authentication, api_missing_spec_db):
    """GET when the raw specification file does not exist returns NOT_FOUND."""
    get_query = {
        "user-id": user_authentication.json["id"],
        "token": user_authentication.json["token"],
        "api-id": api_missing_spec_db.id,
    }
    response = client.get(_MAPPING_API_SPECIFICATIONS_URL, query_string=get_query)
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_get_returns_full_specification(client, api_db):
    """GET returns the full specification text as a single mapped section."""
    response = client.get(_MAPPING_API_SPECIFICATIONS_URL, query_string={"api-id": api_db.id})
    assert response.status_code == HTTPStatus.OK

    mapped = response.json["mapped"]
    assert len(mapped) == 1
    assert mapped[0]["section"] == _UT_API_RAW_SPEC
    assert mapped[0]["offset"] == 0
    assert mapped[0]["coverage"] == 0

    unmapped = response.json["unmapped"]
    assert len(unmapped) == 0


def test_get_mapped_section_has_empty_mapping_lists(client, api_db):
    """The single mapped section contains empty lists for all work-item types."""
    response = client.get(_MAPPING_API_SPECIFICATIONS_URL, query_string={"api-id": api_db.id})
    assert response.status_code == HTTPStatus.OK

    section = response.json["mapped"][0]
    for key in _ALL_MAPPING_KEYS:
        assert key in section, f"missing key '{key}' in mapped section"
        assert section[key] == []
