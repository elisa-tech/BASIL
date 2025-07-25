import os
from db.models.api_sw_requirement import ApiSwRequirementModel
from db.models.sw_requirement import SwRequirementModel
import pytest
import tempfile
from http import HTTPStatus
from db.models.user import UserModel
from db.models.api import ApiModel
from conftest import UT_USER_EMAIL


_MAPPING_COMMENT_URL = '/comments'

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
                              f' Used for {_MAPPING_COMMENT_URL}.'
_UT_API_RAW_UNMAPPED_SPEC = f'BASIL UT: {_UT_API_SPEC_SECTION_NO_MAPPING} Used for {_MAPPING_COMMENT_URL}.'
_UT_API_RAW_MAPPED_SPEC = f'BASIL UT: {_UT_API_SPEC_SECTION_WITH_MAPPING} {_UT_API_SPEC_SECTION_TO_BE_MAPPED} ' \
                          f'Used for {_MAPPING_COMMENT_URL}.'


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
def api_sr_db(client_db, ut_user_db, utilities):
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

    yield ut_api_requirement_mapping

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
    """ Just ensure we are logged in """
    assert user_authentication.status_code == 200


@pytest.mark.parametrize('mandatory_field', ['api-id', 'comment', 'parent_table', 'parent_id', 'user-id', 'token'])
def test_comment_post_bad_payload(client, user_authentication, api_sr_db, mandatory_field):
    """ Post request with bad payload, missing fields """

    api_sr = api_sr_db

    # map a document to unmapped section
    mapping_data = {
        'api-id': api_sr.api_id,
        'user-id': user_authentication.json['id'],
        'token': user_authentication.json['token'],
        'comment': 'My first comment',
        'parent_table': ApiSwRequirementModel.__tablename__,
        'parent_id': api_sr.id
    }

    # Generate bad payload removing a mandatory field
    mapping_data.pop(mandatory_field)

    response = client.post(_MAPPING_COMMENT_URL, json=mapping_data)
    if mandatory_field in ['user-id', 'token']:
        assert response.status_code == HTTPStatus.UNAUTHORIZED
    else:
        assert response.status_code == HTTPStatus.BAD_REQUEST


def test_comment_post_put_delete(client, user_authentication, api_sr_db):
    """ Post and Put ok request """

    api_sr = api_sr_db

    mapping_data = {
        'api-id': api_sr.api_id,
        'user-id': user_authentication.json['id'],
        'token': user_authentication.json['token'],
        'comment': 'My first comment',
        'parent_table': ApiSwRequirementModel.__tablename__,
        'parent_id': api_sr.id
    }

    response = client.post(_MAPPING_COMMENT_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.OK

    comment_id = response.json.get("id")

    """ Put request """

    mapping_data = {
        'api-id': api_sr.api_id,
        'user-id': user_authentication.json['id'],
        'token': user_authentication.json['token'],
        'comment_id': comment_id,
        'comment': 'My first comment modified',
        'parent_table': ApiSwRequirementModel.__tablename__,
        'parent_id': api_sr.id
    }

    response = client.put(_MAPPING_COMMENT_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.OK

    """ Delete request """

    mapping_data = {
        'api-id': api_sr.api_id,
        'user-id': user_authentication.json['id'],
        'token': user_authentication.json['token'],
        'comment_id': comment_id,
        'parent_table': ApiSwRequirementModel.__tablename__,
        'parent_id': api_sr.id
    }

    response = client.delete(_MAPPING_COMMENT_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.OK


@pytest.mark.parametrize('mandatory_field',
                         ['api-id', 'comment_id', 'comment', 'parent_table', 'parent_id', 'user-id', 'token'])
def test_comment_put_bad_payload(client, user_authentication, api_sr_db, mandatory_field):
    """ Put request with bad payload, missing fields """

    api_sr = api_sr_db

    # map a document to unmapped section
    mapping_data = {
        'api-id': api_sr.api_id,
        'user-id': user_authentication.json['id'],
        'token': user_authentication.json['token'],
        'comment_id': 1,
        'comment': 'My first comment modified',
        'parent_table': ApiSwRequirementModel.__tablename__,
        'parent_id': api_sr.id
    }

    # Generate bad payload removing a mandatory field
    mapping_data.pop(mandatory_field)

    response = client.put(_MAPPING_COMMENT_URL, json=mapping_data)
    if mandatory_field in ['user-id', 'token']:
        assert response.status_code == HTTPStatus.UNAUTHORIZED
    else:
        assert response.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.parametrize('mandatory_field', ['api-id', 'comment_id', 'parent_table', 'parent_id', 'user-id', 'token'])
def test_comment_delete_bad_payload(client, user_authentication, api_sr_db, mandatory_field):
    """ Delete request with bad payload, missing fields """

    api_sr = api_sr_db

    # map a document to unmapped section
    mapping_data = {
        'api-id': api_sr.api_id,
        'user-id': user_authentication.json['id'],
        'token': user_authentication.json['token'],
        'comment_id': 1,
        'parent_table': ApiSwRequirementModel.__tablename__,
        'parent_id': api_sr.id
    }

    # Generate bad payload removing a mandatory field
    mapping_data.pop(mandatory_field)

    response = client.put(_MAPPING_COMMENT_URL, json=mapping_data)
    if mandatory_field in ['user-id', 'token']:
        assert response.status_code == HTTPStatus.UNAUTHORIZED
    else:
        assert response.status_code == HTTPStatus.BAD_REQUEST
