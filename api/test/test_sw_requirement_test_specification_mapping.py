import os
import pytest
import tempfile
from http import HTTPStatus
from db.models.user import UserModel
from db.models.api import ApiModel
from db.models.sw_requirement import SwRequirementModel
from db.models.api_sw_requirement import ApiSwRequirementModel
from db.models.sw_requirement_sw_requirement import SwRequirementSwRequirementModel
from db.models.test_specification import TestSpecificationModel
from db.models.sw_requirement_test_specification import SwRequirementTestSpecificationModel
from conftest import UT_USER_EMAIL

_MAPPING_SW_REQUIREMENT_TEST_SPECIFICATIONS_URL = "/mapping/sw-requirement/test-specifications"

_UT_API_NAME = "ut_api"
_UT_API_LIBRARY = "ut_api_library"
_UT_API_LIBRARY_VERSION = "v1.0.0"
_UT_API_CATEGORY = "ut_api_category"
_UT_API_IMPLEMENTATION_FILE_FROM_ROW = 0
_UT_API_IMPLEMENTATION_FILE_TO_ROW = 42
_UT_API_TAGS = "ut_api_tags"

_UT_API_SPEC_SECTION_WITH_MAPPING = "This section has mapping."
_UT_API_SPEC_SECTION_TO_BE_MAPPED = "This section is to be mapped."
_UT_API_RAW_RESTRICTED_SPEC = (
    'BASIL UT: "Reader" user is not able to read this API.'
    f" Used for {_MAPPING_SW_REQUIREMENT_TEST_SPECIFICATIONS_URL}."
)
_UT_API_RAW_MAPPED_SPEC = (
    f"BASIL UT: {_UT_API_SPEC_SECTION_WITH_MAPPING} {_UT_API_SPEC_SECTION_TO_BE_MAPPED} "
    f"Used for {_MAPPING_SW_REQUIREMENT_TEST_SPECIFICATIONS_URL}."
)

_UT_TEST_SPEC_TITLE = "UT Test Specification"
_UT_TEST_SPEC_PRECONDITIONS = "Test preconditions here"
_UT_TEST_SPEC_DESCRIPTION = "Test description here"
_UT_TEST_SPEC_EXPECTED_BEHAVIOR = "Expected behavior here"

UNMATCHING_ID = 99999


def get_sw_requirement_model(client_db, utilities):
    user = client_db.session.query(UserModel).filter(UserModel.email == UT_USER_EMAIL).one()
    return SwRequirementModel(
        f"SW req #{utilities.generate_random_hex_string8()}", "SW shall work as well as possible.", user
    )


def get_test_specification_model(client_db, utilities):
    user = client_db.session.query(UserModel).filter(UserModel.email == UT_USER_EMAIL).one()
    return TestSpecificationModel(
        f"{_UT_TEST_SPEC_TITLE} #{utilities.generate_random_hex_string8()}",
        _UT_TEST_SPEC_PRECONDITIONS,
        _UT_TEST_SPEC_DESCRIPTION,
        _UT_TEST_SPEC_EXPECTED_BEHAVIOR,
        user,
    )


def _create_software_component(client_db, utilities):
    # create API
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
    """Create Api with read restriction for "reader" """

    user = client_db.session.query(UserModel).filter(UserModel.email == UT_USER_EMAIL).one()

    # create raw API specification
    raw_spec = tempfile.NamedTemporaryFile(mode="w", delete=False)
    raw_spec.write(_UT_API_RAW_RESTRICTED_SPEC)
    raw_spec.close()

    # create API
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

    # remove the raw_spec tempfile
    if os.path.isfile(raw_spec.name):
        os.remove(raw_spec.name)


@pytest.fixture()
def mapped_api_sr_ts_db(client_db, ut_user_db, utilities):
    """Create a Test Specification mapped to a SW Requirement that is
    mapped to a section of the API Reference Document"""

    user = client_db.session.query(UserModel).filter(UserModel.email == UT_USER_EMAIL).one()

    # create raw API specification
    raw_spec = tempfile.NamedTemporaryFile(mode="w", delete=False)
    raw_spec.write(_UT_API_RAW_MAPPED_SPEC)
    raw_spec.close()

    # create API
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
    ut_test_specification = get_test_specification_model(client_db, utilities)
    ut_sr_ts_mapping = SwRequirementTestSpecificationModel(
        ut_api_requirement_mapping, None, ut_test_specification, 75, user
    )

    client_db.session.add(ut_api)
    client_db.session.add(ut_sw_requirement)
    client_db.session.add(ut_api_requirement_mapping)
    client_db.session.add(ut_test_specification)
    client_db.session.add(ut_sr_ts_mapping)
    client_db.session.commit()

    yield (ut_api, ut_sw_requirement, ut_api_requirement_mapping, ut_sr_ts_mapping)

    # remove the raw_spec tempfile
    if os.path.isfile(raw_spec.name):
        os.remove(raw_spec.name)


@pytest.fixture()
def mapped_api_sr_sr_ts_db(client_db, ut_user_db, utilities):
    """Create a Test Specification mapped to a SW Requirement that is
    mapped to another SW Requirement that is mapped to the API"""

    user = client_db.session.query(UserModel).filter(UserModel.email == UT_USER_EMAIL).one()

    # create raw API specification
    raw_spec = tempfile.NamedTemporaryFile(mode="w", delete=False)
    raw_spec.write(_UT_API_RAW_MAPPED_SPEC)
    raw_spec.close()

    # create API
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
    ut_test_specification = get_test_specification_model(client_db, utilities)
    ut_sr_ts_mapping = SwRequirementTestSpecificationModel(
        None, ut_requirement_requirement_mapping, ut_test_specification, 80, user
    )

    client_db.session.add(ut_api)
    client_db.session.add(ut_sw_requirement)
    client_db.session.add(ut_api_requirement_mapping)
    client_db.session.add(ut_nested_sw_requirement)
    client_db.session.add(ut_requirement_requirement_mapping)
    client_db.session.add(ut_test_specification)
    client_db.session.add(ut_sr_ts_mapping)
    client_db.session.commit()

    yield (ut_api, ut_sw_requirement, ut_api_requirement_mapping, ut_requirement_requirement_mapping, ut_sr_ts_mapping)

    # remove the raw_spec tempfile
    if os.path.isfile(raw_spec.name):
        os.remove(raw_spec.name)


def test_login(user_authentication):
    """Just ensure that the test user is logged in"""
    assert user_authentication.status_code == HTTPStatus.OK


# Common Tests


def test_unexisting_api(client):
    """Use an API with invalid id"""
    response = client.get(
        _MAPPING_SW_REQUIREMENT_TEST_SPECIFICATIONS_URL, query_string={"api-id": 0, "relation-id": 0}
    )
    assert response.status_code == HTTPStatus.NOT_FOUND

    response = client.post(_MAPPING_SW_REQUIREMENT_TEST_SPECIFICATIONS_URL, json={"api-id": 0})
    assert response.status_code == HTTPStatus.NOT_FOUND

    response = client.put(_MAPPING_SW_REQUIREMENT_TEST_SPECIFICATIONS_URL, json={"api-id": 0})
    assert response.status_code == HTTPStatus.NOT_FOUND

    response = client.delete(_MAPPING_SW_REQUIREMENT_TEST_SPECIFICATIONS_URL, json={"api-id": 0})
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_unauthorized_fail(client, client_db, restricted_api_db, ut_reader_user_db, utilities):
    """Use an API with restrictions"""

    ut_sw_requirement_dict = get_sw_requirement_model(client_db, utilities).as_dict()
    ut_sw_requirement_dict.pop("id", None)

    ut_test_specification_dict = get_test_specification_model(client_db, utilities).as_dict()
    ut_test_specification_dict.pop("id", None)

    mapping_data = {
        "api-id": restricted_api_db.id,
        "relation-to": "api",
        "relation-id": 0,
        "coverage": 50,
        "sw-requirement": ut_sw_requirement_dict,
        "test-specification": ut_test_specification_dict,
        "user-id": ut_reader_user_db.id,
        "token": ut_reader_user_db.token,
    }
    response = client.get(_MAPPING_SW_REQUIREMENT_TEST_SPECIFICATIONS_URL, query_string=mapping_data)
    assert response.status_code == HTTPStatus.UNAUTHORIZED

    response = client.post(_MAPPING_SW_REQUIREMENT_TEST_SPECIFICATIONS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.UNAUTHORIZED

    response = client.put(_MAPPING_SW_REQUIREMENT_TEST_SPECIFICATIONS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.UNAUTHORIZED

    response = client.delete(_MAPPING_SW_REQUIREMENT_TEST_SPECIFICATIONS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.UNAUTHORIZED


# Test GET


@pytest.mark.parametrize("mandatory_field", ["api-id", "relation-id", "relation-to"])
def test_get_missed_fields(client, user_authentication, mapped_api_sr_ts_db, mandatory_field):
    """Read Test Specification mapping without sending a mandatory field"""

    api, sw_requirement, api_sr_mapping, sr_ts_mapping = mapped_api_sr_ts_db
    get_query = {
        "api-id": api.id,
        "relation-id": api_sr_mapping.id,
        "relation-to": "api",
        "sw-requirement": {"id": api_sr_mapping.sw_requirement_id},
        "user-id": user_authentication.json["id"],
        "token": user_authentication.json["token"],
    }
    get_query.pop(mandatory_field)
    response = client.get(_MAPPING_SW_REQUIREMENT_TEST_SPECIFICATIONS_URL, query_string=get_query)
    assert response.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.parametrize("key_to_modify", ["api-id", "relation-id", "relation-to"])
def test_get_bad_payload(client, user_authentication, mapped_api_sr_ts_db, key_to_modify):
    """Read Test Specification mapping sending an unexpected payload"""

    api, sw_requirement, api_sr_mapping, sr_ts_mapping = mapped_api_sr_ts_db
    get_query = {
        "api-id": api.id,
        "relation-id": api_sr_mapping.id,
        "relation-to": "api",
        "sw-requirement": {"id": api_sr_mapping.sw_requirement_id},
        "user-id": user_authentication.json["id"],
        "token": user_authentication.json["token"],
    }
    get_query[key_to_modify] = "unexpected value"
    response = client.get(_MAPPING_SW_REQUIREMENT_TEST_SPECIFICATIONS_URL, query_string=get_query)
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_get_relation_to_api(client, user_authentication, mapped_api_sr_ts_db):
    """Read Test Specification mapping with parent mapped to api"""

    api, sw_requirement, api_sr_mapping, sr_ts_mapping = mapped_api_sr_ts_db
    get_query = {
        "api-id": api.id,
        "relation-id": api_sr_mapping.id,
        "relation-to": "api",
        "user-id": user_authentication.json["id"],
        "token": user_authentication.json["token"],
    }

    response = client.get(_MAPPING_SW_REQUIREMENT_TEST_SPECIFICATIONS_URL, query_string=get_query)
    assert response.status_code == HTTPStatus.OK
    assert isinstance(response.json, list)
    assert len(response.json) == 1


def test_get_relation_to_sw_requirement(client, user_authentication, mapped_api_sr_sr_ts_db):
    """Read Test Specification mapping with parent mapped to sw requirement"""

    api, sw_requirement, api_sr_mapping, sr_sr_mapping, sr_ts_mapping = mapped_api_sr_sr_ts_db
    get_query = {
        "api-id": api.id,
        "relation-id": sr_sr_mapping.id,
        "relation-to": "sw-requirement",
        "user-id": user_authentication.json["id"],
        "token": user_authentication.json["token"],
    }

    response = client.get(_MAPPING_SW_REQUIREMENT_TEST_SPECIFICATIONS_URL, query_string=get_query)
    assert response.status_code == HTTPStatus.OK
    assert isinstance(response.json, list)
    assert len(response.json) == 1


# Test POST


@pytest.mark.parametrize(
    "mandatory_field", ["relation-id", "relation-to", "coverage", "sw-requirement", "test-specification"]
)
def test_post_missed_fields(client, client_db, user_authentication, mapped_api_sr_ts_db, utilities, mandatory_field):
    """Create Test Specification mapping without sending a mandatory field"""

    ut_test_specification_dict = get_test_specification_model(client_db, utilities).as_dict()
    ut_test_specification_dict.pop("id", None)

    api, sw_requirement, api_sr_mapping, sr_ts_mapping = mapped_api_sr_ts_db
    mapping_data = {
        "api-id": api.id,
        "relation-id": api_sr_mapping.id,
        "relation-to": "api",
        "coverage": 50,
        "sw-requirement": sw_requirement.as_dict(),
        "test-specification": ut_test_specification_dict,
        "user-id": user_authentication.json["id"],
        "token": user_authentication.json["token"],
    }
    mapping_data.pop(mandatory_field)
    response = client.post(_MAPPING_SW_REQUIREMENT_TEST_SPECIFICATIONS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_post_bad_payload(client, client_db, user_authentication, mapped_api_sr_ts_db, utilities):
    """Create Test Specification mapping sending an unexpected payload"""

    ut_test_specification_dict = get_test_specification_model(client_db, utilities).as_dict()
    ut_test_specification_dict.pop("id", None)

    # bad relation-to
    api, sw_requirement, api_sr_mapping, sr_ts_mapping = mapped_api_sr_ts_db
    mapping_data = {
        "api-id": api.id,
        "relation-id": api_sr_mapping.id,
        "relation-to": "unexpected value",
        "coverage": 50,
        "sw-requirement": sw_requirement.as_dict(),
        "test-specification": ut_test_specification_dict,
        "user-id": user_authentication.json["id"],
        "token": user_authentication.json["token"],
    }
    response = client.post(_MAPPING_SW_REQUIREMENT_TEST_SPECIFICATIONS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.BAD_REQUEST

    # bad relation-id
    mapping_data = {
        "api-id": api.id,
        "relation-id": 0,
        "relation-to": "api",
        "coverage": 50,
        "sw-requirement": sw_requirement.as_dict(),
        "test-specification": ut_test_specification_dict,
        "user-id": user_authentication.json["id"],
        "token": user_authentication.json["token"],
    }
    response = client.post(_MAPPING_SW_REQUIREMENT_TEST_SPECIFICATIONS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.parametrize(
    "test_specification_field", ["title", "preconditions", "test-description", "expected-behavior"]
)
def test_post_new_to_api(
    client, client_db, user_authentication, mapped_api_sr_ts_db, utilities, test_specification_field
):
    """Create a new Test Specification mapping related to a
    Software Component Reference Document Snippet
    """

    ut_test_specification_dict = get_test_specification_model(client_db, utilities).as_dict()
    ut_test_specification_dict = {k.replace("_", "-"): v for k, v in ut_test_specification_dict.items()}
    ut_test_specification_dict.pop("id")
    ut_test_specification_dict.pop(test_specification_field)

    api, sw_requirement, api_sr_mapping, sr_ts_mapping = mapped_api_sr_ts_db

    # Missed field on test-specification
    mapping_data = {
        "api-id": api.id,
        "coverage": 50,
        "relation-id": api_sr_mapping.id,
        "relation-to": "api",
        "sw-requirement": sw_requirement.as_dict(),
        "test-specification": ut_test_specification_dict,
        "user-id": user_authentication.json["id"],
        "token": user_authentication.json["token"],
    }

    response = client.post(_MAPPING_SW_REQUIREMENT_TEST_SPECIFICATIONS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.BAD_REQUEST

    # New Test Specification - Valid data
    ut_test_specification_dict = get_test_specification_model(client_db, utilities).as_dict()
    ut_test_specification_dict = {k.replace("_", "-"): v for k, v in ut_test_specification_dict.items()}
    ut_test_specification_dict.pop("id", None)

    mapping_data = {
        "api-id": api.id,
        "coverage": 50,
        "relation-id": api_sr_mapping.id,
        "relation-to": "api",
        "sw-requirement": sw_requirement.as_dict(),
        "test-specification": ut_test_specification_dict,
        "user-id": user_authentication.json["id"],
        "token": user_authentication.json["token"],
    }

    response = client.post(_MAPPING_SW_REQUIREMENT_TEST_SPECIFICATIONS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.OK
    assert isinstance(response.json, dict)

    # New Test Specification - Same data: Conflict
    response = client.post(_MAPPING_SW_REQUIREMENT_TEST_SPECIFICATIONS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.CONFLICT

    # Existing test specification - Valid data (not yet mapped)
    new_test_specification = get_test_specification_model(client_db, utilities)
    client_db.session.add(new_test_specification)
    client_db.session.commit()

    mapping_data = {
        "api-id": api.id,
        "coverage": 60,
        "relation-id": api_sr_mapping.id,
        "relation-to": "api",
        "sw-requirement": sw_requirement.as_dict(),
        "test-specification": new_test_specification.as_dict(),
        "user-id": user_authentication.json["id"],
        "token": user_authentication.json["token"],
    }

    response = client.post(_MAPPING_SW_REQUIREMENT_TEST_SPECIFICATIONS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.OK
    assert isinstance(response.json, dict)

    # Existing test specification - Same data: Conflict
    response = client.post(_MAPPING_SW_REQUIREMENT_TEST_SPECIFICATIONS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.CONFLICT

    # Unexisting test specification - Invalid data (deleted test specification)
    new_test_specification = get_test_specification_model(client_db, utilities)
    client_db.session.add(new_test_specification)
    client_db.session.commit()
    new_test_specification_dict = new_test_specification.as_dict()
    client_db.session.delete(new_test_specification)
    client_db.session.commit()

    mapping_data = {
        "api-id": api.id,
        "coverage": 70,
        "relation-id": api_sr_mapping.id,
        "relation-to": "api",
        "sw-requirement": sw_requirement.as_dict(),
        "test-specification": new_test_specification_dict,
        "user-id": user_authentication.json["id"],
        "token": user_authentication.json["token"],
    }

    response = client.post(_MAPPING_SW_REQUIREMENT_TEST_SPECIFICATIONS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_post_new_to_sw_requirement(client, client_db, user_authentication, mapped_api_sr_sr_ts_db, utilities):
    """Create a new Test Specification mapping related to a SW Requirement"""

    ut_test_specification_dict = get_test_specification_model(client_db, utilities).as_dict()
    ut_test_specification_dict.pop("id", None)
    ut_test_specification_dict = {k.replace("_", "-"): v for k, v in ut_test_specification_dict.items()}

    api, sw_requirement, api_sr_mapping, sr_sr_mapping, sr_ts_mapping = mapped_api_sr_sr_ts_db

    # Unexisting relation-id
    mapping_data = {
        "api-id": api.id,
        "coverage": 50,
        "relation-id": 0,
        "relation-to": "sw-requirement",
        "sw-requirement": sw_requirement.as_dict(),
        "test-specification": ut_test_specification_dict,
        "user-id": user_authentication.json["id"],
        "token": user_authentication.json["token"],
    }

    response = client.post(_MAPPING_SW_REQUIREMENT_TEST_SPECIFICATIONS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.NOT_FOUND

    # Unexisting mapping api
    mapping_data = {
        "api-id": UNMATCHING_ID,
        "coverage": 50,
        "relation-id": sr_sr_mapping.id,
        "relation-to": "sw-requirement",
        "sw-requirement": sw_requirement.as_dict(),
        "test-specification": ut_test_specification_dict,
        "user-id": user_authentication.json["id"],
        "token": user_authentication.json["token"],
    }

    response = client.post(_MAPPING_SW_REQUIREMENT_TEST_SPECIFICATIONS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.NOT_FOUND


# Test PUT


@pytest.mark.parametrize("mandatory_field", ["test-specification", "coverage", "relation-id"])
def test_put_miss_fields(client, client_db, user_authentication, mapped_api_sr_ts_db, utilities, mandatory_field):
    """Update Test Specification mapping sending missing mandatory field"""

    ut_test_specification_dict = get_test_specification_model(client_db, utilities).as_dict()

    api, sw_requirement, api_sr_mapping, sr_ts_mapping = mapped_api_sr_ts_db
    mapping_data = {
        "api-id": api.id,
        "coverage": 50,
        "relation-id": sr_ts_mapping.id,
        "sw-requirement": sw_requirement.as_dict(),
        "test-specification": ut_test_specification_dict,
        "user-id": user_authentication.json["id"],
        "token": user_authentication.json["token"],
    }
    mapping_data.pop(mandatory_field)
    response = client.put(_MAPPING_SW_REQUIREMENT_TEST_SPECIFICATIONS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_put_bad_payload(client, client_db, user_authentication, mapped_api_sr_ts_db, utilities):
    """Update Test Specification mapping sending an unexpected payload"""

    ut_test_specification_dict = get_test_specification_model(client_db, utilities).as_dict()

    api, sw_requirement, api_sr_mapping, sr_ts_mapping = mapped_api_sr_ts_db
    mapping_data = {
        "api-id": api.id,
        "relation-id": 0,
        "coverage": 50,
        "sw-requirement": sw_requirement.as_dict(),
        "test-specification": ut_test_specification_dict,
        "user-id": user_authentication.json["id"],
        "token": user_authentication.json["token"],
    }
    response = client.put(_MAPPING_SW_REQUIREMENT_TEST_SPECIFICATIONS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_put_ok(client, client_db, user_authentication, mapped_api_sr_ts_db, utilities):
    """Update Test Specification mapping"""

    api, sw_requirement, api_sr_mapping, sr_ts_mapping = mapped_api_sr_ts_db

    ut_test_specification_dict = sr_ts_mapping.test_specification.as_dict()

    # No changes
    mapping_data = {
        "api-id": api.id,
        "coverage": sr_ts_mapping.coverage,
        "relation-id": sr_ts_mapping.id,
        "sw-requirement": {"id": sw_requirement.id},
        "test-specification": ut_test_specification_dict,
        "user-id": user_authentication.json["id"],
        "token": user_authentication.json["token"],
    }
    response = client.put(_MAPPING_SW_REQUIREMENT_TEST_SPECIFICATIONS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.OK

    # Change coverage
    mapping_data["coverage"] = 85
    response = client.put(_MAPPING_SW_REQUIREMENT_TEST_SPECIFICATIONS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.OK
    assert response.json.get("coverage", 0) == 85

    # Change test-specification
    mapping_data["test-specification"]["title"] = f"{mapping_data['test-specification']['title']}-modified"
    # Add an unexisting field to test-specification
    mapping_data["test-specification"]["unexisting"] = "value"

    response = client.put(_MAPPING_SW_REQUIREMENT_TEST_SPECIFICATIONS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.OK


# Test DELETE


def test_delete_bad_payload(client, client_db, user_authentication, mapped_api_sr_ts_db, utilities):
    """Delete Test Specification mapping sending an unexpected payload"""

    api, sw_requirement, api_sr_mapping, sr_ts_mapping = mapped_api_sr_ts_db

    # miss relation-id
    mapping_data = {
        "api-id": api.id,
        "coverage": 50,
        "user-id": user_authentication.json["id"],
        "token": user_authentication.json["token"],
    }
    response = client.delete(_MAPPING_SW_REQUIREMENT_TEST_SPECIFICATIONS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.BAD_REQUEST

    # wrong relation-id
    delete_data = {
        "api-id": api.id,
        "relation-id": 0,
        "user-id": user_authentication.json["id"],
        "token": user_authentication.json["token"],
    }
    response = client.delete(_MAPPING_SW_REQUIREMENT_TEST_SPECIFICATIONS_URL, json=delete_data)
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_delete_miss_parent(client, client_db, user_authentication, mapped_api_sr_ts_db, utilities):
    """Delete an unexisting mapping"""

    api, sw_requirement, api_sr_mapping, sr_ts_mapping = mapped_api_sr_ts_db

    delete_data = {
        "api-id": api.id,
        "relation-id": UNMATCHING_ID,
        "user-id": user_authentication.json["id"],
        "token": user_authentication.json["token"],
    }

    response = client.delete(_MAPPING_SW_REQUIREMENT_TEST_SPECIFICATIONS_URL, json=delete_data)
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_delete_ok(client, client_db, user_authentication, mapped_api_sr_ts_db, utilities):
    """Delete a mapping"""

    api, sw_requirement, api_sr_mapping, sr_ts_mapping = mapped_api_sr_ts_db

    delete_data = {
        "api-id": api.id,
        "relation-id": sr_ts_mapping.id,
        "user-id": user_authentication.json["id"],
        "token": user_authentication.json["token"],
    }

    response = client.delete(_MAPPING_SW_REQUIREMENT_TEST_SPECIFICATIONS_URL, json=delete_data)
    assert response.status_code == HTTPStatus.OK

    get_query = {
        "api-id": api.id,
        "relation-id": api_sr_mapping.id,
        "relation-to": "api",
        "sw-requirement": {"id": api_sr_mapping.sw_requirement_id},
        "user-id": user_authentication.json["id"],
        "token": user_authentication.json["token"],
    }

    response = client.get(_MAPPING_SW_REQUIREMENT_TEST_SPECIFICATIONS_URL, query_string=get_query)
    assert response.status_code == HTTPStatus.OK
    assert isinstance(response.json, list)
    assert len(response.json) == 0
