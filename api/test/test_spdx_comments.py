"""BASIL mapping comments exported as SPDX Annotations on work items."""

import json
from types import SimpleNamespace
from unittest.mock import MagicMock

from api_utils import parse_optional_int_id_list
from spdx_manager import SPDXAnnotation, SPDXFile, SPDXManager


def _file(spdx_id, name="item"):
    return SPDXFile(spdx_id=spdx_id, name=name, comment="", creation_info=None)


def _manager():
    mgr = object.__new__(SPDXManager)
    mgr.sbom = []
    mgr.getCreationInfoAndPerson = MagicMock(
        return_value=(SimpleNamespace(spdx_id="_:creation_info_comment"), MagicMock())
    )
    return mgr


def _comment(comment_id=11, text="please clarify coverage", todo=False, parent_id=7):
    comment = MagicMock()
    comment.id = comment_id
    comment.parent_table = "sw_requirement_mapping_api"
    comment.parent_id = parent_id
    comment.created_by = SimpleNamespace(id=3, username="alice")
    comment.created_at = None
    comment.as_dict.return_value = {
        "id": comment_id,
        "comment": text,
        "todo": todo,
        "done": False,
        "created_by": "alice",
    }
    return comment


def _dbsession(comments):
    query = MagicMock()
    query.filter.return_value = query
    query.order_by.return_value = query
    query.all.return_value = comments
    dbsession = MagicMock()
    dbsession.query.return_value = query
    return dbsession


def test_add_work_item_comments_creates_review_annotation():
    work_item = _file("spdx:file:basil:software-requirement:42", name="SR")
    mapping = SimpleNamespace(__tablename__="sw_requirement_mapping_api", id=7)
    comment = _comment()
    mgr = _manager()
    mgr.sbom = [work_item]

    mgr.addWorkItemComments(
        spdx_work_item=work_item, mapping=mapping, dbsession=_dbsession([comment])
    )

    annotations = [item for item in mgr.sbom if isinstance(item, SPDXAnnotation)]
    assert len(annotations) == 1
    payload = annotations[0].to_dict()
    assert payload["annotationType"] == "review"
    assert payload["subject"] == work_item.spdx_id
    assert payload["spdxId"] == "spdx:annotation:basil:comment:11"
    statement = json.loads(payload["statement"])
    assert statement["kind"] == "comment"
    assert statement["comment"] == "please clarify coverage"
    assert statement["parent_table"] == "sw_requirement_mapping_api"
    assert statement["parent_id"] == 7
    assert statement["basil:annotationVersion"] == "2.0"


def test_add_work_item_comments_skips_when_disabled():
    work_item = _file("spdx:file:basil:software-requirement:42")
    mapping = SimpleNamespace(__tablename__="sw_requirement_mapping_api", id=7)
    mgr = _manager()
    mgr.include_comments = False
    mgr.sbom = [work_item]
    mgr.addWorkItemComments(
        spdx_work_item=work_item, mapping=mapping, dbsession=_dbsession([_comment()])
    )
    assert all(not isinstance(item, SPDXAnnotation) for item in mgr.sbom)


def test_add_work_item_comments_skips_without_mapping():
    work_item = _file("spdx:file:basil:software-requirement:42")
    mgr = _manager()
    mgr.sbom = [work_item]
    mgr.addWorkItemComments(spdx_work_item=work_item, mapping=None, dbsession=MagicMock())
    assert all(not isinstance(item, SPDXAnnotation) for item in mgr.sbom)


def test_parse_optional_int_id_list():
    assert parse_optional_int_id_list({}) is None
    assert parse_optional_int_id_list({"other": "1"}) is None
    assert parse_optional_int_id_list({"test_run_config_id": ""}) == []
    assert parse_optional_int_id_list({"test_run_config_id": "1,2,2"}) == [1, 2]
