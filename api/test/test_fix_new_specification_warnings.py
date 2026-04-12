import os
import tempfile
from http import HTTPStatus

import pytest

from conftest import UT_USER_EMAIL
from db.models.api import ApiModel
from db.models.api_document import ApiDocumentModel
from db.models.api_justification import ApiJustificationModel
from db.models.api_sw_requirement import ApiSwRequirementModel
from db.models.api_test_case import ApiTestCaseModel
from db.models.api_test_specification import ApiTestSpecificationModel
from db.models.document import DocumentModel
from db.models.justification import JustificationModel
from db.models.sw_requirement import SwRequirementModel
from db.models.test_case import TestCaseModel
from db.models.test_specification import TestSpecificationModel
from db.models.user import UserModel

_FIX_WARNINGS_URL = '/apis/fix-specification-warnings'

_UT_API_NAME = 'ut_fix_warnings_api'
_UT_API_LIBRARY = 'ut_fix_warnings_library'
_UT_API_LIBRARY_VERSION = 'v1.0.0'
_UT_API_CATEGORY = 'ut_fix_warnings_category'

_SECTION_A = 'SectionAlpha'
_SECTION_B = 'SectionBeta'
_SECTION_C = 'SectionGamma'
_SECTION_D = 'SectionDelta'
_SECTION_E = 'SectionEpsilon'

_ORIGINAL_SPEC = f'HEADER {_SECTION_A} {_SECTION_B} {_SECTION_C} {_SECTION_D} {_SECTION_E} FOOTER'
_SHIFTED_SPEC = f'NEW_HEADER {_SECTION_A} {_SECTION_B} {_SECTION_C} {_SECTION_D} {_SECTION_E} FOOTER'


def _write_spec_file(content):
    spec = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.md')
    spec.write(content)
    spec.close()
    return spec.name


def _create_api(dbi, user, spec_path, utilities):
    api = ApiModel(
        _UT_API_NAME + '#' + utilities.generate_random_hex_string8(),
        _UT_API_LIBRARY, _UT_API_LIBRARY_VERSION, spec_path,
        _UT_API_CATEGORY, utilities.generate_random_hex_string8(),
        'stub.impl', 0, 42, 'tag', user,
    )
    dbi.session.add(api)
    dbi.session.commit()
    return api


def _add_mapping(dbi, model_cls, api, work_item, section, spec_content, user):
    mapping = model_cls(api, work_item, section, spec_content.index(section), 0, user)
    dbi.session.add(mapping)
    dbi.session.commit()
    return mapping


@pytest.fixture()
def api_with_all_mappings(client_db, ut_user_db, utilities):
    user = client_db.session.query(UserModel).filter(UserModel.email == UT_USER_EMAIL).one()

    spec_path = _write_spec_file(_ORIGINAL_SPEC)
    api = _create_api(client_db, user, spec_path, utilities)

    sr = SwRequirementModel(f'SR #{utilities.generate_random_hex_string8()}', 'desc', user)
    client_db.session.add(sr)
    client_db.session.commit()
    sr_map = _add_mapping(client_db, ApiSwRequirementModel, api, sr, _SECTION_A, _ORIGINAL_SPEC, user)

    ts = TestSpecificationModel(f'TS #{utilities.generate_random_hex_string8()}', 'pre', 'desc', 'exp', user)
    client_db.session.add(ts)
    client_db.session.commit()
    ts_map = _add_mapping(client_db, ApiTestSpecificationModel, api, ts, _SECTION_B, _ORIGINAL_SPEC, user)

    tc = TestCaseModel('repo', 'path', f'TC #{utilities.generate_random_hex_string8()}', 'desc', user)
    client_db.session.add(tc)
    client_db.session.commit()
    tc_map = _add_mapping(client_db, ApiTestCaseModel, api, tc, _SECTION_C, _ORIGINAL_SPEC, user)

    j = JustificationModel(f'Just #{utilities.generate_random_hex_string8()}', user)
    client_db.session.add(j)
    client_db.session.commit()
    j_map = _add_mapping(client_db, ApiJustificationModel, api, j, _SECTION_D, _ORIGINAL_SPEC, user)

    doc = DocumentModel(
        f'Doc #{utilities.generate_random_hex_string8()}', 'desc',
        'other', 'DESCRIBES', 'http://example.com', 'sec', 0, 1, user,
    )
    client_db.session.add(doc)
    client_db.session.commit()
    doc_map = _add_mapping(client_db, ApiDocumentModel, api, doc, _SECTION_E, _ORIGINAL_SPEC, user)

    yield {
        'api': api,
        'spec_path': spec_path,
        'sr_map': sr_map,
        'ts_map': ts_map,
        'tc_map': tc_map,
        'j_map': j_map,
        'doc_map': doc_map,
    }

    if os.path.isfile(spec_path):
        os.remove(spec_path)


def _shift_spec(fixture):
    """Overwrite the spec file with a shifted version so offsets change."""
    with open(fixture['spec_path'], 'w') as f:
        f.write(_SHIFTED_SPEC)


def _expected_new_offset(section):
    return _SHIFTED_SPEC.index(section)


def _expected_old_offset(section):
    return _ORIGINAL_SPEC.index(section)


# --- Bad-request / not-found tests -----------------------------------------------

def test_missing_id_returns_bad_request(client, user_authentication):
    response = client.get(_FIX_WARNINGS_URL)
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_nonexistent_api_returns_not_found(client, user_authentication):
    response = client.get(_FIX_WARNINGS_URL, query_string={'id': 999999})
    assert response.status_code == HTTPStatus.NOT_FOUND


# --- Fix warnings updates offsets -------------------------------------------------

def test_fix_warnings_returns_ok(client, user_authentication, api_with_all_mappings):
    fixture = api_with_all_mappings
    _shift_spec(fixture)

    response = client.get(_FIX_WARNINGS_URL, query_string={'id': fixture['api'].id})
    assert response.status_code == HTTPStatus.OK
    assert response.get_json() is True


def test_fix_warnings_updates_sw_requirement_offset(client, client_db, user_authentication, api_with_all_mappings):
    fixture = api_with_all_mappings
    _shift_spec(fixture)

    client.get(_FIX_WARNINGS_URL, query_string={'id': fixture['api'].id})

    client_db.session.expire(fixture['sr_map'])
    assert fixture['sr_map'].offset == _expected_new_offset(_SECTION_A)


def test_fix_warnings_updates_test_specification_offset(client, client_db, user_authentication, api_with_all_mappings):
    fixture = api_with_all_mappings
    _shift_spec(fixture)

    client.get(_FIX_WARNINGS_URL, query_string={'id': fixture['api'].id})

    client_db.session.expire(fixture['ts_map'])
    assert fixture['ts_map'].offset == _expected_new_offset(_SECTION_B)


def test_fix_warnings_updates_test_case_offset(client, client_db, user_authentication, api_with_all_mappings):
    fixture = api_with_all_mappings
    _shift_spec(fixture)

    client.get(_FIX_WARNINGS_URL, query_string={'id': fixture['api'].id})

    client_db.session.expire(fixture['tc_map'])
    assert fixture['tc_map'].offset == _expected_new_offset(_SECTION_C)


def test_fix_warnings_updates_justification_offset(client, client_db, user_authentication, api_with_all_mappings):
    fixture = api_with_all_mappings
    _shift_spec(fixture)

    client.get(_FIX_WARNINGS_URL, query_string={'id': fixture['api'].id})

    client_db.session.expire(fixture['j_map'])
    assert fixture['j_map'].offset == _expected_new_offset(_SECTION_D)


def test_fix_warnings_updates_document_offset(client, client_db, user_authentication, api_with_all_mappings):
    fixture = api_with_all_mappings
    _shift_spec(fixture)

    client.get(_FIX_WARNINGS_URL, query_string={'id': fixture['api'].id})

    client_db.session.expire(fixture['doc_map'])
    assert fixture['doc_map'].offset == _expected_new_offset(_SECTION_E)


# --- No warnings: offsets remain unchanged when spec is unmodified ----------------

def test_no_warnings_offsets_unchanged(client, client_db, user_authentication, api_with_all_mappings):
    fixture = api_with_all_mappings

    response = client.get(_FIX_WARNINGS_URL, query_string={'id': fixture['api'].id})
    assert response.status_code == HTTPStatus.OK

    client_db.session.expire_all()
    assert fixture['sr_map'].offset == _expected_old_offset(_SECTION_A)
    assert fixture['ts_map'].offset == _expected_old_offset(_SECTION_B)
    assert fixture['tc_map'].offset == _expected_old_offset(_SECTION_C)
    assert fixture['j_map'].offset == _expected_old_offset(_SECTION_D)
    assert fixture['doc_map'].offset == _expected_old_offset(_SECTION_E)


# --- Idempotency: calling fix twice yields same result ----------------------------

def test_fix_warnings_is_idempotent(client, client_db, user_authentication, api_with_all_mappings):
    fixture = api_with_all_mappings
    _shift_spec(fixture)

    client.get(_FIX_WARNINGS_URL, query_string={'id': fixture['api'].id})
    response = client.get(_FIX_WARNINGS_URL, query_string={'id': fixture['api'].id})

    assert response.status_code == HTTPStatus.OK
    client_db.session.expire_all()
    assert fixture['sr_map'].offset == _expected_new_offset(_SECTION_A)
    assert fixture['ts_map'].offset == _expected_new_offset(_SECTION_B)
    assert fixture['tc_map'].offset == _expected_new_offset(_SECTION_C)
    assert fixture['j_map'].offset == _expected_new_offset(_SECTION_D)
    assert fixture['doc_map'].offset == _expected_new_offset(_SECTION_E)
