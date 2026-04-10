"""HTTP tests for GET /mapping/history (MappingHistory)."""
import os
import tempfile
from http import HTTPStatus

import pytest

from db.models.user import UserModel
from db.models.api import ApiModel
from db.models.document import DocumentModel
from db.models.api_document import ApiDocumentModel
from db.models.document_document import DocumentDocumentModel
from conftest import UT_USER_EMAIL

_MAPPING_HISTORY_URL = "/mapping/history"

_UT_API_NAME = "ut_api"
_UT_API_LIBRARY = "ut_api_library"
_UT_API_LIBRARY_VERSION = "v1.0.0"
_UT_API_CATEGORY = "ut_api_category"
_UT_API_IMPLEMENTATION_FILE_FROM_ROW = 0
_UT_API_IMPLEMENTATION_FILE_TO_ROW = 42
_UT_API_TAGS = "ut_api_tags"

_UT_API_SPEC_SECTION_WITH_MAPPING = "This section has mapping."
_UT_API_SPEC_SECTION_TO_BE_MAPPED = "This section is to be mapped."
_UT_API_RAW_MAPPED_SPEC = (
    f"BASIL UT: {_UT_API_SPEC_SECTION_WITH_MAPPING} {_UT_API_SPEC_SECTION_TO_BE_MAPPED} "
    "Used for /mapping/history."
)

_UNMATCHING_RELATION_ID = 9_999_999


def _get_document(client_db, utilities, *, url="stub.md", section=_UT_API_SPEC_SECTION_WITH_MAPPING, offset=0):
    user = client_db.session.query(UserModel).filter(UserModel.email == UT_USER_EMAIL).one()
    return DocumentModel(
        title=f"Doc #{utilities.generate_random_hex_string8()}",
        description="unit test document",
        document_type="file",
        spdx_relation="relates-to",
        url=url,
        section=section,
        offset=offset,
        valid=0,
        created_by=user,
    )


def _get_mapping_history(client, *, work_item_type, mapped_to_type, relation_id):
    return client.get(
        _MAPPING_HISTORY_URL,
        query_string={
            "work_item_type": work_item_type,
            "mapped_to_type": mapped_to_type,
            "relation_id": relation_id,
        },
    )


def _create_api_with_api_document_mapping(client_db, utilities):
    """Returns (raw_spec_path, ut_api, ut_document, ut_api_doc_mapping) after commit."""
    user = client_db.session.query(UserModel).filter(UserModel.email == UT_USER_EMAIL).one()

    raw_spec = tempfile.NamedTemporaryFile(mode="w", delete=False)
    raw_spec.write(_UT_API_RAW_MAPPED_SPEC)
    raw_spec.close()

    ut_api = ApiModel(
        _UT_API_NAME + "#" + utilities.generate_random_hex_string8(),
        _UT_API_LIBRARY,
        _UT_API_LIBRARY_VERSION,
        raw_spec.name,
        _UT_API_CATEGORY,
        utilities.generate_random_hex_string8(),
        raw_spec.name + "impl",
        _UT_API_IMPLEMENTATION_FILE_FROM_ROW,
        _UT_API_IMPLEMENTATION_FILE_TO_ROW,
        _UT_API_TAGS,
        user,
    )
    ut_document = _get_document(
        client_db,
        utilities,
        url=raw_spec.name,
        section=_UT_API_SPEC_SECTION_WITH_MAPPING,
        offset=_UT_API_RAW_MAPPED_SPEC.find(_UT_API_SPEC_SECTION_WITH_MAPPING),
    )
    ut_api_doc_mapping = ApiDocumentModel(
        ut_api,
        ut_document,
        _UT_API_SPEC_SECTION_WITH_MAPPING,
        _UT_API_RAW_MAPPED_SPEC.find(_UT_API_SPEC_SECTION_WITH_MAPPING),
        0,
        user,
    )
    client_db.session.add(ut_api)
    client_db.session.add(ut_document)
    client_db.session.add(ut_api_doc_mapping)
    client_db.session.commit()
    return raw_spec.name, ut_api, ut_document, ut_api_doc_mapping


def _assert_history_entry_shape(entry):
    assert isinstance(entry, dict)
    assert "version" in entry
    assert "object" in entry
    assert "mapping" in entry
    assert "created_at" in entry
    assert isinstance(entry["object"], dict)
    assert isinstance(entry["mapping"], dict)


@pytest.fixture()
def api_document_mapping_db(client_db, ut_user_db, utilities):
    """API with one ApiDocument mapping (relation_id = ApiDocumentModel.id)."""
    raw_spec_path, _ut_api, _ut_doc, ut_api_doc_mapping = _create_api_with_api_document_mapping(
        client_db, utilities
    )
    yield ut_api_doc_mapping.id

    if os.path.isfile(raw_spec_path):
        os.remove(raw_spec_path)


@pytest.fixture()
def document_document_mapping_db(client_db, ut_user_db, utilities):
    """Nested document mapping: ApiDocument -> DocumentDocument (relation_id = DocumentDocumentModel.id)."""
    user = client_db.session.query(UserModel).filter(UserModel.email == UT_USER_EMAIL).one()
    raw_spec_path, _ut_api, _ut_document, ut_api_document_mapping = _create_api_with_api_document_mapping(
        client_db, utilities
    )
    ut_nested_document = _get_document(client_db, utilities)
    ut_document_document_mapping = DocumentDocumentModel(
        document_mapping_api=ut_api_document_mapping,
        document_mapping_document=None,
        document=ut_nested_document,
        section="Nested section",
        offset=0,
        coverage=50,
        created_by=user,
    )
    client_db.session.add(ut_nested_document)
    client_db.session.add(ut_document_document_mapping)
    client_db.session.commit()

    yield ut_document_document_mapping.id

    if os.path.isfile(raw_spec_path):
        os.remove(raw_spec_path)


def test_mapping_history_missing_work_item_type(client):
    response = client.get(
        _MAPPING_HISTORY_URL,
        query_string={"mapped_to_type": "api", "relation_id": 1},
    )
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_mapping_history_missing_mapped_to_type(client):
    response = client.get(
        _MAPPING_HISTORY_URL,
        query_string={"work_item_type": "document", "relation_id": 1},
    )
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_mapping_history_missing_relation_id(client):
    response = client.get(
        _MAPPING_HISTORY_URL,
        query_string={"work_item_type": "document", "mapped_to_type": "api"},
    )
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_mapping_history_unknown_mapped_to_type_returns_empty_list(client):
    response = _get_mapping_history(
        client,
        work_item_type="document",
        mapped_to_type="not-a-valid-type",
        relation_id=1,
    )
    assert response.status_code == HTTPStatus.OK
    assert response.get_json() == []


def test_mapping_history_unknown_relation_returns_empty_list(client):
    response = _get_mapping_history(
        client,
        work_item_type="document",
        mapped_to_type="api",
        relation_id=_UNMATCHING_RELATION_ID,
    )
    assert response.status_code == HTTPStatus.OK
    assert response.get_json() == []


def test_mapping_history_api_document_ok(client, api_document_mapping_db):
    relation_id = api_document_mapping_db
    response = _get_mapping_history(
        client,
        work_item_type="document",
        mapped_to_type="api",
        relation_id=relation_id,
    )
    assert response.status_code == HTTPStatus.OK
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) >= 1
    _assert_history_entry_shape(data[0])
    assert data[0]["version"] == "1.1"
    assert "title" in data[0]["object"]
    assert "section" in data[0]["mapping"]


def test_mapping_history_document_document_ok(client, document_document_mapping_db):
    relation_id = document_document_mapping_db
    response = _get_mapping_history(
        client,
        work_item_type="document",
        mapped_to_type="document",
        relation_id=relation_id,
    )
    assert response.status_code == HTTPStatus.OK
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) >= 1
    _assert_history_entry_shape(data[0])
    assert data[0]["version"] == "1.1"
