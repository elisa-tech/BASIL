import os
import pytest
import tempfile
from http import HTTPStatus

from db.models.user import UserModel
from db.models.api import ApiModel
from db.models.test_specification import TestSpecificationModel
from db.models.api_test_specification import ApiTestSpecificationModel
from conftest import UT_USER_EMAIL, UT_USER_NAME

_MAPPING_API_TEST_SPECIFICATIONS_URL = "/mapping/api/test-specifications"

_UT_API_NAME = "ut_api"
_UT_API_LIBRARY = "ut_api_library"
_UT_API_LIBRARY_VERSION = "v1.0.0"
_UT_API_CATEGORY = "ut_api_category"
_UT_API_IMPLEMENTATION_FILE_FROM_ROW = 0
_UT_API_IMPLEMENTATION_FILE_TO_ROW = 42
_UT_API_TAGS = "ut_api_tags"

_UT_API_SPEC_SECTION_NO_MAPPING = "This section has no mapping."
_UT_API_SPEC_SECTION_WITH_MAPPING = "This section has mapping."
_UT_API_SPEC_SECTION_TO_BE_MAPPED = "This section is to be mapped."
_UT_API_RAW_RESTRICTED_SPEC = (
    'BASIL UT: "Reader" user is not able to read this API.'
    f" Used for {_MAPPING_API_TEST_SPECIFICATIONS_URL}."
)
_UT_API_RAW_UNMAPPED_SPEC = (
    f"BASIL UT: {_UT_API_SPEC_SECTION_NO_MAPPING} "
    f"Used for {_MAPPING_API_TEST_SPECIFICATIONS_URL}."
)
_UT_API_RAW_MAPPED_SPEC = (
    f"BASIL UT: {_UT_API_SPEC_SECTION_WITH_MAPPING} {_UT_API_SPEC_SECTION_TO_BE_MAPPED} "
    f"Used for {_MAPPING_API_TEST_SPECIFICATIONS_URL}."
)

_UT_TEST_SPEC_TITLE = "UT Test Specification"
_UT_TEST_SPEC_PRECONDITIONS = "Test preconditions here"
_UT_TEST_SPEC_DESCRIPTION = "Test description here"
_UT_TEST_SPEC_EXPECTED_BEHAVIOR = "Expected behavior here"


def _filter_sections_mapped_by_test_specifications(mapped_sections):
    return [section for section in mapped_sections if section.get("test_specifications")]


def _get_sections_mapped_by_test_specifications(client, api_id, user_id=None, token=None):
    query = {"api-id": api_id}
    if user_id is not None:
        query["user-id"] = user_id
    if token is not None:
        query["token"] = token
    response = client.get(_MAPPING_API_TEST_SPECIFICATIONS_URL, query_string=query)
    assert response.status_code == HTTPStatus.OK
    return _filter_sections_mapped_by_test_specifications(response.json["mapped"])


def _get_mapped_test_specification(mapped_section):
    relation_id = mapped_section["test_specifications"][0]["relation_id"]
    test_specification = mapped_section["test_specifications"][0]["test_specification"]
    return relation_id, test_specification


def _assert_mapped_sections(mapped_sections, expected_section_texts):
    current = sorted([s["section"] for s in mapped_sections])
    expected = sorted(expected_section_texts)
    assert current == expected


def _test_specification_dict_kebab(client_db, utilities):
    """Return a new unique test specification payload with hyphenated keys (POST body)."""
    ut = TestSpecificationModel(
        f"{_UT_TEST_SPEC_TITLE} #{utilities.generate_random_hex_string8()}",
        _UT_TEST_SPEC_PRECONDITIONS,
        _UT_TEST_SPEC_DESCRIPTION,
        _UT_TEST_SPEC_EXPECTED_BEHAVIOR,
        client_db.session.query(UserModel).filter(UserModel.email == UT_USER_EMAIL).one(),
    )
    d = {k.replace("_", "-"): v for k, v in ut.as_dict().items()}
    d.pop("id", None)
    return d


def _test_specification_body_for_put(test_spec_dict):
    """Normalize nested test-specification dict for PUT (hyphenated keys)."""
    return {k.replace("_", "-"): v for k, v in test_spec_dict.items()}


def _create_software_component(client_db, utilities):
    user = client_db.session.query(UserModel).filter(UserModel.email == UT_USER_EMAIL).one()
    ut_api = ApiModel(
        _UT_API_NAME + "#" + utilities.generate_random_hex_string8(),
        _UT_API_LIBRARY,
        _UT_API_LIBRARY_VERSION,
        "stub.md",
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
    return ut_api


@pytest.fixture()
def restricted_api_db(client_db, ut_user_db, ut_reader_user_db, utilities):
    """Create Api with read restriction for \"reader\" """

    user = client_db.session.query(UserModel).filter(UserModel.email == UT_USER_EMAIL).one()

    raw_spec = tempfile.NamedTemporaryFile(mode="w", delete=False)
    raw_spec.write(_UT_API_RAW_RESTRICTED_SPEC)
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
    ut_api.read_denials = f"[{ut_reader_user_db.id}]"
    client_db.session.add(ut_api)
    client_db.session.commit()

    yield ut_api

    if os.path.isfile(raw_spec.name):
        os.remove(raw_spec.name)


@pytest.fixture()
def unmapped_api_db(client_db, ut_user_db, utilities):
    """Create Api with no mapped test specification sections."""

    user = client_db.session.query(UserModel).filter(UserModel.email == UT_USER_EMAIL).one()

    raw_spec = tempfile.NamedTemporaryFile(mode="w", delete=False)
    raw_spec.write(_UT_API_RAW_UNMAPPED_SPEC)
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

    yield ut_api

    if os.path.isfile(raw_spec.name):
        os.remove(raw_spec.name)


@pytest.fixture()
def mapped_api_db(client_db, ut_user_db, utilities):
    """Create Api with one Api–Test Specification mapping."""

    user = client_db.session.query(UserModel).filter(UserModel.email == UT_USER_EMAIL).one()

    raw_spec = tempfile.NamedTemporaryFile(mode="w", delete=False)
    raw_spec.write(_UT_API_RAW_MAPPED_SPEC)
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
    ut_test_specification = TestSpecificationModel(
        f"SW req TS #{utilities.generate_random_hex_string8()}",
        _UT_TEST_SPEC_PRECONDITIONS,
        _UT_TEST_SPEC_DESCRIPTION,
        _UT_TEST_SPEC_EXPECTED_BEHAVIOR,
        user,
    )
    ut_api_ts_mapping = ApiTestSpecificationModel(
        ut_api,
        ut_test_specification,
        _UT_API_SPEC_SECTION_WITH_MAPPING,
        _UT_API_RAW_MAPPED_SPEC.find(_UT_API_SPEC_SECTION_WITH_MAPPING),
        0,
        user,
    )

    client_db.session.add(ut_api)
    client_db.session.add(ut_test_specification)
    client_db.session.add(ut_api_ts_mapping)
    client_db.session.commit()

    yield ut_api

    if os.path.isfile(raw_spec.name):
        os.remove(raw_spec.name)


@pytest.fixture()
def test_specification_db(client_db, ut_user_db, utilities):
    """Standalone test specification (not yet mapped to this API in fixtures)."""

    user = client_db.session.query(UserModel).filter(UserModel.email == UT_USER_EMAIL).one()
    ut_ts = TestSpecificationModel(
        f"{_UT_TEST_SPEC_TITLE}_standalone_{utilities.generate_random_hex_string8()}",
        _UT_TEST_SPEC_PRECONDITIONS,
        _UT_TEST_SPEC_DESCRIPTION,
        _UT_TEST_SPEC_EXPECTED_BEHAVIOR,
        user,
    )
    client_db.session.add(ut_ts)
    client_db.session.commit()
    yield ut_ts


def test_login(user_authentication):
    """Just ensure that the test user is logged in"""
    assert user_authentication.status_code == HTTPStatus.OK


# --- GET ---


def test_get_unauthorized_ok(client, unmapped_api_db):
    """Read API without read restrictions: GET is allowed for all users."""
    response = client.get(_MAPPING_API_TEST_SPECIFICATIONS_URL, query_string={"api-id": unmapped_api_db.id})
    assert response.status_code == HTTPStatus.OK
    assert "mapped" in response.json
    assert "unmapped" in response.json


def test_get_unauthorized_fail(client, restricted_api_db):
    """Read API with read restrictions: GET is not allowed for unauthorized users."""
    response = client.get(_MAPPING_API_TEST_SPECIFICATIONS_URL, query_string={"api-id": restricted_api_db.id})
    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert "mapped" not in response.json
    assert "unmapped" not in response.json


def test_get_authorized_restricted_fail(client, reader_authentication, restricted_api_db):
    """Read API with read restrictions for \"reader\": GET is not allowed for this user."""
    get_query = {
        "user-id": reader_authentication.json["id"],
        "token": reader_authentication.json["token"],
        "api-id": restricted_api_db.id,
    }
    response = client.get(_MAPPING_API_TEST_SPECIFICATIONS_URL, query_string=get_query)
    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert "mapped" not in response.json
    assert "unmapped" not in response.json


def test_get_authorized_restricted_ok(client, user_authentication, restricted_api_db):
    """Read API with read restrictions: GET is allowed for the author of the API."""
    get_query = {
        "user-id": user_authentication.json["id"],
        "token": user_authentication.json["token"],
        "api-id": restricted_api_db.id,
    }
    response = client.get(_MAPPING_API_TEST_SPECIFICATIONS_URL, query_string=get_query)
    assert response.status_code == HTTPStatus.OK
    assert "mapped" in response.json
    assert "unmapped" in response.json


@pytest.mark.usefixtures("unmapped_api_db")
def test_get_incorrect_request(client, user_authentication):
    """Read API without specification of the api-id."""
    get_query = {
        "user-id": user_authentication.json["id"],
        "token": user_authentication.json["token"],
    }
    response = client.get(_MAPPING_API_TEST_SPECIFICATIONS_URL, query_string=get_query)
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert "mapped" not in response.json
    assert "unmapped" not in response.json


@pytest.mark.usefixtures("unmapped_api_db")
def test_get_missing_api(client_db, client, user_authentication):
    """Read non-existent API."""
    non_existent_id = 42000
    assert client_db.session.query(ApiModel).get(non_existent_id) is None

    get_query = {
        "user-id": user_authentication.json["id"],
        "token": user_authentication.json["token"],
        "api-id": non_existent_id,
    }
    response = client.get(_MAPPING_API_TEST_SPECIFICATIONS_URL, query_string=get_query)
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert "mapped" not in response.json
    assert "unmapped" not in response.json


def test_get_mapped(client, mapped_api_db):
    """Nominal GET: one section with a test specification mapping."""
    response = client.get(_MAPPING_API_TEST_SPECIFICATIONS_URL, query_string={"api-id": mapped_api_db.id})
    assert response.status_code == HTTPStatus.OK
    mapped_sections = _filter_sections_mapped_by_test_specifications(response.json["mapped"])
    assert len(mapped_sections) == 1
    assert mapped_sections[0]["section"] == _UT_API_SPEC_SECTION_WITH_MAPPING


# --- POST ---


def test_post_unauthorized(client, client_db, unmapped_api_db, utilities):
    """Create mapping without authentication: not allowed."""
    assert len(_get_sections_mapped_by_test_specifications(client, unmapped_api_db.id)) == 0

    mapping_data = {
        "api-id": unmapped_api_db.id,
        "section": _UT_API_SPEC_SECTION_NO_MAPPING,
        "offset": _UT_API_RAW_UNMAPPED_SPEC.find(_UT_API_SPEC_SECTION_NO_MAPPING),
        "coverage": 0,
        "test-specification": _test_specification_dict_kebab(client_db, utilities),
    }
    response = client.post(_MAPPING_API_TEST_SPECIFICATIONS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.UNAUTHORIZED

    assert len(_get_sections_mapped_by_test_specifications(client, unmapped_api_db.id)) == 0


def test_post_restricted_write(client, client_db, reader_authentication, unmapped_api_db, utilities):
    """Create mapping as \"reader\": not allowed."""
    assert len(_get_sections_mapped_by_test_specifications(client, unmapped_api_db.id)) == 0

    mapping_data = {
        "user-id": reader_authentication.json["id"],
        "token": reader_authentication.json["token"],
        "api-id": unmapped_api_db.id,
        "section": _UT_API_SPEC_SECTION_NO_MAPPING,
        "offset": _UT_API_RAW_UNMAPPED_SPEC.find(_UT_API_SPEC_SECTION_NO_MAPPING),
        "coverage": 0,
        "test-specification": _test_specification_dict_kebab(client_db, utilities),
    }
    response = client.post(_MAPPING_API_TEST_SPECIFICATIONS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.UNAUTHORIZED

    assert len(_get_sections_mapped_by_test_specifications(client, unmapped_api_db.id)) == 0


@pytest.mark.parametrize(
    "mandatory_field",
    ["api-id", "section", "coverage", "test-specification"],
)
def test_post_incomplete_request(
    client, client_db, user_authentication, unmapped_api_db, utilities, mandatory_field
):
    """Create mapping without a mandatory top-level field."""
    assert len(_get_sections_mapped_by_test_specifications(client, unmapped_api_db.id)) == 0

    mapping_data = {
        "user-id": user_authentication.json["id"],
        "token": user_authentication.json["token"],
        "api-id": unmapped_api_db.id,
        "section": _UT_API_SPEC_SECTION_NO_MAPPING,
        "offset": _UT_API_RAW_UNMAPPED_SPEC.find(_UT_API_SPEC_SECTION_NO_MAPPING),
        "coverage": 0,
        "test-specification": _test_specification_dict_kebab(client_db, utilities),
    }
    mapping_data.pop(mandatory_field)
    response = client.post(_MAPPING_API_TEST_SPECIFICATIONS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.BAD_REQUEST

    assert len(_get_sections_mapped_by_test_specifications(client, unmapped_api_db.id)) == 0


@pytest.mark.usefixtures("unmapped_api_db")
def test_post_missing_api(client_db, client, user_authentication, utilities):
    """Create mapping for non-existent API."""
    non_existent_id = 42000
    assert client_db.session.query(ApiModel).get(non_existent_id) is None

    mapping_data = {
        "user-id": user_authentication.json["id"],
        "token": user_authentication.json["token"],
        "api-id": non_existent_id,
        "section": _UT_API_SPEC_SECTION_NO_MAPPING,
        "offset": _UT_API_RAW_UNMAPPED_SPEC.find(_UT_API_SPEC_SECTION_NO_MAPPING),
        "coverage": 0,
        "test-specification": _test_specification_dict_kebab(client_db, utilities),
    }
    response = client.post(_MAPPING_API_TEST_SPECIFICATIONS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_post_missing_test_specification(client_db, client, user_authentication, unmapped_api_db):
    """Create mapping with non-existent test specification id."""
    assert len(_get_sections_mapped_by_test_specifications(client, unmapped_api_db.id)) == 0

    non_existent_id = 42000
    assert client_db.session.query(TestSpecificationModel).get(non_existent_id) is None

    mapping_data = {
        "user-id": user_authentication.json["id"],
        "token": user_authentication.json["token"],
        "api-id": unmapped_api_db.id,
        "section": _UT_API_SPEC_SECTION_NO_MAPPING,
        "offset": _UT_API_RAW_UNMAPPED_SPEC.find(_UT_API_SPEC_SECTION_NO_MAPPING),
        "coverage": 0,
        "test-specification": {"id": non_existent_id},
    }
    response = client.post(_MAPPING_API_TEST_SPECIFICATIONS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.NOT_FOUND

    assert len(_get_sections_mapped_by_test_specifications(client, unmapped_api_db.id)) == 0


def test_post_existing_test_specification_ok(client, user_authentication, unmapped_api_db, test_specification_db):
    """Map an existing test specification by id."""
    assert len(_get_sections_mapped_by_test_specifications(client, unmapped_api_db.id)) == 0

    mapping_data = {
        "user-id": user_authentication.json["id"],
        "token": user_authentication.json["token"],
        "api-id": unmapped_api_db.id,
        "section": _UT_API_SPEC_SECTION_NO_MAPPING,
        "offset": _UT_API_RAW_UNMAPPED_SPEC.find(_UT_API_SPEC_SECTION_NO_MAPPING),
        "coverage": 0,
        "test-specification": {"id": test_specification_db.id},
    }
    response = client.post(_MAPPING_API_TEST_SPECIFICATIONS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.CREATED

    mapped_sections = _get_sections_mapped_by_test_specifications(
        client,
        unmapped_api_db.id,
        user_authentication.json["id"],
        user_authentication.json["token"],
    )
    assert len(mapped_sections) == 1
    assert mapped_sections[0]["section"] == _UT_API_SPEC_SECTION_NO_MAPPING
    assert mapped_sections[0]["offset"] == _UT_API_RAW_UNMAPPED_SPEC.find(_UT_API_SPEC_SECTION_NO_MAPPING)
    tss = mapped_sections[0]["test_specifications"]
    assert len(tss) == 1
    assert tss[0]["test_specification"]["title"] == test_specification_db.title
    assert tss[0]["created_by"] == UT_USER_NAME


def test_post_existing_test_specification_conflict(client, user_authentication, mapped_api_db):
    """Duplicate mapping (same api, test spec id, section, offset): conflict."""
    api_id = mapped_api_db.id
    mapped_sections = _get_sections_mapped_by_test_specifications(client, api_id)
    _assert_mapped_sections(mapped_sections, [_UT_API_SPEC_SECTION_WITH_MAPPING])

    _, ts = _get_mapped_test_specification(mapped_sections[0])
    mapping_data = {
        "user-id": user_authentication.json["id"],
        "token": user_authentication.json["token"],
        "api-id": api_id,
        "section": _UT_API_SPEC_SECTION_WITH_MAPPING,
        "offset": _UT_API_RAW_MAPPED_SPEC.find(_UT_API_SPEC_SECTION_WITH_MAPPING),
        "coverage": 0,
        "test-specification": {"id": ts["id"]},
    }
    response = client.post(_MAPPING_API_TEST_SPECIFICATIONS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.CONFLICT

    mapped_sections = _get_sections_mapped_by_test_specifications(client, api_id)
    assert len(mapped_sections) == 1
    assert len(mapped_sections[0]["test_specifications"]) == 1


def test_post_new_test_specification_ok(
    client, client_db, user_authentication, unmapped_api_db, utilities
):
    """Create a new test specification and mapping in one request."""
    api_id = unmapped_api_db.id
    assert len(_get_sections_mapped_by_test_specifications(client, api_id)) == 0

    ts_body = _test_specification_dict_kebab(client_db, utilities)
    mapping_data = {
        "user-id": user_authentication.json["id"],
        "token": user_authentication.json["token"],
        "api-id": api_id,
        "section": _UT_API_SPEC_SECTION_NO_MAPPING,
        "offset": _UT_API_RAW_UNMAPPED_SPEC.find(_UT_API_SPEC_SECTION_NO_MAPPING),
        "coverage": 0,
        "test-specification": ts_body,
    }
    response = client.post(_MAPPING_API_TEST_SPECIFICATIONS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.CREATED

    mapped_sections = _get_sections_mapped_by_test_specifications(
        client,
        api_id,
        user_authentication.json["id"],
        user_authentication.json["token"],
    )
    assert len(mapped_sections) == 1
    assert mapped_sections[0]["section"] == _UT_API_SPEC_SECTION_NO_MAPPING
    tss = mapped_sections[0]["test_specifications"]
    assert len(tss) == 1
    assert tss[0]["test_specification"]["title"] == ts_body["title"]
    assert tss[0]["created_by"] == UT_USER_NAME


def test_post_new_test_specification_conflict(client, user_authentication, mapped_api_db, utilities):
    """POST new test specification with same content as an existing one: conflict."""
    api_id = mapped_api_db.id
    mapped_sections = _get_sections_mapped_by_test_specifications(client, api_id)
    _, ts = _get_mapped_test_specification(mapped_sections[0])

    mapping_data = {
        "user-id": user_authentication.json["id"],
        "token": user_authentication.json["token"],
        "api-id": api_id,
        "section": _UT_API_SPEC_SECTION_TO_BE_MAPPED,
        "offset": _UT_API_RAW_MAPPED_SPEC.find(_UT_API_SPEC_SECTION_TO_BE_MAPPED),
        "coverage": 0,
        "test-specification": {
            "title": ts["title"],
            "preconditions": ts["preconditions"],
            "test-description": ts["test_description"],
            "expected-behavior": ts["expected_behavior"],
        },
    }
    response = client.post(_MAPPING_API_TEST_SPECIFICATIONS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.CONFLICT

    mapped_sections = _get_sections_mapped_by_test_specifications(client, api_id)
    assert len(mapped_sections) == 1


@pytest.mark.parametrize(
    "mandatory_field",
    ["title", "preconditions", "test-description", "expected-behavior", "*"],
)
def test_post_new_test_specification_incomplete(
    client, client_db, user_authentication, unmapped_api_db, utilities, mandatory_field
):
    """Create mapping without a mandatory test-specification field."""
    assert len(_get_sections_mapped_by_test_specifications(client, unmapped_api_db.id)) == 0

    ts_body = _test_specification_dict_kebab(client_db, utilities)
    if mandatory_field == "*":
        ts_body = {}
    else:
        ts_body.pop(mandatory_field, None)

    mapping_data = {
        "user-id": user_authentication.json["id"],
        "token": user_authentication.json["token"],
        "api-id": unmapped_api_db.id,
        "section": _UT_API_SPEC_SECTION_NO_MAPPING,
        "offset": _UT_API_RAW_UNMAPPED_SPEC.find(_UT_API_SPEC_SECTION_NO_MAPPING),
        "coverage": 0,
        "test-specification": ts_body,
    }
    response = client.post(_MAPPING_API_TEST_SPECIFICATIONS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.BAD_REQUEST

    assert len(_get_sections_mapped_by_test_specifications(client, unmapped_api_db.id)) == 0


def test_post_add_second_test_specification(client, client_db, user_authentication, mapped_api_db, utilities):
    """Map a second test specification to the same section."""
    api_id = mapped_api_db.id
    mapped_sections = _get_sections_mapped_by_test_specifications(client, api_id)
    _assert_mapped_sections(mapped_sections, [_UT_API_SPEC_SECTION_WITH_MAPPING])
    assert len(mapped_sections[0]["test_specifications"]) == 1

    mapping_data = {
        "user-id": user_authentication.json["id"],
        "token": user_authentication.json["token"],
        "api-id": api_id,
        "section": _UT_API_SPEC_SECTION_WITH_MAPPING,
        "offset": _UT_API_RAW_MAPPED_SPEC.find(_UT_API_SPEC_SECTION_WITH_MAPPING),
        "coverage": 50,
        "test-specification": _test_specification_dict_kebab(client_db, utilities),
    }
    response = client.post(_MAPPING_API_TEST_SPECIFICATIONS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.CREATED

    mapped_sections = _get_sections_mapped_by_test_specifications(client, api_id)
    assert len(mapped_sections) == 1
    assert len(mapped_sections[0]["test_specifications"]) == 2
    titles = [x["test_specification"]["title"] for x in mapped_sections[0]["test_specifications"]]
    assert titles[0] != titles[1]


# --- PUT ---


def test_put_unauthorized(client, mapped_api_db):
    """Update mapping without authentication: not allowed."""
    mapped_sections = _get_sections_mapped_by_test_specifications(client, mapped_api_db.id)
    _assert_mapped_sections(mapped_sections, [_UT_API_SPEC_SECTION_WITH_MAPPING])

    relation_id, ts = _get_mapped_test_specification(mapped_sections[0])
    mapping_data = {
        "relation-id": relation_id,
        "api-id": mapped_api_db.id,
        "section": _UT_API_SPEC_SECTION_TO_BE_MAPPED,
        "offset": _UT_API_RAW_MAPPED_SPEC.find(_UT_API_SPEC_SECTION_TO_BE_MAPPED),
        "coverage": 0,
        "test-specification": _test_specification_body_for_put(ts),
    }
    response = client.put(_MAPPING_API_TEST_SPECIFICATIONS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.UNAUTHORIZED

    mapped_sections = _get_sections_mapped_by_test_specifications(client, mapped_api_db.id)
    _assert_mapped_sections(mapped_sections, [_UT_API_SPEC_SECTION_WITH_MAPPING])


def test_put_restricted_write(client, reader_authentication, mapped_api_db):
    """Update mapping as reader: not allowed."""
    mapped_sections = _get_sections_mapped_by_test_specifications(client, mapped_api_db.id)
    relation_id, ts = _get_mapped_test_specification(mapped_sections[0])
    mapping_data = {
        "user-id": reader_authentication.json["id"],
        "token": reader_authentication.json["token"],
        "relation-id": relation_id,
        "api-id": mapped_api_db.id,
        "section": _UT_API_SPEC_SECTION_TO_BE_MAPPED,
        "offset": _UT_API_RAW_MAPPED_SPEC.find(_UT_API_SPEC_SECTION_TO_BE_MAPPED),
        "coverage": 0,
        "test-specification": _test_specification_body_for_put(ts),
    }
    response = client.put(_MAPPING_API_TEST_SPECIFICATIONS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.UNAUTHORIZED

    mapped_sections = _get_sections_mapped_by_test_specifications(client, mapped_api_db.id)
    _assert_mapped_sections(mapped_sections, [_UT_API_SPEC_SECTION_WITH_MAPPING])


@pytest.mark.parametrize(
    "mandatory_field",
    ["api-id", "section", "coverage", "test-specification", "relation-id"],
)
def test_put_incomplete_request(client, user_authentication, mapped_api_db, mandatory_field):
    """Update mapping without a mandatory field."""
    mapped_sections = _get_sections_mapped_by_test_specifications(client, mapped_api_db.id)
    relation_id, ts = _get_mapped_test_specification(mapped_sections[0])
    mapping_data = {
        "user-id": user_authentication.json["id"],
        "token": user_authentication.json["token"],
        "relation-id": relation_id,
        "api-id": mapped_api_db.id,
        "section": _UT_API_SPEC_SECTION_TO_BE_MAPPED,
        "offset": _UT_API_RAW_MAPPED_SPEC.find(_UT_API_SPEC_SECTION_TO_BE_MAPPED),
        "coverage": 0,
        "test-specification": _test_specification_body_for_put(ts),
    }
    mapping_data.pop(mandatory_field)
    response = client.put(_MAPPING_API_TEST_SPECIFICATIONS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.BAD_REQUEST

    mapped_sections = _get_sections_mapped_by_test_specifications(client, mapped_api_db.id)
    _assert_mapped_sections(mapped_sections, [_UT_API_SPEC_SECTION_WITH_MAPPING])


def test_put_missing_api(client_db, client, user_authentication, mapped_api_db):
    """Update mapping for non-existent API."""
    non_existent_id = 42000
    assert client_db.session.query(ApiModel).get(non_existent_id) is None

    mapped_sections = _get_sections_mapped_by_test_specifications(client, mapped_api_db.id)
    relation_id, ts = _get_mapped_test_specification(mapped_sections[0])
    mapping_data = {
        "user-id": user_authentication.json["id"],
        "token": user_authentication.json["token"],
        "relation-id": relation_id,
        "api-id": non_existent_id,
        "section": _UT_API_SPEC_SECTION_TO_BE_MAPPED,
        "offset": _UT_API_RAW_MAPPED_SPEC.find(_UT_API_SPEC_SECTION_TO_BE_MAPPED),
        "coverage": 0,
        "test-specification": _test_specification_body_for_put(ts),
    }
    response = client.put(_MAPPING_API_TEST_SPECIFICATIONS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_put_missing_relation(client_db, client, user_authentication, mapped_api_db):
    """Update non-existent ApiTestSpecification mapping relation."""
    non_existent_id = 42000
    assert client_db.session.query(ApiTestSpecificationModel).get(non_existent_id) is None

    mapped_sections = _get_sections_mapped_by_test_specifications(client, mapped_api_db.id)
    _, ts = _get_mapped_test_specification(mapped_sections[0])
    mapping_data = {
        "user-id": user_authentication.json["id"],
        "token": user_authentication.json["token"],
        "relation-id": non_existent_id,
        "api-id": mapped_api_db.id,
        "section": _UT_API_SPEC_SECTION_TO_BE_MAPPED,
        "offset": _UT_API_RAW_MAPPED_SPEC.find(_UT_API_SPEC_SECTION_TO_BE_MAPPED),
        "coverage": 0,
        "test-specification": _test_specification_body_for_put(ts),
    }
    response = client.put(_MAPPING_API_TEST_SPECIFICATIONS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.NOT_FOUND

    mapped_sections = _get_sections_mapped_by_test_specifications(client, mapped_api_db.id)
    _assert_mapped_sections(mapped_sections, [_UT_API_SPEC_SECTION_WITH_MAPPING])


def test_put_update_mapping_ok(client, user_authentication, mapped_api_db):
    """Update mapping section, offset, and coverage."""
    api_id = mapped_api_db.id
    mapped_sections = _get_sections_mapped_by_test_specifications(client, api_id)
    _assert_mapped_sections(mapped_sections, [_UT_API_SPEC_SECTION_WITH_MAPPING])

    relation_id, ts = _get_mapped_test_specification(mapped_sections[0])
    ts_put = _test_specification_body_for_put(ts)
    mapping_data = {
        "user-id": user_authentication.json["id"],
        "token": user_authentication.json["token"],
        "relation-id": relation_id,
        "api-id": api_id,
        "section": _UT_API_SPEC_SECTION_TO_BE_MAPPED,
        "offset": _UT_API_RAW_MAPPED_SPEC.find(_UT_API_SPEC_SECTION_TO_BE_MAPPED),
        "coverage": 0,
        "test-specification": ts_put,
    }
    response = client.put(_MAPPING_API_TEST_SPECIFICATIONS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.OK

    mapped_sections = _get_sections_mapped_by_test_specifications(client, api_id)
    assert len(mapped_sections) == 1
    assert mapped_sections[0]["section"] == _UT_API_SPEC_SECTION_TO_BE_MAPPED
    assert mapped_sections[0]["offset"] == _UT_API_RAW_MAPPED_SPEC.find(_UT_API_SPEC_SECTION_TO_BE_MAPPED)
    assert len(mapped_sections[0]["test_specifications"]) == 1

    mapping_data["coverage"] = 50
    response = client.put(_MAPPING_API_TEST_SPECIFICATIONS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.OK
    mapped_sections = _get_sections_mapped_by_test_specifications(client, api_id)
    assert mapped_sections[0]["covered"] == 50


def test_put_update_mapping_unchanged(client, user_authentication, mapped_api_db):
    """PUT with identical data."""
    api_id = mapped_api_db.id
    mapped_sections = _get_sections_mapped_by_test_specifications(client, api_id)
    relation_id, ts = _get_mapped_test_specification(mapped_sections[0])
    ts_put = _test_specification_body_for_put(ts)
    mapping_data = {
        "user-id": user_authentication.json["id"],
        "token": user_authentication.json["token"],
        "relation-id": relation_id,
        "api-id": api_id,
        "section": _UT_API_SPEC_SECTION_WITH_MAPPING,
        "offset": _UT_API_RAW_MAPPED_SPEC.find(_UT_API_SPEC_SECTION_WITH_MAPPING),
        "coverage": 0,
        "test-specification": ts_put,
    }
    response = client.put(_MAPPING_API_TEST_SPECIFICATIONS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.OK

    mapped_sections = _get_sections_mapped_by_test_specifications(client, api_id)
    _assert_mapped_sections(mapped_sections, [_UT_API_SPEC_SECTION_WITH_MAPPING])


def test_put_update_test_specification_fields(client, user_authentication, mapped_api_db, utilities):
    """Update test specification fields via the mapping PUT."""
    api_id = mapped_api_db.id
    mapped_sections = _get_sections_mapped_by_test_specifications(client, api_id)
    relation_id, ts = _get_mapped_test_specification(mapped_sections[0])
    new_title = f"Updated TS title {utilities.generate_random_hex_string8()}"
    ts["title"] = new_title
    mapping_data = {
        "user-id": user_authentication.json["id"],
        "token": user_authentication.json["token"],
        "relation-id": relation_id,
        "api-id": api_id,
        "section": _UT_API_SPEC_SECTION_WITH_MAPPING,
        "offset": _UT_API_RAW_MAPPED_SPEC.find(_UT_API_SPEC_SECTION_WITH_MAPPING),
        "coverage": 0,
        "test-specification": _test_specification_body_for_put(ts),
    }
    response = client.put(_MAPPING_API_TEST_SPECIFICATIONS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.OK

    mapped_sections = _get_sections_mapped_by_test_specifications(client, api_id)
    assert mapped_sections[0]["test_specifications"][0]["test_specification"]["title"] == new_title


# --- DELETE ---


def test_delete_unauthorized(client, mapped_api_db):
    """Delete mapping without authentication: not allowed."""
    mapped_sections = _get_sections_mapped_by_test_specifications(client, mapped_api_db.id)
    relation_id, _ = _get_mapped_test_specification(mapped_sections[0])
    mapping_data = {"relation-id": relation_id, "api-id": mapped_api_db.id}
    response = client.delete(_MAPPING_API_TEST_SPECIFICATIONS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.UNAUTHORIZED

    mapped_sections = _get_sections_mapped_by_test_specifications(client, mapped_api_db.id)
    assert len(mapped_sections) == 1


def test_delete_wrong_mapping(client_db, client, user_authentication, mapped_api_db, restricted_api_db, utilities):
    """Delete with wrong api-id: NOT_FOUND, UNAUTHORIZED, or BAD_REQUEST."""
    mapped_sections = _get_sections_mapped_by_test_specifications(client, mapped_api_db.id)
    relation_id, _ = _get_mapped_test_specification(mapped_sections[0])

    mapping_data = {"relation-id": relation_id, "api-id": 0}
    response = client.delete(_MAPPING_API_TEST_SPECIFICATIONS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.NOT_FOUND

    mapping_data = {"relation-id": relation_id, "api-id": restricted_api_db.id}
    response = client.delete(_MAPPING_API_TEST_SPECIFICATIONS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.UNAUTHORIZED

    other_api = _create_software_component(client_db, utilities)
    mapping_data = {
        "user-id": user_authentication.json["id"],
        "token": user_authentication.json["token"],
        "relation-id": relation_id,
        "api-id": other_api.id,
    }
    response = client.delete(_MAPPING_API_TEST_SPECIFICATIONS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.BAD_REQUEST

    mapped_sections = _get_sections_mapped_by_test_specifications(client, mapped_api_db.id)
    assert len(mapped_sections) == 1


def test_delete_restricted_write(client, reader_authentication, mapped_api_db):
    """Delete as reader: not allowed."""
    mapped_sections = _get_sections_mapped_by_test_specifications(client, mapped_api_db.id)
    relation_id, _ = _get_mapped_test_specification(mapped_sections[0])
    mapping_data = {
        "user-id": reader_authentication.json["id"],
        "token": reader_authentication.json["token"],
        "relation-id": relation_id,
        "api-id": mapped_api_db.id,
    }
    response = client.delete(_MAPPING_API_TEST_SPECIFICATIONS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.UNAUTHORIZED

    assert len(_get_sections_mapped_by_test_specifications(client, mapped_api_db.id)) == 1


@pytest.mark.parametrize("mandatory_field", ["api-id", "relation-id"])
def test_delete_incomplete_request(client, user_authentication, mapped_api_db, mandatory_field):
    """Delete without a mandatory field."""
    mapped_sections = _get_sections_mapped_by_test_specifications(client, mapped_api_db.id)
    relation_id, _ = _get_mapped_test_specification(mapped_sections[0])
    mapping_data = {
        "user-id": user_authentication.json["id"],
        "token": user_authentication.json["token"],
        "relation-id": relation_id,
        "api-id": mapped_api_db.id,
    }
    mapping_data.pop(mandatory_field)
    response = client.delete(_MAPPING_API_TEST_SPECIFICATIONS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.BAD_REQUEST

    assert len(_get_sections_mapped_by_test_specifications(client, mapped_api_db.id)) == 1


def test_delete_missing_api(client_db, client, user_authentication, mapped_api_db):
    """Delete mapping for non-existent API."""
    non_existent_id = 42000
    assert client_db.session.query(ApiModel).get(non_existent_id) is None

    mapped_sections = _get_sections_mapped_by_test_specifications(client, mapped_api_db.id)
    relation_id, _ = _get_mapped_test_specification(mapped_sections[0])
    mapping_data = {
        "user-id": user_authentication.json["id"],
        "token": user_authentication.json["token"],
        "relation-id": relation_id,
        "api-id": non_existent_id,
    }
    response = client.delete(_MAPPING_API_TEST_SPECIFICATIONS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_delete_missing_relation(client_db, client, user_authentication, mapped_api_db):
    """Delete non-existent relation id."""
    non_existent_id = 42000
    assert client_db.session.query(ApiTestSpecificationModel).get(non_existent_id) is None

    mapping_data = {
        "user-id": user_authentication.json["id"],
        "token": user_authentication.json["token"],
        "relation-id": non_existent_id,
        "api-id": mapped_api_db.id,
    }
    response = client.delete(_MAPPING_API_TEST_SPECIFICATIONS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.NOT_FOUND

    assert len(_get_sections_mapped_by_test_specifications(client, mapped_api_db.id)) == 1


def test_delete_ok(client, user_authentication, mapped_api_db):
    """Nominal delete."""
    api_id = mapped_api_db.id
    mapped_sections = _get_sections_mapped_by_test_specifications(client, api_id)
    relation_id, _ = _get_mapped_test_specification(mapped_sections[0])
    mapping_data = {
        "user-id": user_authentication.json["id"],
        "token": user_authentication.json["token"],
        "relation-id": relation_id,
        "api-id": api_id,
    }
    response = client.delete(_MAPPING_API_TEST_SPECIFICATIONS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.OK

    assert len(_get_sections_mapped_by_test_specifications(client, api_id)) == 0
