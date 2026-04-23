import pytest
from http import HTTPStatus

from db.models.user import UserModel
from db.models.sw_requirement import SwRequirementModel
from db.models.api_sw_requirement import ApiSwRequirementModel
from db.models.api import ApiModel

from conftest import (
    UT_USER_EMAIL,
    AuthActions,
)

_SW_REQUIREMENTS_URL = '/sw-requirements'

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
def unused_sw_requirement_db(client_db, ut_user_db, utilities):
    user = client_db.session.query(UserModel).filter(
        UserModel.email == UT_USER_EMAIL).one()
    sr = SwRequirementModel(
        f'Unused SR #{utilities.generate_random_hex_string8()}',
        f'Description #{utilities.generate_random_hex_string8()}',
        user,
    )
    client_db.session.add(sr)
    client_db.session.commit()
    yield sr


@pytest.fixture()
def used_sw_requirement_db(client_db, ut_user_db, utilities):
    """Create a sw requirement that is mapped to an API (i.e. in use)."""
    user = client_db.session.query(UserModel).filter(
        UserModel.email == UT_USER_EMAIL).one()

    sr = SwRequirementModel(
        f'Used SR #{utilities.generate_random_hex_string8()}',
        f'Description #{utilities.generate_random_hex_string8()}',
        user,
    )
    api = ApiModel(
        f'ut_api_{utilities.generate_random_hex_string8()}',
        'ut_lib', 'v1', 'stub.md', 'ut_cat',
        utilities.generate_random_hex_string8(),
        'stub.impl', 0, 42, 'ut_tags', user,
    )
    client_db.session.add(sr)
    client_db.session.add(api)
    client_db.session.flush()

    mapping = ApiSwRequirementModel(api, sr, 'section', 0, 0, user)
    client_db.session.add(mapping)
    client_db.session.commit()
    yield sr


# ------------------------------------------------------------------
# GET
# ------------------------------------------------------------------

def test_login(user_authentication):
    assert user_authentication.status_code == HTTPStatus.OK


def test_get_sw_requirements_ok(client, unused_sw_requirement_db):
    response = client.get(_SW_REQUIREMENTS_URL)
    assert response.status_code == HTTPStatus.OK
    assert isinstance(response.json, list)
    assert len(response.json) > 0


def test_get_sw_requirements_fields(client, unused_sw_requirement_db):
    response = client.get(_SW_REQUIREMENTS_URL)
    assert response.status_code == HTTPStatus.OK
    sw_requirement = next(
        (sr for sr in response.json if sr['id'] == unused_sw_requirement_db.id),
        None,
    )
    assert sw_requirement is not None
    assert 'id' in sw_requirement
    assert 'title' in sw_requirement
    assert 'description' in sw_requirement
    assert 'status' in sw_requirement
    assert 'created_by' in sw_requirement
    assert 'version' in sw_requirement
    assert 'used' in sw_requirement


def test_get_sw_requirements_used_flag_false(client, unused_sw_requirement_db):
    response = client.get(
        _SW_REQUIREMENTS_URL,
        query_string={'field1': 'id', 'filter1': unused_sw_requirement_db.id},
    )
    assert response.status_code == HTTPStatus.OK
    assert len(response.json) == 1
    assert response.json[0]['used'] is False


def test_get_sw_requirements_used_flag_true(client, used_sw_requirement_db):
    response = client.get(
        _SW_REQUIREMENTS_URL,
        query_string={'field1': 'id', 'filter1': used_sw_requirement_db.id},
    )
    assert response.status_code == HTTPStatus.OK
    assert len(response.json) == 1
    assert response.json[0]['used'] is True


def test_get_sw_requirements_minimal_mode(client, unused_sw_requirement_db):
    response = client.get(
        _SW_REQUIREMENTS_URL,
        query_string={'mode': 'minimal'},
    )
    assert response.status_code == HTTPStatus.OK
    assert len(response.json) > 0
    for sr in response.json:
        assert set(sr.keys()) == {'id', 'title'}


# ------------------------------------------------------------------
# DELETE
# ------------------------------------------------------------------

def test_delete_missing_auth_fields(client, unused_sw_requirement_db):
    response = client.delete(
        _SW_REQUIREMENTS_URL,
        json={'id': unused_sw_requirement_db.id},
    )
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_delete_invalid_token(client, user_authentication, unused_sw_requirement_db):
    response = client.delete(
        _SW_REQUIREMENTS_URL,
        json={
            'id': unused_sw_requirement_db.id,
            'user-id': user_authentication.json['id'],
            'token': 'invalid-token',
        },
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED


def test_delete_guest_forbidden(client, guest_authentication, unused_sw_requirement_db):
    response = client.delete(
        _SW_REQUIREMENTS_URL,
        json={
            'id': unused_sw_requirement_db.id,
            'user-id': guest_authentication.json['id'],
            'token': guest_authentication.json['token'],
        },
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED


@pytest.mark.parametrize('missing_field', ['id', 'user-id', 'token'])
def test_delete_missing_mandatory_field(client, user_authentication, unused_sw_requirement_db, missing_field):
    data = {
        'id': unused_sw_requirement_db.id,
        'user-id': user_authentication.json['id'],
        'token': user_authentication.json['token'],
    }
    data.pop(missing_field)
    response = client.delete(_SW_REQUIREMENTS_URL, json=data)
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_delete_used_sw_requirement(client, user_authentication, used_sw_requirement_db):
    response = client.delete(
        _SW_REQUIREMENTS_URL,
        json={
            'id': used_sw_requirement_db.id,
            'user-id': user_authentication.json['id'],
            'token': user_authentication.json['token'],
        },
    )
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_delete_nonexistent_sw_requirement(client, user_authentication):
    from sqlalchemy.exc import NoResultFound
    non_existent_id = 99999
    with pytest.raises(NoResultFound):
        client.delete(
            _SW_REQUIREMENTS_URL,
            json={
                'id': non_existent_id,
                'user-id': user_authentication.json['id'],
                'token': user_authentication.json['token'],
            },
        )


def test_delete_ok(client, client_db, user_authentication, unused_sw_requirement_db):
    sw_requirement_id = unused_sw_requirement_db.id

    response = client.get(
        _SW_REQUIREMENTS_URL,
        query_string={'field1': 'id', 'filter1': sw_requirement_id},
    )
    assert response.status_code == HTTPStatus.OK
    assert len(response.json) == 1

    response = client.delete(
        _SW_REQUIREMENTS_URL,
        json={
            'id': sw_requirement_id,
            'user-id': user_authentication.json['id'],
            'token': user_authentication.json['token'],
        },
    )
    assert response.status_code == HTTPStatus.OK

    response = client.get(
        _SW_REQUIREMENTS_URL,
        query_string={'field1': 'id', 'filter1': sw_requirement_id},
    )
    assert response.status_code == HTTPStatus.OK
    assert len(response.json) == 0
