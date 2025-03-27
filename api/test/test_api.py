import os
import pytest
import sys

basilrootdir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
sys.path.insert(1, basilrootdir)

from api import api
from db.models.api import ApiModel

api.app.config['TESTING'] = True
api.app.config['DEBUG'] = True


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


def test_api_post(client, user_authentication):
    new_api = {'user-id': user_authentication.json['id'],
               'token': user_authentication.json['token'],
               'action': 'add',
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


def test_api_put(client, user_authentication):
    # Test GET
    response = client.get('/apis')
    assert response.status_code == 200
    assert isinstance(response.json['apis'], list)
    assert len(response.json['apis']) != 0

    api = response.json['apis'][0]
    tmp = {'user-id': user_authentication.json['id'],
           'token': user_authentication.json['token'],
           'api-id': api['id'],
           'api': 'modified_api',
           'category': 'modified_category',
           'default-view': 'view',
           'checksum': '',
           'library': 'modified_library',
           'library-version': '2',
           'raw-specification-url': 'modified_url',
           'tags': 'modified-tag',
           'implementation-file': 'modified-file',
           'implementation-file-from-row': '99',
           'implementation-file-to-row': '999',
           'last_coverage': 0
           }

    log_test('test_api_put', f'{api}')
    response = client.put('/apis', json=convert_keys_with_hash_for_request(tmp))
    assert response.status_code == 200

    # Test PUT effects and GET with filed and filter
    response = client.get(f'/apis?field1=id&filter1={tmp["api-id"]}')
    assert response.status_code == 200
    assert isinstance(response.json['apis'], list)
    assert len(response.json['apis']) == 1

    model_fields = get_model_editable_fields(ApiModel.__table__.columns.keys())
    model_fields = [x.replace('-', '_') for x in model_fields]
    tmp = convert_keys_without_hash_for_response(tmp)
    for mf in model_fields:
        if mf in tmp:
            assert str(response.json['apis'][0][mf]) == str(tmp[mf])


def test_api_delete(client, user_authentication):
    # Test GET
    response = client.get('/apis')
    assert response.status_code == 200
    assert isinstance(response.json['apis'], list)
    assert len(response.json['apis']) != 0

    # Test DELETE
    api = response.json['apis'][0]
    api['api-id'] = api['id']
    api['user-id'] = user_authentication.json['id']
    api['token'] = user_authentication.json['token']
    log_test('test_api_delete', f'{api}')
    response = client.delete('/apis', json=convert_keys_with_hash_for_request(api))
    assert response.status_code == 200

    # Test DELETE effects and GET with filed and filter
    response = client.get(f'/apis?field1=id&filter1={api["api-id"]}')
    assert response.status_code == 200
    assert isinstance(response.json['apis'], list)
    assert len(response.json['apis']) == 0