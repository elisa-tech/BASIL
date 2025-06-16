import os
import pytest
import tempfile
from http import HTTPStatus
from db.models.user import UserModel
from db.models.api import ApiModel
from db.models.sw_requirement import SwRequirementModel
from db.models.api_sw_requirement import ApiSwRequirementModel
from db.models.sw_requirement_sw_requirement import SwRequirementSwRequirementModel
from conftest import UT_USER_EMAIL

_MAPPING_API_SW_REQUIREMENTS_URL = '/mapping/api/sw-requirements'
_MAPPING_SW_REQUIREMENT_SW_REQUIREMENTS_URL = '/mapping/sw-requirement/sw-requirements'

_UT_API_NAME = 'ut_api'
_UT_API_LIBRARY = 'ut_api_library'
_UT_API_LIBRARY_VERSION = 'v1.0.0'
_UT_API_CATEGORY = 'ut_api_category'
_UT_API_IMPLEMENTATION_FILE_FROM_ROW = 0
_UT_API_IMPLEMENTATION_FILE_TO_ROW = 42
_UT_API_TAGS = 'ut_api_tags'

_UT_API_SPEC_SECTION_NO_MAPPING = 'This section has no mapping.'
_UT_API_SPEC_SECTION_WITH_MAPPING = 'This section has mapping.'
_UT_API_SPEC_SECTION_TO_BE_MAPPED = 'This section is to be mapped.'
_UT_API_RAW_RESTRICTED_SPEC = 'BASIL UT: "Reader" user is not able to read this API.' \
                              f' Used for {_MAPPING_API_SW_REQUIREMENTS_URL}.'
_UT_API_RAW_UNMAPPED_SPEC = f'BASIL UT: {_UT_API_SPEC_SECTION_NO_MAPPING} Used for {_MAPPING_API_SW_REQUIREMENTS_URL}.'
_UT_API_RAW_MAPPED_SPEC = f'BASIL UT: {_UT_API_SPEC_SECTION_WITH_MAPPING} {_UT_API_SPEC_SECTION_TO_BE_MAPPED} ' \
                          f'Used for {_MAPPING_API_SW_REQUIREMENTS_URL}.'

_UT_SR_TITLE = 'BASIL UT SW REQUIREMENT TITLE'
_UT_SR_DESCRIPTION = 'BASIL UT SW REQUIREMENT DESCRIPTION'


def get_sw_requirement_model(client_db, utilities):
    user = client_db.session.query(UserModel).filter(UserModel.email == UT_USER_EMAIL).one()
    return SwRequirementModel(f'SW req #{utilities.generate_random_hex_string8()}',
                              'SW shall work as well as possible.', user)


def _filter_sections_mapped_by_sw_requirements(mapped_sections):
    return [section for section in mapped_sections if section['sw_requirements']]


def _get_sections_mapped_by_sw_requirements(client, api_id):
    response = client.get(_MAPPING_API_SW_REQUIREMENTS_URL, query_string={'api-id': api_id})
    assert response.status_code == HTTPStatus.OK
    return _filter_sections_mapped_by_sw_requirements(response.json['mapped'])


def _assert_mapped_sections(mapped_sections, expected_sections):
    current_sections = [s['section'] for s in mapped_sections].sort()
    assert current_sections == expected_sections.sort()


def _get_mapped_sw_requirement(mapped_section):
    relation_id = mapped_section['sw_requirements'][0]['relation_id']
    sw_requirement = mapped_section['sw_requirements'][0]['sw_requirement']
    return relation_id, sw_requirement


def _create_software_component(client_db, utilities):
    # create API
    user = client_db.session.query(UserModel).filter(UserModel.email == UT_USER_EMAIL).one()

    ut_api = ApiModel(_UT_API_NAME + '#' + utilities.generate_random_hex_string8(),
                      _UT_API_LIBRARY, _UT_API_LIBRARY_VERSION, 'stub.md',
                      _UT_API_CATEGORY, utilities.generate_random_hex_string8(), 'stub.impl',
                      _UT_API_IMPLEMENTATION_FILE_FROM_ROW, _UT_API_IMPLEMENTATION_FILE_TO_ROW,
                      _UT_API_TAGS, user)
    client_db.session.add(ut_api)
    client_db.session.commit()

    return ut_api


@pytest.fixture()
def restricted_api_db(client_db, ut_user_db, ut_reader_user_db, utilities):
    """ Create Api with read restriction for "reader" """

    user = client_db.session.query(UserModel).filter(UserModel.email == UT_USER_EMAIL).one()

    # create raw API specification
    raw_spec = tempfile.NamedTemporaryFile(mode="w", delete=False)
    raw_spec.write(_UT_API_RAW_RESTRICTED_SPEC)
    raw_spec.close()

    # create API
    ut_api = ApiModel(_UT_API_NAME + '#' + utilities.generate_random_hex_string8(),
                      _UT_API_LIBRARY, _UT_API_LIBRARY_VERSION, raw_spec.name,
                      _UT_API_CATEGORY, utilities.generate_random_hex_string8(), raw_spec.name + 'impl',
                      _UT_API_IMPLEMENTATION_FILE_FROM_ROW, _UT_API_IMPLEMENTATION_FILE_TO_ROW,
                      _UT_API_TAGS, user)
    ut_api.read_denials = f"[{ut_reader_user_db.id}]"
    client_db.session.add(ut_api)
    client_db.session.commit()

    yield ut_api

    # remove the raw_spec tempfile
    if os.path.isfile(raw_spec.name):
        os.remove(raw_spec.name)


@pytest.fixture()
def mapped_api_sr_sr_db(client_db, ut_user_db, utilities):
    """ Create a Sw Requirement mapped to another Sw requirement that is
    mapped to a section of the API Reference Document"""

    user = client_db.session.query(UserModel).filter(UserModel.email == UT_USER_EMAIL).one()

    # create raw API specification
    raw_spec = tempfile.NamedTemporaryFile(mode="w", delete=False)
    raw_spec.write(_UT_API_RAW_MAPPED_SPEC)
    raw_spec.close()

    # create API
    ut_api = ApiModel(_UT_API_NAME + '#' + utilities.generate_random_hex_string8(),
                      _UT_API_LIBRARY, _UT_API_LIBRARY_VERSION, raw_spec.name,
                      _UT_API_CATEGORY, utilities.generate_random_hex_string8(), raw_spec.name + 'impl',
                      _UT_API_IMPLEMENTATION_FILE_FROM_ROW, _UT_API_IMPLEMENTATION_FILE_TO_ROW,
                      _UT_API_TAGS, user)
    ut_sw_requirement = get_sw_requirement_model(client_db, utilities)
    ut_api_requirement_mapping = ApiSwRequirementModel(ut_api, ut_sw_requirement, _UT_API_SPEC_SECTION_WITH_MAPPING,
                                                       _UT_API_RAW_MAPPED_SPEC.find(_UT_API_SPEC_SECTION_WITH_MAPPING),
                                                       0, user)
    ut_nested_sw_requirement = get_sw_requirement_model(client_db, utilities)
    ut_requirement_requirement_mapping = SwRequirementSwRequirementModel(ut_api_requirement_mapping,
                                                                         None,
                                                                         ut_nested_sw_requirement,
                                                                         50,
                                                                         user)
    client_db.session.add(ut_api)
    client_db.session.add(ut_sw_requirement)
    client_db.session.add(ut_api_requirement_mapping)
    client_db.session.add(ut_nested_sw_requirement)
    client_db.session.add(ut_requirement_requirement_mapping)
    client_db.session.commit()

    yield (ut_api,
           ut_api_requirement_mapping,
           ut_requirement_requirement_mapping)

    # remove the raw_spec tempfile
    if os.path.isfile(raw_spec.name):
        os.remove(raw_spec.name)


@pytest.fixture()
def mapped_api_sr_sr_sr_db(client_db, ut_user_db, utilities):
    """ Create a Sw Requirement mapped to another Sw requirement that is
    mapped to another Sw Requirement """

    user = client_db.session.query(UserModel).filter(UserModel.email == UT_USER_EMAIL).one()

    # create raw API specification
    raw_spec = tempfile.NamedTemporaryFile(mode="w", delete=False)
    raw_spec.write(_UT_API_RAW_MAPPED_SPEC)
    raw_spec.close()

    # create API
    ut_api = ApiModel(_UT_API_NAME + '#' + utilities.generate_random_hex_string8(),
                      _UT_API_LIBRARY, _UT_API_LIBRARY_VERSION, raw_spec.name,
                      _UT_API_CATEGORY, utilities.generate_random_hex_string8(), raw_spec.name + 'impl',
                      _UT_API_IMPLEMENTATION_FILE_FROM_ROW, _UT_API_IMPLEMENTATION_FILE_TO_ROW,
                      _UT_API_TAGS, user)
    ut_sw_requirement = get_sw_requirement_model(client_db, utilities)
    ut_api_requirement_mapping = ApiSwRequirementModel(ut_api, ut_sw_requirement, _UT_API_SPEC_SECTION_WITH_MAPPING,
                                                       _UT_API_RAW_MAPPED_SPEC.find(_UT_API_SPEC_SECTION_WITH_MAPPING),
                                                       0, user)
    ut_nested_sw_requirement = get_sw_requirement_model(client_db, utilities)
    ut_requirement_requirement_mapping = SwRequirementSwRequirementModel(ut_api_requirement_mapping,
                                                                         None,
                                                                         ut_nested_sw_requirement,
                                                                         50,
                                                                         user)
    ut_nested_sw_requirement_2 = get_sw_requirement_model(client_db, utilities)
    ut_requirement_requirement_mapping_2 = SwRequirementSwRequirementModel(None,
                                                                           ut_requirement_requirement_mapping,
                                                                           ut_nested_sw_requirement_2,
                                                                           50,
                                                                           user)
    client_db.session.add(ut_api)
    client_db.session.add(ut_sw_requirement)
    client_db.session.add(ut_api_requirement_mapping)
    client_db.session.add(ut_nested_sw_requirement)
    client_db.session.add(ut_requirement_requirement_mapping)
    client_db.session.add(ut_nested_sw_requirement_2)
    client_db.session.add(ut_requirement_requirement_mapping_2)
    client_db.session.commit()

    yield (ut_api,
           ut_api_requirement_mapping,
           ut_requirement_requirement_mapping,
           ut_requirement_requirement_mapping_2)

    # remove the raw_spec tempfile
    if os.path.isfile(raw_spec.name):
        os.remove(raw_spec.name)


@pytest.fixture()
def sw_requirement_db(client_db, ut_user_db, utilities):
    """ Create SW requirement """

    user = client_db.session.query(UserModel).filter(UserModel.email == UT_USER_EMAIL).one()

    ut_sw_requirement = SwRequirementModel(f'SW req #{utilities.generate_random_hex_string8()}',
                                           'This is an unmapped requirement.', user)

    client_db.session.add(ut_sw_requirement)
    client_db.session.commit()

    yield ut_sw_requirement


def test_login(user_authentication):
    """ Just ensure that the test user is logged in """
    assert user_authentication.status_code == HTTPStatus.OK


# Common Tests


def test_put_unexisting_api(client):
    """ Use an API with invalid id """
    response = client.get(_MAPPING_SW_REQUIREMENT_SW_REQUIREMENTS_URL, query_string={'api-id': 0, 'relation-id': 0})
    assert response.status_code == HTTPStatus.NOT_FOUND

    response = client.post(_MAPPING_SW_REQUIREMENT_SW_REQUIREMENTS_URL, json={'api-id': 0})
    assert response.status_code == HTTPStatus.NOT_FOUND

    response = client.put(_MAPPING_SW_REQUIREMENT_SW_REQUIREMENTS_URL, json={'api-id': 0})
    assert response.status_code == HTTPStatus.NOT_FOUND

    response = client.delete(_MAPPING_SW_REQUIREMENT_SW_REQUIREMENTS_URL, json={'api-id': 0})
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_put_unauthorized_fail(client, client_db, restricted_api_db, ut_reader_user_db, utilities):
    """ Use an API with write restrictions: PUT is not allowed for unauthorized users """

    ut_sw_requirement_dict = get_sw_requirement_model(client_db, utilities).as_dict()
    ut_sw_requirement_dict.pop('id', None)

    mapping_data = {
        'api-id': restricted_api_db.id,
        'relation-to': 'api',
        'relation-id': 0,
        'coverage': 50,
        'sw-requirement': ut_sw_requirement_dict,
        'parent-sw-requirement': {
            'id': 0
        },
        'user-id': ut_reader_user_db.id,
        'token': ut_reader_user_db.token
    }
    response = client.get(_MAPPING_SW_REQUIREMENT_SW_REQUIREMENTS_URL, query_string=mapping_data)
    assert response.status_code == HTTPStatus.UNAUTHORIZED

    response = client.post(_MAPPING_SW_REQUIREMENT_SW_REQUIREMENTS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.UNAUTHORIZED

    response = client.put(_MAPPING_SW_REQUIREMENT_SW_REQUIREMENTS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.UNAUTHORIZED

    response = client.delete(_MAPPING_SW_REQUIREMENT_SW_REQUIREMENTS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.UNAUTHORIZED


# Test GET

@pytest.mark.parametrize('mandatory_field', ['relation-id', 'relation-to'])
def test_get_missed_fields(client, user_authentication, mapped_api_sr_sr_db, mandatory_field):
    """ Read Sw Requirement without sending a mandatory field  """

    api, api_sr_mapping, api_sr_sr_mapping = mapped_api_sr_sr_db
    get_query = {
        'api-id': api.id,
        'relation-id': api_sr_mapping.id,
        'relation-to': 'api',
        'user-id': user_authentication.json['id'],
        'token': user_authentication.json['token']
    }
    get_query.pop(mandatory_field)
    response = client.get(_MAPPING_SW_REQUIREMENT_SW_REQUIREMENTS_URL, query_string=get_query)
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_get_bad_payload(client, user_authentication, mapped_api_sr_sr_db):
    """ Read Sw Requirement sending an unexpected payload  """

    api, api_sr_mapping, api_sr_sr_mapping = mapped_api_sr_sr_db
    get_query = {
        'api-id': api.id,
        'relation-id': api_sr_mapping.id,
        'relation-to': 'unexpected value',
        'user-id': user_authentication.json['id'],
        'token': user_authentication.json['token']
    }
    response = client.get(_MAPPING_SW_REQUIREMENT_SW_REQUIREMENTS_URL, query_string=get_query)
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_get_relation_to_api(client, user_authentication, mapped_api_sr_sr_db):
    """ Read Sw Requirement with parent mapped to api """

    api, api_sr_mapping, api_sr_sr_mapping = mapped_api_sr_sr_db
    get_query = {
        'api-id': api.id,
        'relation-id': api_sr_mapping.id,
        'relation-to': 'api',
        'user-id': user_authentication.json['id'],
        'token': user_authentication.json['token']
    }

    response = client.get(_MAPPING_SW_REQUIREMENT_SW_REQUIREMENTS_URL, query_string=get_query)
    assert response.status_code == HTTPStatus.OK
    assert isinstance(response.json, list)
    assert len(response.json) == 1


def test_get_relation_to_sw_requirement(client, user_authentication, mapped_api_sr_sr_sr_db):
    """ Read Sw Requirement with parent mapped to sw requirement """

    api, api_sr_mapping, api_sr_sr_mapping, api_sr_sr_sr_mapping = mapped_api_sr_sr_sr_db
    get_query = {
        'api-id': api.id,
        'relation-id': api_sr_sr_mapping.id,
        'relation-to': 'sw-requirement',
        'user-id': user_authentication.json['id'],
        'token': user_authentication.json['token']
    }

    response = client.get(_MAPPING_SW_REQUIREMENT_SW_REQUIREMENTS_URL, query_string=get_query)
    assert response.status_code == HTTPStatus.OK
    assert isinstance(response.json, list)
    assert len(response.json) == 1


# Test POST

@pytest.mark.parametrize('mandatory_field', ['relation-id', 'relation-to', 'parent-sw-requirement'])
def test_post_missed_fields(client, client_db, user_authentication, mapped_api_sr_sr_db, utilities, mandatory_field):
    """ File a nested Sw Requirement without sending a mandatory field  """

    ut_sw_requirement_dict = get_sw_requirement_model(client_db, utilities).as_dict()
    ut_sw_requirement_dict.pop('id', None)

    # skip relation-to
    api, api_sr_mapping, api_sr_sr_mapping = mapped_api_sr_sr_db
    mapping_data = {
        'api-id': api.id,
        'relation-id': 0,
        'relation-to': 'api',
        'coverage': 50,
        'sw-requirement': ut_sw_requirement_dict,
        'parent-sw-requirement': {
            'id': 0
        },
        'user-id': user_authentication.json['id'],
        'token': user_authentication.json['token']
    }
    mapping_data.pop(mandatory_field)
    response = client.post(_MAPPING_SW_REQUIREMENT_SW_REQUIREMENTS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.BAD_REQUEST

    # skip parent-sw-requirement.id
    mapping_data = {
        'api-id': api.id,
        'relation-id': 0,
        'relation-to': 'api',
        'coverage': 50,
        'sw-requirement': ut_sw_requirement_dict,
        'parent-sw-requirement': {
        },
        'user-id': user_authentication.json['id'],
        'token': user_authentication.json['token']
    }
    response = client.post(_MAPPING_SW_REQUIREMENT_SW_REQUIREMENTS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_post_bad_payload(client, client_db, user_authentication, mapped_api_sr_sr_db, utilities):
    """ Write Sw Requirement mapping sending an unexpected payload  """

    ut_sw_requirement_dict = get_sw_requirement_model(client_db, utilities).as_dict()
    ut_sw_requirement_dict.pop('id', None)

    # bad relation-to
    api, api_sr_mapping, api_sr_sr_mapping = mapped_api_sr_sr_db
    mapping_data = {
        'api-id': api.id,
        'relation-id': api_sr_mapping.id,
        'relation-to': 'unexpected value',
        'coverage': 50,
        'sw-requirement': ut_sw_requirement_dict,
        'parent-sw-requirement': {
            'id': api_sr_mapping.sw_requirement_id
        },
        'user-id': user_authentication.json['id'],
        'token': user_authentication.json['token']
    }
    response = client.post(_MAPPING_SW_REQUIREMENT_SW_REQUIREMENTS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.BAD_REQUEST

    # bad relation-id
    api, api_sr_mapping, api_sr_sr_mapping = mapped_api_sr_sr_db
    mapping_data = {
        'api-id': api.id,
        'relation-id': 0,
        'relation-to': 'api',
        'coverage': 50,
        'sw-requirement': ut_sw_requirement_dict,
        'parent-sw-requirement': {
            'id': api_sr_mapping.sw_requirement_id
        },
        'user-id': user_authentication.json['id'],
        'token': user_authentication.json['token']
    }
    response = client.post(_MAPPING_SW_REQUIREMENT_SW_REQUIREMENTS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.parametrize('sw_requirement_field', ['title', 'description'])
def test_post_new_to_api(client, client_db, user_authentication, mapped_api_sr_sr_db, utilities, sw_requirement_field):
    """ Write a new Sw Requirement mapping related to a
    Software Component Reference Document Snippet
    """

    ut_sw_requirement_dict = get_sw_requirement_model(client_db, utilities).as_dict()
    ut_sw_requirement_dict.pop('id')
    ut_sw_requirement_dict.pop(sw_requirement_field)

    api, api_sr_mapping, api_sr_sr_mapping = mapped_api_sr_sr_db

    # Missed field on sw-requirement
    mapping_data = {
        'api-id': api.id,
        'coverage': 50,
        'relation-id': api_sr_mapping.id,
        'relation-to': 'api',
        'sw-requirement': ut_sw_requirement_dict,
        'parent-sw-requirement': {
            'id': api_sr_mapping.sw_requirement_id
        },
        'user-id': user_authentication.json['id'],
        'token': user_authentication.json['token']
    }

    response = client.post(_MAPPING_SW_REQUIREMENT_SW_REQUIREMENTS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.BAD_REQUEST

    # New Requirement - Valid data
    ut_sw_requirement_dict = get_sw_requirement_model(client_db, utilities).as_dict()
    ut_sw_requirement_dict.pop('id', None)

    mapping_data = {
        'api-id': api.id,
        'coverage': 50,
        'relation-id': api_sr_mapping.id,
        'relation-to': 'api',
        'sw-requirement': ut_sw_requirement_dict,
        'parent-sw-requirement': {
            'id': api_sr_mapping.sw_requirement_id
        },
        'user-id': user_authentication.json['id'],
        'token': user_authentication.json['token']
    }

    response = client.post(_MAPPING_SW_REQUIREMENT_SW_REQUIREMENTS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.OK
    assert isinstance(response.json, dict)
    assert response.json.get("__tablename__", "") == SwRequirementSwRequirementModel.__tablename__

    # New Requirement - Same data: Conflict
    response = client.post(_MAPPING_SW_REQUIREMENT_SW_REQUIREMENTS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.CONFLICT

    # Existing requirement - Valid data (not yet mapped)
    new_sw_requirement = get_sw_requirement_model(client_db, utilities)
    client_db.session.add(new_sw_requirement)
    client_db.session.commit()

    mapping_data = {
        'api-id': api.id,
        'coverage': 50,
        'relation-id': api_sr_mapping.id,
        'relation-to': 'api',
        'sw-requirement': new_sw_requirement.as_dict(),
        'parent-sw-requirement': {
            'id': api_sr_mapping.sw_requirement_id
        },
        'user-id': user_authentication.json['id'],
        'token': user_authentication.json['token']
    }

    response = client.post(_MAPPING_SW_REQUIREMENT_SW_REQUIREMENTS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.OK
    assert isinstance(response.json, dict)
    assert response.json.get("__tablename__", "") == SwRequirementSwRequirementModel.__tablename__

    # Existing requirement - Same data: Conflict
    response = client.post(_MAPPING_SW_REQUIREMENT_SW_REQUIREMENTS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.CONFLICT

    # Unexisting requirement - Unvalid data (deleted requirement)
    new_sw_requirement = get_sw_requirement_model(client_db, utilities)
    client_db.session.add(new_sw_requirement)
    client_db.session.commit()
    new_sw_requirement_dict = new_sw_requirement.as_dict()
    client_db.session.delete(new_sw_requirement)
    client_db.session.commit()

    mapping_data = {
        'api-id': api.id,
        'coverage': 50,
        'relation-id': api_sr_mapping.id,
        'relation-to': 'api',
        'sw-requirement': new_sw_requirement_dict,
        'parent-sw-requirement': {
            'id': api_sr_mapping.sw_requirement_id
        },
        'user-id': user_authentication.json['id'],
        'token': user_authentication.json['token']
    }

    response = client.post(_MAPPING_SW_REQUIREMENT_SW_REQUIREMENTS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_post_new_to_sw_requirement(client, client_db, user_authentication, mapped_api_sr_sr_sr_db, utilities):
    """ Write a new Sw Requirement mapping related to a Sw Requirement
    """

    ut_sw_requirement_dict = get_sw_requirement_model(client_db, utilities).as_dict()

    new_api = _create_software_component(client_db, utilities)

    api, api_sr_mapping, api_sr_sr_mapping, api_sr_sr_sr_mapping = mapped_api_sr_sr_sr_db

    # Unexisting relation-id
    mapping_data = {
        'api-id': api.id,
        'coverage': 50,
        'relation-id': 0,
        'relation-to': 'sw-requirement',
        'sw-requirement': ut_sw_requirement_dict,
        'parent-sw-requirement': {
            'id': api_sr_sr_mapping.sw_requirement_id
        },
        'user-id': user_authentication.json['id'],
        'token': user_authentication.json['token']
    }

    response = client.post(_MAPPING_SW_REQUIREMENT_SW_REQUIREMENTS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.NOT_FOUND

    # Wrong api-id
    mapping_data = {
        'api-id': new_api.id,
        'coverage': 50,
        'relation-id': api_sr_sr_mapping.id,
        'relation-to': 'sw-requirement',
        'sw-requirement': ut_sw_requirement_dict,
        'parent-sw-requirement': {
            'id': api_sr_sr_mapping.sw_requirement_id
        },
        'user-id': user_authentication.json['id'],
        'token': user_authentication.json['token']
    }

    response = client.post(_MAPPING_SW_REQUIREMENT_SW_REQUIREMENTS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.BAD_REQUEST

    # Unexisting parent sw requirement
    mapping_data = {
        'api-id': api.id,
        'coverage': 50,
        'relation-id': api_sr_sr_mapping.id,
        'relation-to': 'sw-requirement',
        'sw-requirement': ut_sw_requirement_dict,
        'parent-sw-requirement': {
            'id': 0
        },
        'user-id': user_authentication.json['id'],
        'token': user_authentication.json['token']
    }

    response = client.post(_MAPPING_SW_REQUIREMENT_SW_REQUIREMENTS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.NOT_FOUND

    api_sr_mapping.api_id = new_api.id
    client_db.session.add(api_sr_sr_mapping)
    client_db.session.delete(new_api)
    client_db.session.commit()

    # Unexisting mapping api
    mapping_data = {
        'api-id': api.id,
        'coverage': 50,
        'relation-id': api_sr_sr_mapping.id,
        'relation-to': 'sw-requirement',
        'sw-requirement': ut_sw_requirement_dict,
        'parent-sw-requirement': {
            'id': api_sr_sr_mapping.sw_requirement_id
        },
        'user-id': user_authentication.json['id'],
        'token': user_authentication.json['token']
    }

    response = client.post(_MAPPING_SW_REQUIREMENT_SW_REQUIREMENTS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.NOT_FOUND


# Test PUT


def test_put_bad_payload(client, client_db, user_authentication, mapped_api_sr_sr_db, utilities):
    """ Update Sw Requirement mapping sending an unexpected payload  """

    ut_sw_requirement_dict = get_sw_requirement_model(client_db, utilities).as_dict()
    ut_sw_requirement_dict.pop('id', None)

    # miss relation-id
    api, api_sr_mapping, api_sr_sr_mapping = mapped_api_sr_sr_db
    mapping_data = {
        'api-id': api.id,
        'coverage': 50,
        'sw-requirement': ut_sw_requirement_dict,
        'parent-sw-requirement': {
            'id': api_sr_mapping.sw_requirement_id
        },
        'user-id': user_authentication.json['id'],
        'token': user_authentication.json['token']
    }
    response = client.put(_MAPPING_SW_REQUIREMENT_SW_REQUIREMENTS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.BAD_REQUEST

    # bad relation-id
    api, api_sr_mapping, api_sr_sr_mapping = mapped_api_sr_sr_db
    mapping_data = {
        'api-id': api.id,
        'relation-id': 0,
        'coverage': 50,
        'sw-requirement': ut_sw_requirement_dict,
        'parent-sw-requirement': {
            'id': api_sr_mapping.sw_requirement_id
        },
        'user-id': user_authentication.json['id'],
        'token': user_authentication.json['token']
    }
    response = client.put(_MAPPING_SW_REQUIREMENT_SW_REQUIREMENTS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_put_ok(client, client_db, user_authentication, mapped_api_sr_sr_db, utilities):
    """ Update Sw Requirement mapping  """

    api, api_sr_mapping, api_sr_sr_mapping = mapped_api_sr_sr_db

    # parent mapped to api
    ut_sw_requirement_dict = get_sw_requirement_model(client_db, utilities).as_dict()
    ut_sw_requirement_dict.pop('id', None)

    mapping_data = {
        'api-id': api.id,
        'coverage': 50,
        'relation-id': api_sr_mapping.id,
        'relation-to': 'api',
        'sw-requirement': ut_sw_requirement_dict,
        'parent-sw-requirement': {
            'id': api_sr_mapping.sw_requirement_id
        },
        'user-id': user_authentication.json['id'],
        'token': user_authentication.json['token']
    }

    response = client.post(_MAPPING_SW_REQUIREMENT_SW_REQUIREMENTS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.OK
    assert isinstance(response.json, dict)
    assert response.json.get("__tablename__", "") == SwRequirementSwRequirementModel.__tablename__

    # No changes
    mapping_data = {
        'api-id': api.id,
        'coverage': 50,
        'relation-id': response.json.get("relation_id", ""),
        'sw-requirement': ut_sw_requirement_dict,
        'user-id': user_authentication.json['id'],
        'token': user_authentication.json['token']
    }
    response = client.put(_MAPPING_SW_REQUIREMENT_SW_REQUIREMENTS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.OK
    assert response.json.get("__tablename__", "") == SwRequirementSwRequirementModel.__tablename__
    assert response.json.get("version", "") == "1.1"

    # Change coverage
    mapping_data['coverage'] = 75
    response = client.put(_MAPPING_SW_REQUIREMENT_SW_REQUIREMENTS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.OK
    assert response.json.get("__tablename__", "") == SwRequirementSwRequirementModel.__tablename__
    assert response.json.get("version", "") == "1.2"

    # Change sw-requirement
    mapping_data['sw-requirement']['title'] = f"{mapping_data['sw-requirement']['title']}-mod"
    # Add an unexisting field to sw-requirement
    mapping_data['sw-requirement']['unexisting'] = "value"

    response = client.put(_MAPPING_SW_REQUIREMENT_SW_REQUIREMENTS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.OK
    assert response.json.get("__tablename__", "") == SwRequirementSwRequirementModel.__tablename__
    assert response.json.get("version", "") == "2.2"


# Test Delete


def test_delete_bad_payload(client, client_db, user_authentication, mapped_api_sr_sr_db, utilities):
    """ Update Sw Requirement mapping sending an unexpected payload  """

    ut_sw_requirement_dict = get_sw_requirement_model(client_db, utilities).as_dict()
    ut_sw_requirement_dict.pop('id', None)

    # miss relation-id
    api, api_sr_mapping, api_sr_sr_mapping = mapped_api_sr_sr_db
    mapping_data = {
        'api-id': api.id,
        'coverage': 50,
        'sw-requirement': ut_sw_requirement_dict,
        'parent-sw-requirement': {
            'id': api_sr_mapping.sw_requirement_id
        },
        'user-id': user_authentication.json['id'],
        'token': user_authentication.json['token']
    }
    response = client.delete(_MAPPING_SW_REQUIREMENT_SW_REQUIREMENTS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.BAD_REQUEST

    mapping_data = {
        'api-id': api.id,
        'coverage': 50,
        'relation-id': api_sr_mapping.id,
        'relation-to': 'api',
        'sw-requirement': ut_sw_requirement_dict,
        'parent-sw-requirement': {
            'id': api_sr_mapping.sw_requirement_id
        },
        'user-id': user_authentication.json['id'],
        'token': user_authentication.json['token']
    }

    response = client.post(_MAPPING_SW_REQUIREMENT_SW_REQUIREMENTS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.OK
    assert isinstance(response.json, dict)
    assert response.json.get("__tablename__", "") == SwRequirementSwRequirementModel.__tablename__

    # wrong relation-id
    delete_data = {
        'api-id': api.id,
        'relation-id': 0,
        'user-id': user_authentication.json['id'],
        'token': user_authentication.json['token']
    }
    response = client.delete(_MAPPING_SW_REQUIREMENT_SW_REQUIREMENTS_URL, json=delete_data)
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_delete_miss_parent(client, client_db, user_authentication, mapped_api_sr_sr_db, utilities):
    """ Delete an unexsting mapping """

    ut_sw_requirement_dict = get_sw_requirement_model(client_db, utilities).as_dict()
    ut_sw_requirement_dict.pop('id', None)
    api, api_sr_mapping, api_sr_sr_mapping = mapped_api_sr_sr_db

    mapping_data = {
        'api-id': api.id,
        'coverage': 50,
        'relation-id': api_sr_mapping.id,
        'relation-to': 'api',
        'sw-requirement': ut_sw_requirement_dict,
        'parent-sw-requirement': {
            'id': api_sr_mapping.sw_requirement_id
        },
        'user-id': user_authentication.json['id'],
        'token': user_authentication.json['token']
    }

    response = client.post(_MAPPING_SW_REQUIREMENT_SW_REQUIREMENTS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.OK
    assert isinstance(response.json, dict)
    assert response.json.get("__tablename__", "") == SwRequirementSwRequirementModel.__tablename__

    client_db.session.delete(api_sr_mapping)
    client_db.session.commit()

    delete_data = {
        'api-id': api.id,
        'relation-id': response.json.get("relation_id", ""),
        'user-id': user_authentication.json['id'],
        'token': user_authentication.json['token']
    }

    response = client.delete(_MAPPING_SW_REQUIREMENT_SW_REQUIREMENTS_URL, json=delete_data)
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_delete_ok(client, client_db, user_authentication, mapped_api_sr_sr_db, utilities):
    """ Delete a mapping  """

    ut_sw_requirement_dict = get_sw_requirement_model(client_db, utilities).as_dict()
    ut_sw_requirement_dict.pop('id', None)
    api, api_sr_mapping, api_sr_sr_mapping = mapped_api_sr_sr_db

    mapping_data = {
        'api-id': api.id,
        'coverage': 50,
        'relation-id': api_sr_mapping.id,
        'relation-to': 'api',
        'sw-requirement': ut_sw_requirement_dict,
        'parent-sw-requirement': {
            'id': api_sr_mapping.sw_requirement_id
        },
        'user-id': user_authentication.json['id'],
        'token': user_authentication.json['token']
    }

    response = client.post(_MAPPING_SW_REQUIREMENT_SW_REQUIREMENTS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.OK
    assert isinstance(response.json, dict)
    assert response.json.get("__tablename__", "") == SwRequirementSwRequirementModel.__tablename__

    delete_data = {
        'api-id': api.id,
        'relation-id': response.json.get("relation_id", ""),
        'user-id': user_authentication.json['id'],
        'token': user_authentication.json['token']
    }

    response = client.delete(_MAPPING_SW_REQUIREMENT_SW_REQUIREMENTS_URL, json=delete_data)
    assert response.status_code == HTTPStatus.OK

    get_query = {
        'api-id': api.id,
        'relation-id': delete_data["relation-id"],
        'relation-to': 'api',
        'user-id': user_authentication.json['id'],
        'token': user_authentication.json['token']
    }

    response = client.get(_MAPPING_SW_REQUIREMENT_SW_REQUIREMENTS_URL, query_string=get_query)
    assert response.status_code == HTTPStatus.OK
    assert isinstance(response.json, list)
    assert len(response.json) == 0
