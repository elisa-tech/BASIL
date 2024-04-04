import base64
from flask_cors import CORS
from flask import Flask, request, send_file, send_from_directory
from flask_restful import Resource, Api, reqparse
import os
import datetime
import logging
import shutil
from sqlalchemy import or_
from sqlalchemy.orm.exc import NoResultFound
import sys
import urllib
from urllib.error import HTTPError, URLError
from uuid import uuid4

logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
# logging.getLogger('sqlalchemy').setLevel(logging.ERROR)

currentdir = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(1, os.path.dirname(currentdir))

JOIN_APIS_TABLE = "apis"
JOIN_SW_REQUIREMENTS_TABLE = "sw-requirements"
JOIN_TEST_SPECIFICATIONS_TABLE = "test-specifications"
MAX_LOGIN_ATTEMPTS = 5
MAX_LOGIN_ATTEMPTS_TIMEOUT = 60 * 15  # 15 minutes
SSH_KEYS_PATH = os.path.join(currentdir, 'ssh_keys')
TMT_LOGS_PATH = os.getenv('BASIL_TMT_WORKDIR_ROOT', '/var/tmp/tmt')

if not os.path.exists(SSH_KEYS_PATH):
    os.mkdir(SSH_KEYS_PATH)

if not os.path.exists(TMT_LOGS_PATH):
    os.makedirs(TMT_LOGS_PATH, exist_ok=True)

USER_ROLES_DELETE_PERMISSIONS = ['ADMIN', 'USER']
USER_ROLES_EDIT_PERMISSIONS = ['ADMIN', 'USER']
USER_ROLES_WRITE_PERMISSIONS = ['ADMIN', 'USER']
USER_ROLES_MANAGE_PERMISSIONS = ['ADMIN', 'USER']
USER_ROLES_MANAGE_USERS = ['ADMIN',]

BAD_REQUEST_MESSAGE = 'Bad request'
BAD_REQUEST_STATUS = 400
UNAUTHORIZED_MESSAGE = 'User not authorized'
UNAUTHORIZED_STATUS = 401
FORBIDDEN_MESSAGE = 'Forbidden'
FORBIDDEN_STATUS = 403
NOT_FOUND_MESSAGE = 'Not found'
SW_COMPONENT_NOT_FOUND_MESSAGE = 'Sw Component not found.'
NOT_FOUND_STATUS = 404
CONFLICT_MESSAGE = 'Conflict with existing data'
CONFLICT_STATUS = 409
PRECONDITION_FAILED_MESSAGE = 'Same precondition failed'
PRECONDITION_FAILED_STATUS = 412

NOTIFICATION_CATEGORY_NEW = 'success'
NOTIFICATION_CATEGORY_EDIT = 'warning'
NOTIFICATION_CATEGORY_DELETE = 'danger'

API_PERMISSION_FIELDS = ['delete_permissions',
                         'edit_permissions',
                         'manage_permissions',
                         'read_denials',
                         'write_permissions']

from db import db_orm
from db.models.api_justification import ApiJustificationModel, ApiJustificationHistoryModel
from db.models.api_sw_requirement import ApiSwRequirementModel, ApiSwRequirementHistoryModel
from db.models.api_test_case import ApiTestCaseModel, ApiTestCaseHistoryModel
from db.models.api_test_specification import ApiTestSpecificationModel
from db.models.api_test_specification import ApiTestSpecificationHistoryModel
from db.models.api import ApiModel, ApiHistoryModel
from db.models.comment import CommentModel
from db.models.justification import JustificationModel, JustificationHistoryModel
from db.models.notification import NotificationModel
from db.models.ssh_key import SshKeyModel
from db.models.sw_requirement_sw_requirement import SwRequirementSwRequirementModel
from db.models.sw_requirement_sw_requirement import SwRequirementSwRequirementHistoryModel
from db.models.sw_requirement_test_case import SwRequirementTestCaseModel
from db.models.sw_requirement_test_case import SwRequirementTestCaseHistoryModel
from db.models.sw_requirement_test_specification import SwRequirementTestSpecificationModel
from db.models.sw_requirement_test_specification import SwRequirementTestSpecificationHistoryModel
from db.models.sw_requirement import SwRequirementModel, SwRequirementHistoryModel
from db.models.test_case import TestCaseModel, TestCaseHistoryModel
from db.models.test_run import TestRunModel
from db.models.test_run_config import TestRunConfigModel
from db.models.test_specification_test_case import TestSpecificationTestCaseModel
from db.models.test_specification_test_case import TestSpecificationTestCaseHistoryModel
from db.models.test_specification import TestSpecificationModel, TestSpecificationHistoryModel
from db.models.user import UserModel

app = Flask("BASIL-API")
api = Api(app)
CORS(app)

login_attempt_cache = {}

token_parser = reqparse.RequestParser()
token_parser.add_argument('token', location="form")

_A = 'api'
_As = f'{_A}s'
_SR = 'sw_requirement'
_SRs = f'{_SR}s'
_TS = 'test_specification'
_TSs = f'{_TS}s'
_TC = 'test_case'
_TCs = f'{_TC}s'
_J = 'justification'
_Js = f'{_J}s'


def get_api_from_request(_request, _db_session):
    if 'api-id' not in _request.keys():
        return None

    query = _db_session.query(ApiModel).filter(
        ApiModel.id == _request['api-id']
    )

    try:
        api = query.one()
        return api
    except NoResultFound:
        return None


def get_parent_api_id(_mapping, _dbisession):
    # Return api id or None

    # Work Items mapped to a Sw Requirement
    if isinstance(_mapping, SwRequirementSwRequirementModel) or \
       isinstance(_mapping, SwRequirementTestCaseModel) or \
       isinstance(_mapping, SwRequirementTestSpecificationModel):
        api_mapping_model = ApiSwRequirementModel
        parent_model = SwRequirementSwRequirementModel
        parent_mapping_field_id = 'sw_requirement_mapping_sw_requirement_id'
        parent_mapping_api_field_id = 'sw_requirement_mapping_api_id'
    else:
        print(f"\n WARNING: mapping is instance of {type(_mapping)}")
        return None

    api_mapping_id = getattr(_mapping, parent_mapping_api_field_id)
    parent_mapping_id = getattr(_mapping, parent_mapping_field_id)

    if not api_mapping_id:
        try:
            parent_mapping = _dbisession.query(parent_model).filter(
                parent_model.id == parent_mapping_id
            ).one()
            api_mapping_id = get_parent_api_id(parent_mapping, _dbisession)
        except NoResultFound:
            return None

    if api_mapping_id:
        try:
            parent_api_mapping = _dbisession.query(api_mapping_model).filter(
                api_mapping_model.id == api_mapping_id
            ).one()
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
        user = _db_session.query(UserModel).filter(
            UserModel.id == _id
        ).one()
        return user.email
    except NoResultFound:
        return ''


def get_active_user_from_request(_request, _db_session):
    mandatory_fields = ['user-id', 'token']
    for field in mandatory_fields:
        if field not in _request.keys():
            return None

    query = _db_session.query(UserModel).filter(
        UserModel.id == _request['user-id']
    ).filter(
        UserModel.token == _request['token']
    ).filter(
        UserModel.enabled == 1
    )

    try:
        user = query.one()
        return user
    except NoResultFound:
        return None


def get_users_email_from_ids(_ids, _dbi_session):
    # _ids list format [1][3][34]
    user_ids = _ids.split('][')
    user_ids = [x.replace('[', '').replace(']', '') for x in user_ids]
    query = _dbi_session.query(UserModel.email).filter(
        UserModel.id.in_(user_ids)
    )
    users = query.all()
    ret = [x.email for x in users]
    return ret


def get_api_user_permissions(_api, _user_id, _dbi_session):
    # Permissions
    permissions = ''
    if f"[{_user_id}]" not in _api.read_denials:
        permissions += 'r'
    else:
        return permissions

    if f"[{_user_id}]" in _api.manage_permissions:
        permissions += 'm'
    if f"[{_user_id}]" in _api.write_permissions:
        permissions += 'w'
    if f"[{_user_id}]" in _api.edit_permissions:
        permissions += 'e'
    return permissions


def get_combined_history_object(_obj, _map, _obj_fields, _map_fields):
    _obj_fields += ['version']
    _map_fields += ['version']

    # obj_version = _obj['version'] if 'version' in _obj.keys() else ''
    map_version = _map['version'] if 'version' in _map.keys() else ''

    if map_version != '':
        combined_version = f'{_obj["version"]}.{_map["version"]}'
    else:
        combined_version = f'{_obj["version"]}'

    if 'created_at' in _map.keys():
        combined_date = _obj['created_at'] if _obj['created_at'] > _map['created_at'] else _map['created_at']
    else:
        combined_date = _obj['created_at']

    _combined = {'version': combined_version,
                 'object': {},
                 'mapping': {},
                 'created_at': combined_date}

    for k in _obj_fields:
        if k in _obj.keys():
            _combined['object'][k] = _obj[k]

    for j in _map_fields:
        if j in _map.keys():
            _combined['mapping'][j] = _map[j]

    return _combined


def get_reduced_history_data(history_data, _obj_fields, _map_fields, _dbi_session):
    """
    Remove from the history_data fields that has not been modified
    Adding on each history element the name of the user
    """
    fields_to_skip = ['version', 'created_at', 'updated_at']

    if len(history_data) == 0:
        return []

    ret = [{'version': history_data[0]['version'],
            'object': {},
            'mapping': {},
            'created_at': history_data[0]['created_at'].strftime("%d %b %y %H:%M")}]

    for k in _obj_fields:
        if k in history_data[0]['object'].keys() and k not in fields_to_skip:
            ret[0]['object'][k] = history_data[0]['object'][k]

    for j in _map_fields:
        if j in history_data[0]['mapping'].keys() and j not in fields_to_skip:
            ret[0]['mapping'][j] = history_data[0]['mapping'][j]

    # Object - return user email of the first version instead of the id
    if 'edited_by_id' in ret[0]['object'].keys():
        del (ret[0]['object']['edited_by_id'])
    if 'created_by_id' in ret[0]['object'].keys():
        ret[0]['object']['created_by'] = get_user_email_from_id(
            ret[0]['object']['created_by_id'],
            _dbi_session
        )
        del (ret[0]['object']['created_by_id'])

    # Mapping - return user email of the first version instead of the id
    if 'edited_by_id' in ret[0]['mapping'].keys():
        del (ret[0]['mapping']['edited_by_id'])
    if 'created_by_id' in ret[0]['mapping'].keys():
        ret[0]['mapping']['created_by'] = get_user_email_from_id(
            ret[0]['mapping']['created_by_id'],
            _dbi_session
        )
        del (ret[0]['mapping']['created_by_id'])

    if len(history_data) > 1:
        for i in range(1, len(history_data)):
            tmp = {'object': {},
                   'mapping': {},
                   'version': history_data[i]['version'],
                   'created_at': history_data[i]['created_at'].strftime("%d %b %y %H:%M")}

            last_version = history_data[i - 1]['version'].split(".")
            current_version = history_data[i]['version'].split(".")

            if last_version[0] != current_version[0]:
                # object changed
                for k in _obj_fields:
                    if k in history_data[i]['object'].keys() and k not in fields_to_skip:
                        if history_data[i]['object'][k] != history_data[i - 1]['object'][k]:
                            tmp['object'][k] = history_data[i]['object'][k]
                    tmp['object']['edited_by'] = get_user_email_from_id(
                        history_data[i]['object']['edited_by_id'],
                        _dbi_session)

            if len(last_version) > 1 and len(current_version) > 1:
                if last_version[1] != current_version[1]:
                    # mapping changed
                    for j in _map_fields:
                        if j in history_data[i]['mapping'].keys() and j not in fields_to_skip:
                            if history_data[i]['mapping'][j] != history_data[i - 1]['mapping'][j]:
                                tmp['mapping'][j] = history_data[i]['mapping'][j]
                    tmp['mapping']['edited_by'] = get_user_email_from_id(
                        history_data[i]['mapping']['edited_by_id'],
                        _dbi_session)
            ret.append(tmp)

    return ret


def get_dict_without_keys(_dict, _undesired_keys):
    current_keys = _dict.keys()
    for k in _undesired_keys:
        if k in current_keys:
            del _dict[k]
    return _dict


def get_model_editable_fields(_model, _is_history):
    not_editable_model_fields = ['id', 'created_at', 'updated_at',
                                 'created_by_id', 'edited_by_id',
                                 'delete_permissions', 'edit_permissions', 'manage_permissions',
                                 'read_denials', 'write_permissions', 'checksum']

    not_editable_model_history_fields = ['row_id', 'created_at', 'updated_at',
                                         'delete_permissions', 'edit_permissions', 'manage_permissions',
                                         'read_denials', 'write_permissions']

    all_fields = _model.__table__.columns.keys()
    if not _is_history:
        return [x for x in all_fields if x not in not_editable_model_fields]
    else:
        return [x for x in all_fields if x not in not_editable_model_history_fields]


def filter_query(_query, _args, _model, _is_history):
    fields = get_model_editable_fields(_model, _is_history)
    for arg_key in _args.keys():
        if "field" in arg_key:
            field_n = arg_key.replace('field', '')
            field = _args[f'field{field_n}']
            filter = _args[f'filter{field_n}']
            if field in fields:
                _query = _query.filter(getattr(_model, field) == filter)
            elif field == 'id':
                _query = _query.filter(_model.id == filter)

        if arg_key == "search":
            _query = _query.filter(or_(
                getattr(_model, field).like(f'%{_args["search"]}%') for field in fields)
            )

    return _query


def get_db():
    if app.config['TESTING']:
        return 'test.db'
    return 'basil.db'


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
                    content = resource.read().decode('utf-8')
                return content
            except URLError as excp:
                print(f"URLError: {excp.reason} reading {_url_or_path}")
                return None
            except HTTPError as excp:
                print(f"HTTPError: {excp.reason} reading {_url_or_path}")
                return None
            except ValueError as excp:
                print(f"ValueError reading {_url_or_path}: {excp}")
                return None
        else:
            if not os.path.exists(_url_or_path):
                return None

            try:
                f = open(_url_or_path, 'r')
                fc = f.read()
                f.close()
                return fc
            except OSError:
                return None


def get_api_coverage(_sections):
    total_len = sum([len(x['section']) for x in _sections])
    wa = 0
    for i in range(len(_sections)):
        wa += (len(_sections[i]['section']) / total_len) * (_sections[i]['covered'] / 100.0)
    return int(wa * 100)


def split_section(_to_splits, _that_split, _work_item_type):
    sections = []
    _current_work_item = _that_split

    if _work_item_type == _SR:
        if "indirect_sw_requirement" in _that_split.keys():
            _current_work_item['parent_mapping_type'] = "sw_requirement_mapping_sw_requirement"
        else:
            _current_work_item['parent_mapping_type'] = "sw_requirement_mapping_api"

    for _to_split in _to_splits:
        _to_split_range = range(_to_split['offset'],
                                _to_split['offset'] + len(_to_split['section']))
        that_split_range = range(_that_split['offset'], _that_split['offset'] + len(_that_split['section']))
        overlap = len(list(set(_to_split_range) & set(that_split_range))) > 0
        if not overlap:
            tmp_section = {'section': _to_split['section'],
                           'offset': _to_split['offset'],
                           'coverage': _to_split['coverage'],
                           'covered': _to_split['covered'],
                           'gap': _to_split['gap'],
                           'delete': 0,
                           _Js: [],
                           _TCs: [],
                           _TSs: [],
                           _SRs: []}

            for j in range(len(_to_split[_SRs])):
                tmp_section[_SRs].append(_to_split[_SRs][j].copy())
            for j in range(len(_to_split[_TCs])):
                tmp_section[_TCs].append(_to_split[_TCs][j].copy())
            for j in range(len(_to_split[_TSs])):
                tmp_section[_TSs].append(_to_split[_TSs][j].copy())
            for j in range(len(_to_split[_Js])):
                tmp_section[_Js].append(_to_split[_Js][j].copy())

            sections.append(tmp_section)

        else:
            idx = [_to_split['offset'],
                   _to_split['offset'] + len(_to_split['section']),
                   _that_split['offset'],
                   _that_split['offset'] + len(_that_split['section'])]
            idx_set = set(idx)
            idx = sorted(list(idx_set))
            for i in range(1, len(idx)):
                tmp_section = {'section': _to_split['section'][idx[i - 1] - idx[0]:idx[i] - idx[0]],
                               'offset': idx[i - 1],
                               'coverage': _to_split['coverage'],
                               'covered': _to_split['covered'],
                               'gap': _to_split['gap'],
                               'delete': 0,
                               _Js: [],
                               _TCs: [],
                               _TSs: [],
                               _SRs: []}

                for j in range(len(_to_split[_SRs])):
                    tmp_section[_SRs].append(_to_split[_SRs][j].copy())
                for j in range(len(_to_split[_TCs])):
                    tmp_section[_TCs].append(_to_split[_TCs][j].copy())
                for j in range(len(_to_split[_TSs])):
                    tmp_section[_TSs].append(_to_split[_TSs][j].copy())
                for j in range(len(_to_split[_Js])):
                    tmp_section[_Js].append(_to_split[_Js][j].copy())

                sections.append(tmp_section)

    for iSection in range(len(sections)):
        section_range = range(sections[iSection]['offset'],
                              sections[iSection]['offset'] + len(sections[iSection]['section']))
        that_split_range = range(_that_split['offset'], _that_split['offset'] + len(_that_split['section']))
        overlap = len(list(set(section_range) & set(that_split_range))) > 0
        if overlap:
            sections[iSection][f'{_work_item_type}s'].append(_current_work_item)

    return sections


def get_split_sections(_specification, _mapping, _work_item_types):
    """
    _mapping: list of x_y (e.g. ApiSwRequirement) with nested mapping
              each row has its own specification section information
    _work_item_types: list of work items type for direct mapping that I
              what to display in the current view
    return: list of sections with related mapping
    """
    mapped_sections = [{'section': _specification,
                        'offset': 0,
                        'coverage': 0,
                        'covered': 0,
                        'gap': 100,
                        'delete': 0,
                        _TCs: [],
                        _TSs: [],
                        _SRs: [],
                        _Js: []}]

    for iWIT in range(len(_work_item_types)):
        _items_key = f"{_work_item_types[iWIT]}s"
        for iMapping in range(len(_mapping[_items_key])):
            if not _mapping[_items_key][iMapping]['match']:
                continue
            mapped_sections = sorted(mapped_sections, key=lambda k: k['offset'])

            # get overlapping sections
            overlapping_section_indexes = []
            for j in range(len(mapped_sections)):
                section_range = range(mapped_sections[j]['offset'],
                                      mapped_sections[j]['offset'] + len(mapped_sections[j]['section']))
                that_split_range = range(_mapping[_items_key][iMapping]['offset'],
                                         _mapping[_items_key][iMapping]['offset'] + len(
                                             _mapping[_items_key][iMapping]['section']))
                overlap = len(list(set(section_range) & set(that_split_range))) > 0
                if overlap:
                    overlapping_section_indexes.append(j)

            if len(overlapping_section_indexes) > 0:
                for k in overlapping_section_indexes:
                    mapped_sections[k]['delete'] = 1

                mapped_sections += split_section([x for x in mapped_sections if x['delete'] == 1],
                                                 _mapping[_items_key][iMapping], _work_item_types[iWIT])
                mapped_sections = [x for x in mapped_sections if x['delete'] == 0]

    for iS in range(len(mapped_sections)):
        if mapped_sections[iS]['section'].strip() == "":
            if sum([len(mapped_sections[iS][_SRs]),
                    len(mapped_sections[iS][_TSs]),
                    len(mapped_sections[iS][_TCs]),
                    len(mapped_sections[iS][_Js])]) == 0:
                mapped_sections[iS]['delete'] = True

        coverage_total = 0
        for j in range(len(mapped_sections[iS][_SRs])):
            coverage_total += mapped_sections[iS][_SRs][j]['covered']
        for j in range(len(mapped_sections[iS][_TCs])):
            coverage_total += mapped_sections[iS][_TCs][j]['covered']
        for j in range(len(mapped_sections[iS][_TSs])):
            coverage_total += mapped_sections[iS][_TSs][j]['covered']
        for j in range(len(mapped_sections[iS][_Js])):
            coverage_total += mapped_sections[iS][_Js][j]['covered']
        mapped_sections[iS]['covered'] = min(max(coverage_total, 0), 100)

    # Remove Section with section: \n and no work items
    mapped_sections = [x for x in mapped_sections if not x['delete']]
    return sorted(mapped_sections, key=lambda k: k['offset'])


def check_fields_in_request(fields, request):
    for field in fields:
        if field not in request.keys():
            print(f'field: {field} not in request: {request.keys()}')
            return False
    return True


def get_query_string_args(args):
    db = args.get("db", default="head", type=str)
    limit = args.get("limit", default="", type=str)
    order_by = args.get("order_by", default="", type=str)
    order_how = args.get("order_how", default="", type=str)

    permitted_keys = ["api-id", "artifact", "id", "library", "mapped_to_type", "mapped_to_id",
                      "mode", "parent_id", "parent_table", "relation_id", "search",
                      "token", "url", "user-id", "work_item_type"]

    ret = {"db": db,
           "limit": limit,
           "order_by": order_by,
           "order_how": order_how}

    i = 1
    while True:
        if args.get(f'field{i}') and args.get(f'filter{i}'):
            ret[f'field{i}'] = args.get(f'field{i}')
            ret[f'filter{i}'] = args.get(f'filter{i}')
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
    """

    """
    undesired_keys = []

    mapping_field_id = f"{_srm['__tablename__']}_id"

    tmp = _srm

    # Indirect SwRequirement
    ind_sr_query = _dbi.session.query(SwRequirementSwRequirementModel).filter(
        getattr(SwRequirementSwRequirementModel, mapping_field_id) == _srm['relation_id']
    )
    ind_sr = ind_sr_query.all()

    tmp[_SRs] = [get_dict_without_keys(x.as_dict(db_session=_dbi.session),
                                       undesired_keys + ['api'])
                 for x in ind_sr]

    for iSR in range(len(tmp[_SRs])):
        if "indirect_sw_requirement" in tmp[_SRs][iSR].keys():
            tmp[_SRs][iSR]['parent_mapping_type'] = "sw_requirement_mapping_sw_requirement"
        else:
            tmp[_SRs][iSR]['parent_mapping_type'] = "sw_requirement_mapping_api"

    # Indirect Test Specifications
    ind_ts = _dbi.session.query(SwRequirementTestSpecificationModel).filter(
        getattr(SwRequirementTestSpecificationModel, mapping_field_id) == _srm['relation_id']
    ).all()
    tmp[_TSs] = [get_dict_without_keys(x.as_dict(db_session=_dbi.session),
                                       undesired_keys + ['api']) for x in ind_ts]

    for iTS in range(len(tmp[_TSs])):
        # Indirect Test Cases
        curr_srts_id = tmp[_TSs][iTS]['relation_id']
        ind_tc = _dbi.session.query(TestSpecificationTestCaseModel).filter(
            TestSpecificationTestCaseModel.test_specification_mapping_sw_requirement_id == curr_srts_id
        ).all()

        tmp[_TSs][iTS][_TS][_TCs] = [get_dict_without_keys(x.as_dict(db_session=_dbi.session),
                                                           undesired_keys + ['api']) for x in ind_tc]

    # Indirect Test Cases
    ind_tc = _dbi.session.query(SwRequirementTestCaseModel).filter(
        getattr(SwRequirementTestCaseModel, mapping_field_id) == _srm['relation_id']
    ).all()
    tmp[_TCs] = [get_dict_without_keys(x.as_dict(db_session=_dbi.session),
                                       undesired_keys + ['api', 'sw_requirement_mapping_api'])
                 for x in ind_tc]

    # Recursive updating of nested SwRequirements
    for iNSR in range(len(tmp[_SRs])):
        tmp[_SRs][iNSR] = get_sw_requirement_children(_dbi, tmp[_SRs][iNSR])

    return tmp


def get_api_sw_requirements_mapping_sections(dbi, api):
    api_specification = get_api_specification(api.raw_specification_url)
    if api_specification is None:
        api_specification = "WARNING: Unable to load the Reference Document. " \
                            "Please check the url/path value in the Software Component properties" \
                            " and that the file still exists in the expected location."

    sr = dbi.session.query(ApiSwRequirementModel).filter(
        ApiSwRequirementModel.api_id == api.id).order_by(
        ApiSwRequirementModel.offset.asc()).all()
    sr_mapping = [x.as_dict(db_session=dbi.session) for x in sr]

    justifications = dbi.session.query(ApiJustificationModel).filter(
        ApiJustificationModel.api_id == api.id).order_by(
        ApiJustificationModel.offset.asc()).all()
    justifications_mapping = [x.as_dict(db_session=dbi.session) for x in justifications]

    mapping = {_A: api.as_dict(),
               _SRs: sr_mapping,
               _Js: justifications_mapping}

    for iMapping in range(len(mapping[_SRs])):
        current_offset = mapping[_SRs][iMapping]['offset']
        current_section = mapping[_SRs][iMapping]['section']
        mapping[_SRs][iMapping]['match'] = (
                api_specification[current_offset:current_offset + len(current_section)] == current_section)
    for iMapping in range(len(mapping[_Js])):
        current_offset = mapping[_Js][iMapping]['offset']
        current_section = mapping[_Js][iMapping]['section']
        mapping[_Js][iMapping]['match'] = (
                api_specification[current_offset:current_offset + len(current_section)] == current_section)

    mapped_sections = get_split_sections(api_specification, mapping, [_SR, _J])
    unmapped_sections = [x for x in mapping[_SRs] if not x['match']]
    unmapped_sections += [x for x in mapping[_Js] if not x['match']]

    for iMS in range(len(mapped_sections)):
        for iSR in range(len(mapped_sections[iMS][_SRs])):
            children_data = get_sw_requirement_children(dbi, mapped_sections[iMS][_SRs][iSR])
            mapped_sections[iMS][_SRs][iSR] = children_data

    ret = {'mapped': mapped_sections,
           'unmapped': unmapped_sections}

    dbi.engine.dispose()
    return ret


def check_direct_work_items_against_another_spec_file(db_session, spec, api):
    ret = {'sw-requirements': {'ok': [],
                               'ko': [],
                               'warning': []},
           'test-specifications': {'ok': [],
                                   'ko': [],
                                   'warning': []},
           'test-cases': {'ok': [],
                          'ko': [],
                          'warning': []},
           'justifications': {'ok': [],
                              'ko': [],
                              'warning': []}
           }

    # ApiSwRequirement
    api_srs = db_session.query(ApiSwRequirementModel).filter(
        ApiSwRequirementModel.api_id == api.id
    ).all()
    for api_sr in api_srs:
        if api_sr.section in spec:
            if spec.index(api_sr.section) == api_sr.offset:
                ret['sw-requirements']['ok'].append({'id': api_sr.id,
                                                     'title': api_sr.sw_requirement.title})
            else:
                ret['sw-requirements']['warning'].append({'id': api_sr.id,
                                                          'old-offset': api_sr.offset,
                                                          'new-offset': spec.index(api_sr.section),
                                                          'title': api_sr.sw_requirement.title})
        else:
            ret['sw-requirements']['ko'].append({'id': api_sr.id,
                                                 'title': api_sr.sw_requirement.title})

    # ApiTestSpecification
    api_tss = db_session.query(ApiTestSpecificationModel).filter(
        ApiTestSpecificationModel.api_id == api.id
    ).all()
    for api_ts in api_tss:
        if api_ts.section in spec:
            if spec.index(api_ts.section) == api_ts.offset:
                ret['test-specifications']['ok'].append({'id': api_ts.id,
                                                         'title': api_ts.test_specification.title})
            else:
                ret['test-specifications']['warning'].append({'id': api_ts.id,
                                                              'old-offset': api_ts.offset,
                                                              'new-offset': spec.index(api_ts.section),
                                                              'title': api_ts.test_specification.title})
        else:
            ret['test-specifications']['ko'].append({'id': api_ts.id,
                                                     'title': api_ts.test_specification.title})

    # ApiTestCase
    api_tcs = db_session.query(ApiTestCaseModel).filter(
        ApiTestCaseModel.api_id == api.id
    ).all()
    for api_tc in api_tcs:
        if api_tc.section in spec:
            if spec.index(api_tc.section) == api_tc.offset:
                ret['test-cases']['ok'].append({'id': api_tc.id,
                                                'title': api_tc.test_case.title})
            else:
                ret['test-cases']['warning'].append({'id': api_tc.id,
                                                     'old-offset': api_tc.offset,
                                                     'new-offset': spec.index(
                                                         api_tc.section),
                                                     'title': api_tc.test_case.title})
        else:
            ret['test-cases']['ko'].append({'id': api_tc.id,
                                            'title': api_tc.test_case.title})

    # ApiJustification
    api_js = db_session.query(ApiJustificationModel).filter(
        ApiJustificationModel.api_id == api.id
    ).all()
    for api_j in api_js:
        if api_j.section in spec:
            if spec.index(api_j.section) == api_j.offset:
                ret['justifications']['ok'].append({'id': api_j.id,
                                                    'title': api_j.justification.description})
            else:
                ret['justifications']['warning'].append({'id': api_j.id,
                                                         'old-offset': api_j.offset,
                                                         'new-offset': spec.index(
                                                             api_j.section),
                                                         'title': api_j.justification.description})
        else:
            ret['justifications']['ko'].append({'id': api_j.id,
                                                'title': api_j.justification.description})
    return ret


class Token():

    def filter(self, token):
        if token == app.secret_key:
            return True
        return False


tokenManager = Token()


class SPDXLibrary(Resource):
    fields = ['library']

    def get(self):
        from spdx_manager import SPDXManager

        args = get_query_string_args(request.args)
        dbi = db_orm.DbInterface(get_db())

        query = dbi.session.query(ApiModel).filter(
            ApiModel.library == args['library']
        )
        apis = query.all()

        spdxManager = SPDXManager(f"SPDX-{args['library'].upper()}-EXPORT")
        for api in apis:
            spdxManager.add_api_to_export(api.id)
        dt = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

        spdx_base_path = os.path.dirname(currentdir)
        spdx_relative_path = f"app{os.sep}public{os.sep}spdx_export"
        spdx_filename = f"{args['library']}-{dt}.json"
        spdx_filepath = os.path.join(spdx_base_path, spdx_relative_path, spdx_filename)
        for iRP in range(1, len(spdx_relative_path.split(os.sep))):
            currentRelativePath = os.sep.join(spdx_relative_path.split(os.sep)[:iRP+1])
            if not os.path.exists(os.path.join(spdx_base_path, currentRelativePath)):
                os.mkdir(os.path.join(spdx_base_path, currentRelativePath))

        spdxManager.export(spdx_filepath)

        return send_file(spdx_filepath)


class Comment(Resource):
    fields = ["comment", "parent_table", "user-id", "token"]

    def get(self):
        # mandatory_fields = ["parent_table", "parent_id"]
        args = get_query_string_args(request.args)

        if "parent_table" not in args.keys() or "parent_id" not in args.keys():
            return 'bad request!', 400

        dbi = db_orm.DbInterface(get_db())

        query = dbi.session.query(CommentModel).filter(
            CommentModel.parent_table == args["parent_table"]
        ).filter(
            CommentModel.parent_id == args["parent_id"]
        )

        if "search" in args:
            query = query.filter(or_(
                CommentModel.comment.like(f'%{args["search"]}%'),
            ))

        query = query.order_by(CommentModel.created_at.asc())
        comments = [c.as_dict() for c in query.all()]

        dbi.engine.dispose()
        return comments

    def post(self):
        request_data = request.get_json(force=True)

        if not check_fields_in_request(self.fields, request_data):
            return 'bad request!', 400

        dbi = db_orm.DbInterface(get_db())

        # User
        user = get_active_user_from_request(request_data, dbi.session)
        if not isinstance(user, UserModel):
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        parent_table = request_data['parent_table'].strip()
        if parent_table == "":
            return 'bad request!', 400

        parent_id = request_data['parent_id']
        if parent_id == "":
            return 'bad request!', 400

        comment = request_data['comment'].strip()
        if comment == "":
            return 'bad request!', 400

        new_comment = CommentModel(parent_table, parent_id, user, comment)
        dbi.session.add(new_comment)

        dbi.session.commit()

        add_notification = True
        if parent_table == ApiSwRequirementModel.__tablename__:
            notification_obj = "Sw Requirement"
            query = dbi.session.query(ApiSwRequirementModel).filter(
                ApiSwRequirementModel.id == parent_id
            )
            query_obj = "asr"
        elif parent_table == ApiTestSpecificationModel.__tablename__:
            notification_obj = "Test Specification"
            query = dbi.session.query(ApiTestSpecificationModel).filter(
                ApiTestSpecificationModel.id == parent_id
            )
            query_obj = "atc"
        elif parent_table == ApiTestCaseModel.__tablename__:
            notification_obj = "Test Case"
            query = dbi.session.query(ApiTestCaseModel).filter(
                ApiTestCaseModel.id == parent_id
            )
            query_obj = "ats"
        elif parent_table == ApiJustificationModel.__tablename__:
            notification_obj = "Justification"
            query = dbi.session.query(ApiJustificationModel).filter(
                ApiJustificationModel.id == parent_id
            )
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
            notification = f'{user.email} added a Comment to {notification_obj} ' \
                           f'mapped to ' \
                           f'{mapping.api.api} as part of the library {mapping.api.library}'
            notifications = NotificationModel(mapping.api,
                                              NOTIFICATION_CATEGORY_NEW,
                                              f'New Comment from {user.email}',
                                              notification,
                                              str(user.id),
                                              f'/mapping/{mapping.api.id}?{query_obj}={parent_id}&view=comments')
            dbi.session.add(notifications)
            dbi.session.commit()

        dbi.engine.dispose()
        return new_comment.as_dict()


class CheckSpecification(Resource):
    fields = ['id']

    def get(self):

        args = get_query_string_args(request.args)

        if not check_fields_in_request(self.fields, args):
            return 'bad request!', 400

        dbi = db_orm.DbInterface(get_db())

        query = dbi.session.query(ApiModel).filter(
            ApiModel.id == args['id']
        )
        apis = query.all()

        if len(apis) != 1:
            return "Unable to find the api", 400

        api = apis[0]

        if 'url' in args.keys():
            spec = get_api_specification(request.args['url'])
        else:
            spec = get_api_specification(api.raw_specification_url)

        ret = check_direct_work_items_against_another_spec_file(dbi.session, spec, api)
        dbi.engine.dispose()
        return ret


class FixNewSpecificationWarnings(Resource):
    fields = ['id']

    def get(self):

        args = get_query_string_args(request.args)

        if not check_fields_in_request(self.fields, args):
            return 'bad request!', 400

        dbi = db_orm.DbInterface(get_db())

        query = dbi.session.query(ApiModel).filter(
            ApiModel.id == args['id']
        )
        apis = query.all()

        if len(apis) != 1:
            return "Unable to find the api", 400

        api = apis[0]

        spec = get_api_specification(api.raw_specification_url)

        analysis = check_direct_work_items_against_another_spec_file(dbi.session, spec, api)

        # ApiSwRequirements
        for i in range(len(analysis['sw-requirements']['warning'])):
            sr_all = dbi.session.query(ApiSwRequirementModel).filter(
                ApiSwRequirementModel.id == analysis['sw-requirements']['warning'][i]['id']
            ).all()
            if len(sr_all) == 1:
                sr_all[0].offset = analysis['sw-requirements']['warning'][i]['new-offset']
                dbi.session.commit()

        # ApiTestSpecification
        for i in range(len(analysis['test-specifications']['warning'])):
            ts_all = dbi.session.query(ApiTestSpecificationModel).filter(
                ApiTestSpecificationModel.id == analysis['test-specifications']['warning'][i]['id']
            ).all()
            if len(ts_all) == 1:
                ts_all[0].offset = analysis['test-specifications']['warning'][i]['new-offset']
                dbi.session.commit()

        # ApiTestCase
        for i in range(len(analysis['test-cases']['warning'])):
            tc_all = dbi.session.query(ApiTestCaseModel).filter(
                ApiTestCaseModel.id == analysis['test-cases']['warning'][i]['id']
            ).all()
            if len(tc_all) == 1:
                tc_all[0].offset = analysis['test-cases']['warning'][i]['new-offset']
                dbi.session.commit()

        # ApiJustification
        for i in range(len(analysis['justifications']['warning'])):
            j_all = dbi.session.query(ApiJustificationModel).filter(
                ApiJustificationModel.id == analysis['justifications']['warning'][i]['id']
            ).all()
            if len(j_all) == 1:
                j_all[0].offset = analysis['justifications']['warning'][i]['new-offset']
                dbi.session.commit()

        dbi.engine.dispose()
        return True


class Api(Resource):
    fields = get_model_editable_fields(ApiModel, False)
    fields_hashes = [x.replace('_', '-') for x in fields]

    def get(self):
        """
        curl http://localhost:5000/apis
        """
        apis_dict = []
        args = get_query_string_args(request.args)
        dbi = db_orm.DbInterface(get_db())
        user_id = 0

        # User permission
        user = get_active_user_from_request(request.args, dbi.session)
        if isinstance(user, UserModel):
            user_id = user.id
            if not user.api_notifications:
                user_api_notifications = []
            else:
                user_api_notifications = user.api_notifications.replace(' ', '').split(',')
                user_api_notifications = [int(x) for x in user_api_notifications]  # Need list of int
        else:
            user_id = 0
            user_api_notifications = []

        query = dbi.session.query(ApiModel)
        query = filter_query(query, args, ApiModel, False)
        apis = query.all()

        # Remove from the list api that are hidden to the current user
        apis = [x for x in apis if f"[{user_id}]" not in x.read_denials]

        if len(apis):
            apis_dict = [x.as_dict(db_session=dbi.session) for x in apis]

        total_coverage = -1
        for iApi in range(len(apis)):
            sections = get_api_sw_requirements_mapping_sections(dbi, apis[iApi])
            if sections is not None:
                if 'mapped' in sections.keys():
                    total_coverage = get_api_coverage(sections['mapped'])
                    apis_dict[iApi]['covered'] = total_coverage

            # Permissions
            permissions = get_api_user_permissions(apis[iApi], user_id, dbi.session)
            apis_dict[iApi]['permissions'] = permissions

        # Populate user notifications settings
        for i in range(len(apis_dict)):
            if apis_dict[i]['id'] in user_api_notifications:
                apis_dict[i]['notifications'] = 1
            else:
                apis_dict[i]['notifications'] = 0

        ret = apis_dict
        ret = sorted(ret, key=lambda api: (api['api'], api['library_version']))
        dbi.engine.dispose()
        return ret

    def post(self):
        """
        add a new Api
        """
        request_data = request.get_json(force=True)
        post_fields = self.fields_hashes.copy()
        post_fields.append('action')
        post_fields.remove('default-view')
        if not check_fields_in_request(post_fields, request_data):
            return 'bad request!', 400

        dbi = db_orm.DbInterface(get_db())

        # Find api
        api = dbi.session.query(ApiModel).filter(
            ApiModel.api == request_data['api']
        ).filter(
            ApiModel.library == request_data['library']
        ).filter(
            ApiModel.library_version == request_data['library-version']
        ).all()

        if len(api) > 0:
            dbi.engine.dispose()
            return 'Api is already in the db for the selected library', 409

        user = get_active_user_from_request(request_data, dbi.session)
        if not isinstance(user, UserModel):
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS
        if user.role not in USER_ROLES_WRITE_PERMISSIONS:
            return 'Current user have no writing permissions', 401

        if request_data['action'] == 'fork':
            source_api = dbi.session.query(ApiModel).filter(
                ApiModel.id == request_data['api-id']
            ).all()
            if len(source_api) != 1:
                return 'Source Api not found', 409
            if source_api[0].api != request_data['api']:
                return 'Source Api name differ from new Api name', 409
            if source_api[0].library != request_data['library']:
                return 'Source Api library differ from new Api library', 409

        new_api = ApiModel(request_data['api'],
                           request_data['library'],
                           request_data['library-version'],
                           request_data['raw-specification-url'],
                           request_data['category'],
                           '',  # Checksum
                           request_data['implementation-file'],
                           request_data['implementation-file-from-row'],
                           request_data['implementation-file-to-row'],
                           request_data['tags'],
                           user)

        dbi.session.add(new_api)
        dbi.session.commit()  # TO have the id of the new api

        # Add Notifications
        notification = f'{user.email} added the sw component ' \
                       f'{new_api.api} as part of the library {new_api.library}'
        notifications = NotificationModel(new_api,
                                          NOTIFICATION_CATEGORY_NEW,
                                          f'{new_api.api} has been created',
                                          notification,
                                          str(user.id),
                                          f'/?currentLibrary={new_api.library}')
        dbi.session.add(notifications)

        if request_data['action'] == 'fork':
            dbi.session.commit()  # to read the id

            # Clone ApiJustification
            api_justifications = dbi.session.query(ApiJustificationModel).filter(
                ApiJustificationModel.api_id == source_api[0].id
            ).all()
            for api_justification in api_justifications:
                tmp = ApiJustificationModel(new_api,
                                            api_justification.justification,
                                            api_justification.section,
                                            api_justification.offset,
                                            api_justification.coverage,
                                            user)
                dbi.session.add(tmp)

            # Clone ApiSwRequirement
            api_sw_requirements = dbi.session.query(ApiSwRequirementModel).filter(
                ApiSwRequirementModel.api_id == source_api[0].id
            ).all()
            for api_sw_requirement in api_sw_requirements:
                tmp = ApiSwRequirementModel(new_api,
                                            api_sw_requirement.sw_requirement,
                                            api_sw_requirement.section,
                                            api_sw_requirement.offset,
                                            api_sw_requirement.coverage,
                                            user)
                dbi.session.add(tmp)

            # Clone ApiTestSpecification
            api_test_specifications = dbi.session.query(ApiTestSpecificationModel).filter(
                ApiTestSpecificationModel.api_id == source_api[0].id
            ).all()
            for api_test_specification in api_test_specifications:
                tmp = ApiTestSpecificationModel(new_api,
                                                api_test_specification.test_specification,
                                                api_test_specification.section,
                                                api_test_specification.offset,
                                                api_test_specification.coverage,
                                                user)
                dbi.session.add(tmp)

            # Clone ApiTestCase
            api_test_cases = dbi.session.query(ApiTestCaseModel).filter(
                ApiTestCaseModel.api_id == source_api[0].id
            ).all()
            for api_test_case in api_test_cases:
                tmp = ApiTestCaseModel(new_api,
                                       api_test_case.test_case,
                                       api_test_case.section,
                                       api_test_case.offset,
                                       api_test_case.coverage,
                                       user)
                dbi.session.add(tmp)

        dbi.session.commit()
        dbi.engine.dispose()
        return new_api.as_dict()

    def put(self):
        """
        edit an existing Api
        """

        request_data = request.get_json(force=True)
        put_fields = self.fields_hashes.copy()
        put_fields.append('api-id')
        if not check_fields_in_request(put_fields, request_data):
            return BAD_REQUEST_MESSAGE, BAD_REQUEST_STATUS

        dbi = db_orm.DbInterface(get_db())

        # Find api
        api = get_api_from_request(request_data, dbi.session)

        if not api:
            dbi.engine.dispose()
            return NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

        # User permission
        user = get_active_user_from_request(request_data, dbi.session)
        if not isinstance(user, UserModel):
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        # Permissions
        permissions = get_api_user_permissions(api, user.id, dbi.session)
        if 'e' not in permissions or user.role not in USER_ROLES_EDIT_PERMISSIONS:
            dbi.engine.dispose()
            return FORBIDDEN_MESSAGE, FORBIDDEN_STATUS

        # Check that the new api+library+library_version is not already in the db
        same_existing_apis = dbi.session.query(ApiModel).filter(
            ApiModel.api == request_data['api']
        ).filter(
            ApiModel.library == request_data['library']
        ).filter(
            ApiModel.library == request_data['library-version']
        ).filter(
            ApiModel.id != request_data['api-id']).all()

        if len(same_existing_apis) > 0:
            dbi.engine.dispose()
            return 'An Api with selected name and library already exist in the db', 409

        api_modified = False
        for field in self.fields:
            if field.replace('_', '-') in request_data.keys():
                if getattr(api, field) != request_data[field.replace('_', '-')]:
                    api_modified = True
                    setattr(api, field, request_data[field.replace('_', '-')])

        if api_modified:
            api.edited_by_id = user.id

            # Add Notifications
            notification = f'{user.email} modified sw component ' \
                           f'{api.api} as part of the library {api.library}'
            notifications = NotificationModel(api,
                                              NOTIFICATION_CATEGORY_EDIT,
                                              f'{api.api} has been modified',
                                              notification,
                                              str(user.id),
                                              f'/?currentLibrary={api.library}')
            dbi.session.add(notifications)

        dbi.session.commit()
        dbi.engine.dispose()
        return api.as_dict()

    def delete(self):
        request_data = request.get_json(force=True)

        delete_fields = self.fields_hashes.copy()
        delete_fields.append('api-id')
        if not check_fields_in_request(delete_fields, request_data):
            return 'bad request!', 400

        dbi = db_orm.DbInterface(get_db())

        # Find api
        apis = dbi.session.query(ApiModel).filter(
            ApiModel.id == request_data['api-id']
        ).filter(
            ApiModel.api == request_data['api']
        ).filter(
            ApiModel.library == request_data['library']
        ).filter(
            ApiModel.library_version == request_data['library-version']
        ).one()

        if len(apis) != 1:
            dbi.engine.dispose()
            return 'Api not found', 400

        api = apis[0]

        # User permission
        user = get_active_user_from_request(request_data, dbi.session)
        if not isinstance(user, UserModel):
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        # Permissions
        permissions = get_api_user_permissions(api, user.id, dbi.session)
        if 'e' not in permissions or user.role not in USER_ROLES_EDIT_PERMISSIONS:
            dbi.engine.dispose()
            return FORBIDDEN_MESSAGE, FORBIDDEN_STATUS

        justifications_mapping_api = dbi.session.query(ApiJustificationModel).filter(
            ApiJustificationModel.api_id == api.id).all()

        sw_requirements_mapping_api = dbi.session.query(ApiSwRequirementModel).filter(
            ApiSwRequirementModel.api_id == api.id).all()

        test_specifications_mapping_api = dbi.session.query(ApiTestSpecificationModel).filter(
            ApiTestSpecificationModel.api_id == api.id).all()

        test_cases_mapping_api = dbi.session.query(ApiTestCaseModel).filter(
            ApiTestCaseModel.api_id == api.id).all()

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
        notification = f'{user.email} deleted sw component ' \
                       f'{api.api} as part of the library {api.library}'
        notifications = NotificationModel(api,
                                          NOTIFICATION_CATEGORY_DELETE,
                                          f'{api.api} has been deleted',
                                          notification,
                                          str(user.id),
                                          f'/?currentLibrary={api.library}')
        dbi.session.add(notifications)
        dbi.session.commit()
        dbi.engine.dispose()
        return True


class ApiHistory(Resource):
    def get(self):
        args = get_query_string_args(request.args)

        if 'api-id' not in args.keys():
            return []

        dbi = db_orm.DbInterface(get_db())

        _model = ApiModel
        _model_history = ApiHistoryModel
        _model_fields = _model.__table__.columns.keys()

        model_versions_query = dbi.session.query(_model_history).filter(
            _model_history.id == args['api-id']).order_by(
            _model_history.version.asc())
        staging_array = []
        ret = []

        # object dict
        for model_version in model_versions_query.all():
            obj = {"version": model_version.version,
                   "type": "object",
                   "created_at": datetime.datetime.strptime(str(model_version.created_at), '%Y-%m-%d %H:%M:%S.%f')}

            for k in _model_fields:
                if k not in ['row_id', 'version', 'created_at', 'updated_at']:
                    obj[k] = getattr(model_version, k)

            staging_array.append(obj)

        staging_array = sorted(staging_array, key=lambda d: (d['created_at']))

        # get version object.mapping equal to 1.1
        first_found = False
        first_obj = {}
        for i in range(len(staging_array)):
            if staging_array[i]['version'] == 1 and staging_array[i]['type'] == 'object':
                first_obj = staging_array[i]
                first_found = True
                break

        if not first_found:
            dbi.engine.dispose()
            return []

        ret.append(get_combined_history_object(first_obj, {}, _model_fields, []))

        for i in range(len(staging_array)):
            last_obj_version = int(ret[-1]['version'].split(".")[0])
            if staging_array[i]['type'] == 'object' and staging_array[i]['version'] > last_obj_version:
                ret.append(get_combined_history_object(staging_array[i], ret[-1]['mapping'], _model_fields, []))

        ret = get_reduced_history_data(ret, _model_fields, [], dbi.session)

        for i in range(len(ret)):
            for permission_field in API_PERMISSION_FIELDS:
                if permission_field in ret[i]['object'].keys():
                    ret[i]['object'][permission_field] = ", ".join(get_users_email_from_ids(
                        ret[i]['object'][permission_field], dbi.session))
                if permission_field in ret[i]['mapping'].keys():
                    ret[i]['mapping'][permission_field] = ", ".join(get_users_email_from_ids(
                        ret[i]['mapping'][permission_field], dbi.session))

        ret = ret[::-1]
        dbi.engine.dispose()
        return ret


class Library(Resource):

    def get(self):
        """
        curl http://localhost:5000/api
        """

        # args = get_query_string_args(request.args)
        dbi = db_orm.DbInterface(get_db())
        libraries = dbi.session.query(ApiModel.library).distinct().all()
        dbi.engine.dispose()
        return sorted([x.library for x in libraries])


class ApiSpecification(Resource):
    def get(self):
        """
                curl http://localhost:5000/api
                """

        args = get_query_string_args(request.args)
        if "api-id" not in args.keys():
            return {}

        dbi = db_orm.DbInterface(get_db())

        # User
        user_id = get_user_id_from_request(args, dbi.session)

        api = get_api_from_request(args, dbi.session)
        if not api:
            dbi.engine.dispose()
            return NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

        spec = get_api_specification(api.raw_specification_url)

        # Permissions
        permissions = get_api_user_permissions(api, user_id, dbi.session)
        if 'r' not in permissions:
            dbi.engine.dispose()
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        ret = api.as_dict()
        ret['raw_specification'] = spec
        ret['permissions'] = permissions
        dbi.engine.dispose()
        return ret


class ApiTestSpecificationsMapping(Resource):
    fields = ['api-id', 'test-specification', 'section', 'coverage']

    def get(self):
        """
        curl <API_URL>/api/test-specifications?api-id=<api-id>
        """
        args = get_query_string_args(request.args)
        if not check_fields_in_request(['api-id'], args):
            return 'bad request!', 400

        undesired_keys = ['section', 'offset']

        dbi = db_orm.DbInterface(get_db())

        # User
        user_id = get_user_id_from_request(args, dbi.session)

        # Find api
        api = get_api_from_request(args, dbi.session)
        if not api:
            dbi.engine.dispose()
            return NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

        # Permissions
        permissions = get_api_user_permissions(api, user_id, dbi.session)
        if 'r' not in permissions:
            dbi.engine.dispose()
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        api_specification = get_api_specification(api.raw_specification_url)
        if api_specification is None:
            return []

        ts = dbi.session.query(ApiTestSpecificationModel).filter(
            ApiTestSpecificationModel.api_id == api.id).order_by(
            ApiTestSpecificationModel.offset.asc()).all()
        ts_mapping = [x.as_dict(db_session=dbi.session) for x in ts]

        justifications = dbi.session.query(ApiJustificationModel).filter(
            ApiJustificationModel.api_id == api.id).order_by(
            ApiJustificationModel.offset.asc()).all()
        justifications_mapping = [x.as_dict(db_session=dbi.session) for x in justifications]

        mapping = {_A: api.as_dict(),
                   _TSs: ts_mapping,
                   _Js: justifications_mapping}

        for iTS in range(len(mapping[_TSs])):
            # Indirect Test Cases
            curr_ats_id = mapping[_TSs][iTS]['relation_id']

            ind_tc = dbi.session.query(TestSpecificationTestCaseModel).filter(
                TestSpecificationTestCaseModel.test_specification_mapping_api_id == curr_ats_id
            ).all()
            mapping[_TSs][iTS][_TS][_TCs] = [get_dict_without_keys(x.as_dict(db_session=dbi.session),
                                                                   undesired_keys + ['api']) for x in ind_tc]

        for iMapping in range(len(mapping[_TSs])):
            current_offset = mapping[_TSs][iMapping]['offset']
            current_section = mapping[_TSs][iMapping]['section']
            mapping[_TSs][iMapping]['match'] = (
                    api_specification[current_offset:current_offset + len(current_section)] == current_section)
        for iMapping in range(len(mapping[_Js])):
            current_offset = mapping[_Js][iMapping]['offset']
            current_section = mapping[_Js][iMapping]['section']
            mapping[_Js][iMapping]['match'] = (
                    api_specification[current_offset:current_offset + len(current_section)] == current_section)

        mapped_sections = get_split_sections(api_specification, mapping, [_TS, _J])
        unmapped_sections = [x for x in mapping[_TSs] if not x['match']]
        unmapped_sections += [x for x in mapping[_Js] if not x['match']]
        ret = {'mapped': mapped_sections,
               'unmapped': unmapped_sections}

        dbi.engine.dispose()
        return ret

    def post(self):
        request_data = request.get_json(force=True)

        if not check_fields_in_request(self.fields, request_data):
            return 'bad request!', 400

        dbi = db_orm.DbInterface(get_db())

        # User
        user = get_active_user_from_request(request_data, dbi.session)
        if not isinstance(user, UserModel):
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        # Find api
        api = get_api_from_request(request_data, dbi.session)
        if not api:
            dbi.engine.dispose()
            return NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

        # Permissions
        permissions = get_api_user_permissions(api, user.id, dbi.session)
        if 'w' not in permissions or user.role not in USER_ROLES_WRITE_PERMISSIONS:
            dbi.engine.dispose()
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        section = request_data['section']
        offset = request_data['offset']
        coverage = request_data['coverage']

        if 'id' not in request_data['test-specification'].keys():
            # Create a new one
            # `status` field should be skipped because a default is assigned in the model
            for check_field in [x for x in TestSpecification.fields if x not in ['status']]:
                if check_field.replace("_", "-") not in request_data['test-specification'].keys():
                    dbi.engine.dispose()
                    return "Bad request. Unconsistent data.", 400

            title = request_data['test-specification']['title']
            preconditions = request_data['test-specification']['preconditions']
            test_description = request_data['test-specification']['test-description']
            expected_behavior = request_data['test-specification']['expected-behavior']

            if len(dbi.session.query(TestSpecificationModel).filter(
                        TestSpecificationModel.title == title).filter(
                    TestSpecificationModel.preconditions == preconditions).filter(
                    TestSpecificationModel.test_description == test_description).filter(
                    TestSpecificationModel.expected_behavior == expected_behavior).all()) > 0:
                dbi.engine.dispose()
                return "Test Specification already associated to the selected api Specification section.", 409

            new_test_specification = TestSpecificationModel(title,
                                                            preconditions,
                                                            test_description,
                                                            expected_behavior,
                                                            user)
            new_test_specification_mapping_api = ApiTestSpecificationModel(api,
                                                                           new_test_specification,
                                                                           section,
                                                                           offset,
                                                                           coverage,
                                                                           user)

            dbi.session.add(new_test_specification)
            dbi.session.add(new_test_specification_mapping_api)

        else:
            id = request_data['test-specification']['id']
            if len(dbi.session.query(ApiTestSpecificationModel).filter(
                        ApiTestSpecificationModel.api_id == api.id).filter(
                    ApiTestSpecificationModel.test_specification_id == id).filter(
                    ApiTestSpecificationModel.section == section).all()) > 0:
                dbi.engine.dispose()
                return "Test Specification already associated to the selected api Specification section.", 409

            try:
                existing_test_specification = dbi.session.query(TestSpecificationModel).filter(
                    TestSpecificationModel.id == id).one()
            except NoResultFound:
                return f"Unable to find the Test Specification id {id}", 400

            new_test_specification_mapping_api = ApiTestSpecificationModel(api,
                                                                           existing_test_specification,
                                                                           section,
                                                                           offset,
                                                                           coverage,
                                                                           user)
            dbi.session.add(new_test_specification_mapping_api)

        dbi.session.commit()  # To have the id

        # Add Notifications
        notification = f'{user.email} added Test Specification ' \
                       f'{new_test_specification_mapping_api.test_specification.id} ' \
                       f'mapped to ' \
                       f'{api.api} as part of the library {api.library}'
        notifications = NotificationModel(api,
                                          NOTIFICATION_CATEGORY_NEW,
                                          f'{api.api} - Test Specification mapping '
                                          f'{new_test_specification_mapping_api.id} '
                                          f'has been added',
                                          notification,
                                          str(user.id),
                                          f'/mapping/{api.id}')
        dbi.session.add(notifications)
        dbi.session.commit()
        dbi.engine.dispose()
        return new_test_specification_mapping_api.as_dict()

    def put(self):

        request_data = request.get_json(force=True)

        if not check_fields_in_request(self.fields, request_data):
            return 'bad request!', 400

        dbi = db_orm.DbInterface(get_db())

        # User
        user = get_active_user_from_request(request_data, dbi.session)
        if not isinstance(user, UserModel):
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        # Find api
        api = get_api_from_request(request_data, dbi.session)
        if not api:
            dbi.engine.dispose()
            return NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

        # Permissions
        permissions = get_api_user_permissions(api, user.id, dbi.session)
        if 'w' not in permissions or user.role not in USER_ROLES_WRITE_PERMISSIONS:
            dbi.engine.dispose()
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        try:
            test_specification_mapping_api = dbi.session.query(ApiTestSpecificationModel).filter(
                ApiTestSpecificationModel.id == request_data["relation-id"]).one()
        except NoResultFound:
            return f"Unable to find the Test Specification mapping to Api id {request_data['relation-id']}", 400

        test_specification = test_specification_mapping_api.test_specification

        # Update only modified fields
        modified_ts = False
        for field in TestSpecification.fields:
            if field.replace('_', '-') in request_data["test-specification"].keys():
                if getattr(test_specification, field) != request_data["test-specification"][field.replace('_', '-')]:
                    modified_ts = True
                    setattr(test_specification, field, request_data["test-specification"][field.replace('_', '-')])

        if modified_ts:
            setattr(test_specification, 'edited_by_id', user.id)

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
            notification = f'{user.email} modified test specification ' \
                           f'{test_specification_mapping_api.test_specification.title}'
            notifications = NotificationModel(api,
                                              NOTIFICATION_CATEGORY_EDIT,
                                              f'{api.api} - Test Specification has been modified',
                                              notification,
                                              str(user.id),
                                              f'/mapping/{api.id}')
            dbi.session.add(notifications)
            dbi.session.commit()

        dbi.engine.dispose()
        return test_specification_mapping_api.as_dict()

    def delete(self):
        request_data = request.get_json(force=True)

        if not check_fields_in_request(['relation-id', 'api-id'], request_data):
            return 'bad request!', 400

        dbi = db_orm.DbInterface(get_db())

        # User
        user = get_active_user_from_request(request_data, dbi.session)

        # Find api
        api = get_api_from_request(request_data, dbi.session)
        if not api:
            dbi.engine.dispose()
            return NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

        # Permissions
        permissions = get_api_user_permissions(api, user.id, dbi.session)
        if 'w' not in permissions or user.role not in USER_ROLES_WRITE_PERMISSIONS:
            dbi.engine.dispose()
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        # check if api ...
        try:
            test_specification_mapping_api = dbi.session.query(ApiTestSpecificationModel).filter(
                ApiTestSpecificationModel.id == request_data["relation-id"]).one()
        except NoResultFound:
            return f"Unable to find the Test Specification mapping to Api id {request_data['relation-id']}", 400

        if test_specification_mapping_api.api.id != api.id:
            dbi.engine.dispose()
            return 'bad request!', 401

        notification_ts_id = test_specification_mapping_api.test_specification.id
        notification_ts_title = test_specification_mapping_api.test_specification.title
        dbi.session.delete(test_specification_mapping_api)
        dbi.session.commit()

        # Add Notifications
        notification = f'{user.email} deleted test specification ' \
                       f'{notification_ts_id} {notification_ts_title}'
        notifications = NotificationModel(api,
                                          NOTIFICATION_CATEGORY_DELETE,
                                          f'{api.api} - Test Specification has been deleted',
                                          notification,
                                          str(user.id),
                                          f'/mapping/{api.id}')
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
        dbi.engine.dispose()
        return True


class ApiTestCasesMapping(Resource):
    fields = ['api-id', 'test-case', 'section', 'coverage']

    def get(self):
        """
        curl <API_URL>/api/test-cases?api-id=<api-id>
        """

        args = get_query_string_args(request.args)
        if not check_fields_in_request(['api-id'], args):
            return 'bad request!', 400

        # undesired_keys = ['section', 'offset']

        dbi = db_orm.DbInterface(get_db())

        # User
        user_id = get_user_id_from_request(args, dbi.session)

        # Find api
        api = get_api_from_request(args, dbi.session)
        if not api:
            dbi.engine.dispose()
            return NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

        # Permissions
        permissions = get_api_user_permissions(api, user_id, dbi.session)
        if 'r' not in permissions:
            dbi.engine.dispose()
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        api_specification = get_api_specification(api.raw_specification_url)
        if api_specification is None:
            return []

        tc = dbi.session.query(ApiTestCaseModel).filter(
            ApiTestCaseModel.api_id == api.id).order_by(
            ApiTestCaseModel.offset.asc()).all()
        tc_mapping = [x.as_dict(db_session=dbi.session) for x in tc]

        justifications = dbi.session.query(ApiJustificationModel).filter(
            ApiJustificationModel.api_id == api.id).order_by(
            ApiJustificationModel.offset.asc()).all()
        justifications_mapping = [x.as_dict(db_session=dbi.session) for x in justifications]

        mapping = {_A: api.as_dict(),
                   _TCs: tc_mapping,
                   _Js: justifications_mapping}

        for iMapping in range(len(mapping[_TCs])):
            current_offset = mapping[_TCs][iMapping]['offset']
            current_section = mapping[_TCs][iMapping]['section']
            mapping[_TCs][iMapping]['match'] = (
                    api_specification[current_offset:current_offset + len(current_section)] == current_section)
        for iMapping in range(len(mapping[_Js])):
            current_offset = mapping[_Js][iMapping]['offset']
            current_section = mapping[_Js][iMapping]['section']
            mapping[_Js][iMapping]['match'] = (
                    api_specification[current_offset:current_offset + len(current_section)] == current_section)

        mapped_sections = get_split_sections(api_specification, mapping, [_TC, _J])
        unmapped_sections = [x for x in mapping[_TCs] if not x['match']]
        unmapped_sections += [x for x in mapping[_Js] if not x['match']]
        ret = {'mapped': mapped_sections,
               'unmapped': unmapped_sections}

        dbi.engine.dispose()
        return ret

    def post(self):
        request_data = request.get_json(force=True)

        if not check_fields_in_request(self.fields, request_data):
            return 'bad request!', 400

        dbi = db_orm.DbInterface(get_db())

        # User
        user = get_active_user_from_request(request_data, dbi.session)
        if not isinstance(user, UserModel):
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        # Find api
        api = get_api_from_request(request_data, dbi.session)
        if not api:
            dbi.engine.dispose()
            return NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

        # Permissions
        permissions = get_api_user_permissions(api, user.id, dbi.session)
        if 'w' not in permissions or user.role not in USER_ROLES_WRITE_PERMISSIONS:
            dbi.engine.dispose()
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        section = request_data['section']
        offset = request_data['offset']
        coverage = request_data['coverage']

        if 'id' not in request_data['test-case'].keys():
            # Create a new one
            # `status` field should be skipped because a default is assigned in the model
            for check_field in [x for x in TestCase.fields if x not in ['status']]:
                if check_field.replace("_", "-") not in request_data['test-case'].keys():
                    dbi.engine.dispose()
                    return "Bad request. Not consistent data.", 400

            repository = request_data['test-case']['repository']
            relative_path = request_data['test-case']['relative-path']
            title = request_data['test-case']['title']
            description = request_data['test-case']['description']

            # Check if the same Test Case is already associated with the same snippet
            if len(dbi.session.query(ApiTestCaseModel).join(TestCaseModel).filter(
                        ApiTestCaseModel.section == section).filter(
                    TestCaseModel.repository == repository).filter(
                    TestCaseModel.relative_path == relative_path).all()) > 0:
                dbi.engine.dispose()
                return "Test Case already associated to the current api.", 409

            new_test_case = TestCaseModel(repository,
                                          relative_path,
                                          title,
                                          description,
                                          user)

            new_test_case_mapping_api = ApiTestCaseModel(api,
                                                         new_test_case,
                                                         section,
                                                         offset,
                                                         coverage,
                                                         user)
            dbi.session.add(new_test_case)
            dbi.session.add(new_test_case_mapping_api)
        else:
            id = request_data['test-case']['id']
            if len(dbi.session.query(ApiTestCaseModel).filter(ApiTestCaseModel.api_id == api.id).filter(
                    ApiTestCaseModel.test_case_id == id).filter(ApiTestCaseModel.section == section).all()) > 0:
                dbi.engine.dispose()
                return "Test Case already associated to the selected api Specification section.", 409

            try:
                existing_test_case = dbi.session.query(TestCaseModel).filter(TestCaseModel.id == id).one()
            except NoResultFound:
                return f"Unable to find the Test Case id {id}", 400

            new_test_case_mapping_api = ApiTestCaseModel(api,
                                                         existing_test_case,
                                                         section,
                                                         offset,
                                                         coverage,
                                                         user)

            dbi.session.add(new_test_case_mapping_api)

        dbi.session.commit()  # To have the id

        # Add Notifications
        notification = f'{user.email} added Test Case {new_test_case_mapping_api.test_case.id} ' \
                       f'mapped to ' \
                       f'{api.api} as part of the library {api.library}'
        notifications = NotificationModel(api,
                                          NOTIFICATION_CATEGORY_NEW,
                                          f'{api.api} - Test Case mapping '
                                          f'{new_test_case_mapping_api.id} has been added',
                                          notification,
                                          str(user.id),
                                          f'/mapping/{api.id}')
        dbi.session.add(notifications)
        dbi.engine.dispose()
        return new_test_case_mapping_api.as_dict()

    def put(self):
        request_data = request.get_json(force=True)

        if not check_fields_in_request(self.fields, request_data):
            return 'bad request!', 400

        dbi = db_orm.DbInterface(get_db())

        # User
        user = get_active_user_from_request(request_data, dbi.session)
        if not isinstance(user, UserModel):
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        # Find api
        api = get_api_from_request(request_data, dbi.session)
        if not api:
            dbi.engine.dispose()
            return NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

        # Permissions
        permissions = get_api_user_permissions(api, user.id, dbi.session)
        if 'w' not in permissions or user.role not in USER_ROLES_WRITE_PERMISSIONS:
            dbi.engine.dispose()
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        try:
            test_case_mapping_api = dbi.session.query(ApiTestCaseModel).filter(
                ApiTestCaseModel.id == request_data["relation-id"]).one()
            test_case = test_case_mapping_api.test_case
        except NoResultFound:
            dbi.engine.dispose()
            return "Test Case mapping api not found", 400

        # Update only modified fields
        modified_tc = False
        for field in TestCase.fields:
            if field.replace('_', '-') in request_data["test-case"].keys():
                if getattr(test_case, field) != request_data["test-case"][field.replace('_', '-')]:
                    modified_tc = True
                    setattr(test_case, field, request_data["test-case"][field.replace('_', '-')])

        if modified_tc:
            setattr(test_case, 'edited_by_id', user.id)

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
            notification = f'{user.email} modified a test case mapped ' \
                           f'to {api.api}'
            notifications = NotificationModel(api,
                                              NOTIFICATION_CATEGORY_EDIT,
                                              f'{api.api} - Test Case has been modified',
                                              notification,
                                              str(user.id),
                                              f'/mapping/{api.id}')
            dbi.session.add(notifications)
            dbi.session.commit()

        dbi.engine.dispose()
        return test_case_mapping_api.as_dict()

    def delete(self):
        request_data = request.get_json(force=True)

        if not check_fields_in_request(['relation-id', 'api-id'], request_data):
            return 'bad request!', 400

        dbi = db_orm.DbInterface(get_db())

        # User
        user = get_active_user_from_request(request_data, dbi.session)
        if not isinstance(user, UserModel):
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        # Find api
        api = get_api_from_request(request_data, dbi.session)
        if not api:
            dbi.engine.dispose()
            return NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

        # Permissions
        permissions = get_api_user_permissions(api, user.id, dbi.session)
        if 'w' not in permissions or user.role not in USER_ROLES_WRITE_PERMISSIONS:
            dbi.engine.dispose()
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        # check if api ...
        try:
            test_case_mapping_api = dbi.session.query(ApiTestCaseModel).filter(
                ApiTestCaseModel.id == request_data["relation-id"]).one()
        except NoResultFound:
            return f"Unable to find the Test Case mapping to Api id {request_data['relation-id']}", 400

        if test_case_mapping_api.api.id != api.id:
            dbi.engine.dispose()
            return 'bad request!', 401

        notification_tc_id = test_case_mapping_api.test_case.id
        notification_tc_title = test_case_mapping_api.test_case.title
        dbi.session.delete(test_case_mapping_api)
        dbi.session.commit()

        # Add Notifications
        notification = f'{user.email} deleted test case ' \
                       f'{notification_tc_id} {notification_tc_title}'
        notifications = NotificationModel(api,
                                          NOTIFICATION_CATEGORY_DELETE,
                                          f'{api.api} - Test Case has been deleted',
                                          notification,
                                          str(user.id),
                                          f'/mapping/{api.id}')
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
        dbi.engine.dispose()
        return True


class MappingHistory(Resource):
    def get(self):
        args = get_query_string_args(request.args)
        dbi = db_orm.DbInterface(get_db())

        if 'work_item_type' not in args.keys() or \
                'mapped_to_type' not in args.keys() or \
                'relation_id' not in args.keys():
            dbi.engine.dispose()
            return []

        if args['mapped_to_type'] == "api":
            if args['work_item_type'] == 'justification':
                _model = JustificationModel
                _model_map = ApiJustificationModel
                _model_map_history = ApiJustificationHistoryModel
                _model_history = JustificationHistoryModel
            elif args['work_item_type'] == 'sw-requirement':
                _model = SwRequirementModel
                _model_map = ApiSwRequirementModel
                _model_map_history = ApiSwRequirementHistoryModel
                _model_history = SwRequirementHistoryModel
            elif args['work_item_type'] == 'test-specification':
                _model = TestSpecificationModel
                _model_map = ApiTestSpecificationModel
                _model_map_history = ApiTestSpecificationHistoryModel
                _model_history = TestSpecificationHistoryModel
            elif args['work_item_type'] == 'test-case':
                _model = TestCaseModel
                _model_map = ApiTestCaseModel
                _model_map_history = ApiTestCaseHistoryModel
                _model_history = TestCaseHistoryModel
            else:
                dbi.engine.dispose()
                return []

        elif args['mapped_to_type'] == "sw-requirement":
            if args['work_item_type'] == 'sw-requirement':
                _model = SwRequirementModel
                _model_map = SwRequirementSwRequirementModel
                _model_map_history = SwRequirementSwRequirementHistoryModel
                _model_history = SwRequirementHistoryModel
            elif args['work_item_type'] == 'test-specification':
                _model = TestSpecificationModel
                _model_map = SwRequirementTestSpecificationModel
                _model_map_history = SwRequirementTestSpecificationHistoryModel
                _model_history = TestSpecificationHistoryModel
            elif args['work_item_type'] == 'test-case':
                _model = TestCaseModel
                _model_map = SwRequirementTestCaseModel
                _model_map_history = SwRequirementTestCaseHistoryModel
                _model_history = TestCaseHistoryModel
            else:
                dbi.engine.dispose()
                return []

        elif args['mapped_to_type'] == "test-specification":
            if args['work_item_type'] == 'test-case':
                _model = TestCaseModel
                _model_map = TestSpecificationTestCaseModel
                _model_map_history = TestSpecificationTestCaseHistoryModel
                _model_history = TestCaseHistoryModel
            else:
                dbi.engine.dispose()
                return []
        else:
            dbi.engine.dispose()
            return []

        _model_fields = _model.__table__.columns.keys()
        _model_map_fields = _model_map.__table__.columns.keys()

        relation_rows = dbi.session.query(_model_map).filter(_model_map.id == args['relation_id']).all()
        if len(relation_rows) != 1:
            dbi.engine.dispose()
            return []

        relation_row = relation_rows[0].as_dict()

        model_versions_query = dbi.session.query(_model_history).filter(
            _model_history.id == relation_row[args['work_item_type'].replace('-', '_')]['id']).order_by(
            _model_history.version.asc())
        model_map_versions_query = dbi.session.query(_model_map_history).filter(
            _model_map_history.id == args['relation_id']).order_by(
            _model_map_history.version.asc())

        staging_array = []
        ret = []

        # object dict
        for model_version in model_versions_query.all():
            # _description = ''

            obj = {"version": model_version.version,
                   "type": "object",
                   "created_at": datetime.datetime.strptime(str(model_version.created_at), '%Y-%m-%d %H:%M:%S.%f')}

            for k in _model_fields:
                if k not in ['row_id', 'version', 'created_at', 'updated_at']:
                    obj[k] = getattr(model_version, k)

            staging_array.append(obj)

        # map dict
        for model_map_version in model_map_versions_query.all():
            obj = {"version": model_map_version.version,
                   "type": "mapping",
                   "created_at": datetime.datetime.strptime(str(model_map_version.created_at),
                                                            '%Y-%m-%d %H:%M:%S.%f')}
            for k in _model_map_fields:
                if args['work_item_type'] == 'justification':
                    if k not in ['coverage', 'created_at', 'updated_at']:
                        obj[k] = getattr(model_map_version, k)
                else:
                    if k not in ['created_at', 'updated_at']:
                        obj[k] = getattr(model_map_version, k)

            staging_array.append(obj)

        staging_array = sorted(staging_array, key=lambda d: (d['created_at']))

        # get version object.mapping equal to 1.1
        first_found = False
        first_obj = {}
        first_map = {}

        for i in range(len(staging_array)):
            if staging_array[i]['version'] == 1 and staging_array[i]['type'] == 'object':
                first_obj = staging_array[i]
            elif staging_array[i]['version'] == 1 and staging_array[i]['type'] == 'mapping':
                first_map = staging_array[i]
            if first_map != {} and first_obj != {}:
                first_found = True
                break

        if not first_found:
            dbi.engine.dispose()
            return []

        ret.append(get_combined_history_object(first_obj, first_map, _model_fields, _model_map_fields))

        for i in range(len(staging_array)):
            last_obj_version = int(ret[-1]['version'].split(".")[0])
            last_map_version = int(ret[-1]['version'].split(".")[1])
            if staging_array[i]['type'] == 'object' and staging_array[i]['version'] > last_obj_version:
                ret.append(
                    get_combined_history_object(staging_array[i],
                                                ret[-1]['mapping'],
                                                _model_fields,
                                                _model_map_fields))
            elif staging_array[i]['type'] == 'mapping' and staging_array[i]['version'] > last_map_version:
                ret.append(
                    get_combined_history_object(ret[-1]['object'], staging_array[i], _model_fields, _model_map_fields))

        ret = get_reduced_history_data(ret, _model_fields, _model_map_fields, dbi.session)
        ret = ret[::-1]
        dbi.engine.dispose()
        return ret


class MappingUsage(Resource):
    def get(self):
        """ Return list of api the selected work item is mapped directly against
            Improvement: Take in consideration also indirect mapping and other
              work items, like list of Test Specifications where a Test Case
              is used
        """
        args = get_query_string_args(request.args)
        dbi = db_orm.DbInterface(get_db())

        if 'work_item_type' not in args.keys() or 'id' not in args.keys():
            dbi.engine.dispose()
            return []

        _id = args['id']

        # Api
        if args['work_item_type'] == "justification":
            model = ApiJustificationModel
            api_data = dbi.session.query(model).filter(
                model.justification_id == _id
            ).all()
            api_ids = [x.api_id for x in api_data]
        elif args['work_item_type'] == "sw-requirement":
            model = ApiSwRequirementModel
            api_data = dbi.session.query(model).filter(
                model.sw_requirement_id == _id
            ).all()
            api_ids = [x.api_id for x in api_data]
        elif args['work_item_type'] == "test-specification":
            # Direct
            model = ApiTestSpecificationModel
            api_data = dbi.session.query(model).filter(
                model.test_specification_id == _id
            ).all()
            api_ids = [x.api_id for x in api_data]

            # indirect sw requirement mapping api:
            model = SwRequirementTestSpecificationModel
            parent_model = ApiSwRequirementModel
            sr_api_data = dbi.session.query(model).join(parent_model).filter(
                model.test_specification_id == _id
            ).all()
            api_ids += [x.sw_requirement_mapping_api.api_id for x in sr_api_data]
        elif args['work_item_type'] == "test-case":
            model = ApiTestCaseModel
            api_data = dbi.session.query(model).filter(
                model.test_case_id == _id
            ).all()
            api_ids = [x.api_id for x in api_data]

            # indirect test specification mapping api:
            model = TestSpecificationTestCaseModel
            parent_model = ApiTestSpecificationModel
            ts_api_data = dbi.session.query(model).join(parent_model).filter(
                model.test_case_id == _id
            ).all()
            api_ids += [x.sw_requirement_mapping_api.api_id for x in ts_api_data]

            # indirect sw requirement mapping api:
            model = SwRequirementTestCaseModel
            parent_model = ApiSwRequirementModel
            sr_api_data = dbi.session.query(model).join(parent_model).filter(
                model.test_case_id == _id
            ).all()
            api_ids += [x.sw_requirement_mapping_api.api_id for x in sr_api_data]

            # indirect test specification sw requirement:
            model = TestSpecificationTestCaseModel
            parent_model = SwRequirementTestSpecificationModel
            sr_ts_data = dbi.session.query(model).join(parent_model).filter(
                model.test_case_id == _id
            ).all()
            sr_ts_ids = [x.test_specification_mapping_sw_requirement_id for x in sr_ts_data]
            model = SwRequirementTestSpecificationModel
            parent_model = ApiSwRequirementModel
            sr_api_data = dbi.session.query(model).join(parent_model).filter(
                model.sw_requirement_mapping_api_id.in_(sr_ts_ids)).all()
            api_ids += [x.sw_requirement_mapping_api.api_id for x in sr_api_data]

        apis = dbi.session.query(ApiModel).filter(
            ApiModel.id.in_(api_ids)
        ).all()

        query_data = {'api': [{'id': x.id,
                               'api': x.api,
                               'library': x.library,
                               'library_version': x.library_version} for x in apis]}

        return query_data


class ApiSpecificationsMapping(Resource):
    fields = ['api-id', 'justification', 'section', 'offset']

    def get(self):
        """
        curl <API_URL>/api/specifications?api-id=<api-id>
        """

        args = get_query_string_args(request.args)
        if not check_fields_in_request(['api-id'], args):
            return 'bad request!', 400

        # undesired_keys = ['section', 'offset']

        dbi = db_orm.DbInterface(get_db())

        # User
        user_id = get_user_id_from_request(args, dbi.session)

        # Find api
        api = get_api_from_request(args, dbi.session)
        if not api:
            dbi.engine.dispose()
            return NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

        # Permissions
        permissions = get_api_user_permissions(api, user_id, dbi.session)
        if 'r' not in permissions:
            dbi.engine.dispose()
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        api_specification = get_api_specification(api.raw_specification_url)
        if api_specification is None:
            return []

        mapped_sections = [{'section': api_specification,
                            'offset': 0,
                            'coverage': 0,
                            _TCs: [],
                            _TSs: [],
                            _SRs: [],
                            _Js: []}]
        unmapped_sections = []

        ret = {'mapped': mapped_sections,
               'unmapped': unmapped_sections}

        dbi.engine.dispose()
        return ret


class ApiJustificationsMapping(Resource):
    fields = ['api-id', 'justification', 'section', 'offset', 'coverage']

    def get(self):
        """
        curl <API_URL>/api/justifications?api-id=<api-id>
        """

        args = get_query_string_args(request.args)
        if not check_fields_in_request(['api-id'], args):
            return 'bad request!', 400

        # undesired_keys = ['section', 'offset']

        dbi = db_orm.DbInterface(get_db())

        # User
        user_id = get_user_id_from_request(args, dbi.session)

        # Find api
        api = get_api_from_request(args, dbi.session)
        if not api:
            dbi.engine.dispose()
            return NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

        # Permissions
        permissions = get_api_user_permissions(api, user_id, dbi.session)
        if 'r' not in permissions:
            dbi.engine.dispose()
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        api_specification = get_api_specification(api.raw_specification_url)
        if api_specification is None:
            return []

        justifications = dbi.session.query(ApiJustificationModel).filter(
            ApiJustificationModel.api_id == api.id).order_by(
            ApiJustificationModel.offset.asc()).all()
        justifications_mapping = [x.as_dict(db_session=dbi.session) for x in justifications]

        mapping = {_A: api.as_dict(),
                   _Js: justifications_mapping}

        for iMapping in range(len(mapping[_Js])):
            current_offset = mapping[_Js][iMapping]['offset']
            current_section = mapping[_Js][iMapping]['section']
            mapping[_Js][iMapping]['match'] = (
                    api_specification[current_offset:current_offset + len(current_section)] == current_section)

        mapped_sections = get_split_sections(api_specification, mapping, [_J])
        unmapped_sections = [x for x in mapping[_Js] if not x['match']]
        ret = {'mapped': mapped_sections,
               'unmapped': unmapped_sections}

        dbi.engine.dispose()
        return ret

    def post(self):
        request_data = request.get_json(force=True)

        if not check_fields_in_request(self.fields, request_data):
            return 'bad request!', 400

        dbi = db_orm.DbInterface(get_db())

        # User
        user = get_active_user_from_request(request_data, dbi.session)
        if not isinstance(user, UserModel):
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        # Find api
        api = get_api_from_request(request_data, dbi.session)
        if not api:
            dbi.engine.dispose()
            return NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

        # Permissions
        permissions = get_api_user_permissions(api, user.id, dbi.session)
        if 'w' not in permissions or user.role not in USER_ROLES_WRITE_PERMISSIONS:
            dbi.engine.dispose()
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        section = request_data['section']
        offset = request_data['offset']
        coverage = request_data['coverage']

        if 'id' not in request_data['justification'].keys():
            description = request_data['justification']['description']
            new_justification = JustificationModel(description,
                                                   user)
            new_justification_mapping_api = ApiJustificationModel(api,
                                                                  new_justification,
                                                                  section,
                                                                  offset,
                                                                  coverage,
                                                                  user)
            dbi.session.add(new_justification)
            dbi.session.add(new_justification_mapping_api)
        else:
            id = request_data['justification']['id']
            if len(dbi.session.query(ApiJustificationModel).filter(ApiJustificationModel.api_id == api.id).filter(
                        ApiJustificationModel.justification_id == id).filter(
                    ApiJustificationModel.section == section).all()) > 0:
                dbi.engine.dispose()
                return "Justification already associated to the selected api Specification section.", 409

            try:
                existing_justification = dbi.session.query(JustificationModel).filter(
                    JustificationModel.id == id).one()
            except NoResultFound:
                return f"Unable to find the Justification id {id}", 400

            new_justification_mapping_api = ApiJustificationModel(api,
                                                                  existing_justification,
                                                                  section,
                                                                  offset,
                                                                  coverage,
                                                                  user)

            dbi.session.add(new_justification_mapping_api)

        dbi.session.commit()  # TO have the id of the new justification mapping

        # Add Notifications
        notification = f'{user.email} added justification {new_justification_mapping_api.justification.id} ' \
                       f'mapped to ' \
                       f'{api.api} as part of the library {api.library}'
        notifications = NotificationModel(api,
                                          NOTIFICATION_CATEGORY_NEW,
                                          f'Justification mapping {new_justification_mapping_api.id} has been added',
                                          notification,
                                          str(user.id),
                                          f'/mapping/{api.id}')
        dbi.session.add(notifications)

        dbi.session.commit()
        dbi.engine.dispose()
        return new_justification_mapping_api.as_dict()

    def put(self):
        request_data = request.get_json(force=True)

        if not check_fields_in_request(self.fields + ["relation-id"], request_data):
            return 'bad request!', 400

        dbi = db_orm.DbInterface(get_db())

        # User
        user = get_active_user_from_request(request_data, dbi.session)
        if not isinstance(user, UserModel):
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        # Find api
        api = get_api_from_request(request_data, dbi.session)
        if not api:
            dbi.engine.dispose()
            return NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

        # Permissions
        permissions = get_api_user_permissions(api, user.id, dbi.session)
        if 'w' not in permissions or user.role not in USER_ROLES_WRITE_PERMISSIONS:
            dbi.engine.dispose()
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        # check if api ...
        try:
            justification_mapping_api = dbi.session.query(ApiJustificationModel).filter(
                ApiJustificationModel.id == request_data["relation-id"]).one()
        except NoResultFound:
            return f"Unable to find the Justification mapping to Api id {request_data['relation-id']}", 400

        justification = justification_mapping_api.justification

        # Update only modified fields
        modified_j = False
        for field in Justification.fields:
            if field.replace('_', '-') in request_data["justification"].keys():
                if getattr(justification, field) != request_data["justification"][field.replace('_', '-')]:
                    modified_j = True
                    setattr(justification, field, request_data["justification"][field.replace('_', '-')])

        if modified_j:
            setattr(justification, 'edited_by_id', user.id)

        modified_ja = False
        if request_data['section'] != justification_mapping_api.section:
            modified_ja = True
            justification_mapping_api.section = request_data["section"]

        if request_data['offset'] != justification_mapping_api.offset:
            modified_ja = True
            justification_mapping_api.offset = request_data["offset"]

        if request_data['coverage'] != justification_mapping_api.coverage:
            modified_ja = True
            justification_mapping_api.coverage = request_data["coverage"]

        if modified_ja:
            justification_mapping_api.edited_by_id = user.id

        if modified_ja or modified_j:
            # Add Notifications
            notification = f'{user.email} modified justification {justification_mapping_api.justification.id} ' \
                           f'mapped to ' \
                           f'{api.api} as part of the library {api.library}'
            notifications = NotificationModel(api,
                                              NOTIFICATION_CATEGORY_EDIT,
                                              f'Justification mapping {justification_mapping_api.id} '
                                              f'has been modified',
                                              notification,
                                              str(user.id),
                                              f'/mapping/{api.id}')
            dbi.session.add(notifications)

        dbi.session.commit()
        dbi.engine.dispose()
        return justification_mapping_api.as_dict()

    def delete(self):
        request_data = request.get_json(force=True)

        if not check_fields_in_request(['relation-id', 'api-id'], request_data):
            return 'bad request!', 400

        dbi = db_orm.DbInterface(get_db())

        # User
        user = get_active_user_from_request(request_data, dbi.session)
        if not isinstance(user, UserModel):
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        # Find api
        api = get_api_from_request(request_data, dbi.session)
        if not api:
            dbi.engine.dispose()
            return NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

        # Permissions
        permissions = get_api_user_permissions(api, user.id, dbi.session)
        if 'w' not in permissions or user.role not in USER_ROLES_WRITE_PERMISSIONS:
            dbi.engine.dispose()
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        # check if api ...
        justification_mapping_api = dbi.session.query(ApiJustificationModel).filter(
            ApiJustificationModel.id == request_data["relation-id"]).all()

        if len(justification_mapping_api) != 1:
            dbi.engine.dispose()
            return 'bad request!', 401

        justification_mapping_api = justification_mapping_api[0]

        if justification_mapping_api.api.id != api.id:
            dbi.engine.dispose()
            return 'bad request!', 401

        notification_j_id = justification_mapping_api.justification.id
        dbi.session.delete(justification_mapping_api)
        dbi.session.commit()

        # Add Notifications
        notification = f'{user.email} deleted justification {notification_j_id} ' \
                       f'mapped to ' \
                       f'{api.api} as part of the library {api.library}'
        notifications = NotificationModel(api,
                                          NOTIFICATION_CATEGORY_DELETE,
                                          'Justification mapping has been deleted',
                                          notification,
                                          str(user.id),
                                          f'/mapping/{api.id}')
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
        dbi.engine.dispose()
        return True


class ApiSwRequirementsMapping(Resource):
    fields = ['api-id', 'sw-requirement', 'section', 'coverage']

    def get(self):
        """
        curl <API_URL>/api/sw-requirements?api-id=<api-id>
        """
        args = get_query_string_args(request.args)
        if not check_fields_in_request(['api-id'], args):
            return 'bad request!', 400

        # undesired_keys = ['section', 'offset']

        dbi = db_orm.DbInterface(get_db())

        # User
        user_id = get_user_id_from_request(args, dbi.session)

        # Find api
        api = get_api_from_request(args, dbi.session)
        if not api:
            dbi.engine.dispose()
            return NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

        # Permissions
        permissions = get_api_user_permissions(api, user_id, dbi.session)
        if 'r' not in permissions:
            dbi.engine.dispose()
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        ret = get_api_sw_requirements_mapping_sections(dbi, api)
        dbi.engine.dispose()
        return ret

    def post(self):
        request_data = request.get_json(force=True)
        notification_sr_title = ''
        if not check_fields_in_request(self.fields, request_data):
            return 'bad request!', 400

        dbi = db_orm.DbInterface(get_db())

        # User
        user = get_active_user_from_request(request_data, dbi.session)
        if not isinstance(user, UserModel):
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        # Find api
        api = get_api_from_request(request_data, dbi.session)
        if not api:
            dbi.engine.dispose()
            return NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

        # Permissions
        permissions = get_api_user_permissions(api, user.id, dbi.session)
        if 'w' not in permissions or user.role not in USER_ROLES_WRITE_PERMISSIONS:
            dbi.engine.dispose()
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        section = request_data['section']
        coverage = request_data['coverage']
        offset = request_data['offset']

        if 'id' not in request_data['sw-requirement'].keys():
            # Create a new one
            # `status` field should be skipped because a default is assigned in the model
            for check_field in [x for x in SwRequirement.fields if x not in ['status']]:
                if check_field.replace("_", "-") not in request_data['sw-requirement'].keys():
                    dbi.engine.dispose()
                    return "Bad request. Not consistent data.", 400

            title = request_data['sw-requirement']['title']
            description = request_data['sw-requirement']['description']

            if len(dbi.session.query(SwRequirementModel).filter(
                        SwRequirementModel.title == title).filter(
                    SwRequirementModel.description == description).all()) > 0:
                dbi.engine.dispose()
                return "SW Requirement already associated to the selected api Specification section.", 409

            new_sw_requirement = SwRequirementModel(title,
                                                    description,
                                                    user)

            new_sw_requirement_mapping_api = ApiSwRequirementModel(api,
                                                                   new_sw_requirement,
                                                                   section,
                                                                   offset,
                                                                   coverage,
                                                                   user)
            notification_sr_title = title
            dbi.session.add(new_sw_requirement)
            dbi.session.add(new_sw_requirement_mapping_api)

        else:
            # Re using existing sw requirement
            id = request_data['sw-requirement']['id']
            if len(dbi.session.query(ApiSwRequirementModel).filter(
                        ApiSwRequirementModel.api_id == api.id).filter(
                    ApiSwRequirementModel.sw_requirement_id == id).filter(
                    ApiSwRequirementModel.section == section).all()) > 0:
                dbi.engine.dispose()
                return "SW Requirement already associated to the selected api Specification section.", 409

            try:
                existing_sw_requirement = dbi.session.query(SwRequirementModel).filter(
                    SwRequirementModel.id == id).one()
                notification_sr_title = existing_sw_requirement.title
            except NoResultFound:
                return f"SW Requirement {id} not found in the database.", 404

            new_sw_requirement_mapping_api = ApiSwRequirementModel(api,
                                                                   existing_sw_requirement,
                                                                   section,
                                                                   offset,
                                                                   coverage,
                                                                   user)
            dbi.session.add(new_sw_requirement_mapping_api)

        dbi.session.commit()  # To have the id of the new added mapping

        # Add Notifications
        notification = f'{user.email} created a new sw requirement ' \
                       f'{notification_sr_title} - coverage: {coverage}'
        notifications = NotificationModel(api,
                                          NOTIFICATION_CATEGORY_NEW,
                                          f'{api.api} - Sw Requirement has been created',
                                          notification,
                                          str(user.id),
                                          f'/mapping/{api.id}?asr={new_sw_requirement_mapping_api.id}&view=details')
        dbi.session.add(notifications)
        dbi.session.commit()

        dbi.engine.dispose()
        return new_sw_requirement_mapping_api.as_dict()

    def put(self):
        request_data = request.get_json(force=True)

        if not check_fields_in_request(self.fields, request_data):
            return 'bad request!', 400

        dbi = db_orm.DbInterface(get_db())

        # User
        user = get_active_user_from_request(request_data, dbi.session)
        if not isinstance(user, UserModel):
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        # Find api
        api = get_api_from_request(request_data, dbi.session)
        if not api:
            dbi.engine.dispose()
            return NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

        # Permissions
        permissions = get_api_user_permissions(api, user.id, dbi.session)
        if 'w' not in permissions or user.role not in USER_ROLES_WRITE_PERMISSIONS:
            dbi.engine.dispose()
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        try:
            sw_requirement_mapping_api = dbi.session.query(ApiSwRequirementModel).filter(
                ApiSwRequirementModel.id == request_data["relation-id"]).one()
        except NoResultFound:
            return f"Unable to find the Sw Requirement mapping to Api id {request_data['relation-id']}", 400

        sw_requirement = sw_requirement_mapping_api.sw_requirement

        # Software Requirement: Update only modified fields
        modified_sr = False
        for field in SwRequirement.fields:
            if field.replace('_', '-') in request_data["sw-requirement"].keys():
                if getattr(sw_requirement, field) != request_data["sw-requirement"][field.replace('_', '-')]:
                    modified_sr = True
                    setattr(sw_requirement, field, request_data["sw-requirement"][field.replace('_', '-')])

        if modified_sr:
            setattr(sw_requirement, 'edited_by_id', user.id)

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
            notification = f'{user.email} modified sw requirement ' \
                           f'{sw_requirement.title}'
            notifications = NotificationModel(api,
                                              NOTIFICATION_CATEGORY_EDIT,
                                              f'{api.api} - Sw Requirement has been modified',
                                              notification,
                                              str(user.id),
                                              f'/mapping/{api.id}?asr={sw_requirement_mapping_api.id}&view=details')
            dbi.session.add(notifications)

        dbi.session.commit()
        dbi.engine.dispose()
        return sw_requirement_mapping_api.as_dict()

    def delete(self):
        request_data = request.get_json(force=True)

        if not check_fields_in_request(['relation-id', 'api-id'], request_data):
            return BAD_REQUEST_MESSAGE, BAD_REQUEST_STATUS

        dbi = db_orm.DbInterface(get_db())

        # User
        user = get_active_user_from_request(request_data, dbi.session)
        if not isinstance(user, UserModel):
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        # Find api
        api = get_api_from_request(request_data, dbi.session)
        if not api:
            dbi.engine.dispose()
            return NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

        # Permissions
        permissions = get_api_user_permissions(api, user.id, dbi.session)
        if 'w' not in permissions or user.role not in USER_ROLES_WRITE_PERMISSIONS:
            dbi.engine.dispose()
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        # check if api ...
        try:
            sw_requirement_mapping_api = dbi.session.query(ApiSwRequirementModel).filter(
                ApiSwRequirementModel.id == request_data["relation-id"]).one()
        except NoResultFound:
            return f"Unable to find the Sw Requirement mapping to Api id {request_data['relation-id']}", 400

        if sw_requirement_mapping_api.api.id != api.id:
            dbi.engine.dispose()
            return BAD_REQUEST_MESSAGE, BAD_REQUEST_STATUS

        notification_sr_id = sw_requirement_mapping_api.sw_requirement.id
        notification_sr_title = sw_requirement_mapping_api.sw_requirement.title
        dbi.session.delete(sw_requirement_mapping_api)
        dbi.session.commit()

        # Add Notifications
        notification = f'{user.email} deleted sw requirement ' \
                       f'{notification_sr_id} {notification_sr_title}'
        notifications = NotificationModel(api,
                                          NOTIFICATION_CATEGORY_DELETE,
                                          f'{api.api} - Sw Requirement has been deleted',
                                          notification,
                                          str(user.id),
                                          f'/mapping/{api.id}')
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
        dbi.engine.dispose()
        return True


class Justification(Resource):
    fields = get_model_editable_fields(JustificationModel, False)
    fields_hashes = [x.replace('_', '-') for x in fields]

    def get(self):
        """
        """
        args = get_query_string_args(request.args)
        dbi = db_orm.DbInterface(get_db())
        query = dbi.session.query(JustificationModel)
        query = filter_query(query, args, JustificationModel, False)
        jus = [ju.as_dict() for ju in query.all()]

        if 'mode' in args.keys():
            if args['mode'] == 'minimal':
                minimal_keys = ['id', 'description']
                jus = [{key: val for key, val in sub.items() if key in minimal_keys} for sub in jus]

        dbi.engine.dispose()
        return jus


class TestSpecification(Resource):
    fields = get_model_editable_fields(TestSpecificationModel, False)
    fields_hashes = [x.replace('_', '-') for x in fields]

    def get(self):
        """
        """
        args = get_query_string_args(request.args)
        dbi = db_orm.DbInterface(get_db())

        query = dbi.session.query(TestSpecificationModel)
        query = filter_query(query, args, TestSpecificationModel, False)
        tss = [ts.as_dict() for ts in query.all()]

        if 'mode' in args.keys():
            if args['mode'] == 'minimal':
                minimal_keys = ['id', 'title']
                tss = [{key: val for key, val in sub.items() if key in minimal_keys} for sub in tss]

        dbi.engine.dispose()
        return tss


class SwRequirement(Resource):
    fields = get_model_editable_fields(SwRequirementModel, False)
    fields_hashes = [x.replace('_', '-') for x in fields]

    def get(self):
        """
        """
        args = get_query_string_args(request.args)
        dbi = db_orm.DbInterface(get_db())

        query = dbi.session.query(SwRequirementModel)
        query = filter_query(query, args, SwRequirementModel, False)
        srs = [sr.as_dict() for sr in query.all()]

        if 'mode' in args.keys():
            if args['mode'] == 'minimal':
                minimal_keys = ['id', 'title']
                srs = [{key: val for key, val in sub.items() if key in minimal_keys} for sub in srs]

        dbi.engine.dispose()
        return srs


class TestCase(Resource):
    fields = get_model_editable_fields(TestCaseModel, False)
    fields_hashes = [x.replace('_', '-') for x in fields]

    def get(self):
        """
        """
        args = get_query_string_args(request.args)
        dbi = db_orm.DbInterface(get_db())
        query = dbi.session.query(TestCaseModel)
        query = filter_query(query, args, TestCaseModel, False)
        tcs = [tc.as_dict() for tc in query.all()]

        if 'mode' in args.keys():
            if args['mode'] == 'minimal':
                minimal_keys = ['id', 'title']
                tcs = [{key: val for key, val in sub.items() if key in minimal_keys} for sub in tcs]

        dbi.engine.dispose()
        return tcs


class SwRequirementSwRequirementsMapping(Resource):
    fields = ['sw-requirement', 'coverage']

    def get(self):
        """
        curl http://localhost:5000/mapping/sw-requirement/sw-requirements?field=id&filter=24
        """

        args = get_query_string_args(request.args)
        dbi = db_orm.DbInterface(get_db())
        query = dbi.session.query(SwRequirementSwRequirementModel)
        query = filter_query(query, args, SwRequirementSwRequirementModel, False)
        srsrs = [srsr.as_dict(db_session=dbi.session) for srsr in query.all()]

        dbi.engine.dispose()
        return srsrs

        ret = {}
        return ret

    def post(self):
        request_data = request.get_json(force=True)
        api_sr = None
        sr_sr = None

        post_mandatory_fields = self.fields + ['relation-id', 'relation-to', 'parent-sw-requirement']
        if not check_fields_in_request(post_mandatory_fields, request_data):
            return 'bad request!', 400

        if 'id' not in request_data['parent-sw-requirement'].keys():
            return 'bad request!!', 400

        relation_id = request_data['relation-id']
        dbi = db_orm.DbInterface(get_db())

        # User
        user = get_active_user_from_request(request_data, dbi.session)
        if not isinstance(user, UserModel):
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        # Find SwRequirementSwRequirement
        if request_data['relation-to'] == 'api':
            relation_to_query = dbi.session.query(ApiSwRequirementModel).filter(
                ApiSwRequirementModel.id == relation_id
            )
            try:
                relation_to_item = relation_to_query.one()
            except NoResultFound:
                dbi.engine.dispose()
                return "Parent mapping not found", 404

            api_id = relation_to_item.api.id
        elif request_data['relation-to'] == 'sw-requirement':
            relation_to_query = dbi.session.query(SwRequirementSwRequirementModel).filter(
                SwRequirementSwRequirementModel.id == relation_id
            )
            try:
                relation_to_item = relation_to_query.one()
            except NoResultFound:
                dbi.engine.dispose()
                return "Parent mapping not found", 404

            api_id = get_parent_api_id(relation_to_item, dbi.session)
            if not api_id:
                dbi.engine.dispose()
                return SW_COMPONENT_NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

        else:
            dbi.engine.dispose()
            return "Bad request!!!", 400

        try:
            api = dbi.session.query(ApiModel).filter(ApiModel.id == api_id).one()
        except NoResultFound:
            dbi.engine.dispose()
            return SW_COMPONENT_NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

        # Permissions
        permissions = get_api_user_permissions(api, user.id, dbi.session)
        if 'w' not in permissions or user.role not in USER_ROLES_WRITE_PERMISSIONS:
            dbi.engine.dispose()
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        if request_data['relation-to'] == 'api':
            api_sr = relation_to_item
        elif request_data['relation-to'] == 'sw-requirement':
            sr_sr = relation_to_item

        parent_sw_requirement_id = request_data['parent-sw-requirement']['id']
        coverage = request_data['coverage']

        try:
            parent_sw_requirement = dbi.session.query(SwRequirementModel).filter(
                SwRequirementModel.id == parent_sw_requirement_id).one()
        except NoResultFound:
            dbi.engine.dispose()
            return "Sw Requirement not found", 400

        del parent_sw_requirement  # Just need to check it exists

        if 'id' not in request_data['sw-requirement'].keys():
            # Create a new one
            # `status` field should be skipped because a default is assigned in the model
            for check_field in [x for x in SwRequirement.fields if x not in ['status']]:
                if check_field.replace("_", "-") not in request_data['sw-requirement'].keys():
                    dbi.engine.dispose()
                    return "Bad request. Not consistent data.", 400

            title = request_data['sw-requirement']['title']
            description = request_data['sw-requirement']['description']

            existing_sw_requirements = dbi.session.query(SwRequirementModel).filter(
                SwRequirementModel.title == title).filter(
                SwRequirementModel.description == description).all()

            for sr in existing_sw_requirements:
                sr_mapping = dbi.session.query(SwRequirementSwRequirementModel).filter(
                    SwRequirementSwRequirementModel.id == relation_id).filter(
                    SwRequirementSwRequirementModel.sw_requirement_id == sr.id).all()
                if len(sr_mapping) > 0:
                    dbi.engine.dispose()
                    return "Sw Requirement already associated to the selected Sw Requirement.", 409

            new_sw_requirement = SwRequirementModel(title,
                                                    description,
                                                    user)

            new_sw_requirement_mapping_sw_requirement = SwRequirementSwRequirementModel(api_sr,
                                                                                        sr_sr,
                                                                                        new_sw_requirement,
                                                                                        coverage,
                                                                                        user)

            dbi.session.add(new_sw_requirement)
            dbi.session.add(new_sw_requirement_mapping_sw_requirement)

        else:
            # Map an existing SwRequirement
            sw_requirement_id = request_data['sw-requirement']['id']

            if len(dbi.session.query(SwRequirementSwRequirementModel).filter(
                    SwRequirementSwRequirementModel.id == relation_id).filter(
                      SwRequirementSwRequirementModel.sw_requirement_id == sw_requirement_id).all()) > 0:
                dbi.engine.dispose()
                return "Sw Requirement already associated to the selected Sw Requirement.", 409

            try:
                sw_requirement = dbi.session.query(SwRequirementModel).filter(
                    SwRequirementModel.id == sw_requirement_id).one()
            except NoResultFound:
                dbi.engine.dispose()
                return "Bad request.", 400

            if not isinstance(sw_requirement, SwRequirementModel):
                dbi.engine.dispose()
                return "Bad request.", 400

            new_sw_requirement_mapping_sw_requirement = SwRequirementSwRequirementModel(api_sr,
                                                                                        sr_sr,
                                                                                        sw_requirement,
                                                                                        coverage,
                                                                                        user)
            dbi.session.add(new_sw_requirement_mapping_sw_requirement)

        dbi.session.commit()

        # Add Notifications
        notification = f'{user.email} added sw requirement ' \
                       f'to {api.api} mapping as part of the library {api.library}'
        notifications = NotificationModel(api,
                                          NOTIFICATION_CATEGORY_NEW,
                                          f'{api.api}, a sw requirement has been created',
                                          notification,
                                          str(user.id),
                                          f'/mapping/{api.id}')
        dbi.session.add(notifications)
        dbi.session.commit()
        dbi.engine.dispose()
        return new_sw_requirement_mapping_sw_requirement.as_dict()

    def put(self):
        request_data = request.get_json(force=True)

        mandatory_fields = self.fields + ['relation-id']
        if not check_fields_in_request(mandatory_fields, request_data):
            return 'bad request!', 400

        dbi = db_orm.DbInterface(get_db())

        # User
        user = get_active_user_from_request(request_data, dbi.session)
        if not isinstance(user, UserModel):
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        try:
            sr_mapping_sr = dbi.session.query(SwRequirementSwRequirementModel).filter(
                SwRequirementSwRequirementModel.id == request_data['relation-id']
            ).one()
        except NoResultFound:
            dbi.engine.dispose()
            return "Sw Requirement mapping not found", 400

        api_id = get_parent_api_id(sr_mapping_sr, dbi.session)
        if not api_id:
            dbi.engine.dispose()
            return SW_COMPONENT_NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

        try:
            api = dbi.session.query(ApiModel).filter(ApiModel.id == api_id).one()
        except NoResultFound:
            dbi.engine.dispose()
            return SW_COMPONENT_NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

        # Permissions
        permissions = get_api_user_permissions(api, user.id, dbi.session)
        if 'w' not in permissions or user.role not in USER_ROLES_WRITE_PERMISSIONS:
            dbi.engine.dispose()
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        sr = sr_mapping_sr.sw_requirement

        # Update only modified fields
        modified_sr = False
        for field in SwRequirement.fields:
            if field.replace('_', '-') in request_data["sw-requirement"].keys():
                if getattr(sr, field) != request_data["sw-requirement"][field.replace('_', '-')]:
                    modified_sr = True
                    setattr(sr, field, request_data["sw-requirement"][field.replace('_', '-')])

        if modified_sr:
            setattr(sr, 'edited_by_id', user.id)

        modified_srsr = False
        if sr_mapping_sr.coverage != int(request_data["coverage"]):
            modified_srsr = True
            sr_mapping_sr.coverage = int(request_data["coverage"])
            sr_mapping_sr.edited_by_id = user.id

        ret = sr_mapping_sr.as_dict(db_session=dbi.session)
        dbi.session.commit()

        if modified_sr or modified_srsr:
            # Add Notifications
            notification = f'{user.email} modified sw requirement ' \
                           f'from {api.api} mapping as part of the library {api.library}'
            notifications = NotificationModel(api,
                                              NOTIFICATION_CATEGORY_EDIT,
                                              f'{api.api}, a sw requirement has been modified',
                                              notification,
                                              str(user.id),
                                              f'/mapping/{api.id}')
            dbi.session.add(notifications)
            dbi.session.commit()
        dbi.engine.dispose()
        return ret

    def delete(self):
        request_data = request.get_json(force=True)

        if not check_fields_in_request(['relation-id'], request_data):
            return 'bad request!', 400

        dbi = db_orm.DbInterface(get_db())

        # User
        user = get_active_user_from_request(request_data, dbi.session)
        if not isinstance(user, UserModel):
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        # check sw_requirement_mapping_sw_requirement ...
        try:
            sr_mapping_sr = dbi.session.query(SwRequirementSwRequirementModel).filter(
                SwRequirementSwRequirementModel.id == request_data['relation-id']).one()
        except NoResultFound:
            return 'bad request!', 401

        api_id = get_parent_api_id(sr_mapping_sr, dbi.session)
        if not api_id:
            dbi.engine.dispose()
            return SW_COMPONENT_NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

        try:
            api = dbi.session.query(ApiModel).filter(ApiModel.id == api_id).one()
        except NoResultFound:
            dbi.engine.dispose()
            return SW_COMPONENT_NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

        # Permissions
        permissions = get_api_user_permissions(api, user.id, dbi.session)
        if 'w' not in permissions or user.role not in USER_ROLES_WRITE_PERMISSIONS:
            dbi.engine.dispose()
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        """
        if sw_requirement_mapping_sw_requirement.sw_requirement_id != sw_requirement.id:
            dbi.engine.dispose()
            return 'bad request!', 401
        """

        notification_sr_id = sr_mapping_sr.sw_requirement.id
        notification_sr_title = sr_mapping_sr.sw_requirement.title
        dbi.session.delete(sr_mapping_sr)
        dbi.session.commit()

        # Add Notifications
        notification = f'{user.email} deleted sw requirement ' \
                       f'{notification_sr_id} {notification_sr_title} mapping as part of the library {api.library}'
        notifications = NotificationModel(api,
                                          NOTIFICATION_CATEGORY_DELETE,
                                          f'{api.api}, a sw requirement has been deleted',
                                          notification,
                                          str(user.id),
                                          f'/mapping/{api.id}')
        dbi.session.add(notifications)
        dbi.session.commit()
        dbi.engine.dispose()
        return True


class SwRequirementTestSpecificationsMapping(Resource):
    fields = ['api-id', 'sw-requirement', 'test-specification', 'coverage']

    def get(self):
        """
        curl http://localhost:5000/api/test-specifications?db=head&field=id&filter=24
        """

        ret = {}
        return ret

    def post(self):
        api_sr = None
        sr_sr = None

        request_data = request.get_json(force=True)
        mandatory_fields = self.fields + ['relation-id', 'relation-to']
        if not check_fields_in_request(mandatory_fields, request_data):
            return 'bad request!', 400

        if 'id' not in request_data['sw-requirement'].keys():
            return 'bad request!!', 400

        relation_id = request_data['relation-id']
        relation_to = request_data['relation-to']

        dbi = db_orm.DbInterface(get_db())

        # User
        user = get_active_user_from_request(request_data, dbi.session)
        if not isinstance(user, UserModel):
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        sw_requirement_id = request_data['sw-requirement']['id']
        coverage = request_data['coverage']

        try:
            sw_requirement = dbi.session.query(SwRequirementModel).filter(
                SwRequirementModel.id == sw_requirement_id).one()
        except NoResultFound:
            dbi.engine.dispose()
            return "Sw Requirement not found", 400

        del sw_requirement  # Just need to check it exists

        if relation_to == 'api':
            relation_to_query = dbi.session.query(ApiSwRequirementModel).filter(
                ApiSwRequirementModel.id == relation_id
            )
            try:
                relation_to_item = relation_to_query.one()
            except NoResultFound:
                dbi.engine.dispose()
                return "Parent mapping not found", 404

            api_id = relation_to_item.api.id
        elif relation_to == 'sw-requirement':
            relation_to_query = dbi.session.query(SwRequirementSwRequirementModel).filter(
                SwRequirementSwRequirementModel.id == relation_id
            )
            try:
                relation_to_item = relation_to_query.one()
            except NoResultFound:
                dbi.engine.dispose()
                return "Parent mapping not found", 404

            api_id = get_parent_api_id(relation_to_item, dbi.session)
            if not api_id:
                dbi.engine.dispose()
                return SW_COMPONENT_NOT_FOUND_MESSAGE, NOT_FOUND_STATUS
        else:
            dbi.engine.dispose()
            return "Bad request!!!", 400

        try:
            api = dbi.session.query(ApiModel).filter(ApiModel.id == api_id).one()
        except NoResultFound:
            dbi.engine.dispose()
            return SW_COMPONENT_NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

        # Permissions
        permissions = get_api_user_permissions(api, user.id, dbi.session)
        if 'w' not in permissions or user.role not in USER_ROLES_WRITE_PERMISSIONS:
            dbi.engine.dispose()
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        if relation_to == 'api':
            api_sr = relation_to_item
        elif relation_to == 'sw-requirement':
            sr_sr = relation_to_item

        if 'id' not in request_data['test-specification'].keys():
            # Create a new one
            # `status` field should be skipped because a default is assigned in the model
            for check_field in [x for x in TestSpecification.fields if x not in ['status']]:
                if check_field.replace("_", "-") not in request_data['test-specification'].keys():
                    dbi.engine.dispose()
                    return "Bad request. Not consistent data.", 400

            title = request_data['test-specification']['title']
            preconditions = request_data['test-specification']['preconditions']
            test_description = request_data['test-specification']['test-description']
            expected_behavior = request_data['test-specification']['expected-behavior']

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
                    dbi.engine.dispose()
                    return "Test Specification already associated to the selected api Specification section.", 409
            """

            new_test_specification = TestSpecificationModel(title,
                                                            preconditions,
                                                            test_description,
                                                            expected_behavior,
                                                            user)

            new_test_specification_mapping_sw_requirement = SwRequirementTestSpecificationModel(api_sr,
                                                                                                sr_sr,
                                                                                                new_test_specification,
                                                                                                coverage,
                                                                                                user)

            dbi.session.add(new_test_specification)
            dbi.session.add(new_test_specification_mapping_sw_requirement)

        else:
            test_specification_id = request_data['test-specification']['id']

            if len(dbi.session.query(SwRequirementTestSpecificationModel).filter(
                        SwRequirementTestSpecificationModel.sw_requirement_mapping_api_id == request_data[
                            'relation-id']).filter(
                    SwRequirementTestSpecificationModel.test_specification_id == test_specification_id).all()) > 0:
                dbi.engine.dispose()
                return "Test Specification already associated to the selected Api and Sw Requirement.", 409

            try:
                test_specification = dbi.session.query(TestSpecificationModel).filter(
                    TestSpecificationModel.id == test_specification_id).one()
            except NoResultFound:
                return "Unable to find the selected Test Specification", 400

            if not isinstance(test_specification, TestSpecificationModel):
                dbi.engine.dispose()
                return "Bad request.", 400

            new_test_specification_mapping_sw_requirement = SwRequirementTestSpecificationModel(api_sr,
                                                                                                sr_sr,
                                                                                                test_specification,
                                                                                                coverage,
                                                                                                user)
            dbi.session.add(new_test_specification_mapping_sw_requirement)

        dbi.session.commit()

        # Add Notifications
        notification = f'{user.email} added test specification ' \
                       f'to {api.api} mapping as part of the library {api.library}'
        notifications = NotificationModel(api,
                                          NOTIFICATION_CATEGORY_NEW,
                                          f'{api.api}, a test specification has been created',
                                          notification,
                                          str(user.id),
                                          f'/mapping/{api.id}')
        dbi.session.add(notifications)
        dbi.session.commit()
        dbi.engine.dispose()
        return new_test_specification_mapping_sw_requirement.as_dict()

    def put(self):

        request_data = request.get_json(force=True)

        mandatory_fields = self.fields + ['relation-id']
        if not check_fields_in_request(mandatory_fields, request_data):
            return 'bad request!', 400

        dbi = db_orm.DbInterface(get_db())

        # User
        user = get_active_user_from_request(request_data, dbi.session)
        if not isinstance(user, UserModel):
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        try:
            sw_mapping_ts = dbi.session.query(SwRequirementTestSpecificationModel).filter(
                SwRequirementTestSpecificationModel.id == request_data['relation-id']
            ).one()
        except NoResultFound:
            return f"Unable to find the Test Specification " \
                   f"mapping to Sw Requirement id {request_data['relation-id']}", 400

        api_id = get_parent_api_id(sw_mapping_ts, dbi.session)
        if not api_id:
            dbi.engine.dispose()
            return SW_COMPONENT_NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

        try:
            api = dbi.session.query(ApiModel).filter(ApiModel.id == api_id).one()
        except NoResultFound:
            dbi.engine.dispose()
            return SW_COMPONENT_NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

        # Permissions
        permissions = get_api_user_permissions(api, user.id, dbi.session)
        if 'w' not in permissions or user.role not in USER_ROLES_WRITE_PERMISSIONS:
            dbi.engine.dispose()
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        test_specification = sw_mapping_ts.test_specification

        # Update only modified fields
        modified_ts = False
        for field in TestSpecification.fields:
            if field.replace('_', '-') in request_data["test-specification"].keys():
                if getattr(test_specification, field) != request_data["test-specification"][field.replace('_', '-')]:
                    modified_ts = True
                    setattr(test_specification, field, request_data["test-specification"][field.replace('_', '-')])

        if modified_ts:
            setattr(test_specification, 'edited_by_id', user.id)

        modified_srts = False
        if sw_mapping_ts.coverage != int(request_data["coverage"]):
            modified_srts = True
            sw_mapping_ts.coverage = int(request_data["coverage"])
            sw_mapping_ts.edited_by_id = user.id

        ret = sw_mapping_ts.as_dict(db_session=dbi.session)
        dbi.session.commit()

        if modified_ts or modified_srts:
            # Add Notifications
            notification = f'{user.email} modified test specification ' \
                           f'from {api.api} mapping as part of the library {api.library}'
            notifications = NotificationModel(api,
                                              NOTIFICATION_CATEGORY_EDIT,
                                              f'{api.api}, a test specification has been modified',
                                              notification,
                                              str(user.id),
                                              f'/mapping/{api.id}')
            dbi.session.add(notifications)
            dbi.session.commit()
        dbi.engine.dispose()
        return ret

    def delete(self):

        ret = False
        request_data = request.get_json(force=True)

        mandatory_fields = ['relation-id']
        if not check_fields_in_request(mandatory_fields, request_data):
            return 'bad request!', 400

        dbi = db_orm.DbInterface(get_db())

        # User
        user = get_active_user_from_request(request_data, dbi.session)
        if not isinstance(user, UserModel):
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        try:
            sw_mapping_ts = dbi.session.query(SwRequirementTestSpecificationModel).filter(
                SwRequirementTestSpecificationModel.id == request_data['relation-id']
            ).one()
        except NoResultFound:
            return f"Unable to find the Test Specification " \
                   f"mapping to Sw Requirement id {request_data['relation-id']}", 400

        api_id = get_parent_api_id(sw_mapping_ts, dbi.session)
        if not api_id:
            dbi.engine.dispose()
            return SW_COMPONENT_NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

        try:
            api = dbi.session.query(ApiModel).filter(ApiModel.id == api_id).one()
        except NoResultFound:
            dbi.engine.dispose()
            return SW_COMPONENT_NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

        # Permissions
        permissions = get_api_user_permissions(api, user.id, dbi.session)
        if 'w' not in permissions or user.role not in USER_ROLES_WRITE_PERMISSIONS:
            dbi.engine.dispose()
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        # test_specification = sw_mapping_ts.test_specification
        # dbi.session.delete(test_specification)

        notification_ts_id = sw_mapping_ts.test_specification.id
        notification_ts_title = sw_mapping_ts.test_specification.title
        dbi.session.delete(sw_mapping_ts)
        dbi.session.commit()

        # Add Notifications
        notification = f'{user.email} deleted test specification ' \
                       f'{notification_ts_id} {notification_ts_title} mapping as part of the library {api.library}'
        notifications = NotificationModel(api,
                                          NOTIFICATION_CATEGORY_DELETE,
                                          f'{api.api}, a test specification has been deleted',
                                          notification,
                                          str(user.id),
                                          f'/mapping/{api.id}')
        dbi.session.add(notifications)
        dbi.session.commit()
        dbi.engine.dispose()

        return ret


class SwRequirementTestCasesMapping(Resource):
    fields = ['api-id', 'sw-requirement', 'test-case', 'coverage']

    def get(self):
        """
        curl http://localhost:5000/api/test-specifications?db=head&field=id&filter=24
        """

        ret = {}
        return ret

    def post(self):
        api_sr = None
        sr_sr = None
        request_data = request.get_json(force=True)

        post_mandatory_fields = self.fields + ['relation-id', 'relation-to']
        if not check_fields_in_request(post_mandatory_fields, request_data):
            return 'bad request!', 400

        if 'id' not in request_data['sw-requirement'].keys():
            return 'bad request!!', 400

        relation_id = request_data['relation-id']
        relation_to = request_data['relation-to']

        dbi = db_orm.DbInterface(get_db())

        # User
        user = get_active_user_from_request(request_data, dbi.session)
        if not isinstance(user, UserModel):
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        # Find ApiSwRequirement
        if relation_to == 'api':
            relation_to_query = dbi.session.query(ApiSwRequirementModel).filter(
                ApiSwRequirementModel.id == relation_id
            )

            try:
                relation_to_item = relation_to_query.one()
            except NoResultFound:
                dbi.engine.dispose()
                return "Parent mapping not found", 404

            api_id = relation_to_item.api.id

        elif relation_to == 'sw-requirement':
            relation_to_query = dbi.session.query(SwRequirementSwRequirementModel).filter(
                SwRequirementSwRequirementModel.id == relation_id
            )
            try:
                relation_to_item = relation_to_query.one()
            except NoResultFound:
                dbi.engine.dispose()
                return "Parent mapping not found", 404

            api_id = get_parent_api_id(relation_to_item, dbi.session)
            if not api_id:
                dbi.engine.dispose()
                return SW_COMPONENT_NOT_FOUND_MESSAGE, NOT_FOUND_STATUS
        else:
            dbi.engine.dispose()
            return "Bad request!!!", 400

        try:
            api = dbi.session.query(ApiModel).filter(ApiModel.id == api_id).one()
        except NoResultFound:
            dbi.engine.dispose()
            return SW_COMPONENT_NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

        # Permissions
        permissions = get_api_user_permissions(api, user.id, dbi.session)
        if 'w' not in permissions or user.role not in USER_ROLES_WRITE_PERMISSIONS:
            dbi.engine.dispose()
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        if relation_to == 'api':
            api_sr = relation_to_item
        elif relation_to == 'sw-requirement':
            sr_sr = relation_to_item

        sw_requirement_id = request_data['sw-requirement']['id']
        coverage = request_data['coverage']

        try:
            sw_requirement = dbi.session.query(SwRequirementModel).filter(
                SwRequirementModel.id == sw_requirement_id).one()
        except NoResultFound:
            dbi.engine.dispose()
            return "Sw Requirement not found", 400

        del sw_requirement  # Just need to check it exists

        if 'id' not in request_data['test-case'].keys():
            # Create a new one
            # `status` field should be skipped because a default is assigned in the model
            for check_field in [x for x in TestCase.fields if x not in ['status']]:
                if check_field.replace("_", "-") not in request_data['test-case'].keys():
                    dbi.engine.dispose()
                    return "Bad request. Not consistent data.", 400

            title = request_data['test-case']['title']
            description = request_data['test-case']['description']
            repository = request_data['test-case']['repository']
            relative_path = request_data['test-case']['relative-path']

            existing_test_cases = dbi.session.query(TestCaseModel).filter(
                TestCaseModel.title == title).filter(
                TestCaseModel.description == description).filter(
                TestCaseModel.repository == repository).filter(
                TestCaseModel.relative_path == relative_path).all()

            for tc in existing_test_cases:
                tc_mapping = dbi.session.query(SwRequirementTestCaseModel).filter(
                    SwRequirementTestCaseModel.id == relation_id).filter(
                    SwRequirementTestCaseModel.test_case_id == tc.id).all()
                if len(tc_mapping) > 0:
                    dbi.engine.dispose()
                    return "Test Case already associated to the selected api Specification section.", 409

            new_test_case = TestCaseModel(repository,
                                          relative_path,
                                          title,
                                          description,
                                          user)

            new_test_case_mapping_sw_requirement = SwRequirementTestCaseModel(api_sr,
                                                                              sr_sr,
                                                                              new_test_case,
                                                                              coverage,
                                                                              user)

            dbi.session.add(new_test_case)
            dbi.session.add(new_test_case_mapping_sw_requirement)

        else:
            # Map an existing Test Case
            test_case_id = request_data['test-case']['id']

            if len(dbi.session.query(SwRequirementTestCaseModel).filter(
                        SwRequirementTestCaseModel.id == relation_id).filter(
                    SwRequirementTestCaseModel.test_case_id == test_case_id).all()) > 0:
                dbi.engine.dispose()
                return "Test Case already associated to the selected Api and Sw Requirement.", 409

            try:
                test_case = dbi.session.query(TestCaseModel).filter(
                    TestCaseModel.id == test_case_id).one()
            except NoResultFound:
                dbi.engine.dispose()
                return "Bad request.", 400

            if not isinstance(test_case, TestCaseModel):
                dbi.engine.dispose()
                return "Bad request.", 400

            new_test_case_mapping_sw_requirement = SwRequirementTestCaseModel(api_sr,
                                                                              sr_sr,
                                                                              test_case,
                                                                              coverage,
                                                                              user)
            dbi.session.add(new_test_case_mapping_sw_requirement)

        dbi.session.commit()

        # Add Notifications
        notification = f'{user.email} added test case ' \
                       f'to {api.api} mapping as part of the library {api.library}'
        notifications = NotificationModel(api,
                                          NOTIFICATION_CATEGORY_NEW,
                                          f'{api.api}, a test case has been created',
                                          notification,
                                          str(user.id),
                                          f'/mapping/{api.id}')
        dbi.session.add(notifications)
        dbi.session.commit()
        dbi.engine.dispose()
        return new_test_case_mapping_sw_requirement.as_dict()

    def put(self):
        request_data = request.get_json(force=True)

        mandatory_fields = self.fields + ['relation-id']
        if not check_fields_in_request(mandatory_fields, request_data):
            return 'bad request!', 400

        dbi = db_orm.DbInterface(get_db())

        # User
        user = get_active_user_from_request(request_data, dbi.session)
        if not isinstance(user, UserModel):
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        try:
            sw_mapping_tc = dbi.session.query(SwRequirementTestCaseModel).filter(
                SwRequirementTestCaseModel.id == request_data['relation-id']
            ).one()
        except NoResultFound:
            return f"Unable to find the Test Case mapping to Sw Requirement id {request_data['relation-id']}", 400

        api_id = get_parent_api_id(sw_mapping_tc, dbi.session)
        if not api_id:
            dbi.engine.dispose()
            return SW_COMPONENT_NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

        try:
            api = dbi.session.query(ApiModel).filter(ApiModel.id == api_id).one()
        except NoResultFound:
            dbi.engine.dispose()
            return SW_COMPONENT_NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

        # Permissions
        permissions = get_api_user_permissions(api, user.id, dbi.session)
        if 'w' not in permissions or user.role not in USER_ROLES_WRITE_PERMISSIONS:
            dbi.engine.dispose()
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        test_case = sw_mapping_tc.test_case

        # Update only modified fields
        modified_tc = False
        for field in TestCase.fields:
            if field.replace('_', '-') in request_data["test-case"].keys():
                if getattr(test_case, field) != request_data["test-case"][field.replace('_', '-')]:
                    modified_tc = True
                    setattr(test_case, field, request_data["test-case"][field.replace('_', '-')])

        if modified_tc:
            setattr(test_case, 'edited_by_id', user.id)

        modified_srtc = False
        if sw_mapping_tc.coverage != int(request_data["coverage"]):
            modified_srtc = True
            sw_mapping_tc.coverage = int(request_data["coverage"])
            sw_mapping_tc.edited_by_id = user.id

        ret = sw_mapping_tc.as_dict(db_session=dbi.session)
        dbi.session.commit()

        if modified_tc or modified_srtc:
            # Add Notifications
            notification = f'{user.email} modified test case ' \
                           f'from {api.api} mapping as part of the library {api.library}'
            notifications = NotificationModel(api,
                                              NOTIFICATION_CATEGORY_EDIT,
                                              f'{api.api}, a test case has been modified',
                                              notification,
                                              str(user.id),
                                              f'/mapping/{api.id}')
            dbi.session.add(notifications)
            dbi.session.commit()

        dbi.engine.dispose()
        return ret

    def delete(self):

        ret = False
        request_data = request.get_json(force=True)

        mandatory_fields = ['relation-id']
        if not check_fields_in_request(mandatory_fields, request_data):
            return 'bad request!', 400

        dbi = db_orm.DbInterface(get_db())

        # User
        user = get_active_user_from_request(request_data, dbi.session)
        if not isinstance(user, UserModel):
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        try:
            sw_mapping_tc = dbi.session.query(SwRequirementTestCaseModel).filter(
                SwRequirementTestCaseModel.id == request_data['relation-id']
            ).one()
        except NoResultFound:
            return f"Unable to find the Test Case mapping to Sw Requirement id {request_data['relation-id']}", 400

        api_id = get_parent_api_id(sw_mapping_tc, dbi.session)
        if not api_id:
            dbi.engine.dispose()
            return SW_COMPONENT_NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

        try:
            api = dbi.session.query(ApiModel).filter(ApiModel.id == api_id).one()
        except NoResultFound:
            dbi.engine.dispose()
            return SW_COMPONENT_NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

        # Permissions
        permissions = get_api_user_permissions(api, user.id, dbi.session)
        if 'w' not in permissions or user.role not in USER_ROLES_WRITE_PERMISSIONS:
            dbi.engine.dispose()
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        # test_case = sw_mapping_tc.test_case
        # dbi.session.delete(test_case)

        notification_tc_id = sw_mapping_tc.test_case.id
        notification_tc_title = sw_mapping_tc.test_case.title
        dbi.session.delete(sw_mapping_tc)
        dbi.session.commit()

        # Add Notifications
        notification = f'{user.email} deleted test case ' \
                       f'{notification_tc_id} {notification_tc_title} mapping as part of the library {api.library}'
        notifications = NotificationModel(api,
                                          NOTIFICATION_CATEGORY_DELETE,
                                          f'{api.api}, a test case has been deleted',
                                          notification,
                                          str(user.id),
                                          f'/mapping/{api.id}')
        dbi.session.add(notifications)
        dbi.session.commit()
        dbi.engine.dispose()

        return ret


class TestSpecificationTestCasesMapping(Resource):
    fields = ['api-id', 'test-specification', 'test-case', 'coverage']

    def get(self):
        return []

    def post(self):
        request_data = request.get_json(force=True)
        api_ts = None
        sr_ts = None

        post_mandatory_fields = self.fields + ['relation-id', 'relation-to']
        if not check_fields_in_request(post_mandatory_fields, request_data):
            return 'bad request!', 400

        if 'id' not in request_data['test-specification'].keys():
            return 'bad request!!', 400

        relation_id = request_data['relation-id']
        dbi = db_orm.DbInterface(get_db())

        # User
        user = get_active_user_from_request(request_data, dbi.session)
        if not isinstance(user, UserModel):
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        # Find ApiSwRequirement
        if request_data['relation-to'] == 'api':
            relation_to_query = dbi.session.query(ApiTestSpecificationModel).filter(
                ApiTestSpecificationModel.id == relation_id
            )
        elif request_data['relation-to'] == 'sw-requirement':
            relation_to_query = dbi.session.query(SwRequirementTestSpecificationModel).filter(
                SwRequirementTestSpecificationModel.id == relation_id
            )
        else:
            dbi.engine.dispose()
            return "Bad request!!!", 400

        try:
            relation_to_item = relation_to_query.one()
        except NoResultFound:
            return "Parent mapping not found", 404

        if request_data['relation-to'] == 'api':
            api_ts = relation_to_item
            api = api_ts.api
            api_id = api.id
        elif request_data['relation-to'] == 'sw-requirement':
            sr_ts = relation_to_item
            api_id = get_parent_api_id(sr_ts, dbi.session)
            if not api_id:
                dbi.engine.dispose()
                return SW_COMPONENT_NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

            try:
                api = dbi.session.query(ApiModel).filter(ApiModel.id == api_id).one()
            except NoResultFound:
                dbi.engine.dispose()
                return SW_COMPONENT_NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

        # Permissions
        permissions = get_api_user_permissions(api, user.id, dbi.session)
        if 'w' not in permissions or user.role not in USER_ROLES_WRITE_PERMISSIONS:
            dbi.engine.dispose()
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        test_specification_id = request_data['test-specification']['id']
        coverage = request_data['coverage']

        try:
            test_specification = dbi.session.query(TestSpecificationModel).filter(
                TestSpecificationModel.id == test_specification_id).one()
        except NoResultFound:
            dbi.engine.dispose()
            return "Test Specification not found", 400

        del test_specification  # Just need to check it exists

        if 'id' not in request_data['test-case'].keys():
            # Create a new one
            # `status` field should be skipped because a default is assigned in the model
            for check_field in [x for x in TestCase.fields if x not in ['status']]:
                if check_field.replace("_", "-") not in request_data['test-case'].keys():
                    dbi.engine.dispose()
                    return "Bad request. Not consistent data.", 400

            title = request_data['test-case']['title']
            description = request_data['test-case']['description']
            repository = request_data['test-case']['repository']
            relative_path = request_data['test-case']['relative-path']

            existing_test_cases = dbi.session.query(TestCaseModel).filter(
                TestCaseModel.title == title).filter(
                TestCaseModel.description == description).filter(
                TestCaseModel.repository == repository).filter(
                TestCaseModel.relative_path == relative_path).all()

            for tc in existing_test_cases:
                tc_mapping = dbi.session.query(TestSpecificationTestCaseModel).filter(
                    TestSpecificationTestCaseModel.id == relation_id).filter(
                    TestSpecificationTestCaseModel.test_case_id == tc.id).all()
                if len(tc_mapping) > 0:
                    dbi.engine.dispose()
                    return "Test Case already associated to the selected api Specification section.", 409

            new_test_case = TestCaseModel(repository,
                                          relative_path,
                                          title,
                                          description,
                                          user)

            new_test_case_mapping_test_specification = TestSpecificationTestCaseModel(api_ts,
                                                                                      sr_ts,
                                                                                      new_test_case,
                                                                                      coverage,
                                                                                      user)

            dbi.session.add(new_test_case)
            dbi.session.add(new_test_case_mapping_test_specification)

        else:
            # Map an existing Test Case
            test_case_id = request_data['test-case']['id']

            if len(dbi.session.query(TestSpecificationTestCaseModel).filter(
                        TestSpecificationTestCaseModel.id == relation_id).filter(
                    TestSpecificationTestCaseModel.test_case_id == test_case_id).all()) > 0:
                dbi.engine.dispose()
                return "Test Case already associated to the selected Api and Test Specification.", 409

            try:
                test_case = dbi.session.query(TestCaseModel).filter(
                    TestCaseModel.id == test_case_id).one()
            except NoResultFound:
                dbi.engine.dispose()
                return "Bad request.", 400

            if not isinstance(test_case, TestCaseModel):
                dbi.engine.dispose()
                return "Bad request.", 400

            new_test_case_mapping_test_specification = TestSpecificationTestCaseModel(api_ts,
                                                                                      sr_ts,
                                                                                      test_case,
                                                                                      coverage,
                                                                                      user)
            dbi.session.add(new_test_case_mapping_test_specification)

        dbi.session.commit()

        # Add Notifications
        notification = f'{user.email} added test case ' \
                       f'to {api.api} mapping as part of the library {api.library}'
        notifications = NotificationModel(api,
                                          NOTIFICATION_CATEGORY_NEW,
                                          f'{api.api}, a test case has been created',
                                          notification,
                                          str(user.id),
                                          f'/mapping/{api.id}')
        dbi.session.add(notifications)
        dbi.session.commit()
        dbi.engine.dispose()
        return new_test_case_mapping_test_specification.as_dict()

    def put(self):
        request_data = request.get_json(force=True)

        mandatory_fields = self.fields + ['relation-id']
        if not check_fields_in_request(mandatory_fields, request_data):
            return 'bad request!', 400

        dbi = db_orm.DbInterface(get_db())

        # User
        user = get_active_user_from_request(request_data, dbi.session)
        if not isinstance(user, UserModel):
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        try:
            ts_mapping_tc = dbi.session.query(TestSpecificationTestCaseModel).filter(
                TestSpecificationTestCaseModel.id == request_data['relation-id']
            ).one()
        except NoResultFound:
            return f"Unable to find the Test Case mapping to Test Specification id {request_data['relation-id']}", 400

        # Api
        if ts_mapping_tc.test_specification_mapping_api_id:
            try:
                api_ts = dbi.session.query(ApiTestSpecificationModel).filter(
                    ApiTestSpecificationModel.id == ts_mapping_tc.test_specification_mapping_api_id
                ).one()
            except NoResultFound:
                return SW_COMPONENT_NOT_FOUND_MESSAGE, NOT_FOUND_STATUS
            api = api_ts.api
        elif ts_mapping_tc.test_specification_mapping_sw_requirement_id:
            try:
                sr_ts = dbi.session.query(SwRequirementTestSpecificationModel).filter(
                    SwRequirementTestSpecificationModel.id ==
                    ts_mapping_tc.test_specification_mapping_sw_requirement_id
                ).one()
            except NoResultFound:
                return SW_COMPONENT_NOT_FOUND_MESSAGE, NOT_FOUND_STATUS
            api_id = get_parent_api_id(sr_ts, dbi.session)
            if not api_id:
                dbi.engine.dispose()
                return SW_COMPONENT_NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

            try:
                api = dbi.session.query(ApiModel).filter(ApiModel.id == api_id).one()
            except NoResultFound:
                dbi.engine.dispose()
                return SW_COMPONENT_NOT_FOUND_MESSAGE, NOT_FOUND_STATUS
        else:
            return SW_COMPONENT_NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

        # Permissions
        permissions = get_api_user_permissions(api, user.id, dbi.session)
        if 'w' not in permissions or user.role not in USER_ROLES_WRITE_PERMISSIONS:
            dbi.engine.dispose()
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        test_case = ts_mapping_tc.test_case

        # Update only modified fields
        modified_tc = False
        for field in TestCase.fields:
            if field.replace('_', '-') in request_data["test-case"].keys():
                if getattr(test_case, field) != request_data["test-case"][field.replace('_', '-')]:
                    modified_tc = True
                    setattr(test_case, field, request_data["test-case"][field.replace('_', '-')])

        if modified_tc:
            setattr(test_case, 'edited_by_id', user.id)

        modified_tstc = False
        if ts_mapping_tc.coverage != int(request_data["coverage"]):
            modified_tstc = True
            ts_mapping_tc.coverage = int(request_data["coverage"])
            ts_mapping_tc.edited_by_id = user.id

        ret = ts_mapping_tc.as_dict(db_session=dbi.session)
        dbi.session.commit()

        if modified_tc or modified_tstc:
            # Add Notifications
            notification = f'{user.email} modified test case ' \
                           f'to {api.api} mapping as part of the library {api.library}'
            notifications = NotificationModel(api,
                                              NOTIFICATION_CATEGORY_EDIT,
                                              f'{api.api}, a test case has been modified',
                                              notification,
                                              str(user.id),
                                              f'/mapping/{api.id}')
            dbi.session.add(notifications)
            dbi.session.commit()
        dbi.engine.dispose()
        return ret

    def delete(self):
        ret = False
        request_data = request.get_json(force=True)

        mandatory_fields = ['relation-id']
        if not check_fields_in_request(mandatory_fields, request_data):
            return 'bad request!', 400

        dbi = db_orm.DbInterface(get_db())

        # User
        user = get_active_user_from_request(request_data, dbi.session)
        if not isinstance(user, UserModel):
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        try:
            ts_mapping_tc = dbi.session.query(TestSpecificationTestCaseModel).filter(
                TestSpecificationTestCaseModel.id == request_data['relation-id']
            ).one()
        except NoResultFound:
            return f"Unable to find the Test Case mapping to Test Specification id {request_data['relation-id']}", 400

        # Api
        if ts_mapping_tc.test_specification_mapping_api_id:
            try:
                api_ts = dbi.session.query(ApiTestSpecificationModel).filter(
                    ApiTestSpecificationModel.id == ts_mapping_tc.test_specification_mapping_api_id
                ).one()
            except NoResultFound:
                return SW_COMPONENT_NOT_FOUND_MESSAGE, NOT_FOUND_STATUS
            api = api_ts.api
        elif ts_mapping_tc.test_specification_mapping_sw_requirement_id:
            try:
                sr_ts = dbi.session.query(SwRequirementTestSpecificationModel).filter(
                    SwRequirementTestSpecificationModel.id ==
                    ts_mapping_tc.test_specification_mapping_sw_requirement_id
                ).one()
            except NoResultFound:
                return SW_COMPONENT_NOT_FOUND_MESSAGE, NOT_FOUND_STATUS
            api_id = get_parent_api_id(sr_ts, dbi.session)
            if not api_id:
                dbi.engine.dispose()
                return SW_COMPONENT_NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

            try:
                api = dbi.session.query(ApiModel).filter(ApiModel.id == api_id).one()
            except NoResultFound:
                dbi.engine.dispose()
                return SW_COMPONENT_NOT_FOUND_MESSAGE, NOT_FOUND_STATUS
        else:
            return SW_COMPONENT_NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

        # Permissions
        permissions = get_api_user_permissions(api, user.id, dbi.session)
        if 'w' not in permissions or user.role not in USER_ROLES_WRITE_PERMISSIONS:
            dbi.engine.dispose()
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        # test_case = ts_mapping_tc.test_case
        # dbi.session.delete(test_case)

        notification_tc_id = ts_mapping_tc.test_case.id
        notification_tc_title = ts_mapping_tc.test_case.title
        dbi.session.delete(ts_mapping_tc)
        dbi.session.commit()

        # Add Notifications
        notification = f'{user.email} deleted test case ' \
                       f'{notification_tc_id} {notification_tc_title} mapping as part of the library {api.library}'
        notifications = NotificationModel(api,
                                          NOTIFICATION_CATEGORY_DELETE,
                                          f'{api.api}, a test case has been deleted',
                                          notification,
                                          str(user.id),
                                          f'/mapping/{api.id}')
        dbi.session.add(notifications)
        dbi.session.commit()
        dbi.engine.dispose()
        return ret


class ForkApiSwRequirement(Resource):
    def post(self):
        request_data = request.get_json(force=True)

        mandatory_fields = ['relation-id']
        if not check_fields_in_request(mandatory_fields, request_data):
            return 'bad request!', 400

        dbi = db_orm.DbInterface(get_db())

        # User
        user = get_active_user_from_request(request_data, dbi.session)
        if not isinstance(user, UserModel):
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        try:
            asr_mapping = dbi.session.query(ApiSwRequirementModel).filter(
                ApiSwRequirementModel.id == request_data['relation-id']
            ).one()
        except NoResultFound:
            return f"Unable to find the Sw Requirement mapping to Api id {request_data['relation-id']}", 400

        # Permissions
        permissions = get_api_user_permissions(asr_mapping.api, user.id, dbi.session)
        if 'w' not in permissions or user.role not in USER_ROLES_WRITE_PERMISSIONS:
            dbi.engine.dispose()
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        new_sr = SwRequirementModel(asr_mapping.sw_requirement.title,
                                    asr_mapping.sw_requirement.description,
                                    user)
        dbi.session.add(new_sr)
        dbi.session.commit()

        asr_mapping.sw_requirement_id = new_sr.id

        dbi.session.commit()
        dbi.engine.dispose()
        return asr_mapping.as_dict()


class ForkSwRequirementSwRequirement(Resource):
    def post(self):
        request_data = request.get_json(force=True)

        mandatory_fields = ['relation-id']
        if not check_fields_in_request(mandatory_fields, request_data):
            return 'bad request!', 400

        dbi = db_orm.DbInterface(get_db())

        # User
        user = get_active_user_from_request(request_data, dbi.session)
        if not isinstance(user, UserModel):
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        try:
            sr_sr_mapping = dbi.session.query(SwRequirementSwRequirementModel).filter(
                SwRequirementSwRequirementModel.id == request_data['relation-id']
            ).one()
        except NoResultFound:
            return f"Unable to find the Sw Requirement mapping to Sw Requirement id {request_data['relation-id']}", 400

        # Permissions
        api_id = get_parent_api_id(sr_sr_mapping, dbi.session)
        if not api_id:
            dbi.engine.dispose()
            return SW_COMPONENT_NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

        try:
            api = dbi.session.query(ApiModel).filter(ApiModel.id == api_id).one()
        except NoResultFound:
            dbi.engine.dispose()
            return SW_COMPONENT_NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

        permissions = get_api_user_permissions(api, user.id, dbi.session)
        if 'w' not in permissions or user.role not in USER_ROLES_WRITE_PERMISSIONS:
            dbi.engine.dispose()
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        new_sr = SwRequirementModel(sr_sr_mapping.sw_requirement.title,
                                    sr_sr_mapping.sw_requirement.description,
                                    user)
        dbi.session.add(new_sr)
        dbi.session.commit()

        sr_sr_mapping.sw_requirement_id = new_sr.id

        dbi.session.commit()
        dbi.engine.dispose()
        return sr_sr_mapping.as_dict()


class TestingSupportInitDb(Resource):

    def get(self):
        if app.config['TESTING']:
            app.config['DB'] = 'test.db'
            import db.models.init_db as init_db
            init_db.initialization(db_name='test.db')
        return True


class UserLogin(Resource):
    def post(self):
        DATE_FORMAT = "%m/%d/%Y, %H:%M:%S"
        mandatory_fields = ['email', 'password']
        request_data = request.get_json(force=True)
        if not check_fields_in_request(mandatory_fields, request_data):
            return 'bad request!', 400

        cache_key = f"{request_data['email']}|{request.remote_addr}"

        if cache_key in login_attempt_cache.keys():
            if login_attempt_cache[cache_key]["attempts"] >= MAX_LOGIN_ATTEMPTS:
                # check last attempt date
                last_attempt_str = login_attempt_cache[cache_key]['last_attempt_dt']
                last_attempt_dt = datetime.datetime.strptime(last_attempt_str, DATE_FORMAT)
                delta_sec = (datetime.datetime.now() - last_attempt_dt).total_seconds()
                if delta_sec <= MAX_LOGIN_ATTEMPTS_TIMEOUT:
                    return f"Too many attempts for user {request_data['email']}. Retry in 15 minutes.", 400
                else:
                    login_attempt_cache[cache_key]["attempts"] = 1

        try:
            str_encoded_password = base64.b64encode(request_data['password'].encode('utf-8')).decode('utf-8')
            dbi = db_orm.DbInterface(get_db())
            user = dbi.session.query(UserModel).filter(
                    UserModel.email == request_data['email']).one()
            if not user.enabled:
                return "This user has been disabled, please contact your BASIL admin.", 400
            if user.pwd != str_encoded_password:
                if cache_key in login_attempt_cache.keys():
                    login_attempt_cache[cache_key]['attempts'] = \
                        login_attempt_cache[cache_key]['attempts'] + 1
                else:
                    login_attempt_cache[cache_key] = {'attempts': 1}

                login_attempt_cache[cache_key]['last_attempt_dt'] = \
                    datetime.datetime.now().strftime(DATE_FORMAT)

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
        dbi.engine.dispose()

        return {"id": user.id,
                "role": user.role,
                "email": user.email,
                "token": user.token}


class UserSignin(Resource):
    def post(self):
        mandatory_fields = ['email', 'password']
        request_data = request.get_json(force=True)
        if not check_fields_in_request(mandatory_fields, request_data):
            return 'bad request!', 400

        dbi = db_orm.DbInterface(get_db())

        same_email = dbi.session.query(UserModel).filter(
                     UserModel.email == request_data['email']).all()
        if len(same_email) > 0:
            return "Email already in use.", 400

        user = UserModel(request_data['email'].strip(),
                         request_data['password'],
                         "GUEST")
        dbi.session.add(user)
        dbi.session.commit()  # To have the user id

        # Add Notifications
        notification = f'{user.email} joined us on BASIL!'
        notifications = NotificationModel(None,
                                          NOTIFICATION_CATEGORY_NEW,
                                          'New user!',
                                          notification,
                                          str(user.id),
                                          '')
        dbi.session.add(notifications)
        dbi.session.commit()
        dbi.engine.dispose()

        return {"id": user.id,
                "email": user.email,
                "token": user.token}


class UserPermissionsApi(Resource):
    def get(self):
        # Requester identified by id and token
        # Email is related to the user for who I need to know api permissions
        mandatory_fields = ['api-id', 'email', 'token', 'user-id']
        request_data = request.args

        if not check_fields_in_request(mandatory_fields, request_data):
            return BAD_REQUEST_MESSAGE, BAD_REQUEST_STATUS

        dbi = db_orm.DbInterface(get_db())

        user = get_active_user_from_request(request_data, dbi.session)
        if not user:
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        # api
        try:
            api = dbi.session.query(ApiModel).filter(
                ApiModel.id == request_data["api-id"]
            ).one()
        except NoResultFound:
            return "Software component not found.", 402

        # check requester user api permission
        user_permissions = get_api_user_permissions(api, user.id, dbi.session)
        if 'm' not in user_permissions or user.role not in USER_ROLES_MANAGE_PERMISSIONS:
            return f"Operation not allowed for user {user.email}", 405

        try:
            target_user = dbi.session.query(UserModel).filter(
                UserModel.email == request_data["email"]
            ).one()
        except NoResultFound:
            return f"User {request_data['email']} not found.", 403

        target_user_permissions = get_api_user_permissions(api, target_user.id, dbi.session)
        dbi.engine.dispose()
        return {"email": request_data["email"],
                "api": request_data["api-id"],
                "role": target_user.role,
                "permissions": target_user_permissions}

    def put(self):
        # Requester identified by id and token
        # Email is related to the user for who I need to know api permissions
        mandatory_fields = ['api-id', 'email', 'token', 'user-id']
        request_data = request.get_json(force=True)

        if not check_fields_in_request(mandatory_fields, request_data):
            return 'bad request!', 400

        dbi = db_orm.DbInterface(get_db())

        user = get_active_user_from_request(request_data, dbi.session)
        if not isinstance(user, UserModel):
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        # api
        try:
            api = dbi.session.query(ApiModel).filter(
                ApiModel.id == request_data["api-id"]
            ).one()
        except NoResultFound:
            return "Software component not found.", 402

        # check requester user api permission
        user_permissions = get_api_user_permissions(api, user.id, dbi.session)
        if 'm' not in user_permissions or user.role not in USER_ROLES_MANAGE_PERMISSIONS:
            return f"Operation not allowed for user {user.email}", 405

        try:
            target_user = dbi.session.query(UserModel).filter(
                UserModel.email == request_data["email"]
            ).one()
        except NoResultFound:
            return f"User {request_data['email']} not found.", 403

        permission_string = f"[{target_user.id}]"

        # Edit Permission
        if 'e' in request_data['permissions']:
            if permission_string not in api.edit_permissions:
                api.edit_permissions += permission_string
        else:
            if permission_string in api.edit_permissions:
                api.edit_permissions = api.edit_permissions.replace(permission_string, "")

        # Manage Permission
        if 'm' in request_data['permissions']:
            if permission_string not in api.manage_permissions:
                api.manage_permissions += permission_string
        else:
            if permission_string in api.manage_permissions:
                api.manage_permissions = api.manage_permissions.replace(permission_string, "")

        # Read Permission
        if 'r' in request_data['permissions']:
            if permission_string in api.read_denials:
                api.read_denials = api.read_denials.replace(permission_string, "")
                if api.read_denials == '[0]':
                    api.read_denials = ''
        else:
            if permission_string not in api.read_denials:
                api.read_denials += permission_string
                if '[0]' not in api.read_denials:
                    api.read_denials += '[0]'

        # Write Permission
        if 'w' in request_data['permissions']:
            if permission_string not in api.write_permissions:
                api.write_permissions += permission_string
        else:
            if permission_string in api.write_permissions:
                api.write_permissions = api.write_permissions.replace(permission_string, "")

        target_user_permissions = get_api_user_permissions(api, target_user.id, dbi.session)

        dbi.session.add(api)
        dbi.session.commit()
        dbi.engine.dispose()

        return {"email": request_data["email"],
                "api": request_data["api-id"],
                "permissions": target_user_permissions}


class UserEnable(Resource):

    def put(self):
        # Requester identified by id and token
        # Email is related to the user for who I need to change the status
        mandatory_fields = ['email', 'token', 'user-id', 'enabled']
        request_data = request.get_json(force=True)

        if not check_fields_in_request(mandatory_fields, request_data):
            return 'bad request!', 400

        dbi = db_orm.DbInterface(get_db())

        user = get_active_user_from_request(request_data, dbi.session)
        if not isinstance(user, UserModel):
            dbi.engine.dispose()
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        if user.role not in USER_ROLES_MANAGE_USERS:
            dbi.engine.dispose()
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        try:
            target_user = dbi.session.query(UserModel).filter(
                UserModel.email == request_data["email"]
            ).one()
        except NoResultFound:
            dbi.engine.dispose()
            return f"User {request_data['email']} not found.", 403

        target_user.enabled = int(request_data['enabled'])

        dbi.session.add(target_user)
        dbi.session.commit()
        dbi.engine.dispose()

        return {"email": request_data["email"],
                "enabled": target_user.enabled}


class User(Resource):

    def get(self):
        # Requester identified by id and token
        mandatory_fields = ['user-id', 'token']
        request_data = request.args

        if not check_fields_in_request(mandatory_fields, request_data):
            return 'bad request!', 400

        dbi = db_orm.DbInterface(get_db())

        user = get_active_user_from_request(request_data, dbi.session)
        if not isinstance(user, UserModel):
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        if user.role != 'ADMIN':
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        users = dbi.session.query(UserModel).filter(
            UserModel.id != request_data['user-id']
        ).all()
        # users = [{k: v for k, v in user.as_dict().items() if k not in ['pwd']} for user in users]

        dbi.engine.dispose()

        return [x.as_dict(full_data=True) for x in users]


class UserResetPassword(Resource):

    def put(self):
        # Requester identified by id and token
        # Email is related to the user for who I need to change the status
        mandatory_fields = ['email', 'token', 'user-id', 'password']
        request_data = request.get_json(force=True)

        if not check_fields_in_request(mandatory_fields, request_data):
            return BAD_REQUEST_MESSAGE, BAD_REQUEST_STATUS

        dbi = db_orm.DbInterface(get_db())

        user = get_active_user_from_request(request_data, dbi.session)
        if not isinstance(user, UserModel):
            dbi.engine.dispose()
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        if user.role not in USER_ROLES_MANAGE_USERS:
            dbi.engine.dispose()
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        try:
            target_user = dbi.session.query(UserModel).filter(
                UserModel.email == request_data["email"]
            ).one()
        except NoResultFound:
            dbi.engine.dispose()
            return f"User {request_data['email']} not found.", 403

        target_user.pwd = request_data['password']
        dbi.session.commit()
        dbi.engine.dispose()

        return {"email": request_data["email"]}


class UserRole(Resource):

    def put(self):
        # Requester identified by id and token
        # Email is related to the user for who I need to change the role
        mandatory_fields = ['email', 'token', 'user-id', 'role']
        request_data = request.get_json(force=True)

        if not check_fields_in_request(mandatory_fields, request_data):
            return BAD_REQUEST_MESSAGE, BAD_REQUEST_STATUS

        if not request_data['role'] in ['ADMIN', 'GUEST', 'USER']:
            return BAD_REQUEST_MESSAGE, BAD_REQUEST_STATUS

        dbi = db_orm.DbInterface(get_db())

        user = get_active_user_from_request(request_data, dbi.session)
        if not isinstance(user, UserModel):
            dbi.engine.dispose()
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        if user.role not in USER_ROLES_MANAGE_USERS:
            dbi.engine.dispose()
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        try:
            target_user = dbi.session.query(UserModel).filter(
                UserModel.email == request_data["email"]
            ).one()
        except NoResultFound:
            dbi.engine.dispose()
            return f"User {request_data['email']} not found.", 403

        target_user.role = request_data['role']
        dbi.session.commit()
        dbi.engine.dispose()

        return {"email": request_data["email"]}


class UserNotifications(Resource):

    def delete(self):
        mandatory_fields = ['token', 'user-id']
        request_data = request.get_json(force=True)
        if not check_fields_in_request(mandatory_fields, request_data):
            return BAD_REQUEST_MESSAGE, BAD_REQUEST_STATUS

        dbi = db_orm.DbInterface(get_db())

        user = get_active_user_from_request(request_data, dbi.session)
        if not isinstance(user, UserModel):
            dbi.engine.dispose()
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        # It should be possible to delete 1 notification filtering with `id`
        # It should be possible to clear all the notifications if `id` is not defined
        if 'id' in request_data.keys():
            try:
                notifications = dbi.session.query(NotificationModel).filter(
                    NotificationModel.id == request_data['id']
                ).all()
            except NoResultFound:
                return NOT_FOUND_MESSAGE, NOT_FOUND_STATUS
        else:

            user_api_notifications = user.api_notifications.replace(' ', '').split(',')
            user_api_notifications = [int(x) for x in user_api_notifications]  # Need list of int

            NoneVar = None  # To avoid flake8 warning comparing with None with `==` instead of `is`
            notifications = dbi.session.query(NotificationModel).filter(or_(
                NotificationModel.api_id.in_(user_api_notifications),
                NotificationModel.api_id == NoneVar)
            ).order_by(
                NotificationModel.created_at.desc()
            ).all()

        for i in range(len(notifications)):
            read_by = notifications[i].read_by.split(',')
            if user.id not in read_by:
                read_by.append(user.id)
            notifications[i].read_by = ",".join([str(x) for x in read_by])

        dbi.session.commit()
        dbi.engine.dispose()
        return "Notification updated"

    def get(self):
        undesired_keys = ['ready_by']
        request_data = request.args

        dbi = db_orm.DbInterface(get_db())

        user = get_active_user_from_request(request_data, dbi.session)
        if not isinstance(user, UserModel):
            dbi.engine.dispose()
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        user_api_notifications = []
        if user.api_notifications:
            user_api_notifications = user.api_notifications.replace(' ', '').split(',')
            user_api_notifications = [int(x) for x in user_api_notifications]  # Need list of int

        NoneVar = None  # To avoid flake8 warning comparing with None with `==` instead of `is`
        notifications = dbi.session.query(NotificationModel).filter(or_(
            NotificationModel.api_id.in_(user_api_notifications),
            NotificationModel.api_id == NoneVar)
        ).order_by(
            NotificationModel.created_at.desc()
        ).all()

        tmp = [x.as_dict() for x in notifications]
        tmp = [get_dict_without_keys(x,
                                     undesired_keys) for x in tmp if str(user.id) not in x['read_by']]
        return tmp

    def put(self):
        mandatory_fields = ['api-id', 'notifications', 'token', 'user-id']
        request_data = request.get_json(force=True)
        if not check_fields_in_request(mandatory_fields, request_data):
            return BAD_REQUEST_MESSAGE, BAD_REQUEST_STATUS

        dbi = db_orm.DbInterface(get_db())

        user = get_active_user_from_request(request_data, dbi.session)
        if not isinstance(user, UserModel):
            dbi.engine.dispose()
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        if not user.api_notifications:
            user_api_notifications = []
        else:
            user_api_notifications = user.api_notifications.replace(' ', '').split(',')
            user_api_notifications = [int(x) for x in user_api_notifications]  # Need list of int

        api_id = int(request_data['api-id'])
        if request_data['notifications'] == 0:
            if api_id in user_api_notifications:
                user_api_notifications.remove(api_id)
        elif request_data['notifications'] == 1:
            if api_id not in user_api_notifications:
                user_api_notifications.append(api_id)

        user.api_notifications = "".join([str(x) for x in user_api_notifications])
        dbi.session.add(user)
        dbi.session.commit()
        dbi.engine.dispose()
        return "Notification updated"


class Testing(Resource):
    def get(self):
        request_data = request.args
        dbi = db_orm.DbInterface(get_db())
        if 'mapped_to_id' not in request_data.keys():
            return "wrong input", 400

        """
        mapping = dbi.session.query(SwRequirementSwRequirementModel).filter(
            SwRequirementSwRequirementModel.id == request_data['mapped_to_id']
        ).one()
        """

        mapping = dbi.session.query(SwRequirementTestCaseModel).filter(
            SwRequirementTestCaseModel.id == request_data['mapped_to_id']
        ).one()

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

        ssh_keys = dbi.session.query(SshKeyModel).filter(
            SshKeyModel.created_by_id == user_id).order_by(
            SshKeyModel.created_at.desc()).all()
        ssh_keys = [x.as_dict(full_data=True) for x in ssh_keys]
        return ssh_keys

    def post(self):
        request_data = request.get_json(force=True)

        if not check_fields_in_request(self.fields, request_data):
            return 'bad request!', 400

        dbi = db_orm.DbInterface(get_db())

        # User
        user = get_active_user_from_request(request_data, dbi.session)
        if not isinstance(user, UserModel):
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        title = request_data['title'].strip()
        ssh_key = request_data['ssh_key'].strip()
        if title == '' or ssh_key == '':
            return BAD_REQUEST_MESSAGE, BAD_REQUEST_STATUS

        existing = dbi.session.query(SshKeyModel).filter(
            SshKeyModel.title == title,
            SshKeyModel.created_by_id == user.id
        ).all()

        if len(existing):
            return CONFLICT_MESSAGE, CONFLICT_STATUS

        new_ssh_key = SshKeyModel(title, ssh_key, user)
        dbi.session.add(new_ssh_key)
        dbi.session.commit()

        # File creation and permissions set
        if not os.path.exists(SSH_KEYS_PATH):
            os.mkdir(SSH_KEYS_PATH)

        f = open(f'{SSH_KEYS_PATH}/{new_ssh_key.id}', 'w')
        f.write(f'{new_ssh_key.ssh_key.strip()}\n')
        f.close()

        os.chmod(f'{SSH_KEYS_PATH}/{new_ssh_key.id}', 0o600)

        if not os.path.exists(f'{SSH_KEYS_PATH}/{new_ssh_key.id}'):
            dbi.session.delete(new_ssh_key)
            dbi.session.commit()
            return "Error", 400

        dbi.engine.dispose()

        return new_ssh_key.as_dict()

    def delete(self):
        request_data = request.get_json(force=True)

        if not check_fields_in_request(['id'], request_data):
            return 'bad request!', 400

        dbi = db_orm.DbInterface(get_db())

        # User
        user = get_active_user_from_request(request_data, dbi.session)
        if not isinstance(user, UserModel):
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        try:
            ssh_key = dbi.session.query(SshKeyModel).filter(
                SshKeyModel.id == request_data['id']
            ).one()
        except NoResultFound:
            return NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

        if ssh_key.created_by.id != user.id:
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        dbi.session.delete(ssh_key)
        dbi.session.commit()

        if os.path.exists(f'{SSH_KEYS_PATH}/{ssh_key.id}'):
            os.remove(f'{SSH_KEYS_PATH}/{ssh_key.id}')

        dbi.engine.dispose()
        return True


class TestRunConfig(Resource):
    # Do not support delete, put and post
    # Once a Test Run has been executed the Test Run Config is defined
    # and should be accessible in future to identify the Test Run
    # A new Test Config is creeated by the Test Run post endpoint

    fields = get_model_editable_fields(TestRunConfigModel, False)

    def get(self):

        args = get_query_string_args(request.args)
        dbi = db_orm.DbInterface(get_db())

        # User
        user_id = get_user_id_from_request(args, dbi.session)
        if user_id == 0:
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        query = dbi.session.query(TestRunConfigModel).filter(
            TestRunConfigModel.created_by_id == user_id)

        if 'search' in args.keys():
            query = query.filter(or_(
                TestRunConfigModel.title.like(f'%{args["search"]}%'),
                TestRunConfigModel.provision_guest.like(f'%{args["search"]}%'),
                TestRunConfigModel.provision_guest_port.like(f'%{args["search"]}%'),
                TestRunConfigModel.environment_vars.like(f'%{args["search"]}%'),
                TestRunConfigModel.context_vars.like(f'%{args["search"]}%')
            ))

        configs = query.order_by(
            TestRunConfigModel.created_at.desc()).all()

        configs = [x.as_dict(full_data=True) for x in configs]
        return configs


class TestRun(Resource):
    fields = get_model_editable_fields(TestRunModel, False)

    def get(self):
        mandatory_fields = ['api-id', 'mapped_to_type', 'mapped_to_id']
        args = get_query_string_args(request.args)
        if not check_fields_in_request(mandatory_fields, args):
            return BAD_REQUEST_MESSAGE, BAD_REQUEST_STATUS

        dbi = db_orm.DbInterface(get_db())

        # User
        user = get_active_user_from_request(args, dbi.session)
        if isinstance(user, UserModel):
            user_id = user.id
        else:
            user_id = 0

        # Find api
        api = get_api_from_request(args, dbi.session)
        if not api:
            dbi.engine.dispose()
            return NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

        # Permissions
        permissions = get_api_user_permissions(api, user_id, dbi.session)
        if 'r' not in permissions:
            dbi.engine.dispose()
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        runs_query = dbi.session.query(TestRunModel).join(
            TestRunConfigModel).filter(
            TestRunModel.api_id == api.id,
            TestRunModel.mapping_to == args['mapped_to_type'],
            TestRunModel.mapping_id == args['mapped_to_id'],
        )

        if 'search' in args.keys():
            search = args['search']
            runs_query = runs_query.filter(or_(
                TestRunModel.id.like(f'%{search}%'),
                TestRunModel.uid.like(f'%{search}%'),
                TestRunModel.title.like(f'%{search}%'),
                TestRunModel.note.like(f'%{search}%'),
                TestRunModel.bugs.like(f'%{search}%'),
                TestRunModel.result.like(f'%{search}%'),
                TestRunModel.created_at.like(f'%{search}%'),
                TestRunConfigModel.title.like(f'%{search}%'),
                TestRunConfigModel.provision_type.like(f'%{search}%'),
                TestRunConfigModel.git_repo_ref.like(f'%{search}%'),
                TestRunConfigModel.context_vars.like(f'%{search}%'),
                TestRunConfigModel.environment_vars.like(f'%{search}%'),
                TestRunConfigModel.provision_guest.like(f'%{search}%'),
                TestRunConfigModel.provision_guest_port.like(f'%{search}%'),
            ))

        runs = runs_query.order_by(
            TestRunModel.created_at.desc()).all()

        runs = [x.as_dict(full_data=True) for x in runs]
        return runs

    def post(self):
        request_data = request.get_json(force=True)
        mandatory_fields = ['api-id', 'title', 'note', 'test-run-config', 'mapped_to_type', 'mapped_to_id']
        if not check_fields_in_request(mandatory_fields, request_data):
            return BAD_REQUEST_MESSAGE, BAD_REQUEST_STATUS

        config_mandatory_fields = ['context_vars', 'environment_vars',
                                   'from_db', 'id',
                                   'title', 'git_repo_ref', 'ssh_key',
                                   'provision_type', 'provision_guest', 'provision_guest_port']
        if not check_fields_in_request(config_mandatory_fields, request_data['test-run-config']):
            return BAD_REQUEST_MESSAGE, BAD_REQUEST_STATUS

        dbi = db_orm.DbInterface(get_db())

        # User
        user = get_active_user_from_request(request_data, dbi.session)
        if not isinstance(user, UserModel):
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        # Find api
        api = get_api_from_request(request_data, dbi.session)
        if not api:
            dbi.engine.dispose()
            return NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

        # Config
        test_run_config_id = str(request_data['test-run-config']['id']).strip()
        config_title = str(request_data['test-run-config']['title']).strip()
        git_repo_ref = str(request_data['test-run-config']['git_repo_ref']).strip()
        context_vars = str(request_data['test-run-config']['context_vars']).strip()
        environment_vars = str(request_data['test-run-config']['environment_vars']).strip()
        provision_type = str(request_data['test-run-config']['provision_type']).strip()
        provision_guest = str(request_data['test-run-config']['provision_guest']).strip()
        provision_guest_port = str(request_data['test-run-config']['provision_guest_port']).strip()
        ssh_key_id = request_data['test-run-config']['ssh_key']

        if test_run_config_id == '0':
            # Check mandatory fields
            if config_title == '' or provision_type == '':
                return BAD_REQUEST_MESSAGE, BAD_REQUEST_STATUS

            if provision_type == 'connect':
                if provision_guest == '' or provision_guest_port == '' or ssh_key_id == '' or ssh_key_id == '0':
                    return BAD_REQUEST_MESSAGE, BAD_REQUEST_STATUS

                try:
                    ssh_key = dbi.session.query(SshKeyModel).filter(
                        SshKeyModel.id == ssh_key_id,
                        SshKeyModel.created_by_id == user.id
                    ).one()
                except NoResultFound:
                    return BAD_REQUEST_MESSAGE, BAD_REQUEST_STATUS
            else:
                ssh_key = None

            test_config = TestRunConfigModel(config_title,
                                             git_repo_ref,
                                             context_vars,
                                             environment_vars,
                                             provision_type,
                                             provision_guest,
                                             provision_guest_port,
                                             ssh_key,
                                             user)

            dbi.session.add(test_config)

        else:
            # Reuse existing Test Config
            try:
                test_config = dbi.session.query(TestRunConfigModel).filter(
                    TestRunConfigModel.id == test_run_config_id
                ).one()
            except NoResultFound:
                return NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

            # Check the ssh_key still exists
            if test_config.provision_type == 'connect':
                if not test_config.ssh_key:
                    return NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

        # Test Run
        title = request_data['title'].strip()
        note = request_data['note'].strip()
        mapping_to = str(request_data['mapped_to_type']).strip()
        mapping_id = request_data['mapped_to_id']

        # Check mandatory fields
        if title == '' or mapping_to == '' or mapping_id == '':
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
            mapping = dbi.session.query(mapping_model).filter(
                mapping_model.id == mapping_id
            ).one()
        except NoResultFound:
            return NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

        # Create the Test Config only if the Test Run data is consistent
        dbi.session.commit()

        new_test_run = TestRunModel(api,
                                    title,
                                    note,
                                    test_config,
                                    mapping_to,
                                    mapping_id,
                                    user)

        dbi.session.add(new_test_run)
        dbi.session.commit()

        # Start the detached process to run the test async
        cmd = f"python3 {os.path.join(currentdir, 'tmttestrun.py')} --id {new_test_run.id} " \
              f"&> {TMT_LOGS_PATH}/{new_test_run.uid}.log &"
        os.system(cmd)

        # Notification
        notification = f'{user.email} started a Test Run for Test Case ' \
                       f'{mapping.test_case.title} as part of the sw component ' \
                       f'{api.api}, library {api.library}'
        notifications = NotificationModel(api,
                                          'info',
                                          f'Test Run for {api.api} has been requested',
                                          notification,
                                          str(user.id),
                                          f'/mapping/{api.id}')
        dbi.session.add(notifications)
        dbi.session.commit()
        dbi.engine.dispose()

        return new_test_run.as_dict()

    def put(self):
        request_data = request.get_json(force=True)
        mandatory_fields = ['api-id', 'id', 'bugs', 'note', 'mapped_to_type', 'mapped_to_id']
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
            dbi.engine.dispose()
            return NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

        # Permissions
        permissions = get_api_user_permissions(api, user.id, dbi.session)
        if 'r' not in permissions:
            dbi.engine.dispose()
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        mapping_model = None
        mapping_to = request_data['mapped_to_type']
        mapping_id = request_data['mapped_to_id']
        if mapping_to == ApiTestCaseModel.__tablename__:
            mapping_model = ApiTestCaseModel
        elif mapping_to == SwRequirementTestCaseModel.__tablename__:
            mapping_model = SwRequirementTestCaseModel
        elif mapping_to == TestSpecificationTestCaseModel.__tablename__:
            mapping_model = TestSpecificationTestCaseModel
        else:
            return BAD_REQUEST_MESSAGE, BAD_REQUEST_STATUS

        try:
            mapping = dbi.session.query(mapping_model).filter(
                mapping_model.id == mapping_id
            ).one()
        except NoResultFound:
            return NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

        try:
            run = dbi.session.query(TestRunModel).filter(
                TestRunModel.api_id == api.id,
                TestRunModel.id == request_data['id'],
                TestRunModel.mapping_to == mapping_to,
                TestRunModel.mapping_id == mapping_id,
            ).one()
        except NoResultFound:
            return NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

        test_run_modified = False
        if run.bugs != request_data['bugs']:
            test_run_modified = True
            run.bugs = request_data['bugs']

        if run.note != request_data['note']:
            test_run_modified = True
            run.note = request_data['note']

        if test_run_modified:
            dbi.session.add(run)
            dbi.session.commit()

            # Notification
            notification = f'{user.email} modified a Test Run for Test Case ' \
                           f'{mapping.test_case.title} as part of the sw component ' \
                           f'{api.api}, library {api.library}.\nBugs: {run.bugs}'
            notifications = NotificationModel(api,
                                              'info',
                                              f'Test Run for {api.api} has been modified',
                                              notification,
                                              str(user.id),
                                              f'/mapping/{api.id}')
            dbi.session.add(notifications)
            dbi.session.commit()

        dbi.engine.dispose()
        return run.as_dict()

    def delete(self):
        request_data = request.get_json(force=True)
        mandatory_fields = ['api-id', 'id', 'mapped_to_type', 'mapped_to_id']
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
            dbi.engine.dispose()
            return NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

        # Permissions
        permissions = get_api_user_permissions(api, user.id, dbi.session)
        if 'w' not in permissions:
            dbi.engine.dispose()
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        mapping_model = None
        mapping_to = request_data['mapped_to_type']
        mapping_id = request_data['mapped_to_id']
        if mapping_to == ApiTestCaseModel.__tablename__:
            mapping_model = ApiTestCaseModel
        elif mapping_to == SwRequirementTestCaseModel.__tablename__:
            mapping_model = SwRequirementTestCaseModel
        elif mapping_to == TestSpecificationTestCaseModel.__tablename__:
            mapping_model = TestSpecificationTestCaseModel
        else:
            return BAD_REQUEST_MESSAGE, BAD_REQUEST_STATUS

        try:
            mapping = dbi.session.query(mapping_model).filter(
                mapping_model.id == mapping_id
            ).one()
        except NoResultFound:
            return NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

        try:
            run = dbi.session.query(TestRunModel).filter(
                TestRunModel.api_id == api.id,
                TestRunModel.id == request_data['id'],
                TestRunModel.mapping_to == mapping_to,
                TestRunModel.mapping_id == mapping_id,
            ).one()
        except NoResultFound:
            return NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

        run_dict = run.as_dict()
        dbi.session.delete(run)
        dbi.session.commit()

        # Remove folder
        run_path = os.path.join(TMT_LOGS_PATH, run_dict['uid'])
        if os.path.exists(run_path):
            if os.path.isdir(run_path):
                shutil.rmtree(run_path)

        # Notification
        notification = f'{user.email} deleted a Test Run for Test Case ' \
                       f'{mapping.test_case.title} as part of the sw component ' \
                       f'{api.api}, library {api.library}.'
        notifications = NotificationModel(api,
                                          'info',
                                          f'Test Run for {api.api} has been removed',
                                          notification,
                                          str(user.id),
                                          f'/mapping/{api.id}')
        dbi.session.add(notifications)
        dbi.session.commit()
        dbi.engine.dispose()
        return run_dict


class TestRunLog(Resource):

    def get(self):
        mandatory_fields = ['api-id', 'id']
        args = get_query_string_args(request.args)
        if not check_fields_in_request(mandatory_fields, args):
            return BAD_REQUEST_MESSAGE, BAD_REQUEST_STATUS

        dbi = db_orm.DbInterface(get_db())

        # User
        user = get_active_user_from_request(args, dbi.session)
        if isinstance(user, UserModel):
            user_id = user.id
        else:
            user_id = 0

        # Find api
        api = get_api_from_request(args, dbi.session)
        if not api:
            dbi.engine.dispose()
            return NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

        # Permissions
        permissions = get_api_user_permissions(api, user_id, dbi.session)
        if 'r' not in permissions:
            dbi.engine.dispose()
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        try:
            run = dbi.session.query(TestRunModel).filter(
                TestRunModel.api_id == api.id,
                TestRunModel.id == args['id'],
            ).one()
        except NoResultFound:
            return NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

        log_txt = ''
        log_exec = ''
        log_txt_path = os.path.join(TMT_LOGS_PATH, run.uid, 'log.txt')

        if os.path.exists(log_txt_path):
            f = open(log_txt_path, 'r')
            log_txt = f.read()
            f.close()
        else:
            log_txt = "File not found that mean there was an error in the execution. See the stdout/stderr section."

        log_exec_path = os.path.join(TMT_LOGS_PATH, f'{run.uid}.log')
        if os.path.exists(log_exec_path):
            f = open(log_exec_path, 'r')
            log_exec = f.read()
            f.close()
        else:
            log_exec = "File not found that mean there was an error in the execution."

        # List files in the TMT_PLAN_DATA dir
        artifacts = []
        if os.path.exists(os.path.join(TMT_LOGS_PATH, run.uid, 'api', 'tmt-plan', 'data')):
            artifacts = os.listdir(os.path.join(TMT_LOGS_PATH, run.uid, 'api', 'tmt-plan', 'data'))

        return {'artifacts': artifacts,
                'log_txt': log_txt,
                'log_exec': log_exec,
                'stdout_stderr': run.log}


class TestRunArtifacts(Resource):

    def get(self):
        mandatory_fields = ['api-id', 'artifact', 'id']
        args = get_query_string_args(request.args)
        if not check_fields_in_request(mandatory_fields, args):
            return BAD_REQUEST_MESSAGE, BAD_REQUEST_STATUS

        dbi = db_orm.DbInterface(get_db())

        # User
        user = get_active_user_from_request(args, dbi.session)
        if isinstance(user, UserModel):
            user_id = user.id
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS
        else:
            user_id = 0

        # Find api
        api = get_api_from_request(args, dbi.session)
        if not api:
            dbi.engine.dispose()
            return NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

        # Permissions
        permissions = get_api_user_permissions(api, user_id, dbi.session)
        if 'r' not in permissions:
            dbi.engine.dispose()
            return UNAUTHORIZED_MESSAGE, UNAUTHORIZED_STATUS

        try:
            run = dbi.session.query(TestRunModel).filter(
                TestRunModel.api_id == api.id,
                TestRunModel.id == args['id'],
            ).one()
        except NoResultFound:
            return NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

        # List files in the TMT_PLAN_DATA dir
        artifacts_path = os.path.join(TMT_LOGS_PATH, run.uid, 'api', 'tmt-plan', 'data')
        artifacts = os.listdir(artifacts_path)
        if args['artifact'] not in artifacts:
            return NOT_FOUND_MESSAGE, NOT_FOUND_STATUS

        return send_from_directory(artifacts_path, args['artifact'])


api.add_resource(Api, '/apis')
api.add_resource(ApiHistory, '/apis/history')
api.add_resource(ApiSpecification, '/api-specifications')
api.add_resource(Library, '/libraries')
api.add_resource(SPDXLibrary, '/spdx/libraries')
api.add_resource(Justification, '/justifications')
api.add_resource(SwRequirement, '/sw-requirements')
api.add_resource(TestSpecification, '/test-specifications')
api.add_resource(TestCase, '/test-cases')
# Mapping
# - Direct
api.add_resource(ApiSpecificationsMapping, '/mapping/api/specifications')
api.add_resource(ApiJustificationsMapping, '/mapping/api/justifications')
api.add_resource(ApiSwRequirementsMapping, '/mapping/api/sw-requirements')
api.add_resource(ApiTestSpecificationsMapping, '/mapping/api/test-specifications')
api.add_resource(ApiTestCasesMapping, '/mapping/api/test-cases')
api.add_resource(TestRunConfig, '/mapping/api/test-run-configs')
api.add_resource(TestRun, '/mapping/api/test-runs')
api.add_resource(TestRunLog, '/mapping/api/test-run/log')
api.add_resource(TestRunArtifacts, '/mapping/api/test-run/artifacts')
# - Indirect
api.add_resource(SwRequirementSwRequirementsMapping, '/mapping/sw-requirement/sw-requirements')
api.add_resource(SwRequirementTestSpecificationsMapping, '/mapping/sw-requirement/test-specifications')
api.add_resource(SwRequirementTestCasesMapping, '/mapping/sw-requirement/test-cases')
api.add_resource(TestSpecificationTestCasesMapping, '/mapping/test-specification/test-cases')
# History
api.add_resource(MappingHistory, '/mapping/history')
api.add_resource(CheckSpecification, '/apis/check-specification')
api.add_resource(FixNewSpecificationWarnings, '/apis/fix-specification-warnings')

# Testing Support
api.add_resource(TestingSupportInitDb, '/test-support/init-db')

# Usage
api.add_resource(MappingUsage, '/mapping/usage')
# Comments
api.add_resource(Comment, '/comments')
# Fork
api.add_resource(ForkApiSwRequirement, '/fork/api/sw-requirement')
api.add_resource(ForkSwRequirementSwRequirement, '/fork/sw-requirement/sw-requirement')
# api.add_resource(ForkTestSpecification, '/fork/api/test-specification')
# api.add_resource(ForkTestCase, '/fork/api/test-case')
# api.add_resource(ForkJustification, '/fork/api/justification')
api.add_resource(User, '/user')
api.add_resource(UserEnable, '/user/enable')
api.add_resource(UserLogin, '/user/login')
api.add_resource(UserNotifications, '/user/notifications')
api.add_resource(UserPermissionsApi, '/user/permissions/api')
api.add_resource(UserResetPassword, '/user/reset-password')
api.add_resource(UserRole, '/user/role')
api.add_resource(UserSignin, '/user/signin')
api.add_resource(UserSshKey, '/user/ssh-key')
api.add_resource(Testing, '/testing')


if __name__ == "__main__":
    import argparse
    import sys
    parser = argparse.ArgumentParser()
    parser.add_argument('--testing',
                        default=False,
                        action='store_true',
                        help='Test Api Project using db/test.db database')
    args = parser.parse_args()

    app.config['TESTING'] = args.testing
    app.config['ENV'] = 'local'

    if app.config['TESTING']:
        app.config['DB'] = 'test.db'
        import db.models.init_db as init_db
        init_db.initialization(db_name='test.db')
    else:
        app.config['DB'] = 'basil.db'
    app.run()
