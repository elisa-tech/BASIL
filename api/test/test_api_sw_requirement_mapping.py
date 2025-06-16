import os
import pytest
import tempfile
from http import HTTPStatus
from db.models.user import UserModel
from db.models.api import ApiModel
from db.models.sw_requirement import SwRequirementModel
from db.models.api_sw_requirement import ApiSwRequirementModel
from conftest import UT_USER_EMAIL


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
def unmapped_api_db(client_db, ut_user_db, utilities):
    """ Create Api with no mapped sections """

    user = client_db.session.query(UserModel).filter(UserModel.email == UT_USER_EMAIL).one()

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
    client_db.session.add(ut_api)
    client_db.session.commit()

    yield ut_api

    # remove the raw_spec tempfile
    if os.path.isfile(raw_spec.name):
        os.remove(raw_spec.name)


@pytest.fixture()
def mapped_api_db(client_db, ut_user_db, utilities):
    """ Create Api with one mapped section """

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
    ut_sw_requirement = SwRequirementModel(f'SW req #{utilities.generate_random_hex_string8()}',
                                           'SW shall work as well as possible.', user)
    ut_api_requirement_mapping = ApiSwRequirementModel(ut_api, ut_sw_requirement, _UT_API_SPEC_SECTION_WITH_MAPPING,
                                                       _UT_API_RAW_MAPPED_SPEC.find(_UT_API_SPEC_SECTION_WITH_MAPPING),
                                                       0, user)

    client_db.session.add(ut_api)
    client_db.session.add(ut_sw_requirement)
    client_db.session.add(ut_api_requirement_mapping)
    client_db.session.commit()

    yield ut_api

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


# Test GET

def test_get_unauthorized_ok(client, unmapped_api_db):
    """ Read API without read restrictions: GET is allowed for all users """
    response = client.get(_MAPPING_API_SW_REQUIREMENTS_URL, query_string={'api-id': unmapped_api_db.id})
    assert response.status_code == HTTPStatus.OK
    assert 'mapped' in response.json
    assert 'unmapped' in response.json


def test_get_unauthorized_fail(client, restricted_api_db):
    """ Read API with read restrictions: GET is not allowed for unauthorized users """

    response = client.get(_MAPPING_API_SW_REQUIREMENTS_URL, query_string={'api-id': restricted_api_db.id})
    assert response.status_code == HTTPStatus.UNAUTHORIZED
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
    assert response.status_code == HTTPStatus.UNAUTHORIZED
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
    assert response.status_code == HTTPStatus.OK
    assert 'mapped' in response.json
    assert 'unmapped' in response.json


@pytest.mark.usefixtures("unmapped_api_db")
def test_get_incorrect_request(client, user_authentication):
    """ Read API without specification of the api-id """

    get_query = {
        'user-id': user_authentication.json['id'],
        'token': user_authentication.json['token']
    }
    response = client.get(_MAPPING_API_SW_REQUIREMENTS_URL, query_string=get_query)
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert 'mapped' not in response.json
    assert 'unmapped' not in response.json


@pytest.mark.usefixtures("unmapped_api_db")
def test_get_missing_api(client_db, client, user_authentication):
    """ Read non-existent API """

    non_existent_id = 42000
    # ensure this api id does not exist
    supposed_api = client_db.session.query(ApiModel).get(non_existent_id)
    assert supposed_api is None

    # read non-existent API
    get_query = {
        'user-id': user_authentication.json['id'],
        'token': user_authentication.json['token'],
        'api-id': non_existent_id
    }
    response = client.get(_MAPPING_API_SW_REQUIREMENTS_URL, query_string=get_query)
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert 'mapped' not in response.json
    assert 'unmapped' not in response.json


def test_get_mapped(client, mapped_api_db):
    """ Nominal test for GET """

    response = client.get(_MAPPING_API_SW_REQUIREMENTS_URL, query_string={'api-id': mapped_api_db.id})
    assert response.status_code == HTTPStatus.OK
    # there should be only one mapped section: _UT_API_SPEC_SECTION_WITH_MAPPING
    mapped_sections = _filter_sections_mapped_by_sw_requirements(response.json['mapped'])
    assert len(mapped_sections) == 1
    assert mapped_sections[0]['section'] == _UT_API_SPEC_SECTION_WITH_MAPPING


# Test POST

def test_post_unauthorized(client, unmapped_api_db, utilities):
    """ Creation of a new mapping without authentication: it is not allowed to update mapping """

    # ensure there is no mapped SW requirements for this API
    mapped_sections = _get_sections_mapped_by_sw_requirements(client, unmapped_api_db.id)
    assert len(mapped_sections) == 0

    # map a SW requirement to unmapped section
    mapping_data = {
        'api-id': unmapped_api_db.id,
        'section': _UT_API_SPEC_SECTION_NO_MAPPING,
        'offset': _UT_API_RAW_UNMAPPED_SPEC.find(_UT_API_SPEC_SECTION_NO_MAPPING),
        'coverage': 0,
        'sw-requirement': {
            'title': f'SW req #{utilities.generate_random_hex_string8()}',
            'description': 'SW requirement description'
        }
    }
    response = client.post(_MAPPING_API_SW_REQUIREMENTS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.UNAUTHORIZED

    # there should be no new mappings
    mapped_sections = _get_sections_mapped_by_sw_requirements(client, unmapped_api_db.id)
    assert len(mapped_sections) == 0


def test_post_restricted_write(client, reader_authentication, unmapped_api_db, utilities):
    """ Creation of a new mapping by "reader": the "reader" is not allowed to update mapping """

    # ensure there is no mapped SW requirements for this API
    mapped_sections = _get_sections_mapped_by_sw_requirements(client, unmapped_api_db.id)
    assert len(mapped_sections) == 0

    # map a SW requirement to unmapped section
    mapping_data = {
        'user-id': reader_authentication.json['id'],
        'token': reader_authentication.json['token'],
        'api-id': unmapped_api_db.id,
        'section': _UT_API_SPEC_SECTION_NO_MAPPING,
        'offset': _UT_API_RAW_UNMAPPED_SPEC.find(_UT_API_SPEC_SECTION_NO_MAPPING),
        'coverage': 0,
        'sw-requirement': {
            'title': f'SW req #{utilities.generate_random_hex_string8()}',
            'description': 'SW requirement description'
        }
    }
    response = client.post(_MAPPING_API_SW_REQUIREMENTS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.UNAUTHORIZED

    # there should be no new mappings
    mapped_sections = _get_sections_mapped_by_sw_requirements(client, unmapped_api_db.id)
    assert len(mapped_sections) == 0


@pytest.mark.parametrize('mandatory_field', ['api-id', 'section', 'offset', 'coverage', 'sw-requirement'])
def test_post_incomplete_request(client, user_authentication, unmapped_api_db, utilities, mandatory_field):
    """ Create mapping without specification of a mandatory parameter: it is not allowed """

    # ensure there is no mapped SW requirements for this API
    mapped_sections = _get_sections_mapped_by_sw_requirements(client, unmapped_api_db.id)
    assert len(mapped_sections) == 0

    # map a SW requirement to unmapped section, but without a mandatory field
    mapping_data = {
        'user-id': user_authentication.json['id'],
        'token': user_authentication.json['token'],
        'api-id': unmapped_api_db.id,
        'section': _UT_API_SPEC_SECTION_NO_MAPPING,
        'offset': _UT_API_RAW_UNMAPPED_SPEC.find(_UT_API_SPEC_SECTION_NO_MAPPING),
        'coverage': 0,
        'sw-requirement': {
            'title': f'SW req #{utilities.generate_random_hex_string8()}',
            'description': 'SW requirement description'
        }
    }
    mapping_data.pop(mandatory_field)
    response = client.post(_MAPPING_API_SW_REQUIREMENTS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.BAD_REQUEST

    # there should be no new mappings
    mapped_sections = _get_sections_mapped_by_sw_requirements(client, unmapped_api_db.id)
    assert len(mapped_sections) == 0


@pytest.mark.usefixtures("unmapped_api_db")
def test_post_missing_api(client_db, client, user_authentication, utilities):
    """ Create mapping for non-existent API """

    non_existent_id = 42000
    # ensure this api id does not exist
    supposed_api = client_db.session.query(ApiModel).get(non_existent_id)
    assert supposed_api is None

    # map a SW requirement to unmapped section
    mapping_data = {
        'user-id': user_authentication.json['id'],
        'token': user_authentication.json['token'],
        'api-id': non_existent_id,
        'section': _UT_API_SPEC_SECTION_NO_MAPPING,
        'offset': _UT_API_RAW_UNMAPPED_SPEC.find(_UT_API_SPEC_SECTION_NO_MAPPING),
        'coverage': 0,
        'sw-requirement': {
            'title': f'SW req #{utilities.generate_random_hex_string8()}',
            'description': 'SW requirement description'
        }
    }
    response = client.post(_MAPPING_API_SW_REQUIREMENTS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_post_missing_sw_requirement(client_db, client, user_authentication, unmapped_api_db):
    """ Create mapping for a section with non-existing SW requirement """

    non_existent_id = 42000
    # ensure this SW requirements id does not exist
    supposed_sw_requirement = client_db.session.query(SwRequirementModel).get(non_existent_id)
    assert supposed_sw_requirement is None

    # ensure there is no mapped SW requirements for this API
    mapped_sections = _get_sections_mapped_by_sw_requirements(client, unmapped_api_db.id)
    assert len(mapped_sections) == 0

    # map a non-existent SW requirement to unmapped section
    mapping_data = {
        'user-id': user_authentication.json['id'],
        'token': user_authentication.json['token'],
        'api-id': unmapped_api_db.id,
        'section': _UT_API_SPEC_SECTION_NO_MAPPING,
        'offset': _UT_API_RAW_UNMAPPED_SPEC.find(_UT_API_SPEC_SECTION_NO_MAPPING),
        'coverage': 0,
        'sw-requirement': {
            'id': non_existent_id
        }
    }
    response = client.post(_MAPPING_API_SW_REQUIREMENTS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.NOT_FOUND

    # there should be no new mappings
    mapped_sections = _get_sections_mapped_by_sw_requirements(client, unmapped_api_db.id)
    assert len(mapped_sections) == 0


def test_post_existing_sw_requirement_ok(client, user_authentication, unmapped_api_db, sw_requirement_db):
    """ Nominal test for mapping a section with an existing SW requirement """

    # ensure there is no mapped SW requirements for this API
    mapped_sections = _get_sections_mapped_by_sw_requirements(client, unmapped_api_db.id)
    assert len(mapped_sections) == 0

    # map a SW requirement to unmapped section
    mapping_data = {
        'user-id': user_authentication.json['id'],
        'token': user_authentication.json['token'],
        'api-id': unmapped_api_db.id,
        'section': _UT_API_SPEC_SECTION_NO_MAPPING,
        'offset': _UT_API_RAW_UNMAPPED_SPEC.find(_UT_API_SPEC_SECTION_NO_MAPPING),
        'coverage': 0,
        'sw-requirement': {
            'id': sw_requirement_db.id
        }
    }
    response = client.post(_MAPPING_API_SW_REQUIREMENTS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.OK

    # ensure SW requirement is added
    mapped_sections = _get_sections_mapped_by_sw_requirements(client, unmapped_api_db.id)
    assert len(mapped_sections) == 1  # there should be only one mapped section
    assert mapped_sections[0]['section'] == _UT_API_SPEC_SECTION_NO_MAPPING
    assert mapped_sections[0]['offset'] == _UT_API_RAW_UNMAPPED_SPEC.find(_UT_API_SPEC_SECTION_NO_MAPPING)
    mapped_sw_requirements = mapped_sections[0]['sw_requirements']
    assert len(mapped_sw_requirements) == 1  # there should be only one SW requirement
    assert mapped_sw_requirements[0]['sw_requirement']['title'] == sw_requirement_db.title
    assert mapped_sw_requirements[0]['created_by'] == UT_USER_EMAIL


def test_post_existing_sw_requirement_conflict(client, user_authentication, mapped_api_db):
    """ Create mapping duplication: it is not allowed """

    api_id = mapped_api_db.id
    # there should be only one mapped section: _UT_API_SPEC_SECTION_WITH_MAPPING
    mapped_sections = _get_sections_mapped_by_sw_requirements(client, api_id)
    _assert_mapped_sections(mapped_sections, [_UT_API_SPEC_SECTION_WITH_MAPPING])

    # try to create the same mapping
    _, sw_requirement = _get_mapped_sw_requirement(mapped_sections[0])
    mapping_data = {
        'user-id': user_authentication.json['id'],
        'token': user_authentication.json['token'],
        'api-id': api_id,
        'section': _UT_API_SPEC_SECTION_WITH_MAPPING,
        'offset': _UT_API_RAW_MAPPED_SPEC.find(_UT_API_SPEC_SECTION_WITH_MAPPING),
        'coverage': 0,
        'sw-requirement': {
            'id': sw_requirement['id']
        }
    }
    response = client.post(_MAPPING_API_SW_REQUIREMENTS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.CONFLICT

    # ensure mapping is not updated, there should be only one mapped section: _UT_API_SPEC_SECTION_WITH_MAPPING
    mapped_sections = _get_sections_mapped_by_sw_requirements(client, api_id)
    assert len(mapped_sections) == 1
    assert mapped_sections[0]['section'] == _UT_API_SPEC_SECTION_WITH_MAPPING
    assert mapped_sections[0]['offset'] == _UT_API_RAW_MAPPED_SPEC.find(_UT_API_SPEC_SECTION_WITH_MAPPING)
    assert len(mapped_sections[0]['sw_requirements']) == 1  # there should be only one SW requirement


def test_post_new_sw_requirement_ok(client, user_authentication, unmapped_api_db, utilities):
    """ Nominal test for mapping a section """

    api_id = unmapped_api_db.id
    sw_requirement_title = f'SW req #{utilities.generate_random_hex_string8()}'

    # ensure there is no mapped SW requirements for this API
    mapped_sections = _get_sections_mapped_by_sw_requirements(client, api_id)
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
    assert response.status_code == HTTPStatus.OK

    # ensure SW requirement is added
    mapped_sections = _get_sections_mapped_by_sw_requirements(client, api_id)
    assert len(mapped_sections) == 1  # there should be only one mapped section
    assert mapped_sections[0]['section'] == _UT_API_SPEC_SECTION_NO_MAPPING
    assert mapped_sections[0]['offset'] == _UT_API_RAW_UNMAPPED_SPEC.find(_UT_API_SPEC_SECTION_NO_MAPPING)
    mapped_sw_requirements = mapped_sections[0]['sw_requirements']
    assert len(mapped_sw_requirements) == 1  # there should be only one SW requirement
    assert mapped_sw_requirements[0]['sw_requirement']['title'] == sw_requirement_title
    assert mapped_sw_requirements[0]['created_by'] == UT_USER_EMAIL


def test_post_new_sw_requirement_conflict(client, user_authentication, mapped_api_db):
    """ Create SW requirement duplication: it is not allowed """

    api_id = mapped_api_db.id
    # there should be only one mapped section: _UT_API_SPEC_SECTION_WITH_MAPPING
    mapped_sections = _get_sections_mapped_by_sw_requirements(client, api_id)
    _assert_mapped_sections(mapped_sections, [_UT_API_SPEC_SECTION_WITH_MAPPING])

    # map a SW requirement to unmapped section, but with a SW requirement duplicate
    _, sw_requirement = _get_mapped_sw_requirement(mapped_sections[0])
    mapping_data = {
        'user-id': user_authentication.json['id'],
        'token': user_authentication.json['token'],
        'api-id': api_id,
        'section': _UT_API_SPEC_SECTION_TO_BE_MAPPED,
        'offset': _UT_API_RAW_MAPPED_SPEC.find(_UT_API_SPEC_SECTION_TO_BE_MAPPED),
        'coverage': 0,
        'sw-requirement': {
            'title': sw_requirement['title'],
            'description': sw_requirement['description']
        }
    }
    response = client.post(_MAPPING_API_SW_REQUIREMENTS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.CONFLICT

    # ensure no SW requirement is added
    mapped_sections = _get_sections_mapped_by_sw_requirements(client, api_id)
    assert len(mapped_sections) == 1  # there should be only one mapped section
    assert mapped_sections[0]['section'] == _UT_API_SPEC_SECTION_WITH_MAPPING
    assert mapped_sections[0]['offset'] == _UT_API_RAW_MAPPED_SPEC.find(_UT_API_SPEC_SECTION_WITH_MAPPING)
    mapped_sw_requirements = mapped_sections[0]['sw_requirements']
    assert len(mapped_sw_requirements) == 1  # there should be only one SW requirement
    assert mapped_sw_requirements[0]['sw_requirement']['title'] == sw_requirement['title']
    assert mapped_sw_requirements[0]['created_by'] == UT_USER_EMAIL


@pytest.mark.parametrize('mandatory_field', ['title', 'description', '*'])
def test_post_new_sw_requirement_incomplete(client, user_authentication, unmapped_api_db, utilities, mandatory_field):
    """ Create mapping without specification of a mandatory SW requirement field: it is not allowed """

    # ensure there is no mapped SW requirements for this API
    mapped_sections = _get_sections_mapped_by_sw_requirements(client, unmapped_api_db.id)
    assert len(mapped_sections) == 0

    # map a SW requirement to unmapped section, but without a mandatory field
    mapping_data = {
        'user-id': user_authentication.json['id'],
        'token': user_authentication.json['token'],
        'api-id': unmapped_api_db.id,
        'section': _UT_API_SPEC_SECTION_NO_MAPPING,
        'offset': _UT_API_RAW_UNMAPPED_SPEC.find(_UT_API_SPEC_SECTION_NO_MAPPING),
        'coverage': 0,
        'sw-requirement': {
            'title': f'SW req #{utilities.generate_random_hex_string8()}',
            'description': 'SW requirement description'
        }
    }
    if mandatory_field == '*':
        mapping_data['sw-requirement'] = {}
    else:
        mapping_data['sw-requirement'].pop(mandatory_field)
    response = client.post(_MAPPING_API_SW_REQUIREMENTS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.BAD_REQUEST

    # there should be no new mappings
    mapped_sections = _get_sections_mapped_by_sw_requirements(client, unmapped_api_db.id)
    assert len(mapped_sections) == 0


def test_post_add_sw_requirement(client, user_authentication, mapped_api_db, utilities):
    """ Map one section with two different requirements """

    api_id = mapped_api_db.id

    # there should be only one mapped section: _UT_API_SPEC_SECTION_WITH_MAPPING
    mapped_sections = _get_sections_mapped_by_sw_requirements(client, api_id)
    _assert_mapped_sections(mapped_sections, [_UT_API_SPEC_SECTION_WITH_MAPPING])
    mapped_sw_requirements = mapped_sections[0]['sw_requirements']
    assert len(mapped_sw_requirements) == 1  # there should be only one SW requirement

    # map a new SW requirement to mapped section
    mapping_data = {
        'user-id': user_authentication.json['id'],
        'token': user_authentication.json['token'],
        'api-id': api_id,
        'section': _UT_API_SPEC_SECTION_WITH_MAPPING,
        'offset': _UT_API_RAW_MAPPED_SPEC.find(_UT_API_SPEC_SECTION_WITH_MAPPING),
        'coverage': 50,
        'sw-requirement': {
            'title': f'SW req #{utilities.generate_random_hex_string8()}',
            'description': 'A new SW requirement for this section'
        }
    }
    response = client.post(_MAPPING_API_SW_REQUIREMENTS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.OK

    # ensure a SW requirement is added for a mapped section
    mapped_sections = _get_sections_mapped_by_sw_requirements(client, api_id)
    assert len(mapped_sections) == 1
    assert mapped_sections[0]['section'] == _UT_API_SPEC_SECTION_WITH_MAPPING
    assert mapped_sections[0]['offset'] == _UT_API_RAW_MAPPED_SPEC.find(_UT_API_SPEC_SECTION_WITH_MAPPING)
    # there should be two different SW requirements
    mapped_sw_requirements = mapped_sections[0]['sw_requirements']
    assert len(mapped_sw_requirements) == 2
    assert mapped_sw_requirements[0]['sw_requirement']['title'] != mapped_sw_requirements[1]['sw_requirement']['title']


def test_put_unauthorized(client, mapped_api_db):
    """ Update mapping without authentication: it is not allowed """

    # there should be only one mapped section: _UT_API_SPEC_SECTION_WITH_MAPPING
    mapped_sections = _get_sections_mapped_by_sw_requirements(client, mapped_api_db.id)
    _assert_mapped_sections(mapped_sections, [_UT_API_SPEC_SECTION_WITH_MAPPING])

    # update mapping from _UT_API_SPEC_SECTION_WITH_MAPPING to _UT_API_SPEC_SECTION_TO_BE_MAPPED
    relation_id, sw_requirement = _get_mapped_sw_requirement(mapped_sections[0])
    mapping_data = {
        'relation-id': relation_id,
        'api-id': mapped_api_db.id,
        'section': _UT_API_SPEC_SECTION_TO_BE_MAPPED,
        'offset': _UT_API_RAW_MAPPED_SPEC.find(_UT_API_SPEC_SECTION_TO_BE_MAPPED),
        'coverage': 0,
        'sw-requirement': sw_requirement
    }
    response = client.put(_MAPPING_API_SW_REQUIREMENTS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.UNAUTHORIZED

    # there should be no new mappings
    mapped_sections = _get_sections_mapped_by_sw_requirements(client, mapped_api_db.id)
    _assert_mapped_sections(mapped_sections, [_UT_API_SPEC_SECTION_WITH_MAPPING])


def test_put_restricted_write(client, reader_authentication, mapped_api_db):
    """ Update mapping by "reader": the "reader" is not allowed to update mapping """

    # there should be only one mapped section: _UT_API_SPEC_SECTION_WITH_MAPPING
    mapped_sections = _get_sections_mapped_by_sw_requirements(client, mapped_api_db.id)
    _assert_mapped_sections(mapped_sections, [_UT_API_SPEC_SECTION_WITH_MAPPING])

    # update mapping from _UT_API_SPEC_SECTION_WITH_MAPPING to _UT_API_SPEC_SECTION_TO_BE_MAPPED
    relation_id, sw_requirement = _get_mapped_sw_requirement(mapped_sections[0])
    mapping_data = {
        'user-id': reader_authentication.json['id'],
        'token': reader_authentication.json['token'],
        'relation-id': relation_id,
        'api-id': mapped_api_db.id,
        'section': _UT_API_SPEC_SECTION_TO_BE_MAPPED,
        'offset': _UT_API_RAW_MAPPED_SPEC.find(_UT_API_SPEC_SECTION_TO_BE_MAPPED),
        'coverage': 0,
        'sw-requirement': sw_requirement
    }
    response = client.put(_MAPPING_API_SW_REQUIREMENTS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.UNAUTHORIZED

    # there should be no new mappings
    mapped_sections = _get_sections_mapped_by_sw_requirements(client, mapped_api_db.id)
    _assert_mapped_sections(mapped_sections, [_UT_API_SPEC_SECTION_WITH_MAPPING])


@pytest.mark.parametrize('mandatory_field', ['api-id', 'section', 'offset', 'coverage', 'sw-requirement'])
def test_put_incomplete_request(client, user_authentication, mapped_api_db, mandatory_field):
    """ Update mapping without specification of a mandatory parameter: it is not allowed """

    # there should be only one mapped section: _UT_API_SPEC_SECTION_WITH_MAPPING
    mapped_sections = _get_sections_mapped_by_sw_requirements(client, mapped_api_db.id)
    _assert_mapped_sections(mapped_sections, [_UT_API_SPEC_SECTION_WITH_MAPPING])

    # update mapping from _UT_API_SPEC_SECTION_WITH_MAPPING to _UT_API_SPEC_SECTION_TO_BE_MAPPED
    relation_id, sw_requirement = _get_mapped_sw_requirement(mapped_sections[0])
    mapping_data = {
        'user-id': user_authentication.json['id'],
        'token': user_authentication.json['token'],
        'relation-id': relation_id,
        'api-id': mapped_api_db.id,
        'section': _UT_API_SPEC_SECTION_TO_BE_MAPPED,
        'offset': _UT_API_RAW_MAPPED_SPEC.find(_UT_API_SPEC_SECTION_TO_BE_MAPPED),
        'coverage': 0,
        'sw-requirement': sw_requirement
    }
    mapping_data.pop(mandatory_field)
    response = client.put(_MAPPING_API_SW_REQUIREMENTS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.BAD_REQUEST

    # there should be no new mappings
    mapped_sections = _get_sections_mapped_by_sw_requirements(client, mapped_api_db.id)
    _assert_mapped_sections(mapped_sections, [_UT_API_SPEC_SECTION_WITH_MAPPING])


def test_put_missing_api(client_db, client, user_authentication, mapped_api_db):
    """ Update mapping for non-existent API """

    non_existent_id = 42000
    # ensure this api id does not exist
    supposed_api = client_db.session.query(ApiModel).get(non_existent_id)
    assert supposed_api is None

    # update mapping from _UT_API_SPEC_SECTION_WITH_MAPPING to _UT_API_SPEC_SECTION_TO_BE_MAPPED
    mapped_sections = _get_sections_mapped_by_sw_requirements(client, mapped_api_db.id)
    relation_id, sw_requirement = _get_mapped_sw_requirement(mapped_sections[0])
    mapping_data = {
        'user-id': user_authentication.json['id'],
        'token': user_authentication.json['token'],
        'relation-id': relation_id,
        'api-id': non_existent_id,
        'section': _UT_API_SPEC_SECTION_TO_BE_MAPPED,
        'offset': _UT_API_RAW_MAPPED_SPEC.find(_UT_API_SPEC_SECTION_TO_BE_MAPPED),
        'coverage': 0,
        'sw-requirement': sw_requirement
    }
    response = client.put(_MAPPING_API_SW_REQUIREMENTS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_put_missing_relation(client_db, client, user_authentication, mapped_api_db):
    """ Update mapping for non-existent relation """

    non_existent_id = 42000
    # ensure this relation id does not exist
    supposed_mapping = client_db.session.query(ApiSwRequirementModel).get(non_existent_id)
    assert supposed_mapping is None

    # update mapping from _UT_API_SPEC_SECTION_WITH_MAPPING to _UT_API_SPEC_SECTION_TO_BE_MAPPED
    mapped_sections = _get_sections_mapped_by_sw_requirements(client, mapped_api_db.id)
    _, sw_requirement = _get_mapped_sw_requirement(mapped_sections[0])
    mapping_data = {
        'user-id': user_authentication.json['id'],
        'token': user_authentication.json['token'],
        'relation-id': non_existent_id,
        'api-id': mapped_api_db.id,
        'section': _UT_API_SPEC_SECTION_TO_BE_MAPPED,
        'offset': _UT_API_RAW_MAPPED_SPEC.find(_UT_API_SPEC_SECTION_TO_BE_MAPPED),
        'coverage': 0,
        'sw-requirement': sw_requirement
    }
    response = client.put(_MAPPING_API_SW_REQUIREMENTS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.NOT_FOUND

    # there should be no new mappings
    mapped_sections = _get_sections_mapped_by_sw_requirements(client, mapped_api_db.id)
    _assert_mapped_sections(mapped_sections, [_UT_API_SPEC_SECTION_WITH_MAPPING])


def test_put_update_mapping_ok(client, user_authentication, mapped_api_db):
    """ Nominal test for mapping update: section and offset """

    api_id = mapped_api_db.id
    # there should be only one mapped section: _UT_API_SPEC_SECTION_WITH_MAPPING
    mapped_sections = _get_sections_mapped_by_sw_requirements(client, api_id)
    _assert_mapped_sections(mapped_sections, [_UT_API_SPEC_SECTION_WITH_MAPPING])

    # update mapping from _UT_API_SPEC_SECTION_WITH_MAPPING to _UT_API_SPEC_SECTION_TO_BE_MAPPED
    relation_id, sw_requirement = _get_mapped_sw_requirement(mapped_sections[0])
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
    assert response.status_code == HTTPStatus.OK

    # ensure mapping is updated to _UT_API_SPEC_SECTION_TO_BE_MAPPED
    mapped_sections = _get_sections_mapped_by_sw_requirements(client, api_id)
    assert len(mapped_sections) == 1
    assert mapped_sections[0]['section'] == _UT_API_SPEC_SECTION_TO_BE_MAPPED
    assert mapped_sections[0]['offset'] == _UT_API_RAW_MAPPED_SPEC.find(_UT_API_SPEC_SECTION_TO_BE_MAPPED)
    assert mapped_sections[0]['covered'] == 0
    assert len(mapped_sections[0]['sw_requirements']) == 1  # there should be only one SW requirement
    assert mapped_sections[0]['sw_requirements'][0]['version'] == '1.2'

    # ensure covered is updated and version increment accordingly
    mapping_data = {
        'user-id': user_authentication.json['id'],
        'token': user_authentication.json['token'],
        'relation-id': relation_id,
        'api-id': api_id,
        'section': _UT_API_SPEC_SECTION_TO_BE_MAPPED,
        'offset': _UT_API_RAW_MAPPED_SPEC.find(_UT_API_SPEC_SECTION_TO_BE_MAPPED),
        'coverage': 50,
        'sw-requirement': sw_requirement
    }
    response = client.put(_MAPPING_API_SW_REQUIREMENTS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.OK
    mapped_sections = _get_sections_mapped_by_sw_requirements(client, api_id)
    assert mapped_sections[0]['covered'] == 50
    assert len(mapped_sections[0]['sw_requirements']) == 1  # there should be only one SW requirement
    assert mapped_sections[0]['sw_requirements'][0]['version'] == '1.3'


def test_put_update_mapping_unchanged(client, user_authentication, mapped_api_db):
    """ Update mapping with the same data """

    api_id = mapped_api_db.id
    # there should be only one mapped section: _UT_API_SPEC_SECTION_WITH_MAPPING
    mapped_sections = _get_sections_mapped_by_sw_requirements(client, api_id)
    _assert_mapped_sections(mapped_sections, [_UT_API_SPEC_SECTION_WITH_MAPPING])

    # update with the same data
    relation_id, sw_requirement = _get_mapped_sw_requirement(mapped_sections[0])
    mapping_data = {
        'user-id': user_authentication.json['id'],
        'token': user_authentication.json['token'],
        'relation-id': relation_id,
        'api-id': api_id,
        'section': _UT_API_SPEC_SECTION_WITH_MAPPING,
        'offset': _UT_API_RAW_MAPPED_SPEC.find(_UT_API_SPEC_SECTION_WITH_MAPPING),
        'coverage': 0,
        'sw-requirement': sw_requirement
    }
    response = client.put(_MAPPING_API_SW_REQUIREMENTS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.OK

    # ensure mapping is still to _UT_API_SPEC_SECTION_WITH_MAPPING
    mapped_sections = _get_sections_mapped_by_sw_requirements(client, api_id)
    _assert_mapped_sections(mapped_sections, [_UT_API_SPEC_SECTION_WITH_MAPPING])
    assert mapped_sections[0]['sw_requirements'][0]['version'] == '1.1'


def test_put_update_sw_requirement(client, user_authentication, mapped_api_db, utilities):
    """ Nominal test for mapping update: SW requirement data """

    api_id = mapped_api_db.id
    # there should be only one mapped section: _UT_API_SPEC_SECTION_WITH_MAPPING
    mapped_sections = _get_sections_mapped_by_sw_requirements(client, api_id)
    _assert_mapped_sections(mapped_sections, [_UT_API_SPEC_SECTION_WITH_MAPPING])

    # update sw requirement
    relation_id, sw_requirement = _get_mapped_sw_requirement(mapped_sections[0])
    new_sw_requirement_title = f'SW req #{utilities.generate_random_hex_string8()}'
    sw_requirement['title'] = new_sw_requirement_title
    mapping_data = {
        'user-id': user_authentication.json['id'],
        'token': user_authentication.json['token'],
        'relation-id': relation_id,
        'api-id': api_id,
        'section': _UT_API_SPEC_SECTION_WITH_MAPPING,
        'offset': _UT_API_RAW_MAPPED_SPEC.find(_UT_API_SPEC_SECTION_WITH_MAPPING),
        'coverage': 0,
        'sw-requirement': sw_requirement
    }
    response = client.put(_MAPPING_API_SW_REQUIREMENTS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.OK

    # ensure mapping is still to _UT_API_SPEC_SECTION_WITH_MAPPING
    mapped_sections = _get_sections_mapped_by_sw_requirements(client, api_id)
    _assert_mapped_sections(mapped_sections, [_UT_API_SPEC_SECTION_WITH_MAPPING])
    # there should be only one SW requirement with the new title
    assert len(mapped_sections[0]['sw_requirements']) == 1
    sw_requirement = mapped_sections[0]['sw_requirements'][0]['sw_requirement']
    assert sw_requirement['title'] == new_sw_requirement_title
    assert mapped_sections[0]['sw_requirements'][0]['version'] == '2.1'


def test_delete_unauthorized(client, mapped_api_db):
    """ Delete mapping without authentication: it is not allowed """

    # there should be only one mapped section: _UT_API_SPEC_SECTION_WITH_MAPPING
    mapped_sections = _get_sections_mapped_by_sw_requirements(client, mapped_api_db.id)
    _assert_mapped_sections(mapped_sections, [_UT_API_SPEC_SECTION_WITH_MAPPING])

    # delete mapping
    relation_id, _ = _get_mapped_sw_requirement(mapped_sections[0])
    mapping_data = {
        'relation-id': relation_id,
        'api-id': mapped_api_db.id
    }
    response = client.delete(_MAPPING_API_SW_REQUIREMENTS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.UNAUTHORIZED

    # the mapping should exist
    mapped_sections = _get_sections_mapped_by_sw_requirements(client, mapped_api_db.id)
    _assert_mapped_sections(mapped_sections, [_UT_API_SPEC_SECTION_WITH_MAPPING])


def test_delete_wrong_mapping(client_db, client, user_authentication, mapped_api_db, restricted_api_db, utilities):
    """ Delete mapping that is not matching api-id: it is not allowed
    we can have 2 cases:
    - The api doesn't exists NOT FOUND
    - User is not authorized for the api, the api will return UNAUTHORIZED
    - User is authorized for the api, the api will return BAD REQUEST
    """

    # Case 1 - The api doesn't exists
    # there should be only one mapped section: _UT_API_SPEC_SECTION_WITH_MAPPING
    mapped_sections = _get_sections_mapped_by_sw_requirements(client, mapped_api_db.id)
    _assert_mapped_sections(mapped_sections, [_UT_API_SPEC_SECTION_WITH_MAPPING])

    # delete mapping
    relation_id, _ = _get_mapped_sw_requirement(mapped_sections[0])
    mapping_data = {
        'relation-id': relation_id,
        'api-id': 0
    }
    response = client.delete(_MAPPING_API_SW_REQUIREMENTS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.NOT_FOUND

    # the mapping should exist
    mapped_sections = _get_sections_mapped_by_sw_requirements(client, mapped_api_db.id)
    _assert_mapped_sections(mapped_sections, [_UT_API_SPEC_SECTION_WITH_MAPPING])

    # Case 2 - User is not authorized for the api
    # there should be only one mapped section: _UT_API_SPEC_SECTION_WITH_MAPPING
    mapped_sections = _get_sections_mapped_by_sw_requirements(client, mapped_api_db.id)
    _assert_mapped_sections(mapped_sections, [_UT_API_SPEC_SECTION_WITH_MAPPING])

    # delete mapping
    relation_id, _ = _get_mapped_sw_requirement(mapped_sections[0])
    mapping_data = {
        'relation-id': relation_id,
        'api-id': restricted_api_db.id,
    }
    response = client.delete(_MAPPING_API_SW_REQUIREMENTS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.UNAUTHORIZED

    # the mapping should exist
    mapped_sections = _get_sections_mapped_by_sw_requirements(client, mapped_api_db.id)
    _assert_mapped_sections(mapped_sections, [_UT_API_SPEC_SECTION_WITH_MAPPING])

    # Case 2 - User is authorized for the api but it is not the one related to the mapping
    # there should be only one mapped section: _UT_API_SPEC_SECTION_WITH_MAPPING
    mapped_sections = _get_sections_mapped_by_sw_requirements(client, mapped_api_db.id)
    _assert_mapped_sections(mapped_sections, [_UT_API_SPEC_SECTION_WITH_MAPPING])

    # delete mapping
    relation_id, _ = _get_mapped_sw_requirement(mapped_sections[0])
    api = _create_software_component(client_db, utilities)
    mapping_data = {
        'user-id': user_authentication.json['id'],
        'token': user_authentication.json['token'],
        'relation-id': relation_id,
        'api-id': api.id
    }
    response = client.delete(_MAPPING_API_SW_REQUIREMENTS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.BAD_REQUEST

    # the mapping should exist
    mapped_sections = _get_sections_mapped_by_sw_requirements(client, mapped_api_db.id)
    _assert_mapped_sections(mapped_sections, [_UT_API_SPEC_SECTION_WITH_MAPPING])


def test_delete_restricted_write(client, reader_authentication, mapped_api_db):
    """ Delete mapping by "reader": the "reader" is not allowed to delete mapping """

    # there should be only one mapped section: _UT_API_SPEC_SECTION_WITH_MAPPING
    mapped_sections = _get_sections_mapped_by_sw_requirements(client, mapped_api_db.id)
    _assert_mapped_sections(mapped_sections, [_UT_API_SPEC_SECTION_WITH_MAPPING])

    # delete mapping
    relation_id, _ = _get_mapped_sw_requirement(mapped_sections[0])
    mapping_data = {
        'user-id': reader_authentication.json['id'],
        'token': reader_authentication.json['token'],
        'relation-id': relation_id,
        'api-id': mapped_api_db.id
    }
    response = client.delete(_MAPPING_API_SW_REQUIREMENTS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.UNAUTHORIZED

    # the mapping should exist
    mapped_sections = _get_sections_mapped_by_sw_requirements(client, mapped_api_db.id)
    _assert_mapped_sections(mapped_sections, [_UT_API_SPEC_SECTION_WITH_MAPPING])


@pytest.mark.parametrize('mandatory_field', ['api-id', 'relation-id'])
def test_delete_incomplete_request(client, user_authentication, mapped_api_db, mandatory_field):
    """ Delete mapping without specification of a mandatory parameter: it is not allowed """

    # there should be only one mapped section: _UT_API_SPEC_SECTION_WITH_MAPPING
    mapped_sections = _get_sections_mapped_by_sw_requirements(client, mapped_api_db.id)
    _assert_mapped_sections(mapped_sections, [_UT_API_SPEC_SECTION_WITH_MAPPING])

    # delete mapping
    relation_id, _ = _get_mapped_sw_requirement(mapped_sections[0])
    mapping_data = {
        'user-id': user_authentication.json['id'],
        'token': user_authentication.json['token'],
        'relation-id': relation_id,
        'api-id': mapped_api_db.id
    }
    mapping_data.pop(mandatory_field)
    response = client.delete(_MAPPING_API_SW_REQUIREMENTS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.BAD_REQUEST

    # the mapping should exist
    mapped_sections = _get_sections_mapped_by_sw_requirements(client, mapped_api_db.id)
    _assert_mapped_sections(mapped_sections, [_UT_API_SPEC_SECTION_WITH_MAPPING])


def test_delete_missing_api(client_db, client, user_authentication, mapped_api_db):
    """ Delete mapping for non-existent API """

    non_existent_id = 42000
    # ensure this api id does not exist
    supposed_api = client_db.session.query(ApiModel).get(non_existent_id)
    assert supposed_api is None

    # delete mapping
    mapped_sections = _get_sections_mapped_by_sw_requirements(client, mapped_api_db.id)
    relation_id, _ = _get_mapped_sw_requirement(mapped_sections[0])
    mapping_data = {
        'user-id': user_authentication.json['id'],
        'token': user_authentication.json['token'],
        'relation-id': relation_id,
        'api-id': non_existent_id
    }
    response = client.delete(_MAPPING_API_SW_REQUIREMENTS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_delete_missing_relation(client_db, client, user_authentication, mapped_api_db):
    """ Delete mapping for non-existent relation """

    non_existent_id = 42000
    # ensure this relation id does not exist
    supposed_mapping = client_db.session.query(ApiSwRequirementModel).get(non_existent_id)
    assert supposed_mapping is None

    # delete mapping
    mapping_data = {
        'user-id': user_authentication.json['id'],
        'token': user_authentication.json['token'],
        'relation-id': non_existent_id,
        'api-id': mapped_api_db.id
    }
    response = client.delete(_MAPPING_API_SW_REQUIREMENTS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.NOT_FOUND

    # the mapping should exist
    mapped_sections = _get_sections_mapped_by_sw_requirements(client, mapped_api_db.id)
    _assert_mapped_sections(mapped_sections, [_UT_API_SPEC_SECTION_WITH_MAPPING])


def test_delete_ok(client, user_authentication, mapped_api_db):
    """ Nominal test for mapping removal """

    api_id = mapped_api_db.id
    # ensure there is a mapped SW requirement for this API for section _UT_API_SPEC_SECTION_WITH_MAPPING
    mapped_sections = _get_sections_mapped_by_sw_requirements(client, api_id)
    _assert_mapped_sections(mapped_sections, [_UT_API_SPEC_SECTION_WITH_MAPPING])

    # delete mapping
    relation_id, _ = _get_mapped_sw_requirement(mapped_sections[0])
    mapping_data = {
        'user-id': user_authentication.json['id'],
        'token': user_authentication.json['token'],
        'relation-id': relation_id,
        'api-id': api_id
    }
    response = client.delete(_MAPPING_API_SW_REQUIREMENTS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.OK

    # ensure the relation is deleted
    mapped_sections = _get_sections_mapped_by_sw_requirements(client, api_id)
    assert len(mapped_sections) == 0
