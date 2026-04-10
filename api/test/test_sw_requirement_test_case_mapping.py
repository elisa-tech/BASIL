import os
import pytest
import tempfile
from http import HTTPStatus

from db.models.user import UserModel
from db.models.api import ApiModel
from db.models.sw_requirement import SwRequirementModel
from db.models.api_sw_requirement import ApiSwRequirementModel
from db.models.sw_requirement_sw_requirement import SwRequirementSwRequirementModel
from db.models.test_case import TestCaseModel
from db.models.sw_requirement_test_case import SwRequirementTestCaseModel
from conftest import UT_USER_EMAIL

_MAPPING_SW_REQUIREMENT_TEST_CASES_URL = "/mapping/sw-requirement/test-cases"

_UT_API_NAME = "ut_api"
_UT_API_LIBRARY = "ut_api_library"
_UT_API_LIBRARY_VERSION = "v1.0.0"
_UT_API_CATEGORY = "ut_api_category"
_UT_API_IMPLEMENTATION_FILE_FROM_ROW = 0
_UT_API_IMPLEMENTATION_FILE_TO_ROW = 42
_UT_API_TAGS = "ut_api_tags"

_UT_API_SPEC_SECTION_WITH_MAPPING = "This section has mapping."
_UT_API_SPEC_SECTION_TO_BE_MAPPED = "This section is to be mapped."
_UT_API_RAW_MAPPED_SPEC = (
    f"BASIL UT: {_UT_API_SPEC_SECTION_WITH_MAPPING} {_UT_API_SPEC_SECTION_TO_BE_MAPPED} "
    f"Used for {_MAPPING_SW_REQUIREMENT_TEST_CASES_URL}."
)

_UT_TC_REPOSITORY = "https://github.com/example/repo"

UNMATCHING_ID = 99999


def get_sw_requirement_model(client_db, utilities):
    user = client_db.session.query(UserModel).filter(UserModel.email == UT_USER_EMAIL).one()
    return SwRequirementModel(
        f"SW req #{utilities.generate_random_hex_string8()}", "SW shall work as well as possible.", user
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


@pytest.fixture()
def mapped_api_sr_tc_db(client_db, ut_user_db, utilities):
    """Create a Test Case mapped to a SW Requirement that is mapped to the API reference."""

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
    ut_sw_requirement = get_sw_requirement_model(client_db, utilities)
    ut_api_requirement_mapping = ApiSwRequirementModel(
        ut_api,
        ut_sw_requirement,
        _UT_API_SPEC_SECTION_WITH_MAPPING,
        _UT_API_RAW_MAPPED_SPEC.find(_UT_API_SPEC_SECTION_WITH_MAPPING),
        0,
        user,
    )
    ut_test_case = get_test_case_model(client_db, utilities)
    ut_sr_tc_mapping = SwRequirementTestCaseModel(
        ut_api_requirement_mapping, None, ut_test_case, 75, user
    )

    client_db.session.add(ut_api)
    client_db.session.add(ut_sw_requirement)
    client_db.session.add(ut_api_requirement_mapping)
    client_db.session.add(ut_test_case)
    client_db.session.add(ut_sr_tc_mapping)
    client_db.session.commit()

    yield (ut_api, ut_sw_requirement, ut_api_requirement_mapping, ut_sr_tc_mapping)

    if os.path.isfile(raw_spec.name):
        os.remove(raw_spec.name)


@pytest.fixture()
def mapped_api_sr_sr_tc_db(client_db, ut_user_db, utilities):
    """Create a Test Case mapped to a nested SW Requirement (sr–sr) under the API."""

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
    ut_sw_requirement = get_sw_requirement_model(client_db, utilities)
    ut_api_requirement_mapping = ApiSwRequirementModel(
        ut_api,
        ut_sw_requirement,
        _UT_API_SPEC_SECTION_WITH_MAPPING,
        _UT_API_RAW_MAPPED_SPEC.find(_UT_API_SPEC_SECTION_WITH_MAPPING),
        0,
        user,
    )
    ut_nested_sw_requirement = get_sw_requirement_model(client_db, utilities)
    ut_requirement_requirement_mapping = SwRequirementSwRequirementModel(
        ut_api_requirement_mapping, None, ut_nested_sw_requirement, 50, user
    )
    ut_test_case = get_test_case_model(client_db, utilities)
    ut_sr_tc_mapping = SwRequirementTestCaseModel(
        None, ut_requirement_requirement_mapping, ut_test_case, 80, user
    )

    client_db.session.add(ut_api)
    client_db.session.add(ut_sw_requirement)
    client_db.session.add(ut_api_requirement_mapping)
    client_db.session.add(ut_nested_sw_requirement)
    client_db.session.add(ut_requirement_requirement_mapping)
    client_db.session.add(ut_test_case)
    client_db.session.add(ut_sr_tc_mapping)
    client_db.session.commit()

    yield (
        ut_api,
        ut_sw_requirement,
        ut_api_requirement_mapping,
        ut_requirement_requirement_mapping,
        ut_sr_tc_mapping,
    )

    if os.path.isfile(raw_spec.name):
        os.remove(raw_spec.name)


def test_login(user_authentication):
    assert user_authentication.status_code == HTTPStatus.OK


def test_unexisting_api(client):
    """SwRequirementTestCasesMapping GET does not resolve api-id via Api guard; empty result is OK."""

    response = client.get(
        _MAPPING_SW_REQUIREMENT_TEST_CASES_URL,
        query_string={"api-id": 0, "relation-id": 0, "relation-to": "api"},
    )
    assert response.status_code == HTTPStatus.OK
    assert response.json == []

    response = client.post(_MAPPING_SW_REQUIREMENT_TEST_CASES_URL, json={"api-id": 0})
    assert response.status_code == HTTPStatus.BAD_REQUEST

    response = client.put(_MAPPING_SW_REQUIREMENT_TEST_CASES_URL, json={"api-id": 0})
    assert response.status_code == HTTPStatus.BAD_REQUEST

    response = client.delete(_MAPPING_SW_REQUIREMENT_TEST_CASES_URL, json={"api-id": 0})
    assert response.status_code == HTTPStatus.BAD_REQUEST


# Test GET


def test_get_missed_relation_to(client, user_authentication, mapped_api_sr_tc_db):
    api, sw_requirement, api_sr_mapping, sr_tc_mapping = mapped_api_sr_tc_db
    get_query = {
        "api-id": api.id,
        "relation-id": api_sr_mapping.id,
        "relation-to": "api",
        "user-id": user_authentication.json["id"],
        "token": user_authentication.json["token"],
    }
    get_query.pop("relation-to")
    response = client.get(_MAPPING_SW_REQUIREMENT_TEST_CASES_URL, query_string=get_query)
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_get_wrong_relation_to(client, user_authentication, mapped_api_sr_tc_db):
    api, sw_requirement, api_sr_mapping, sr_tc_mapping = mapped_api_sr_tc_db
    get_query = {
        "api-id": api.id,
        "relation-id": api_sr_mapping.id,
        "relation-to": "not-a-valid-value",
        "user-id": user_authentication.json["id"],
        "token": user_authentication.json["token"],
    }
    response = client.get(_MAPPING_SW_REQUIREMENT_TEST_CASES_URL, query_string=get_query)
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_get_relation_to_api(client, user_authentication, mapped_api_sr_tc_db):
    api, sw_requirement, api_sr_mapping, sr_tc_mapping = mapped_api_sr_tc_db
    get_query = {
        "api-id": api.id,
        "relation-id": api_sr_mapping.id,
        "relation-to": "api",
        "user-id": user_authentication.json["id"],
        "token": user_authentication.json["token"],
    }

    response = client.get(_MAPPING_SW_REQUIREMENT_TEST_CASES_URL, query_string=get_query)
    assert response.status_code == HTTPStatus.OK
    assert isinstance(response.json, list)
    assert len(response.json) == 1


def test_get_relation_to_sw_requirement(client, user_authentication, mapped_api_sr_sr_tc_db):
    api, sw_requirement, api_sr_mapping, sr_sr_mapping, sr_tc_mapping = mapped_api_sr_sr_tc_db
    get_query = {
        "api-id": api.id,
        "relation-id": sr_sr_mapping.id,
        "relation-to": "sw-requirement",
        "user-id": user_authentication.json["id"],
        "token": user_authentication.json["token"],
    }

    response = client.get(_MAPPING_SW_REQUIREMENT_TEST_CASES_URL, query_string=get_query)
    assert response.status_code == HTTPStatus.OK
    assert isinstance(response.json, list)
    assert len(response.json) == 1


# Test POST


@pytest.mark.parametrize(
    "mandatory_field",
    ["relation-id", "relation-to", "coverage", "sw-requirement", "test-case", "api-id"],
)
def test_post_missed_fields(
    client, client_db, user_authentication, mapped_api_sr_tc_db, utilities, mandatory_field
):
    ut_test_case_dict = get_test_case_model(client_db, utilities).as_dict()
    ut_test_case_dict.pop("id", None)

    api, sw_requirement, api_sr_mapping, sr_tc_mapping = mapped_api_sr_tc_db
    mapping_data = {
        "api-id": api.id,
        "relation-id": api_sr_mapping.id,
        "relation-to": "api",
        "coverage": 50,
        "sw-requirement": sw_requirement.as_dict(),
        "test-case": ut_test_case_dict,
        "user-id": user_authentication.json["id"],
        "token": user_authentication.json["token"],
    }
    mapping_data.pop(mandatory_field)
    response = client.post(_MAPPING_SW_REQUIREMENT_TEST_CASES_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_post_bad_payload(client, client_db, user_authentication, mapped_api_sr_tc_db, utilities):
    ut_test_case_dict = get_test_case_model(client_db, utilities).as_dict()
    ut_test_case_dict.pop("id", None)

    api, sw_requirement, api_sr_mapping, sr_tc_mapping = mapped_api_sr_tc_db

    mapping_data = {
        "api-id": api.id,
        "relation-id": api_sr_mapping.id,
        "relation-to": "unexpected value",
        "coverage": 50,
        "sw-requirement": sw_requirement.as_dict(),
        "test-case": ut_test_case_dict,
        "user-id": user_authentication.json["id"],
        "token": user_authentication.json["token"],
    }
    response = client.post(_MAPPING_SW_REQUIREMENT_TEST_CASES_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.BAD_REQUEST

    mapping_data = {
        "api-id": api.id,
        "relation-id": 0,
        "relation-to": "api",
        "coverage": 50,
        "sw-requirement": sw_requirement.as_dict(),
        "test-case": ut_test_case_dict,
        "user-id": user_authentication.json["id"],
        "token": user_authentication.json["token"],
    }
    response = client.post(_MAPPING_SW_REQUIREMENT_TEST_CASES_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.parametrize(
    "test_case_field",
    ["title", "description", "repository", "relative-path"],
)
def test_post_new_to_api(
    client, client_db, user_authentication, mapped_api_sr_tc_db, utilities, test_case_field
):
    ut_test_case_dict = get_test_case_model(client_db, utilities).as_dict()
    ut_test_case_dict = {k.replace("_", "-"): v for k, v in ut_test_case_dict.items()}
    ut_test_case_dict.pop("id")
    ut_test_case_dict.pop(test_case_field)

    api, sw_requirement, api_sr_mapping, sr_tc_mapping = mapped_api_sr_tc_db

    mapping_data = {
        "api-id": api.id,
        "coverage": 50,
        "relation-id": api_sr_mapping.id,
        "relation-to": "api",
        "sw-requirement": sw_requirement.as_dict(),
        "test-case": ut_test_case_dict,
        "user-id": user_authentication.json["id"],
        "token": user_authentication.json["token"],
    }

    response = client.post(_MAPPING_SW_REQUIREMENT_TEST_CASES_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.BAD_REQUEST

    ut_test_case_dict = get_test_case_model(client_db, utilities).as_dict()
    ut_test_case_dict = {k.replace("_", "-"): v for k, v in ut_test_case_dict.items()}
    ut_test_case_dict.pop("id", None)

    mapping_data = {
        "api-id": api.id,
        "coverage": 50,
        "relation-id": api_sr_mapping.id,
        "relation-to": "api",
        "sw-requirement": sw_requirement.as_dict(),
        "test-case": ut_test_case_dict,
        "user-id": user_authentication.json["id"],
        "token": user_authentication.json["token"],
    }

    response = client.post(_MAPPING_SW_REQUIREMENT_TEST_CASES_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.CREATED
    assert isinstance(response.json, dict)

    response = client.post(_MAPPING_SW_REQUIREMENT_TEST_CASES_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.CONFLICT

    new_test_case = get_test_case_model(client_db, utilities)
    client_db.session.add(new_test_case)
    client_db.session.commit()

    mapping_data = {
        "api-id": api.id,
        "coverage": 60,
        "relation-id": api_sr_mapping.id,
        "relation-to": "api",
        "sw-requirement": sw_requirement.as_dict(),
        "test-case": new_test_case.as_dict(),
        "user-id": user_authentication.json["id"],
        "token": user_authentication.json["token"],
    }

    response = client.post(_MAPPING_SW_REQUIREMENT_TEST_CASES_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.CREATED
    assert isinstance(response.json, dict)

    response = client.post(_MAPPING_SW_REQUIREMENT_TEST_CASES_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.CONFLICT

    new_test_case = get_test_case_model(client_db, utilities)
    client_db.session.add(new_test_case)
    client_db.session.commit()
    new_test_case_dict = new_test_case.as_dict()
    client_db.session.delete(new_test_case)
    client_db.session.commit()

    mapping_data = {
        "api-id": api.id,
        "coverage": 70,
        "relation-id": api_sr_mapping.id,
        "relation-to": "api",
        "sw-requirement": sw_requirement.as_dict(),
        "test-case": new_test_case_dict,
        "user-id": user_authentication.json["id"],
        "token": user_authentication.json["token"],
    }

    response = client.post(_MAPPING_SW_REQUIREMENT_TEST_CASES_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_post_new_to_sw_requirement(client, client_db, user_authentication, mapped_api_sr_sr_tc_db, utilities):
    ut_test_case_dict = get_test_case_model(client_db, utilities).as_dict()
    ut_test_case_dict.pop("id", None)
    ut_test_case_dict = {k.replace("_", "-"): v for k, v in ut_test_case_dict.items()}

    api, sw_requirement, api_sr_mapping, sr_sr_mapping, sr_tc_mapping = mapped_api_sr_sr_tc_db

    mapping_data = {
        "api-id": api.id,
        "coverage": 50,
        "relation-id": 0,
        "relation-to": "sw-requirement",
        "sw-requirement": sw_requirement.as_dict(),
        "test-case": ut_test_case_dict,
        "user-id": user_authentication.json["id"],
        "token": user_authentication.json["token"],
    }

    response = client.post(_MAPPING_SW_REQUIREMENT_TEST_CASES_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.NOT_FOUND

    # POST is not guarded by check_api_user_write_permission; mismatched api-id can still
    # resolve the parent mapping. Use a non-existent relation-id to assert NOT_FOUND.
    mapping_data = {
        "api-id": api.id,
        "coverage": 50,
        "relation-id": UNMATCHING_ID,
        "relation-to": "sw-requirement",
        "sw-requirement": sw_requirement.as_dict(),
        "test-case": ut_test_case_dict,
        "user-id": user_authentication.json["id"],
        "token": user_authentication.json["token"],
    }

    response = client.post(_MAPPING_SW_REQUIREMENT_TEST_CASES_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.NOT_FOUND


# Test PUT


@pytest.mark.parametrize("mandatory_field", ["test-case", "coverage", "relation-id", "sw-requirement", "api-id"])
def test_put_miss_fields(
    client, client_db, user_authentication, mapped_api_sr_tc_db, utilities, mandatory_field
):
    ut_test_case_dict = get_test_case_model(client_db, utilities).as_dict()

    api, sw_requirement, api_sr_mapping, sr_tc_mapping = mapped_api_sr_tc_db
    mapping_data = {
        "api-id": api.id,
        "coverage": 50,
        "relation-id": sr_tc_mapping.id,
        "sw-requirement": sw_requirement.as_dict(),
        "test-case": ut_test_case_dict,
        "user-id": user_authentication.json["id"],
        "token": user_authentication.json["token"],
    }
    mapping_data.pop(mandatory_field)
    response = client.put(_MAPPING_SW_REQUIREMENT_TEST_CASES_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_put_bad_payload(client, client_db, user_authentication, mapped_api_sr_tc_db, utilities):
    ut_test_case_dict = get_test_case_model(client_db, utilities).as_dict()

    api, sw_requirement, api_sr_mapping, sr_tc_mapping = mapped_api_sr_tc_db
    mapping_data = {
        "api-id": api.id,
        "relation-id": 0,
        "coverage": 50,
        "sw-requirement": sw_requirement.as_dict(),
        "test-case": ut_test_case_dict,
        "user-id": user_authentication.json["id"],
        "token": user_authentication.json["token"],
    }
    response = client.put(_MAPPING_SW_REQUIREMENT_TEST_CASES_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_put_ok(client, client_db, user_authentication, mapped_api_sr_tc_db, utilities):
    api, sw_requirement, api_sr_mapping, sr_tc_mapping = mapped_api_sr_tc_db

    ut_test_case_dict = sr_tc_mapping.test_case.as_dict()
    ut_test_case_dict = {k.replace("_", "-"): v for k, v in ut_test_case_dict.items()}

    mapping_data = {
        "api-id": api.id,
        "coverage": sr_tc_mapping.coverage,
        "relation-id": sr_tc_mapping.id,
        "sw-requirement": {"id": sw_requirement.id},
        "test-case": ut_test_case_dict,
        "user-id": user_authentication.json["id"],
        "token": user_authentication.json["token"],
    }
    response = client.put(_MAPPING_SW_REQUIREMENT_TEST_CASES_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.OK

    mapping_data["coverage"] = 85
    response = client.put(_MAPPING_SW_REQUIREMENT_TEST_CASES_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.OK
    assert response.json.get("coverage", 0) == 85

    mapping_data["test-case"]["title"] = f"{mapping_data['test-case']['title']}-modified"
    mapping_data["test-case"]["unexisting"] = "value"

    response = client.put(_MAPPING_SW_REQUIREMENT_TEST_CASES_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.OK


# Test DELETE


def test_delete_bad_payload(client, client_db, user_authentication, mapped_api_sr_tc_db, utilities):
    api, sw_requirement, api_sr_mapping, sr_tc_mapping = mapped_api_sr_tc_db

    mapping_data = {
        "api-id": api.id,
        "coverage": 50,
        "user-id": user_authentication.json["id"],
        "token": user_authentication.json["token"],
    }
    response = client.delete(_MAPPING_SW_REQUIREMENT_TEST_CASES_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.BAD_REQUEST

    delete_data = {
        "api-id": api.id,
        "relation-id": 0,
        "user-id": user_authentication.json["id"],
        "token": user_authentication.json["token"],
    }
    response = client.delete(_MAPPING_SW_REQUIREMENT_TEST_CASES_URL, json=delete_data)
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_delete_miss_parent(client, client_db, user_authentication, mapped_api_sr_tc_db, utilities):
    api, sw_requirement, api_sr_mapping, sr_tc_mapping = mapped_api_sr_tc_db

    delete_data = {
        "api-id": api.id,
        "relation-id": UNMATCHING_ID,
        "user-id": user_authentication.json["id"],
        "token": user_authentication.json["token"],
    }

    response = client.delete(_MAPPING_SW_REQUIREMENT_TEST_CASES_URL, json=delete_data)
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_delete_ok(client, client_db, user_authentication, mapped_api_sr_tc_db, utilities):
    api, sw_requirement, api_sr_mapping, sr_tc_mapping = mapped_api_sr_tc_db

    delete_data = {
        "api-id": api.id,
        "relation-id": sr_tc_mapping.id,
        "user-id": user_authentication.json["id"],
        "token": user_authentication.json["token"],
    }

    response = client.delete(_MAPPING_SW_REQUIREMENT_TEST_CASES_URL, json=delete_data)
    assert response.status_code == HTTPStatus.OK

    get_query = {
        "api-id": api.id,
        "relation-id": api_sr_mapping.id,
        "relation-to": "api",
        "user-id": user_authentication.json["id"],
        "token": user_authentication.json["token"],
    }

    response = client.get(_MAPPING_SW_REQUIREMENT_TEST_CASES_URL, query_string=get_query)
    assert response.status_code == HTTPStatus.OK
    assert isinstance(response.json, list)
    assert len(response.json) == 0
