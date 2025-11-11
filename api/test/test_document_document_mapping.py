import os
import pytest
import tempfile
from http import HTTPStatus
from db.models.user import UserModel
from db.models.api import ApiModel
from db.models.document import DocumentModel
from db.models.api_document import ApiDocumentModel
from db.models.document_document import DocumentDocumentModel
from conftest import UT_USER_EMAIL, UT_USER_NAME

_MAPPING_API_DOCUMENTS_URL = '/mapping/api/documents'
_MAPPING_DOCUMENT_DOCUMENTS_URL = '/mapping/document/documents'

_UT_API_NAME = 'ut_api'
_UT_API_LIBRARY = 'ut_api_library'
_UT_API_LIBRARY_VERSION = 'v1.0.0'
_UT_API_CATEGORY = 'ut_api_category'
_UT_API_IMPLEMENTATION_FILE_FROM_ROW = 0
_UT_API_IMPLEMENTATION_FILE_TO_ROW = 42
_UT_API_TAGS = 'ut_api_tags'

_UT_API_SPEC_SECTION_WITH_MAPPING = 'This section has mapping.'
_UT_API_SPEC_SECTION_TO_BE_MAPPED = 'This section is to be mapped.'
_UT_API_RAW_RESTRICTED_SPEC = 'BASIL UT: "Reader" user is not able to read this API.' \
                              f' Used for {_MAPPING_API_DOCUMENTS_URL}.'
_UT_API_RAW_MAPPED_SPEC = f'BASIL UT: {_UT_API_SPEC_SECTION_WITH_MAPPING} {_UT_API_SPEC_SECTION_TO_BE_MAPPED} ' \
                          f'Used for {_MAPPING_API_DOCUMENTS_URL}.'
UNMATCHING_ID = 99999


def get_document_model(client_db, utilities, *, url='stub.md', section=_UT_API_SPEC_SECTION_WITH_MAPPING,
                       offset=0):
    user = client_db.session.query(UserModel).filter(UserModel.email == UT_USER_EMAIL).one()
    return DocumentModel(
        title=f'Doc #{utilities.generate_random_hex_string8()}',
        description='This document shall be clear and accurate.',
        document_type='file',
        spdx_relation='relates-to',
        url=url,
        section=section,
        offset=offset,
        valid=0,
        created_by=user,
    )


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
def mapped_api_doc_doc_db(client_db, ut_user_db, utilities):
    """ Create a Document mapped to another Document that is
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
    ut_document = get_document_model(
        client_db, utilities, url=raw_spec.name,
        section=_UT_API_SPEC_SECTION_WITH_MAPPING,
        offset=_UT_API_RAW_MAPPED_SPEC.find(_UT_API_SPEC_SECTION_WITH_MAPPING)
    )
    ut_api_document_mapping = ApiDocumentModel(
        api=ut_api,
        document=ut_document,
        section=_UT_API_SPEC_SECTION_WITH_MAPPING,
        offset=_UT_API_RAW_MAPPED_SPEC.find(_UT_API_SPEC_SECTION_WITH_MAPPING),
        coverage=0,
        created_by=user,
    )
    ut_nested_document = get_document_model(client_db, utilities)
    ut_document_document_mapping = DocumentDocumentModel(
        document_mapping_api=ut_api_document_mapping,
        document_mapping_document=None,
        document=ut_nested_document,
        section="Nested section",
        offset=0,
        coverage=50,
        created_by=user,
    )
    client_db.session.add(ut_api)
    client_db.session.add(ut_document)
    client_db.session.add(ut_api_document_mapping)
    client_db.session.add(ut_nested_document)
    client_db.session.add(ut_document_document_mapping)
    client_db.session.commit()

    yield (
        ut_api,
        ut_api_document_mapping,
        ut_document_document_mapping,
    )

    # remove the raw_spec tempfile
    if os.path.isfile(raw_spec.name):
        os.remove(raw_spec.name)


@pytest.fixture()
def mapped_api_doc_doc_doc_db(client_db, ut_user_db, utilities):
    """ Create a Document mapped to another Document that is
    mapped to another Document """

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
    ut_document = get_document_model(client_db, utilities)
    ut_api_document_mapping = ApiDocumentModel(
        api=ut_api,
        document=ut_document,
        section=_UT_API_SPEC_SECTION_WITH_MAPPING,
        offset=_UT_API_RAW_MAPPED_SPEC.find(_UT_API_SPEC_SECTION_WITH_MAPPING),
        coverage=0,
        created_by=user,
    )
    ut_nested_document = get_document_model(client_db, utilities)
    ut_document_document_mapping = DocumentDocumentModel(
        document_mapping_api=ut_api_document_mapping,
        document_mapping_document=None,
        document=ut_nested_document,
        section="Nested section",
        offset=0,
        coverage=50,
        created_by=user,
    )
    ut_nested_document_2 = get_document_model(client_db, utilities)
    ut_document_document_mapping_2 = DocumentDocumentModel(
        document_mapping_api=None,
        document_mapping_document=ut_document_document_mapping,
        document=ut_nested_document_2,
        section="Nested section 2",
        offset=0,
        coverage=50,
        created_by=user,
    )
    client_db.session.add(ut_api)
    client_db.session.add(ut_document)
    client_db.session.add(ut_api_document_mapping)
    client_db.session.add(ut_nested_document)
    client_db.session.add(ut_document_document_mapping)
    client_db.session.add(ut_nested_document_2)
    client_db.session.add(ut_document_document_mapping_2)
    client_db.session.commit()

    yield (
        ut_api,
        ut_api_document_mapping,
        ut_document_document_mapping,
        ut_document_document_mapping_2,
    )

    # remove the raw_spec tempfile
    if os.path.isfile(raw_spec.name):
        os.remove(raw_spec.name)


@pytest.fixture()
def document_db(client_db, ut_user_db, utilities):
    """ Create Document """

    ut_document = get_document_model(client_db, utilities)

    client_db.session.add(ut_document)
    client_db.session.commit()

    yield ut_document


def test_login(user_authentication):
    """ Just ensure that the test user is logged in """
    assert user_authentication.status_code == HTTPStatus.OK


# Common Tests


def test_put_unexisting_api(client):
    """ Use an API with invalid id """
    response = client.get(_MAPPING_DOCUMENT_DOCUMENTS_URL, query_string={'api-id': 0, 'relation-id': 0})
    assert response.status_code == HTTPStatus.NOT_FOUND

    response = client.post(_MAPPING_DOCUMENT_DOCUMENTS_URL, json={'api-id': 0})
    assert response.status_code == HTTPStatus.NOT_FOUND

    response = client.put(_MAPPING_DOCUMENT_DOCUMENTS_URL, json={'api-id': 0})
    assert response.status_code == HTTPStatus.NOT_FOUND

    response = client.delete(_MAPPING_DOCUMENT_DOCUMENTS_URL, json={'api-id': 0})
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_put_unauthorized_fail(client, client_db, restricted_api_db, ut_reader_user_db, utilities):
    """ Use an API with write restrictions: PUT is not allowed for unauthorized users """

    ut_document_dict = get_document_model(client_db, utilities).as_dict()
    ut_document_dict.pop('id', None)

    mapping_data = {
        'api-id': restricted_api_db.id,
        'relation-to': 'api',
        'relation-id': 0,
        'coverage': 50,
        'document': ut_document_dict,
        'parent-document': {
            'id': 0
        },
        'user-id': ut_reader_user_db.id,
        'token': ut_reader_user_db.token
    }
    response = client.get(_MAPPING_DOCUMENT_DOCUMENTS_URL, query_string=mapping_data)
    assert response.status_code == HTTPStatus.UNAUTHORIZED

    response = client.post(_MAPPING_DOCUMENT_DOCUMENTS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.UNAUTHORIZED

    response = client.put(_MAPPING_DOCUMENT_DOCUMENTS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.UNAUTHORIZED

    response = client.delete(_MAPPING_DOCUMENT_DOCUMENTS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.UNAUTHORIZED


# Test GET

@pytest.mark.parametrize('mandatory_field', ['relation-id', 'relation-to'])
def test_get_missed_fields(client, user_authentication, mapped_api_doc_doc_db, mandatory_field):
    """ Read Document without sending a mandatory field  """

    api, api_doc_mapping, api_doc_doc_mapping = mapped_api_doc_doc_db
    get_query = {
        'api-id': api.id,
        'relation-id': api_doc_mapping.id,
        'relation-to': 'api',
        'user-id': user_authentication.json['id'],
        'token': user_authentication.json['token']
    }
    get_query.pop(mandatory_field)
    response = client.get(_MAPPING_DOCUMENT_DOCUMENTS_URL, query_string=get_query)
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_get_bad_payload(client, user_authentication, mapped_api_doc_doc_db):
    """ Read Document sending an unexpected payload  """

    api, api_doc_mapping, api_doc_doc_mapping = mapped_api_doc_doc_db
    get_query = {
        'api-id': api.id,
        'relation-id': api_doc_mapping.id,
        'relation-to': 'unexpected value',
        'user-id': user_authentication.json['id'],
        'token': user_authentication.json['token']
    }
    response = client.get(_MAPPING_DOCUMENT_DOCUMENTS_URL, query_string=get_query)
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_get_relation_to_api(client, user_authentication, mapped_api_doc_doc_db):
    """ Read Document with parent mapped to api """

    api, api_doc_mapping, api_doc_doc_mapping = mapped_api_doc_doc_db
    get_query = {
        'api-id': api.id,
        'relation-id': api_doc_mapping.id,
        'relation-to': 'api',
        'user-id': user_authentication.json['id'],
        'token': user_authentication.json['token']
    }

    response = client.get(_MAPPING_DOCUMENT_DOCUMENTS_URL, query_string=get_query)
    assert response.status_code == HTTPStatus.OK
    assert isinstance(response.json, list)
    assert len(response.json) == 1


def test_get_relation_to_document(client, user_authentication, mapped_api_doc_doc_doc_db):
    """ Read Document with parent mapped to document """

    api, api_doc_mapping, api_doc_doc_mapping, api_doc_doc_doc_mapping = mapped_api_doc_doc_doc_db
    get_query = {
        'api-id': api.id,
        'relation-id': api_doc_doc_mapping.id,
        'relation-to': 'document',
        'user-id': user_authentication.json['id'],
        'token': user_authentication.json['token']
    }

    response = client.get(_MAPPING_DOCUMENT_DOCUMENTS_URL, query_string=get_query)
    assert response.status_code == HTTPStatus.OK
    assert isinstance(response.json, list)
    assert len(response.json) == 1


# Test POST

@pytest.mark.parametrize('mandatory_field', ['relation-id', 'relation-to', 'coverage', 'parent-document'])
def test_post_missed_fields(client, client_db, user_authentication, mapped_api_doc_doc_db, utilities, mandatory_field):
    """ File a nested Document without sending a mandatory field  """

    ut_document_dict = get_document_model(client_db, utilities).as_dict()
    ut_document_dict.pop('id', None)

    # skip relation-to
    api, api_doc_mapping, api_doc_doc_mapping = mapped_api_doc_doc_db
    mapping_data = {
        'api-id': api.id,
        'relation-id': 0,
        'relation-to': 'api',
        'coverage': 50,
        'document': ut_document_dict,
        'parent-document': {
            'id': 0
        },
        'user-id': user_authentication.json['id'],
        'token': user_authentication.json['token']
    }
    mapping_data.pop(mandatory_field)
    response = client.post(_MAPPING_DOCUMENT_DOCUMENTS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.BAD_REQUEST

    # skip parent-document.id
    mapping_data = {
        'api-id': api.id,
        'relation-id': 0,
        'relation-to': 'api',
        'coverage': 50,
        'document': ut_document_dict,
        'parent-document': {
        },
        'user-id': user_authentication.json['id'],
        'token': user_authentication.json['token']
    }
    response = client.post(_MAPPING_DOCUMENT_DOCUMENTS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_post_bad_payload(client, client_db, user_authentication, mapped_api_doc_doc_db, utilities):
    """ Write Document mapping sending an unexpected payload  """

    ut_document_dict = get_document_model(client_db, utilities).as_dict()
    ut_document_dict.pop('id', None)

    # bad relation-to
    api, api_doc_mapping, api_doc_doc_mapping = mapped_api_doc_doc_db
    mapping_data = {
        'api-id': api.id,
        'relation-id': api_doc_mapping.id,
        'relation-to': 'unexpected value',
        'coverage': 50,
        'document': ut_document_dict,
        'parent-document': {
            'id': api_doc_mapping.document_id
        },
        'user-id': user_authentication.json['id'],
        'token': user_authentication.json['token']
    }
    response = client.post(_MAPPING_DOCUMENT_DOCUMENTS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.BAD_REQUEST

    # bad relation-id
    api, api_doc_mapping, api_doc_doc_mapping = mapped_api_doc_doc_db
    mapping_data = {
        'api-id': api.id,
        'relation-id': 0,
        'relation-to': 'api',
        'coverage': 50,
        'document': ut_document_dict,
        'parent-document': {
            'id': api_doc_mapping.document_id
        },
        'user-id': user_authentication.json['id'],
        'token': user_authentication.json['token']
    }
    response = client.post(_MAPPING_DOCUMENT_DOCUMENTS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.parametrize('document_field', ['title', 'description'])
def test_post_new_to_api(client, client_db, user_authentication, mapped_api_doc_doc_db, utilities, document_field):
    """ Write a new Document mapping related to a
    Software Component Reference Document Snippet
    """

    ut_document_dict = get_document_model(client_db, utilities).as_dict()
    ut_document_dict = {k.replace("_", "-"): v for k, v in ut_document_dict.items()}
    ut_document_dict.pop('id')
    ut_document_dict.pop(document_field)

    api, api_doc_mapping, api_doc_doc_mapping = mapped_api_doc_doc_db

    # Missed field on document
    mapping_data = {
        'api-id': api.id,
        'coverage': 50,
        'relation-id': api_doc_mapping.id,
        'relation-to': 'api',
        'document': ut_document_dict,
        'parent-document': {
            'id': api_doc_mapping.document_id
        },
        'user-id': user_authentication.json['id'],
        'token': user_authentication.json['token']
    }

    response = client.post(_MAPPING_DOCUMENT_DOCUMENTS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.BAD_REQUEST

    # New Document - Valid data
    ut_document_dict = get_document_model(client_db, utilities).as_dict()
    ut_document_dict = {k.replace("_", "-"): v for k, v in ut_document_dict.items()}
    ut_document_dict.pop('id', None)

    mapping_data = {
        'api-id': api.id,
        'coverage': 50,
        'relation-id': api_doc_mapping.id,
        'relation-to': 'api',
        'document': ut_document_dict,
        'parent-document': {
            'id': api_doc_mapping.document_id
        },
        'user-id': user_authentication.json['id'],
        'token': user_authentication.json['token']
    }

    response = client.post(_MAPPING_DOCUMENT_DOCUMENTS_URL, json=mapping_data)

    assert response.status_code == HTTPStatus.OK
    assert isinstance(response.json, dict)
    assert response.json.get("__tablename__", "") == DocumentDocumentModel.__tablename__

    # New Document - Same data: Conflict
    response = client.post(_MAPPING_DOCUMENT_DOCUMENTS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.CONFLICT

    # Existing Document - Valid data (not yet mapped)
    new_document = get_document_model(client_db, utilities)
    ut_document_dict = {k.replace("_", "-"): v for k, v in ut_document_dict.items()}
    client_db.session.add(new_document)
    client_db.session.commit()

    mapping_data = {
        'api-id': api.id,
        'coverage': 50,
        'relation-id': api_doc_mapping.id,
        'relation-to': 'api',
        'document': new_document.as_dict(),
        'parent-document': {
            'id': api_doc_mapping.document_id
        },
        'user-id': user_authentication.json['id'],
        'token': user_authentication.json['token']
    }

    response = client.post(_MAPPING_DOCUMENT_DOCUMENTS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.OK
    assert isinstance(response.json, dict)
    assert response.json.get("__tablename__", "") == DocumentDocumentModel.__tablename__

    # Existing Document - Same data: Conflict
    response = client.post(_MAPPING_DOCUMENT_DOCUMENTS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.CONFLICT

    # Unexisting Document - Unvalid data (deleted Document)
    new_document = get_document_model(client_db, utilities)
    client_db.session.add(new_document)
    client_db.session.commit()
    new_document_dict = new_document.as_dict()
    new_document_dict = {k.replace("_", "-"): v for k, v in new_document_dict.items()}
    client_db.session.delete(new_document)
    client_db.session.commit()

    mapping_data = {
        'api-id': api.id,
        'coverage': 50,
        'relation-id': api_doc_mapping.id,
        'relation-to': 'api',
        'document': new_document_dict,
        'parent-document': {
            'id': api_doc_mapping.document_id
        },
        'user-id': user_authentication.json['id'],
        'token': user_authentication.json['token']
    }

    response = client.post(_MAPPING_DOCUMENT_DOCUMENTS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_post_new_to_document(client, client_db, user_authentication, mapped_api_doc_doc_doc_db, utilities):
    """ Write a new Document mapping related to a Document
    """

    ut_document_dict = get_document_model(client_db, utilities).as_dict()

    new_api = _create_software_component(client_db, utilities)

    api, api_doc_mapping, api_doc_doc_mapping, api_doc_doc_doc_mapping = mapped_api_doc_doc_doc_db

    # Unexisting relation-id
    mapping_data = {
        'api-id': api.id,
        'coverage': 50,
        'relation-id': 0,
        'relation-to': 'document',
        'document': ut_document_dict,
        'parent-document': {
            'id': api_doc_doc_mapping.document_id
        },
        'user-id': user_authentication.json['id'],
        'token': user_authentication.json['token']
    }

    response = client.post(_MAPPING_DOCUMENT_DOCUMENTS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.NOT_FOUND

    # Wrong api-id
    mapping_data = {
        'api-id': new_api.id,
        'coverage': 50,
        'relation-id': api_doc_doc_mapping.id,
        'relation-to': 'document',
        'document': ut_document_dict,
        'parent-document': {
            'id': api_doc_doc_mapping.document_id
        },
        'user-id': user_authentication.json['id'],
        'token': user_authentication.json['token']
    }

    response = client.post(_MAPPING_DOCUMENT_DOCUMENTS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.BAD_REQUEST

    # Unexisting mapping api
    mapping_data = {
        'api-id': UNMATCHING_ID,
        'coverage': 50,
        'relation-id': api_doc_doc_mapping.id,
        'relation-to': 'document',
        'document': ut_document_dict,
        'parent-document': {
            'id': api_doc_doc_mapping.document_id
        },
        'user-id': user_authentication.json['id'],
        'token': user_authentication.json['token']
    }

    response = client.post(_MAPPING_DOCUMENT_DOCUMENTS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.NOT_FOUND


# Test PUT

@pytest.mark.parametrize('mandatory_field', ['document', 'coverage', 'relation-id'])
def test_put_miss_fields(client, client_db, user_authentication, mapped_api_doc_doc_db, utilities, mandatory_field):
    """ Update Document mapping sending an unexpected payload  """

    ut_document_dict = get_document_model(client_db, utilities).as_dict()
    ut_document_dict.pop('id', None)

    # miss relation-id
    api, api_doc_mapping, api_doc_doc_mapping = mapped_api_doc_doc_db
    mapping_data = {
        'api-id': api.id,
        'coverage': 50,
        'relation-id': api_doc_mapping.id,
        'document': ut_document_dict,
        'user-id': user_authentication.json['id'],
        'token': user_authentication.json['token']
    }
    mapping_data.pop(mandatory_field)
    response = client.put(_MAPPING_DOCUMENT_DOCUMENTS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_put_bad_payload(client, client_db, user_authentication, mapped_api_doc_doc_db, utilities):
    """ Update Document mapping sending an unexpected payload  """

    ut_document_dict = get_document_model(client_db, utilities).as_dict()
    ut_document_dict.pop('id', None)

    # bad relation-id
    api, api_doc_mapping, api_doc_doc_mapping = mapped_api_doc_doc_db
    mapping_data = {
        'api-id': api.id,
        'relation-id': 0,
        'coverage': 50,
        'document': ut_document_dict,
        'parent-document': {
            'id': api_doc_mapping.document_id
        },
        'user-id': user_authentication.json['id'],
        'token': user_authentication.json['token']
    }
    response = client.put(_MAPPING_DOCUMENT_DOCUMENTS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_put_ok(client, client_db, user_authentication, mapped_api_doc_doc_db, utilities):
    """ Update Document mapping  """

    api, api_doc_mapping, api_doc_doc_mapping = mapped_api_doc_doc_db

    # parent mapped to api
    ut_document_dict = get_document_model(client_db, utilities).as_dict()
    ut_document_dict = {k.replace("_", "-"): v for k, v in ut_document_dict.items()}
    ut_document_dict.pop('id', None)

    mapping_data = {
        'api-id': api.id,
        'coverage': 50,
        'relation-id': api_doc_mapping.id,
        'relation-to': 'api',
        'document': ut_document_dict,
        'parent-document': {
            'id': api_doc_mapping.document_id
        },
        'user-id': user_authentication.json['id'],
        'token': user_authentication.json['token']
    }

    response = client.post(_MAPPING_DOCUMENT_DOCUMENTS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.OK
    assert isinstance(response.json, dict)
    assert response.json.get("__tablename__", "") == DocumentDocumentModel.__tablename__

    # No changes
    mapping_data = {
        'api-id': api.id,
        'coverage': 50,
        'relation-id': response.json.get("relation_id", ""),
        'document': ut_document_dict,
        'user-id': user_authentication.json['id'],
        'token': user_authentication.json['token']
    }
    response = client.put(_MAPPING_DOCUMENT_DOCUMENTS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.OK
    assert response.json.get("__tablename__", "") == DocumentDocumentModel.__tablename__
    assert response.json.get("version", "") == "1.1"
    assert response.json.get("created_by", "") == UT_USER_NAME

    # Change coverage
    mapping_data['coverage'] = 75
    response = client.put(_MAPPING_DOCUMENT_DOCUMENTS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.OK
    assert response.json.get("__tablename__", "") == DocumentDocumentModel.__tablename__
    assert response.json.get("version", "") == "1.2"

    # Change document
    mapping_data['document']['title'] = f"{mapping_data['document']['title']}-mod"
    # Add an unexisting field to document
    mapping_data['document']['unexisting'] = "value"

    response = client.put(_MAPPING_DOCUMENT_DOCUMENTS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.OK
    assert response.json.get("__tablename__", "") == DocumentDocumentModel.__tablename__
    assert response.json.get("version", "") == "2.2"


# Test Delete


def test_delete_bad_payload(client, client_db, user_authentication, mapped_api_doc_doc_db, utilities):
    """ Update Document mapping sending an unexpected payload  """

    ut_document_dict = get_document_model(client_db, utilities).as_dict()
    ut_document_dict = {k.replace("_", "-"): v for k, v in ut_document_dict.items()}
    ut_document_dict.pop('id', None)

    # miss relation-id
    api, api_doc_mapping, api_doc_doc_mapping = mapped_api_doc_doc_db
    mapping_data = {
        'api-id': api.id,
        'coverage': 50,
        'document': ut_document_dict,
        'parent-document': {
            'id': api_doc_mapping.document_id
        },
        'user-id': user_authentication.json['id'],
        'token': user_authentication.json['token']
    }
    response = client.delete(_MAPPING_DOCUMENT_DOCUMENTS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.BAD_REQUEST

    mapping_data = {
        'api-id': api.id,
        'coverage': 50,
        'relation-id': api_doc_mapping.id,
        'relation-to': 'api',
        'document': ut_document_dict,
        'parent-document': {
            'id': api_doc_mapping.document_id
        },
        'user-id': user_authentication.json['id'],
        'token': user_authentication.json['token']
    }

    response = client.post(_MAPPING_DOCUMENT_DOCUMENTS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.OK
    assert isinstance(response.json, dict)
    assert response.json.get("__tablename__", "") == DocumentDocumentModel.__tablename__

    # wrong relation-id
    delete_data = {
        'api-id': api.id,
        'relation-id': 0,
        'user-id': user_authentication.json['id'],
        'token': user_authentication.json['token']
    }
    response = client.delete(_MAPPING_DOCUMENT_DOCUMENTS_URL, json=delete_data)
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_delete_miss_parent(client, client_db, user_authentication, mapped_api_doc_doc_db, utilities):
    """ Delete an unexisting mapping """

    ut_document_dict = get_document_model(client_db, utilities).as_dict()
    ut_document_dict = {k.replace("_", "-"): v for k, v in ut_document_dict.items()}
    ut_document_dict.pop('id', None)
    api, api_doc_mapping, api_doc_doc_mapping = mapped_api_doc_doc_db

    mapping_data = {
        'api-id': api.id,
        'coverage': 50,
        'relation-id': api_doc_mapping.id,
        'relation-to': 'api',
        'document': ut_document_dict,
        'parent-document': {
            'id': api_doc_mapping.document_id
        },
        'user-id': user_authentication.json['id'],
        'token': user_authentication.json['token']
    }

    response = client.post(_MAPPING_DOCUMENT_DOCUMENTS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.OK
    assert isinstance(response.json, dict)
    assert response.json.get("__tablename__", "") == DocumentDocumentModel.__tablename__

    delete_data = {
        'api-id': api.id,
        'relation-id': UNMATCHING_ID,
        'user-id': user_authentication.json['id'],
        'token': user_authentication.json['token']
    }

    response = client.delete(_MAPPING_DOCUMENT_DOCUMENTS_URL, json=delete_data)
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_delete_ok(client, client_db, user_authentication, mapped_api_doc_doc_db, utilities):
    """ Delete a mapping  """

    ut_document_dict = get_document_model(client_db, utilities).as_dict()
    ut_document_dict = {k.replace("_", "-"): v for k, v in ut_document_dict.items()}
    ut_document_dict.pop('id', None)
    api, api_doc_mapping, api_doc_doc_mapping = mapped_api_doc_doc_db

    mapping_data = {
        'api-id': api.id,
        'coverage': 50,
        'relation-id': api_doc_mapping.id,
        'relation-to': 'api',
        'document': ut_document_dict,
        'parent-document': {
            'id': api_doc_mapping.document_id
        },
        'user-id': user_authentication.json['id'],
        'token': user_authentication.json['token']
    }

    response = client.post(_MAPPING_DOCUMENT_DOCUMENTS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.OK
    assert isinstance(response.json, dict)
    assert response.json.get("__tablename__", "") == DocumentDocumentModel.__tablename__

    delete_data = {
        'api-id': api.id,
        'relation-id': response.json.get("relation_id", ""),
        'user-id': user_authentication.json['id'],
        'token': user_authentication.json['token']
    }

    response = client.delete(_MAPPING_DOCUMENT_DOCUMENTS_URL, json=delete_data)
    assert response.status_code == HTTPStatus.OK

    get_query = {
        'api-id': api.id,
        'relation-id': delete_data["relation-id"],
        'relation-to': 'api',
        'user-id': user_authentication.json['id'],
        'token': user_authentication.json['token']
    }

    response = client.get(_MAPPING_DOCUMENT_DOCUMENTS_URL, query_string=get_query)
    assert response.status_code == HTTPStatus.OK
    assert isinstance(response.json, list)
    assert len(response.json) == 0
