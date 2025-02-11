import base64
import datetime
import json
import logging
import math
import os
import shutil
import sys
import time
import urllib
from urllib.error import HTTPError, URLError
from uuid import uuid4

import gitlab
from flask import Flask, request, send_file, send_from_directory
from flask_cors import CORS
from flask_restful import Api, Resource, reqparse
from pyaml_env import parse_config
from sqlalchemy import and_, or_, update
from sqlalchemy.orm.exc import NoResultFound
from testrun import TestRunner

logging.basicConfig()
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

currentdir = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(1, os.path.dirname(currentdir))

JOIN_APIS_TABLE = "apis"
JOIN_SW_REQUIREMENTS_TABLE = "sw-requirements"
JOIN_TEST_SPECIFICATIONS_TABLE = "test-specifications"
MAX_LOGIN_ATTEMPTS = 5
MAX_LOGIN_ATTEMPTS_TIMEOUT = 60 * 5  # 5 minutes
SSH_KEYS_PATH = os.path.join(currentdir, "ssh_keys")
TESTRUN_PRESET_FILEPATH = os.path.join(currentdir, "testrun_plugin_presets.yaml")
TEST_RUNS_BASE_DIR = os.getenv("TEST_RUNS_BASE_DIR", "/var/test-runs")
USER_FILES_BASE_DIR = os.path.join(currentdir, "user-files")  # forced under api to ensure tmt tree validity

if not os.path.exists(SSH_KEYS_PATH):
    os.makedirs(SSH_KEYS_PATH, exist_ok=True)

if not os.path.exists(TEST_RUNS_BASE_DIR):
    os.makedirs(TEST_RUNS_BASE_DIR, exist_ok=True)

if not os.path.exists(USER_FILES_BASE_DIR):
    os.makedirs(USER_FILES_BASE_DIR, exist_ok=True)

USER_ROLES_DELETE_PERMISSIONS = ["ADMIN", "USER"]
USER_ROLES_EDIT_PERMISSIONS = ["ADMIN", "USER"]
USER_ROLES_WRITE_PERMISSIONS = ["ADMIN", "USER"]
USER_ROLES_MANAGE_PERMISSIONS = ["ADMIN", "USER"]
USER_ROLES_MANAGE_USERS = [
    "ADMIN",
]

OK_STATUS = 200
CREATED_STATUS = 201
BAD_REQUEST_MESSAGE = "Bad request"
BAD_REQUEST_STATUS = 400
UNAUTHORIZED_MESSAGE = "User not authorized"
UNAUTHORIZED_STATUS = 401
FORBIDDEN_MESSAGE = "Forbidden"
FORBIDDEN_STATUS = 403
NOT_FOUND_MESSAGE = "Not found"
SW_COMPONENT_NOT_FOUND_MESSAGE = "Sw Component not found."
NOT_FOUND_STATUS = 404
CONFLICT_MESSAGE = "Conflict with existing data"
CONFLICT_STATUS = 409
PRECONDITION_FAILED_MESSAGE = "Same precondition failed"
PRECONDITION_FAILED_STATUS = 412

NOTIFICATION_CATEGORY_NEW = "success"
NOTIFICATION_CATEGORY_EDIT = "warning"
NOTIFICATION_CATEGORY_DELETE = "danger"

API_PERMISSION_FIELDS = [
    "delete_permissions",
    "edit_permissions",
    "manage_permissions",
    "read_denials",
    "write_permissions",
]

from db import db_orm
from db.models.api import ApiHistoryModel, ApiModel
from db.models.api_document import ApiDocumentHistoryModel, ApiDocumentModel
from db.models.api_justification import ApiJustificationHistoryModel, ApiJustificationModel
from db.models.api_sw_requirement import ApiSwRequirementHistoryModel, ApiSwRequirementModel
from db.models.api_test_case import ApiTestCaseHistoryModel, ApiTestCaseModel
from db.models.api_test_specification import ApiTestSpecificationHistoryModel, ApiTestSpecificationModel
from db.models.comment import CommentModel
from db.models.document import DocumentHistoryModel, DocumentModel
from db.models.justification import JustificationHistoryModel, JustificationModel
from db.models.notification import NotificationModel
from db.models.ssh_key import SshKeyModel
from db.models.sw_requirement import SwRequirementHistoryModel, SwRequirementModel
from db.models.sw_requirement_sw_requirement import (
    SwRequirementSwRequirementHistoryModel,
    SwRequirementSwRequirementModel,
)
from db.models.sw_requirement_test_case import SwRequirementTestCaseHistoryModel, SwRequirementTestCaseModel
from db.models.sw_requirement_test_specification import (
    SwRequirementTestSpecificationHistoryModel,
    SwRequirementTestSpecificationModel,
)
from db.models.test_case import TestCaseHistoryModel, TestCaseModel
from db.models.test_run import TestRunModel
from db.models.test_run_config import TestRunConfigModel
from db.models.test_specification import TestSpecificationHistoryModel, TestSpecificationModel
from db.models.test_specification_test_case import (
    TestSpecificationTestCaseHistoryModel,
    TestSpecificationTestCaseModel,
)
from db.models.user import UserModel
from spdx_manager import SPDXImport, SPDXManager

app = Flask("BASIL-API")
api = Api(app)
CORS(app)

login_attempt_cache = {}

token_parser = reqparse.RequestParser()
token_parser.add_argument("token", location="form")

_A = "api"
_As = f"{_A}s"
_SR = "sw_requirement"
_SRs = f"{_SR}s"
_TS = "test_specification"
_TSs = f"{_TS}s"
_TC = "test_case"
_TCs = f"{_TC}s"
_J = "justification"
_Js = f"{_J}s"
_D = "document"
_Ds = f"{_D}s"


def get_api_from_request(_request, _db_session):
    if "api-id" not in _request.keys():
        return None

    query = _db_session.query(ApiModel).filter(ApiModel.id == _request["api-id"])

    try:
        api = query.one()
        return api
    except NoResultFound:
        return None


def get_parent_api_id(_mapping, _dbisession):
    # Return api id or None

    # Work Items mapped to a Sw Requirement
    if (
        isinstance(_mapping, SwRequirementSwRequirementModel)
        or isinstance(_mapping, SwRequirementTestCaseModel)
        or isinstance(_mapping, SwRequirementTestSpecificationModel)
    ):
        api_mapping_model = ApiSwRequirementModel
        parent_model = SwRequirementSwRequirementModel
        parent_mapping_field_id = "sw_requirement_mapping_sw_requirement_id"
        parent_mapping_api_field_id = "sw_requirement_mapping_api_id"
    else:
        print(f"\n WARNING: mapping is instance of {type(_mapping)}")
        return None

    api_mapping_id = getattr(_mapping, parent_mapping_api_field_id)
    parent_mapping_id = getattr(_mapping, parent_mapping_field_id)

    if not api_mapping_id:
        try:
            parent_mapping = _dbisession.query(parent_model).filter(parent_model.id == parent_mapping_id).one()
            api_mapping_id = get_parent_api_id(parent_mapping, _dbisession)
        except NoResultFound:
            return None

    if api_mapping_id:
        try:
            parent_api_mapping = (
                _dbisession.query(api_mapping_model).filter(api_mapping_model.id == api_mapping_id).one()
            )
            return parent_api_mapping.api.id
        except NoResultFound:
            return None
    return None


def get_user_id_from_request(_request, _db_session):
    user = get_active_user_from_request(_request, _db_session)
    if isinstance(user, UserModel):
        user_id = user.id
    else:
        user_id = 0
    return user_id


def get_user_email_from_id(_id, _db_session):
    try:
        user = _db_session.query(UserModel).filter(UserModel.id == _id).one()
        return user.email
    except NoResultFound:
        return ""


def get_active_user_from_request(_request, _db_session):
    mandatory_fields = ["user-id", "token"]
    for field in mandatory_fields:
        if field not in _request.keys():
            return None

    query = (
        _db_session.query(UserModel)
        .filter(UserModel.id == _request["user-id"])
        .filter(UserModel.token == _request["token"])
        .filter(UserModel.enabled == 1)
    )

    try:
        user = query.one()
        return user
    except NoResultFound:
        return None


def get_users_email_from_ids(_ids, _dbi_session):
    # _ids list format [1][3][34]
    user_ids = _ids.split("][")
    user_ids = [x.replace("[", "").replace("]", "") for x in user_ids]
    query = _dbi_session.query(UserModel.email).filter(UserModel.id.in_(user_ids))
    users = query.all()
    ret = [x.email for x in users]
    return ret


def get_api_user_permissions(_api, _user_id, _user_role, _dbi_session):
    """Extract user permissions from api

    - guest (without user entry) has id = 0
    - user with GUEST role doesn't have read permissions in case a read denial is defined
    - guest (without user entry) or user with GUEST role can only have read permissions
    - for other roles, Write permission implies Read permission
    """
    permissions = ""
    if _api.created_by_id == _user_id:
        return "rwem"

    if _user_id == 0 or _user_role == 'GUEST':
        if _api.read_denials == '':
            permissions = "r"
        return permissions
    else:
        if f"[{_user_id}]" not in _api.read_denials:
            permissions += "r"
            if f"[{_user_id}]" in _api.write_permissions:
                permissions += "w"

    if f"[{_user_id}]" in _api.manage_permissions:
        permissions += "m"
    if f"[{_user_id}]" in _api.edit_permissions:
        permissions += "e"
    return permissions


def get_combined_history_object(_obj, _map, _obj_fields, _map_fields):
    _obj_fields += ["version"]
    _map_fields += ["version"]

    # obj_version = _obj['version'] if 'version' in _obj.keys() else ''
    map_version = _map["version"] if "version" in _map.keys() else ""

    if map_version != "":
        combined_version = f'{_obj["version"]}.{_map["version"]}'
    else:
        combined_version = f'{_obj["version"]}'

    if "created_at" in _map.keys():
        combined_date = _obj["created_at"] if _obj["created_at"] > _map["created_at"] else _map["created_at"]
    else:
        combined_date = _obj["created_at"]

    _combined = {"version": combined_version, "object": {}, "mapping": {}, "created_at": combined_date}

    for k in _obj_fields:
        if k in _obj.keys():
            _combined["object"][k] = _obj[k]

    for j in _map_fields:
        if j in _map.keys():
            _combined["mapping"][j] = _map[j]

    return _combined


def get_reduced_history_data(history_data, _obj_fields, _map_fields, _dbi_session):
    """
    Remove from the history_data fields that has not been modified
    Adding on each history element the name of the user
    """
    fields_to_skip = ["version", "created_at", "updated_at"]

    if len(history_data) == 0:
        return []

    ret = [
        {
            "version": history_data[0]["version"],
            "object": {},
            "mapping": {},
            "created_at": history_data[0]["created_at"].strftime("%d %b %y %H:%M"),
        }
    ]

    for k in _obj_fields:
        if k in history_data[0]["object"].keys() and k not in fields_to_skip:
            ret[0]["object"][k] = history_data[0]["object"][k]

    for j in _map_fields:
        if j in history_data[0]["mapping"].keys() and j not in fields_to_skip:
            ret[0]["mapping"][j] = history_data[0]["mapping"][j]

    # Object - return user email of the first version instead of the id
    if "edited_by_id" in ret[0]["object"].keys():
        del ret[0]["object"]["edited_by_id"]
    if "created_by_id" in ret[0]["object"].keys():
        ret[0]["object"]["created_by"] = get_user_email_from_id(ret[0]["object"]["created_by_id"], _dbi_session)
        del ret[0]["object"]["created_by_id"]

    # Mapping - return user email of the first version instead of the id
    if "edited_by_id" in ret[0]["mapping"].keys():
        del ret[0]["mapping"]["edited_by_id"]
    if "created_by_id" in ret[0]["mapping"].keys():
        ret[0]["mapping"]["created_by"] = get_user_email_from_id(ret[0]["mapping"]["created_by_id"], _dbi_session)
        del ret[0]["mapping"]["created_by_id"]

    if len(history_data) > 1:
        for i in range(1, len(history_data)):
            tmp = {
                "object": {},
                "mapping": {},
                "version": history_data[i]["version"],
                "created_at": history_data[i]["created_at"].strftime("%d %b %y %H:%M"),
            }

            last_version = history_data[i - 1]["version"].split(".")
            current_version = history_data[i]["version"].split(".")

            if last_version[0] != current_version[0]:
                # object changed
                for k in _obj_fields:
                    if k in history_data[i]["object"].keys() and k not in fields_to_skip:
                        if history_data[i]["object"][k] != history_data[i - 1]["object"][k]:
                            tmp["object"][k] = history_data[i]["object"][k]
                    tmp["object"]["edited_by"] = get_user_email_from_id(
                        history_data[i]["object"]["edited_by_id"], _dbi_session
                    )

            if len(last_version) > 1 and len(current_version) > 1:
                if last_version[1] != current_version[1]:
                    # mapping changed
                    for j in _map_fields:
                        if j in history_data[i]["mapping"].keys() and j not in fields_to_skip:
                            if history_data[i]["mapping"][j] != history_data[i - 1]["mapping"][j]:
                                tmp["mapping"][j] = history_data[i]["mapping"][j]
                    tmp["mapping"]["edited_by"] = get_user_email_from_id(
                        history_data[i]["mapping"]["edited_by_id"], _dbi_session
                    )
            ret.append(tmp)

    return ret


def get_dict_without_keys(_dict, _undesired_keys):
    current_keys = _dict.keys()
    for k in _undesired_keys:
        if k in current_keys:
            del _dict[k]
    return _dict


def get_model_editable_fields(_model, _is_history):
    not_editable_model_fields = [
        "id",
        "created_at",
        "updated_at",
        "created_by_id",
        "edited_by_id",
        "delete_permissions",
        "edit_permissions",
        "manage_permissions",
        "read_denials",
        "write_permissions",
        "checksum",
    ]

    not_editable_model_history_fields = [
        "row_id",
        "created_at",
        "updated_at",
        "delete_permissions",
        "edit_permissions",
        "manage_permissions",
        "read_denials",
        "write_permissions",
    ]

    all_fields = _model.__table__.columns.keys()
    if not _is_history:
        return [x for x in all_fields if x not in not_editable_model_fields]
    else:
        return [x for x in all_fields if x not in not_editable_model_history_fields]


def get_dict_with_db_format_keys(_dict):
    """
    return a dict with keys formatted with _ instead of -
    """
    tmp = {}
    for iKey in list(_dict.keys()):
        tmp[iKey.replace("-", "_")] = _dict[iKey]
    return tmp


def filter_query(_query, _args, _model, _is_history):
    fields = get_model_editable_fields(_model, _is_history)
    for arg_key in _args.keys():
        if "field" in arg_key:
            field_n = arg_key.replace("field", "")
            field = _args[f"field{field_n}"]
            filter = _args[f"filter{field_n}"]
            if field in fields:
                _query = _query.filter(getattr(_model, field) == filter)
            elif field == "id":
                _query = _query.filter(_model.id == filter)

        if arg_key == "search":
            _query = _query.filter(or_(getattr(_model, field).like(f'%{_args["search"]}%') for field in fields))

    return _query


def get_db():
    if app.config["TESTING"]:
        return "test.db"
    return "basil.db"


def get_api_specification(_url_or_path):
    if _url_or_path is None:
        return None
    else:
        _url_or_path = _url_or_path.strip()
        if len(_url_or_path) == 0:
            return None

        if _url_or_path.startswith("http"):
            try:
                resource = urllib.request.urlopen(_url_or_path)
                if resource.headers.get_content_charset():
                    content = resource.read().decode(resource.headers.get_content_charset())
                else:
                    content = resource.read().decode("utf-8")
                return content
            except HTTPError as excp:
                print(f"HTTPError: {excp.reason} reading {_url_or_path}")
                return None
            except URLError as excp:
                print(f"URLError: {excp.reason} reading {_url_or_path}")
                return None
            except ValueError as excp:
                print(f"ValueError reading {_url_or_path}: {excp}")
                return None
        else:
            if not os.path.exists(_url_or_path):
                return None

            try:
                f = open(_url_or_path, "r")
                fc = f.read()
                f.close()
                return fc
            except OSError:
                return None


def get_api_coverage(_sections):
    total_len = sum([len(x["section"]) for x in _sections])
    wa = 0
    for i in range(len(_sections)):
        wa += (len(_sections[i]["section"]) / total_len) * (_sections[i]["covered"] / 100.0)
    return int(wa * 100)


def split_section(_to_splits, _that_split, _work_item_type):
    sections = []
    _current_work_item = _that_split

    if _work_item_type == _SR:
        if "indirect_sw_requirement" in _that_split.keys():
            _current_work_item["parent_mapping_type"] = "sw_requirement_mapping_sw_requirement"
        else:
            _current_work_item["parent_mapping_type"] = "sw_requirement_mapping_api"

    for _to_split in _to_splits:
        _to_split_range = range(_to_split["offset"], _to_split["offset"] + len(_to_split["section"]))
        that_split_range = range(_that_split["offset"], _that_split["offset"] + len(_that_split["section"]))
        overlap = len(list(set(_to_split_range) & set(that_split_range))) > 0
        if not overlap:
            tmp_section = {
                "section": _to_split["section"],
                "offset": _to_split["offset"],
                "coverage": _to_split["coverage"],
                "covered": _to_split["covered"],
                "gap": _to_split["gap"],
                "delete": 0,
                _Js: [],
                _TCs: [],
                _TSs: [],
                _SRs: [],
                _Ds: [],
            }

            for j in range(len(_to_split[_SRs])):
                tmp_section[_SRs].append(_to_split[_SRs][j].copy())
            for j in range(len(_to_split[_TCs])):
                tmp_section[_TCs].append(_to_split[_TCs][j].copy())
            for j in range(len(_to_split[_TSs])):
                tmp_section[_TSs].append(_to_split[_TSs][j].copy())
            for j in range(len(_to_split[_Js])):
                tmp_section[_Js].append(_to_split[_Js][j].copy())
            for j in range(len(_to_split[_Ds])):
                tmp_section[_Ds].append(_to_split[_Ds][j].copy())

            sections.append(tmp_section)

        else:
            idx = [
                _to_split["offset"],
                _to_split["offset"] + len(_to_split["section"]),
                _that_split["offset"],
                _that_split["offset"] + len(_that_split["section"]),
            ]
            idx_set = set(idx)
            idx = sorted(list(idx_set))
            for i in range(1, len(idx)):
                tmp_section = {
                    "section": _to_split["section"][idx[i - 1] - idx[0] : idx[i] - idx[0]],
                    "offset": idx[i - 1],
                    "coverage": _to_split["coverage"],
                    "covered": _to_split["covered"],
                    "gap": _to_split["gap"],
                    "delete": 0,
                    _Js: [],
                    _TCs: [],
                    _TSs: [],
                    _SRs: [],
                    _Ds: [],
                }

                for j in range(len(_to_split[_SRs])):
                    tmp_section[_SRs].append(_to_split[_SRs][j].copy())
                for j in range(len(_to_split[_TCs])):
                    tmp_section[_TCs].append(_to_split[_TCs][j].copy())
                for j in range(len(_to_split[_TSs])):
                    tmp_section[_TSs].append(_to_split[_TSs][j].copy())
                for j in range(len(_to_split[_Js])):
                    tmp_section[_Js].append(_to_split[_Js][j].copy())
                for j in range(len(_to_split[_Ds])):
                    tmp_section[_Ds].append(_to_split[_Ds][j].copy())

                sections.append(tmp_section)

    for iSection in range(len(sections)):
        section_range = range(
            sections[iSection]["offset"], sections[iSection]["offset"] + len(sections[iSection]["section"])
        )
        that_split_range = range(_that_split["offset"], _that_split["offset"] + len(_that_split["section"]))
        overlap = len(list(set(section_range) & set(that_split_range))) > 0
        if overlap:
            sections[iSection][f"{_work_item_type}s"].append(_current_work_item)

    return sections


def get_split_sections(_specification, _mapping, _work_item_types):
    """
    _mapping: list of x_y (e.g. ApiSwRequirement) with nested mapping
              each row has its own specification section information
    _work_item_types: list of work items type for direct mapping that I
              what to display in the current view
    return: list of sections with related mapping
    """
    mapped_sections = [
        {
            "section": _specification,
            "offset": 0,
            "coverage": 0,
            "covered": 0,
            "gap": 100,
            "delete": 0,
            _TCs: [],
            _TSs: [],
            _SRs: [],
            _Js: [],
            _Ds: [],
        }
    ]

    for iWIT in range(len(_work_item_types)):
        _items_key = f"{_work_item_types[iWIT]}s"
        for iMapping in range(len(_mapping[_items_key])):
            if not _mapping[_items_key][iMapping]["match"]:
                continue
            mapped_sections = sorted(mapped_sections, key=lambda k: k["offset"])

            # get overlapping sections
            overlapping_section_indexes = []
            for j in range(len(mapped_sections)):
                section_range = range(
                    mapped_sections[j]["offset"], mapped_sections[j]["offset"] + len(mapped_sections[j]["section"])
                )
                that_split_range = range(
                    _mapping[_items_key][iMapping]["offset"],
                    _mapping[_items_key][iMapping]["offset"] + len(_mapping[_items_key][iMapping]["section"]),
                )
                overlap = len(list(set(section_range) & set(that_split_range))) > 0
                if overlap:
                    overlapping_section_indexes.append(j)

            if len(overlapping_section_indexes) > 0:
                for k in overlapping_section_indexes:
                    mapped_sections[k]["delete"] = 1

                mapped_sections += split_section(
                    [x for x in mapped_sections if x["delete"] == 1],
                    _mapping[_items_key][iMapping],
                    _work_item_types[iWIT],
                )
                mapped_sections = [x for x in mapped_sections if x["delete"] == 0]

    for iS in range(len(mapped_sections)):
        if mapped_sections[iS]["section"].strip() == "":
            if (
                sum(
                    [
                        len(mapped_sections[iS][_SRs]),
                        len(mapped_sections[iS][_TSs]),
                        len(mapped_sections[iS][_TCs]),
                        len(mapped_sections[iS][_Js]),
                        len(mapped_sections[iS][_Ds]),
                    ]
                )
                == 0
            ):
                mapped_sections[iS]["delete"] = True

        coverage_total = 0
        for j in range(len(mapped_sections[iS][_SRs])):
            coverage_total += mapped_sections[iS][_SRs][j]["covered"]
        for j in range(len(mapped_sections[iS][_TCs])):
            coverage_total += mapped_sections[iS][_TCs][j]["covered"]
        for j in range(len(mapped_sections[iS][_TSs])):
            coverage_total += mapped_sections[iS][_TSs][j]["covered"]
        for j in range(len(mapped_sections[iS][_Js])):
            coverage_total += mapped_sections[iS][_Js][j]["covered"]
        for j in range(len(mapped_sections[iS][_Ds])):
            coverage_total += mapped_sections[iS][_Ds][j]["covered"]
        mapped_sections[iS]["covered"] = min(max(coverage_total, 0), 100)

    # Remove Section with section: \n and no work items
    mapped_sections = [x for x in mapped_sections if not x["delete"]]
    return sorted(mapped_sections, key=lambda k: k["offset"])


def check_fields_in_request(fields, request, allow_empty_string=True):
    for field in fields:
        if field not in request.keys():
            print(f"field: {field} not in request: {request.keys()}")
            return False
        else:
            if allow_empty_string:
                pass
            else:
                if not str(request[field]):
                    print(f"field {field} is empty")
                    return False
    return True


def get_query_string_args(args):
    db = args.get("db", default="head", type=str)
    limit = args.get("limit", default="", type=str)
    order_by = args.get("order_by", default="", type=str)
    order_how = args.get("order_how", default="", type=str)

    permitted_keys = [
        "api-id",
        "artifact",
        "id",
        "library",
        "mapped_to_type",
        "mapped_to_id",
        "mode",
        "parent_id",
        "parent_table",
        "plugin",
        "relation_id",
        "search",
        "token",
        "url",
        "user-id",
        "work_item_type",
        "page",
        "per_page",
        "preset",
        "job",
        "stage",
        "ref",
        "params",
    ]

    ret = {"db": db, "limit": limit, "order_by": order_by, "order_how": order_how}

    i = 1
    while True:
        if args.get(f"field{i}") and args.get(f"filter{i}"):
            ret[f"field{i}"] = args.get(f"field{i}")
            ret[f"filter{i}"] = args.get(f"filter{i}")
            i = i + 1
        else:
            break

    if "join" in args.keys() and "join_id" in args.keys():
        ret["join"] = args.get("join")
        ret["join_id"] = args.get("join_id")

    for k in permitted_keys:
        if k in args.keys():
            ret[k] = args.get(k)

    return ret


def get_sw_requirement_children(_dbi, _srm):
    """ """
    undesired_keys = []

    mapping_field_id = f"{_srm['__tablename__']}_id"

    tmp = _srm

    # Indirect SwRequirement
    ind_sr_query = _dbi.session.query(SwRequirementSwRequirementModel).filter(
        getattr(SwRequirementSwRequirementModel, mapping_field_id) == _srm["relation_id"]
    )
    ind_sr = ind_sr_query.all()

    tmp[_SRs] = [get_dict_without_keys(x.as_dict(db_session=_dbi.session), undesired_keys + ["api"]) for x in ind_sr]

    for iSR in range(len(tmp[_SRs])):
        if "indirect_sw_requirement" in tmp[_SRs][iSR].keys():
            tmp[_SRs][iSR]["parent_mapping_type"] = "sw_requirement_mapping_sw_requirement"
        else:
            tmp[_SRs][iSR]["parent_mapping_type"] = "sw_requirement_mapping_api"

    # Indirect Test Specifications
    ind_ts = (
        _dbi.session.query(SwRequirementTestSpecificationModel)
        .filter(getattr(SwRequirementTestSpecificationModel, mapping_field_id) == _srm["relation_id"])
        .all()
    )
    tmp[_TSs] = [get_dict_without_keys(x.as_dict(db_session=_dbi.session), undesired_keys + ["api"]) for x in ind_ts]

    for iTS in range(len(tmp[_TSs])):
        # Indirect Test Cases
        curr_srts_id = tmp[_TSs][iTS]["relation_id"]
        ind_tc = (
            _dbi.session.query(TestSpecificationTestCaseModel)
            .filter(TestSpecificationTestCaseModel.test_specification_mapping_sw_requirement_id == curr_srts_id)
            .all()
        )

        tmp[_TSs][iTS][_TS][_TCs] = [
            get_dict_without_keys(x.as_dict(db_session=_dbi.session), undesired_keys + ["api"]) for x in ind_tc
        ]

    # Indirect Test Cases
    ind_tc = (
        _dbi.session.query(SwRequirementTestCaseModel)
        .filter(getattr(SwRequirementTestCaseModel, mapping_field_id) == _srm["relation_id"])
        .all()
    )
    tmp[_TCs] = [
        get_dict_without_keys(
            x.as_dict(db_session=_dbi.session), undesired_keys + ["api", "sw_requirement_mapping_api"]
        )
        for x in ind_tc
    ]

    # Recursive updating of nested SwRequirements
    for iNSR in range(len(tmp[_SRs])):
        tmp[_SRs][iNSR] = get_sw_requirement_children(_dbi, tmp[_SRs][iNSR])

    return tmp


def get_api_sw_requirements_mapping_sections(dbi, api):
    api_specification = get_api_specification(api.raw_specification_url)
    if api_specification is None:
        api_specification = (
            "WARNING: Unable to load the Reference Document. "
            "Please check the url/path value in the Software Component properties"
            " and that the file still exists in the expected location."
        )

    sr = (
        dbi.session.query(ApiSwRequirementModel)
        .filter(ApiSwRequirementModel.api_id == api.id)
        .order_by(ApiSwRequirementModel.offset.asc())
        .all()
    )
    sr_mapping = [x.as_dict(db_session=dbi.session) for x in sr]

    documents = (
        dbi.session.query(ApiDocumentModel)
        .filter(ApiDocumentModel.api_id == api.id)
        .order_by(ApiDocumentModel.offset.asc())
        .all()
    )
    documents_mapping = [x.as_dict(db_session=dbi.session) for x in documents]

    justifications = (
        dbi.session.query(ApiJustificationModel)
        .filter(ApiJustificationModel.api_id == api.id)
        .order_by(ApiJustificationModel.offset.asc())
        .all()
    )
    justifications_mapping = [x.as_dict(db_session=dbi.session) for x in justifications]

    mapping = {_A: api.as_dict(), _SRs: sr_mapping, _Js: justifications_mapping, _Ds: documents_mapping}

    for iType in [_SRs, _Js, _Ds]:
        for iMapping in range(len(mapping[iType])):
            current_offset = mapping[iType][iMapping]["offset"]
            current_section = mapping[iType][iMapping]["section"]
            mapping[iType][iMapping]["match"] = (
                api_specification[current_offset : current_offset + len(current_section)] == current_section
            )

    mapped_sections = get_split_sections(api_specification, mapping, [_SR, _J, _D])
    unmapped_sections = [x for x in mapping[_SRs] if not x["match"]]
    unmapped_sections += [x for x in mapping[_Js] if not x["match"]]
    unmapped_sections += [x for x in mapping[_Ds] if not x["match"]]

    for iMS in range(len(mapped_sections)):
        for iSR in range(len(mapped_sections[iMS][_SRs])):
            children_data = get_sw_requirement_children(dbi, mapped_sections[iMS][_SRs][iSR])
            mapped_sections[iMS][_SRs][iSR] = children_data

    ret = {"mapped": mapped_sections, "unmapped": unmapped_sections}

    return ret


def check_direct_work_items_against_another_spec_file(db_session, spec, api):
    ret = {
        "sw-requirements": {"ok": [], "ko": [], "warning": []},
        "test-specifications": {"ok": [], "ko": [], "warning": []},
        "test-cases": {"ok": [], "ko": [], "warning": []},
        "justifications": {"ok": [], "ko": [], "warning": []},
        "documents": {"ok": [], "ko": [], "warning": []},
    }

    if not spec:
        return ret

    # ApiSwRequirement
    api_srs = db_session.query(ApiSwRequirementModel).filter(ApiSwRequirementModel.api_id == api.id).all()
    for api_sr in api_srs:
        if api_sr.section in spec:
            if spec.index(api_sr.section) == api_sr.offset:
                ret["sw-requirements"]["ok"].append({"id": api_sr.id, "title": api_sr.sw_requirement.title})
            else:
                ret["sw-requirements"]["warning"].append(
                    {
                        "id": api_sr.id,
                        "old-offset": api_sr.offset,
                        "new-offset": spec.index(api_sr.section),
                        "title": api_sr.sw_requirement.title,
                    }
                )
        else:
            ret["sw-requirements"]["ko"].append({"id": api_sr.id, "title": api_sr.sw_requirement.title})

    # ApiTestSpecification
    api_tss = db_session.query(ApiTestSpecificationModel).filter(ApiTestSpecificationModel.api_id == api.id).all()
    for api_ts in api_tss:
        if api_ts.section in spec:
            if spec.index(api_ts.section) == api_ts.offset:
                ret["test-specifications"]["ok"].append({"id": api_ts.id, "title": api_ts.test_specification.title})
            else:
                ret["test-specifications"]["warning"].append(
                    {
                        "id": api_ts.id,
                        "old-offset": api_ts.offset,
                        "new-offset": spec.index(api_ts.section),
                        "title": api_ts.test_specification.title,
                    }
                )
        else:
            ret["test-specifications"]["ko"].append({"id": api_ts.id, "title": api_ts.test_specification.title})

    # ApiTestCase
    api_tcs = db_session.query(ApiTestCaseModel).filter(ApiTestCaseModel.api_id == api.id).all()
    for api_tc in api_tcs:
        if api_tc.section in spec:
            if spec.index(api_tc.section) == api_tc.offset:
                ret["test-cases"]["ok"].append({"id": api_tc.id, "title": api_tc.test_case.title})
            else:
                ret["test-cases"]["warning"].append(
                    {
                        "id": api_tc.id,
                        "old-offset": api_tc.offset,
                        "new-offset": spec.index(api_tc.section),
                        "title": api_tc.test_case.title,
                    }
                )
        else:
            ret["test-cases"]["ko"].append({"id": api_tc.id, "title": api_tc.test_case.title})

    # ApiJustification
    api_js = db_session.query(ApiJustificationModel).filter(ApiJustificationModel.api_id == api.id).all()
    for api_j in api_js:
        if api_j.section in spec:
            if spec.index(api_j.section) == api_j.offset:
                ret["justifications"]["ok"].append({"id": api_j.id, "title": api_j.justification.description})
            else:
                ret["justifications"]["warning"].append(
                    {
                        "id": api_j.id,
                        "old-offset": api_j.offset,
                        "new-offset": spec.index(api_j.section),
                        "title": api_j.justification.description,
                    }
                )
        else:
            ret["justifications"]["ko"].append({"id": api_j.id, "title": api_j.justification.description})

    # ApiDocument
    api_docs = db_session.query(ApiDocumentModel).filter(ApiDocumentModel.api_id == api.id).all()
    for api_doc in api_docs:
        if api_doc.section in spec:
            if spec.index(api_doc.section) == api_doc.offset:
                ret["documents"]["ok"].append({"id": api_doc.id, "title": api_doc.document.title})
            else:
                ret["documents"]["warning"].append(
                    {
                        "id": api_doc.id,
                        "old-offset": api_doc.offset,
                        "new-offset": spec.index(api_doc.section),
                        "title": api_doc.document.title,
                    }
                )
        else:
            ret["documents"]["ko"].append({"id": api_doc.id, "title": api_doc.document.title})

    return ret


class Token:

    def filter(self, token):
        if token == app.secret_key:
            return True
        return False


def add_test_run_config(dbi, request_data, user):
    mandatory_fields = ["environment_vars", "git_repo_ref", "id", "plugin", "plugin_preset", "title"]
    tmt_mandatory_fields = ["context_vars", "provision_guest", "provision_guest_port", "provision_type", "ssh_key"]
    gitlab_ci_mandatory_fields = ["job", "private_token", "project_id", "stage", "trigger_token", "url"]
    github_actions_mandatory_fields = ["job", "private_token", "url", "workflow_id"]
    kernel_ci_mandatory_fields = []
    testing_farm_mandatory_fields = ["arch", "compose", "private_token", "url"]

    if not check_fields_in_request(mandatory_fields, request_data):
        return f"{BAD_REQUEST_MESSAGE} Miss mandatory fields.", BAD_REQUEST_STATUS

    if request_data["id"] not in ["", 0]:
        if str(request_data["id"]).strip().isnumeric():
            testrun_config_id = int(str(request_data["id"]))
            try:
                existing_config = (
                    dbi.session.query(TestRunConfigModel).filter(TestRunConfigModel.id == testrun_config_id).one()
                )
                return existing_config, OK_STATUS
            except NoResultFound:
                return f"{BAD_REQUEST_MESSAGE} Unable to find the Test Run Configuration.", BAD_REQUEST_STATUS
        else:
            return f"{BAD_REQUEST_MESSAGE} Test Run Configuration ID is not valid.", BAD_REQUEST_STATUS

    if request_data["plugin"] not in TestRunner.test_run_plugin_models.keys():
        if not check_fields_in_request(tmt_mandatory_fields, request_data):
            return f"{BAD_REQUEST_MESSAGE} Plugin not supported.", BAD_REQUEST_STATUS

    # Config
    config_title = str(request_data["title"]).strip()
    environment_vars = str(request_data["environment_vars"]).strip()
    git_repo_ref = str(request_data["git_repo_ref"]).strip()
    plugin = str(request_data["plugin"]).strip()
    plugin_preset = str(request_data["plugin_preset"]).strip()
    plugin_vars = ""
    context_vars = ""
    provision_type = ""
    provision_guest = ""
    provision_guest_port = ""
    ssh_key = None

    # Check mandatory fields
    if config_title == "":
        return f"{BAD_REQUEST_MESSAGE} Empty Configuration Title.", BAD_REQUEST_STATUS

    if plugin == TestRunner.TMT:
        if not check_fields_in_request(tmt_mandatory_fields, request_data):
            return f"{BAD_REQUEST_MESSAGE} tmt miss mandatory fields.", BAD_REQUEST_STATUS

        context_vars = str(request_data["context_vars"]).strip()
        provision_type = str(request_data["provision_type"]).strip()
        provision_guest = str(request_data["provision_guest"]).strip()
        provision_guest_port = str(request_data["provision_guest_port"]).strip()
        ssh_key_id = request_data["ssh_key"]

        if not plugin_preset:
            if not provision_type:
                return f"{BAD_REQUEST_MESSAGE} tmt provision type not defined.", BAD_REQUEST_STATUS

            if provision_type == "connect":
                if provision_guest == "" or provision_guest_port == "" or ssh_key_id == "" or ssh_key_id == "0":
                    return f"{BAD_REQUEST_MESSAGE} tmt provision configuration is not correct.", BAD_REQUEST_STATUS

                try:
                    ssh_key = (
                        dbi.session.query(SshKeyModel)
                        .filter(SshKeyModel.id == ssh_key_id, SshKeyModel.created_by_id == user.id)
                        .one()
                    )
                except NoResultFound:
                    return f"{BAD_REQUEST_MESSAGE} Unable to find the SSH Key.", BAD_REQUEST_STATUS

    elif plugin == TestRunner.GITLAB_CI:
        if not check_fields_in_request(gitlab_ci_mandatory_fields, request_data):
            return f"{BAD_REQUEST_MESSAGE} GitlabCI miss mandatory fields.", BAD_REQUEST_STATUS
        plugin_vars += ";".join(
            [f"{field}={str(request_data[field]).strip()}" for field in gitlab_ci_mandatory_fields]
        )
    elif plugin == TestRunner.GITHUB_ACTIONS:
        if not check_fields_in_request(github_actions_mandatory_fields, request_data):
            return f"{BAD_REQUEST_MESSAGE} Github Actions miss mandatory fields.", BAD_REQUEST_STATUS
        plugin_vars += ";".join(
            [f"{field}={str(request_data[field]).strip()}" for field in github_actions_mandatory_fields]
        )
    elif plugin == TestRunner.KERNEL_CI:
        if not check_fields_in_request(kernel_ci_mandatory_fields, request_data):
            return f"{BAD_REQUEST_MESSAGE} KernelCI miss mandatory fields.", BAD_REQUEST_STATUS
        plugin_vars += ";".join(
            [f"{field}={str(request_data[field]).strip()}" for field in kernel_ci_mandatory_fields]
        )
    elif plugin == TestRunner.TESTING_FARM:
        if not check_fields_in_request(testing_farm_mandatory_fields, request_data):
            return f"{BAD_REQUEST_MESSAGE} Testing Farm miss mandatory fields.", BAD_REQUEST_STATUS
        context_vars = str(request_data["context_vars"]).strip()
        plugin_vars += ";".join(
            [f"{field}={str(request_data[field]).strip()}" for field in testing_farm_mandatory_fields]
        )

    test_config = TestRunConfigModel(
        plugin,
        plugin_preset,
        plugin_vars,
        config_title,
        git_repo_ref,
        context_vars,
        environment_vars,
        provision_type,
        provision_guest,
        provision_guest_port,
        ssh_key,
        user,
    )
    dbi.session.add(test_config)
    dbi.session.commit()
    return test_config, CREATED_STATUS


tokenManager = Token()


class SPDXLibrary(Resource):
    fields = ["library"]

    def get(self):
        request_data = request.args

        if not check_fields_in_request(self.fields, request_data):
            return BAD_REQUEST_MESSAGE, BAD_REQUEST_STATUS

        dbi = db_orm.DbInterface(get_db())

        query = dbi.session.query(ApiModel).filter(ApiModel.library == request_data["library"])
        apis = query.all()
        if not apis:
            return f"Nothing to export, no apis found as part of library {request_data['library']}", 400

        spdxManager = SPDXManager(request_data["library"])
        for api in apis:
            spdxManager.add_api_to_export(api)
        dt = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

        spdx_public_path = os.path.join(currentdir, "public", "spdx_export")
        spdx_filename = f"{request_data['library']}-{dt}"
        spdx_filepath = os.path.join(spdx_public_path, spdx_filename)
        if not os.path.exists(spdx_public_path):
            os.makedirs(spdx_public_path, exist_ok=True)

        spdxManager.export(spdx_filepath)

        return send_file(f"{spdx_filepath}.jsonld")


class SPDXApi(Resource):
    fields = ["id"]

    def get(self):
        request_data = request.args

        if not check_fields_in_request(self.fields, request_data):
            return BAD_REQUEST_MESSAGE, BAD_REQUEST_STATUS

        dbi = db_orm.DbInterface(get_db())

        query = dbi.session.query(ApiModel).filter(ApiModel.id == request_data["id"])
        try:
            api = query.one()
        except NoResultFound:
            if not api:
                return f"Nothing to export, no apis found with id {request_data['id']}", 400

        spdxManager = SPDXManager(api.library)
        spdxManager.add_api_to_export(api)
        dt = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

        spdx_public_path = os.path.join(currentdir, "public", "spdx_export")
        spdx_filename = f"{api.library}-{api.id}-{dt}"
        spdx_filepath = os.path.join(spdx_public_path, spdx_filename)
        if not os.path.exists(spdx_public_path):
            os.makedirs(spdx_public_path, exist_ok=True)

        spdxManager.export(spdx_filepath)

        return send_file(f"{spdx_filepath}.jsonld")


class Comment(Resource):
    fields = ["comment", "parent_table", "user-id", "token"]

    def get(self):
        # mandatory_fields = ["parent_table", "parent_id"]
        args = get_query_string_args(request.args)

        if "parent_table" not in args.keys() or "parent_id" not in args.keys():
            return "bad request!", 400

        dbi = db_orm.DbInterface(get_db())

        query = (
            dbi.session.query(CommentModel)
            .filter(CommentModel.parent_table == args["parent_table"])
            .filter(CommentModel.parent_id == args["parent_id"])
        )

        if "search" in args:
            query = query.filter(
                or_(
                    CommentModel.comment.like(f'%{args["search"]}%'),
                )
            )

        query = query.order_by(CommentModel.created_at.asc())
        comments = [c.as_dict() for c in query.all()]
        return comments

    def post(self):
        request_data = request.get_json(force=True)

        if not check_fields_in_request(self.fields, request_data):
            return "bad request!", 400

        dbi = db_orm.DbInterface(get_db())

        # User
        user = get_active_user_from_request(request_data, dbi.session)
        if not isinstance(user, UserModel):
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        parent_table = request_data["parent_table"].strip()
        if parent_table == "":
            return "bad request!", 400

        parent_id = request_data["parent_id"]
        if parent_id == "":
            return "bad request!", 400

        comment = request_data["comment"].strip()
        if comment == "":
            return "bad request!", 400

        new_comment = CommentModel(parent_table, parent_id, user, comment)
        dbi.session.add(new_comment)

        dbi.session.commit()

        add_notification = True
        if parent_table == ApiSwRequirementModel.__tablename__:
            notification_obj = "Sw Requirement"
            query = dbi.session.query(ApiSwRequirementModel).filter(ApiSwRequirementModel.id == parent_id)
            query_obj = "asr"
        elif parent_table == ApiTestSpecificationModel.__tablename__:
            notification_obj = "Test Specification"
            query = dbi.session.query(ApiTestSpecificationModel).filter(ApiTestSpecificationModel.id == parent_id)
            query_obj = "atc"
        elif parent_table == ApiTestCaseModel.__tablename__:
            notification_obj = "Test Case"
            query = dbi.session.query(ApiTestCaseModel).filter(ApiTestCaseModel.id == parent_id)
            query_obj = "ats"
        elif parent_table == ApiJustificationModel.__tablename__:
            notification_obj = "Justification"
            query = dbi.session.query(ApiJustificationModel).filter(ApiJustificationModel.id == parent_id)
            query_obj = "aj"
        else:
            add_notification = False

        if add_notification:
            try:
                mapping = query.one()
            except NoResultFound:
                add_notification = False

        # Add Notifications
        if add_notification:
            notification = (
                f"{user.email} added a Comment to {notification_obj} "
                f"mapped to "
                f"{mapping.api.api} as part of the library {mapping.api.library}"
            )
            notifications = NotificationModel(
                mapping.api,
                NOTIFICATION_CATEGORY_NEW,
                f"New Comment from {user.email}",
                notification,
                str(user.id),
                f"/mapping/{mapping.api.id}?{query_obj}={parent_id}&view=comments",
            )
            dbi.session.add(notifications)
            dbi.session.commit()

        return new_comment.as_dict()


class CheckSpecification(Resource):
    fields = ["id"]

    def get(self):

        args = get_query_string_args(request.args)

        if not check_fields_in_request(self.fields, args):
            return "bad request!", 400

        dbi = db_orm.DbInterface(get_db())

        query = dbi.session.query(ApiModel).filter(ApiModel.id == args["id"])
        apis = query.all()

        if len(apis) != 1:
            return "Unable to find the api", 400

        api = apis[0]

        if "url" in args.keys():
            spec = get_api_specification(request.args["url"])
        else:
            spec = get_api_specification(api.raw_specification_url)

        ret = check_direct_work_items_against_another_spec_file(dbi.session, spec, api)
        return ret


class Document(Resource):
    def get(self):
        args = get_query_string_args(request.args)
        dbi = db_orm.DbInterface(get_db())
        query = dbi.session.query(DocumentModel)
        query = filter_query(query, args, DocumentModel, False)
        docs = [doc.as_dict() for doc in query.all()]
        return docs


class RemoteDocument(Resource):
    def get(self):
        args = get_query_string_args(request.args)
        ret = {}
        if "api-id" not in args.keys():
            return {}

        if "id" not in args.keys() and "url" not in args.keys():
            return {}

        dbi = db_orm.DbInterface(get_db())

        # User permission
        user = get_active_user_from_request(args, dbi.session)
        if not isinstance(user, UserModel):
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        api = get_api_from_request(args, dbi.session)
        if not api:
            return NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

        # Permissions
        permissions = get_api_user_permissions(api, user.id, user.role, dbi.session)
        if "r" not in permissions:
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        if "url" in args.keys():
            ret = {"url": args["url"], "valid": None, "content": get_api_specification(args["url"])}  # not evaluated
        elif "id" in args.keys():
            try:
                document = dbi.session.query(DocumentModel).filter(DocumentModel.id == args["id"]).one()
                content = get_api_specification(document.url)
                valid = False
                if content:
                    valid = content[document.offset : document.offset + len(document.section)] == document.section
                if int(valid) == 0 and document.valid == 1:
                    document.valid = int(valid)
                    dbi.session.add(document)

                    # Add Notifications
                    notification = (
                        f"Document {document.title} "
                        f"mapped to "
                        f"{api.api} as part of the library {api.library} it is not valid anymore"
                    )
                    notifications = NotificationModel(
                        api,
                        NOTIFICATION_CATEGORY_EDIT,
                        f"Document {document.title} it is not valid anymore",
                        notification,
                        "",
                        f"/mapping/{api.id}",
                    )
                    dbi.session.add(notifications)
                    dbi.session.commit()

            except NoResultFound:
                return f"Unable to find the Document id {id}", 400
            ret = {"id": args["id"], "content": content, "valid": valid}

        return ret


class FixNewSpecificationWarnings(Resource):
    fields = ["id"]

    def get(self):
        args = get_query_string_args(request.args)

        if not check_fields_in_request(self.fields, args):
            return "bad request!", 400

        dbi = db_orm.DbInterface(get_db())

        query = dbi.session.query(ApiModel).filter(ApiModel.id == args["id"])
        apis = query.all()

        if len(apis) != 1:
            return "Unable to find the api", 400

        api = apis[0]

        spec = get_api_specification(api.raw_specification_url)

        analysis = check_direct_work_items_against_another_spec_file(dbi.session, spec, api)

        # ApiSwRequirements
        for i in range(len(analysis["sw-requirements"]["warning"])):
            sr_all = (
                dbi.session.query(ApiSwRequirementModel)
                .filter(ApiSwRequirementModel.id == analysis["sw-requirements"]["warning"][i]["id"])
                .all()
            )
            if len(sr_all) == 1:
                sr_all[0].offset = analysis["sw-requirements"]["warning"][i]["new-offset"]
                dbi.session.commit()

        # ApiTestSpecification
        for i in range(len(analysis["test-specifications"]["warning"])):
            ts_all = (
                dbi.session.query(ApiTestSpecificationModel)
                .filter(ApiTestSpecificationModel.id == analysis["test-specifications"]["warning"][i]["id"])
                .all()
            )
            if len(ts_all) == 1:
                ts_all[0].offset = analysis["test-specifications"]["warning"][i]["new-offset"]
                dbi.session.commit()

        # ApiTestCase
        for i in range(len(analysis["test-cases"]["warning"])):
            tc_all = (
                dbi.session.query(ApiTestCaseModel)
                .filter(ApiTestCaseModel.id == analysis["test-cases"]["warning"][i]["id"])
                .all()
            )
            if len(tc_all) == 1:
                tc_all[0].offset = analysis["test-cases"]["warning"][i]["new-offset"]
                dbi.session.commit()

        # ApiJustification
        for i in range(len(analysis["justifications"]["warning"])):
            j_all = (
                dbi.session.query(ApiJustificationModel)
                .filter(ApiJustificationModel.id == analysis["justifications"]["warning"][i]["id"])
                .all()
            )
            if len(j_all) == 1:
                j_all[0].offset = analysis["justifications"]["warning"][i]["new-offset"]
                dbi.session.commit()

        # ApiDocument
        for i in range(len(analysis["documents"]["warning"])):
            doc_all = (
                dbi.session.query(ApiDocumentModel)
                .filter(ApiDocumentModel.id == analysis["documents"]["warning"][i]["id"])
                .all()
            )
            if len(doc_all) == 1:
                doc_all[0].offset = analysis["documents"]["warning"][i]["new-offset"]
                dbi.session.commit()

        return True


class Api(Resource):
    fields = get_model_editable_fields(ApiModel, False)
    fields.remove("last_coverage")
    fields_hashes = [x.replace("_", "-") for x in fields]

    def get(self):
        apis_dict = []
        args = get_query_string_args(request.args)
        dbi = db_orm.DbInterface(get_db())
        user_id = 0

        # User permission
        user = get_active_user_from_request(args, dbi.session)
        if isinstance(user, UserModel):
            user_id = user.id
            user_role = user.role
            if not user.api_notifications:
                user_api_notifications = []
            else:
                user_api_notifications = user.api_notifications.replace(" ", "").split(",")
                user_api_notifications = [int(x) for x in user_api_notifications]  # Need list of int
        else:
            user_id = 0
            user_role = ''
            user_api_notifications = []

        query = dbi.session.query(ApiModel)
        query = filter_query(query, args, ApiModel, False)
        query = query.order_by(and_(ApiModel.api, ApiModel.library_version))

        # Pagination
        page = 1
        per_page = 10
        if "page" in args.keys():
            if str(request.args["page"]).isnumeric():
                page = max(int(args["page"]), 1)
                if "per_page" in args.keys():
                    if per_page in [5, 10, 20, 40, "5", "10", "20", "40"]:
                        per_page = int(args["per_page"])

        count = query.count()
        apis = query.offset((page - 1) * per_page).limit(per_page).all()
        page_count = math.ceil(count / per_page)

        if len(apis):
            apis_dict = [x.as_dict() for x in apis]

        for iApi in range(len(apis_dict)):
            apis_dict[iApi]["covered"] = apis_dict[iApi]["last_coverage"]

            # Permissions
            permissions = get_api_user_permissions(apis[iApi], user_id, user_role, dbi.session)
            apis_dict[iApi]["permissions"] = permissions

        # Filter api based on read permission
        apis_dict = [api_dict for api_dict in apis_dict if "r" in api_dict["permissions"]]

        # Populate user notifications settings
        for i in range(len(apis_dict)):
            if apis_dict[i]["id"] in user_api_notifications:
                apis_dict[i]["notifications"] = 1
            else:
                apis_dict[i]["notifications"] = 0

        ret = {
            "apis": sorted(apis_dict, key=lambda api: (api["api"], api["library_version"])),
            "current_page": page,
            "page_count": page_count,
            "per_page": per_page,
            "count": count,
        }

        return ret

    def post(self):
        request_data = request.get_json(force=True)
        post_fields = self.fields_hashes.copy()
        post_fields.append("action")
        post_fields.remove("default-view")
        if not check_fields_in_request(post_fields, request_data):
            return "bad request!", 400

        dbi = db_orm.DbInterface(get_db())

        # Find api
        api = (
            dbi.session.query(ApiModel)
            .filter(ApiModel.api == request_data["api"])
            .filter(ApiModel.library == request_data["library"])
            .filter(ApiModel.library_version == request_data["library-version"])
            .all()
        )

        if len(api) > 0:
            return "Api is already in the db for the selected library", 409

        user = get_active_user_from_request(request_data, dbi.session)
        if not isinstance(user, UserModel):
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS
        if user.role not in USER_ROLES_WRITE_PERMISSIONS:
            return "Current user have no writing permissions", 401

        if request_data["action"] == "fork":
            source_api = dbi.session.query(ApiModel).filter(ApiModel.id == request_data["api-id"]).all()
            if len(source_api) != 1:
                return "Source Api not found", 409
            if source_api[0].api != request_data["api"]:
                return "Source Api name differ from new Api name", 409
            if source_api[0].library != request_data["library"]:
                return "Source Api library differ from new Api library", 409

        new_api = ApiModel(
            request_data["api"],
            request_data["library"],
            request_data["library-version"],
            request_data["raw-specification-url"],
            request_data["category"],
            "",  # Checksum
            request_data["implementation-file"],
            request_data["implementation-file-from-row"],
            request_data["implementation-file-to-row"],
            request_data["tags"],
            user,
        )

        dbi.session.add(new_api)
        dbi.session.commit()  # TO have the id of the new api

        # Add Notifications
        notification = (
            f"{user.email} added the sw component " f"{new_api.api} as part of the library {new_api.library}"
        )
        notifications = NotificationModel(
            new_api,
            NOTIFICATION_CATEGORY_NEW,
            f"{new_api.api} has been created",
            notification,
            str(user.id),
            f"/?currentLibrary={new_api.library}",
        )
        dbi.session.add(notifications)

        if request_data["action"] == "fork":
            dbi.session.commit()  # to read the id

            # Clone ApiJustification
            api_justifications = (
                dbi.session.query(ApiJustificationModel).filter(ApiJustificationModel.api_id == source_api[0].id).all()
            )
            for api_justification in api_justifications:
                tmp = ApiJustificationModel(
                    new_api,
                    api_justification.justification,
                    api_justification.section,
                    api_justification.offset,
                    api_justification.coverage,
                    user,
                )
                dbi.session.add(tmp)

            # Clone ApiDocument
            api_documents = (
                dbi.session.query(ApiDocumentModel).filter(ApiDocumentModel.api_id == source_api[0].id).all()
            )
            for api_document in api_documents:
                tmp = ApiDocumentModel(
                    new_api,
                    api_document.document,
                    api_document.section,
                    api_document.offset,
                    api_document.coverage,
                    user,
                )
                dbi.session.add(tmp)

            # Clone ApiSwRequirement
            api_sw_requirements = (
                dbi.session.query(ApiSwRequirementModel).filter(ApiSwRequirementModel.api_id == source_api[0].id).all()
            )
            for api_sw_requirement in api_sw_requirements:
                tmp = ApiSwRequirementModel(
                    new_api,
                    api_sw_requirement.sw_requirement,
                    api_sw_requirement.section,
                    api_sw_requirement.offset,
                    api_sw_requirement.coverage,
                    user,
                )
                dbi.session.add(tmp)

            # Clone ApiTestSpecification
            api_test_specifications = (
                dbi.session.query(ApiTestSpecificationModel)
                .filter(ApiTestSpecificationModel.api_id == source_api[0].id)
                .all()
            )
            for api_test_specification in api_test_specifications:
                tmp = ApiTestSpecificationModel(
                    new_api,
                    api_test_specification.test_specification,
                    api_test_specification.section,
                    api_test_specification.offset,
                    api_test_specification.coverage,
                    user,
                )
                dbi.session.add(tmp)

            # Clone ApiTestCase
            api_test_cases = (
                dbi.session.query(ApiTestCaseModel).filter(ApiTestCaseModel.api_id == source_api[0].id).all()
            )
            for api_test_case in api_test_cases:
                tmp = ApiTestCaseModel(
                    new_api,
                    api_test_case.test_case,
                    api_test_case.section,
                    api_test_case.offset,
                    api_test_case.coverage,
                    user,
                )
                dbi.session.add(tmp)

        dbi.session.commit()
        return new_api.as_dict()

    def put(self):
        request_data = request.get_json(force=True)
        put_fields = self.fields_hashes.copy()
        put_fields.append("api-id")
        if not check_fields_in_request(put_fields, request_data):
            return BAD_REQUEST_MESSAGE, BAD_REQUEST_STATUS

        dbi = db_orm.DbInterface(get_db())

        # Find api
        api = get_api_from_request(request_data, dbi.session)

        if not api:
            return NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

        # User permission
        user = get_active_user_from_request(request_data, dbi.session)
        if not isinstance(user, UserModel):
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        # Permissions
        permissions = get_api_user_permissions(api, user.id, user.role, dbi.session)
        if "e" not in permissions or user.role not in USER_ROLES_EDIT_PERMISSIONS:
            return FORBIDDEN_MESSAGE, FORBIDDEN_STATUS

        # Check that the new api+library+library_version is not already in the db
        same_existing_apis = (
            dbi.session.query(ApiModel)
            .filter(ApiModel.api == request_data["api"])
            .filter(ApiModel.library == request_data["library"])
            .filter(ApiModel.library == request_data["library-version"])
            .filter(ApiModel.id != request_data["api-id"])
            .all()
        )

        if len(same_existing_apis) > 0:
            return "An Api with selected name and library already exist in the db", 409

        api_modified = False
        for field in self.fields:
            if field.replace("_", "-") in request_data.keys():
                if getattr(api, field) != request_data[field.replace("_", "-")]:
                    api_modified = True
                    setattr(api, field, request_data[field.replace("_", "-")])

        if api_modified:
            api.edited_by_id = user.id

            # Add Notifications
            notification = f"{user.email} modified sw component " f"{api.api} as part of the library {api.library}"
            notifications = NotificationModel(
                api,
                NOTIFICATION_CATEGORY_EDIT,
                f"{api.api} has been modified",
                notification,
                str(user.id),
                f"/?currentLibrary={api.library}",
            )
            dbi.session.add(notifications)

        dbi.session.commit()
        return api.as_dict()

    def delete(self):
        request_data = request.get_json(force=True)

        delete_fields = self.fields_hashes.copy()
        delete_fields.append("api-id")
        if not check_fields_in_request(delete_fields, request_data):
            return "bad request!", 400

        dbi = db_orm.DbInterface(get_db())

        # Find api
        apis = (
            dbi.session.query(ApiModel)
            .filter(ApiModel.id == request_data["api-id"])
            .filter(ApiModel.api == request_data["api"])
            .filter(ApiModel.library == request_data["library"])
            .filter(ApiModel.library_version == request_data["library-version"])
            .one()
        )

        if len(apis) != 1:
            return "Api not found", 400

        api = apis[0]

        # User permission
        user = get_active_user_from_request(request_data, dbi.session)
        if not isinstance(user, UserModel):
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        # Permissions
        permissions = get_api_user_permissions(api, user.id, user.role, dbi.session)
        if "e" not in permissions or user.role not in USER_ROLES_EDIT_PERMISSIONS:
            return FORBIDDEN_MESSAGE, FORBIDDEN_STATUS

        justifications_mapping_api = (
            dbi.session.query(ApiJustificationModel).filter(ApiJustificationModel.api_id == api.id).all()
        )

        sw_requirements_mapping_api = (
            dbi.session.query(ApiSwRequirementModel).filter(ApiSwRequirementModel.api_id == api.id).all()
        )

        test_specifications_mapping_api = (
            dbi.session.query(ApiTestSpecificationModel).filter(ApiTestSpecificationModel.api_id == api.id).all()
        )

        test_cases_mapping_api = dbi.session.query(ApiTestCaseModel).filter(ApiTestCaseModel.api_id == api.id).all()

        for j in justifications_mapping_api:
            dbi.session.delete(j)

        for s in sw_requirements_mapping_api:
            dbi.session.delete(s)

        for ts in test_specifications_mapping_api:
            dbi.session.delete(ts)

        for tc in test_cases_mapping_api:
            dbi.session.delete(tc)

        dbi.session.delete(api)
        dbi.session.commit()

        # Add Notifications
        notification = f"{user.email} deleted sw component " f"{api.api} as part of the library {api.library}"
        notifications = NotificationModel(
            api,
            NOTIFICATION_CATEGORY_DELETE,
            f"{api.api} has been deleted",
            notification,
            str(user.id),
            f"/?currentLibrary={api.library}",
        )
        dbi.session.add(notifications)
        dbi.session.commit()
        return True


class ApiLastCoverage(Resource):
    def put(self):
        """
        edit api last_coverage field
        """
        request_data = request.get_json(force=True)
        edit_field = "last_coverage"
        put_fields = ["api-id", edit_field.replace("_", "-")]

        if not check_fields_in_request(put_fields, request_data):
            return BAD_REQUEST_MESSAGE, BAD_REQUEST_STATUS

        dbi = db_orm.DbInterface(get_db())

        # Find api
        api = get_api_from_request(request_data, dbi.session)

        if not api:
            return NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

        # User permission
        user = get_active_user_from_request(request_data, dbi.session)
        if not isinstance(user, UserModel):
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        # Permissions
        permissions = get_api_user_permissions(api, user.id, user.role, dbi.session)
        if "r" not in permissions:
            return FORBIDDEN_MESSAGE, FORBIDDEN_STATUS

        api_modified = False
        if getattr(api, edit_field) != request_data[edit_field.replace("_", "-")]:
            api_modified = True
            setattr(api, edit_field, request_data[edit_field.replace("_", "-")])

        if api_modified:
            dbi.session.add(api)
            dbi.session.commit()

        return api.as_dict()


class ApiHistory(Resource):
    def get(self):
        args = get_query_string_args(request.args)

        if "api-id" not in args.keys():
            return []

        dbi = db_orm.DbInterface(get_db())

        _model = ApiModel
        _model_history = ApiHistoryModel
        _model_fields = _model.__table__.columns.keys()

        model_versions_query = (
            dbi.session.query(_model_history)
            .filter(_model_history.id == args["api-id"])
            .order_by(_model_history.version.asc())
        )
        staging_array = []
        ret = []

        # object dict
        for model_version in model_versions_query.all():
            obj = {
                "version": model_version.version,
                "type": "object",
                "created_at": datetime.datetime.strptime(str(model_version.created_at), "%Y-%m-%d %H:%M:%S.%f"),
            }

            for k in _model_fields:
                if k not in ["row_id", "version", "last_coverage", "created_at", "updated_at"]:
                    obj[k] = getattr(model_version, k)

            staging_array.append(obj)

        staging_array = sorted(staging_array, key=lambda d: (d["created_at"]))

        # get version object.mapping equal to 1.1
        first_found = False
        first_obj = {}
        for i in range(len(staging_array)):
            if staging_array[i]["version"] == 1 and staging_array[i]["type"] == "object":
                first_obj = staging_array[i]
                first_found = True
                break

        if not first_found:
            return []

        ret.append(get_combined_history_object(first_obj, {}, _model_fields, []))

        for i in range(len(staging_array)):
            last_obj_version = int(ret[-1]["version"].split(".")[0])
            if staging_array[i]["type"] == "object" and staging_array[i]["version"] > last_obj_version:
                ret.append(get_combined_history_object(staging_array[i], ret[-1]["mapping"], _model_fields, []))

        ret = get_reduced_history_data(ret, _model_fields, [], dbi.session)

        for i in range(len(ret)):
            for permission_field in API_PERMISSION_FIELDS:
                if permission_field in ret[i]["object"].keys():
                    ret[i]["object"][permission_field] = ", ".join(
                        get_users_email_from_ids(ret[i]["object"][permission_field], dbi.session)
                    )
                if permission_field in ret[i]["mapping"].keys():
                    ret[i]["mapping"][permission_field] = ", ".join(
                        get_users_email_from_ids(ret[i]["mapping"][permission_field], dbi.session)
                    )

        ret = ret[::-1]
        return ret


class Library(Resource):

    def get(self):
        # args = get_query_string_args(request.args)
        dbi = db_orm.DbInterface(get_db())
        libraries = dbi.session.query(ApiModel.library).distinct().all()
        return sorted([x.library for x in libraries])


class ApiSpecification(Resource):
    def get(self):
        args = get_query_string_args(request.args)
        if "api-id" not in args.keys():
            return {}

        dbi = db_orm.DbInterface(get_db())

        # User
        user = get_active_user_from_request(args, dbi.session)
        if not isinstance(user, UserModel):
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        api = get_api_from_request(args, dbi.session)
        if not api:
            return NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

        spec = get_api_specification(api.raw_specification_url)

        # Permissions
        permissions = get_api_user_permissions(api, user.id, user.role, dbi.session)
        if "r" not in permissions:
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        ret = api.as_dict()
        ret["raw_specification"] = spec
        ret["permissions"] = permissions
        return ret


class ApiTestSpecificationsMapping(Resource):
    fields = ["api-id", "test-specification", "section", "coverage"]

    def get(self):
        args = get_query_string_args(request.args)
        if not check_fields_in_request(["api-id"], args):
            return "bad request!", 400

        undesired_keys = ["section", "offset"]

        dbi = db_orm.DbInterface(get_db())

        # User
        user = get_active_user_from_request(args, dbi.session)
        if not isinstance(user, UserModel):
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        # Find api
        api = get_api_from_request(args, dbi.session)
        if not api:
            return NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

        # Permissions
        permissions = get_api_user_permissions(api, user.id, user.role, dbi.session)
        if "r" not in permissions:
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        api_specification = get_api_specification(api.raw_specification_url)
        if api_specification is None:
            return []

        ts = (
            dbi.session.query(ApiTestSpecificationModel)
            .filter(ApiTestSpecificationModel.api_id == api.id)
            .order_by(ApiTestSpecificationModel.offset.asc())
            .all()
        )
        ts_mapping = [x.as_dict(db_session=dbi.session) for x in ts]

        documents = (
            dbi.session.query(ApiDocumentModel)
            .filter(ApiDocumentModel.api_id == api.id)
            .order_by(ApiDocumentModel.offset.asc())
            .all()
        )
        documents_mapping = [x.as_dict(db_session=dbi.session) for x in documents]

        justifications = (
            dbi.session.query(ApiJustificationModel)
            .filter(ApiJustificationModel.api_id == api.id)
            .order_by(ApiJustificationModel.offset.asc())
            .all()
        )
        justifications_mapping = [x.as_dict(db_session=dbi.session) for x in justifications]

        mapping = {_A: api.as_dict(), _TSs: ts_mapping, _Js: justifications_mapping, _Ds: documents_mapping}

        for iTS in range(len(mapping[_TSs])):
            # Indirect Test Cases
            curr_ats_id = mapping[_TSs][iTS]["relation_id"]

            ind_tc = (
                dbi.session.query(TestSpecificationTestCaseModel)
                .filter(TestSpecificationTestCaseModel.test_specification_mapping_api_id == curr_ats_id)
                .all()
            )
            mapping[_TSs][iTS][_TS][_TCs] = [
                get_dict_without_keys(x.as_dict(db_session=dbi.session), undesired_keys + ["api"]) for x in ind_tc
            ]

        for iType in [_TSs, _Js, _Ds]:
            for iMapping in range(len(mapping[iType])):
                current_offset = mapping[iType][iMapping]["offset"]
                current_section = mapping[iType][iMapping]["section"]
                mapping[iType][iMapping]["match"] = (
                    api_specification[current_offset : current_offset + len(current_section)] == current_section
                )

        mapped_sections = get_split_sections(api_specification, mapping, [_TS, _J, _D])
        unmapped_sections = [x for x in mapping[_TSs] if not x["match"]]
        unmapped_sections += [x for x in mapping[_Js] if not x["match"]]
        unmapped_sections += [x for x in mapping[_Ds] if not x["match"]]
        ret = {"mapped": mapped_sections, "unmapped": unmapped_sections}

        return ret

    def post(self):
        request_data = request.get_json(force=True)

        if not check_fields_in_request(self.fields, request_data):
            return "bad request!", 400

        dbi = db_orm.DbInterface(get_db())

        # User
        user = get_active_user_from_request(request_data, dbi.session)
        if not isinstance(user, UserModel):
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        # Find api
        api = get_api_from_request(request_data, dbi.session)
        if not api:
            return NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

        # Permissions
        permissions = get_api_user_permissions(api, user.id, user.role, dbi.session)
        if "w" not in permissions or user.role not in USER_ROLES_WRITE_PERMISSIONS:
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        section = request_data["section"]
        offset = request_data["offset"]
        coverage = request_data["coverage"]

        if "id" not in request_data["test-specification"].keys():
            # Create a new one
            # `status` field should be skipped because a default is assigned in the model
            for check_field in [x for x in TestSpecification.fields if x not in ["status"]]:
                if check_field.replace("_", "-") not in request_data["test-specification"].keys():
                    return "Bad request. Unconsistent data.", 400

            title = request_data["test-specification"]["title"]
            preconditions = request_data["test-specification"]["preconditions"]
            test_description = request_data["test-specification"]["test-description"]
            expected_behavior = request_data["test-specification"]["expected-behavior"]

            if (
                len(
                    dbi.session.query(TestSpecificationModel)
                    .filter(TestSpecificationModel.title == title)
                    .filter(TestSpecificationModel.preconditions == preconditions)
                    .filter(TestSpecificationModel.test_description == test_description)
                    .filter(TestSpecificationModel.expected_behavior == expected_behavior)
                    .all()
                )
                > 0
            ):
                return "Test Specification already associated to the selected api Specification section.", 409

            new_test_specification = TestSpecificationModel(
                title, preconditions, test_description, expected_behavior, user
            )
            new_test_specification_mapping_api = ApiTestSpecificationModel(
                api, new_test_specification, section, offset, coverage, user
            )

            dbi.session.add(new_test_specification)
            dbi.session.add(new_test_specification_mapping_api)

        else:
            id = request_data["test-specification"]["id"]
            if (
                len(
                    dbi.session.query(ApiTestSpecificationModel)
                    .filter(ApiTestSpecificationModel.api_id == api.id)
                    .filter(ApiTestSpecificationModel.test_specification_id == id)
                    .filter(ApiTestSpecificationModel.section == section)
                    .all()
                )
                > 0
            ):
                return "Test Specification already associated to the selected api Specification section.", 409

            try:
                existing_test_specification = (
                    dbi.session.query(TestSpecificationModel).filter(TestSpecificationModel.id == id).one()
                )
            except NoResultFound:
                return f"Unable to find the Test Specification id {id}", 400

            new_test_specification_mapping_api = ApiTestSpecificationModel(
                api, existing_test_specification, section, offset, coverage, user
            )
            dbi.session.add(new_test_specification_mapping_api)

        dbi.session.commit()  # To have the id

        # Add Notifications
        notification = (
            f"{user.email} added Test Specification "
            f"{new_test_specification_mapping_api.test_specification.id} "
            f"mapped to "
            f"{api.api} as part of the library {api.library}"
        )
        notifications = NotificationModel(
            api,
            NOTIFICATION_CATEGORY_NEW,
            f"{api.api} - Test Specification mapping " f"{new_test_specification_mapping_api.id} " f"has been added",
            notification,
            str(user.id),
            f"/mapping/{api.id}",
        )
        dbi.session.add(notifications)
        dbi.session.commit()
        return new_test_specification_mapping_api.as_dict()

    def put(self):
        request_data = request.get_json(force=True)

        if not check_fields_in_request(self.fields, request_data):
            return "bad request!", 400

        dbi = db_orm.DbInterface(get_db())

        # User
        user = get_active_user_from_request(request_data, dbi.session)
        if not isinstance(user, UserModel):
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        # Find api
        api = get_api_from_request(request_data, dbi.session)
        if not api:
            return NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

        # Permissions
        permissions = get_api_user_permissions(api, user.id, user.role, dbi.session)
        if "w" not in permissions or user.role not in USER_ROLES_WRITE_PERMISSIONS:
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        try:
            test_specification_mapping_api = (
                dbi.session.query(ApiTestSpecificationModel)
                .filter(ApiTestSpecificationModel.id == request_data["relation-id"])
                .one()
            )
        except NoResultFound:
            return f"Unable to find the Test Specification mapping to Api id {request_data['relation-id']}", 400

        test_specification = test_specification_mapping_api.test_specification

        # Update only modified fields
        modified_ts = False
        for field in TestSpecification.fields:
            if field.replace("_", "-") in request_data["test-specification"].keys():
                if getattr(test_specification, field) != request_data["test-specification"][field.replace("_", "-")]:
                    modified_ts = True
                    setattr(test_specification, field, request_data["test-specification"][field.replace("_", "-")])

        if modified_ts:
            setattr(test_specification, "edited_by_id", user.id)

        modified_tsa = False
        if test_specification_mapping_api.section != request_data["section"]:
            modified_tsa = True
            test_specification_mapping_api.section = request_data["section"]

        if test_specification_mapping_api.offset != request_data["offset"]:
            modified_tsa = True
            test_specification_mapping_api.offset = request_data["offset"]

        if test_specification_mapping_api.coverage != int(request_data["coverage"]):
            modified_tsa = True
            test_specification_mapping_api.coverage = int(request_data["coverage"])

        if modified_tsa:
            test_specification_mapping_api.edited_by_id = user.id

        dbi.session.commit()

        if modified_ts or modified_tsa:
            # Add Notifications
            notification = (
                f"{user.email} modified test specification "
                f"{test_specification_mapping_api.test_specification.title}"
            )
            notifications = NotificationModel(
                api,
                NOTIFICATION_CATEGORY_EDIT,
                f"{api.api} - Test Specification has been modified",
                notification,
                str(user.id),
                f"/mapping/{api.id}",
            )
            dbi.session.add(notifications)
            dbi.session.commit()

        return test_specification_mapping_api.as_dict()

    def delete(self):
        request_data = request.get_json(force=True)

        if not check_fields_in_request(["relation-id", "api-id"], request_data):
            return "bad request!", 400

        dbi = db_orm.DbInterface(get_db())

        # User
        user = get_active_user_from_request(request_data, dbi.session)

        # Find api
        api = get_api_from_request(request_data, dbi.session)
        if not api:
            return NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

        # Permissions
        permissions = get_api_user_permissions(api, user.id, user.role, dbi.session)
        if "w" not in permissions or user.role not in USER_ROLES_WRITE_PERMISSIONS:
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        # check if api ...
        try:
            test_specification_mapping_api = (
                dbi.session.query(ApiTestSpecificationModel)
                .filter(ApiTestSpecificationModel.id == request_data["relation-id"])
                .one()
            )
        except NoResultFound:
            return f"Unable to find the Test Specification mapping to Api id {request_data['relation-id']}", 400

        if test_specification_mapping_api.api.id != api.id:
            return "bad request!", 401

        notification_ts_id = test_specification_mapping_api.test_specification.id
        notification_ts_title = test_specification_mapping_api.test_specification.title
        dbi.session.delete(test_specification_mapping_api)
        dbi.session.commit()

        # Add Notifications
        notification = f"{user.email} deleted test specification " f"{notification_ts_id} {notification_ts_title}"
        notifications = NotificationModel(
            api,
            NOTIFICATION_CATEGORY_DELETE,
            f"{api.api} - Test Specification has been deleted",
            notification,
            str(user.id),
            f"/mapping/{api.id}",
        )
        dbi.session.add(notifications)

        # TODO: Remove work item only user request to do
        """
        test_specification = test_specification_mapping_api.test_specification

        if len(dbi.session.query(ApiTestSpecificationModel).filter( \
                ApiTestSpecificationModel.api_id == api.id).filter( \
                ApiTestSpecificationModel.test_specification_id == test_specification.id).all()) == 0:
            dbi.session.delete(test_specification)
        """

        dbi.session.commit()
        return True


class ApiTestCasesMapping(Resource):
    fields = ["api-id", "test-case", "section", "coverage"]

    def get(self):
        args = get_query_string_args(request.args)
        if not check_fields_in_request(["api-id"], args):
            return "bad request!", 400

        dbi = db_orm.DbInterface(get_db())

        # User
        user = get_active_user_from_request(args, dbi.session)
        if not isinstance(user, UserModel):
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        # Find api
        api = get_api_from_request(args, dbi.session)
        if not api:
            return NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

        # Permissions
        permissions = get_api_user_permissions(api, user.id, user.role, dbi.session)
        if "r" not in permissions:
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        api_specification = get_api_specification(api.raw_specification_url)
        if api_specification is None:
            return []

        tc = (
            dbi.session.query(ApiTestCaseModel)
            .filter(ApiTestCaseModel.api_id == api.id)
            .order_by(ApiTestCaseModel.offset.asc())
            .all()
        )
        tc_mapping = [x.as_dict(db_session=dbi.session) for x in tc]

        documents = (
            dbi.session.query(ApiDocumentModel)
            .filter(ApiDocumentModel.api_id == api.id)
            .order_by(ApiDocumentModel.offset.asc())
            .all()
        )
        documents_mapping = [x.as_dict(db_session=dbi.session) for x in documents]

        justifications = (
            dbi.session.query(ApiJustificationModel)
            .filter(ApiJustificationModel.api_id == api.id)
            .order_by(ApiJustificationModel.offset.asc())
            .all()
        )
        justifications_mapping = [x.as_dict(db_session=dbi.session) for x in justifications]

        mapping = {_A: api.as_dict(), _TCs: tc_mapping, _Js: justifications_mapping, _Ds: documents_mapping}

        for iType in [_TCs, _Js, _Ds]:
            for iMapping in range(len(mapping[iType])):
                current_offset = mapping[iType][iMapping]["offset"]
                current_section = mapping[iType][iMapping]["section"]
                mapping[iType][iMapping]["match"] = (
                    api_specification[current_offset : current_offset + len(current_section)] == current_section
                )

        mapped_sections = get_split_sections(api_specification, mapping, [_TC, _J, _D])
        unmapped_sections = [x for x in mapping[_TCs] if not x["match"]]
        unmapped_sections += [x for x in mapping[_Js] if not x["match"]]
        unmapped_sections += [x for x in mapping[_Ds] if not x["match"]]
        ret = {"mapped": mapped_sections, "unmapped": unmapped_sections}

        return ret

    def post(self):
        request_data = request.get_json(force=True)

        if not check_fields_in_request(self.fields, request_data):
            return "bad request!", 400

        dbi = db_orm.DbInterface(get_db())

        # User
        user = get_active_user_from_request(request_data, dbi.session)
        if not isinstance(user, UserModel):
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        # Find api
        api = get_api_from_request(request_data, dbi.session)
        if not api:
            return NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

        # Permissions
        permissions = get_api_user_permissions(api, user.id, user.role, dbi.session)
        if "w" not in permissions or user.role not in USER_ROLES_WRITE_PERMISSIONS:
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        section = request_data["section"]
        offset = request_data["offset"]
        coverage = request_data["coverage"]

        if "id" not in request_data["test-case"].keys():
            # Create a new one
            # `status` field should be skipped because a default is assigned in the model
            for check_field in [x for x in TestCase.fields if x not in ["status"]]:
                if check_field.replace("_", "-") not in request_data["test-case"].keys():
                    return "Bad request. Not consistent data.", 400

            repository = request_data["test-case"]["repository"]
            relative_path = request_data["test-case"]["relative-path"]
            title = request_data["test-case"]["title"]
            description = request_data["test-case"]["description"]

            # Check if the same Test Case is already associated with the same snippet
            if (
                len(
                    dbi.session.query(ApiTestCaseModel)
                    .join(TestCaseModel)
                    .filter(ApiTestCaseModel.section == section)
                    .filter(TestCaseModel.title == title)
                    .filter(TestCaseModel.repository == repository)
                    .filter(TestCaseModel.relative_path == relative_path)
                    .all()
                )
                > 0
            ):
                return "Test Case already associated to the current api.", 409

            new_test_case = TestCaseModel(repository, relative_path, title, description, user)

            new_test_case_mapping_api = ApiTestCaseModel(api, new_test_case, section, offset, coverage, user)
            dbi.session.add(new_test_case)
            dbi.session.add(new_test_case_mapping_api)
        else:
            id = request_data["test-case"]["id"]
            if (
                len(
                    dbi.session.query(ApiTestCaseModel)
                    .filter(ApiTestCaseModel.api_id == api.id)
                    .filter(ApiTestCaseModel.test_case_id == id)
                    .filter(ApiTestCaseModel.section == section)
                    .all()
                )
                > 0
            ):
                return "Test Case already associated to the selected api Specification section.", 409

            try:
                existing_test_case = dbi.session.query(TestCaseModel).filter(TestCaseModel.id == id).one()
            except NoResultFound:
                return f"Unable to find the Test Case id {id}", 400

            new_test_case_mapping_api = ApiTestCaseModel(api, existing_test_case, section, offset, coverage, user)

            dbi.session.add(new_test_case_mapping_api)

        dbi.session.commit()  # To have the id

        # Add Notifications
        notification = (
            f"{user.email} added Test Case {new_test_case_mapping_api.test_case.id} "
            f"mapped to "
            f"{api.api} as part of the library {api.library}"
        )
        notifications = NotificationModel(
            api,
            NOTIFICATION_CATEGORY_NEW,
            f"{api.api} - Test Case mapping " f"{new_test_case_mapping_api.id} has been added",
            notification,
            str(user.id),
            f"/mapping/{api.id}",
        )
        dbi.session.add(notifications)
        return new_test_case_mapping_api.as_dict()

    def put(self):
        request_data = request.get_json(force=True)

        if not check_fields_in_request(self.fields, request_data):
            return "bad request!", 400

        dbi = db_orm.DbInterface(get_db())

        # User
        user = get_active_user_from_request(request_data, dbi.session)
        if not isinstance(user, UserModel):
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        # Find api
        api = get_api_from_request(request_data, dbi.session)
        if not api:
            return NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

        # Permissions
        permissions = get_api_user_permissions(api, user.id, user.role,  dbi.session)
        if "w" not in permissions or user.role not in USER_ROLES_WRITE_PERMISSIONS:
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        try:
            test_case_mapping_api = (
                dbi.session.query(ApiTestCaseModel).filter(ApiTestCaseModel.id == request_data["relation-id"]).one()
            )
            test_case = test_case_mapping_api.test_case
        except NoResultFound:
            return "Test Case mapping api not found", 400

        # Update only modified fields
        modified_tc = False
        for field in TestCase.fields:
            if field.replace("_", "-") in request_data["test-case"].keys():
                if getattr(test_case, field) != request_data["test-case"][field.replace("_", "-")]:
                    modified_tc = True
                    setattr(test_case, field, request_data["test-case"][field.replace("_", "-")])

        if modified_tc:
            setattr(test_case, "edited_by_id", user.id)

        modified_tca = False
        if test_case_mapping_api.section != request_data["section"]:
            modified_tca = True
            test_case_mapping_api.section = request_data["section"]

        if test_case_mapping_api.offset != request_data["offset"]:
            modified_tca = True
            test_case_mapping_api.offset = request_data["offset"]

        if test_case_mapping_api.coverage != int(request_data["coverage"]):
            modified_tca = True
            test_case_mapping_api.coverage = int(request_data["coverage"])

        if modified_tca:
            test_case_mapping_api.edited_by_id = user.id

        dbi.session.commit()

        if modified_tc or modified_tca:
            # Add Notifications
            notification = f"{user.email} modified a test case mapped " f"to {api.api}"
            notifications = NotificationModel(
                api,
                NOTIFICATION_CATEGORY_EDIT,
                f"{api.api} - Test Case has been modified",
                notification,
                str(user.id),
                f"/mapping/{api.id}",
            )
            dbi.session.add(notifications)
            dbi.session.commit()

        return test_case_mapping_api.as_dict()

    def delete(self):
        request_data = request.get_json(force=True)

        if not check_fields_in_request(["relation-id", "api-id"], request_data):
            return "bad request!", 400

        dbi = db_orm.DbInterface(get_db())

        # User
        user = get_active_user_from_request(request_data, dbi.session)
        if not isinstance(user, UserModel):
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        # Find api
        api = get_api_from_request(request_data, dbi.session)
        if not api:
            return NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

        # Permissions
        permissions = get_api_user_permissions(api, user.id, user.role, dbi.session)
        if "w" not in permissions or user.role not in USER_ROLES_WRITE_PERMISSIONS:
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        # check if api ...
        try:
            test_case_mapping_api = (
                dbi.session.query(ApiTestCaseModel).filter(ApiTestCaseModel.id == request_data["relation-id"]).one()
            )
        except NoResultFound:
            return f"Unable to find the Test Case mapping to Api id {request_data['relation-id']}", 400

        if test_case_mapping_api.api.id != api.id:
            return "bad request!", 401

        notification_tc_id = test_case_mapping_api.test_case.id
        notification_tc_title = test_case_mapping_api.test_case.title
        dbi.session.delete(test_case_mapping_api)
        dbi.session.commit()

        # Add Notifications
        notification = f"{user.email} deleted test case " f"{notification_tc_id} {notification_tc_title}"
        notifications = NotificationModel(
            api,
            NOTIFICATION_CATEGORY_DELETE,
            f"{api.api} - Test Case has been deleted",
            notification,
            str(user.id),
            f"/mapping/{api.id}",
        )
        dbi.session.add(notifications)

        # TODO: Remove work item only user request to do
        """
        test_case = test_case_mapping_api.test_case

        if len(dbi.session.query(ApiTestCaseModel).filter( \
                ApiTestCaseModel.api_id == api.id).filter( \
                ApiTestCaseModel.test_case_id == test_case.id).all()) == 0:
            dbi.session.delete(test_case)
        """

        dbi.session.commit()
        return True


class MappingHistory(Resource):
    def get(self):
        args = get_query_string_args(request.args)
        dbi = db_orm.DbInterface(get_db())

        if (
            "work_item_type" not in args.keys()
            or "mapped_to_type" not in args.keys()
            or "relation_id" not in args.keys()
        ):
            return []

        if args["mapped_to_type"] == "api":
            if args["work_item_type"] == "justification":
                _model = JustificationModel
                _model_map = ApiJustificationModel
                _model_map_history = ApiJustificationHistoryModel
                _model_history = JustificationHistoryModel
            elif args["work_item_type"] == "document":
                _model = DocumentModel
                _model_map = ApiDocumentModel
                _model_map_history = ApiDocumentHistoryModel
                _model_history = DocumentHistoryModel
            elif args["work_item_type"] == "sw-requirement":
                _model = SwRequirementModel
                _model_map = ApiSwRequirementModel
                _model_map_history = ApiSwRequirementHistoryModel
                _model_history = SwRequirementHistoryModel
            elif args["work_item_type"] == "test-specification":
                _model = TestSpecificationModel
                _model_map = ApiTestSpecificationModel
                _model_map_history = ApiTestSpecificationHistoryModel
                _model_history = TestSpecificationHistoryModel
            elif args["work_item_type"] == "test-case":
                _model = TestCaseModel
                _model_map = ApiTestCaseModel
                _model_map_history = ApiTestCaseHistoryModel
                _model_history = TestCaseHistoryModel
            else:
                return []

        elif args["mapped_to_type"] == "sw-requirement":
            if args["work_item_type"] == "sw-requirement":
                _model = SwRequirementModel
                _model_map = SwRequirementSwRequirementModel
                _model_map_history = SwRequirementSwRequirementHistoryModel
                _model_history = SwRequirementHistoryModel
            elif args["work_item_type"] == "test-specification":
                _model = TestSpecificationModel
                _model_map = SwRequirementTestSpecificationModel
                _model_map_history = SwRequirementTestSpecificationHistoryModel
                _model_history = TestSpecificationHistoryModel
            elif args["work_item_type"] == "test-case":
                _model = TestCaseModel
                _model_map = SwRequirementTestCaseModel
                _model_map_history = SwRequirementTestCaseHistoryModel
                _model_history = TestCaseHistoryModel
            else:
                return []

        elif args["mapped_to_type"] == "test-specification":
            if args["work_item_type"] == "test-case":
                _model = TestCaseModel
                _model_map = TestSpecificationTestCaseModel
                _model_map_history = TestSpecificationTestCaseHistoryModel
                _model_history = TestCaseHistoryModel
            else:
                return []
        else:
            return []

        _model_fields = _model.__table__.columns.keys()
        _model_map_fields = _model_map.__table__.columns.keys()

        relation_rows = dbi.session.query(_model_map).filter(_model_map.id == args["relation_id"]).all()
        if len(relation_rows) != 1:
            return []

        relation_row = relation_rows[0].as_dict()

        model_versions_query = (
            dbi.session.query(_model_history)
            .filter(_model_history.id == relation_row[args["work_item_type"].replace("-", "_")]["id"])
            .order_by(_model_history.version.asc())
        )
        model_map_versions_query = (
            dbi.session.query(_model_map_history)
            .filter(_model_map_history.id == args["relation_id"])
            .order_by(_model_map_history.version.asc())
        )

        staging_array = []
        ret = []

        # object dict
        for model_version in model_versions_query.all():
            obj = {
                "version": model_version.version,
                "type": "object",
                "created_at": datetime.datetime.strptime(str(model_version.created_at), "%Y-%m-%d %H:%M:%S.%f"),
            }

            for k in _model_fields:
                if k not in ["row_id", "version", "created_at", "updated_at"]:
                    obj[k] = getattr(model_version, k)

            staging_array.append(obj)

        # map dict
        for model_map_version in model_map_versions_query.all():
            obj = {
                "version": model_map_version.version,
                "type": "mapping",
                "created_at": datetime.datetime.strptime(str(model_map_version.created_at), "%Y-%m-%d %H:%M:%S.%f"),
            }
            for k in _model_map_fields:
                if args["work_item_type"] == "justification":
                    if k not in ["coverage", "created_at", "updated_at"]:
                        obj[k] = getattr(model_map_version, k)
                else:
                    if k not in ["created_at", "updated_at"]:
                        obj[k] = getattr(model_map_version, k)

            staging_array.append(obj)

        staging_array = sorted(staging_array, key=lambda d: (d["created_at"]))

        # get version object.mapping equal to 1.1
        first_found = False
        first_obj = {}
        first_map = {}

        for i in range(len(staging_array)):
            if staging_array[i]["version"] == 1 and staging_array[i]["type"] == "object":
                first_obj = staging_array[i]
            elif staging_array[i]["version"] == 1 and staging_array[i]["type"] == "mapping":
                first_map = staging_array[i]
            if first_map != {} and first_obj != {}:
                first_found = True
                break

        if not first_found:
            return []

        ret.append(get_combined_history_object(first_obj, first_map, _model_fields, _model_map_fields))

        for i in range(len(staging_array)):
            last_obj_version = int(ret[-1]["version"].split(".")[0])
            last_map_version = int(ret[-1]["version"].split(".")[1])
            if staging_array[i]["type"] == "object" and staging_array[i]["version"] > last_obj_version:
                ret.append(
                    get_combined_history_object(staging_array[i], ret[-1]["mapping"], _model_fields, _model_map_fields)
                )
            elif staging_array[i]["type"] == "mapping" and staging_array[i]["version"] > last_map_version:
                ret.append(
                    get_combined_history_object(ret[-1]["object"], staging_array[i], _model_fields, _model_map_fields)
                )

        ret = get_reduced_history_data(ret, _model_fields, _model_map_fields, dbi.session)
        ret = ret[::-1]
        return ret


class MappingUsage(Resource):
    def get(self):
        """Return list of api the selected work item is mapped directly against
        Improvement: Take in consideration also indirect mapping and other
          work items, like list of Test Specifications where a Test Case
          is used
        """
        args = get_query_string_args(request.args)
        dbi = db_orm.DbInterface(get_db())

        if "work_item_type" not in args.keys() or "id" not in args.keys():
            return []

        _id = args["id"]

        # Api
        if args["work_item_type"] == "justification":
            model = ApiJustificationModel
            api_data = dbi.session.query(model).filter(model.justification_id == _id).all()
            api_ids = [x.api_id for x in api_data]
        elif args["work_item_type"] == "document":
            model = ApiDocumentModel
            api_data = dbi.session.query(model).filter(model.document_id == _id).all()
            api_ids = [x.api_id for x in api_data]
        elif args["work_item_type"] == "sw-requirement":
            model = ApiSwRequirementModel
            api_data = dbi.session.query(model).filter(model.sw_requirement_id == _id).all()
            api_ids = [x.api_id for x in api_data]
        elif args["work_item_type"] == "test-specification":
            # Direct
            model = ApiTestSpecificationModel
            api_data = dbi.session.query(model).filter(model.test_specification_id == _id).all()
            api_ids = [x.api_id for x in api_data]

            # indirect sw requirement mapping api:
            model = SwRequirementTestSpecificationModel
            parent_model = ApiSwRequirementModel
            sr_api_data = dbi.session.query(model).join(parent_model).filter(model.test_specification_id == _id).all()
            api_ids += [x.sw_requirement_mapping_api.api_id for x in sr_api_data]
        elif args["work_item_type"] == "test-case":
            model = ApiTestCaseModel
            api_data = dbi.session.query(model).filter(model.test_case_id == _id).all()
            api_ids = [x.api_id for x in api_data]

            # indirect test specification mapping api:
            model = TestSpecificationTestCaseModel
            parent_model = ApiTestSpecificationModel
            ts_api_data = dbi.session.query(model).join(parent_model).filter(model.test_case_id == _id).all()
            api_ids += [x.sw_requirement_mapping_api.api_id for x in ts_api_data]

            # indirect sw requirement mapping api:
            model = SwRequirementTestCaseModel
            parent_model = ApiSwRequirementModel
            sr_api_data = dbi.session.query(model).join(parent_model).filter(model.test_case_id == _id).all()
            api_ids += [x.sw_requirement_mapping_api.api_id for x in sr_api_data]

            # indirect test specification sw requirement:
            model = TestSpecificationTestCaseModel
            parent_model = SwRequirementTestSpecificationModel
            sr_ts_data = dbi.session.query(model).join(parent_model).filter(model.test_case_id == _id).all()
            sr_ts_ids = [x.test_specification_mapping_sw_requirement_id for x in sr_ts_data]
            model = SwRequirementTestSpecificationModel
            parent_model = ApiSwRequirementModel
            sr_api_data = (
                dbi.session.query(model)
                .join(parent_model)
                .filter(model.sw_requirement_mapping_api_id.in_(sr_ts_ids))
                .all()
            )
            api_ids += [x.sw_requirement_mapping_api.api_id for x in sr_api_data]

        apis = dbi.session.query(ApiModel).filter(ApiModel.id.in_(api_ids)).all()

        query_data = {
            "api": [
                {"id": x.id, "api": x.api, "library": x.library, "library_version": x.library_version} for x in apis
            ]
        }

        return query_data


class ApiSpecificationsMapping(Resource):
    fields = ["api-id", "justification", "section", "offset"]

    def get(self):
        args = get_query_string_args(request.args)
        if not check_fields_in_request(["api-id"], args):
            return "bad request!", 400

        # undesired_keys = ['section', 'offset']

        dbi = db_orm.DbInterface(get_db())

        # User
        user = get_active_user_from_request(args, dbi.session)
        if not isinstance(user, UserModel):
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        # Find api
        api = get_api_from_request(args, dbi.session)
        if not api:
            return NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

        # Permissions
        permissions = get_api_user_permissions(api, user.id, user.role, dbi.session)
        if "r" not in permissions:
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        api_specification = get_api_specification(api.raw_specification_url)
        if api_specification is None:
            return []

        mapped_sections = [
            {"section": api_specification, "offset": 0, "coverage": 0, _TCs: [], _TSs: [], _SRs: [], _Js: []}
        ]
        unmapped_sections = []

        ret = {"mapped": mapped_sections, "unmapped": unmapped_sections}

        return ret


class ApiJustificationsMapping(Resource):
    fields = ["api-id", "justification", "section", "offset", "coverage"]

    def get(self):
        args = get_query_string_args(request.args)
        if not check_fields_in_request(["api-id"], args):
            return "bad request!", 400

        # undesired_keys = ['section', 'offset']

        dbi = db_orm.DbInterface(get_db())

        # User
        user = get_active_user_from_request(args, dbi.session)
        if not isinstance(user, UserModel):
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        # Find api
        api = get_api_from_request(args, dbi.session)
        if not api:
            return NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

        # Permissions
        permissions = get_api_user_permissions(api, user.id, user.role, dbi.session)
        if "r" not in permissions:
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        api_specification = get_api_specification(api.raw_specification_url)
        if api_specification is None:
            return []

        justifications = (
            dbi.session.query(ApiJustificationModel)
            .filter(ApiJustificationModel.api_id == api.id)
            .order_by(ApiJustificationModel.offset.asc())
            .all()
        )
        justifications_mapping = [x.as_dict(db_session=dbi.session) for x in justifications]

        mapping = {_A: api.as_dict(), _Js: justifications_mapping}

        for iType in [_Js]:
            for iMapping in range(len(mapping[iType])):
                current_offset = mapping[iType][iMapping]["offset"]
                current_section = mapping[iType][iMapping]["section"]
                mapping[iType][iMapping]["match"] = (
                    api_specification[current_offset : current_offset + len(current_section)] == current_section
                )

        mapped_sections = get_split_sections(api_specification, mapping, [_J])
        unmapped_sections = [x for x in mapping[_Js] if not x["match"]]
        ret = {"mapped": mapped_sections, "unmapped": unmapped_sections}

        return ret

    def post(self):
        request_data = request.get_json(force=True)

        if not check_fields_in_request(self.fields, request_data):
            return "bad request!", 400

        dbi = db_orm.DbInterface(get_db())

        # User
        user = get_active_user_from_request(request_data, dbi.session)
        if not isinstance(user, UserModel):
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        # Find api
        api = get_api_from_request(request_data, dbi.session)
        if not api:
            return NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

        # Permissions
        permissions = get_api_user_permissions(api, user.id, user.role, dbi.session)
        if "w" not in permissions or user.role not in USER_ROLES_WRITE_PERMISSIONS:
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        section = request_data["section"]
        offset = request_data["offset"]
        coverage = request_data["coverage"]

        if "id" not in request_data["justification"].keys():
            description = request_data["justification"]["description"]
            new_justification = JustificationModel(description, user)
            new_justification_mapping_api = ApiJustificationModel(
                api, new_justification, section, offset, coverage, user
            )
            dbi.session.add(new_justification)
            dbi.session.add(new_justification_mapping_api)
        else:
            id = request_data["justification"]["id"]
            if (
                len(
                    dbi.session.query(ApiJustificationModel)
                    .filter(ApiJustificationModel.api_id == api.id)
                    .filter(ApiJustificationModel.justification_id == id)
                    .filter(ApiJustificationModel.section == section)
                    .all()
                )
                > 0
            ):
                return "Justification already associated to the selected api Specification section.", 409

            try:
                existing_justification = (
                    dbi.session.query(JustificationModel).filter(JustificationModel.id == id).one()
                )
            except NoResultFound:
                return f"Unable to find the Justification id {id}", 400

            new_justification_mapping_api = ApiJustificationModel(
                api, existing_justification, section, offset, coverage, user
            )

            dbi.session.add(new_justification_mapping_api)

        dbi.session.commit()  # TO have the id of the new justification mapping

        # Add Notifications
        notification = (
            f"{user.email} added justification {new_justification_mapping_api.justification.id} "
            f"mapped to "
            f"{api.api} as part of the library {api.library}"
        )
        notifications = NotificationModel(
            api,
            NOTIFICATION_CATEGORY_NEW,
            f"Justification mapping {new_justification_mapping_api.id} has been added",
            notification,
            str(user.id),
            f"/mapping/{api.id}",
        )
        dbi.session.add(notifications)

        dbi.session.commit()
        return new_justification_mapping_api.as_dict()

    def put(self):
        request_data = request.get_json(force=True)

        if not check_fields_in_request(self.fields + ["relation-id"], request_data):
            return "bad request!", 400

        dbi = db_orm.DbInterface(get_db())

        # User
        user = get_active_user_from_request(request_data, dbi.session)
        if not isinstance(user, UserModel):
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        # Find api
        api = get_api_from_request(request_data, dbi.session)
        if not api:
            return NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

        # Permissions
        permissions = get_api_user_permissions(api, user.id, user.role, dbi.session)
        if "w" not in permissions or user.role not in USER_ROLES_WRITE_PERMISSIONS:
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        # check if api ...
        try:
            justification_mapping_api = (
                dbi.session.query(ApiJustificationModel)
                .filter(ApiJustificationModel.id == request_data["relation-id"])
                .one()
            )
        except NoResultFound:
            return f"Unable to find the Justification mapping to Api id {request_data['relation-id']}", 400

        justification = justification_mapping_api.justification

        # Update only modified fields
        modified_j = False
        for field in Justification.fields:
            if field.replace("_", "-") in request_data["justification"].keys():
                if getattr(justification, field) != request_data["justification"][field.replace("_", "-")]:
                    modified_j = True
                    setattr(justification, field, request_data["justification"][field.replace("_", "-")])

        if modified_j:
            setattr(justification, "edited_by_id", user.id)

        modified_ja = False
        if request_data["section"] != justification_mapping_api.section:
            modified_ja = True
            justification_mapping_api.section = request_data["section"]

        if request_data["offset"] != justification_mapping_api.offset:
            modified_ja = True
            justification_mapping_api.offset = request_data["offset"]

        if request_data["coverage"] != justification_mapping_api.coverage:
            modified_ja = True
            justification_mapping_api.coverage = request_data["coverage"]

        if modified_ja:
            justification_mapping_api.edited_by_id = user.id

        if modified_ja or modified_j:
            # Add Notifications
            notification = (
                f"{user.email} modified justification {justification_mapping_api.justification.id} "
                f"mapped to "
                f"{api.api} as part of the library {api.library}"
            )
            notifications = NotificationModel(
                api,
                NOTIFICATION_CATEGORY_EDIT,
                f"Justification mapping {justification_mapping_api.id} " f"has been modified",
                notification,
                str(user.id),
                f"/mapping/{api.id}",
            )
            dbi.session.add(notifications)

        dbi.session.commit()
        return justification_mapping_api.as_dict()

    def delete(self):
        request_data = request.get_json(force=True)

        if not check_fields_in_request(["relation-id", "api-id"], request_data):
            return "bad request!", 400

        dbi = db_orm.DbInterface(get_db())

        # User
        user = get_active_user_from_request(request_data, dbi.session)
        if not isinstance(user, UserModel):
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        # Find api
        api = get_api_from_request(request_data, dbi.session)
        if not api:
            return NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

        # Permissions
        permissions = get_api_user_permissions(api, user.id, user.role, dbi.session)
        if "w" not in permissions or user.role not in USER_ROLES_WRITE_PERMISSIONS:
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        # check if api ...
        justification_mapping_api = (
            dbi.session.query(ApiJustificationModel)
            .filter(ApiJustificationModel.id == request_data["relation-id"])
            .all()
        )

        if len(justification_mapping_api) != 1:
            return "bad request!", 401

        justification_mapping_api = justification_mapping_api[0]

        if justification_mapping_api.api.id != api.id:
            return "bad request!", 401

        notification_j_id = justification_mapping_api.justification.id
        dbi.session.delete(justification_mapping_api)
        dbi.session.commit()

        # Add Notifications
        notification = (
            f"{user.email} deleted justification {notification_j_id} "
            f"mapped to "
            f"{api.api} as part of the library {api.library}"
        )
        notifications = NotificationModel(
            api,
            NOTIFICATION_CATEGORY_DELETE,
            "Justification mapping has been deleted",
            notification,
            str(user.id),
            f"/mapping/{api.id}",
        )
        dbi.session.add(notifications)

        # TODO: Remove work item only user request to do
        """
        justification = justification_mapping_api.justification

        if len(dbi.session.query(ApiJustificationModel).filter( \
                ApiJustificationModel.api_id == api.id).filter( \
                ApiJustificationModel.justification_id == justification.id).all()) == 0:
            dbi.session.delete(justification)
        """

        dbi.session.commit()
        return True


class ApiDocumentsMapping(Resource):
    fields = ["api-id", "coverage", "document", "offset", "section"]

    document_fields = ["description", "document_type", "offset", "section", "spdx_relation", "title", "url"]

    def get(self):
        args = get_query_string_args(request.args)
        if not check_fields_in_request(["api-id"], args):
            return "bad request!", 400

        dbi = db_orm.DbInterface(get_db())

        # User
        user = get_active_user_from_request(args, dbi.session)
        if not isinstance(user, UserModel):
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        # Find api
        api = get_api_from_request(args, dbi.session)
        if not api:
            return NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

        # Permissions
        permissions = get_api_user_permissions(api, user.id, user.role, dbi.session)
        if "r" not in permissions:
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        api_specification = get_api_specification(api.raw_specification_url)
        if api_specification is None:
            return []

        documents = (
            dbi.session.query(ApiDocumentModel)
            .filter(ApiDocumentModel.api_id == api.id)
            .order_by(ApiDocumentModel.offset.asc())
            .all()
        )
        documents_mapping = [x.as_dict(db_session=dbi.session) for x in documents]

        mapping = {_A: api.as_dict(), _Ds: documents_mapping}

        for iType in [_Ds]:
            for iMapping in range(len(mapping[iType])):
                current_offset = mapping[iType][iMapping]["offset"]
                current_section = mapping[iType][iMapping]["section"]
                mapping[iType][iMapping]["match"] = (
                    api_specification[current_offset : current_offset + len(current_section)] == current_section
                )

        mapped_sections = get_split_sections(api_specification, mapping, [_D])
        unmapped_sections = [x for x in mapping[_Ds] if not x["match"]]
        ret = {"mapped": mapped_sections, "unmapped": unmapped_sections}

        return ret

    def post(self):
        request_data = request.get_json(force=True)

        if not check_fields_in_request(self.fields, request_data):
            return "bad request!", 400

        dbi = db_orm.DbInterface(get_db())

        # User
        user = get_active_user_from_request(request_data, dbi.session)
        if not isinstance(user, UserModel):
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        # Find api
        api = get_api_from_request(request_data, dbi.session)
        if not api:
            return NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

        # Permissions
        permissions = get_api_user_permissions(api, user.id, user.role, dbi.session)
        if "w" not in permissions or user.role not in USER_ROLES_WRITE_PERMISSIONS:
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        mapping_section = request_data["section"]
        mapping_offset = request_data["offset"]
        mapping_coverage = request_data["coverage"]

        if "id" not in request_data["document"].keys():

            if not check_fields_in_request(self.document_fields, request_data["document"]):
                return "bad request!!", 400

            doc_title = request_data["document"]["title"]
            doc_description = request_data["document"]["description"]
            doc_type = request_data["document"]["document_type"]
            doc_spdx_relation = request_data["document"]["spdx_relation"]
            doc_url = request_data["document"]["url"]
            doc_section = request_data["document"]["section"]
            doc_offset = request_data["document"]["offset"]
            doc_valid = 0  # default 0, it will be evaluated once rendered
            new_document = DocumentModel(
                doc_title,
                doc_description,
                doc_type,
                doc_spdx_relation,
                doc_url,
                doc_section,
                doc_offset,
                doc_valid,
                user,
            )
            new_document_mapping_api = ApiDocumentModel(
                api, new_document, mapping_section, mapping_offset, mapping_coverage, user
            )
            dbi.session.add(new_document)
            dbi.session.add(new_document_mapping_api)

        else:
            id = request_data["document"]["id"]
            if (
                len(
                    dbi.session.query(ApiDocumentModel)
                    .filter(ApiDocumentModel.api_id == api.id)
                    .filter(ApiDocumentModel.document_id == id)
                    .filter(ApiDocumentModel.section == mapping_section)
                    .all()
                )
                > 0
            ):
                return "Document already associated to the selected api Specification section.", 409

            try:
                existing_document = dbi.session.query(DocumentModel).filter(DocumentModel.id == id).one()
            except NoResultFound:
                return f"Unable to find the Document id {id}", 400

            new_document_mapping_api = ApiDocumentModel(
                api, existing_document, mapping_section, mapping_offset, mapping_coverage, user
            )

            dbi.session.add(new_document_mapping_api)
        dbi.session.commit()  # TO have the id of the new document mapping

        # Add Notifications
        notification = (
            f"{user.email} added document {new_document_mapping_api.document.id} "
            f"mapped to "
            f"{api.api} as part of the library {api.library}"
        )
        notifications = NotificationModel(
            api,
            NOTIFICATION_CATEGORY_NEW,
            f"Document mapping {new_document_mapping_api.id} has been added",
            notification,
            str(user.id),
            f"/mapping/{api.id}",
        )
        dbi.session.add(notifications)

        dbi.session.commit()
        return new_document_mapping_api.as_dict()

    def put(self):
        request_data = request.get_json(force=True)
        document_fields = self.document_fields + ["status"]

        if not check_fields_in_request(self.fields + ["relation-id"], request_data):
            return "bad request!", 400

        if not check_fields_in_request(document_fields, request_data["document"]):
            return "bad request!!", 400

        dbi = db_orm.DbInterface(get_db())

        # User
        user = get_active_user_from_request(request_data, dbi.session)
        if not isinstance(user, UserModel):
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        # Find api
        api = get_api_from_request(request_data, dbi.session)
        if not api:
            return NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

        # Permissions
        permissions = get_api_user_permissions(api, user.id, user.role, dbi.session)
        if "w" not in permissions or user.role not in USER_ROLES_WRITE_PERMISSIONS:
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        # check if api ...
        try:
            document_mapping_api = (
                dbi.session.query(ApiDocumentModel).filter(ApiDocumentModel.id == request_data["relation-id"]).one()
            )
        except NoResultFound:
            return f"Unable to find the Document mapping to Api id {request_data['relation-id']}", 400

        document = document_mapping_api.document

        # Update only modified fields
        modified_d = False
        request_document_data = get_dict_with_db_format_keys(request_data["document"])
        for field in document_fields:
            if field in request_document_data.keys():
                if getattr(document, field) != request_document_data[field]:
                    modified_d = True
                    setattr(document, field, request_document_data[field])
                    if field == "url":  # move valid to false
                        setattr(document, "valid", 0)

        if modified_d:
            setattr(document, "edited_by_id", user.id)

        modified_da = False  # da: document mapping api
        if request_data["section"] != document_mapping_api.section:
            modified_da = True
            document_mapping_api.section = request_data["section"]

        if request_data["offset"] != document_mapping_api.offset:
            modified_da = True
            document_mapping_api.offset = request_data["offset"]

        if request_data["coverage"] != document_mapping_api.coverage:
            modified_da = True
            document_mapping_api.coverage = request_data["coverage"]

        if modified_da:
            document_mapping_api.edited_by_id = user.id

        if modified_da or modified_d:
            # Add Notifications
            notification = (
                f"{user.email} modified document {document_mapping_api.document.id} "
                f"mapped to "
                f"{api.api} as part of the library {api.library}"
            )
            notifications = NotificationModel(
                api,
                NOTIFICATION_CATEGORY_EDIT,
                f"Document mapping {document_mapping_api.id} " f"has been modified",
                notification,
                str(user.id),
                f"/mapping/{api.id}",
            )
            dbi.session.add(notifications)

        dbi.session.commit()
        return document_mapping_api.as_dict()

    def delete(self):
        request_data = request.get_json(force=True)

        if not check_fields_in_request(["relation-id", "api-id"], request_data):
            return "bad request!", 400

        dbi = db_orm.DbInterface(get_db())

        # User
        user = get_active_user_from_request(request_data, dbi.session)
        if not isinstance(user, UserModel):
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        # Find api
        api = get_api_from_request(request_data, dbi.session)
        if not api:
            return NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

        # Permissions
        permissions = get_api_user_permissions(api, user.id, user.role, dbi.session)
        if "w" not in permissions or user.role not in USER_ROLES_WRITE_PERMISSIONS:
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        # check if api ...
        document_mapping_api = (
            dbi.session.query(ApiDocumentModel).filter(ApiDocumentModel.id == request_data["relation-id"]).all()
        )

        if len(document_mapping_api) != 1:
            return "bad request!", 401

        document_mapping_api = document_mapping_api[0]

        if document_mapping_api.api.id != api.id:
            return "bad request!", 401

        notification_d_id = document_mapping_api.document.id
        dbi.session.delete(document_mapping_api)
        dbi.session.commit()

        # Add Notifications
        notification = (
            f"{user.email} deleted document {notification_d_id} "
            f"mapped to "
            f"{api.api} as part of the library {api.library}"
        )
        notifications = NotificationModel(
            api,
            NOTIFICATION_CATEGORY_DELETE,
            "Document mapping has been deleted",
            notification,
            str(user.id),
            f"/mapping/{api.id}",
        )
        dbi.session.add(notifications)

        # TODO: Remove work item only user request to do
        """
        document = document_mapping_api.document

        if len(dbi.session.query(ApiDocumentModel).filter( \
                ApiDocumentModel.api_id == api.id).filter( \
                ApiDocumentModel.document_id == document.id).all()) == 0:
            dbi.session.delete(document)
        """

        dbi.session.commit()
        return True


class ApiSwRequirementsMapping(Resource):
    fields = ["api-id", "sw-requirement", "section", "coverage"]

    def get(self):
        args = get_query_string_args(request.args)
        if not check_fields_in_request(["api-id"], args):
            return "bad request!", 400

        # undesired_keys = ['section', 'offset']

        dbi = db_orm.DbInterface(get_db())

        # User
        user = get_active_user_from_request(args, dbi.session)
        if not isinstance(user, UserModel):
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        # Find api
        api = get_api_from_request(args, dbi.session)
        if not api:
            return NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

        # Permissions
        permissions = get_api_user_permissions(api, user.id, user.role, dbi.session)
        if "r" not in permissions:
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        ret = get_api_sw_requirements_mapping_sections(dbi, api)
        return ret

    def post(self):
        request_data = request.get_json(force=True)
        notification_sr_title = ""
        if not check_fields_in_request(self.fields, request_data):
            return "bad request!", 400

        dbi = db_orm.DbInterface(get_db())

        # User
        user = get_active_user_from_request(request_data, dbi.session)
        if not isinstance(user, UserModel):
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        # Find api
        api = get_api_from_request(request_data, dbi.session)
        if not api:
            return NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

        # Permissions
        permissions = get_api_user_permissions(api, user.id, user.role, dbi.session)
        if "w" not in permissions or user.role not in USER_ROLES_WRITE_PERMISSIONS:
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        section = request_data["section"]
        coverage = request_data["coverage"]
        offset = request_data["offset"]

        if "id" not in request_data["sw-requirement"].keys():
            # Create a new one
            # `status` field should be skipped because a default is assigned in the model
            for check_field in [x for x in SwRequirement.fields if x not in ["status"]]:
                if check_field.replace("_", "-") not in request_data["sw-requirement"].keys():
                    return "Bad request. Not consistent data.", 400

            title = request_data["sw-requirement"]["title"]
            description = request_data["sw-requirement"]["description"]

            if (
                len(
                    dbi.session.query(SwRequirementModel)
                    .filter(SwRequirementModel.title == title)
                    .filter(SwRequirementModel.description == description)
                    .all()
                )
                > 0
            ):
                return "SW Requirement already associated to the selected api Specification section.", 409

            new_sw_requirement = SwRequirementModel(title, description, user)

            new_sw_requirement_mapping_api = ApiSwRequirementModel(
                api, new_sw_requirement, section, offset, coverage, user
            )
            notification_sr_title = title
            dbi.session.add(new_sw_requirement)
            dbi.session.add(new_sw_requirement_mapping_api)

        else:
            # Re using existing sw requirement
            id = request_data["sw-requirement"]["id"]
            if (
                len(
                    dbi.session.query(ApiSwRequirementModel)
                    .filter(ApiSwRequirementModel.api_id == api.id)
                    .filter(ApiSwRequirementModel.sw_requirement_id == id)
                    .filter(ApiSwRequirementModel.section == section)
                    .all()
                )
                > 0
            ):
                return "SW Requirement already associated to the selected api Specification section.", 409

            try:
                existing_sw_requirement = (
                    dbi.session.query(SwRequirementModel).filter(SwRequirementModel.id == id).one()
                )
                notification_sr_title = existing_sw_requirement.title
            except NoResultFound:
                return f"SW Requirement {id} not found in the database.", 404

            new_sw_requirement_mapping_api = ApiSwRequirementModel(
                api, existing_sw_requirement, section, offset, coverage, user
            )
            dbi.session.add(new_sw_requirement_mapping_api)

        dbi.session.commit()  # To have the id of the new added mapping

        # Add Notifications
        notification = f"{user.email} created a new sw requirement " f"{notification_sr_title} - coverage: {coverage}"
        notifications = NotificationModel(
            api,
            NOTIFICATION_CATEGORY_NEW,
            f"{api.api} - Sw Requirement has been created",
            notification,
            str(user.id),
            f"/mapping/{api.id}?asr={new_sw_requirement_mapping_api.id}&view=details",
        )
        dbi.session.add(notifications)
        dbi.session.commit()

        return new_sw_requirement_mapping_api.as_dict()

    def put(self):
        request_data = request.get_json(force=True)

        if not check_fields_in_request(self.fields, request_data):
            return "bad request!", 400

        dbi = db_orm.DbInterface(get_db())

        # User
        user = get_active_user_from_request(request_data, dbi.session)
        if not isinstance(user, UserModel):
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        # Find api
        api = get_api_from_request(request_data, dbi.session)
        if not api:
            return NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

        # Permissions
        permissions = get_api_user_permissions(api, user.id, user.role, dbi.session)
        if "w" not in permissions or user.role not in USER_ROLES_WRITE_PERMISSIONS:
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        try:
            sw_requirement_mapping_api = (
                dbi.session.query(ApiSwRequirementModel)
                .filter(ApiSwRequirementModel.id == request_data["relation-id"])
                .one()
            )
        except NoResultFound:
            return f"Unable to find the Sw Requirement mapping to Api id {request_data['relation-id']}", 400

        sw_requirement = sw_requirement_mapping_api.sw_requirement

        # Software Requirement: Update only modified fields
        modified_sr = False
        for field in SwRequirement.fields:
            if field.replace("_", "-") in request_data["sw-requirement"].keys():
                if getattr(sw_requirement, field) != request_data["sw-requirement"][field.replace("_", "-")]:
                    modified_sr = True
                    setattr(sw_requirement, field, request_data["sw-requirement"][field.replace("_", "-")])

        if modified_sr:
            setattr(sw_requirement, "edited_by_id", user.id)

        # Software Requirement Mapping: Update only modified fields
        modified_srm = False
        if sw_requirement_mapping_api.section != request_data["section"]:
            modified_srm = True
            sw_requirement_mapping_api.section = request_data["section"]

        if sw_requirement_mapping_api.offset != request_data["offset"]:
            modified_srm = True
            sw_requirement_mapping_api.offset = request_data["offset"]

        if sw_requirement_mapping_api.coverage != int(request_data["coverage"]):
            modified_srm = True
            sw_requirement_mapping_api.coverage = int(request_data["coverage"])

        if modified_srm:
            sw_requirement_mapping_api.edited_by_id = user.id

        if modified_sr or modified_srm:
            # Add Notifications
            notification = f"{user.email} modified sw requirement " f"{sw_requirement.title}"
            notifications = NotificationModel(
                api,
                NOTIFICATION_CATEGORY_EDIT,
                f"{api.api} - Sw Requirement has been modified",
                notification,
                str(user.id),
                f"/mapping/{api.id}?asr={sw_requirement_mapping_api.id}&view=details",
            )
            dbi.session.add(notifications)

        dbi.session.commit()
        return sw_requirement_mapping_api.as_dict()

    def delete(self):
        request_data = request.get_json(force=True)

        if not check_fields_in_request(["relation-id", "api-id"], request_data):
            return BAD_REQUEST_MESSAGE, BAD_REQUEST_STATUS

        dbi = db_orm.DbInterface(get_db())

        # User
        user = get_active_user_from_request(request_data, dbi.session)
        if not isinstance(user, UserModel):
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        # Find api
        api = get_api_from_request(request_data, dbi.session)
        if not api:
            return NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

        # Permissions
        permissions = get_api_user_permissions(api, user.id, user.role, dbi.session)
        if "w" not in permissions or user.role not in USER_ROLES_WRITE_PERMISSIONS:
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        # check if api ...
        try:
            sw_requirement_mapping_api = (
                dbi.session.query(ApiSwRequirementModel)
                .filter(ApiSwRequirementModel.id == request_data["relation-id"])
                .one()
            )
        except NoResultFound:
            return f"Unable to find the Sw Requirement mapping to Api id {request_data['relation-id']}", 400

        if sw_requirement_mapping_api.api.id != api.id:
            return BAD_REQUEST_MESSAGE, BAD_REQUEST_STATUS

        notification_sr_id = sw_requirement_mapping_api.sw_requirement.id
        notification_sr_title = sw_requirement_mapping_api.sw_requirement.title
        dbi.session.delete(sw_requirement_mapping_api)
        dbi.session.commit()

        # Add Notifications
        notification = f"{user.email} deleted sw requirement " f"{notification_sr_id} {notification_sr_title}"
        notifications = NotificationModel(
            api,
            NOTIFICATION_CATEGORY_DELETE,
            f"{api.api} - Sw Requirement has been deleted",
            notification,
            str(user.id),
            f"/mapping/{api.id}",
        )
        dbi.session.add(notifications)

        # TODO: Remove work item only user request to do
        """
        sw_requirement = sw_requirement_mapping_api.sw_requirement

        if len(dbi.session.query(ApiSwRequirementModel).filter( \
                ApiSwRequirementModel.api_id == api.id).filter( \
                ApiSwRequirementModel.sw_requirement_id == sw_requirement.id).all()) == 0:
            dbi.session.delete(sw_requirement)
        """

        dbi.session.commit()
        return True


class SwRequirementImport(Resource):
    def post(self):
        request_data = request.get_json(force=True)

        if "file_content" not in request_data:
            return BAD_REQUEST_MESSAGE, BAD_REQUEST_STATUS

        spdx_importer = SPDXImport()
        return {_SRs: spdx_importer.getBasilSwRequirementsToSelect(request_data["file_content"])}

    def put(self):
        request_data = request.get_json(force=True)

        if not check_fields_in_request(["file_content", "filter_ids"], request_data):
            return BAD_REQUEST_MESSAGE, BAD_REQUEST_STATUS

        dbi = db_orm.DbInterface(get_db())

        # User
        user = get_active_user_from_request(request_data, dbi.session)
        if not isinstance(user, UserModel):
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        # Permissions
        if user.role not in USER_ROLES_WRITE_PERMISSIONS:
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        spdx_importer = SPDXImport()
        filter_ids = [f.strip() for f in request_data["filter_ids"].split(",") if len(f.strip())]
        sw_requirements = spdx_importer.getBasilSwRequirementsToImport(request_data["file_content"], filter_ids, user)

        # Pay attention: we actually doesn't check if the requirement already exists
        # (if already exists a requirement with same content)
        if sw_requirements:
            dbi.session.add_all(sw_requirements)
            dbi.session.commit()
            return {_SRs: [sr.as_dict() for sr in sw_requirements]}

        return {_SRs: []}


class Justification(Resource):
    fields = get_model_editable_fields(JustificationModel, False)
    fields_hashes = [x.replace("_", "-") for x in fields]

    def get(self):
        args = get_query_string_args(request.args)
        dbi = db_orm.DbInterface(get_db())
        query = dbi.session.query(JustificationModel)
        query = filter_query(query, args, JustificationModel, False)
        jus = [ju.as_dict() for ju in query.all()]

        if "mode" in args.keys():
            if args["mode"] == "minimal":
                minimal_keys = ["id", "description"]
                jus = [{key: val for key, val in sub.items() if key in minimal_keys} for sub in jus]

        return jus


class TestSpecification(Resource):
    fields = get_model_editable_fields(TestSpecificationModel, False)
    fields_hashes = [x.replace("_", "-") for x in fields]

    def get(self):
        args = get_query_string_args(request.args)
        dbi = db_orm.DbInterface(get_db())

        query = dbi.session.query(TestSpecificationModel)
        query = filter_query(query, args, TestSpecificationModel, False)
        tss = [ts.as_dict() for ts in query.all()]

        if "mode" in args.keys():
            if args["mode"] == "minimal":
                minimal_keys = ["id", "title"]
                tss = [{key: val for key, val in sub.items() if key in minimal_keys} for sub in tss]

        return tss


class SwRequirement(Resource):
    fields = get_model_editable_fields(SwRequirementModel, False)
    fields_hashes = [x.replace("_", "-") for x in fields]

    def get(self):
        args = get_query_string_args(request.args)
        dbi = db_orm.DbInterface(get_db())

        query = dbi.session.query(SwRequirementModel)
        query = filter_query(query, args, SwRequirementModel, False)
        srs = [sr.as_dict() for sr in query.all()]

        if "mode" in args.keys():
            if args["mode"] == "minimal":
                minimal_keys = ["id", "title"]
                srs = [{key: val for key, val in sub.items() if key in minimal_keys} for sub in srs]

        return srs


class TestCase(Resource):
    fields = get_model_editable_fields(TestCaseModel, False)
    fields_hashes = [x.replace("_", "-") for x in fields]

    def get(self):
        args = get_query_string_args(request.args)
        dbi = db_orm.DbInterface(get_db())
        query = dbi.session.query(TestCaseModel)
        query = filter_query(query, args, TestCaseModel, False)
        tcs = [tc.as_dict() for tc in query.all()]

        if "mode" in args.keys():
            if args["mode"] == "minimal":
                minimal_keys = ["id", "title"]
                tcs = [{key: val for key, val in sub.items() if key in minimal_keys} for sub in tcs]

        return tcs


class SwRequirementSwRequirementsMapping(Resource):
    fields = ["sw-requirement", "coverage"]

    def get(self):
        args = get_query_string_args(request.args)
        dbi = db_orm.DbInterface(get_db())
        query = dbi.session.query(SwRequirementSwRequirementModel)
        query = filter_query(query, args, SwRequirementSwRequirementModel, False)
        srsrs = [srsr.as_dict(db_session=dbi.session) for srsr in query.all()]

        return srsrs

    def post(self):
        request_data = request.get_json(force=True)
        api_sr = None
        sr_sr = None

        post_mandatory_fields = self.fields + ["relation-id", "relation-to", "parent-sw-requirement"]
        if not check_fields_in_request(post_mandatory_fields, request_data):
            return "bad request!", 400

        if "id" not in request_data["parent-sw-requirement"].keys():
            return "bad request!!", 400

        relation_id = request_data["relation-id"]
        dbi = db_orm.DbInterface(get_db())

        # User
        user = get_active_user_from_request(request_data, dbi.session)
        if not isinstance(user, UserModel):
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        # Find SwRequirementSwRequirement
        if request_data["relation-to"] == "api":
            relation_to_query = dbi.session.query(ApiSwRequirementModel).filter(
                ApiSwRequirementModel.id == relation_id
            )
            try:
                relation_to_item = relation_to_query.one()
            except NoResultFound:
                return "Parent mapping not found", 404

            api_id = relation_to_item.api.id
        elif request_data["relation-to"] == "sw-requirement":
            relation_to_query = dbi.session.query(SwRequirementSwRequirementModel).filter(
                SwRequirementSwRequirementModel.id == relation_id
            )
            try:
                relation_to_item = relation_to_query.one()
            except NoResultFound:
                return "Parent mapping not found", 404

            api_id = get_parent_api_id(relation_to_item, dbi.session)
            if not api_id:
                return SW_COMPONENT_NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

        else:
            return "Bad request!!!", 400

        try:
            api = dbi.session.query(ApiModel).filter(ApiModel.id == api_id).one()
        except NoResultFound:
            return SW_COMPONENT_NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

        # Permissions
        permissions = get_api_user_permissions(api, user.id, user.role, dbi.session)
        if "w" not in permissions or user.role not in USER_ROLES_WRITE_PERMISSIONS:
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        if request_data["relation-to"] == "api":
            api_sr = relation_to_item
        elif request_data["relation-to"] == "sw-requirement":
            sr_sr = relation_to_item

        parent_sw_requirement_id = request_data["parent-sw-requirement"]["id"]
        coverage = request_data["coverage"]

        try:
            parent_sw_requirement = (
                dbi.session.query(SwRequirementModel).filter(SwRequirementModel.id == parent_sw_requirement_id).one()
            )
        except NoResultFound:
            return "Sw Requirement not found", 400

        del parent_sw_requirement  # Just need to check it exists

        if "id" not in request_data["sw-requirement"].keys():
            # Create a new one
            # `status` field should be skipped because a default is assigned in the model
            for check_field in [x for x in SwRequirement.fields if x not in ["status"]]:
                if check_field.replace("_", "-") not in request_data["sw-requirement"].keys():
                    return "Bad request. Not consistent data.", 400

            title = request_data["sw-requirement"]["title"]
            description = request_data["sw-requirement"]["description"]

            existing_sw_requirements = (
                dbi.session.query(SwRequirementModel)
                .filter(SwRequirementModel.title == title)
                .filter(SwRequirementModel.description == description)
                .all()
            )

            for sr in existing_sw_requirements:
                sr_mapping = (
                    dbi.session.query(SwRequirementSwRequirementModel)
                    .filter(SwRequirementSwRequirementModel.id == relation_id)
                    .filter(SwRequirementSwRequirementModel.sw_requirement_id == sr.id)
                    .all()
                )
                if len(sr_mapping) > 0:
                    return "Sw Requirement already associated to the selected Sw Requirement.", 409

            new_sw_requirement = SwRequirementModel(title, description, user)

            new_sw_requirement_mapping_sw_requirement = SwRequirementSwRequirementModel(
                api_sr, sr_sr, new_sw_requirement, coverage, user
            )

            dbi.session.add(new_sw_requirement)
            dbi.session.add(new_sw_requirement_mapping_sw_requirement)

        else:
            # Map an existing SwRequirement
            sw_requirement_id = request_data["sw-requirement"]["id"]

            if (
                len(
                    dbi.session.query(SwRequirementSwRequirementModel)
                    .filter(SwRequirementSwRequirementModel.id == relation_id)
                    .filter(SwRequirementSwRequirementModel.sw_requirement_id == sw_requirement_id)
                    .all()
                )
                > 0
            ):
                return "Sw Requirement already associated to the selected Sw Requirement.", 409

            try:
                sw_requirement = (
                    dbi.session.query(SwRequirementModel).filter(SwRequirementModel.id == sw_requirement_id).one()
                )
            except NoResultFound:
                return "Bad request.", 400

            if not isinstance(sw_requirement, SwRequirementModel):
                return "Bad request.", 400

            new_sw_requirement_mapping_sw_requirement = SwRequirementSwRequirementModel(
                api_sr, sr_sr, sw_requirement, coverage, user
            )
            dbi.session.add(new_sw_requirement_mapping_sw_requirement)

        dbi.session.commit()

        # Add Notifications
        notification = (
            f"{user.email} added sw requirement " f"to {api.api} mapping as part of the library {api.library}"
        )
        notifications = NotificationModel(
            api,
            NOTIFICATION_CATEGORY_NEW,
            f"{api.api}, a sw requirement has been created",
            notification,
            str(user.id),
            f"/mapping/{api.id}",
        )
        dbi.session.add(notifications)
        dbi.session.commit()
        return new_sw_requirement_mapping_sw_requirement.as_dict()

    def put(self):
        request_data = request.get_json(force=True)

        mandatory_fields = self.fields + ["relation-id"]
        if not check_fields_in_request(mandatory_fields, request_data):
            return "bad request!", 400

        dbi = db_orm.DbInterface(get_db())

        # User
        user = get_active_user_from_request(request_data, dbi.session)
        if not isinstance(user, UserModel):
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        try:
            sr_mapping_sr = (
                dbi.session.query(SwRequirementSwRequirementModel)
                .filter(SwRequirementSwRequirementModel.id == request_data["relation-id"])
                .one()
            )
        except NoResultFound:
            return "Sw Requirement mapping not found", 400

        api_id = get_parent_api_id(sr_mapping_sr, dbi.session)
        if not api_id:
            return SW_COMPONENT_NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

        try:
            api = dbi.session.query(ApiModel).filter(ApiModel.id == api_id).one()
        except NoResultFound:
            return SW_COMPONENT_NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

        # Permissions
        permissions = get_api_user_permissions(api, user.id, user.role, dbi.session)
        if "w" not in permissions or user.role not in USER_ROLES_WRITE_PERMISSIONS:
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        sr = sr_mapping_sr.sw_requirement

        # Update only modified fields
        modified_sr = False
        for field in SwRequirement.fields:
            if field.replace("_", "-") in request_data["sw-requirement"].keys():
                if getattr(sr, field) != request_data["sw-requirement"][field.replace("_", "-")]:
                    modified_sr = True
                    setattr(sr, field, request_data["sw-requirement"][field.replace("_", "-")])

        if modified_sr:
            setattr(sr, "edited_by_id", user.id)

        modified_srsr = False
        if sr_mapping_sr.coverage != int(request_data["coverage"]):
            modified_srsr = True
            sr_mapping_sr.coverage = int(request_data["coverage"])
            sr_mapping_sr.edited_by_id = user.id

        ret = sr_mapping_sr.as_dict(db_session=dbi.session)
        dbi.session.commit()

        if modified_sr or modified_srsr:
            # Add Notifications
            notification = (
                f"{user.email} modified sw requirement " f"from {api.api} mapping as part of the library {api.library}"
            )
            notifications = NotificationModel(
                api,
                NOTIFICATION_CATEGORY_EDIT,
                f"{api.api}, a sw requirement has been modified",
                notification,
                str(user.id),
                f"/mapping/{api.id}",
            )
            dbi.session.add(notifications)
            dbi.session.commit()
        return ret

    def delete(self):
        request_data = request.get_json(force=True)

        if not check_fields_in_request(["relation-id"], request_data):
            return "bad request!", 400

        dbi = db_orm.DbInterface(get_db())

        # User
        user = get_active_user_from_request(request_data, dbi.session)
        if not isinstance(user, UserModel):
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        # check sw_requirement_mapping_sw_requirement ...
        try:
            sr_mapping_sr = (
                dbi.session.query(SwRequirementSwRequirementModel)
                .filter(SwRequirementSwRequirementModel.id == request_data["relation-id"])
                .one()
            )
        except NoResultFound:
            return "bad request!", 401

        api_id = get_parent_api_id(sr_mapping_sr, dbi.session)
        if not api_id:
            return SW_COMPONENT_NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

        try:
            api = dbi.session.query(ApiModel).filter(ApiModel.id == api_id).one()
        except NoResultFound:
            return SW_COMPONENT_NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

        # Permissions
        permissions = get_api_user_permissions(api, user.id, user.role, dbi.session)
        if "w" not in permissions or user.role not in USER_ROLES_WRITE_PERMISSIONS:
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        """
        if sw_requirement_mapping_sw_requirement.sw_requirement_id != sw_requirement.id:
            return 'bad request!', 401
        """

        notification_sr_id = sr_mapping_sr.sw_requirement.id
        notification_sr_title = sr_mapping_sr.sw_requirement.title
        dbi.session.delete(sr_mapping_sr)
        dbi.session.commit()

        # Add Notifications
        notification = (
            f"{user.email} deleted sw requirement "
            f"{notification_sr_id} {notification_sr_title} mapping as part of the library {api.library}"
        )
        notifications = NotificationModel(
            api,
            NOTIFICATION_CATEGORY_DELETE,
            f"{api.api}, a sw requirement has been deleted",
            notification,
            str(user.id),
            f"/mapping/{api.id}",
        )
        dbi.session.add(notifications)
        dbi.session.commit()
        return True


class SwRequirementTestSpecificationsMapping(Resource):
    fields = ["api-id", "sw-requirement", "test-specification", "coverage"]

    def get(self):
        ret = {}
        return ret

    def post(self):
        api_sr = None
        sr_sr = None

        request_data = request.get_json(force=True)
        mandatory_fields = self.fields + ["relation-id", "relation-to"]
        if not check_fields_in_request(mandatory_fields, request_data):
            return "bad request!", 400

        if "id" not in request_data["sw-requirement"].keys():
            return "bad request!!", 400

        relation_id = request_data["relation-id"]
        relation_to = request_data["relation-to"]

        dbi = db_orm.DbInterface(get_db())

        # User
        user = get_active_user_from_request(request_data, dbi.session)
        if not isinstance(user, UserModel):
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        sw_requirement_id = request_data["sw-requirement"]["id"]
        coverage = request_data["coverage"]

        try:
            sw_requirement = (
                dbi.session.query(SwRequirementModel).filter(SwRequirementModel.id == sw_requirement_id).one()
            )
        except NoResultFound:
            return "Sw Requirement not found", 400

        del sw_requirement  # Just need to check it exists

        if relation_to == "api":
            relation_to_query = dbi.session.query(ApiSwRequirementModel).filter(
                ApiSwRequirementModel.id == relation_id
            )
            try:
                relation_to_item = relation_to_query.one()
            except NoResultFound:
                return "Parent mapping not found", 404

            api_id = relation_to_item.api.id
        elif relation_to == "sw-requirement":
            relation_to_query = dbi.session.query(SwRequirementSwRequirementModel).filter(
                SwRequirementSwRequirementModel.id == relation_id
            )
            try:
                relation_to_item = relation_to_query.one()
            except NoResultFound:
                return "Parent mapping not found", 404

            api_id = get_parent_api_id(relation_to_item, dbi.session)
            if not api_id:
                return SW_COMPONENT_NOT_FOUND_MESSAGE, NOT_FOUND_STATUS
        else:
            return "Bad request!!!", 400

        try:
            api = dbi.session.query(ApiModel).filter(ApiModel.id == api_id).one()
        except NoResultFound:
            return SW_COMPONENT_NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

        # Permissions
        permissions = get_api_user_permissions(api, user.id, user.role, dbi.session)
        if "w" not in permissions or user.role not in USER_ROLES_WRITE_PERMISSIONS:
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        if relation_to == "api":
            api_sr = relation_to_item
        elif relation_to == "sw-requirement":
            sr_sr = relation_to_item

        if "id" not in request_data["test-specification"].keys():
            # Create a new one
            # `status` field should be skipped because a default is assigned in the model
            for check_field in [x for x in TestSpecification.fields if x not in ["status"]]:
                if check_field.replace("_", "-") not in request_data["test-specification"].keys():
                    return "Bad request. Not consistent data.", 400

            title = request_data["test-specification"]["title"]
            preconditions = request_data["test-specification"]["preconditions"]
            test_description = request_data["test-specification"]["test-description"]
            expected_behavior = request_data["test-specification"]["expected-behavior"]

            """
            TODO: Evaluate if the following check is needed

            existing_test_specifications = dbi.session.query(TestSpecificationModel).filter(
                TestSpecificationModel.title == title).filter(
                TestSpecificationModel.preconditions == preconditions).filter(
                TestSpecificationModel.test_description == test_description).filter(
                TestSpecificationModel.expected_behavior == expected_behavior).all()

            for ts in existing_test_specifications:
                ts_mapping = dbi.session.query(SwRequirementTestSpecificationModel).join(
                    ApiSwRequirementModel).filter(
                    ApiSwRequirementModel.sw_requirement_id == sw_requirement_id).filter(
                    SwRequirementTestSpecificationModel.test_specification_id == ts.id).filter(
                    ApiSwRequirementModel.api_id == api.id).all()
                if len(ts_mapping) > 0:
                    return "Test Specification already associated to the selected api Specification section.", 409
            """

            new_test_specification = TestSpecificationModel(
                title, preconditions, test_description, expected_behavior, user
            )

            new_test_specification_mapping_sw_requirement = SwRequirementTestSpecificationModel(
                api_sr, sr_sr, new_test_specification, coverage, user
            )

            dbi.session.add(new_test_specification)
            dbi.session.add(new_test_specification_mapping_sw_requirement)

        else:
            test_specification_id = request_data["test-specification"]["id"]

            if (
                len(
                    dbi.session.query(SwRequirementTestSpecificationModel)
                    .filter(
                        SwRequirementTestSpecificationModel.sw_requirement_mapping_api_id
                        == request_data["relation-id"]
                    )
                    .filter(SwRequirementTestSpecificationModel.test_specification_id == test_specification_id)
                    .all()
                )
                > 0
            ):
                return "Test Specification already associated to the selected Api and Sw Requirement.", 409

            try:
                test_specification = (
                    dbi.session.query(TestSpecificationModel)
                    .filter(TestSpecificationModel.id == test_specification_id)
                    .one()
                )
            except NoResultFound:
                return "Unable to find the selected Test Specification", 400

            if not isinstance(test_specification, TestSpecificationModel):
                return "Bad request.", 400

            new_test_specification_mapping_sw_requirement = SwRequirementTestSpecificationModel(
                api_sr, sr_sr, test_specification, coverage, user
            )
            dbi.session.add(new_test_specification_mapping_sw_requirement)

        dbi.session.commit()

        # Add Notifications
        notification = (
            f"{user.email} added test specification " f"to {api.api} mapping as part of the library {api.library}"
        )
        notifications = NotificationModel(
            api,
            NOTIFICATION_CATEGORY_NEW,
            f"{api.api}, a test specification has been created",
            notification,
            str(user.id),
            f"/mapping/{api.id}",
        )
        dbi.session.add(notifications)
        dbi.session.commit()
        return new_test_specification_mapping_sw_requirement.as_dict()

    def put(self):
        request_data = request.get_json(force=True)

        mandatory_fields = self.fields + ["relation-id"]
        if not check_fields_in_request(mandatory_fields, request_data):
            return "bad request!", 400

        dbi = db_orm.DbInterface(get_db())

        # User
        user = get_active_user_from_request(request_data, dbi.session)
        if not isinstance(user, UserModel):
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        try:
            sw_mapping_ts = (
                dbi.session.query(SwRequirementTestSpecificationModel)
                .filter(SwRequirementTestSpecificationModel.id == request_data["relation-id"])
                .one()
            )
        except NoResultFound:
            return (
                f"Unable to find the Test Specification "
                f"mapping to Sw Requirement id {request_data['relation-id']}",
                400,
            )

        api_id = get_parent_api_id(sw_mapping_ts, dbi.session)
        if not api_id:
            return SW_COMPONENT_NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

        try:
            api = dbi.session.query(ApiModel).filter(ApiModel.id == api_id).one()
        except NoResultFound:
            return SW_COMPONENT_NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

        # Permissions
        permissions = get_api_user_permissions(api, user.id, user.role, dbi.session)
        if "w" not in permissions or user.role not in USER_ROLES_WRITE_PERMISSIONS:
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        test_specification = sw_mapping_ts.test_specification

        # Update only modified fields
        modified_ts = False
        for field in TestSpecification.fields:
            if field.replace("_", "-") in request_data["test-specification"].keys():
                if getattr(test_specification, field) != request_data["test-specification"][field.replace("_", "-")]:
                    modified_ts = True
                    setattr(test_specification, field, request_data["test-specification"][field.replace("_", "-")])

        if modified_ts:
            setattr(test_specification, "edited_by_id", user.id)

        modified_srts = False
        if sw_mapping_ts.coverage != int(request_data["coverage"]):
            modified_srts = True
            sw_mapping_ts.coverage = int(request_data["coverage"])
            sw_mapping_ts.edited_by_id = user.id

        ret = sw_mapping_ts.as_dict(db_session=dbi.session)
        dbi.session.commit()

        if modified_ts or modified_srts:
            # Add Notifications
            notification = (
                f"{user.email} modified test specification "
                f"from {api.api} mapping as part of the library {api.library}"
            )
            notifications = NotificationModel(
                api,
                NOTIFICATION_CATEGORY_EDIT,
                f"{api.api}, a test specification has been modified",
                notification,
                str(user.id),
                f"/mapping/{api.id}",
            )
            dbi.session.add(notifications)
            dbi.session.commit()
        return ret

    def delete(self):
        ret = False
        request_data = request.get_json(force=True)

        mandatory_fields = ["relation-id"]
        if not check_fields_in_request(mandatory_fields, request_data):
            return "bad request!", 400

        dbi = db_orm.DbInterface(get_db())

        # User
        user = get_active_user_from_request(request_data, dbi.session)
        if not isinstance(user, UserModel):
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        try:
            sw_mapping_ts = (
                dbi.session.query(SwRequirementTestSpecificationModel)
                .filter(SwRequirementTestSpecificationModel.id == request_data["relation-id"])
                .one()
            )
        except NoResultFound:
            return (
                f"Unable to find the Test Specification "
                f"mapping to Sw Requirement id {request_data['relation-id']}",
                400,
            )

        api_id = get_parent_api_id(sw_mapping_ts, dbi.session)
        if not api_id:
            return SW_COMPONENT_NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

        try:
            api = dbi.session.query(ApiModel).filter(ApiModel.id == api_id).one()
        except NoResultFound:
            return SW_COMPONENT_NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

        # Permissions
        permissions = get_api_user_permissions(api, user.id, user.role, dbi.session)
        if "w" not in permissions or user.role not in USER_ROLES_WRITE_PERMISSIONS:
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        # test_specification = sw_mapping_ts.test_specification
        # dbi.session.delete(test_specification)

        notification_ts_id = sw_mapping_ts.test_specification.id
        notification_ts_title = sw_mapping_ts.test_specification.title
        dbi.session.delete(sw_mapping_ts)
        dbi.session.commit()

        # Add Notifications
        notification = (
            f"{user.email} deleted test specification "
            f"{notification_ts_id} {notification_ts_title} mapping as part of the library {api.library}"
        )
        notifications = NotificationModel(
            api,
            NOTIFICATION_CATEGORY_DELETE,
            f"{api.api}, a test specification has been deleted",
            notification,
            str(user.id),
            f"/mapping/{api.id}",
        )
        dbi.session.add(notifications)
        dbi.session.commit()

        return ret


class SwRequirementTestCasesMapping(Resource):
    fields = ["api-id", "sw-requirement", "test-case", "coverage"]

    def get(self):
        ret = {}
        return ret

    def post(self):
        api_sr = None
        sr_sr = None
        request_data = request.get_json(force=True)

        post_mandatory_fields = self.fields + ["relation-id", "relation-to"]
        if not check_fields_in_request(post_mandatory_fields, request_data):
            return "bad request!", 400

        if "id" not in request_data["sw-requirement"].keys():
            return "bad request!!", 400

        relation_id = request_data["relation-id"]
        relation_to = request_data["relation-to"]

        dbi = db_orm.DbInterface(get_db())

        # User
        user = get_active_user_from_request(request_data, dbi.session)
        if not isinstance(user, UserModel):
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        # Find ApiSwRequirement
        if relation_to == "api":
            relation_to_query = dbi.session.query(ApiSwRequirementModel).filter(
                ApiSwRequirementModel.id == relation_id
            )

            try:
                relation_to_item = relation_to_query.one()
            except NoResultFound:
                return "Parent mapping not found", 404

            api_id = relation_to_item.api.id

        elif relation_to == "sw-requirement":
            relation_to_query = dbi.session.query(SwRequirementSwRequirementModel).filter(
                SwRequirementSwRequirementModel.id == relation_id
            )
            try:
                relation_to_item = relation_to_query.one()
            except NoResultFound:
                return "Parent mapping not found", 404

            api_id = get_parent_api_id(relation_to_item, dbi.session)
            if not api_id:
                return SW_COMPONENT_NOT_FOUND_MESSAGE, NOT_FOUND_STATUS
        else:
            return "Bad request!!!", 400

        try:
            api = dbi.session.query(ApiModel).filter(ApiModel.id == api_id).one()
        except NoResultFound:
            return SW_COMPONENT_NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

        # Permissions
        permissions = get_api_user_permissions(api, user.id, user.role, dbi.session)
        if "w" not in permissions or user.role not in USER_ROLES_WRITE_PERMISSIONS:
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        if relation_to == "api":
            api_sr = relation_to_item
        elif relation_to == "sw-requirement":
            sr_sr = relation_to_item

        sw_requirement_id = request_data["sw-requirement"]["id"]
        coverage = request_data["coverage"]

        try:
            sw_requirement = (
                dbi.session.query(SwRequirementModel).filter(SwRequirementModel.id == sw_requirement_id).one()
            )
        except NoResultFound:
            return "Sw Requirement not found", 400

        del sw_requirement  # Just need to check it exists

        if "id" not in request_data["test-case"].keys():
            # Create a new one
            # `status` field should be skipped because a default is assigned in the model
            for check_field in [x for x in TestCase.fields if x not in ["status"]]:
                if check_field.replace("_", "-") not in request_data["test-case"].keys():
                    return "Bad request. Not consistent data.", 400

            title = request_data["test-case"]["title"]
            description = request_data["test-case"]["description"]
            repository = request_data["test-case"]["repository"]
            relative_path = request_data["test-case"]["relative-path"]

            existing_test_cases = (
                dbi.session.query(TestCaseModel)
                .filter(TestCaseModel.title == title)
                .filter(TestCaseModel.description == description)
                .filter(TestCaseModel.repository == repository)
                .filter(TestCaseModel.relative_path == relative_path)
                .all()
            )

            for tc in existing_test_cases:
                tc_mapping = (
                    dbi.session.query(SwRequirementTestCaseModel)
                    .filter(SwRequirementTestCaseModel.id == relation_id)
                    .filter(SwRequirementTestCaseModel.test_case_id == tc.id)
                    .all()
                )
                if len(tc_mapping) > 0:
                    return "Test Case already associated to the selected api Specification section.", 409

            new_test_case = TestCaseModel(repository, relative_path, title, description, user)

            new_test_case_mapping_sw_requirement = SwRequirementTestCaseModel(
                api_sr, sr_sr, new_test_case, coverage, user
            )

            dbi.session.add(new_test_case)
            dbi.session.add(new_test_case_mapping_sw_requirement)

        else:
            # Map an existing Test Case
            test_case_id = request_data["test-case"]["id"]

            if (
                len(
                    dbi.session.query(SwRequirementTestCaseModel)
                    .filter(SwRequirementTestCaseModel.id == relation_id)
                    .filter(SwRequirementTestCaseModel.test_case_id == test_case_id)
                    .all()
                )
                > 0
            ):
                return "Test Case already associated to the selected Api and Sw Requirement.", 409

            try:
                test_case = dbi.session.query(TestCaseModel).filter(TestCaseModel.id == test_case_id).one()
            except NoResultFound:
                return "Bad request.", 400

            if not isinstance(test_case, TestCaseModel):
                return "Bad request.", 400

            new_test_case_mapping_sw_requirement = SwRequirementTestCaseModel(api_sr, sr_sr, test_case, coverage, user)
            dbi.session.add(new_test_case_mapping_sw_requirement)

        dbi.session.commit()

        # Add Notifications
        notification = f"{user.email} added test case " f"to {api.api} mapping as part of the library {api.library}"
        notifications = NotificationModel(
            api,
            NOTIFICATION_CATEGORY_NEW,
            f"{api.api}, a test case has been created",
            notification,
            str(user.id),
            f"/mapping/{api.id}",
        )
        dbi.session.add(notifications)
        dbi.session.commit()
        return new_test_case_mapping_sw_requirement.as_dict()

    def put(self):
        request_data = request.get_json(force=True)

        mandatory_fields = self.fields + ["relation-id"]
        if not check_fields_in_request(mandatory_fields, request_data):
            return "bad request!", 400

        dbi = db_orm.DbInterface(get_db())

        # User
        user = get_active_user_from_request(request_data, dbi.session)
        if not isinstance(user, UserModel):
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        try:
            sw_mapping_tc = (
                dbi.session.query(SwRequirementTestCaseModel)
                .filter(SwRequirementTestCaseModel.id == request_data["relation-id"])
                .one()
            )
        except NoResultFound:
            return f"Unable to find the Test Case mapping to Sw Requirement id {request_data['relation-id']}", 400

        api_id = get_parent_api_id(sw_mapping_tc, dbi.session)
        if not api_id:
            return SW_COMPONENT_NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

        try:
            api = dbi.session.query(ApiModel).filter(ApiModel.id == api_id).one()
        except NoResultFound:
            return SW_COMPONENT_NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

        # Permissions
        permissions = get_api_user_permissions(api, user.id, user.role, dbi.session)
        if "w" not in permissions or user.role not in USER_ROLES_WRITE_PERMISSIONS:
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        test_case = sw_mapping_tc.test_case

        # Update only modified fields
        modified_tc = False
        for field in TestCase.fields:
            if field.replace("_", "-") in request_data["test-case"].keys():
                if getattr(test_case, field) != request_data["test-case"][field.replace("_", "-")]:
                    modified_tc = True
                    setattr(test_case, field, request_data["test-case"][field.replace("_", "-")])

        if modified_tc:
            setattr(test_case, "edited_by_id", user.id)

        modified_srtc = False
        if sw_mapping_tc.coverage != int(request_data["coverage"]):
            modified_srtc = True
            sw_mapping_tc.coverage = int(request_data["coverage"])
            sw_mapping_tc.edited_by_id = user.id

        ret = sw_mapping_tc.as_dict(db_session=dbi.session)
        dbi.session.commit()

        if modified_tc or modified_srtc:
            # Add Notifications
            notification = (
                f"{user.email} modified test case " f"from {api.api} mapping as part of the library {api.library}"
            )
            notifications = NotificationModel(
                api,
                NOTIFICATION_CATEGORY_EDIT,
                f"{api.api}, a test case has been modified",
                notification,
                str(user.id),
                f"/mapping/{api.id}",
            )
            dbi.session.add(notifications)
            dbi.session.commit()

        return ret

    def delete(self):
        ret = False
        request_data = request.get_json(force=True)

        mandatory_fields = ["relation-id"]
        if not check_fields_in_request(mandatory_fields, request_data):
            return "bad request!", 400

        dbi = db_orm.DbInterface(get_db())

        # User
        user = get_active_user_from_request(request_data, dbi.session)
        if not isinstance(user, UserModel):
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        try:
            sw_mapping_tc = (
                dbi.session.query(SwRequirementTestCaseModel)
                .filter(SwRequirementTestCaseModel.id == request_data["relation-id"])
                .one()
            )
        except NoResultFound:
            return f"Unable to find the Test Case mapping to Sw Requirement id {request_data['relation-id']}", 400

        api_id = get_parent_api_id(sw_mapping_tc, dbi.session)
        if not api_id:
            return SW_COMPONENT_NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

        try:
            api = dbi.session.query(ApiModel).filter(ApiModel.id == api_id).one()
        except NoResultFound:
            return SW_COMPONENT_NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

        # Permissions
        permissions = get_api_user_permissions(api, user.id, user.role, dbi.session)
        if "w" not in permissions or user.role not in USER_ROLES_WRITE_PERMISSIONS:
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        # test_case = sw_mapping_tc.test_case
        # dbi.session.delete(test_case)

        notification_tc_id = sw_mapping_tc.test_case.id
        notification_tc_title = sw_mapping_tc.test_case.title
        dbi.session.delete(sw_mapping_tc)
        dbi.session.commit()

        # Add Notifications
        notification = (
            f"{user.email} deleted test case "
            f"{notification_tc_id} {notification_tc_title} mapping as part of the library {api.library}"
        )
        notifications = NotificationModel(
            api,
            NOTIFICATION_CATEGORY_DELETE,
            f"{api.api}, a test case has been deleted",
            notification,
            str(user.id),
            f"/mapping/{api.id}",
        )
        dbi.session.add(notifications)
        dbi.session.commit()

        return ret


class TestSpecificationTestCasesMapping(Resource):
    fields = ["api-id", "test-specification", "test-case", "coverage"]

    def get(self):
        return []

    def post(self):
        request_data = request.get_json(force=True)
        api_ts = None
        sr_ts = None

        post_mandatory_fields = self.fields + ["relation-id", "relation-to"]
        if not check_fields_in_request(post_mandatory_fields, request_data):
            return "bad request!", 400

        if "id" not in request_data["test-specification"].keys():
            return "bad request!!", 400

        relation_id = request_data["relation-id"]
        dbi = db_orm.DbInterface(get_db())

        # User
        user = get_active_user_from_request(request_data, dbi.session)
        if not isinstance(user, UserModel):
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        # Find ApiSwRequirement
        if request_data["relation-to"] == "api":
            relation_to_query = dbi.session.query(ApiTestSpecificationModel).filter(
                ApiTestSpecificationModel.id == relation_id
            )
        elif request_data["relation-to"] == "sw-requirement":
            relation_to_query = dbi.session.query(SwRequirementTestSpecificationModel).filter(
                SwRequirementTestSpecificationModel.id == relation_id
            )
        else:
            return "Bad request!!!", 400

        try:
            relation_to_item = relation_to_query.one()
        except NoResultFound:
            return "Parent mapping not found", 404

        if request_data["relation-to"] == "api":
            api_ts = relation_to_item
            api = api_ts.api
            api_id = api.id
        elif request_data["relation-to"] == "sw-requirement":
            sr_ts = relation_to_item
            api_id = get_parent_api_id(sr_ts, dbi.session)
            if not api_id:
                return SW_COMPONENT_NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

            try:
                api = dbi.session.query(ApiModel).filter(ApiModel.id == api_id).one()
            except NoResultFound:
                return SW_COMPONENT_NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

        # Permissions
        permissions = get_api_user_permissions(api, user.id, user.role, dbi.session)
        if "w" not in permissions or user.role not in USER_ROLES_WRITE_PERMISSIONS:
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        test_specification_id = request_data["test-specification"]["id"]
        coverage = request_data["coverage"]

        try:
            test_specification = (
                dbi.session.query(TestSpecificationModel)
                .filter(TestSpecificationModel.id == test_specification_id)
                .one()
            )
        except NoResultFound:
            return "Test Specification not found", 400

        del test_specification  # Just need to check it exists

        if "id" not in request_data["test-case"].keys():
            # Create a new one
            # `status` field should be skipped because a default is assigned in the model
            for check_field in [x for x in TestCase.fields if x not in ["status"]]:
                if check_field.replace("_", "-") not in request_data["test-case"].keys():
                    return "Bad request. Not consistent data.", 400

            title = request_data["test-case"]["title"]
            description = request_data["test-case"]["description"]
            repository = request_data["test-case"]["repository"]
            relative_path = request_data["test-case"]["relative-path"]

            existing_test_cases = (
                dbi.session.query(TestCaseModel)
                .filter(TestCaseModel.title == title)
                .filter(TestCaseModel.description == description)
                .filter(TestCaseModel.repository == repository)
                .filter(TestCaseModel.relative_path == relative_path)
                .all()
            )

            for tc in existing_test_cases:
                tc_mapping = (
                    dbi.session.query(TestSpecificationTestCaseModel)
                    .filter(TestSpecificationTestCaseModel.id == relation_id)
                    .filter(TestSpecificationTestCaseModel.test_case_id == tc.id)
                    .all()
                )
                if len(tc_mapping) > 0:
                    return "Test Case already associated to the selected api Specification section.", 409

            new_test_case = TestCaseModel(repository, relative_path, title, description, user)

            new_test_case_mapping_test_specification = TestSpecificationTestCaseModel(
                api_ts, sr_ts, new_test_case, coverage, user
            )

            dbi.session.add(new_test_case)
            dbi.session.add(new_test_case_mapping_test_specification)

        else:
            # Map an existing Test Case
            test_case_id = request_data["test-case"]["id"]

            if (
                len(
                    dbi.session.query(TestSpecificationTestCaseModel)
                    .filter(TestSpecificationTestCaseModel.id == relation_id)
                    .filter(TestSpecificationTestCaseModel.test_case_id == test_case_id)
                    .all()
                )
                > 0
            ):
                return "Test Case already associated to the selected Api and Test Specification.", 409

            try:
                test_case = dbi.session.query(TestCaseModel).filter(TestCaseModel.id == test_case_id).one()
            except NoResultFound:
                return "Bad request.", 400

            if not isinstance(test_case, TestCaseModel):
                return "Bad request.", 400

            new_test_case_mapping_test_specification = TestSpecificationTestCaseModel(
                api_ts, sr_ts, test_case, coverage, user
            )
            dbi.session.add(new_test_case_mapping_test_specification)

        dbi.session.commit()

        # Add Notifications
        notification = f"{user.email} added test case " f"to {api.api} mapping as part of the library {api.library}"
        notifications = NotificationModel(
            api,
            NOTIFICATION_CATEGORY_NEW,
            f"{api.api}, a test case has been created",
            notification,
            str(user.id),
            f"/mapping/{api.id}",
        )
        dbi.session.add(notifications)
        dbi.session.commit()
        return new_test_case_mapping_test_specification.as_dict()

    def put(self):
        request_data = request.get_json(force=True)

        mandatory_fields = self.fields + ["relation-id"]
        if not check_fields_in_request(mandatory_fields, request_data):
            return "bad request!", 400

        dbi = db_orm.DbInterface(get_db())

        # User
        user = get_active_user_from_request(request_data, dbi.session)
        if not isinstance(user, UserModel):
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        try:
            ts_mapping_tc = (
                dbi.session.query(TestSpecificationTestCaseModel)
                .filter(TestSpecificationTestCaseModel.id == request_data["relation-id"])
                .one()
            )
        except NoResultFound:
            return f"Unable to find the Test Case mapping to Test Specification id {request_data['relation-id']}", 400

        # Api
        if ts_mapping_tc.test_specification_mapping_api_id:
            try:
                api_ts = (
                    dbi.session.query(ApiTestSpecificationModel)
                    .filter(ApiTestSpecificationModel.id == ts_mapping_tc.test_specification_mapping_api_id)
                    .one()
                )
            except NoResultFound:
                return SW_COMPONENT_NOT_FOUND_MESSAGE, NOT_FOUND_STATUS
            api = api_ts.api
        elif ts_mapping_tc.test_specification_mapping_sw_requirement_id:
            try:
                sr_ts = (
                    dbi.session.query(SwRequirementTestSpecificationModel)
                    .filter(
                        SwRequirementTestSpecificationModel.id
                        == ts_mapping_tc.test_specification_mapping_sw_requirement_id
                    )
                    .one()
                )
            except NoResultFound:
                return SW_COMPONENT_NOT_FOUND_MESSAGE, NOT_FOUND_STATUS
            api_id = get_parent_api_id(sr_ts, dbi.session)
            if not api_id:
                return SW_COMPONENT_NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

            try:
                api = dbi.session.query(ApiModel).filter(ApiModel.id == api_id).one()
            except NoResultFound:
                return SW_COMPONENT_NOT_FOUND_MESSAGE, NOT_FOUND_STATUS
        else:
            return SW_COMPONENT_NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

        # Permissions
        permissions = get_api_user_permissions(api, user.id, user.role, dbi.session)
        if "w" not in permissions or user.role not in USER_ROLES_WRITE_PERMISSIONS:
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        test_case = ts_mapping_tc.test_case

        # Update only modified fields
        modified_tc = False
        for field in TestCase.fields:
            if field.replace("_", "-") in request_data["test-case"].keys():
                if getattr(test_case, field) != request_data["test-case"][field.replace("_", "-")]:
                    modified_tc = True
                    setattr(test_case, field, request_data["test-case"][field.replace("_", "-")])

        if modified_tc:
            setattr(test_case, "edited_by_id", user.id)

        modified_tstc = False
        if ts_mapping_tc.coverage != int(request_data["coverage"]):
            modified_tstc = True
            ts_mapping_tc.coverage = int(request_data["coverage"])
            ts_mapping_tc.edited_by_id = user.id

        ret = ts_mapping_tc.as_dict(db_session=dbi.session)
        dbi.session.commit()

        if modified_tc or modified_tstc:
            # Add Notifications
            notification = (
                f"{user.email} modified test case " f"to {api.api} mapping as part of the library {api.library}"
            )
            notifications = NotificationModel(
                api,
                NOTIFICATION_CATEGORY_EDIT,
                f"{api.api}, a test case has been modified",
                notification,
                str(user.id),
                f"/mapping/{api.id}",
            )
            dbi.session.add(notifications)
            dbi.session.commit()
        return ret

    def delete(self):
        ret = False
        request_data = request.get_json(force=True)

        mandatory_fields = ["relation-id"]
        if not check_fields_in_request(mandatory_fields, request_data):
            return "bad request!", 400

        dbi = db_orm.DbInterface(get_db())

        # User
        user = get_active_user_from_request(request_data, dbi.session)
        if not isinstance(user, UserModel):
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        try:
            ts_mapping_tc = (
                dbi.session.query(TestSpecificationTestCaseModel)
                .filter(TestSpecificationTestCaseModel.id == request_data["relation-id"])
                .one()
            )
        except NoResultFound:
            return f"Unable to find the Test Case mapping to Test Specification id {request_data['relation-id']}", 400

        # Api
        if ts_mapping_tc.test_specification_mapping_api_id:
            try:
                api_ts = (
                    dbi.session.query(ApiTestSpecificationModel)
                    .filter(ApiTestSpecificationModel.id == ts_mapping_tc.test_specification_mapping_api_id)
                    .one()
                )
            except NoResultFound:
                return SW_COMPONENT_NOT_FOUND_MESSAGE, NOT_FOUND_STATUS
            api = api_ts.api
        elif ts_mapping_tc.test_specification_mapping_sw_requirement_id:
            try:
                sr_ts = (
                    dbi.session.query(SwRequirementTestSpecificationModel)
                    .filter(
                        SwRequirementTestSpecificationModel.id
                        == ts_mapping_tc.test_specification_mapping_sw_requirement_id
                    )
                    .one()
                )
            except NoResultFound:
                return SW_COMPONENT_NOT_FOUND_MESSAGE, NOT_FOUND_STATUS
            api_id = get_parent_api_id(sr_ts, dbi.session)
            if not api_id:
                return SW_COMPONENT_NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

            try:
                api = dbi.session.query(ApiModel).filter(ApiModel.id == api_id).one()
            except NoResultFound:
                return SW_COMPONENT_NOT_FOUND_MESSAGE, NOT_FOUND_STATUS
        else:
            return SW_COMPONENT_NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

        # Permissions
        permissions = get_api_user_permissions(api, user.id, user.role, dbi.session)
        if "w" not in permissions or user.role not in USER_ROLES_WRITE_PERMISSIONS:
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        # test_case = ts_mapping_tc.test_case
        # dbi.session.delete(test_case)

        notification_tc_id = ts_mapping_tc.test_case.id
        notification_tc_title = ts_mapping_tc.test_case.title
        dbi.session.delete(ts_mapping_tc)
        dbi.session.commit()

        # Add Notifications
        notification = (
            f"{user.email} deleted test case "
            f"{notification_tc_id} {notification_tc_title} mapping as part of the library {api.library}"
        )
        notifications = NotificationModel(
            api,
            NOTIFICATION_CATEGORY_DELETE,
            f"{api.api}, a test case has been deleted",
            notification,
            str(user.id),
            f"/mapping/{api.id}",
        )
        dbi.session.add(notifications)
        dbi.session.commit()
        return ret


class ForkApiSwRequirement(Resource):
    def post(self):
        request_data = request.get_json(force=True)

        mandatory_fields = ["relation-id"]
        if not check_fields_in_request(mandatory_fields, request_data):
            return "bad request!", 400

        dbi = db_orm.DbInterface(get_db())

        # User
        user = get_active_user_from_request(request_data, dbi.session)
        if not isinstance(user, UserModel):
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        try:
            asr_mapping = (
                dbi.session.query(ApiSwRequirementModel)
                .filter(ApiSwRequirementModel.id == request_data["relation-id"])
                .one()
            )
        except NoResultFound:
            return f"Unable to find the Sw Requirement mapping to Api id {request_data['relation-id']}", 400

        # Permissions
        permissions = get_api_user_permissions(asr_mapping.api, user.id, user.role, dbi.session)
        if "w" not in permissions or user.role not in USER_ROLES_WRITE_PERMISSIONS:
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        new_sr = SwRequirementModel(asr_mapping.sw_requirement.title, asr_mapping.sw_requirement.description, user)
        dbi.session.add(new_sr)
        dbi.session.commit()

        asr_mapping.sw_requirement_id = new_sr.id

        dbi.session.commit()
        return asr_mapping.as_dict()


class ForkSwRequirementSwRequirement(Resource):
    def post(self):
        request_data = request.get_json(force=True)

        mandatory_fields = ["relation-id"]
        if not check_fields_in_request(mandatory_fields, request_data):
            return "bad request!", 400

        dbi = db_orm.DbInterface(get_db())

        # User
        user = get_active_user_from_request(request_data, dbi.session)
        if not isinstance(user, UserModel):
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        try:
            sr_sr_mapping = (
                dbi.session.query(SwRequirementSwRequirementModel)
                .filter(SwRequirementSwRequirementModel.id == request_data["relation-id"])
                .one()
            )
        except NoResultFound:
            return f"Unable to find the Sw Requirement mapping to Sw Requirement id {request_data['relation-id']}", 400

        # Permissions
        api_id = get_parent_api_id(sr_sr_mapping, dbi.session)
        if not api_id:
            return SW_COMPONENT_NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

        try:
            api = dbi.session.query(ApiModel).filter(ApiModel.id == api_id).one()
        except NoResultFound:
            return SW_COMPONENT_NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

        permissions = get_api_user_permissions(api, user.id, user.role, dbi.session)
        if "w" not in permissions or user.role not in USER_ROLES_WRITE_PERMISSIONS:
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        new_sr = SwRequirementModel(sr_sr_mapping.sw_requirement.title, sr_sr_mapping.sw_requirement.description, user)
        dbi.session.add(new_sr)
        dbi.session.commit()

        sr_sr_mapping.sw_requirement_id = new_sr.id

        dbi.session.commit()
        return sr_sr_mapping.as_dict()


class TestingSupportInitDb(Resource):

    def get(self):
        if app.config["TESTING"]:
            app.config["DB"] = "test.db"
            import db.models.init_db as init_db

            init_db.initialization(db_name="test.db")
        return True


class UserLogin(Resource):
    def post(self):
        DATE_FORMAT = "%m/%d/%Y, %H:%M:%S"
        mandatory_fields = ["email", "password"]
        request_data = request.get_json(force=True)
        if not check_fields_in_request(mandatory_fields, request_data):
            return "bad request!", 400

        cache_key = f"{request_data['email']}|{request.remote_addr}"

        if cache_key in login_attempt_cache.keys():
            if login_attempt_cache[cache_key]["attempts"] >= MAX_LOGIN_ATTEMPTS:
                # check last attempt date
                last_attempt_str = login_attempt_cache[cache_key]["last_attempt_dt"]
                last_attempt_dt = datetime.datetime.strptime(last_attempt_str, DATE_FORMAT)
                delta_sec = (datetime.datetime.now() - last_attempt_dt).total_seconds()
                if delta_sec <= MAX_LOGIN_ATTEMPTS_TIMEOUT:
                    return (
                        f"Too many attempts (>= {MAX_LOGIN_ATTEMPTS}) for user {request_data['email']}."
                        f" Retry in {MAX_LOGIN_ATTEMPTS_TIMEOUT/60} minutes.",
                        400,
                    )
                else:
                    login_attempt_cache[cache_key]["attempts"] = 1

        try:
            str_encoded_password = base64.b64encode(request_data["password"].encode("utf-8")).decode("utf-8")
            dbi = db_orm.DbInterface(get_db())
            user = dbi.session.query(UserModel).filter(UserModel.email == request_data["email"]).one()
            if not user.enabled:
                return "This user has been disabled, please contact your BASIL admin.", 400
            if user.pwd != str_encoded_password:
                if cache_key in login_attempt_cache.keys():
                    login_attempt_cache[cache_key]["attempts"] = login_attempt_cache[cache_key]["attempts"] + 1
                else:
                    login_attempt_cache[cache_key] = {"attempts": 1}

                login_attempt_cache[cache_key]["last_attempt_dt"] = datetime.datetime.now().strftime(DATE_FORMAT)

                return f"Wrong credentials for user {request_data['email']}", 400

        except NoResultFound:
            return "Email not assigned to any user, consider to sign in.", 400

        # Login success, clear login attempt cache for that ip
        if cache_key in login_attempt_cache.keys():
            del login_attempt_cache[cache_key]

        # Refresh user token
        user.token = str(uuid4())
        dbi.session.add(user)
        dbi.session.commit()

        return {"id": user.id, "role": user.role, "email": user.email, "token": user.token}


class UserSignin(Resource):
    def post(self):
        mandatory_fields = ["email", "password"]
        request_data = request.get_json(force=True)
        if not check_fields_in_request(mandatory_fields, request_data):
            return "bad request!", 400

        dbi = db_orm.DbInterface(get_db())

        same_email = dbi.session.query(UserModel).filter(UserModel.email == request_data["email"]).all()
        if len(same_email) > 0:
            return "Email already in use.", 400

        user = UserModel(request_data["email"].strip(), request_data["password"], "GUEST")
        dbi.session.add(user)
        dbi.session.commit()  # To have the user id

        # Deny access to restricted software components
        set_api_permission_stmt = (update(ApiModel).where(ApiModel.read_denials != '')).values(
            read_denials=ApiModel.read_denials + f"[{user.id}]")
        dbi.session.execute(set_api_permission_stmt)
        print(set_api_permission_stmt)

        # Add Notifications
        notification = f"{user.email} joined us on BASIL!"
        notifications = NotificationModel(None, NOTIFICATION_CATEGORY_NEW, "New user!", notification, str(user.id), "")
        dbi.session.add(notifications)
        dbi.session.commit()

        return {"id": user.id, "email": user.email, "token": user.token}


class UserApis(Resource):
    def get(self):
        """List of software components for the ones the user has owner permissions
        without the api with api-id

        This endpoint is used to list the apis that can be used in the permission copy
        """
        # Requester identified by id and token
        # Email is related to the user for who I need to know api permissions
        mandatory_fields = ["api-id", "token", "user-id"]
        request_data = request.args

        if not check_fields_in_request(mandatory_fields, request_data):
            return BAD_REQUEST_MESSAGE, BAD_REQUEST_STATUS

        dbi = db_orm.DbInterface(get_db())

        user = get_active_user_from_request(request_data, dbi.session)
        if not user:
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        # api
        try:
            api = dbi.session.query(ApiModel).filter(ApiModel.id == request_data["api-id"]).one()
        except NoResultFound:
            return "Software component not found.", 402

        # check requester user api permission
        user_permissions = get_api_user_permissions(api, user.id, user.role, dbi.session)
        if "m" not in user_permissions or user.role not in USER_ROLES_MANAGE_PERMISSIONS:
            return f"Operation not allowed for user {user.email}", 405

        # apis
        query = dbi.session.query(ApiModel).filter(
            or_(ApiModel.manage_permissions.like(f'%[{user.id}]%'),
                ApiModel.created_by_id == user.id)
            ).filter(ApiModel.id != api.id)

        if "search" in request_data.keys():
            search = request_data["search"]
            query = query    .filter(
                    or_(ApiModel.api.like(f'%{search}%'),
                        ApiModel.library.like(f'%{search}%'),
                        ApiModel.library_version.like(f'%{search}%'),
                        ApiModel.category.like(f'%{search}%'),
                        ApiModel.tags.like(f'%{search}%'),)
                )
        query = query.order_by(ApiModel.api.asc())
        apis = query.all()

        ret = []
        for current_api in apis:
            current_api_dict = current_api.as_dict()
            del current_api_dict["raw_specification_url"]
            del current_api_dict["category"]
            del current_api_dict["checksum"]
            del current_api_dict["default_view"]
            del current_api_dict["implementation_file"]
            del current_api_dict["implementation_file_from_row"]
            del current_api_dict["implementation_file_to_row"]
            del current_api_dict["edited_by"]
            del current_api_dict["last_coverage"]
            del current_api_dict["tags"]
            del current_api_dict["created_by"]
            current_api_dict["selected"] = 1
            if current_api.delete_permissions != api.delete_permissions:
                current_api_dict["selected"] = 0
            if current_api.edit_permissions != api.edit_permissions:
                current_api_dict["selected"] = 0
            if current_api.manage_permissions != api.manage_permissions:
                current_api_dict["selected"] = 0
            if current_api.read_denials != api.read_denials:
                current_api_dict["selected"] = 0
            if current_api.write_permissions != api.write_permissions:
                current_api_dict["selected"] = 0
            ret.append(current_api_dict)
        return ret


class UserPermissionsApiCopy(Resource):
    def put(self):
        """Copy user permissions from api identified by api-id to the ones
        specified in the copy-to list

        User that is making the request is identified by user-id and token

        Need to check that user has the owner permissions for each api defined in copy-to
        """
        mandatory_fields = ["api-id", "copy-to", "token", "user-id"]
        request_data = request.get_json(force=True)

        if not check_fields_in_request(mandatory_fields, request_data):
            return "bad request!", 400

        dbi = db_orm.DbInterface(get_db())

        user = get_active_user_from_request(request_data, dbi.session)
        if not isinstance(user, UserModel):
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        # api
        try:
            api = dbi.session.query(ApiModel).filter(ApiModel.id == request_data["api-id"]).one()
        except NoResultFound:
            return "Software component not found.", 402

        # check requester user api permission
        user_permissions = get_api_user_permissions(api, user.id, user.role, dbi.session)
        if "m" not in user_permissions or user.role not in USER_ROLES_MANAGE_PERMISSIONS:
            return f"Operation not allowed for user {user.email}", 405

        for copy_to_api_id in request_data["copy-to"]:
            try:
                copy_to_api = dbi.session.query(ApiModel).filter(ApiModel.id == copy_to_api_id).one()
            except NoResultFound:
                return "Software component not found.", 402

            # check requester user api permission
            user_permissions = get_api_user_permissions(copy_to_api, user.id, user.role, dbi.session)
            if "m" not in user_permissions or user.role not in USER_ROLES_MANAGE_PERMISSIONS:
                return f"Operation not allowed for user {user.email}", 405

            copy_to_api.delete_permissions = api.delete_permissions
            copy_to_api.edit_permissions = api.edit_permissions
            copy_to_api.manage_permissions = api.manage_permissions
            copy_to_api.read_denials = api.read_denials
            copy_to_api.write_permissions = api.write_permissions
            dbi.session.add(copy_to_api)

        dbi.session.commit()

        return {"result": "success"}


class UserPermissionsApi(Resource):
    def get(self):
        # Requester identified by id and token
        # Email is related to the user for who I need to know api permissions
        mandatory_fields = ["api-id", "token", "user-id"]
        request_data = request.args

        if not check_fields_in_request(mandatory_fields, request_data):
            return BAD_REQUEST_MESSAGE, BAD_REQUEST_STATUS

        dbi = db_orm.DbInterface(get_db())

        user = get_active_user_from_request(request_data, dbi.session)
        if not user:
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        # api
        try:
            api = dbi.session.query(ApiModel).filter(ApiModel.id == request_data["api-id"]).one()
        except NoResultFound:
            return "Software component not found.", 402

        # check requester user api permission
        user_permissions = get_api_user_permissions(api, user.id, user.role, dbi.session)
        if "m" not in user_permissions or user.role not in USER_ROLES_MANAGE_PERMISSIONS:
            return f"Operation not allowed for user {user.email}", 405

        query = dbi.session.query(UserModel).filter(
            UserModel.id != user.id
        ).filter(
            UserModel.role != 'GUEST'
        ).filter(
            UserModel.enabled == 1
        )
        if "search" in request_data.keys():
            query = query.filter(UserModel.email.like(f"%{request_data['search']}%"))

        users = query.all()
        users_dict = [user.as_dict() for user in users]
        for i in range(len(users_dict)):
            users_dict[i]["permissions"] = get_api_user_permissions(api,
                                                                    users_dict[i]['id'],
                                                                    users_dict[i]['role'],
                                                                    dbi.session)
            del users_dict[i]["api_notifications"]
        return users_dict

    def put(self):
        # Requester identified by id and token
        # Email is related to the user for who I need to know api permissions
        mandatory_fields = ["api-id", "permissions", "token", "user-id"]
        request_data = request.get_json(force=True)

        if not check_fields_in_request(mandatory_fields, request_data):
            return "bad request!", 400

        dbi = db_orm.DbInterface(get_db())

        user = get_active_user_from_request(request_data, dbi.session)
        if not isinstance(user, UserModel):
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        # api
        try:
            api = dbi.session.query(ApiModel).filter(ApiModel.id == request_data["api-id"]).one()
        except NoResultFound:
            return "Software component not found.", 402

        # check requester user api permission
        user_permissions = get_api_user_permissions(api, user.id, user.role, dbi.session)
        if "m" not in user_permissions or user.role not in USER_ROLES_MANAGE_PERMISSIONS:
            return f"Operation not allowed for user {user.email}", 405

        for user_permission in request_data["permissions"]:
            try:
                target_user = dbi.session.query(UserModel).filter(
                    UserModel.id == user_permission["id"]).filter(
                    UserModel.role != 'GUEST').one()
            except NoResultFound:
                return f"User {request_data['email']} not found.", 403

            permission_string = f"[{target_user.id}]"

            # Edit Permission
            if "e" in user_permission["permissions"]:
                if permission_string not in api.edit_permissions:
                    api.edit_permissions += permission_string
            else:
                if permission_string in api.edit_permissions:
                    api.edit_permissions = api.edit_permissions.replace(permission_string, "")

            # Manage Permission
            if "m" in user_permission["permissions"]:
                if permission_string not in api.manage_permissions:
                    api.manage_permissions += permission_string
            else:
                if permission_string in api.manage_permissions:
                    api.manage_permissions = api.manage_permissions.replace(permission_string, "")

            # Read Permission
            if "r" in user_permission["permissions"]:
                if permission_string in api.read_denials:
                    api.read_denials = api.read_denials.replace(permission_string, "")
                    if api.read_denials == "[0]":
                        api.read_denials = ""
            else:
                if permission_string not in api.read_denials:
                    api.read_denials += permission_string
                    if "[0]" not in api.read_denials:
                        api.read_denials += "[0]"

            # Write Permission
            if "w" in user_permission["permissions"]:
                if permission_string not in api.write_permissions:
                    api.write_permissions += permission_string
            else:
                if permission_string in api.write_permissions:
                    api.write_permissions = api.write_permissions.replace(permission_string, "")

        dbi.session.add(api)
        dbi.session.commit()

        return {"result": "success"}


class UserEnable(Resource):

    def put(self):
        # Requester identified by id and token
        # Email is related to the user for who I need to change the status
        mandatory_fields = ["email", "token", "user-id", "enabled"]
        request_data = request.get_json(force=True)

        if not check_fields_in_request(mandatory_fields, request_data):
            return "bad request!", 400

        dbi = db_orm.DbInterface(get_db())

        user = get_active_user_from_request(request_data, dbi.session)
        if not isinstance(user, UserModel):
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        if user.role not in USER_ROLES_MANAGE_USERS:
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        try:
            target_user = dbi.session.query(UserModel).filter(UserModel.email == request_data["email"]).one()
        except NoResultFound:
            return f"User {request_data['email']} not found.", 403

        target_user.enabled = int(request_data["enabled"])

        dbi.session.add(target_user)
        dbi.session.commit()

        return {"email": request_data["email"], "enabled": target_user.enabled}


class User(Resource):

    def get(self):
        # Requester identified by id and token
        mandatory_fields = ["user-id", "token"]
        request_data = request.args

        if not check_fields_in_request(mandatory_fields, request_data):
            return "bad request!", 400

        dbi = db_orm.DbInterface(get_db())

        user = get_active_user_from_request(request_data, dbi.session)
        if not isinstance(user, UserModel):
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        if user.role != "ADMIN":
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        users = dbi.session.query(UserModel).filter(UserModel.id != request_data["user-id"]).all()
        # users = [{k: v for k, v in user.as_dict().items() if k not in ['pwd']} for user in users]

        return [x.as_dict(full_data=True) for x in users]


class UserResetPassword(Resource):

    def put(self):
        # Requester identified by id and token
        # Email is related to the user for who I need to change the status
        mandatory_fields = ["email", "token", "user-id", "password"]
        request_data = request.get_json(force=True)

        if not check_fields_in_request(mandatory_fields, request_data):
            return BAD_REQUEST_MESSAGE, BAD_REQUEST_STATUS

        dbi = db_orm.DbInterface(get_db())

        user = get_active_user_from_request(request_data, dbi.session)
        if not isinstance(user, UserModel):
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        if user.role not in USER_ROLES_MANAGE_USERS:
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        try:
            target_user = dbi.session.query(UserModel).filter(UserModel.email == request_data["email"]).one()
        except NoResultFound:
            return f"User {request_data['email']} not found.", 403

        target_user.pwd = request_data["password"]
        dbi.session.commit()

        return {"email": request_data["email"]}


class UserRole(Resource):

    def put(self):
        # Requester identified by id and token
        # Email is related to the user for who I need to change the role
        mandatory_fields = ["email", "token", "user-id", "role"]
        request_data = request.get_json(force=True)

        if not check_fields_in_request(mandatory_fields, request_data):
            return BAD_REQUEST_MESSAGE, BAD_REQUEST_STATUS

        if not request_data["role"] in ["ADMIN", "GUEST", "USER"]:
            return BAD_REQUEST_MESSAGE, BAD_REQUEST_STATUS

        dbi = db_orm.DbInterface(get_db())

        user = get_active_user_from_request(request_data, dbi.session)
        if not isinstance(user, UserModel):
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        if user.role not in USER_ROLES_MANAGE_USERS:
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        try:
            target_user = dbi.session.query(UserModel).filter(UserModel.email == request_data["email"]).one()
        except NoResultFound:
            return f"User {request_data['email']} not found.", 403

        target_user.role = request_data["role"]
        dbi.session.commit()

        return {"email": request_data["email"]}


class UserNotifications(Resource):

    def delete(self):
        mandatory_fields = ["token", "user-id"]
        request_data = request.get_json(force=True)
        if not check_fields_in_request(mandatory_fields, request_data):
            return BAD_REQUEST_MESSAGE, BAD_REQUEST_STATUS

        dbi = db_orm.DbInterface(get_db())

        user = get_active_user_from_request(request_data, dbi.session)
        if not isinstance(user, UserModel):
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        # It should be possible to delete 1 notification filtering with `id`
        # It should be possible to clear all the notifications if `id` is not defined
        if "id" in request_data.keys():
            try:
                notifications = (
                    dbi.session.query(NotificationModel).filter(NotificationModel.id == request_data["id"]).all()
                )
            except NoResultFound:
                return NOT_FOUND_MESSAGE, NOT_FOUND_STATUS
        else:

            user_api_notifications = user.api_notifications.replace(" ", "").split(",")
            user_api_notifications = [int(x) for x in user_api_notifications]  # Need list of int

            NoneVar = None  # To avoid flake8 warning comparing with None with `==` instead of `is`
            notifications = (
                dbi.session.query(NotificationModel)
                .filter(or_(NotificationModel.api_id.in_(user_api_notifications), NotificationModel.api_id == NoneVar))
                .order_by(NotificationModel.created_at.desc())
                .all()
            )

        for i in range(len(notifications)):
            read_by = notifications[i].read_by.split(",")
            if user.id not in read_by:
                read_by.append(user.id)
            notifications[i].read_by = ",".join([str(x) for x in read_by])

        dbi.session.commit()
        return "Notification updated"

    def get(self):
        undesired_keys = ["ready_by"]
        request_data = request.args

        dbi = db_orm.DbInterface(get_db())

        user = get_active_user_from_request(request_data, dbi.session)
        if not isinstance(user, UserModel):
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        user_api_notifications = []
        if user.api_notifications:
            user_api_notifications = user.api_notifications.replace(" ", "").split(",")
            user_api_notifications = [int(x) for x in user_api_notifications]  # Need list of int

        NoneVar = None  # To avoid flake8 warning comparing with None with `==` instead of `is`
        notifications = (
            dbi.session.query(NotificationModel)
            .filter(or_(NotificationModel.api_id.in_(user_api_notifications), NotificationModel.api_id == NoneVar))
            .order_by(NotificationModel.created_at.desc())
            .all()
        )

        tmp = [x.as_dict() for x in notifications]
        tmp = [get_dict_without_keys(x, undesired_keys) for x in tmp if str(user.id) not in x["read_by"]]
        return tmp

    def put(self):
        mandatory_fields = ["api-id", "notifications", "token", "user-id"]
        request_data = request.get_json(force=True)
        if not check_fields_in_request(mandatory_fields, request_data):
            return BAD_REQUEST_MESSAGE, BAD_REQUEST_STATUS

        dbi = db_orm.DbInterface(get_db())

        user = get_active_user_from_request(request_data, dbi.session)
        if not isinstance(user, UserModel):
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        if not user.api_notifications:
            user_api_notifications = []
        else:
            user_api_notifications = user.api_notifications.replace(" ", "").split(",")
            user_api_notifications = [int(x) for x in user_api_notifications]  # Need list of int

        api_id = int(request_data["api-id"])
        if request_data["notifications"] == 0:
            if api_id in user_api_notifications:
                user_api_notifications.remove(api_id)
        elif request_data["notifications"] == 1:
            if api_id not in user_api_notifications:
                user_api_notifications.append(api_id)

        user.api_notifications = ",".join([str(x) for x in user_api_notifications])
        dbi.session.add(user)
        dbi.session.commit()
        return "Notification updated"


class Testing(Resource):
    def get(self):
        request_data = request.args
        dbi = db_orm.DbInterface(get_db())
        if "mapped_to_id" not in request_data.keys():
            return "wrong input", 400

        """
        mapping = dbi.session.query(SwRequirementSwRequirementModel).filter(
            SwRequirementSwRequirementModel.id == request_data['mapped_to_id']
        ).one()
        """

        mapping = (
            dbi.session.query(SwRequirementTestCaseModel)
            .filter(SwRequirementTestCaseModel.id == request_data["mapped_to_id"])
            .one()
        )

        return get_parent_api_id(mapping, dbi.session)


class UserSshKey(Resource):
    fields = get_model_editable_fields(SshKeyModel, False)

    def get(self):
        args = get_query_string_args(request.args)
        dbi = db_orm.DbInterface(get_db())

        # User
        user_id = get_user_id_from_request(args, dbi.session)
        if user_id == 0:
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        ssh_keys = (
            dbi.session.query(SshKeyModel)
            .filter(SshKeyModel.created_by_id == user_id)
            .order_by(SshKeyModel.created_at.desc())
            .all()
        )
        ssh_keys = [x.as_dict(full_data=True) for x in ssh_keys]
        return ssh_keys

    def post(self):
        request_data = request.get_json(force=True)

        if not check_fields_in_request(self.fields, request_data):
            return "bad request!", 400

        dbi = db_orm.DbInterface(get_db())

        # User
        user = get_active_user_from_request(request_data, dbi.session)
        if not isinstance(user, UserModel):
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        title = request_data["title"].strip()
        ssh_key = request_data["ssh_key"].strip()
        if title == "" or ssh_key == "":
            return BAD_REQUEST_MESSAGE, BAD_REQUEST_STATUS

        existing = (
            dbi.session.query(SshKeyModel)
            .filter(SshKeyModel.title == title, SshKeyModel.created_by_id == user.id)
            .all()
        )

        if len(existing):
            return CONFLICT_MESSAGE, CONFLICT_STATUS

        new_ssh_key = SshKeyModel(title, ssh_key, user)
        dbi.session.add(new_ssh_key)
        dbi.session.commit()

        # File creation and permissions set
        if not os.path.exists(SSH_KEYS_PATH):
            os.mkdir(SSH_KEYS_PATH)

        f = open(f"{SSH_KEYS_PATH}/{new_ssh_key.id}", "w")
        f.write(f"{new_ssh_key.ssh_key.strip()}\n")
        f.close()

        os.chmod(f"{SSH_KEYS_PATH}/{new_ssh_key.id}", 0o600)

        if not os.path.exists(f"{SSH_KEYS_PATH}/{new_ssh_key.id}"):
            dbi.session.delete(new_ssh_key)
            dbi.session.commit()
            return "Error", 400

        return new_ssh_key.as_dict()

    def delete(self):
        request_data = request.get_json(force=True)

        if not check_fields_in_request(["id"], request_data):
            return "bad request!", 400

        dbi = db_orm.DbInterface(get_db())

        # User
        user = get_active_user_from_request(request_data, dbi.session)
        if not isinstance(user, UserModel):
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        try:
            ssh_key = dbi.session.query(SshKeyModel).filter(SshKeyModel.id == request_data["id"]).one()
        except NoResultFound:
            return NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

        if ssh_key.created_by.id != user.id:
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        dbi.session.delete(ssh_key)
        dbi.session.commit()

        if os.path.exists(f"{SSH_KEYS_PATH}/{ssh_key.id}"):
            os.remove(f"{SSH_KEYS_PATH}/{ssh_key.id}")

        return True


class UserFiles(Resource):

    def get(self):
        ret = []
        args = get_query_string_args(request.args)
        dbi = db_orm.DbInterface(get_db())

        # User
        user_id = get_user_id_from_request(args, dbi.session)
        if user_id == 0:
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        dbi.session.close()
        dbi.engine.dispose()

        user_files_path = os.path.join(USER_FILES_BASE_DIR, f"{user_id}")
        if not os.path.exists(user_files_path):
            os.makedirs(user_files_path, exist_ok=True)
            return ret

        i = 0
        for user_file in os.listdir(user_files_path):
            tmp = {
                "index": i,
                "filepath": os.path.join(user_files_path, user_file),
                "updated_at": time.ctime(os.path.getmtime(os.path.join(user_files_path, user_file))),
            }
            ret.append(tmp)
            i += 1

        ret = sorted(ret, key=lambda f: f["filepath"], reverse=False)  # sort by filename
        return ret

    def post(self):
        fields = ["filename", "filecontent"]
        request_data = request.get_json(force=True)

        if not check_fields_in_request(fields, request_data):
            return BAD_REQUEST_MESSAGE, BAD_REQUEST_STATUS

        dbi = db_orm.DbInterface(get_db())

        # User
        user_id = get_user_id_from_request(request_data, dbi.session)
        if user_id == 0:
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        dbi.session.close()
        dbi.engine.dispose()

        user_files_path = os.path.join(USER_FILES_BASE_DIR, f"{user_id}")
        if not os.path.exists(user_files_path):
            os.makedirs(user_files_path, exist_ok=True)

        filename = request_data["filename"]
        filecontent = request_data["filecontent"]
        filepath = os.path.join(user_files_path, filename)

        if filename == "" or filecontent == "":
            return BAD_REQUEST_MESSAGE, BAD_REQUEST_STATUS

        if os.path.exists(filepath):
            return CONFLICT_MESSAGE, CONFLICT_STATUS

        f = open(filepath, "w")
        f.write(filecontent)
        f.close()

        if not os.path.exists(filepath):
            return NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

        ret = {
            "index": 0,
            "filepath": filepath,
            "updated_at": time.ctime(os.path.getmtime(filepath))
            }
        return ret

    def delete(self):
        fields = ["filename"]
        request_data = request.get_json(force=True)

        if not check_fields_in_request(fields, request_data):
            return BAD_REQUEST_MESSAGE, BAD_REQUEST_STATUS

        dbi = db_orm.DbInterface(get_db())

        # User
        user_id = get_user_id_from_request(request_data, dbi.session)
        if user_id == 0:
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        dbi.session.close()
        dbi.engine.dispose()

        user_files_path = os.path.join(USER_FILES_BASE_DIR, f"{user_id}")
        if not os.path.exists(user_files_path):
            os.makedirs(user_files_path, exist_ok=True)
            return NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

        filename = request_data["filename"]
        filepath = os.path.join(user_files_path, filename)

        if filename == "":
            return BAD_REQUEST_MESSAGE, BAD_REQUEST_STATUS

        if not os.path.exists(filepath):
            return NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

        os.remove(filepath)

        if os.path.exists(filepath):
            return CONFLICT_MESSAGE, CONFLICT_STATUS

        ret = {"index": 0,
               "filepath": filepath,
               "updated_at": ""}
        return ret


class UserFileContent(Resource):

    def get(self):
        fields = ["filename"]
        ret = {}
        args = request.args

        if not check_fields_in_request(fields, args):
            return BAD_REQUEST_MESSAGE, BAD_REQUEST_STATUS

        dbi = db_orm.DbInterface(get_db())

        # User
        user_id = get_user_id_from_request(args, dbi.session)
        if user_id == 0:
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        dbi.session.close()
        dbi.engine.dispose()

        user_files_path = os.path.join(USER_FILES_BASE_DIR, f"{user_id}")
        if not os.path.exists(user_files_path):
            os.makedirs(user_files_path, exist_ok=True)
            return NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

        filepath = os.path.join(user_files_path, args["filename"])
        if not os.path.exists(filepath):
            return NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

        f = open(filepath, "r")
        filecontent = f.read()
        f.close()

        ret = {
            "index": 0,
            "filepath": filepath,
            "filecontent": filecontent,
            "updated_at": time.ctime(os.path.getmtime(os.path.join(filepath))),
        }

        return ret

    def put(self):
        fields = ["filename", "filecontent"]
        request_data = request.get_json(force=True)

        if not check_fields_in_request(fields, request_data):
            return BAD_REQUEST_MESSAGE, BAD_REQUEST_STATUS

        dbi = db_orm.DbInterface(get_db())

        # User
        user_id = get_user_id_from_request(request_data, dbi.session)
        if user_id == 0:
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        dbi.session.close()
        dbi.engine.dispose()

        user_files_path = os.path.join(USER_FILES_BASE_DIR, f"{user_id}")
        if not os.path.exists(user_files_path):
            os.makedirs(user_files_path, exist_ok=True)
            return NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

        filename = request_data["filename"]
        filecontent = request_data["filecontent"]
        filepath = os.path.join(user_files_path, filename)

        if filename == "" or filecontent == "":
            return BAD_REQUEST_MESSAGE, BAD_REQUEST_STATUS

        if not os.path.exists(filepath):
            return NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

        f = open(filepath, "w")
        f.write(filecontent)
        f.close()

        if not os.path.exists(filepath):
            return NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

        ret = {
            "index": 0,
            "filepath": filepath,
            "filecontent": filecontent,
            "updated_at": time.ctime(os.path.getmtime(filepath)),
        }
        return ret


class TestRunConfig(Resource):
    # Do not support delete, put and post
    # Once a Test Run has been executed the Test Run Config is defined
    # and should be accessible in future to identify the Test Run
    # A new Test Config is created by the Test Run post endpoint

    fields = get_model_editable_fields(TestRunConfigModel, False)

    def get(self):

        args = get_query_string_args(request.args)
        dbi = db_orm.DbInterface(get_db())

        # User
        user_id = get_user_id_from_request(args, dbi.session)
        if user_id == 0:
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        query = dbi.session.query(TestRunConfigModel).filter(TestRunConfigModel.created_by_id == user_id)

        if "search" in args.keys():
            query = query.filter(
                or_(
                    TestRunConfigModel.title.like(f'%{args["search"]}%'),
                    TestRunConfigModel.provision_guest.like(f'%{args["search"]}%'),
                    TestRunConfigModel.provision_guest_port.like(f'%{args["search"]}%'),
                    TestRunConfigModel.environment_vars.like(f'%{args["search"]}%'),
                    TestRunConfigModel.context_vars.like(f'%{args["search"]}%'),
                )
            )

        configs = query.order_by(TestRunConfigModel.created_at.desc()).all()

        configs = [x.as_dict(full_data=True) for x in configs]
        return configs

    def post(self):
        request_data = request.get_json(force=True)

        dbi = db_orm.DbInterface(get_db())

        # User
        user = get_active_user_from_request(request_data, dbi.session)
        if not isinstance(user, UserModel):
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        # Test Run Configuration
        test_config_ret, test_config_status = add_test_run_config(dbi, request_data, user)
        if test_config_status not in [OK_STATUS, CREATED_STATUS]:
            return test_config_ret, test_config_status
        else:
            test_config = test_config_ret

        return test_config.as_dict()


class TestRun(Resource):
    fields = get_model_editable_fields(TestRunModel, False)

    def get(self):
        mandatory_fields = ["api-id", "mapped_to_type", "mapped_to_id"]
        args = get_query_string_args(request.args)
        if not check_fields_in_request(mandatory_fields, args):
            return BAD_REQUEST_MESSAGE, BAD_REQUEST_STATUS

        dbi = db_orm.DbInterface(get_db())

        # User
        user = get_active_user_from_request(args, dbi.session)
        if isinstance(user, UserModel):
            user_id = user.id
            user_role = user.role
        else:
            user_id = 0
            user_role = ''

        # Find api
        api = get_api_from_request(args, dbi.session)
        if not api:
            return NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

        # Permissions
        permissions = get_api_user_permissions(api, user_id, user_role, dbi.session)
        if "r" not in permissions:
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        runs_query = (
            dbi.session.query(TestRunModel)
            .join(TestRunConfigModel)
            .filter(
                TestRunModel.api_id == api.id,
                TestRunModel.mapping_to == args["mapped_to_type"],
                TestRunModel.mapping_id == args["mapped_to_id"],
            )
        )

        if "search" in args.keys():
            search = args["search"]
            runs_query = runs_query.filter(
                or_(
                    TestRunModel.id.like(f"%{search}%"),
                    TestRunModel.uid.like(f"%{search}%"),
                    TestRunModel.title.like(f"%{search}%"),
                    TestRunModel.notes.like(f"%{search}%"),
                    TestRunModel.bugs.like(f"%{search}%"),
                    TestRunModel.fixes.like(f"%{search}%"),
                    TestRunModel.report.like(f"%{search}%"),
                    TestRunModel.result.like(f"%{search}%"),
                    TestRunModel.created_at.like(f"%{search}%"),
                    TestRunConfigModel.title.like(f"%{search}%"),
                    TestRunConfigModel.provision_type.like(f"%{search}%"),
                    TestRunConfigModel.git_repo_ref.like(f"%{search}%"),
                    TestRunConfigModel.context_vars.like(f"%{search}%"),
                    TestRunConfigModel.environment_vars.like(f"%{search}%"),
                    TestRunConfigModel.provision_guest.like(f"%{search}%"),
                    TestRunConfigModel.provision_guest_port.like(f"%{search}%"),
                )
            )

        runs = runs_query.order_by(TestRunModel.created_at.desc()).all()

        runs = [x.as_dict(full_data=True) for x in runs]
        return runs

    def post(self):
        request_data = request.get_json(force=True)
        mandatory_fields = ["api-id", "title", "notes", "test-run-config", "mapped_to_type", "mapped_to_id"]
        if not check_fields_in_request(mandatory_fields, request_data):
            return BAD_REQUEST_MESSAGE, BAD_REQUEST_STATUS

        dbi = db_orm.DbInterface(get_db())

        # User
        user = get_active_user_from_request(request_data, dbi.session)
        if not isinstance(user, UserModel):
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        # Find api
        api = get_api_from_request(request_data, dbi.session)
        if not api:
            return NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

        # Test Run Configuration
        test_config_ret, test_config_status = add_test_run_config(dbi, request_data["test-run-config"], user)
        if test_config_status not in [OK_STATUS, CREATED_STATUS]:
            return test_config_ret, test_config_status
        else:
            test_config = test_config_ret

        # Test Run
        title = request_data["title"].strip()
        notes = request_data["notes"].strip()
        mapping_to = str(request_data["mapped_to_type"]).strip()
        mapping_id = request_data["mapped_to_id"]

        # Check mandatory fields
        if title == "" or mapping_to == "" or mapping_id == "":
            return BAD_REQUEST_MESSAGE, BAD_REQUEST_STATUS

        mapping_model = None
        if mapping_to == ApiTestCaseModel.__tablename__:
            mapping_model = ApiTestCaseModel
        elif mapping_to == SwRequirementTestCaseModel.__tablename__:
            mapping_model = SwRequirementTestCaseModel
        elif mapping_to == TestSpecificationTestCaseModel.__tablename__:
            mapping_model = TestSpecificationTestCaseModel
        else:
            return BAD_REQUEST_MESSAGE, BAD_REQUEST_STATUS

        try:
            mapping = dbi.session.query(mapping_model).filter(mapping_model.id == mapping_id).one()
        except NoResultFound:
            return NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

        # Create the Test Config only if the Test Run data is consistent
        dbi.session.commit()
        new_test_run = TestRunModel(api, title, notes, test_config, mapping_to, mapping_id, user)

        if "report" in request_data.keys():
            new_test_run.report = request_data["report"]
        if "result" in request_data.keys():
            new_test_run.result = request_data["result"]
        if "status" in request_data.keys():
            new_test_run.status = request_data["status"]

        dbi.session.add(new_test_run)
        dbi.session.commit()

        # Start the detached process to run the test async
        if new_test_run.status == "created":
            cmd = (
                f"python3 {os.path.join(currentdir, 'testrun.py')} --id {new_test_run.id} "
                f"&> {TEST_RUNS_BASE_DIR}/{new_test_run.uid}.log &"
            )
            os.system(cmd)

            # Notification
            notification = (
                f"{user.email} started a Test Run for Test Case "
                f"{mapping.test_case.title} as part of the sw component "
                f"{api.api}, library {api.library}"
            )
            notifications = NotificationModel(
                api,
                "info",
                f"Test Run for {api.api} has been requested",
                notification,
                str(user.id),
                f"/mapping/{api.id}",
            )
            dbi.session.add(notifications)
            dbi.session.commit()

        return new_test_run.as_dict()

    def put(self):
        request_data = request.get_json(force=True)
        mandatory_fields = ["api-id", "id", "bugs", "fixes", "notes", "mapped_to_type", "mapped_to_id"]
        if not check_fields_in_request(mandatory_fields, request_data):
            return BAD_REQUEST_MESSAGE, BAD_REQUEST_STATUS

        dbi = db_orm.DbInterface(get_db())

        # User
        user = get_active_user_from_request(request_data, dbi.session)
        if not isinstance(user, UserModel):
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        # Find api
        api = get_api_from_request(request_data, dbi.session)
        if not api:
            return NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

        # Permissions
        permissions = get_api_user_permissions(api, user.id, user.role, dbi.session)
        if "r" not in permissions:
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        mapping_model = None
        mapping_to = request_data["mapped_to_type"]
        mapping_id = request_data["mapped_to_id"]
        if mapping_to == ApiTestCaseModel.__tablename__:
            mapping_model = ApiTestCaseModel
        elif mapping_to == SwRequirementTestCaseModel.__tablename__:
            mapping_model = SwRequirementTestCaseModel
        elif mapping_to == TestSpecificationTestCaseModel.__tablename__:
            mapping_model = TestSpecificationTestCaseModel
        else:
            return BAD_REQUEST_MESSAGE, BAD_REQUEST_STATUS

        try:
            mapping = dbi.session.query(mapping_model).filter(mapping_model.id == mapping_id).one()
        except NoResultFound:
            return NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

        try:
            run = (
                dbi.session.query(TestRunModel)
                .filter(
                    TestRunModel.api_id == api.id,
                    TestRunModel.id == request_data["id"],
                    TestRunModel.mapping_to == mapping_to,
                    TestRunModel.mapping_id == mapping_id,
                )
                .one()
            )
        except NoResultFound:
            return NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

        test_run_modified = False
        if run.bugs != request_data["bugs"]:
            test_run_modified = True
            run.bugs = request_data["bugs"]

        if run.fixes != request_data["fixes"]:
            test_run_modified = True
            run.fixes = request_data["fixes"]

        if run.notes != request_data["notes"]:
            test_run_modified = True
            run.notes = request_data["notes"]

        if test_run_modified:
            dbi.session.add(run)
            dbi.session.commit()

            # Notification
            notification = (
                f"{user.email} modified a Test Run for Test Case "
                f"{mapping.test_case.title} as part of the sw component "
                f"{api.api}, library {api.library}.\nBugs: {run.bugs}"
            )
            notifications = NotificationModel(
                api,
                "info",
                f"Test Run for {api.api} has been modified",
                notification,
                str(user.id),
                f"/mapping/{api.id}",
            )
            dbi.session.add(notifications)
            dbi.session.commit()

        return run.as_dict()

    def delete(self):
        request_data = request.get_json(force=True)
        mandatory_fields = ["api-id", "id", "mapped_to_type", "mapped_to_id"]
        if not check_fields_in_request(mandatory_fields, request_data):
            return BAD_REQUEST_MESSAGE, BAD_REQUEST_STATUS

        dbi = db_orm.DbInterface(get_db())

        # User
        user = get_active_user_from_request(request_data, dbi.session)
        if not isinstance(user, UserModel):
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        # Find api
        api = get_api_from_request(request_data, dbi.session)
        if not api:
            return NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

        # Permissions
        permissions = get_api_user_permissions(api, user.id, user.role, dbi.session)
        if "w" not in permissions:
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        mapping_model = None
        mapping_to = request_data["mapped_to_type"]
        mapping_id = request_data["mapped_to_id"]
        if mapping_to == ApiTestCaseModel.__tablename__:
            mapping_model = ApiTestCaseModel
        elif mapping_to == SwRequirementTestCaseModel.__tablename__:
            mapping_model = SwRequirementTestCaseModel
        elif mapping_to == TestSpecificationTestCaseModel.__tablename__:
            mapping_model = TestSpecificationTestCaseModel
        else:
            return BAD_REQUEST_MESSAGE, BAD_REQUEST_STATUS

        try:
            mapping = dbi.session.query(mapping_model).filter(mapping_model.id == mapping_id).one()
        except NoResultFound:
            return NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

        try:
            run = (
                dbi.session.query(TestRunModel)
                .filter(
                    TestRunModel.api_id == api.id,
                    TestRunModel.id == request_data["id"],
                    TestRunModel.mapping_to == mapping_to,
                    TestRunModel.mapping_id == mapping_id,
                )
                .one()
            )
        except NoResultFound:
            return NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

        run_dict = run.as_dict()
        dbi.session.delete(run)
        dbi.session.commit()

        # Remove folder
        run_path = os.path.join(TEST_RUNS_BASE_DIR, run_dict["uid"])
        if os.path.exists(run_path):
            if os.path.isdir(run_path):
                shutil.rmtree(run_path)

        # Notification
        notification = (
            f"{user.email} deleted a Test Run for Test Case "
            f"{mapping.test_case.title} as part of the sw component "
            f"{api.api}, library {api.library}."
        )
        notifications = NotificationModel(
            api, "info", f"Test Run for {api.api} has been removed", notification, str(user.id), f"/mapping/{api.id}"
        )
        dbi.session.add(notifications)
        dbi.session.commit()
        return run_dict


class TestRunLog(Resource):

    def get(self):
        mandatory_fields = ["api-id", "id"]
        args = get_query_string_args(request.args)
        if not check_fields_in_request(mandatory_fields, args):
            return BAD_REQUEST_MESSAGE, BAD_REQUEST_STATUS

        dbi = db_orm.DbInterface(get_db())

        # User
        user = get_active_user_from_request(args, dbi.session)
        if isinstance(user, UserModel):
            user_id = user.id
            user_role = user.role
        else:
            user_id = 0
            user_role = ''

        # Find api
        api = get_api_from_request(args, dbi.session)
        if not api:
            return NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

        # Permissions
        permissions = get_api_user_permissions(api, user_id, user_role, dbi.session)
        if "r" not in permissions:
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        try:
            run = (
                dbi.session.query(TestRunModel)
                .filter(
                    TestRunModel.api_id == api.id,
                    TestRunModel.id == args["id"],
                )
                .one()
            )
        except NoResultFound:
            return NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

        log_exec = ""
        log_exec_path = os.path.join(TEST_RUNS_BASE_DIR, f"{run.uid}.log")

        if run.test_run_config.plugin == TestRunner.TMT:
            log_exec_path = os.path.join(TEST_RUNS_BASE_DIR, run.uid, "log.txt")

        if os.path.exists(log_exec_path):
            f = open(log_exec_path, "r")
            log_exec = f.read()
            f.close()
        else:
            log_exec = "File not found."

        # List files in the TMT_PLAN_DATA dir
        artifacts = []
        if os.path.exists(os.path.join(TEST_RUNS_BASE_DIR, run.uid, "api", "tmt-plan", "data")):
            artifacts = os.listdir(os.path.join(TEST_RUNS_BASE_DIR, run.uid, "api", "tmt-plan", "data"))

        ret = run.as_dict()
        ret["artifacts"] = artifacts
        ret["log_exec"] = log_exec
        return ret


class TestRunArtifacts(Resource):

    def get(self):
        mandatory_fields = ["api-id", "artifact", "id"]
        args = get_query_string_args(request.args)
        if not check_fields_in_request(mandatory_fields, args):
            return BAD_REQUEST_MESSAGE, BAD_REQUEST_STATUS

        dbi = db_orm.DbInterface(get_db())

        # User
        user = get_active_user_from_request(args, dbi.session)
        if not isinstance(user, UserModel):
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        # Find api
        api = get_api_from_request(args, dbi.session)
        if not api:
            return NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

        # Permissions
        permissions = get_api_user_permissions(api, user.id, user.role, dbi.session)
        if "r" not in permissions:
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        try:
            run = (
                dbi.session.query(TestRunModel)
                .filter(
                    TestRunModel.api_id == api.id,
                    TestRunModel.id == args["id"],
                )
                .one()
            )
        except NoResultFound:
            return NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

        # List files in the TMT_PLAN_DATA dir
        artifacts_path = os.path.join(TEST_RUNS_BASE_DIR, run.uid, "api", "tmt-plan", "data")
        artifacts = os.listdir(artifacts_path)
        if args["artifact"] not in artifacts:
            return NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

        return send_from_directory(artifacts_path, args["artifact"])


class TestRunPluginPresets(Resource):

    def get(self):
        mandatory_fields = ["api-id", "plugin"]
        args = get_query_string_args(request.args)
        if not check_fields_in_request(mandatory_fields, args):
            return BAD_REQUEST_MESSAGE, BAD_REQUEST_STATUS

        plugin = args["plugin"]
        dbi = db_orm.DbInterface(get_db())

        # User
        user = get_active_user_from_request(args, dbi.session)
        if not isinstance(user, UserModel):
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        # Find api
        api = get_api_from_request(args, dbi.session)
        if not api:
            return NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

        # Permissions
        permissions = get_api_user_permissions(api, user.id, user.role, dbi.session)
        if "r" not in permissions:
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        if os.path.exists(TESTRUN_PRESET_FILEPATH):
            try:
                presets = parse_config(path=TESTRUN_PRESET_FILEPATH)
                if plugin in presets.keys():
                    if isinstance(presets[plugin], list):
                        return [x["name"] for x in presets[plugin] if "name" in x.keys()]
            except Exception:
                print(f"Unable to read {TESTRUN_PRESET_FILEPATH}")
                return []
        return []


class ExternalTestRuns(Resource):
    def get(self):
        PARAM_DATE_FORMAT = "%Y-%m-%d"
        GITLAB_CI_DATE_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"
        KERNEL_CI_DATE_FORMAT = "%Y-%m-%dT%H:%M:%S"

        mandatory_fields = ["api-id", "plugin", "preset"]
        args = get_query_string_args(request.args)

        if not check_fields_in_request(mandatory_fields, args):
            return BAD_REQUEST_MESSAGE, BAD_REQUEST_STATUS

        ret = []
        ret_pipelines = []
        all_pipelines = []
        filtered_pipelines = []
        plugin = args["plugin"].strip()
        preset = args["preset"].strip()
        params_strings = []
        params = {}

        preset_config = None
        dbi = db_orm.DbInterface(get_db())

        # User
        user = get_active_user_from_request(args, dbi.session)
        if not isinstance(user, UserModel):
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        # Find api
        api = get_api_from_request(args, dbi.session)
        if not api:
            return NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

        # Permissions
        permissions = get_api_user_permissions(api, user.id, user.role, dbi.session)
        if "r" not in permissions:
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        if preset:
            presets = parse_config(path=TESTRUN_PRESET_FILEPATH)

            if plugin in presets.keys():
                tmp = [x for x in presets[plugin] if x["name"] == preset]
                if tmp:
                    # Init the config with the preset
                    # Values from test_run_config will override preset values
                    preset_config = tmp[0]

            if not preset_config:
                return "Preset not found", NOT_FOUND_STATUS

            if "params" in args.keys():
                params_strings = args["params"].split(";")
                params_strings = [x for x in params_strings if "=" in x]
                for param_string in params_strings:
                    k = param_string.split("=")[0].strip()
                    v = param_string.split("=")[1].strip()
                    if k and v:
                        params[k] = v
                        # Override preset config with params
                        preset_config[k] = v

            if plugin == TestRunner.GITLAB_CI:
                gitlab_ci_mandatory_fields = ["private_token", "project_id", "url"]

                # Skip pending pipelines from the list
                gitlab_ci_valid_status = ["success", "failed"]

                if not check_fields_in_request(gitlab_ci_mandatory_fields, preset_config, allow_empty_string=False):
                    return BAD_REQUEST_MESSAGE, BAD_REQUEST_STATUS

                gl = gitlab.Gitlab(url=preset_config["url"], private_token=preset_config["private_token"])
                gl.auth()
                project = gl.projects.get(id=preset_config["project_id"])

                job = None
                ref = None
                stage = None

                if "job" in preset_config.keys():
                    if preset_config["job"]:
                        job = preset_config["job"]

                if "ref" in preset_config.keys():
                    if preset_config["ref"]:
                        ref = preset_config["ref"]
                elif "git_repo_ref" in preset_config.keys():
                    if preset_config["git_repo_ref"]:
                        ref = preset_config["git_repo_ref"]

                if "stage" in preset_config.keys():
                    if preset_config["stage"]:
                        stage = preset_config["stage"]

                if ref:
                    all_pipelines = project.pipelines.list(ref=ref)
                else:
                    all_pipelines = project.pipelines.list()

                # Filter
                all_pipelines = [x for x in all_pipelines if x.status in gitlab_ci_valid_status]
                if not all_pipelines:
                    return []
                pipeline_attrs = all_pipelines[0].__dict__["_attrs"].keys()
                params_pipelines = all_pipelines
                filtered_by_params = False
                filtered_pipelines = []

                if params.keys():
                    for k, v in params.items():
                        if k in pipeline_attrs:
                            params_pipelines = [x for x in params_pipelines if x.__dict__["_attrs"][k] == v]
                            filtered_by_params = True

                    if "updated_after" in params.keys():
                        if params["updated_after"]:
                            try:
                                compare_date = datetime.datetime.strptime(params["updated_after"], PARAM_DATE_FORMAT)
                                params_pipelines = [
                                    x
                                    for x in params_pipelines
                                    if datetime.datetime.strptime(x.updated_at, GITLAB_CI_DATE_FORMAT) >= compare_date
                                ]
                                filtered_by_params = True
                            except ValueError as e:
                                print(f"ExternalTestRuns Exception at gitlab ci {e}")
                                pass

                    if "updated_before" in params.keys():
                        if params["updated_before"]:
                            try:
                                compare_date = datetime.datetime.strptime(params["updated_before"], PARAM_DATE_FORMAT)
                                params_pipelines = [
                                    x
                                    for x in params_pipelines
                                    if datetime.datetime.strptime(x.updated_at, GITLAB_CI_DATE_FORMAT) <= compare_date
                                ]
                                filtered_by_params = True
                            except ValueError as e:
                                print(f"ExternalTestRuns Exception at gitlab ci {e}")
                                pass

                if not filtered_by_params:
                    params_pipelines = all_pipelines

                if stage:
                    for pipeline in params_pipelines:
                        pipeline_jobs = pipeline.jobs.list()
                        for pipeline_job in pipeline_jobs:
                            if pipeline_job.__dict__["_attrs"]["stage"] == stage:
                                if job:
                                    if pipeline_job.__dict__["_attrs"]["name"] == job:
                                        filtered_pipelines.append(pipeline)
                                        break
                                else:
                                    filtered_pipelines.append(pipeline)
                                    break
                else:
                    for pipeline in params_pipelines:
                        pipeline_jobs = pipeline.jobs.list()
                        for pipeline_job in pipeline_jobs:
                            if job:
                                if pipeline_job.__dict__["_attrs"]["name"] == job:
                                    filtered_pipelines.append(pipeline)
                                    break
                            else:
                                filtered_pipelines.append(pipeline)
                                break

                for p in filtered_pipelines:
                    ret.append(
                        {
                            "created_at": p.created_at,
                            "id": p.id,
                            "project": project.name,
                            "ref": p.ref,
                            "details": p.name,
                            "status": "pass" if p.status == "success" else "fail",
                            "web_url": p.web_url,
                        }
                    )

            if plugin == TestRunner.GITHUB_ACTIONS:
                github_actions_mandatory_fields = ["private_token", "url"]
                ref = None

                if not check_fields_in_request(
                    github_actions_mandatory_fields, preset_config, allow_empty_string=False
                ):
                    return BAD_REQUEST_MESSAGE, BAD_REQUEST_STATUS

                if preset_config["url"].endswith("/"):
                    preset_config["url"] = preset_config["url"][:-1]
                if preset_config["url"].endswith(".git"):
                    preset_config["url"] = preset_config["url"][:-4]

                url_split = preset_config["url"].split("/")
                if len(url_split) < 2:
                    return f"{BAD_REQUEST_MESSAGE} Github repository url is not valid", BAD_REQUEST_STATUS

                owner = url_split[-2]
                repo = url_split[-1]
                workflows_url = f"https://api.github.com/repos/{owner}/{repo}/actions/runs?"

                if "ref" in preset_config.keys():
                    if preset_config["ref"]:
                        ref = preset_config["ref"]
                elif "git_repo_ref" in preset_config.keys():
                    if preset_config["git_repo_ref"]:
                        ref = preset_config["git_repo_ref"]

                if ref:
                    workflows_url += f"&branch={ref}"

                if "workflow_id" in preset_config.keys():
                    workflows_url += f"&workflow_id={preset_config['workflow_id']}"

                if params_strings:
                    workflows_url += "&" + "&".join(params_strings)

                headers = {
                    "Accept": "application/vnd.github+json",
                    "Authorization": f"Bearer {preset_config['private_token']}",
                    "X-GitHub-Api-Version": "2022-11-28",
                }

                try:
                    request_params = urllib.request.Request(url=workflows_url, headers=headers)

                    response_data = urllib.request.urlopen(request_params).read()
                    content = json.loads(response_data.decode("utf-8"))
                except Exception as e:
                    return f"{BAD_REQUEST_MESSAGE} Unable to read workflows {e}", BAD_REQUEST_STATUS
                else:
                    ret_pipelines = content["workflow_runs"]

                for p in ret_pipelines:
                    ret.append(
                        {
                            "created_at": p["created_at"],
                            "id": p["id"],
                            "project": f"{owner}/{repo}",
                            "ref": p["head_branch"],
                            "details": p["name"],
                            "status": "pass" if p["conclusion"] == "success" else "fail",
                            "web_url": f"{preset_config['url']}/actions/runs/{p['id']}",
                        }
                    )

            if plugin == TestRunner.KERNEL_CI:
                NODES_ENDPOINT = "nodes"
                dashboard_base_url = "https://dashboard.kernelci.org/tree/unknown/test/maestro:"
                kernel_ci_mandatory_fields = ["private_token", "url"]

                if not check_fields_in_request(kernel_ci_mandatory_fields, preset_config, allow_empty_string=False):
                    return BAD_REQUEST_MESSAGE, BAD_REQUEST_STATUS

                if preset_config["url"].endswith("/"):
                    preset_config["url"] = preset_config["url"][:-1]

                # We use double underscore in the param key for kernelCI
                # that should be replace with a . when used in the kernelCI API
                for i in range(len(params_strings)):
                    kv = params_strings[i].split("=")
                    k = kv[0]
                    v = kv[1]
                    if k == "created_after":
                        try:
                            compare_date = datetime.datetime.strptime(params["created_after"], PARAM_DATE_FORMAT)
                            compare_date_str = compare_date.strftime(KERNEL_CI_DATE_FORMAT)
                            params_strings[i] = f"created__gt={compare_date_str}"
                        except ValueError as e:
                            print(f"ExternalTestRuns Exception at KernelCI {e}")
                            pass
                    elif k == "created_before":
                        try:
                            compare_date = datetime.datetime.strptime(params["created_before"], PARAM_DATE_FORMAT)
                            compare_date_str = compare_date.strftime(KERNEL_CI_DATE_FORMAT)
                            params_strings[i] = f"created__lt={compare_date_str}"
                        except ValueError as e:
                            print(f"ExternalTestRuns Exception at KernelCI {e}")
                            pass
                    else:
                        params_strings[i] = f"{k.replace('__', '.')}={v}"

                kernel_ci_url = f"{preset_config['url']}/{NODES_ENDPOINT}?kind=test&state=done"
                if params_strings:
                    kernel_ci_url += f"&{'&'.join(params_strings)}"

                headers = {
                    "Authorization": f"Bearer {preset_config['private_token']}",
                }

                try:
                    kernel_ci_request = urllib.request.Request(url=kernel_ci_url, headers=headers)

                    response_data = urllib.request.urlopen(kernel_ci_request).read()
                    content = json.loads(response_data.decode("utf-8"))
                except Exception as e:
                    return f"{BAD_REQUEST_MESSAGE} Unable to read workflows {e}", BAD_REQUEST_STATUS
                else:
                    ret_pipelines = content["items"]

                for p in ret_pipelines:
                    project = p["data"]["kernel_revision"]["tree"]
                    branch = p["data"]["kernel_revision"]["branch"]
                    ret.append(
                        {
                            "created_at": p["created"],
                            "id": p["id"],
                            "project": project,
                            "ref": branch,
                            "details": p["name"],
                            "status": "pass" if p["result"] == "pass" else "fail",
                            "web_url": f"{dashboard_base_url}{p['id']}",
                        }
                    )

        return ret


class AdminTestRunPluginsPresets(Resource):
    def get(self):
        ret = {"content": ""}

        mandatory_fields = ["token", "user-id"]
        args = get_query_string_args(request.args)

        if not check_fields_in_request(mandatory_fields, args):
            return "bad request!", 400

        dbi = db_orm.DbInterface(get_db())

        user = get_active_user_from_request(args, dbi.session)
        if not isinstance(user, UserModel):
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        if user.role not in USER_ROLES_MANAGE_USERS:
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        if os.path.exists(TESTRUN_PRESET_FILEPATH):
            try:
                f = open(TESTRUN_PRESET_FILEPATH, "r")
                fc = f.read()
                f.close()
                ret["content"] = fc
            except Exception:
                print(f"Unable to read {TESTRUN_PRESET_FILEPATH}")
        return ret

    def put(self):
        request_data = request.get_json(force=True)
        ret = {"content": ""}
        mandatory_fields = ["content", "user-id", "token"]
        if not check_fields_in_request(mandatory_fields, request_data):
            return BAD_REQUEST_MESSAGE, BAD_REQUEST_STATUS

        dbi = db_orm.DbInterface(get_db())

        user = get_active_user_from_request(request_data, dbi.session)
        if not isinstance(user, UserModel):
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        if user.role not in USER_ROLES_MANAGE_USERS:
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        # Validate the content
        try:
            new_content = parse_config(data=request_data["content"])  # noqa: F841
        except Exception as exc:
            return f"{BAD_REQUEST_MESSAGE} {exc}", BAD_REQUEST_STATUS

        f = open(TESTRUN_PRESET_FILEPATH, "w")
        f.write(request_data["content"])
        f.close()
        ret["content"] = request_data["content"]
        return ret


class Version(Resource):

    def get(self):
        version = ""
        filepath = os.path.join(os.path.dirname(currentdir), "pyproject.toml")
        f = open(filepath, "r")
        fc = f.read()
        f.close()
        version_row = [x for x in fc.split("\n") if "version = " in x]
        if len(version_row) == 1:
            version = version_row[0].split("=")[-1].replace('"', "").strip()
        return {"version": version}


api.add_resource(Api, "/apis")
api.add_resource(ApiHistory, "/apis/history")
api.add_resource(ApiSpecification, "/api-specifications")
api.add_resource(Library, "/libraries")
api.add_resource(SPDXLibrary, "/spdx/libraries")
api.add_resource(SPDXApi, "/spdx/apis")
api.add_resource(Document, "/documents")
api.add_resource(RemoteDocument, "/remote-documents")
api.add_resource(Justification, "/justifications")
api.add_resource(SwRequirement, "/sw-requirements")
api.add_resource(TestSpecification, "/test-specifications")
api.add_resource(TestCase, "/test-cases")
# Mapping
# - Direct
api.add_resource(ApiSpecificationsMapping, "/mapping/api/specifications")
api.add_resource(ApiDocumentsMapping, "/mapping/api/documents")
api.add_resource(ApiJustificationsMapping, "/mapping/api/justifications")
api.add_resource(ApiLastCoverage, "/mapping/api/last-coverage")
api.add_resource(ApiSwRequirementsMapping, "/mapping/api/sw-requirements")
api.add_resource(ApiTestSpecificationsMapping, "/mapping/api/test-specifications")
api.add_resource(ApiTestCasesMapping, "/mapping/api/test-cases")
api.add_resource(TestRunConfig, "/mapping/api/test-run-configs")
api.add_resource(TestRun, "/mapping/api/test-runs")
api.add_resource(ExternalTestRuns, "/mapping/api/test-runs/external")
api.add_resource(TestRunLog, "/mapping/api/test-run/log")
api.add_resource(TestRunArtifacts, "/mapping/api/test-run/artifacts")
api.add_resource(TestRunPluginPresets, "/mapping/api/test-run-plugins-presets")
api.add_resource(AdminTestRunPluginsPresets, "/admin/test-run-plugins-presets")

# - Import
api.add_resource(SwRequirementImport, "/import/sw-requirements")

# - Indirect
api.add_resource(SwRequirementSwRequirementsMapping, "/mapping/sw-requirement/sw-requirements")
api.add_resource(SwRequirementTestSpecificationsMapping, "/mapping/sw-requirement/test-specifications")
api.add_resource(SwRequirementTestCasesMapping, "/mapping/sw-requirement/test-cases")
api.add_resource(TestSpecificationTestCasesMapping, "/mapping/test-specification/test-cases")

# History
api.add_resource(MappingHistory, "/mapping/history")
api.add_resource(CheckSpecification, "/apis/check-specification")
api.add_resource(FixNewSpecificationWarnings, "/apis/fix-specification-warnings")

# Testing Support
api.add_resource(TestingSupportInitDb, "/test-support/init-db")

# Usage
api.add_resource(MappingUsage, "/mapping/usage")
# Comments
api.add_resource(Comment, "/comments")
# Fork
api.add_resource(ForkApiSwRequirement, "/fork/api/sw-requirement")
api.add_resource(ForkSwRequirementSwRequirement, "/fork/sw-requirement/sw-requirement")
# api.add_resource(ForkTestSpecification, '/fork/api/test-specification')
# api.add_resource(ForkTestCase, '/fork/api/test-case')
# api.add_resource(ForkJustification, '/fork/api/justification')
api.add_resource(User, "/user")
api.add_resource(UserApis, "/user/apis")
api.add_resource(UserEnable, "/user/enable")
api.add_resource(UserLogin, "/user/login")
api.add_resource(UserNotifications, "/user/notifications")
api.add_resource(UserPermissionsApi, "/user/permissions/api")
api.add_resource(UserPermissionsApiCopy, "/user/permissions/copy")
api.add_resource(UserResetPassword, "/user/reset-password")
api.add_resource(UserRole, "/user/role")
api.add_resource(UserSignin, "/user/signin")
api.add_resource(UserSshKey, "/user/ssh-key")
api.add_resource(UserFiles, "/user/files")
api.add_resource(UserFileContent, "/user/files/content")
api.add_resource(Testing, "/testing")
api.add_resource(Version, "/version")


if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--testing", default=False, action="store_true", help="Test Api Project using db/test.db database"
    )
    args = parser.parse_args()

    app.config["TESTING"] = args.testing
    app.config["ENV"] = "local"

    if app.config["TESTING"]:
        app.config["DB"] = "test.db"
        import db.models.init_db as init_db

        init_db.initialization(db_name="test.db")
    else:
        app.config["DB"] = "basil.db"
    app.run()
