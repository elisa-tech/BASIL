import os
import pytest
import tempfile
from http import HTTPStatus

from db.models.user import UserModel
from db.models.api import ApiModel
from db.models.justification import JustificationModel
from db.models.api_justification import ApiJustificationModel

from conftest import UT_USER_EMAIL, UT_USER_NAME


_MAPPING_API_JUSTIFICATIONS_URL = '/mapping/api/justifications'

_UT_API_NAME = 'ut_api'
_UT_API_LIBRARY = 'ut_api_library'
_UT_API_LIBRARY_VERSION = 'v1.0.0'
_UT_API_CATEGORY = 'ut_api_category'
_UT_API_IMPLEMENTATION_FILE_FROM_ROW = 0
_UT_API_IMPLEMENTATION_FILE_TO_ROW = 42
_UT_API_TAGS = 'ut_api_tags'

_UT_API_SPEC_SECTION_NO_MAPPING = 'This section has no mapping.'
_UT_API_SPEC_SECTION_WITH_MAPPING = 'This section has mapping.'
_UT_API_SPEC_SECTION_TO_BE_MAPPED = 'This section is to be mapped.'
_UT_API_RAW_RESTRICTED_SPEC = 'BASIL UT: "Reader" user is not able to read this API.' \
                              f' Used for {_MAPPING_API_JUSTIFICATIONS_URL}.'
_UT_API_RAW_UNMAPPED_SPEC = f'BASIL UT: {_UT_API_SPEC_SECTION_NO_MAPPING} Used for {_MAPPING_API_JUSTIFICATIONS_URL}.'
_UT_API_RAW_MAPPED_SPEC = f'BASIL UT: {_UT_API_SPEC_SECTION_WITH_MAPPING} {_UT_API_SPEC_SECTION_TO_BE_MAPPED} ' \
                          f'Used for {_MAPPING_API_JUSTIFICATIONS_URL}.'


def _filter_sections_mapped_by_justifications(mapped_sections):
    return [section for section in mapped_sections if section['justifications']]


def _get_sections_mapped_by_justifications(client, api_id):
    response = client.get(_MAPPING_API_JUSTIFICATIONS_URL, query_string={'api-id': api_id})
    assert response.status_code == HTTPStatus.OK
    return _filter_sections_mapped_by_justifications(response.json['mapped'])


def _get_mapped_justification(mapped_section):
    relation_id = mapped_section['justifications'][0]['relation_id']
    justification = mapped_section['justifications'][0]['justification']
    return relation_id, justification


def _with_auth(user_authentication, mapping_data):
    return {
        'user-id': user_authentication.json['id'],
        'token': user_authentication.json['token'],
        **mapping_data,
    }


def _create_api_without_mappings(client_db, utilities):
    user = client_db.session.query(UserModel).filter(UserModel.email == UT_USER_EMAIL).one()
    ut_api = ApiModel(_UT_API_NAME + '#' + utilities.generate_random_hex_string8(),
                      _UT_API_LIBRARY, _UT_API_LIBRARY_VERSION, 'stub.md',
                      _UT_API_CATEGORY, utilities.generate_random_hex_string8(), 'stub.impl',
                      _UT_API_IMPLEMENTATION_FILE_FROM_ROW, _UT_API_IMPLEMENTATION_FILE_TO_ROW,
                      _UT_API_TAGS, user)
    client_db.session.add(ut_api)
    client_db.session.commit()
    return ut_api


@pytest.fixture()
def restricted_api_db(client_db, ut_user_db, ut_reader_user_db, utilities):
    """Create Api with read restriction for \"reader\"."""

    user = client_db.session.query(UserModel).filter(UserModel.email == UT_USER_EMAIL).one()

    raw_spec = tempfile.NamedTemporaryFile(mode="w", delete=False)
    raw_spec.write(_UT_API_RAW_RESTRICTED_SPEC)
    raw_spec.close()

    ut_api = ApiModel(_UT_API_NAME + '#' + utilities.generate_random_hex_string8(),
                      _UT_API_LIBRARY, _UT_API_LIBRARY_VERSION, raw_spec.name,
                      _UT_API_CATEGORY, utilities.generate_random_hex_string8(), raw_spec.name + 'impl',
                      _UT_API_IMPLEMENTATION_FILE_FROM_ROW, _UT_API_IMPLEMENTATION_FILE_TO_ROW,
                      _UT_API_TAGS, user)
    ut_api.read_denials = f"[{ut_reader_user_db.id}]"
    client_db.session.add(ut_api)
    client_db.session.commit()

    yield ut_api

    if os.path.isfile(raw_spec.name):
        os.remove(raw_spec.name)


@pytest.fixture()
def unmapped_api_db(client_db, ut_user_db, utilities):
    """Create Api with no mapped sections."""

    user = client_db.session.query(UserModel).filter(UserModel.email == UT_USER_EMAIL).one()

    raw_spec = tempfile.NamedTemporaryFile(mode="w", delete=False)
    raw_spec.write(_UT_API_RAW_UNMAPPED_SPEC)
    raw_spec.close()

    ut_api = ApiModel(_UT_API_NAME + '#' + utilities.generate_random_hex_string8(),
                      _UT_API_LIBRARY, _UT_API_LIBRARY_VERSION, raw_spec.name,
                      _UT_API_CATEGORY, utilities.generate_random_hex_string8(), raw_spec.name + 'impl',
                      _UT_API_IMPLEMENTATION_FILE_FROM_ROW, _UT_API_IMPLEMENTATION_FILE_TO_ROW,
                      _UT_API_TAGS, user)
    client_db.session.add(ut_api)
    client_db.session.commit()

    yield ut_api

    if os.path.isfile(raw_spec.name):
        os.remove(raw_spec.name)


@pytest.fixture()
def mapped_api_db(client_db, ut_user_db, utilities):
    """Create Api with one justification mapping."""

    user = client_db.session.query(UserModel).filter(UserModel.email == UT_USER_EMAIL).one()

    raw_spec = tempfile.NamedTemporaryFile(mode="w", delete=False)
    raw_spec.write(_UT_API_RAW_MAPPED_SPEC)
    raw_spec.close()

    ut_api = ApiModel(_UT_API_NAME + '#' + utilities.generate_random_hex_string8(),
                      _UT_API_LIBRARY, _UT_API_LIBRARY_VERSION, raw_spec.name,
                      _UT_API_CATEGORY, utilities.generate_random_hex_string8(), raw_spec.name + 'impl',
                      _UT_API_IMPLEMENTATION_FILE_FROM_ROW, _UT_API_IMPLEMENTATION_FILE_TO_ROW,
                      _UT_API_TAGS, user)
    ut_justification = JustificationModel(f'Justification #{utilities.generate_random_hex_string8()}', user)
    ut_api_justification_mapping = ApiJustificationModel(
        ut_api,
        ut_justification,
        _UT_API_SPEC_SECTION_WITH_MAPPING,
        _UT_API_RAW_MAPPED_SPEC.find(_UT_API_SPEC_SECTION_WITH_MAPPING),
        0,
        user,
    )

    client_db.session.add(ut_api)
    client_db.session.add(ut_justification)
    client_db.session.add(ut_api_justification_mapping)
    client_db.session.commit()

    yield ut_api

    if os.path.isfile(raw_spec.name):
        os.remove(raw_spec.name)


@pytest.fixture()
def justification_db(client_db, ut_user_db, utilities):
    """Create a standalone justification (not yet mapped to the test API)."""

    user = client_db.session.query(UserModel).filter(UserModel.email == UT_USER_EMAIL).one()

    ut_justification = JustificationModel(f'Justification #{utilities.generate_random_hex_string8()}', user)

    client_db.session.add(ut_justification)
    client_db.session.commit()

    yield ut_justification


def test_login(user_authentication):
    assert user_authentication.status_code == HTTPStatus.OK


# --- GET ---


def test_get_unauthorized_ok(client, unmapped_api_db):
    response = client.get(_MAPPING_API_JUSTIFICATIONS_URL, query_string={'api-id': unmapped_api_db.id})
    assert response.status_code == HTTPStatus.OK
    assert 'mapped' in response.json
    assert 'unmapped' in response.json


def test_get_unauthorized_fail(client, restricted_api_db):
    response = client.get(_MAPPING_API_JUSTIFICATIONS_URL, query_string={'api-id': restricted_api_db.id})
    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert 'mapped' not in response.json
    assert 'unmapped' not in response.json


def test_get_authorized_restricted_fail(client, reader_authentication, restricted_api_db):
    get_query = {
        'user-id': reader_authentication.json['id'],
        'token': reader_authentication.json['token'],
        'api-id': restricted_api_db.id
    }
    response = client.get(_MAPPING_API_JUSTIFICATIONS_URL, query_string=get_query)
    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert 'mapped' not in response.json
    assert 'unmapped' not in response.json


def test_get_authorized_restricted_ok(client, user_authentication, restricted_api_db):
    get_query = {
        'user-id': user_authentication.json['id'],
        'token': user_authentication.json['token'],
        'api-id': restricted_api_db.id
    }
    response = client.get(_MAPPING_API_JUSTIFICATIONS_URL, query_string=get_query)
    assert response.status_code == HTTPStatus.OK
    assert 'mapped' in response.json
    assert 'unmapped' in response.json


@pytest.mark.usefixtures("unmapped_api_db")
def test_get_incorrect_request(client, user_authentication):
    get_query = {
        'user-id': user_authentication.json['id'],
        'token': user_authentication.json['token']
    }
    response = client.get(_MAPPING_API_JUSTIFICATIONS_URL, query_string=get_query)
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert 'mapped' not in response.json
    assert 'unmapped' not in response.json


@pytest.mark.usefixtures("unmapped_api_db")
def test_get_missing_api(client_db, client, user_authentication):
    non_existent_id = 42000
    supposed_api = client_db.session.query(ApiModel).get(non_existent_id)
    assert supposed_api is None

    get_query = {
        'user-id': user_authentication.json['id'],
        'token': user_authentication.json['token'],
        'api-id': non_existent_id
    }
    response = client.get(_MAPPING_API_JUSTIFICATIONS_URL, query_string=get_query)
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert 'mapped' not in response.json
    assert 'unmapped' not in response.json


def test_get_mapped(client, mapped_api_db):
    response = client.get(_MAPPING_API_JUSTIFICATIONS_URL, query_string={'api-id': mapped_api_db.id})
    assert response.status_code == HTTPStatus.OK
    mapped_sections = _filter_sections_mapped_by_justifications(response.json['mapped'])
    assert len(mapped_sections) == 1
    assert mapped_sections[0]['section'] == _UT_API_SPEC_SECTION_WITH_MAPPING


# --- POST ---


def test_post_unauthorized(client, unmapped_api_db, utilities):
    mapped_sections = _get_sections_mapped_by_justifications(client, unmapped_api_db.id)
    assert len(mapped_sections) == 0

    mapping_data = {
        'api-id': unmapped_api_db.id,
        'section': _UT_API_SPEC_SECTION_NO_MAPPING,
        'offset': _UT_API_RAW_UNMAPPED_SPEC.find(_UT_API_SPEC_SECTION_NO_MAPPING),
        'coverage': 0,
        'justification': {
            'description': f'Justification #{utilities.generate_random_hex_string8()}',
        }
    }
    response = client.post(_MAPPING_API_JUSTIFICATIONS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.UNAUTHORIZED

    mapped_sections = _get_sections_mapped_by_justifications(client, unmapped_api_db.id)
    assert len(mapped_sections) == 0


def test_post_restricted_write(client, reader_authentication, unmapped_api_db, utilities):
    mapped_sections = _get_sections_mapped_by_justifications(client, unmapped_api_db.id)
    assert len(mapped_sections) == 0

    mapping_data = _with_auth(reader_authentication, {
        'api-id': unmapped_api_db.id,
        'section': _UT_API_SPEC_SECTION_NO_MAPPING,
        'offset': _UT_API_RAW_UNMAPPED_SPEC.find(_UT_API_SPEC_SECTION_NO_MAPPING),
        'coverage': 0,
        'justification': {
            'description': f'Justification #{utilities.generate_random_hex_string8()}',
        }
    })
    response = client.post(_MAPPING_API_JUSTIFICATIONS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.UNAUTHORIZED

    mapped_sections = _get_sections_mapped_by_justifications(client, unmapped_api_db.id)
    assert len(mapped_sections) == 0


@pytest.mark.parametrize('mandatory_field', ['api-id', 'section', 'offset', 'coverage', 'justification'])
def test_post_incomplete_request(client, user_authentication, unmapped_api_db, utilities, mandatory_field):
    mapped_sections = _get_sections_mapped_by_justifications(client, unmapped_api_db.id)
    assert len(mapped_sections) == 0

    mapping_data = _with_auth(user_authentication, {
        'api-id': unmapped_api_db.id,
        'section': _UT_API_SPEC_SECTION_NO_MAPPING,
        'offset': _UT_API_RAW_UNMAPPED_SPEC.find(_UT_API_SPEC_SECTION_NO_MAPPING),
        'coverage': 0,
        'justification': {
            'description': f'Justification #{utilities.generate_random_hex_string8()}',
        }
    })
    mapping_data.pop(mandatory_field)
    response = client.post(_MAPPING_API_JUSTIFICATIONS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.BAD_REQUEST

    mapped_sections = _get_sections_mapped_by_justifications(client, unmapped_api_db.id)
    assert len(mapped_sections) == 0


@pytest.mark.usefixtures("unmapped_api_db")
def test_post_missing_api(client_db, client, user_authentication, utilities):
    non_existent_id = 42000
    supposed_api = client_db.session.query(ApiModel).get(non_existent_id)
    assert supposed_api is None

    mapping_data = _with_auth(user_authentication, {
        'api-id': non_existent_id,
        'section': _UT_API_SPEC_SECTION_NO_MAPPING,
        'offset': _UT_API_RAW_UNMAPPED_SPEC.find(_UT_API_SPEC_SECTION_NO_MAPPING),
        'coverage': 0,
        'justification': {
            'description': f'Justification #{utilities.generate_random_hex_string8()}',
        }
    })
    response = client.post(_MAPPING_API_JUSTIFICATIONS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_post_missing_justification(client_db, client, user_authentication, unmapped_api_db):
    non_existent_id = 42000
    supposed_j = client_db.session.query(JustificationModel).get(non_existent_id)
    assert supposed_j is None

    mapped_sections = _get_sections_mapped_by_justifications(client, unmapped_api_db.id)
    assert len(mapped_sections) == 0

    mapping_data = _with_auth(user_authentication, {
        'api-id': unmapped_api_db.id,
        'section': _UT_API_SPEC_SECTION_NO_MAPPING,
        'offset': _UT_API_RAW_UNMAPPED_SPEC.find(_UT_API_SPEC_SECTION_NO_MAPPING),
        'coverage': 0,
        'justification': {
            'id': non_existent_id
        }
    })
    response = client.post(_MAPPING_API_JUSTIFICATIONS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.NOT_FOUND

    mapped_sections = _get_sections_mapped_by_justifications(client, unmapped_api_db.id)
    assert len(mapped_sections) == 0


def test_post_existing_justification_ok(client, user_authentication, unmapped_api_db, justification_db):
    mapped_sections = _get_sections_mapped_by_justifications(client, unmapped_api_db.id)
    assert len(mapped_sections) == 0

    mapping_data = _with_auth(user_authentication, {
        'api-id': unmapped_api_db.id,
        'section': _UT_API_SPEC_SECTION_NO_MAPPING,
        'offset': _UT_API_RAW_UNMAPPED_SPEC.find(_UT_API_SPEC_SECTION_NO_MAPPING),
        'coverage': 0,
        'justification': {
            'id': justification_db.id
        }
    })
    response = client.post(_MAPPING_API_JUSTIFICATIONS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.CREATED

    mapped_sections = _get_sections_mapped_by_justifications(client, unmapped_api_db.id)
    assert len(mapped_sections) == 1
    assert mapped_sections[0]['section'] == _UT_API_SPEC_SECTION_NO_MAPPING
    assert mapped_sections[0]['offset'] == _UT_API_RAW_UNMAPPED_SPEC.find(_UT_API_SPEC_SECTION_NO_MAPPING)
    mapped_justifications = mapped_sections[0]['justifications']
    assert len(mapped_justifications) == 1
    assert mapped_justifications[0]['justification']['description'] == justification_db.description
    assert mapped_justifications[0]['created_by'] == UT_USER_NAME


def test_post_existing_justification_conflict(client, user_authentication, mapped_api_db):
    api_id = mapped_api_db.id
    mapped_sections = _get_sections_mapped_by_justifications(client, api_id)
    assert len(mapped_sections) == 1
    assert mapped_sections[0]['section'] == _UT_API_SPEC_SECTION_WITH_MAPPING

    _, justification = _get_mapped_justification(mapped_sections[0])
    mapping_data = _with_auth(user_authentication, {
        'api-id': api_id,
        'section': _UT_API_SPEC_SECTION_WITH_MAPPING,
        'offset': _UT_API_RAW_MAPPED_SPEC.find(_UT_API_SPEC_SECTION_WITH_MAPPING),
        'coverage': 0,
        'justification': {
            'id': justification['id']
        }
    })
    response = client.post(_MAPPING_API_JUSTIFICATIONS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.CONFLICT

    mapped_sections = _get_sections_mapped_by_justifications(client, api_id)
    assert len(mapped_sections) == 1
    assert mapped_sections[0]['section'] == _UT_API_SPEC_SECTION_WITH_MAPPING
    assert len(mapped_sections[0]['justifications']) == 1


def test_post_new_justification_ok(client, user_authentication, unmapped_api_db, utilities):
    api_id = unmapped_api_db.id
    description = f'Justification #{utilities.generate_random_hex_string8()}'

    mapped_sections = _get_sections_mapped_by_justifications(client, api_id)
    assert len(mapped_sections) == 0

    mapping_data = _with_auth(user_authentication, {
        'api-id': api_id,
        'section': _UT_API_SPEC_SECTION_NO_MAPPING,
        'offset': _UT_API_RAW_UNMAPPED_SPEC.find(_UT_API_SPEC_SECTION_NO_MAPPING),
        'coverage': 0,
        'justification': {
            'description': description,
        }
    })
    response = client.post(_MAPPING_API_JUSTIFICATIONS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.CREATED

    mapped_sections = _get_sections_mapped_by_justifications(client, api_id)
    assert len(mapped_sections) == 1
    assert mapped_sections[0]['section'] == _UT_API_SPEC_SECTION_NO_MAPPING
    mapped_justifications = mapped_sections[0]['justifications']
    assert len(mapped_justifications) == 1
    assert mapped_justifications[0]['justification']['description'] == description
    assert mapped_justifications[0]['created_by'] == UT_USER_NAME


def test_post_new_justification_conflict(client, user_authentication, mapped_api_db):
    api_id = mapped_api_db.id
    mapped_sections = _get_sections_mapped_by_justifications(client, api_id)
    assert len(mapped_sections) == 1

    _, justification = _get_mapped_justification(mapped_sections[0])
    mapping_data = _with_auth(user_authentication, {
        'api-id': api_id,
        'section': _UT_API_SPEC_SECTION_TO_BE_MAPPED,
        'offset': _UT_API_RAW_MAPPED_SPEC.find(_UT_API_SPEC_SECTION_TO_BE_MAPPED),
        'coverage': 0,
        'justification': {
            'description': justification['description'],
        }
    })
    response = client.post(_MAPPING_API_JUSTIFICATIONS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.CONFLICT

    mapped_sections = _get_sections_mapped_by_justifications(client, api_id)
    assert len(mapped_sections) == 1
    assert len(mapped_sections[0]['justifications']) == 1


# --- PUT ---


def test_put_unauthorized(client, mapped_api_db):
    mapped_sections = _get_sections_mapped_by_justifications(client, mapped_api_db.id)
    assert len(mapped_sections) == 1

    relation_id, justification = _get_mapped_justification(mapped_sections[0])
    justification = {k.replace("_", "-"): v for k, v in justification.items()}
    mapping_data = {
        'relation-id': relation_id,
        'api-id': mapped_api_db.id,
        'section': _UT_API_SPEC_SECTION_TO_BE_MAPPED,
        'offset': _UT_API_RAW_MAPPED_SPEC.find(_UT_API_SPEC_SECTION_TO_BE_MAPPED),
        'coverage': 0,
        'justification': justification
    }
    response = client.put(_MAPPING_API_JUSTIFICATIONS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.UNAUTHORIZED

    mapped_sections = _get_sections_mapped_by_justifications(client, mapped_api_db.id)
    assert len(mapped_sections) == 1
    assert mapped_sections[0]['section'] == _UT_API_SPEC_SECTION_WITH_MAPPING


def test_put_restricted_write(client, reader_authentication, mapped_api_db):
    mapped_sections = _get_sections_mapped_by_justifications(client, mapped_api_db.id)
    relation_id, justification = _get_mapped_justification(mapped_sections[0])
    justification = {k.replace("_", "-"): v for k, v in justification.items()}
    mapping_data = _with_auth(reader_authentication, {
        'relation-id': relation_id,
        'api-id': mapped_api_db.id,
        'section': _UT_API_SPEC_SECTION_TO_BE_MAPPED,
        'offset': _UT_API_RAW_MAPPED_SPEC.find(_UT_API_SPEC_SECTION_TO_BE_MAPPED),
        'coverage': 0,
        'justification': justification
    })
    response = client.put(_MAPPING_API_JUSTIFICATIONS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.UNAUTHORIZED

    mapped_sections = _get_sections_mapped_by_justifications(client, mapped_api_db.id)
    assert mapped_sections[0]['section'] == _UT_API_SPEC_SECTION_WITH_MAPPING


@pytest.mark.parametrize(
    "mandatory_field",
    ["api-id", "section", "offset", "coverage", "justification", "relation-id"],
)
def test_put_incomplete_request(client, user_authentication, mapped_api_db, mandatory_field):
    mapped_sections = _get_sections_mapped_by_justifications(client, mapped_api_db.id)
    relation_id, justification = _get_mapped_justification(mapped_sections[0])
    justification = {k.replace("_", "-"): v for k, v in justification.items()}
    mapping_data = _with_auth(user_authentication, {
        'relation-id': relation_id,
        'api-id': mapped_api_db.id,
        'section': _UT_API_SPEC_SECTION_TO_BE_MAPPED,
        'offset': _UT_API_RAW_MAPPED_SPEC.find(_UT_API_SPEC_SECTION_TO_BE_MAPPED),
        'coverage': 0,
        'justification': justification
    })
    mapping_data.pop(mandatory_field)
    response = client.put(_MAPPING_API_JUSTIFICATIONS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.BAD_REQUEST

    mapped_sections = _get_sections_mapped_by_justifications(client, mapped_api_db.id)
    assert mapped_sections[0]['section'] == _UT_API_SPEC_SECTION_WITH_MAPPING


def test_put_missing_relation(client_db, client, user_authentication, mapped_api_db):
    non_existent_id = 42000
    supposed_mapping = client_db.session.query(ApiJustificationModel).get(non_existent_id)
    assert supposed_mapping is None

    mapped_sections = _get_sections_mapped_by_justifications(client, mapped_api_db.id)
    _, justification = _get_mapped_justification(mapped_sections[0])
    justification = {k.replace("_", "-"): v for k, v in justification.items()}
    mapping_data = _with_auth(user_authentication, {
        'relation-id': non_existent_id,
        'api-id': mapped_api_db.id,
        'section': _UT_API_SPEC_SECTION_TO_BE_MAPPED,
        'offset': _UT_API_RAW_MAPPED_SPEC.find(_UT_API_SPEC_SECTION_TO_BE_MAPPED),
        'coverage': 0,
        'justification': justification
    })
    response = client.put(_MAPPING_API_JUSTIFICATIONS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.NOT_FOUND

    mapped_sections = _get_sections_mapped_by_justifications(client, mapped_api_db.id)
    assert mapped_sections[0]['section'] == _UT_API_SPEC_SECTION_WITH_MAPPING


def test_put_update_mapping_ok(client, user_authentication, mapped_api_db):
    api_id = mapped_api_db.id
    mapped_sections = _get_sections_mapped_by_justifications(client, api_id)
    relation_id, justification = _get_mapped_justification(mapped_sections[0])
    justification = {k.replace("_", "-"): v for k, v in justification.items()}

    mapping_data = _with_auth(user_authentication, {
        'relation-id': relation_id,
        'api-id': api_id,
        'section': _UT_API_SPEC_SECTION_TO_BE_MAPPED,
        'offset': _UT_API_RAW_MAPPED_SPEC.find(_UT_API_SPEC_SECTION_TO_BE_MAPPED),
        'coverage': 0,
        'justification': justification
    })
    response = client.put(_MAPPING_API_JUSTIFICATIONS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.OK

    mapped_sections = _get_sections_mapped_by_justifications(client, api_id)
    assert len(mapped_sections) == 1
    assert mapped_sections[0]['section'] == _UT_API_SPEC_SECTION_TO_BE_MAPPED
    assert mapped_sections[0]['offset'] == _UT_API_RAW_MAPPED_SPEC.find(_UT_API_SPEC_SECTION_TO_BE_MAPPED)
    assert len(mapped_sections[0]['justifications']) == 1


def test_put_update_justification_description(client, user_authentication, mapped_api_db, utilities):
    api_id = mapped_api_db.id
    mapped_sections = _get_sections_mapped_by_justifications(client, api_id)
    relation_id, justification = _get_mapped_justification(mapped_sections[0])
    new_description = f'Updated justification #{utilities.generate_random_hex_string8()}'
    justification['description'] = new_description
    justification = {k.replace("_", "-"): v for k, v in justification.items()}

    mapping_data = _with_auth(user_authentication, {
        'relation-id': relation_id,
        'api-id': api_id,
        'section': _UT_API_SPEC_SECTION_WITH_MAPPING,
        'offset': _UT_API_RAW_MAPPED_SPEC.find(_UT_API_SPEC_SECTION_WITH_MAPPING),
        'coverage': 0,
        'justification': justification
    })
    response = client.put(_MAPPING_API_JUSTIFICATIONS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.OK

    mapped_sections = _get_sections_mapped_by_justifications(client, api_id)
    assert mapped_sections[0]['justifications'][0]['justification']['description'] == new_description


# --- DELETE ---


def test_delete_unauthorized(client, mapped_api_db):
    mapped_sections = _get_sections_mapped_by_justifications(client, mapped_api_db.id)
    relation_id, _ = _get_mapped_justification(mapped_sections[0])
    mapping_data = {
        'relation-id': relation_id,
        'api-id': mapped_api_db.id
    }
    response = client.delete(_MAPPING_API_JUSTIFICATIONS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.UNAUTHORIZED

    mapped_sections = _get_sections_mapped_by_justifications(client, mapped_api_db.id)
    assert len(mapped_sections) == 1


def test_delete_wrong_mapping(client_db, client, user_authentication, mapped_api_db, restricted_api_db, utilities):
    mapped_sections = _get_sections_mapped_by_justifications(client, mapped_api_db.id)
    relation_id, _ = _get_mapped_justification(mapped_sections[0])

    mapping_data = {
        'relation-id': relation_id,
        'api-id': 0
    }
    response = client.delete(_MAPPING_API_JUSTIFICATIONS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.NOT_FOUND

    mapped_sections = _get_sections_mapped_by_justifications(client, mapped_api_db.id)
    assert len(mapped_sections) == 1

    mapping_data = {
        'relation-id': relation_id,
        'api-id': restricted_api_db.id,
    }
    response = client.delete(_MAPPING_API_JUSTIFICATIONS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.UNAUTHORIZED

    mapped_sections = _get_sections_mapped_by_justifications(client, mapped_api_db.id)
    assert len(mapped_sections) == 1

    other_api = _create_api_without_mappings(client_db, utilities)
    mapping_data = _with_auth(user_authentication, {
        'relation-id': relation_id,
        'api-id': other_api.id
    })
    response = client.delete(_MAPPING_API_JUSTIFICATIONS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.PRECONDITION_FAILED

    mapped_sections = _get_sections_mapped_by_justifications(client, mapped_api_db.id)
    assert len(mapped_sections) == 1


def test_delete_restricted_write(client, reader_authentication, mapped_api_db):
    mapped_sections = _get_sections_mapped_by_justifications(client, mapped_api_db.id)
    relation_id, _ = _get_mapped_justification(mapped_sections[0])
    mapping_data = _with_auth(reader_authentication, {
        'relation-id': relation_id,
        'api-id': mapped_api_db.id
    })
    response = client.delete(_MAPPING_API_JUSTIFICATIONS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.UNAUTHORIZED

    mapped_sections = _get_sections_mapped_by_justifications(client, mapped_api_db.id)
    assert len(mapped_sections) == 1


@pytest.mark.parametrize('mandatory_field', ['api-id', 'relation-id'])
def test_delete_incomplete_request(client, user_authentication, mapped_api_db, mandatory_field):
    mapped_sections = _get_sections_mapped_by_justifications(client, mapped_api_db.id)
    relation_id, _ = _get_mapped_justification(mapped_sections[0])
    mapping_data = _with_auth(user_authentication, {
        'relation-id': relation_id,
        'api-id': mapped_api_db.id
    })
    mapping_data.pop(mandatory_field)
    response = client.delete(_MAPPING_API_JUSTIFICATIONS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.BAD_REQUEST

    mapped_sections = _get_sections_mapped_by_justifications(client, mapped_api_db.id)
    assert len(mapped_sections) == 1


def test_delete_missing_api(client_db, client, user_authentication, mapped_api_db):
    non_existent_id = 42000
    supposed_api = client_db.session.query(ApiModel).get(non_existent_id)
    assert supposed_api is None

    mapped_sections = _get_sections_mapped_by_justifications(client, mapped_api_db.id)
    relation_id, _ = _get_mapped_justification(mapped_sections[0])
    mapping_data = _with_auth(user_authentication, {
        'relation-id': relation_id,
        'api-id': non_existent_id
    })
    response = client.delete(_MAPPING_API_JUSTIFICATIONS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_delete_missing_relation(client_db, client, user_authentication, mapped_api_db):
    non_existent_id = 42000
    supposed_mapping = client_db.session.query(ApiJustificationModel).get(non_existent_id)
    assert supposed_mapping is None

    mapping_data = _with_auth(user_authentication, {
        'relation-id': non_existent_id,
        'api-id': mapped_api_db.id
    })
    response = client.delete(_MAPPING_API_JUSTIFICATIONS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.PRECONDITION_FAILED

    mapped_sections = _get_sections_mapped_by_justifications(client, mapped_api_db.id)
    assert len(mapped_sections) == 1


def test_delete_ok(client, user_authentication, mapped_api_db):
    api_id = mapped_api_db.id
    mapped_sections = _get_sections_mapped_by_justifications(client, api_id)
    relation_id, _ = _get_mapped_justification(mapped_sections[0])
    mapping_data = _with_auth(user_authentication, {
        'relation-id': relation_id,
        'api-id': api_id
    })
    response = client.delete(_MAPPING_API_JUSTIFICATIONS_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.OK

    mapped_sections = _get_sections_mapped_by_justifications(client, api_id)
    assert len(mapped_sections) == 0
