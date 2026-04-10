import os
import pytest
import tempfile
from http import HTTPStatus

from db.models.user import UserModel
from db.models.api import ApiModel
from db.models.test_case import TestCaseModel
from db.models.api_test_case import ApiTestCaseModel
from conftest import UT_USER_EMAIL, UT_USER_NAME

_MAPPING_API_TEST_CASES_URL = "/mapping/api/test-cases"

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
_UT_API_RAW_UNMAPPED_SPEC = f"BASIL UT: {_UT_API_SPEC_SECTION_NO_MAPPING} Used for {_MAPPING_API_TEST_CASES_URL}."
_UT_API_RAW_MAPPED_SPEC = (
    f"BASIL UT: {_UT_API_SPEC_SECTION_WITH_MAPPING} {_UT_API_SPEC_SECTION_TO_BE_MAPPED} "
    f"Used for {_MAPPING_API_TEST_CASES_URL}."
)
_UT_API_RAW_RESTRICTED_SPEC = (
    'BASIL UT: "Reader" user is not able to read this API.'
    f" Used for {_MAPPING_API_TEST_CASES_URL}."
)

_UT_TC_REPOSITORY = "https://github.com/example/repo"


def _write_spec_tempfile(spec_content: str) -> str:
    raw_spec = tempfile.NamedTemporaryFile(mode="w", delete=False)
    raw_spec.write(spec_content)
    raw_spec.close()
    return raw_spec.name


def _make_api_model(raw_spec_path: str, user, utilities) -> ApiModel:
    return ApiModel(
        _UT_API_NAME + "#" + utilities.generate_random_hex_string8(),
        _UT_API_LIBRARY,
        _UT_API_LIBRARY_VERSION,
        raw_spec_path,
        _UT_API_CATEGORY,
        utilities.generate_random_hex_string8(),
        raw_spec_path + "impl",
        _UT_API_IMPLEMENTATION_FILE_FROM_ROW,
        _UT_API_IMPLEMENTATION_FILE_TO_ROW,
        _UT_API_TAGS,
        user,
    )


def get_test_case_model(client_db, utilities):
    user = client_db.session.query(UserModel).filter(UserModel.email == UT_USER_EMAIL).one()
    return TestCaseModel(
        _UT_TC_REPOSITORY,
        f"tests/test_{utilities.generate_random_hex_string8()}.py",
        f"TC #{utilities.generate_random_hex_string8()}",
        "test case description for UT",
        user,
    )


def hyphenate_test_case_dict(tc_dict):
    return {k.replace("_", "-"): v for k, v in tc_dict.items()}


def _sections_with_test_cases(mapped_sections):
    return [s for s in mapped_sections if s.get("test_cases")]


def _get_sections_with_test_cases(client, api_id, auth_json):
    response = client.get(
        _MAPPING_API_TEST_CASES_URL,
        query_string={
            "api-id": api_id,
            "user-id": auth_json["id"],
            "token": auth_json["token"],
        },
    )
    assert response.status_code == HTTPStatus.OK
    payload = response.json
    if isinstance(payload, list):
        return []
    return _sections_with_test_cases(payload["mapped"])


@pytest.fixture()
def unmapped_api_db(client_db, ut_user_db, utilities):
    """API whose spec has a section with no test-case mapping yet."""

    user = client_db.session.query(UserModel).filter(UserModel.email == UT_USER_EMAIL).one()

    raw_path = _write_spec_tempfile(_UT_API_RAW_UNMAPPED_SPEC)
    ut_api = _make_api_model(raw_path, user, utilities)
    client_db.session.add(ut_api)
    client_db.session.commit()

    yield ut_api

    if os.path.isfile(raw_path):
        os.remove(raw_path)


@pytest.fixture()
def mapped_api_tc_db(client_db, ut_user_db, utilities):
    """API with one ApiTestCaseModel on a mapped section of the spec."""

    user = client_db.session.query(UserModel).filter(UserModel.email == UT_USER_EMAIL).one()

    raw_path = _write_spec_tempfile(_UT_API_RAW_MAPPED_SPEC)
    ut_api = _make_api_model(raw_path, user, utilities)
    ut_test_case = get_test_case_model(client_db, utilities)
    section_offset = _UT_API_RAW_MAPPED_SPEC.find(_UT_API_SPEC_SECTION_WITH_MAPPING)
    ut_api_tc_mapping = ApiTestCaseModel(
        ut_api, ut_test_case, _UT_API_SPEC_SECTION_WITH_MAPPING, section_offset, 75, user
    )

    client_db.session.add(ut_api)
    client_db.session.add(ut_test_case)
    client_db.session.add(ut_api_tc_mapping)
    client_db.session.commit()

    yield ut_api, ut_test_case, ut_api_tc_mapping

    if os.path.isfile(raw_path):
        os.remove(raw_path)


@pytest.fixture()
def restricted_api_db(client_db, ut_user_db, ut_reader_user_db, utilities):
    """API that denies read access to the reader user."""

    user = client_db.session.query(UserModel).filter(UserModel.email == UT_USER_EMAIL).one()

    raw_path = _write_spec_tempfile(_UT_API_RAW_RESTRICTED_SPEC)
    ut_api = _make_api_model(raw_path, user, utilities)
    ut_api.read_denials = f"[{ut_reader_user_db.id}]"
    client_db.session.add(ut_api)
    client_db.session.commit()

    yield ut_api

    if os.path.isfile(raw_path):
        os.remove(raw_path)


def test_login(user_authentication):
    assert user_authentication.status_code == HTTPStatus.OK


def test_unexisting_api(client, user_authentication):
    """Invalid api-id is rejected by the permission decorator before the handler body."""

    auth = {"user-id": user_authentication.json["id"], "token": user_authentication.json["token"]}
    response = client.get(_MAPPING_API_TEST_CASES_URL, query_string={"api-id": 0, **auth})
    assert response.status_code == HTTPStatus.NOT_FOUND

    response = client.post(_MAPPING_API_TEST_CASES_URL, json={"api-id": 0, **auth})
    assert response.status_code == HTTPStatus.NOT_FOUND

    response = client.put(_MAPPING_API_TEST_CASES_URL, json={"api-id": 0, **auth})
    assert response.status_code == HTTPStatus.NOT_FOUND

    response = client.delete(_MAPPING_API_TEST_CASES_URL, json={"api-id": 0, **auth})
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_unauthorized_fail(client, user_authentication, restricted_api_db, ut_reader_user_db):
    """Reader cannot read or write an API that denies read access."""

    auth = {"user-id": ut_reader_user_db.id, "token": ut_reader_user_db.token}
    response = client.get(
        _MAPPING_API_TEST_CASES_URL, query_string={"api-id": restricted_api_db.id, **auth}
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED

    response = client.post(
        _MAPPING_API_TEST_CASES_URL,
        json={"api-id": restricted_api_db.id, **auth},
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED

    response = client.put(
        _MAPPING_API_TEST_CASES_URL,
        json={"api-id": restricted_api_db.id, **auth},
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED

    response = client.delete(
        _MAPPING_API_TEST_CASES_URL,
        json={"api-id": restricted_api_db.id, **auth},
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED


# --- GET ---


def test_get_ok_structure(client, user_authentication, mapped_api_tc_db):
    api, _tc, _mapping = mapped_api_tc_db
    response = client.get(
        _MAPPING_API_TEST_CASES_URL,
        query_string={
            "api-id": api.id,
            "user-id": user_authentication.json["id"],
            "token": user_authentication.json["token"],
        },
    )
    assert response.status_code == HTTPStatus.OK
    payload = response.json
    assert isinstance(payload, dict)
    assert "mapped" in payload and "unmapped" in payload


def test_get_lists_mapped_test_case(client, user_authentication, mapped_api_tc_db):
    api, test_case, api_tc_mapping = mapped_api_tc_db
    sections = _get_sections_with_test_cases(client, api.id, user_authentication.json)
    assert len(sections) == 1
    assert sections[0]["section"] == _UT_API_SPEC_SECTION_WITH_MAPPING
    tcs = sections[0]["test_cases"]
    assert len(tcs) == 1
    assert tcs[0]["relation_id"] == api_tc_mapping.id
    assert tcs[0]["test_case"]["title"] == test_case.title


# --- POST ---


@pytest.mark.parametrize("mandatory_field", ["api-id", "test-case", "section", "coverage"])
def test_post_missed_fields(
    client, client_db, user_authentication, unmapped_api_db, utilities, mandatory_field
):
    tc = get_test_case_model(client_db, utilities).as_dict()
    tc = hyphenate_test_case_dict(tc)
    tc.pop("id", None)

    base = {
        "section": _UT_API_SPEC_SECTION_NO_MAPPING,
        "offset": _UT_API_RAW_UNMAPPED_SPEC.find(_UT_API_SPEC_SECTION_NO_MAPPING),
        "coverage": 50,
        "test-case": tc,
        "user-id": user_authentication.json["id"],
        "token": user_authentication.json["token"],
        "api-id": unmapped_api_db.id,
    }
    base.pop(mandatory_field)
    response = client.post(_MAPPING_API_TEST_CASES_URL, json=base)
    assert response.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.parametrize("test_case_field", ["title", "description", "repository", "relative-path"])
def test_post_new_test_case_required_fields(
    client, client_db, user_authentication, unmapped_api_db, utilities, test_case_field
):
    """Creating a new Test Case without id requires all TestCase fields except status."""

    tc = get_test_case_model(client_db, utilities).as_dict()
    tc = hyphenate_test_case_dict(tc)
    tc.pop("id", None)
    tc.pop(test_case_field)

    mapping_data = {
        "api-id": unmapped_api_db.id,
        "section": _UT_API_SPEC_SECTION_NO_MAPPING,
        "offset": _UT_API_RAW_UNMAPPED_SPEC.find(_UT_API_SPEC_SECTION_NO_MAPPING),
        "coverage": 55,
        "test-case": tc,
        "user-id": user_authentication.json["id"],
        "token": user_authentication.json["token"],
    }
    response = client.post(_MAPPING_API_TEST_CASES_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.BAD_REQUEST

    tc = get_test_case_model(client_db, utilities).as_dict()
    tc = hyphenate_test_case_dict(tc)
    tc.pop("id", None)

    mapping_data["test-case"] = tc
    response = client.post(_MAPPING_API_TEST_CASES_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.CREATED
    assert isinstance(response.json, dict)

    response = client.post(_MAPPING_API_TEST_CASES_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.CONFLICT


def test_post_new_test_case_duplicate_content_conflict(
    client, client_db, user_authentication, unmapped_api_db, utilities
):
    """Second POST with identical new test-case content hits duplicate Test Case detection."""

    tc = get_test_case_model(client_db, utilities).as_dict()
    tc = hyphenate_test_case_dict(tc)
    tc.pop("id", None)

    mapping_data = {
        "api-id": unmapped_api_db.id,
        "section": _UT_API_SPEC_SECTION_NO_MAPPING,
        "offset": _UT_API_RAW_UNMAPPED_SPEC.find(_UT_API_SPEC_SECTION_NO_MAPPING),
        "coverage": 60,
        "test-case": tc,
        "user-id": user_authentication.json["id"],
        "token": user_authentication.json["token"],
    }
    response = client.post(_MAPPING_API_TEST_CASES_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.CREATED

    tc2 = get_test_case_model(client_db, utilities).as_dict()
    tc2 = hyphenate_test_case_dict(tc2)
    tc2.pop("id", None)
    mapping_data["test-case"] = tc2
    mapping_data["coverage"] = 61
    response = client.post(_MAPPING_API_TEST_CASES_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.CREATED

    mapping_data["test-case"] = tc
    mapping_data["coverage"] = 62
    response = client.post(_MAPPING_API_TEST_CASES_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.CONFLICT


def test_post_existing_test_case_id(
    client, client_db, user_authentication, unmapped_api_db, mapped_api_tc_db, utilities
):
    """Map an existing Test Case by id to two different (section, offset) pairs on the same API."""

    _source_api, existing_tc, _ = mapped_api_tc_db
    _UT_SECOND_SECTION = "BASIL UT:"
    offset_second = _UT_API_RAW_UNMAPPED_SPEC.find(_UT_SECOND_SECTION)

    tc_dict = hyphenate_test_case_dict(existing_tc.as_dict())

    mapping_data = {
        "api-id": unmapped_api_db.id,
        "section": _UT_API_SPEC_SECTION_NO_MAPPING,
        "offset": _UT_API_RAW_UNMAPPED_SPEC.find(_UT_API_SPEC_SECTION_NO_MAPPING),
        "coverage": 40,
        "test-case": tc_dict,
        "user-id": user_authentication.json["id"],
        "token": user_authentication.json["token"],
    }
    response = client.post(_MAPPING_API_TEST_CASES_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.CREATED

    mapping_data["section"] = _UT_SECOND_SECTION
    mapping_data["offset"] = offset_second
    mapping_data["coverage"] = 41
    response = client.post(_MAPPING_API_TEST_CASES_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.CREATED

    response = client.post(_MAPPING_API_TEST_CASES_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.CONFLICT


def test_post_existing_test_case_id_not_found(client, client_db, user_authentication, unmapped_api_db, utilities):
    tc = get_test_case_model(client_db, utilities)
    client_db.session.add(tc)
    client_db.session.commit()
    tc_dict = hyphenate_test_case_dict(tc.as_dict())
    client_db.session.delete(tc)
    client_db.session.commit()

    mapping_data = {
        "api-id": unmapped_api_db.id,
        "section": _UT_API_SPEC_SECTION_NO_MAPPING,
        "offset": _UT_API_RAW_UNMAPPED_SPEC.find(_UT_API_SPEC_SECTION_NO_MAPPING),
        "coverage": 30,
        "test-case": tc_dict,
        "user-id": user_authentication.json["id"],
        "token": user_authentication.json["token"],
    }
    response = client.post(_MAPPING_API_TEST_CASES_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.NOT_FOUND


# --- PUT ---


@pytest.mark.parametrize(
    "mandatory_field",
    ["api-id", "test-case", "section", "coverage", "relation-id"],
)
def test_put_missed_fields(
    client, client_db, user_authentication, mapped_api_tc_db, utilities, mandatory_field
):
    api, _tc, api_tc_mapping = mapped_api_tc_db
    ut_test_case_dict = api_tc_mapping.test_case.as_dict()

    mapping_data = {
        "api-id": api.id,
        "relation-id": api_tc_mapping.id,
        "section": api_tc_mapping.section,
        "offset": api_tc_mapping.offset,
        "coverage": api_tc_mapping.coverage,
        "test-case": ut_test_case_dict,
        "user-id": user_authentication.json["id"],
        "token": user_authentication.json["token"],
    }
    mapping_data.pop(mandatory_field)
    response = client.put(_MAPPING_API_TEST_CASES_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_put_not_found_relation(client, client_db, user_authentication, mapped_api_tc_db, utilities):
    api, _tc, api_tc_mapping = mapped_api_tc_db
    ut_test_case_dict = api_tc_mapping.test_case.as_dict()

    mapping_data = {
        "api-id": api.id,
        "relation-id": 0,
        "section": api_tc_mapping.section,
        "offset": api_tc_mapping.offset,
        "coverage": api_tc_mapping.coverage,
        "test-case": ut_test_case_dict,
        "user-id": user_authentication.json["id"],
        "token": user_authentication.json["token"],
    }
    response = client.put(_MAPPING_API_TEST_CASES_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_put_ok(client, client_db, user_authentication, mapped_api_tc_db, utilities):
    api, _tc, api_tc_mapping = mapped_api_tc_db
    ut_test_case_dict = api_tc_mapping.test_case.as_dict()

    mapping_data = {
        "api-id": api.id,
        "relation-id": api_tc_mapping.id,
        "section": api_tc_mapping.section,
        "offset": api_tc_mapping.offset,
        "coverage": api_tc_mapping.coverage,
        "test-case": ut_test_case_dict,
        "user-id": user_authentication.json["id"],
        "token": user_authentication.json["token"],
    }
    response = client.put(_MAPPING_API_TEST_CASES_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.OK

    mapping_data["coverage"] = 88
    response = client.put(_MAPPING_API_TEST_CASES_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.OK
    assert response.json.get("coverage", 0) == 88

    mapping_data["test-case"]["title"] = f"{mapping_data['test-case']['title']}-modified"
    mapping_data["test-case"]["unexisting"] = "value"
    response = client.put(_MAPPING_API_TEST_CASES_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.OK


# --- DELETE ---


def test_delete_bad_payload(client, user_authentication, mapped_api_tc_db):
    api, _tc, _m = mapped_api_tc_db
    delete_data = {
        "api-id": api.id,
        "user-id": user_authentication.json["id"],
        "token": user_authentication.json["token"],
    }
    response = client.delete(_MAPPING_API_TEST_CASES_URL, json=delete_data)
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_delete_not_found(client, user_authentication, mapped_api_tc_db):
    api, _tc, _m = mapped_api_tc_db
    delete_data = {
        "api-id": api.id,
        "relation-id": 0,
        "user-id": user_authentication.json["id"],
        "token": user_authentication.json["token"],
    }
    response = client.delete(_MAPPING_API_TEST_CASES_URL, json=delete_data)
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_delete_wrong_api_id(client, user_authentication, mapped_api_tc_db, client_db, utilities):
    api, _tc, api_tc_mapping = mapped_api_tc_db
    user = client_db.session.query(UserModel).filter(UserModel.email == UT_USER_EMAIL).one()
    raw_path = _write_spec_tempfile(_UT_API_RAW_MAPPED_SPEC)
    second_api = _make_api_model(raw_path, user, utilities)
    client_db.session.add(second_api)
    client_db.session.commit()
    try:
        delete_data = {
            "api-id": second_api.id,
            "relation-id": api_tc_mapping.id,
            "user-id": user_authentication.json["id"],
            "token": user_authentication.json["token"],
        }
        response = client.delete(_MAPPING_API_TEST_CASES_URL, json=delete_data)
        assert response.status_code == HTTPStatus.BAD_REQUEST
    finally:
        if os.path.isfile(raw_path):
            os.remove(raw_path)


def test_delete_ok(client, user_authentication, mapped_api_tc_db):
    api, _tc, api_tc_mapping = mapped_api_tc_db
    delete_data = {
        "api-id": api.id,
        "relation-id": api_tc_mapping.id,
        "user-id": user_authentication.json["id"],
        "token": user_authentication.json["token"],
    }
    response = client.delete(_MAPPING_API_TEST_CASES_URL, json=delete_data)
    assert response.status_code == HTTPStatus.OK

    sections = _get_sections_with_test_cases(client, api.id, user_authentication.json)
    assert len(sections) == 0


def test_post_created_notification_and_version(client, user_authentication, unmapped_api_db, client_db, utilities):
    tc = get_test_case_model(client_db, utilities).as_dict()
    tc = hyphenate_test_case_dict(tc)
    tc.pop("id", None)

    mapping_data = {
        "api-id": unmapped_api_db.id,
        "section": _UT_API_SPEC_SECTION_NO_MAPPING,
        "offset": _UT_API_RAW_UNMAPPED_SPEC.find(_UT_API_SPEC_SECTION_NO_MAPPING),
        "coverage": 77,
        "test-case": tc,
        "user-id": user_authentication.json["id"],
        "token": user_authentication.json["token"],
    }
    response = client.post(_MAPPING_API_TEST_CASES_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.CREATED
    assert response.json["test_case"]["created_by"] == UT_USER_NAME
    assert response.json["version"] == "1.1"
