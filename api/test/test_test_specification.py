import pytest
from http import HTTPStatus

from db.models.user import UserModel
from db.models.test_specification import TestSpecificationModel
from db.models.api_test_specification import ApiTestSpecificationModel
from db.models.api import ApiModel

from conftest import (
    UT_USER_EMAIL,
    AuthActions,
)

_TEST_SPECIFICATIONS_URL = '/test-specifications'

_UT_GUEST_NAME = 'ut_ts_guest_name'
_UT_GUEST_EMAIL = 'ut_ts_guest_email'
_UT_GUEST_PASSWORD = 'ut_ts_guest_password'


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
def unused_test_specification_db(client_db, ut_user_db, utilities):
    user = client_db.session.query(UserModel).filter(
        UserModel.email == UT_USER_EMAIL).one()
    ts = TestSpecificationModel(
        f'Unused TS #{utilities.generate_random_hex_string8()}',
        'preconditions',
        'test description',
        'expected behavior',
        user,
    )
    client_db.session.add(ts)
    client_db.session.commit()
    yield ts


@pytest.fixture()
def used_test_specification_db(client_db, ut_user_db, utilities):
    user = client_db.session.query(UserModel).filter(
        UserModel.email == UT_USER_EMAIL).one()

    ts = TestSpecificationModel(
        f'Used TS #{utilities.generate_random_hex_string8()}',
        'preconditions',
        'test description',
        'expected behavior',
        user,
    )
    api = ApiModel(
        f'ut_api_{utilities.generate_random_hex_string8()}',
        'ut_lib', 'v1', 'stub.md', 'ut_cat',
        utilities.generate_random_hex_string8(),
        'stub.impl', 0, 42, 'ut_tags', user,
    )
    client_db.session.add(ts)
    client_db.session.add(api)
    client_db.session.flush()

    mapping = ApiTestSpecificationModel(api, ts, 'section', 0, 0, user)
    client_db.session.add(mapping)
    client_db.session.commit()
    yield ts


# ------------------------------------------------------------------
# GET
# ------------------------------------------------------------------

def test_login(user_authentication):
    assert user_authentication.status_code == HTTPStatus.OK


def test_get_test_specifications_ok(client, unused_test_specification_db):
    response = client.get(_TEST_SPECIFICATIONS_URL)
    assert response.status_code == HTTPStatus.OK
    assert isinstance(response.json, list)
    assert len(response.json) > 0


def test_get_test_specifications_fields(client, unused_test_specification_db):
    response = client.get(_TEST_SPECIFICATIONS_URL)
    assert response.status_code == HTTPStatus.OK
    ts = next(
        (t for t in response.json if t['id'] == unused_test_specification_db.id),
        None,
    )
    assert ts is not None
    assert 'id' in ts
    assert 'title' in ts
    assert 'preconditions' in ts
    assert 'test_description' in ts
    assert 'expected_behavior' in ts
    assert 'status' in ts
    assert 'created_by' in ts
    assert 'version' in ts
    assert 'used' in ts


def test_get_test_specifications_used_flag_false(client, unused_test_specification_db):
    response = client.get(
        _TEST_SPECIFICATIONS_URL,
        query_string={'field1': 'id', 'filter1': unused_test_specification_db.id},
    )
    assert response.status_code == HTTPStatus.OK
    assert len(response.json) == 1
    assert response.json[0]['used'] is False


def test_get_test_specifications_used_flag_true(client, used_test_specification_db):
    response = client.get(
        _TEST_SPECIFICATIONS_URL,
        query_string={'field1': 'id', 'filter1': used_test_specification_db.id},
    )
    assert response.status_code == HTTPStatus.OK
    assert len(response.json) == 1
    assert response.json[0]['used'] is True


def test_get_test_specifications_minimal_mode(client, unused_test_specification_db):
    response = client.get(
        _TEST_SPECIFICATIONS_URL,
        query_string={'mode': 'minimal'},
    )
    assert response.status_code == HTTPStatus.OK
    assert len(response.json) > 0
    for ts in response.json:
        assert set(ts.keys()) == {'id', 'title'}


# ------------------------------------------------------------------
# DELETE
# ------------------------------------------------------------------

def test_delete_missing_auth_fields(client, unused_test_specification_db):
    response = client.delete(
        _TEST_SPECIFICATIONS_URL,
        json={'id': unused_test_specification_db.id},
    )
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_delete_invalid_token(client, user_authentication, unused_test_specification_db):
    response = client.delete(
        _TEST_SPECIFICATIONS_URL,
        json={
            'id': unused_test_specification_db.id,
            'user-id': user_authentication.json['id'],
            'token': 'invalid-token',
        },
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED


def test_delete_guest_forbidden(client, guest_authentication, unused_test_specification_db):
    response = client.delete(
        _TEST_SPECIFICATIONS_URL,
        json={
            'id': unused_test_specification_db.id,
            'user-id': guest_authentication.json['id'],
            'token': guest_authentication.json['token'],
        },
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED


@pytest.mark.parametrize('missing_field', ['id', 'user-id', 'token'])
def test_delete_missing_mandatory_field(client, user_authentication, unused_test_specification_db, missing_field):
    data = {
        'id': unused_test_specification_db.id,
        'user-id': user_authentication.json['id'],
        'token': user_authentication.json['token'],
    }
    data.pop(missing_field)
    response = client.delete(_TEST_SPECIFICATIONS_URL, json=data)
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_delete_used_test_specification(client, user_authentication, used_test_specification_db):
    response = client.delete(
        _TEST_SPECIFICATIONS_URL,
        json={
            'id': used_test_specification_db.id,
            'user-id': user_authentication.json['id'],
            'token': user_authentication.json['token'],
        },
    )
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_delete_nonexistent_test_specification(client, user_authentication):
    from sqlalchemy.exc import NoResultFound
    non_existent_id = 99999
    with pytest.raises(NoResultFound):
        client.delete(
            _TEST_SPECIFICATIONS_URL,
            json={
                'id': non_existent_id,
                'user-id': user_authentication.json['id'],
                'token': user_authentication.json['token'],
            },
        )


def test_delete_ok(client, client_db, user_authentication, unused_test_specification_db):
    ts_id = unused_test_specification_db.id

    response = client.get(
        _TEST_SPECIFICATIONS_URL,
        query_string={'field1': 'id', 'filter1': ts_id},
    )
    assert response.status_code == HTTPStatus.OK
    assert len(response.json) == 1

    response = client.delete(
        _TEST_SPECIFICATIONS_URL,
        json={
            'id': ts_id,
            'user-id': user_authentication.json['id'],
            'token': user_authentication.json['token'],
        },
    )
    assert response.status_code == HTTPStatus.OK

    response = client.get(
        _TEST_SPECIFICATIONS_URL,
        query_string={'field1': 'id', 'filter1': ts_id},
    )
    assert response.status_code == HTTPStatus.OK
    assert len(response.json) == 0
