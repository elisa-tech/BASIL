import pytest
from http import HTTPStatus

from db.models.user import UserModel
from db.models.test_case import TestCaseModel
from db.models.api_test_case import ApiTestCaseModel
from db.models.api import ApiModel

from conftest import (
    UT_USER_EMAIL,
    AuthActions,
)

_TEST_CASES_URL = '/test-cases'

_UT_GUEST_NAME = 'ut_tc_guest_name'
_UT_GUEST_EMAIL = 'ut_tc_guest_email'
_UT_GUEST_PASSWORD = 'ut_tc_guest_password'


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
def unused_test_case_db(client_db, ut_user_db, utilities):
    user = client_db.session.query(UserModel).filter(
        UserModel.email == UT_USER_EMAIL).one()
    tc = TestCaseModel(
        'https://example.com/repo',
        'tests/test_example.py',
        f'Unused TC #{utilities.generate_random_hex_string8()}',
        'A test case not mapped anywhere',
        user,
    )
    client_db.session.add(tc)
    client_db.session.commit()
    yield tc


@pytest.fixture()
def used_test_case_db(client_db, ut_user_db, utilities):
    """Create a test case that is mapped to an API (i.e. in use)."""
    user = client_db.session.query(UserModel).filter(
        UserModel.email == UT_USER_EMAIL).one()

    tc = TestCaseModel(
        'https://example.com/repo',
        'tests/test_used.py',
        f'Used TC #{utilities.generate_random_hex_string8()}',
        'A test case mapped to an API',
        user,
    )
    api = ApiModel(
        f'ut_api_{utilities.generate_random_hex_string8()}',
        'ut_lib', 'v1', 'stub.md', 'ut_cat',
        utilities.generate_random_hex_string8(),
        'stub.impl', 0, 42, 'ut_tags', user,
    )
    client_db.session.add(tc)
    client_db.session.add(api)
    client_db.session.flush()

    mapping = ApiTestCaseModel(api, tc, 'section', 0, 0, user)
    client_db.session.add(mapping)
    client_db.session.commit()
    yield tc


# ------------------------------------------------------------------
# GET
# ------------------------------------------------------------------

def test_login(user_authentication):
    assert user_authentication.status_code == HTTPStatus.OK


def test_get_test_cases_ok(client, unused_test_case_db):
    response = client.get(_TEST_CASES_URL)
    assert response.status_code == HTTPStatus.OK
    assert isinstance(response.json, list)
    assert len(response.json) > 0


def test_get_test_cases_fields(client, unused_test_case_db):
    response = client.get(_TEST_CASES_URL)
    assert response.status_code == HTTPStatus.OK
    test_case = next(
        (tc for tc in response.json if tc['id'] == unused_test_case_db.id),
        None,
    )
    assert test_case is not None
    assert 'id' in test_case
    assert 'title' in test_case
    assert 'description' in test_case
    assert 'repository' in test_case
    assert 'relative_path' in test_case
    assert 'status' in test_case
    assert 'created_by' in test_case
    assert 'version' in test_case
    assert 'used' in test_case


def test_get_test_cases_used_flag_false(client, unused_test_case_db):
    response = client.get(
        _TEST_CASES_URL,
        query_string={'field1': 'id', 'filter1': unused_test_case_db.id},
    )
    assert response.status_code == HTTPStatus.OK
    assert len(response.json) == 1
    assert response.json[0]['used'] is False


def test_get_test_cases_used_flag_true(client, used_test_case_db):
    response = client.get(
        _TEST_CASES_URL,
        query_string={'field1': 'id', 'filter1': used_test_case_db.id},
    )
    assert response.status_code == HTTPStatus.OK
    assert len(response.json) == 1
    assert response.json[0]['used'] is True


def test_get_test_cases_minimal_mode(client, unused_test_case_db):
    response = client.get(
        _TEST_CASES_URL,
        query_string={'mode': 'minimal'},
    )
    assert response.status_code == HTTPStatus.OK
    assert len(response.json) > 0
    for tc in response.json:
        assert set(tc.keys()) == {'id', 'title'}


# ------------------------------------------------------------------
# DELETE
# ------------------------------------------------------------------

def test_delete_missing_auth_fields(client, unused_test_case_db):
    response = client.delete(
        _TEST_CASES_URL,
        json={'id': unused_test_case_db.id},
    )
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_delete_invalid_token(client, user_authentication, unused_test_case_db):
    response = client.delete(
        _TEST_CASES_URL,
        json={
            'id': unused_test_case_db.id,
            'user-id': user_authentication.json['id'],
            'token': 'invalid-token',
        },
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED


def test_delete_guest_forbidden(client, guest_authentication, unused_test_case_db):
    response = client.delete(
        _TEST_CASES_URL,
        json={
            'id': unused_test_case_db.id,
            'user-id': guest_authentication.json['id'],
            'token': guest_authentication.json['token'],
        },
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED


@pytest.mark.parametrize('missing_field', ['id', 'user-id', 'token'])
def test_delete_missing_mandatory_field(client, user_authentication, unused_test_case_db, missing_field):
    data = {
        'id': unused_test_case_db.id,
        'user-id': user_authentication.json['id'],
        'token': user_authentication.json['token'],
    }
    data.pop(missing_field)
    response = client.delete(_TEST_CASES_URL, json=data)
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_delete_used_test_case(client, user_authentication, used_test_case_db):
    response = client.delete(
        _TEST_CASES_URL,
        json={
            'id': used_test_case_db.id,
            'user-id': user_authentication.json['id'],
            'token': user_authentication.json['token'],
        },
    )
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_delete_nonexistent_test_case(client, user_authentication):
    from sqlalchemy.exc import NoResultFound
    non_existent_id = 99999
    with pytest.raises(NoResultFound):
        client.delete(
            _TEST_CASES_URL,
            json={
                'id': non_existent_id,
                'user-id': user_authentication.json['id'],
                'token': user_authentication.json['token'],
            },
        )


def test_delete_ok(client, client_db, user_authentication, unused_test_case_db):
    test_case_id = unused_test_case_db.id

    response = client.get(
        _TEST_CASES_URL,
        query_string={'field1': 'id', 'filter1': test_case_id},
    )
    assert response.status_code == HTTPStatus.OK
    assert len(response.json) == 1

    response = client.delete(
        _TEST_CASES_URL,
        json={
            'id': test_case_id,
            'user-id': user_authentication.json['id'],
            'token': user_authentication.json['token'],
        },
    )
    assert response.status_code == HTTPStatus.OK

    response = client.get(
        _TEST_CASES_URL,
        query_string={'field1': 'id', 'filter1': test_case_id},
    )
    assert response.status_code == HTTPStatus.OK
    assert len(response.json) == 0
