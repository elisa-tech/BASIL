import pytest
from api import api
from db import db_orm
from db.models.db_base import Base
import db.models.init_db as init_db
from db.models.user import UserModel

DB_NAME = 'test.db'

UT_USER_NAME = 'ut_user_name'
UT_USER_EMAIL = 'ut_user_email'
UT_USER_PASSWORD = 'ut_user_password'
UT_USER_ROLE = 'USER'


@pytest.fixture(scope="module")
def client():
    with api.app.test_client() as client:
        yield client


@pytest.fixture(scope="module", autouse=True)
def client_db():
    init_db.initialization(db_name=DB_NAME)

    yield

    dbi = db_orm.DbInterface(DB_NAME)
    Base.metadata.drop_all(bind=dbi.engine)


@pytest.fixture(scope="module")
def ut_user_db(client_db):
    dbi = db_orm.DbInterface(DB_NAME)

    # add user for unit testing
    ut_test_user = UserModel(UT_USER_NAME, UT_USER_EMAIL, UT_USER_PASSWORD, UT_USER_ROLE)
    dbi.session.add(ut_test_user)
    dbi.session.commit()


class AuthActions(object):
    def __init__(self, client):
        self._client = client

    def login(self, email=UT_USER_EMAIL, password=UT_USER_PASSWORD):
        return self._client.post(
            '/user/login',
            json={'email': email, 'password': password}
        )


@pytest.fixture(scope="module")
def user_authentication(client, ut_user_db):
    authentication = AuthActions(client)
    login_response = authentication.login()

    return login_response
