import pytest
from http import HTTPStatus

from db.models.user import UserModel
from db.models.justification import JustificationModel
from db.models.api_justification import ApiJustificationModel
from db.models.api import ApiModel

from conftest import (
    UT_USER_EMAIL,
    AuthActions,
)

_JUSTIFICATIONS_URL = '/justifications'

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
def unused_justification_db(client_db, ut_user_db, utilities):
    user = client_db.session.query(UserModel).filter(
        UserModel.email == UT_USER_EMAIL).one()
    j = JustificationModel(
        f'Unused justification #{utilities.generate_random_hex_string8()}',
        user,
    )
    client_db.session.add(j)
    client_db.session.commit()
    yield j


@pytest.fixture()
def used_justification_db(client_db, ut_user_db, utilities):
    """Create a justification that is mapped to an API (i.e. in use)."""
    user = client_db.session.query(UserModel).filter(
        UserModel.email == UT_USER_EMAIL).one()

    j = JustificationModel(
        f'Used justification #{utilities.generate_random_hex_string8()}',
        user,
    )
    api = ApiModel(
        f'ut_api_{utilities.generate_random_hex_string8()}',
        'ut_lib', 'v1', 'stub.md', 'ut_cat',
        utilities.generate_random_hex_string8(),
        'stub.impl', 0, 42, 'ut_tags', user,
    )
    client_db.session.add(j)
    client_db.session.add(api)
    client_db.session.flush()

    mapping = ApiJustificationModel(api, j, 'section', 0, 0, user)
    client_db.session.add(mapping)
    client_db.session.commit()
    yield j


# ------------------------------------------------------------------
# GET
# ------------------------------------------------------------------

def test_login(user_authentication):
    assert user_authentication.status_code == HTTPStatus.OK


def test_get_justifications_ok(client, unused_justification_db):
    response = client.get(_JUSTIFICATIONS_URL)
    assert response.status_code == HTTPStatus.OK
    assert isinstance(response.json, list)
    assert len(response.json) > 0


def test_get_justifications_fields(client, unused_justification_db):
    response = client.get(_JUSTIFICATIONS_URL)
    assert response.status_code == HTTPStatus.OK
    justification = next(
        (j for j in response.json if j['id'] == unused_justification_db.id),
        None,
    )
    assert justification is not None
    assert 'id' in justification
    assert 'description' in justification
    assert 'status' in justification
    assert 'created_by' in justification
    assert 'version' in justification
    assert 'used' in justification


def test_get_justifications_used_flag_false(client, unused_justification_db):
    response = client.get(
        _JUSTIFICATIONS_URL,
        query_string={'field1': 'id', 'filter1': unused_justification_db.id},
    )
    assert response.status_code == HTTPStatus.OK
    assert len(response.json) == 1
    assert response.json[0]['used'] is False


def test_get_justifications_used_flag_true(client, used_justification_db):
    response = client.get(
        _JUSTIFICATIONS_URL,
        query_string={'field1': 'id', 'filter1': used_justification_db.id},
    )
    assert response.status_code == HTTPStatus.OK
    assert len(response.json) == 1
    assert response.json[0]['used'] is True


def test_get_justifications_minimal_mode(client, unused_justification_db):
    response = client.get(
        _JUSTIFICATIONS_URL,
        query_string={'mode': 'minimal'},
    )
    assert response.status_code == HTTPStatus.OK
    assert len(response.json) > 0
    for j in response.json:
        assert set(j.keys()) == {'id', 'description'}


# ------------------------------------------------------------------
# DELETE
# ------------------------------------------------------------------

def test_delete_missing_auth_fields(client, unused_justification_db):
    response = client.delete(
        _JUSTIFICATIONS_URL,
        json={'id': unused_justification_db.id},
    )
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_delete_invalid_token(client, user_authentication, unused_justification_db):
    response = client.delete(
        _JUSTIFICATIONS_URL,
        json={
            'id': unused_justification_db.id,
            'user-id': user_authentication.json['id'],
            'token': 'invalid-token',
        },
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED


def test_delete_guest_forbidden(client, guest_authentication, unused_justification_db):
    response = client.delete(
        _JUSTIFICATIONS_URL,
        json={
            'id': unused_justification_db.id,
            'user-id': guest_authentication.json['id'],
            'token': guest_authentication.json['token'],
        },
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED


@pytest.mark.parametrize('missing_field', ['id', 'user-id', 'token'])
def test_delete_missing_mandatory_field(client, user_authentication, unused_justification_db, missing_field):
    data = {
        'id': unused_justification_db.id,
        'user-id': user_authentication.json['id'],
        'token': user_authentication.json['token'],
    }
    data.pop(missing_field)
    response = client.delete(_JUSTIFICATIONS_URL, json=data)
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_delete_used_justification(client, user_authentication, used_justification_db):
    response = client.delete(
        _JUSTIFICATIONS_URL,
        json={
            'id': used_justification_db.id,
            'user-id': user_authentication.json['id'],
            'token': user_authentication.json['token'],
        },
    )
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_delete_nonexistent_justification(client, user_authentication):
    from sqlalchemy.exc import NoResultFound
    non_existent_id = 99999
    with pytest.raises(NoResultFound):
        client.delete(
            _JUSTIFICATIONS_URL,
            json={
                'id': non_existent_id,
                'user-id': user_authentication.json['id'],
                'token': user_authentication.json['token'],
            },
        )


def test_delete_ok(client, client_db, user_authentication, unused_justification_db):
    justification_id = unused_justification_db.id

    response = client.get(
        _JUSTIFICATIONS_URL,
        query_string={'field1': 'id', 'filter1': justification_id},
    )
    assert response.status_code == HTTPStatus.OK
    assert len(response.json) == 1

    response = client.delete(
        _JUSTIFICATIONS_URL,
        json={
            'id': justification_id,
            'user-id': user_authentication.json['id'],
            'token': user_authentication.json['token'],
        },
    )
    assert response.status_code == HTTPStatus.OK

    response = client.get(
        _JUSTIFICATIONS_URL,
        query_string={'field1': 'id', 'filter1': justification_id},
    )
    assert response.status_code == HTTPStatus.OK
    assert len(response.json) == 0
