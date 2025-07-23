import os
import pytest
import tempfile
from http import HTTPStatus
from db.models.user import UserModel
from db.models.api import ApiModel
from conftest import UT_USER_EMAIL


_MAPPING_API_WRITE_PERMISSION_REQUEST_URL = '/apis/write-permission-request'

_UT_API_NAME = 'ut_api'
_UT_API_LIBRARY = 'ut_api_library'
_UT_API_LIBRARY_VERSION = 'v1.0.0'
_UT_API_CATEGORY = 'ut_api_category'
_UT_API_IMPLEMENTATION_FILE_FROM_ROW = 0
_UT_API_IMPLEMENTATION_FILE_TO_ROW = 42
_UT_API_TAGS = 'ut_api_tags'

_UT_API_SPEC_SECTION_NO_MAPPING = 'This section has no mapping.'
_UT_API_RAW_UNMAPPED_SPEC = (
    f'BASIL UT: {_UT_API_SPEC_SECTION_NO_MAPPING} '
    'Used for {_MAPPING_API_WRITE_PERMISSION_REQUEST_URL}.'
)


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

    yield ut_api.id

    # remove the raw_spec tempfile
    if os.path.isfile(raw_spec.name):
        os.remove(raw_spec.name)


def test_login(user_authentication):
    """ Just ensure we are logged in """
    assert user_authentication.status_code == 200


@pytest.mark.parametrize('mandatory_field', ['api-id', 'user-id', 'token'])
def test_api_write_permission_request_put_bad_payload(client, user_authentication, unmapped_api_db, mandatory_field):
    """ Put request with bad payload, missing fields """

    api_id = unmapped_api_db

    # map a document to unmapped section
    mapping_data = {
        'user-id': user_authentication.json['id'],
        'token': user_authentication.json['token'],
        'api-id': api_id,
    }

    # Generate bad payload removing a mandatory field
    mapping_data.pop(mandatory_field)

    response = client.put(_MAPPING_API_WRITE_PERMISSION_REQUEST_URL, json=mapping_data)
    if mandatory_field in ['user-id', 'token']:
        assert response.status_code == HTTPStatus.UNAUTHORIZED
    else:
        assert response.status_code == HTTPStatus.BAD_REQUEST


def test_api_write_permission_request_put_owner_conflict(client, user_authentication, unmapped_api_db):
    """ Put request from user owner that already has write permissions """

    api_id = unmapped_api_db

    # map a document to unmapped section
    mapping_data = {
        'user-id': user_authentication.json['id'],
        'token': user_authentication.json['token'],
        'api-id': api_id,
    }

    response = client.put(_MAPPING_API_WRITE_PERMISSION_REQUEST_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.CONFLICT


def test_api_write_permission_request_put_ok(client, ut_reader_user_db, unmapped_api_db):
    """ Put request from user that is not owner """

    api_id = unmapped_api_db

    # map a document to unmapped section
    mapping_data = {
        'user-id': ut_reader_user_db.id,
        'token': ut_reader_user_db.token,
        'api-id': api_id,
    }

    response = client.put(_MAPPING_API_WRITE_PERMISSION_REQUEST_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.OK

    # Request already there
    response = client.put(_MAPPING_API_WRITE_PERMISSION_REQUEST_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.CONFLICT
