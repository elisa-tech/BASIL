import os
import pytest
import tempfile
from http import HTTPStatus
from db import db_orm
from db.models.user import UserModel
from db.models.api import ApiModel
from db.models.document import DocumentModel
from db.models.api_document import ApiDocumentModel
from conftest import UT_USER_EMAIL
from conftest import DB_NAME


_MAPPING_API_DOCUMENTS_URL = '/mapping/api/documents'

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
_UT_API_RAW_UNMAPPED_SPEC = f'BASIL UT: {_UT_API_SPEC_SECTION_NO_MAPPING} Used for {_MAPPING_API_DOCUMENTS_URL}.'
_UT_API_RAW_MAPPED_SPEC = f'BASIL UT: {_UT_API_SPEC_SECTION_WITH_MAPPING} {_UT_API_SPEC_SECTION_TO_BE_MAPPED} ' \
                          f'Used for {_MAPPING_API_DOCUMENTS_URL}.'

_UT_DOC_TITLE = 'ut_doc_title_1234'


def _filter_sections_mapped_by_documents(mapped_sections):
    return [section for section in mapped_sections if section['documents']]


def _get_sections_mapped_by_docs(client, api_id):
    response = client.get(_MAPPING_API_DOCUMENTS_URL, query_string={'api-id': api_id})
    assert response.status_code == HTTPStatus.OK
    return _filter_sections_mapped_by_documents(response.json['mapped'])


def _assert_mapped_sections(mapped_sections, expected_sections):
    current_sections = [s['section'] for s in mapped_sections].sort()
    assert current_sections == expected_sections.sort()


def _get_mapped_document(mapped_section):
    relation_id = mapped_section['documents'][0]['relation_id']
    document = mapped_section['documents'][0]['document']
    return relation_id, document


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

    yield ut_api.id

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
    ut_document = DocumentModel('doc_title', 'doc_description', 'doc_type', 'doc_spdx_relation',
                                'doc_url', 'doc_section', 0, 1, user)
    ut_api_doc_mapping = ApiDocumentModel(ut_api, ut_document, _UT_API_SPEC_SECTION_WITH_MAPPING,
                                          _UT_API_RAW_MAPPED_SPEC.find(_UT_API_SPEC_SECTION_WITH_MAPPING),
                                          0, user)

    dbi.session.add(ut_api)
    dbi.session.add(ut_document)
    dbi.session.add(ut_api_doc_mapping)

    dbi.session.commit()

    yield ut_api

    # remove the raw_spec tempfile
    if os.path.isfile(raw_spec.name):
        os.remove(raw_spec.name)


@pytest.fixture
def document_file():
    with tempfile.NamedTemporaryFile(mode="w", delete=True) as fp:
        fp.write('BASIL UT: A document to map API section.')
        fp.flush()
        yield fp


def test_login(user_authentication):
    """ Just ensure we are logged in """
    assert user_authentication.status_code == 200


def test_api_document_post_ok(client, user_authentication, unmapped_api_db, document_file):
    """ Nominal test for mapping a section """

    api_id = unmapped_api_db
    mapped_sections = _get_sections_mapped_by_docs(client, api_id)
    assert len(mapped_sections) == 0

    # map a document to unmapped section
    mapping_data = {
        'user-id': user_authentication.json['id'],
        'token': user_authentication.json['token'],
        'api-id': api_id,
        'section': _UT_API_SPEC_SECTION_NO_MAPPING,
        'offset': _UT_API_RAW_UNMAPPED_SPEC.find(_UT_API_SPEC_SECTION_NO_MAPPING),
        'coverage': 0,
        'document': {
            'title': _UT_DOC_TITLE,
            'description': 'ut_doc_description',
            'document_type': 'ut_doc_document_type',
            'spdx_relation': 'ut_doc_spdx_relation',
            'url': document_file.name,
            'section': 'ut_doc_section',
            'offset': 0
        }
    }
    response = client.post(_MAPPING_API_DOCUMENTS_URL, json=mapping_data)
    assert response.status_code == 200

    # ensure document is added
    mapped_sections = _get_sections_mapped_by_docs(client, api_id)
    assert len(mapped_sections) == 1  # there should be only one mapped section
    assert mapped_sections[0]['section'] == _UT_API_SPEC_SECTION_NO_MAPPING
    assert mapped_sections[0]['offset'] == _UT_API_RAW_UNMAPPED_SPEC.find(_UT_API_SPEC_SECTION_NO_MAPPING)
    mapped_documents = mapped_sections[0]['documents']
    assert len(mapped_documents) == 1  # there should be only one document
    assert mapped_documents[0]['document']['title'] == _UT_DOC_TITLE
    assert mapped_documents[0]['created_by'] == UT_USER_EMAIL
    assert mapped_documents[0]['version'] == "1.1"


def test_api_document_put_ok(client, user_authentication, mapped_api_db):
    """ Nominal test for mapping update """

    api_id = mapped_api_db.id
    # there should be only one mapped section: _UT_API_SPEC_SECTION_WITH_MAPPING
    mapped_sections = _get_sections_mapped_by_docs(client, api_id)
    assert len(mapped_sections) == 1
    assert mapped_sections[0]['section'] == _UT_API_SPEC_SECTION_WITH_MAPPING
    # get the relation ID and document
    relation_id = mapped_sections[0]['documents'][0]['relation_id']
    document = mapped_sections[0]['documents'][0]['document']

    # update mapping from _UT_API_SPEC_SECTION_WITH_MAPPING to _UT_API_SPEC_SECTION_TO_BE_MAPPED
    mapping_data = {
        'user-id': user_authentication.json['id'],
        'token': user_authentication.json['token'],
        'relation-id': relation_id,
        'api-id': api_id,
        'section': _UT_API_SPEC_SECTION_TO_BE_MAPPED,
        'offset': _UT_API_RAW_MAPPED_SPEC.find(_UT_API_SPEC_SECTION_TO_BE_MAPPED),
        'coverage': 0,
        'document': document
    }
    response = client.put(_MAPPING_API_DOCUMENTS_URL, json=mapping_data)
    assert response.status_code == 200

    mapped_sections = _get_sections_mapped_by_docs(client, api_id)
    # there should be only one mapped section: _UT_API_SPEC_SECTION_TO_BE_MAPPED
    assert len(mapped_sections) == 1
    assert mapped_sections[0]['section'] == _UT_API_SPEC_SECTION_TO_BE_MAPPED
    assert mapped_sections[0]['offset'] == _UT_API_RAW_MAPPED_SPEC.find(_UT_API_SPEC_SECTION_TO_BE_MAPPED)
    assert len(mapped_sections[0]['documents']) == 1  # there should be only one document
    assert mapped_sections[0]['documents'][0]['version'] == "1.2"


def test_put_update_document(client, user_authentication, mapped_api_db, utilities):
    """ Nominal test for mapping update: SW requirement data """

    api_id = mapped_api_db.id
    # there should be only one mapped section: _UT_API_SPEC_SECTION_WITH_MAPPING
    mapped_sections = _get_sections_mapped_by_docs(client, api_id)
    _assert_mapped_sections(mapped_sections, [_UT_API_SPEC_SECTION_WITH_MAPPING])

    # update sw requirement
    relation_id, document = _get_mapped_document(mapped_sections[0])
    new_document_title = f'{_UT_DOC_TITLE} #{utilities.generate_random_hex_string8()}'
    document['title'] = new_document_title
    mapping_data = {
        'user-id': user_authentication.json['id'],
        'token': user_authentication.json['token'],
        'relation-id': relation_id,
        'api-id': api_id,
        'section': _UT_API_SPEC_SECTION_WITH_MAPPING,
        'offset': _UT_API_RAW_MAPPED_SPEC.find(_UT_API_SPEC_SECTION_WITH_MAPPING),
        'coverage': 0,
        'document': document
    }
    response = client.put(_MAPPING_API_DOCUMENTS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.OK

    # ensure mapping is still to _UT_API_SPEC_SECTION_WITH_MAPPING
    mapped_sections = _get_sections_mapped_by_docs(client, api_id)
    _assert_mapped_sections(mapped_sections, [_UT_API_SPEC_SECTION_WITH_MAPPING])
    # there should be only one SW requirement with the new title
    assert len(mapped_sections[0]['documents']) == 1
    document = mapped_sections[0]['documents'][0]['document']
    assert document['title'] == new_document_title
    assert mapped_sections[0]['documents'][0]['version'] == '2.1'


def test_api_document_delete_ok(client, user_authentication, mapped_api_db):
    """ Nominal test for mapping removal """

    api_id = mapped_api_db.id
    mapped_sections = _get_sections_mapped_by_docs(client, api_id)
    # there should be only one mapped section: _UT_API_SPEC_SECTION_WITH_MAPPING
    assert len(mapped_sections) == 1
    assert mapped_sections[0]['section'] == _UT_API_SPEC_SECTION_WITH_MAPPING
    # get the relation ID
    relation_id = mapped_sections[0]['documents'][0]['relation_id']

    # delete mapping
    mapping_data = {
        'user-id': user_authentication.json['id'],
        'token': user_authentication.json['token'],
        'relation-id': relation_id,
        'api-id': api_id
    }
    response = client.delete(_MAPPING_API_DOCUMENTS_URL, json=mapping_data)
    assert response.status_code == 200

    # ensure the relation is deleted
    mapped_sections = _get_sections_mapped_by_docs(client, api_id)
    assert len(mapped_sections) == 0
