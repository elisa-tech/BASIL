import pytest
from api import api
from db import db_orm
from db.models.db_base import Base
import db.models.init_db as init_db
from db.models.user import UserModel


_USER_LOGIN_URL = '/user/login'
_DB_NAME = 'test.db'
_UT_USER_NAME = 'ut_user_name'
_UT_USER_EMAIL = 'ut_user_email'
_UT_USER_PASSWORD = 'ut_user_password'
_UT_USER_ROLE = 'USER'

api.app.config['TESTING'] = True
api.app.config['DEBUG'] = True


@pytest.fixture
def client():
    with api.app.test_client() as client:
        yield client


@pytest.fixture(scope="module", autouse=True)
def test_client_db():
    init_db.initialization(db_name=_DB_NAME)
    dbi = db_orm.DbInterface(_DB_NAME)

    ut_test_user = UserModel(_UT_USER_NAME, _UT_USER_EMAIL, _UT_USER_PASSWORD, _UT_USER_ROLE)
    dbi.session.add(ut_test_user)
    dbi.session.commit()

    yield

    Base.metadata.drop_all(bind=dbi.engine)


def test_user_login_post_ok(client):
    """ Nominal test for the registered user """
    user_data = {'email': _UT_USER_EMAIL, 'password': _UT_USER_PASSWORD}
    response = client.post(_USER_LOGIN_URL, json=user_data)
    assert response.status_code == 200


@pytest.mark.parametrize(('email', 'password'), (
    ('', ''),
    ('not_registered', 'not_registered')
))
def test_user_login_post_unauthorized(client, email, password):
    """ Nominal test for not registered users """
    user_data = {'email': email, 'password': password}
    response = client.post(_USER_LOGIN_URL, json=user_data)
    assert response.status_code == 401


def test_user_login_post_wrong_credentials(client):
    """ Nominal test with incorrect password """
    user_data = {'email': _UT_USER_EMAIL, 'password': _UT_USER_PASSWORD + '_wrong_pwd'}
    response = client.post(_USER_LOGIN_URL, json=user_data)
    assert response.status_code == 400


def test_user_login_post_bad_request(client):
    """ Off-nominal test with incorrect payload """
    user_data = {'wrong_data': "no_email", 'password': "dummy_user"}
    response = client.post(_USER_LOGIN_URL, json=user_data)
    assert response.status_code == 400
