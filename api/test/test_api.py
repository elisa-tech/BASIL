import os
import pytest
import sys

basilrootdir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
sys.path.insert(1, basilrootdir)

from api import api
from db.models.api import ApiModel
from db.models.test_case import TestCaseModel, TestCaseHistoryModel
from db.models.test_specification import TestSpecificationModel, TestSpecificationHistoryModel
from db.models.test_specification_test_case import TestSpecificationTestCaseModel
from db.models.test_specification_test_case import TestSpecificationTestCaseHistoryModel
import db.models.init_db as init_db

# Exclude internal class from pytest
TestCaseModel.__test__ = False
TestCaseHistoryModel.__test__ = False
TestSpecificationModel.__test__ = False
TestSpecificationHistoryModel.__test__ = False
TestSpecificationTestCaseModel.__test__ = False
TestSpecificationTestCaseHistoryModel.__test__ = False

api.app.config['TESTING'] = True
api.app.config['DEBUG'] = True

init_db.initialization(db_name="test.db")


def log_test(_test, _log):
    f = open('test.log', 'a')
    f.write(f'* {_test}\n  > {_log}')
    f.close()


def get_model_editable_fields(_fields):
    not_editable = ['id', 'created_at', 'updated_at']
    tmp = [x for x in _fields if x not in not_editable]
    return tmp


def convert_keys_with_hash_for_request(_object):
    tmp = {}
    for k in _object.keys():
        tmp[k.replace('_', '-')] = _object[k]
    return tmp


def convert_keys_without_hash_for_response(_object):
    tmp = {}
    for k in _object.keys():
        tmp[k.replace('-', '_')] = _object[k]
    return tmp


def delete_db():
    currentdir = os.path.dirname(os.path.realpath(__file__))
    db_path = os.path.join(currentdir, 'db', 'test.db')
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def client():
    with api.app.test_client() as client:
        with api.app.app_context():
            pass
        yield client


def test_api_post(client):
    new_api = {'action': 'add',
               'api': 'test_api',
               'category': 'test_category',
               'library': 'test_library',
               'library-version': '1',
               'raw-specification-url': os.path.realpath(__file__),
               'tags': 'tag1, tag2',
               'implementation-file': '',
               'implementation-file-from-row': 0,
               'implementation-file-to-row': 1,
               }

    response = client.post('/apis', json=new_api)
    assert response.status_code == 200


def test_api_put(client):
    # Test GET
    response = client.get('/apis')
    assert response.status_code == 200
    assert isinstance(response.json, list)
    assert len(response.json) != 0

    # Test PUT
    api = response.json[0]
    tmp = {'api-id': api['id'],
           'api': 'modified_api',
           'category': 'modified_category',
           'library': 'modified_library',
           'library-version': '2',
           'raw-specification-url': 'modified_url',
           'tags': 'modified-tag',
           'implementation-file': 'modified-file',
           'implementation-file-from-row': '99',
           'implementation-file-to-row': '999',
           }

    log_test('test_api_put', f'{api}')
    response = client.put('/apis', json=convert_keys_with_hash_for_request(tmp))
    assert response.status_code == 200

    # Test PUT effects and GET with filed and filter
    response = client.get(f'/apis?field1=id&filter1={tmp["api-id"]}')
    assert response.status_code == 200
    assert isinstance(response.json, list)
    assert len(response.json) == 1

    model_fields = get_model_editable_fields(ApiModel.__table__.columns.keys())
    model_fields = [x.replace('-', '_') for x in model_fields]
    tmp = convert_keys_without_hash_for_response(tmp)
    for mf in model_fields:
        assert str(response.json[0][mf]) == str(tmp[mf])


def test_api_delete(client):
    # Test GET
    response = client.get('/apis')
    assert response.status_code == 200
    assert isinstance(response.json, list)
    assert len(response.json) != 0

    # Test DELETE
    api = response.json[0]
    api['api-id'] = api['id']
    log_test('test_api_delete', f'{api}')
    response = client.delete('/apis', json=convert_keys_with_hash_for_request(api))
    assert response.status_code == 200

    # Test DELETE effects and GET with filed and filter
    response = client.get(f'/apis?field1=id&filter1={api["api-id"]}')
    assert response.status_code == 200
    assert isinstance(response.json, list)
    assert len(response.json) == 0
    delete_db()
