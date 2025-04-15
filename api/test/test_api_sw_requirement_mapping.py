import os
import pytest
import tempfile
from db import db_orm
from db.models.user import UserModel
from db.models.api import ApiModel
from db.models.sw_requirement import SwRequirementModel
from db.models.api_sw_requirement import ApiSwRequirementModel
from conftest import UT_USER_EMAIL
from conftest import DB_NAME


_MAPPING_API_SW_REQUIREMENTS_URL = '/mapping/api/sw-requirements'

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


def _get_sections_mapped_by_sw_requirements(mapped_sections):
    return [section for section in mapped_sections if section['sw_requirements']]


@pytest.fixture()
def restricted_api_db(client_db, ut_user_db, ut_reader_user_db, utilities):
    """ Create Api with read restriction for "reader" """

    dbi = db_orm.DbInterface(DB_NAME)

    user = dbi.session.query(UserModel).filter(UserModel.email == UT_USER_EMAIL).one()

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
    dbi.session.add(ut_api)
    dbi.session.commit()

    yield ut_api

    # remove the raw_spec tempfile
    if os.path.isfile(raw_spec.name):
        os.remove(raw_spec.name)


@pytest.fixture()
def unmapped_api_db(client_db, ut_user_db, utilities):
    """ Create Api with no mapped sections """

    dbi = db_orm.DbInterface(DB_NAME)

    user = dbi.session.query(UserModel).filter(UserModel.email == UT_USER_EMAIL).one()

    # create raw API specification
    raw_spec = tempfile.NamedTemporaryFile(mode="w", delete=False)
    raw_spec.write(_UT_API_RAW_UNMAPPED_SPEC)
    raw_spec.close()

    # create API
    ut_api = ApiModel(_UT_API_NAME + '#' + utilities.generate_random_hex_string8(),
                      _UT_API_LIBRARY, _UT_API_LIBRARY_VERSION, raw_spec.name,
                      _UT_API_CATEGORY, utilities.generate_random_hex_string8(), raw_spec.name + 'impl',
                      _UT_API_IMPLEMENTATION_FILE_FROM_ROW, _UT_API_IMPLEMENTATION_FILE_TO_ROW,
                      _UT_API_TAGS, user)
    dbi.session.add(ut_api)
    dbi.session.commit()

    yield ut_api

    # remove the raw_spec tempfile
    if os.path.isfile(raw_spec.name):
        os.remove(raw_spec.name)


@pytest.fixture()
def mapped_api_db(client_db, ut_user_db, utilities):
    """ Create Api with one mapped section """

    dbi = db_orm.DbInterface(DB_NAME)

    user = dbi.session.query(UserModel).filter(UserModel.email == UT_USER_EMAIL).one()

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
    ut_sw_requirement = SwRequirementModel(f'SW req #{utilities.generate_random_hex_string8()}',
                                           'SW shall work as well as possible.', user)
    ut_api_requirement_mapping = ApiSwRequirementModel(ut_api, ut_sw_requirement, _UT_API_SPEC_SECTION_WITH_MAPPING,
                                                       _UT_API_RAW_MAPPED_SPEC.find(_UT_API_SPEC_SECTION_WITH_MAPPING),
                                                       0, user)

    dbi.session.add(ut_api)
    dbi.session.add(ut_sw_requirement)
    dbi.session.add(ut_api_requirement_mapping)
    dbi.session.commit()

    yield ut_api

    # remove the raw_spec tempfile
    if os.path.isfile(raw_spec.name):
        os.remove(raw_spec.name)


def test_login(user_authentication):
    """ Just ensure that the test user is logged in """
    assert user_authentication.status_code == 200


# Test GET

def test_get_unauthorized_ok(client, unmapped_api_db):
    """ Read API without read restrictions: GET is allowed for all users """
    response = client.get(_MAPPING_API_SW_REQUIREMENTS_URL, query_string={'api-id': unmapped_api_db.id})
    assert response.status_code == 200
    assert 'mapped' in response.json
    assert 'unmapped' in response.json


def test_get_unauthorized_fail(client, restricted_api_db):
    """ Read API with read restrictions: GET is not allowed for unauthorized users """

    response = client.get(_MAPPING_API_SW_REQUIREMENTS_URL, query_string={'api-id': restricted_api_db.id})
    assert response.status_code == 401
    assert 'mapped' not in response.json
    assert 'unmapped' not in response.json


def test_get_authorized_restricted_fail(client, reader_authentication, restricted_api_db):
    """ Read API with read restrictions for "reader" user: GET is not allowed for this user """

    get_query = {
        'user-id': reader_authentication.json['id'],
        'token': reader_authentication.json['token'],
        'api-id': restricted_api_db.id
    }
    response = client.get(_MAPPING_API_SW_REQUIREMENTS_URL, query_string=get_query)
    assert response.status_code == 401
    assert 'mapped' not in response.json
    assert 'unmapped' not in response.json


def test_get_authorized_restricted_ok(client, user_authentication, restricted_api_db):
    """ Read API with read restrictions: GET is allowed for the author of the API """

    get_query = {
        'user-id': user_authentication.json['id'],
        'token': user_authentication.json['token'],
        'api-id': restricted_api_db.id
    }
    response = client.get(_MAPPING_API_SW_REQUIREMENTS_URL, query_string=get_query)
    assert response.status_code == 200
    assert 'mapped' in response.json
    assert 'unmapped' in response.json


def test_get_incorrect_request(client, user_authentication, unmapped_api_db):
    """ Read API without specification of the api-id """

    get_query = {
        'user-id': user_authentication.json['id'],
        'token': user_authentication.json['token']
    }
    response = client.get(_MAPPING_API_SW_REQUIREMENTS_URL, query_string=get_query)
    assert response.status_code == 400
    assert 'mapped' not in response.json
    assert 'unmapped' not in response.json


def test_get_missing_api_fail(client, user_authentication, unmapped_api_db):
    """ Read non-existent API """

    non_existent_id = 42000
    # ensure this api id is not exist
    dbi = db_orm.DbInterface(DB_NAME)
    supposed_api = dbi.session.query(ApiModel).get(non_existent_id)
    assert supposed_api is None

    # read non-existent API
    get_query = {
        'user-id': user_authentication.json['id'],
        'token': user_authentication.json['token'],
        'api-id': non_existent_id
    }
    response = client.get(_MAPPING_API_SW_REQUIREMENTS_URL, query_string=get_query)
    assert response.status_code == 404
    assert 'mapped' not in response.json
    assert 'unmapped' not in response.json


def test_get_mapped(client, mapped_api_db):
    """ Nominal test for GET """

    response = client.get(_MAPPING_API_SW_REQUIREMENTS_URL, query_string={'api-id': mapped_api_db.id})
    assert response.status_code == 200
    # there should be only one mapped section: _UT_API_SPEC_SECTION_WITH_MAPPING
    mapped_sections = _get_sections_mapped_by_sw_requirements(response.json['mapped'])
    assert len(mapped_sections) == 1
    assert mapped_sections[0]['section'] == _UT_API_SPEC_SECTION_WITH_MAPPING


# Test POST

def test_post_ok(client, user_authentication, unmapped_api_db, utilities):
    """ Nominal test for mapping a section """

    api_id = unmapped_api_db.id
    sw_requirement_title = f'SW req #{utilities.generate_random_hex_string8()}'

    # ensure there is no mapped SW requirements for this API
    response = client.get(_MAPPING_API_SW_REQUIREMENTS_URL, query_string={'api-id': api_id})
    assert response.status_code == 200
    mapped_sections = _get_sections_mapped_by_sw_requirements(response.json['mapped'])
    assert len(mapped_sections) == 0

    # map a SW requirement to unmapped section
    mapping_data = {
        'user-id': user_authentication.json['id'],
        'token': user_authentication.json['token'],
        'api-id': api_id,
        'section': _UT_API_SPEC_SECTION_NO_MAPPING,
        'offset': _UT_API_RAW_UNMAPPED_SPEC.find(_UT_API_SPEC_SECTION_NO_MAPPING),
        'coverage': 0,
        'sw-requirement': {
            'title': sw_requirement_title,
            'description': 'SW requirement description'
        }
    }
    response = client.post(_MAPPING_API_SW_REQUIREMENTS_URL, json=mapping_data)
    assert response.status_code == 200

    # ensure SW requirement is added
    response = client.get(_MAPPING_API_SW_REQUIREMENTS_URL, query_string={'api-id': api_id})
    assert response.status_code == 200
    mapped_sections = _get_sections_mapped_by_sw_requirements(response.json['mapped'])
    assert len(mapped_sections) == 1  # there should be only one mapped section
    assert mapped_sections[0]['section'] == _UT_API_SPEC_SECTION_NO_MAPPING
    assert mapped_sections[0]['offset'] == _UT_API_RAW_UNMAPPED_SPEC.find(_UT_API_SPEC_SECTION_NO_MAPPING)
    mapped_sw_requirements = mapped_sections[0]['sw_requirements']
    assert len(mapped_sw_requirements) == 1  # there should be only one SW requirement
    assert mapped_sw_requirements[0]['sw_requirement']['title'] == sw_requirement_title
    assert mapped_sw_requirements[0]['created_by'] == UT_USER_EMAIL


def test_put_ok(client, user_authentication, mapped_api_db):
    """ Nominal test for mapping update """

    api_id = mapped_api_db.id
    # ensure there is a mapped SW requirement for this API
    response = client.get(_MAPPING_API_SW_REQUIREMENTS_URL, query_string={'api-id': api_id})
    assert response.status_code == 200
    # there should be only one mapped section: _UT_API_SPEC_SECTION_WITH_MAPPING
    mapped_sections = _get_sections_mapped_by_sw_requirements(response.json['mapped'])
    assert len(mapped_sections) == 1
    assert mapped_sections[0]['section'] == _UT_API_SPEC_SECTION_WITH_MAPPING
    # get the relation ID and SW requirement
    relation_id = mapped_sections[0]['sw_requirements'][0]['relation_id']
    sw_requirement = mapped_sections[0]['sw_requirements'][0]['sw_requirement']

    # update mapping from _UT_API_SPEC_SECTION_WITH_MAPPING to _UT_API_SPEC_SECTION_TO_BE_MAPPED
    mapping_data = {
        'user-id': user_authentication.json['id'],
        'token': user_authentication.json['token'],
        'relation-id': relation_id,
        'api-id': api_id,
        'section': _UT_API_SPEC_SECTION_TO_BE_MAPPED,
        'offset': _UT_API_RAW_MAPPED_SPEC.find(_UT_API_SPEC_SECTION_TO_BE_MAPPED),
        'coverage': 0,
        'sw-requirement': sw_requirement
    }
    response = client.put(_MAPPING_API_SW_REQUIREMENTS_URL, json=mapping_data)
    assert response.status_code == 200

    # ensure mapping is updated
    response = client.get(_MAPPING_API_SW_REQUIREMENTS_URL, query_string={'api-id': api_id})
    assert response.status_code == 200
    mapped_sections = _get_sections_mapped_by_sw_requirements(response.json['mapped'])
    # there should be only one mapped section: _UT_API_SPEC_SECTION_TO_BE_MAPPED
    assert len(mapped_sections) == 1
    assert mapped_sections[0]['section'] == _UT_API_SPEC_SECTION_TO_BE_MAPPED
    assert mapped_sections[0]['offset'] == _UT_API_RAW_MAPPED_SPEC.find(_UT_API_SPEC_SECTION_TO_BE_MAPPED)
    assert len(mapped_sections[0]['sw_requirements']) == 1  # there should be only one SW requirement


def test_delete_ok(client, user_authentication, mapped_api_db):
    """ Nominal test for mapping removal """

    api_id = mapped_api_db.id
    # ensure there is a mapped SW requirement for this API
    response = client.get(_MAPPING_API_SW_REQUIREMENTS_URL, query_string={'api-id': api_id})
    assert response.status_code == 200
    mapped_sections = _get_sections_mapped_by_sw_requirements(response.json['mapped'])
    # there should be only one mapped section: _UT_API_SPEC_SECTION_WITH_MAPPING
    assert len(mapped_sections) == 1
    assert mapped_sections[0]['section'] == _UT_API_SPEC_SECTION_WITH_MAPPING
    # get the relation ID
    relation_id = mapped_sections[0]['sw_requirements'][0]['relation_id']

    # delete mapping
    mapping_data = {
        'user-id': user_authentication.json['id'],
        'token': user_authentication.json['token'],
        'relation-id': relation_id,
        'api-id': api_id
    }
    response = client.delete(_MAPPING_API_SW_REQUIREMENTS_URL, json=mapping_data)
    assert response.status_code == 200

    # ensure the relation is deleted
    response = client.get(_MAPPING_API_SW_REQUIREMENTS_URL, query_string={'api-id': api_id})
    assert response.status_code == 200
    mapped_sections = _get_sections_mapped_by_sw_requirements(response.json['mapped'])
    assert len(mapped_sections) == 0
