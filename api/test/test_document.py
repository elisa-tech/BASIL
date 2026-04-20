import pytest
from http import HTTPStatus

from db.models.user import UserModel
from db.models.document import DocumentModel
from db.models.api_document import ApiDocumentModel
from db.models.api import ApiModel

from conftest import (
    UT_USER_EMAIL,
    AuthActions,
)

_DOCUMENTS_URL = '/documents'

_UT_GUEST_NAME = 'ut_guest_name'
_UT_GUEST_EMAIL = 'ut_guest_email'
_UT_GUEST_PASSWORD = 'ut_guest_password'


@pytest.fixture(scope="module")
def guest_user_db(client_db):
    from db import db_orm
    dbi = db_orm.DbInterface('test')
    guest = UserModel(_UT_GUEST_NAME, _UT_GUEST_EMAIL, _UT_GUEST_PASSWORD, 'GUEST')
    dbi.session.add(guest)
    dbi.session.commit()
    yield guest


@pytest.fixture(scope="module")
def guest_authentication(client, guest_user_db):
    auth = AuthActions(client)
    return auth.login(email=_UT_GUEST_EMAIL, password=_UT_GUEST_PASSWORD)


@pytest.fixture()
def unused_document_db(client_db, ut_user_db, utilities):
    user = client_db.session.query(UserModel).filter(
        UserModel.email == UT_USER_EMAIL).one()
    d = DocumentModel(
        title=f'Unused document #{utilities.generate_random_hex_string8()}',
        description='A test document',
        document_type='file',
        spdx_relation='DESCRIBES',
        url='https://example.com/doc',
        section='',
        offset=-1,
        valid=-1,
        created_by=user,
    )
    client_db.session.add(d)
    client_db.session.commit()
    yield d


@pytest.fixture()
def used_document_db(client_db, ut_user_db, utilities):
    """Create a document that is mapped to an API (i.e. in use)."""
    user = client_db.session.query(UserModel).filter(
        UserModel.email == UT_USER_EMAIL).one()

    d = DocumentModel(
        title=f'Used document #{utilities.generate_random_hex_string8()}',
        description='A test document in use',
        document_type='file',
        spdx_relation='DESCRIBES',
        url='https://example.com/doc-used',
        section='',
        offset=-1,
        valid=-1,
        created_by=user,
    )
    api = ApiModel(
        f'ut_api_{utilities.generate_random_hex_string8()}',
        'ut_lib', 'v1', 'stub.md', 'ut_cat',
        utilities.generate_random_hex_string8(),
        'stub.impl', 0, 42, 'ut_tags', user,
    )
    client_db.session.add(d)
    client_db.session.add(api)
    client_db.session.flush()

    mapping = ApiDocumentModel(api, d, 'section', 0, 100, user)
    client_db.session.add(mapping)
    client_db.session.commit()
    yield d


# ------------------------------------------------------------------
# GET
# ------------------------------------------------------------------

def test_login(user_authentication):
    assert user_authentication.status_code == HTTPStatus.OK


def test_get_documents_ok(client, unused_document_db):
    response = client.get(_DOCUMENTS_URL)
    assert response.status_code == HTTPStatus.OK
    assert isinstance(response.json, list)
    assert len(response.json) > 0


def test_get_documents_fields(client, unused_document_db):
    response = client.get(_DOCUMENTS_URL)
    assert response.status_code == HTTPStatus.OK
    doc = next(
        (d for d in response.json if d['id'] == unused_document_db.id),
        None,
    )
    assert doc is not None
    assert 'id' in doc
    assert 'title' in doc
    assert 'description' in doc
    assert 'document_type' in doc
    assert 'status' in doc
    assert 'created_by' in doc
    assert 'version' in doc
    assert 'used' in doc


def test_get_documents_used_flag_false(client, unused_document_db):
    response = client.get(
        _DOCUMENTS_URL,
        query_string={'field1': 'id', 'filter1': unused_document_db.id},
    )
    assert response.status_code == HTTPStatus.OK
    assert len(response.json) == 1
    assert response.json[0]['used'] is False


def test_get_documents_used_flag_true(client, used_document_db):
    response = client.get(
        _DOCUMENTS_URL,
        query_string={'field1': 'id', 'filter1': used_document_db.id},
    )
    assert response.status_code == HTTPStatus.OK
    assert len(response.json) == 1
    assert response.json[0]['used'] is True


# ------------------------------------------------------------------
# DELETE
# ------------------------------------------------------------------

def test_delete_missing_auth_fields(client, unused_document_db):
    response = client.delete(
        _DOCUMENTS_URL,
        json={'id': unused_document_db.id},
    )
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_delete_invalid_token(client, user_authentication, unused_document_db):
    response = client.delete(
        _DOCUMENTS_URL,
        json={
            'id': unused_document_db.id,
            'user-id': user_authentication.json['id'],
            'token': 'invalid-token',
        },
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED


def test_delete_guest_forbidden(client, guest_authentication, unused_document_db):
    response = client.delete(
        _DOCUMENTS_URL,
        json={
            'id': unused_document_db.id,
            'user-id': guest_authentication.json['id'],
            'token': guest_authentication.json['token'],
        },
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED


@pytest.mark.parametrize('missing_field', ['id', 'user-id', 'token'])
def test_delete_missing_mandatory_field(client, user_authentication, unused_document_db, missing_field):
    data = {
        'id': unused_document_db.id,
        'user-id': user_authentication.json['id'],
        'token': user_authentication.json['token'],
    }
    data.pop(missing_field)
    response = client.delete(_DOCUMENTS_URL, json=data)
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_delete_used_document(client, user_authentication, used_document_db):
    response = client.delete(
        _DOCUMENTS_URL,
        json={
            'id': used_document_db.id,
            'user-id': user_authentication.json['id'],
            'token': user_authentication.json['token'],
        },
    )
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_delete_nonexistent_document(client, user_authentication):
    from sqlalchemy.exc import NoResultFound
    non_existent_id = 99999
    with pytest.raises(NoResultFound):
        client.delete(
            _DOCUMENTS_URL,
            json={
                'id': non_existent_id,
                'user-id': user_authentication.json['id'],
                'token': user_authentication.json['token'],
            },
        )


def test_delete_ok(client, client_db, user_authentication, unused_document_db):
    document_id = unused_document_db.id

    response = client.get(
        _DOCUMENTS_URL,
        query_string={'field1': 'id', 'filter1': document_id},
    )
    assert response.status_code == HTTPStatus.OK
    assert len(response.json) == 1

    response = client.delete(
        _DOCUMENTS_URL,
        json={
            'id': document_id,
            'user-id': user_authentication.json['id'],
            'token': user_authentication.json['token'],
        },
    )
    assert response.status_code == HTTPStatus.OK

    response = client.get(
        _DOCUMENTS_URL,
        query_string={'field1': 'id', 'filter1': document_id},
    )
    assert response.status_code == HTTPStatus.OK
    assert len(response.json) == 0
