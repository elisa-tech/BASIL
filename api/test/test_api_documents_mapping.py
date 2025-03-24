import pytest
import tempfile
from api import api
from db import db_orm
from db.models.db_base import Base
import db.models.init_db as init_db
from db.models.user import UserModel
from db.models.api import ApiModel


_MAPPING_API_DOCUMENTS_URL = '/mapping/api/documents'
_DB_NAME = 'test.db'

_UT_USER_NAME = 'ut_user_name'
_UT_USER_EMAIL = 'ut_user_email'
_UT_USER_PASSWORD = 'ut_user_password'
_UT_USER_ROLE = 'USER'

_UT_API_NAME = 'ut_api_name'
_UT_API_LIBRARY = 'ut_api_library'
_UT_API_LIBRARY_VERSION = 'v1.0.0'
_UT_API_CATEGORY = 'ut_api_category'
_UT_API_CHECKSUM = '123'
_UT_API_IMPLEMENTATION_FILE = 'ut_api_implementation'
_UT_API_IMPLEMENTATION_FILE_FROM_ROW = 42
_UT_API_IMPLEMENTATION_FILE_TO_ROW = 44
_UT_API_TAGS = 'ut_api_tags'

_UT_API_SPEC_MAPPED_SECTION = 'A section for a mapped document.'
_UT_API_RAW_SPEC = f'BASIL UT: {_UT_API_SPEC_MAPPED_SECTION} Used for {_MAPPING_API_DOCUMENTS_URL}.'

api.app.config['TESTING'] = True
api.app.config['DEBUG'] = True


@pytest.fixture
def client():
    with api.app.test_client() as client:
        yield client


class AuthActions(object):
    def __init__(self, client):
        self._client = client

    def login(self, email=_UT_USER_EMAIL, password=_UT_USER_PASSWORD):
        return self._client.post(
            '/user/login',
            json={'email': email, 'password': password}
        )


@pytest.fixture
def auth(client):
    return AuthActions(client)


@pytest.fixture(scope="module", autouse=True)
def client_db():
    init_db.initialization(db_name=_DB_NAME)
    dbi = db_orm.DbInterface(_DB_NAME)

    # add user for unit testing
    ut_test_user = UserModel(_UT_USER_NAME, _UT_USER_EMAIL, _UT_USER_PASSWORD, _UT_USER_ROLE)
    dbi.session.add(ut_test_user)

    # create raw API specification in a temporary file
    raw_spec = tempfile.NamedTemporaryFile(mode="w", delete=True, delete_on_close=False)
    raw_spec.write(_UT_API_RAW_SPEC)
    raw_spec.flush()

    # create API
    ut_api = ApiModel(_UT_API_NAME, _UT_API_LIBRARY, _UT_API_LIBRARY_VERSION, raw_spec.name,
                    _UT_API_CATEGORY, _UT_API_CHECKSUM, _UT_API_IMPLEMENTATION_FILE,
                    _UT_API_IMPLEMENTATION_FILE_FROM_ROW, _UT_API_IMPLEMENTATION_FILE_TO_ROW,
                    _UT_API_TAGS, ut_test_user)
    dbi.session.add(ut_api)

    dbi.session.commit()
    global _UT_API_ID
    _UT_API_ID = ut_api.id

    yield

    Base.metadata.drop_all(bind=dbi.engine)


@pytest.fixture(scope="module")
def document_file():
    with tempfile.NamedTemporaryFile(mode="w", delete=True, delete_on_close=False) as fp:
        fp.write('BASIL UT: A document to map API section.')
        fp.flush()
        yield fp


def test_api_document_post_ok(client, auth, document_file):
    """ Nominal test for mapping a section """
    login_response = auth.login()
    assert login_response.status_code == 200

    # ensure there is no mapped sections for this API
    response = client.get(_MAPPING_API_DOCUMENTS_URL, query_string={'api-id': _UT_API_ID})
    assert response.status_code == 200
    assert response.json['mapped'] == []
    assert response.json['unmapped'] != []

    # add new document
    api_data = {'user-id': login_response.json['id'],
               'token': login_response.json['token'],
               'api-id': _UT_API_ID,
               'section': _UT_API_SPEC_MAPPED_SECTION,
               'offset': _UT_API_RAW_SPEC.find(_UT_API_SPEC_MAPPED_SECTION),
               'coverage': 0,
               'document': {
                        'title': 'ut_doc_title',
                        'description': 'ut_doc_description',
                        'document_type': 'ut_doc_document_type',
                        'spdx_relation': 'ut_doc_spdx_relation',
                        'url': document_file.name,
                        'section': 'ut_doc_section',
                        'offset': 0
                    }
               }

    response = client.post(_MAPPING_API_DOCUMENTS_URL, json=api_data)
    assert response.status_code == 200

    # ensure document is added
    response = client.get(_MAPPING_API_DOCUMENTS_URL, query_string={'api-id': _UT_API_ID})
    assert response.status_code == 200
    assert response.json['mapped'] != []