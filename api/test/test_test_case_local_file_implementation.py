"""HTTP tests for TestCaseLocalFileImplementation (/test-cases/local-file-implementation)."""
import os
import pytest
import tempfile
from http import HTTPStatus

import api as basil_api
from db.models.user import UserModel
from db.models.api import ApiModel
from db.models.sw_requirement import SwRequirementModel
from db.models.api_sw_requirement import ApiSwRequirementModel
from db.models.sw_requirement_sw_requirement import SwRequirementSwRequirementModel
from db.models.test_specification import TestSpecificationModel
from db.models.sw_requirement_test_specification import SwRequirementTestSpecificationModel
from db.models.test_case import TestCaseModel
from db.models.api_test_case import ApiTestCaseModel
from db.models.sw_requirement_test_case import SwRequirementTestCaseModel
from db.models.test_specification_test_case import TestSpecificationTestCaseModel
from conftest import UT_USER_EMAIL

_LOCAL_FILE_IMPL_URL = "/test-cases/local-file-implementation"

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
    "Used for local-file-implementation UT."
)
_UT_API_RAW_RESTRICTED_SPEC = (
    'BASIL UT: "Reader" user is not able to read this API.'
    " Used for local-file-implementation UT."
)

_UT_TC_REMOTE_REPOSITORY = "https://github.com/example/repo"

_UT_TEST_SPEC_TITLE = "UT Test Specification"
_UT_TEST_SPEC_PRECONDITIONS = "Test preconditions here"
_UT_TEST_SPEC_DESCRIPTION = "Test description here"
_UT_TEST_SPEC_EXPECTED_BEHAVIOR = "Expected behavior here"

UNMATCHING_ID = 99999


def _auth_query(auth_json):
    uid = auth_json.get("id") if "id" in auth_json else auth_json.get("user-id")
    return {"user-id": uid, "token": auth_json["token"]}


def _get_local_file_impl(client, auth_json, api_id, test_case_id, relation_id, relation_to, extra=None):
    qs = {
        **_auth_query(auth_json),
        "api-id": api_id,
        "test-case-id": test_case_id,
        "relation-id": relation_id,
        "relation-to": relation_to,
    }
    if extra:
        qs = {**qs, **extra}
    return client.get(_LOCAL_FILE_IMPL_URL, query_string=qs)


def _write_spec_tempfile(spec_content: str) -> str:
    raw_spec = tempfile.NamedTemporaryFile(mode="w", delete=False)
    raw_spec.write(spec_content)
    raw_spec.close()
    return raw_spec.name


def _make_api_model(raw_spec_path: str, user, utilities) -> ApiModel:
    return ApiModel(
        _UT_API_NAME + "#" + utilities.generate_random_hex_string8(),
        _UT_API_LIBRARY,
        _UT_API_LIBRARY_VERSION,
        raw_spec_path,
        _UT_API_CATEGORY,
        utilities.generate_random_hex_string8(),
        raw_spec_path + "impl",
        _UT_API_IMPLEMENTATION_FILE_FROM_ROW,
        _UT_API_IMPLEMENTATION_FILE_TO_ROW,
        _UT_API_TAGS,
        user,
    )


def _get_test_case_model_remote(client_db, utilities):
    user = client_db.session.query(UserModel).filter(UserModel.email == UT_USER_EMAIL).one()
    return TestCaseModel(
        _UT_TC_REMOTE_REPOSITORY,
        f"tests/test_{utilities.generate_random_hex_string8()}.py",
        f"TC #{utilities.generate_random_hex_string8()}",
        "test case description for UT",
        user,
    )


def _get_sw_requirement_model(client_db, utilities):
    user = client_db.session.query(UserModel).filter(UserModel.email == UT_USER_EMAIL).one()
    return SwRequirementModel(
        f"SW req #{utilities.generate_random_hex_string8()}", "SW shall work as well as possible.", user
    )


def _get_test_specification_model(client_db, utilities):
    user = client_db.session.query(UserModel).filter(UserModel.email == UT_USER_EMAIL).one()
    return TestSpecificationModel(
        f"{_UT_TEST_SPEC_TITLE} #{utilities.generate_random_hex_string8()}",
        _UT_TEST_SPEC_PRECONDITIONS,
        _UT_TEST_SPEC_DESCRIPTION,
        _UT_TEST_SPEC_EXPECTED_BEHAVIOR,
        user,
    )


def _prepare_local_repo_and_file(test_case: TestCaseModel, user_id: int, utilities, content="local-content\n"):
    """Point test_case at a file under USER_FILES_BASE_DIR and write that file."""
    base = os.path.join(os.path.abspath(basil_api.USER_FILES_BASE_DIR), str(user_id))
    os.makedirs(base, exist_ok=True)
    rel = f"ut_tclocal_{utilities.generate_random_hex_string8()}.txt"
    path = os.path.join(base, rel)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    test_case.repository = base
    test_case.relative_path = rel
    return path


def _remove_if_exists(path):
    if path and os.path.isfile(path):
        os.remove(path)


@pytest.fixture()
def mapped_api_tc_db(client_db, ut_user_db, utilities):
    """API with one ApiTestCaseModel (remote test case repository by default)."""

    user = client_db.session.query(UserModel).filter(UserModel.email == UT_USER_EMAIL).one()

    raw_path = _write_spec_tempfile(_UT_API_RAW_MAPPED_SPEC)
    ut_api = _make_api_model(raw_path, user, utilities)
    ut_test_case = _get_test_case_model_remote(client_db, utilities)
    section_offset = _UT_API_RAW_MAPPED_SPEC.find(_UT_API_SPEC_SECTION_WITH_MAPPING)
    ut_api_tc_mapping = ApiTestCaseModel(
        ut_api, ut_test_case, _UT_API_SPEC_SECTION_WITH_MAPPING, section_offset, 75, user
    )

    client_db.session.add(ut_api)
    client_db.session.add(ut_test_case)
    client_db.session.add(ut_api_tc_mapping)
    client_db.session.commit()

    yield ut_api, ut_test_case, ut_api_tc_mapping

    if os.path.isfile(raw_path):
        os.remove(raw_path)


@pytest.fixture()
def restricted_api_db(client_db, ut_user_db, ut_reader_user_db, utilities):
    """API that denies read access to the reader user."""

    user = client_db.session.query(UserModel).filter(UserModel.email == UT_USER_EMAIL).one()

    raw_path = _write_spec_tempfile(_UT_API_RAW_RESTRICTED_SPEC)
    ut_api = _make_api_model(raw_path, user, utilities)
    ut_api.read_denials = f"[{ut_reader_user_db.id}]"
    client_db.session.add(ut_api)
    client_db.session.commit()

    yield ut_api

    if os.path.isfile(raw_path):
        os.remove(raw_path)


@pytest.fixture()
def mapped_api_sr_tc_db(client_db, ut_user_db, utilities):
    """Test Case mapped to a SW Requirement linked from the API reference."""

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
    ut_sw_requirement = _get_sw_requirement_model(client_db, utilities)
    ut_api_requirement_mapping = ApiSwRequirementModel(
        ut_api,
        ut_sw_requirement,
        _UT_API_SPEC_SECTION_WITH_MAPPING,
        _UT_API_RAW_MAPPED_SPEC.find(_UT_API_SPEC_SECTION_WITH_MAPPING),
        0,
        user,
    )
    ut_test_case = _get_test_case_model_remote(client_db, utilities)
    ut_sr_tc_mapping = SwRequirementTestCaseModel(
        ut_api_requirement_mapping, None, ut_test_case, 75, user
    )

    client_db.session.add(ut_api)
    client_db.session.add(ut_sw_requirement)
    client_db.session.add(ut_api_requirement_mapping)
    client_db.session.add(ut_test_case)
    client_db.session.add(ut_sr_tc_mapping)
    client_db.session.commit()

    yield ut_api, ut_sw_requirement, ut_api_requirement_mapping, ut_sr_tc_mapping

    if os.path.isfile(raw_spec.name):
        os.remove(raw_spec.name)


@pytest.fixture()
def mapped_api_sr_sr_tc_db(client_db, ut_user_db, utilities):
    """Test Case mapped to a nested Sw Requirement (sr–sr)."""

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
    ut_sw_requirement = _get_sw_requirement_model(client_db, utilities)
    ut_api_requirement_mapping = ApiSwRequirementModel(
        ut_api,
        ut_sw_requirement,
        _UT_API_SPEC_SECTION_WITH_MAPPING,
        _UT_API_RAW_MAPPED_SPEC.find(_UT_API_SPEC_SECTION_WITH_MAPPING),
        0,
        user,
    )
    ut_nested_sw_requirement = _get_sw_requirement_model(client_db, utilities)
    ut_requirement_requirement_mapping = SwRequirementSwRequirementModel(
        ut_api_requirement_mapping, None, ut_nested_sw_requirement, 50, user
    )
    ut_test_case = _get_test_case_model_remote(client_db, utilities)
    ut_sr_tc_mapping = SwRequirementTestCaseModel(
        None, ut_requirement_requirement_mapping, ut_test_case, 80, user
    )

    client_db.session.add(ut_api)
    client_db.session.add(ut_sw_requirement)
    client_db.session.add(ut_api_requirement_mapping)
    client_db.session.add(ut_nested_sw_requirement)
    client_db.session.add(ut_requirement_requirement_mapping)
    client_db.session.add(ut_test_case)
    client_db.session.add(ut_sr_tc_mapping)
    client_db.session.commit()

    yield (
        ut_api,
        ut_sw_requirement,
        ut_api_requirement_mapping,
        ut_requirement_requirement_mapping,
        ut_sr_tc_mapping,
    )

    if os.path.isfile(raw_spec.name):
        os.remove(raw_spec.name)


@pytest.fixture()
def mapped_api_sr_sr_ts_tc_db(client_db, ut_user_db, utilities):
    """Test Case under SwRequirementTestSpecification (nested sr–sr)."""

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
    ut_sw_requirement = _get_sw_requirement_model(client_db, utilities)
    ut_api_requirement_mapping = ApiSwRequirementModel(
        ut_api,
        ut_sw_requirement,
        _UT_API_SPEC_SECTION_WITH_MAPPING,
        _UT_API_RAW_MAPPED_SPEC.find(_UT_API_SPEC_SECTION_WITH_MAPPING),
        0,
        user,
    )
    ut_nested_sw_requirement = _get_sw_requirement_model(client_db, utilities)
    ut_requirement_requirement_mapping = SwRequirementSwRequirementModel(
        ut_api_requirement_mapping, None, ut_nested_sw_requirement, 50, user
    )
    ut_test_specification = _get_test_specification_model(client_db, utilities)
    ut_sr_ts_mapping = SwRequirementTestSpecificationModel(
        None, ut_requirement_requirement_mapping, ut_test_specification, 80, user
    )
    ut_test_case = _get_test_case_model_remote(client_db, utilities)
    ut_ts_tc_mapping = TestSpecificationTestCaseModel(None, ut_sr_ts_mapping, ut_test_case, 70, user)

    client_db.session.add(ut_api)
    client_db.session.add(ut_sw_requirement)
    client_db.session.add(ut_api_requirement_mapping)
    client_db.session.add(ut_nested_sw_requirement)
    client_db.session.add(ut_requirement_requirement_mapping)
    client_db.session.add(ut_test_specification)
    client_db.session.add(ut_sr_ts_mapping)
    client_db.session.add(ut_test_case)
    client_db.session.add(ut_ts_tc_mapping)
    client_db.session.commit()

    yield (
        ut_api,
        ut_sw_requirement,
        ut_api_requirement_mapping,
        ut_requirement_requirement_mapping,
        ut_sr_ts_mapping,
        ut_ts_tc_mapping,
    )

    if os.path.isfile(raw_spec.name):
        os.remove(raw_spec.name)


def test_login(user_authentication):
    assert user_authentication.status_code == HTTPStatus.OK


@pytest.mark.parametrize("omit_key", ["test-case-id", "relation-to", "relation-id"])
def test_get_missing_handler_mandatory_fields(
    client, user_authentication, mapped_api_tc_db, omit_key
):
    api, test_case, api_tc_mapping = mapped_api_tc_db
    auth = user_authentication.json
    qs = {
        **_auth_query(auth),
        "api-id": api.id,
        "test-case-id": test_case.id,
        "relation-id": api_tc_mapping.id,
        "relation-to": "api",
    }
    del qs[omit_key]
    response = client.get(_LOCAL_FILE_IMPL_URL, query_string=qs)
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_get_not_found_unknown_api(client, user_authentication):
    auth = user_authentication.json
    response = _get_local_file_impl(
        client, auth, 0, UNMATCHING_ID, UNMATCHING_ID, "api"
    )
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_get_not_found_api_relation_wrong_mapping(
    client, user_authentication, mapped_api_tc_db
):
    api, test_case, api_tc_mapping = mapped_api_tc_db
    auth = user_authentication.json
    response = _get_local_file_impl(
        client, auth, api.id, test_case.id, UNMATCHING_ID, "api"
    )
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_get_unauthorized_reader_restricted_api(
    client, restricted_api_db, ut_reader_user_db, mapped_api_tc_db
):
    _other_api, test_case, _mapping = mapped_api_tc_db
    auth = {"user-id": ut_reader_user_db.id, "token": ut_reader_user_db.token}
    response = _get_local_file_impl(
        client, auth, restricted_api_db.id, test_case.id, UNMATCHING_ID, "api"
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED


def test_get_bad_request_remote_repository(client, user_authentication, mapped_api_tc_db):
    """Remote repository (non-local) cannot be read via repository + relative path."""
    api, test_case, api_tc_mapping = mapped_api_tc_db
    auth = user_authentication.json
    response = _get_local_file_impl(
        client, auth, api.id, test_case.id, api_tc_mapping.id, "api"
    )
    assert response.status_code == HTTPStatus.BAD_REQUEST
    text = response.get_data(as_text=True).lower()
    assert "remote" in text


def test_get_ok_api_relation_local_file(
    client, client_db, user_authentication, mapped_api_tc_db, utilities
):
    api, test_case, api_tc_mapping = mapped_api_tc_db
    auth = user_authentication.json
    user_id = auth["id"]
    path = _prepare_local_repo_and_file(test_case, user_id, utilities, content="plain-text-utf8")
    client_db.session.add(test_case)
    client_db.session.commit()
    try:
        response = _get_local_file_impl(
            client, auth, api.id, test_case.id, api_tc_mapping.id, "api"
        )
        assert response.status_code == HTTPStatus.OK
        assert "text/plain" in (response.mimetype or "")
        assert response.get_data(as_text=True) == "plain-text-utf8"
    finally:
        _remove_if_exists(path)


def test_get_bad_request_unsafe_local_path(
    client, client_db, user_authentication, mapped_api_tc_db, utilities
):
    api, test_case, api_tc_mapping = mapped_api_tc_db
    auth = user_authentication.json
    test_case.repository = "/tmp"
    test_case.relative_path = f"not_under_user_files_{utilities.generate_random_hex_string8()}.txt"
    client_db.session.add(test_case)
    client_db.session.commit()

    response = _get_local_file_impl(
        client, auth, api.id, test_case.id, api_tc_mapping.id, "api"
    )
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert "traversal" in response.get_data(as_text=True).lower()


def test_get_not_found_missing_local_file(
    client, client_db, user_authentication, mapped_api_tc_db, utilities
):
    api, test_case, api_tc_mapping = mapped_api_tc_db
    auth = user_authentication.json
    user_id = auth["id"]
    base = os.path.join(os.path.abspath(basil_api.USER_FILES_BASE_DIR), str(user_id))
    os.makedirs(base, exist_ok=True)
    test_case.repository = base
    test_case.relative_path = f"missing_{utilities.generate_random_hex_string8()}.txt"
    client_db.session.add(test_case)
    client_db.session.commit()

    response = _get_local_file_impl(
        client, auth, api.id, test_case.id, api_tc_mapping.id, "api"
    )
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_get_ok_sw_requirement_relation_local_file(
    client, client_db, user_authentication, mapped_api_sr_tc_db, utilities
):
    api, _sw, _api_sr, sr_tc_mapping = mapped_api_sr_tc_db
    auth = user_authentication.json
    test_case = sr_tc_mapping.test_case
    path = _prepare_local_repo_and_file(test_case, auth["id"], utilities, content="sr-local")
    client_db.session.add(test_case)
    client_db.session.commit()
    try:
        response = _get_local_file_impl(
            client, auth, api.id, test_case.id, sr_tc_mapping.id, "sw-requirement"
        )
        assert response.status_code == HTTPStatus.OK
        assert response.get_data(as_text=True) == "sr-local"
    finally:
        _remove_if_exists(path)


def test_get_bad_request_sw_requirement_wrong_api(
    client, client_db, user_authentication, mapped_api_sr_tc_db, utilities
):
    api, _sw, _api_sr, sr_tc_mapping = mapped_api_sr_tc_db
    user = client_db.session.query(UserModel).filter(UserModel.email == UT_USER_EMAIL).one()
    raw_path = _write_spec_tempfile(_UT_API_RAW_MAPPED_SPEC)
    other_api = _make_api_model(raw_path, user, utilities)
    client_db.session.add(other_api)
    client_db.session.commit()
    test_case = sr_tc_mapping.test_case
    try:
        response = _get_local_file_impl(
            client,
            user_authentication.json,
            other_api.id,
            test_case.id,
            sr_tc_mapping.id,
            "sw-requirement",
        )
        assert response.status_code == HTTPStatus.BAD_REQUEST
    finally:
        row = client_db.session.get(ApiModel, other_api.id)
        if row is not None:
            client_db.session.delete(row)
            client_db.session.commit()
        if os.path.isfile(raw_path):
            os.remove(raw_path)


def test_get_ok_sw_requirement_nested_sr_sr_local_file(
    client, client_db, user_authentication, mapped_api_sr_sr_tc_db, utilities
):
    api, _sw, _api_sr, _sr_sr, sr_tc_mapping = mapped_api_sr_sr_tc_db
    auth = user_authentication.json
    test_case = sr_tc_mapping.test_case
    path = _prepare_local_repo_and_file(test_case, auth["id"], utilities, content="nested-sr")
    client_db.session.add(test_case)
    client_db.session.commit()
    try:
        response = _get_local_file_impl(
            client, auth, api.id, test_case.id, sr_tc_mapping.id, "sw-requirement"
        )
        assert response.status_code == HTTPStatus.OK
        assert response.get_data(as_text=True) == "nested-sr"
    finally:
        _remove_if_exists(path)


def test_get_ok_test_specification_via_sr_mapping_local_file(
    client, client_db, user_authentication, mapped_api_sr_sr_ts_tc_db, utilities
):
    api, _sw, _api_sr, _sr_sr, _sr_ts, ts_tc_mapping = mapped_api_sr_sr_ts_tc_db
    auth = user_authentication.json
    test_case = ts_tc_mapping.test_case
    path = _prepare_local_repo_and_file(test_case, auth["id"], utilities, content="ts-sr")
    client_db.session.add(test_case)
    client_db.session.commit()
    try:
        response = _get_local_file_impl(
            client, auth, api.id, test_case.id, ts_tc_mapping.id, "test-specification"
        )
        assert response.status_code == HTTPStatus.OK
        assert response.get_data(as_text=True) == "ts-sr"
    finally:
        _remove_if_exists(path)
