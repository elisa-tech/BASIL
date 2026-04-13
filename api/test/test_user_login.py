import pytest
from http import HTTPStatus
from conftest import UT_USER_EMAIL, UT_USER_PASSWORD


_USER_LOGIN_URL = '/user/login'


def test_user_login_post_ok(client, ut_user_db):
    """ Nominal test for the registered user """
    user_data = {'email': UT_USER_EMAIL, 'password': UT_USER_PASSWORD}
    response = client.post(_USER_LOGIN_URL, json=user_data)
    assert response.status_code == HTTPStatus.OK


@pytest.mark.parametrize(('email', 'password'), (
    ('', ''),
    ('not_registered', 'not_registered')
))
def test_user_login_post_unauthorized(client, email, password):
    """ Nominal test for not registered users """
    user_data = {'email': email, 'password': password}
    response = client.post(_USER_LOGIN_URL, json=user_data)
    assert response.status_code == HTTPStatus.UNAUTHORIZED


def test_user_login_post_wrong_credentials(client):
    """ Nominal test with incorrect password """
    user_data = {'email': UT_USER_EMAIL, 'password': UT_USER_PASSWORD + '_wrong_pwd'}
    response = client.post(_USER_LOGIN_URL, json=user_data)
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_user_login_post_bad_request(client):
    """ Off-nominal test with incorrect payload """
    user_data = {'wrong_data': "no_email", 'password': "dummy_user"}
    response = client.post(_USER_LOGIN_URL, json=user_data)
    assert response.status_code == HTTPStatus.BAD_REQUEST
