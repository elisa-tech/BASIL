import datetime
import hashlib
import json
import os
import sys

from semantic_version import Version
from spdx_tools.spdx3.model.positive_integer_range import PositiveIntegerRange
from spdx_tools.spdx3.payload import Payload
from spdx_tools.spdx3.model import (
    Hash,
    HashAlgorithm,
    CreationInfo,
    ProfileIdentifierType,
    Relationship,
    RelationshipCompleteness,
    RelationshipType,
)
from spdx_tools.spdx3.model.software import File, Sbom, SBOMType, Snippet
from spdx_tools.spdx3.writer.json_ld import json_ld_writer
from typing import List, Optional, Union

currentdir = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(1, os.path.dirname(currentdir))

from db.db_orm import DbInterface  # noqa E402
from db.models.api import ApiModel  # noqa E402
from db.models.api_document import ApiDocumentModel  # noqa E402
from db.models.api_justification import ApiJustificationModel  # noqa E402
from db.models.api_sw_requirement import ApiSwRequirementModel  # noqa E402
from db.models.api_test_case import ApiTestCaseModel  # noqa E402
from db.models.api_test_specification import ApiTestSpecificationModel  # noqa E402
from db.models.sw_requirement_sw_requirement import SwRequirementSwRequirementModel  # noqa E402
from db.models.sw_requirement_test_case import SwRequirementTestCaseModel  # noqa E402
from db.models.sw_requirement_test_specification import SwRequirementTestSpecificationModel  # noqa E402
from db.models.sw_requirement import SwRequirementModel  # noqa E402
from db.models.test_run import TestRunModel  # noqa E402
from db.models.test_specification_test_case import TestSpecificationTestCaseModel  # noqa E402
from db.models.user import UserModel  # noqa E402


class SPDXManager:

    sbom = None

    API_REFERENCE_DOC_SPDX_ID_PREFIX = "API-REFERENCE-DOCUMENT"
    API_SPDX_ID_PREFIX = "API"
    DOCUMENT_SPDX_ID_PREFIX = "DOCUMENT"
    JUSTIFICATION_SPDX_ID_PREFIX = "JUSTIFICATION"
    SW_REQUIREMENT_SPDX_ID_PREFIX = "SW-REQUIREMENT"
    TEST_CASE_SPDX_ID_PREFIX = "TEST-CASE"
    TEST_RUN_SPDX_ID_PREFIX = "TEST-RUN"
    TEST_SPECIFICATION_SPDX_ID_PREFIX = "TEST-SPECIFICATION"

    def __init__(self, library_name):
        spdx_id = f"SPDX-{library_name.strip()}-EXPORT"
        ci = CreationInfo(
            spec_version=Version(version_string="1.0.0"),
            profile=[ProfileIdentifierType.SOFTWARE],
            created_by=["BASIL"],
            created=datetime.datetime.now(),
        )
        self.sbom = Sbom(
            creation_info=ci,
            spdx_id=spdx_id,
            element=[],
            root_element=[],
            name=library_name,
            sbom_type=[SBOMType.DESIGN],
        )
        self.payload = Payload()
        self.payload.add_element(self.sbom)

    def add_files_to_payload(self, _files: List[File]):
        """Add a File to Payload if not already there"""
        for _file in _files:
            existing = [f for f in self.payload.get_full_map().keys() if f == _file.spdx_id]
            if not existing:
                self.payload.add_element(_file)

    def get_relationship_from_str(self, _relationship_str: str) -> RelationshipType:
        """Convert a string to a RelationshipType

        In the db we save the relationship as string.

        :param _relationship_str: string of the relationship type
        :return: RelationshipType related to the relationship string or OTHER
        """
        relationship_string_mapping = {
            "AFFECTS": RelationshipType.AFFECTS,
            "AMENDS": RelationshipType.AMENDS,
            "ANCESTOR": RelationshipType.ANCESTOR,
            "AVAILABLE_FROM": RelationshipType.AVAILABLE_FROM,
            "BUILD_DEPENDENCY": RelationshipType.BUILD_DEPENDENCY,
            "BUILD_TOOL": RelationshipType.BUILD_TOOL,
            "COORDINATED_BY": RelationshipType.COORDINATED_BY,
            "CONTAINS": RelationshipType.CONTAINS,
            "CONFIG_OF": RelationshipType.CONFIG_OF,
            "COPY": RelationshipType.COPY,
            "DATA_FILE": RelationshipType.DATA_FILE,
            "DEPENDENCY_MANIFEST": RelationshipType.DEPENDENCY_MANIFEST,
            "DEPENDS_ON": RelationshipType.DEPENDS_ON,
            "DESCENDANT": RelationshipType.DESCENDANT,
            "DESCRIBES": RelationshipType.DESCRIBES,
            "DEV_DEPENDENCY": RelationshipType.DEV_DEPENDENCY,
            "DEV_TOOL": RelationshipType.DEV_TOOL,
            "DISTRIBUTION_ARTIFACT": RelationshipType.DISTRIBUTION_ARTIFACT,
            "DOCUMENTATION": RelationshipType.DOCUMENTATION,
            "DOES_NOT_AFFECT": RelationshipType.DOES_NOT_AFFECT,
            "DYNAMIC_LINK": RelationshipType.DYNAMIC_LINK,
            "EXAMPLE": RelationshipType.EXAMPLE,
            "EVIDENCE_FOR": RelationshipType.EVIDENCE_FOR,
            "EXPANDED_FROM_ARCHIVE": RelationshipType.EXPANDED_FROM_ARCHIVE,
            "EXPLOIT_CREATED_BY": RelationshipType.EXPLOIT_CREATED_BY,
            "FILE_ADDED": RelationshipType.FILE_ADDED,
            "FILE_DELETED": RelationshipType.FILE_DELETED,
            "FILE_MODIFIED": RelationshipType.FILE_MODIFIED,
            "FIXED_BY": RelationshipType.FIXED_BY,
            "FIXED_IN": RelationshipType.FIXED_IN,
            "FOUND_BY": RelationshipType.FOUND_BY,
            "GENERATES": RelationshipType.GENERATES,
            "HAS_ASSESSMENT_FOR": RelationshipType.HAS_ASSESSMENT_FOR,
            "HAS_ASSOCIATED_VULNERABILITY": RelationshipType.HAS_ASSOCIATED_VULNERABILITY,
            "HOST_OF": RelationshipType.HOST_OF,
            "INPUT_OF": RelationshipType.INPUT_OF,
            "INVOKED_BY": RelationshipType.INVOKED_BY,
            "METAFILE": RelationshipType.METAFILE,
            "ON_BEHALF_OF": RelationshipType.ON_BEHALF_OF,
            "OPTIONAL_COMPONENT": RelationshipType.OPTIONAL_COMPONENT,
            "OPTIONAL_DEPENDENCY": RelationshipType.OPTIONAL_DEPENDENCY,
            "OTHER": RelationshipType.OTHER,
            "OUTPUT_OF": RelationshipType.OUTPUT_OF,
            "PACKAGES": RelationshipType.PACKAGES,
            "PATCH": RelationshipType.PATCH,
            "PREREQUISITE": RelationshipType.PREREQUISITE,
            "PROVIDED_DEPENDENCY": RelationshipType.PROVIDED_DEPENDENCY,
            "PUBLISHED_BY": RelationshipType.PUBLISHED_BY,
            "REPORTED_BY": RelationshipType.REPORTED_BY,
            "REPUBLISHED_BY": RelationshipType.REPUBLISHED_BY,
            "REQUIREMENT_FOR": RelationshipType.REQUIREMENT_FOR,
            "RUNTIME_DEPENDENCY": RelationshipType.RUNTIME_DEPENDENCY,
            "SPECIFICATION_FOR": RelationshipType.SPECIFICATION_FOR,
            "STATIC_LINK": RelationshipType.STATIC_LINK,
            "TEST": RelationshipType.TEST,
            "TEST_CASE": RelationshipType.TEST_CASE,
            "TEST_DEPENDENCY": RelationshipType.TEST_DEPENDENCY,
            "TEST_TOOL": RelationshipType.TEST_TOOL,
            "TESTED_ON": RelationshipType.TESTED_ON,
            "TRAINED_ON": RelationshipType.TRAINED_ON,
            "UNDER_INVESTIGATION_FOR": RelationshipType.UNDER_INVESTIGATION_FOR,
            "VARIANT": RelationshipType.VARIANT,
        }
        return relationship_string_mapping.get(_relationship_str, RelationshipType.OTHER)

    def dict_hash(self, dictionary) -> str:
        """MD5 hash of a dictionary."""
        dhash = hashlib.md5()
        # We need to sort arguments so {'a': 1, 'b': 2} is
        # the same as {'b': 2, 'a': 1}
        encoded = json.dumps(dictionary, sort_keys=True).encode()
        dhash.update(encoded)
        return dhash.hexdigest()

    def clean_api_relation_dict(self, relation_dict):
        """Remove unwanted keys from a dictionary of a relation to api"""
        unwanted_keys = ["api", "document", "justification", "sw_requirement", "test_case", "test_specification"]
        for key in unwanted_keys:
            if key in relation_dict.keys():
                relation_dict.pop(key, None)
        return relation_dict

    def get_completeness(self, coverage: int) -> RelationshipCompleteness:
        """Return RelationshipCompleteness based on the mapping coverage percentage"""
        if coverage >= 100:
            return RelationshipCompleteness.COMPLETE
        else:
            return RelationshipCompleteness.INCOMPLETE

    def SnippetSPDX(self, _mapping, _dbsession) -> Snippet:
        """In BASIL, Software Component Reference Document are
        split in Snippets and each Snippet is assigned to work items.
        This function create SPDX Snippet class describing snippet of the reference document
        """
        mapping_from_id_prefix = self.API_SPDX_ID_PREFIX
        mapping_to_id_prefix = ""

        if isinstance(_mapping, ApiDocumentModel):
            mapping_to_id_prefix = self.DOCUMENT_SPDX_ID_PREFIX
        elif isinstance(_mapping, ApiSwRequirementModel):
            mapping_to_id_prefix = self.SW_REQUIREMENT_SPDX_ID_PREFIX
        elif isinstance(_mapping, ApiTestSpecificationModel):
            mapping_to_id_prefix = self.TEST_SPECIFICATION_SPDX_ID_PREFIX
        elif isinstance(_mapping, ApiTestCaseModel):
            mapping_to_id_prefix = self.TEST_CASE_SPDX_ID_PREFIX
        elif isinstance(_mapping, ApiJustificationModel):
            mapping_to_id_prefix = self.JUSTIFICATION_SPDX_ID_PREFIX

        mapping_dict = _mapping.as_dict(full_data=True, db_session=_dbsession)
        api = mapping_dict["api"]["api"]
        api_id = mapping_dict["api"]["id"]
        relation_id = mapping_dict["relation_id"]
        mapping_dict = self.clean_api_relation_dict(mapping_dict)

        return Snippet(
            spdx_id=f"SNIPPET-{mapping_from_id_prefix}-" f"{mapping_to_id_prefix}-" f"{api_id}-" f"{relation_id}",
            name=f"Snippet of api {api} reference document",
            comment="",
            byte_range=PositiveIntegerRange(
                mapping_dict["offset"], mapping_dict["offset"] + len(mapping_dict["section"])
            ),
            attribution_text=json.dumps(mapping_dict),
        )

    def ApiSPDX(self, _api, _dbsession) -> File:
        """This function create SPDX File class describing a BASIL Software Component"""
        api_dict = _api.as_dict(full_data=True, db_session=_dbsession)
        api_dict["__tablename__"] = _api.__tablename__
        return File(
            spdx_id=f"{self.API_SPDX_ID_PREFIX}-{api_dict['id']}",
            name=f"{api_dict['api']}",
            verified_using=[Hash(algorithm=HashAlgorithm.MD5, hash_value=self.dict_hash(api_dict))],
            attribution_text=json.dumps(api_dict),
            summary=_api._description,
        )

    def ApiReferenceDocumentSPDX(self, _api, _dbsession) -> File:
        """This function create SPDX File class describing a BASIL Software Component Reference Document"""
        api_dict = _api.as_dict(full_data=True, db_session=_dbsession)
        return File(
            spdx_id=f"{self.API_REFERENCE_DOC_SPDX_ID_PREFIX}-{api_dict['id']}",
            name=f"{api_dict['raw_specification_url']}",
            verified_using=[Hash(algorithm=HashAlgorithm.MD5, hash_value=self.dict_hash(api_dict))],
            attribution_text=json.dumps(api_dict),
            summary=_api._description,
        )

    def SwRequirementSPDX(self, _sr, _dbsession) -> File:
        """This function create SPDX File class describing a BASIL Software Requirement"""
        sr_dict = _sr.as_dict(full_data=True, db_session=_dbsession)
        sr_dict["__tablename__"] = _sr.__tablename__
        return File(
            spdx_id=f"{self.SW_REQUIREMENT_SPDX_ID_PREFIX}_{sr_dict['id']}",
            name=f"{sr_dict['title']}",
            verified_using=[Hash(algorithm=HashAlgorithm.MD5, hash_value=self.dict_hash(sr_dict))],
            attribution_text=json.dumps(sr_dict),
            summary=_sr._description,
        )

    def TestSpecificationSPDX(self, _ts, _dbsession) -> File:
        """This function create SPDX File class describing a BASIL Test Specification"""
        ts_dict = _ts.as_dict(full_data=True, db_session=_dbsession)
        ts_dict["__tablename__"] = _ts.__tablename__
        return File(
            spdx_id=f"{self.TEST_SPECIFICATION_SPDX_ID_PREFIX}_{ts_dict['id']}",
            name=f"{ts_dict['title']}",
            verified_using=[Hash(algorithm=HashAlgorithm.MD5, hash_value=self.dict_hash(ts_dict))],
            attribution_text=json.dumps(ts_dict),
            summary=_ts._description,
        )

    def TestCaseSPDX(self, _tc, _mapping_to_prefix, _dbsession) -> File:
        """This function create SPDX File class describing a BASIL Test Case"""
        tc_dict = _tc.as_dict(full_data=True, db_session=_dbsession)
        tc_dict["__tablename__"] = _tc.__tablename__
        return File(
            spdx_id=f"{self.TEST_CASE_SPDX_ID_PREFIX}@{_mapping_to_prefix}_{tc_dict['id']}",
            name=f"{tc_dict['title']}",
            verified_using=[Hash(algorithm=HashAlgorithm.MD5, hash_value=self.dict_hash(tc_dict))],
            attribution_text=json.dumps(tc_dict),
            summary=_tc._description,
        )

    def TestRunSPDX(self, _tr, _dbsession) -> File:
        """This function create SPDX File class describing a BASIL Test Run"""
        tr_dict = _tr.as_dict(full_data=True)
        tr_dict["__tablename__"] = _tr.__tablename__
        return File(
            spdx_id=f"{self.TEST_RUN_SPDX_ID_PREFIX}_{tr_dict['id']}",
            name=f"{tr_dict['title']}",
            verified_using=[Hash(algorithm=HashAlgorithm.MD5, hash_value=self.dict_hash(tr_dict))],
            attribution_text=json.dumps(tr_dict),
            summary=_tr._description,
        )

    def JustificationSPDX(self, _js, _dbsession) -> File:
        """This function create SPDX File class describing a BASIL Justification"""
        js_dict = _js.as_dict(full_data=True, db_session=_dbsession)
        js_dict["__tablename__"] = _js.__tablename__
        return File(
            spdx_id=f"{self.JUSTIFICATION_SPDX_ID_PREFIX}_{js_dict['id']}",
            name=f"{js_dict['description']}",
            verified_using=[Hash(algorithm=HashAlgorithm.MD5, hash_value=self.dict_hash(js_dict))],
            attribution_text=json.dumps(js_dict),
            summary=_js._description,
        )

    def DocumentSPDX(self, _doc, _dbsession) -> File:
        """This function create SPDX File class describing a BASIL Document"""
        doc_dict = _doc.as_dict(full_data=True, db_session=_dbsession)
        doc_dict["__tablename__"] = _doc.__tablename__
        return File(
            spdx_id=f"{self.DOCUMENT_SPDX_ID_PREFIX}_{doc_dict['id']}",
            name=f"{doc_dict['title']}",
            verified_using=[Hash(algorithm=HashAlgorithm.MD5, hash_value=self.dict_hash(doc_dict))],
            attribution_text=json.dumps(doc_dict),
            summary=_doc._description,
        )

    def get_x_sr_children(self,
                          api: ApiModel,
                          xsr: Optional[Union[ApiSwRequirementModel, SwRequirementSwRequirementModel]],
                          spdx_sr: SwRequirementSPDX,
                          dbi: DbInterface):
        """In BASIL user can create a complex hierarchy of Software Requirements.
        Moreover we can assign other work items to each Software Requirement in the chain.
        This method navigate the hierarchy and return all the work items

        :param api: software component where the mapping is defined
        :param xsr: Sw Requirement mapping model instance
        :param spdx_sr: SwRequirementSPDX instance
        :param dbi: Database interface instance
        :return:
        """
        files = []
        relationships = []

        if isinstance(xsr, ApiSwRequirementModel):
            mapping_field_id = "sw_requirement_mapping_api_id"
        elif isinstance(xsr, SwRequirementSwRequirementModel):
            mapping_field_id = "sw_requirement_mapping_sw_requirement_id"
        else:
            return files, relationships

        # SwRequirementSwRequirementModel
        sr_srs = (
            dbi.session.query(SwRequirementSwRequirementModel)
            .filter(getattr(SwRequirementSwRequirementModel, mapping_field_id) == xsr.id)
            .all()
        )
        for sr_sr in sr_srs:
            spdx_sr_sr = self.SwRequirementSPDX(sr_sr.sw_requirement, dbi.session)
            spdx_sr_sr_rel = Relationship(
                spdx_id=f"REL_{spdx_sr.spdx_id}_{spdx_sr_sr.spdx_id}",
                from_element=spdx_sr.spdx_id,
                completeness=self.get_completeness(sr_sr.coverage),
                relationship_type=RelationshipType.GENERATES,
                to=[spdx_sr_sr.spdx_id],
            )

            files += [spdx_sr_sr]
            relationships += [spdx_sr_sr_rel]

            child_files, child_relationships = self.get_x_sr_children(api, sr_sr, spdx_sr_sr, dbi)
            files += child_files
            relationships += child_relationships

        # SwRequirementTestSpecificationModel
        sr_tss = (
            dbi.session.query(SwRequirementTestSpecificationModel)
            .filter(getattr(SwRequirementTestSpecificationModel, mapping_field_id) == xsr.id)
            .all()
        )
        for sr_ts in sr_tss:
            spdx_ts = self.TestSpecificationSPDX(sr_ts.test_specification, dbi.session)
            spdx_sr_ts_rel = Relationship(
                spdx_id=f"REL_{spdx_ts.spdx_id}_{spdx_sr.spdx_id}",
                from_element=spdx_ts.spdx_id,
                completeness=self.get_completeness(sr_ts.coverage),
                relationship_type=RelationshipType.TEST,
                to=[spdx_sr.spdx_id],
            )
            files += [spdx_ts]
            relationships += [spdx_sr_ts_rel]

            # TestSpecificationTestCaseModel
            ts_tcs = (
                dbi.session.query(TestSpecificationTestCaseModel)
                .filter(TestSpecificationTestCaseModel.test_specification_mapping_sw_requirement_id == sr_ts.id)
                .all()
            )
            for ts_tc in ts_tcs:
                spdx_tc = self.TestCaseSPDX(ts_tc.test_case, self.TEST_SPECIFICATION_SPDX_ID_PREFIX, dbi.session)
                spdx_ts_tc_rel = Relationship(
                    spdx_id=f"REL_{spdx_ts.spdx_id}_{spdx_tc.spdx_id}",
                    from_element=spdx_ts.spdx_id,
                    completeness=self.get_completeness(ts_tc.coverage),
                    relationship_type=RelationshipType.SPECIFICATION_FOR,
                    to=[spdx_tc.spdx_id],
                )
                files += [spdx_tc]
                relationships += [spdx_ts_tc_rel]

                # Test Runs
                spdx_trs, spdx_trs_rel = self.get_test_runs(api.id, ts_tc, spdx_tc, dbi)
                files += spdx_trs
                relationships += spdx_trs_rel

        # SwRequirementTestCaseModel
        sr_tcs = (
            dbi.session.query(SwRequirementTestCaseModel)
            .filter(getattr(SwRequirementTestCaseModel, mapping_field_id) == xsr.id)
            .all()
        )
        for sr_tc in sr_tcs:
            spdx_tc = self.TestCaseSPDX(sr_tc.test_case, self.SW_REQUIREMENT_SPDX_ID_PREFIX, dbi.session)
            spdx_sr_tc_rel = Relationship(
                spdx_id=f"REL_{spdx_tc.spdx_id}_{spdx_sr.spdx_id}",
                from_element=spdx_tc.spdx_id,
                completeness=self.get_completeness(sr_tc.coverage),
                relationship_type=RelationshipType.TEST_CASE,
                to=[spdx_sr.spdx_id],
            )
            files += [spdx_tc]
            relationships += [spdx_sr_tc_rel]

            # Test Runs
            spdx_trs, spdx_trs_rel = self.get_test_runs(api.id, sr_tc, spdx_tc, dbi)
            files += spdx_trs
            relationships += spdx_trs_rel

        return files, relationships

    def get_test_runs(self, api_id, mapping_model_instance, spdx_tc, dbi):
        """List Test Run for a selected mapping_model_instance and api_id and return
        list of TestRunSPDX and list of Relationship to Test Case

        Note: Same Test Case can be mapped to different section of the Reference Document
        or to different work items. BASIL Test Runs refers to the mapping ot the Test Case, not to
        the Test Case itself.
        """
        trs = (
            dbi.session.query(TestRunModel)
            .filter(
                TestRunModel.api_id == api_id,
                TestRunModel.mapping_to == mapping_model_instance.__tablename__,
                TestRunModel.mapping_id == mapping_model_instance.id,
            )
            .all()
        )

        spdx_trs = []
        spdx_trs_rel = []

        for tr in trs:
            spdx_tr = self.TestRunSPDX(tr, dbi.session)
            spdx_tr_rel = Relationship(
                spdx_id=f"REL_{spdx_tr.spdx_id}_{spdx_tc.spdx_id}",
                from_element=spdx_tr.spdx_id,
                relationship_type=RelationshipType.EVIDENCE_FOR,
                to=[spdx_tc.spdx_id],
            )
            spdx_trs.append(spdx_tr)
            spdx_trs_rel.append(spdx_tr_rel)
        return spdx_trs, spdx_trs_rel

    def add_api_to_export(self, dbi: DbInterface, api: ApiModel):
        """Collect all the work items of a BASIL Software Component and their relationships
        and add them to the class payload"""
        api = dbi.session.query(ApiModel).filter(ApiModel.id == api.id).one()

        # Api
        spdx_api = self.ApiSPDX(api, dbi.session)
        spdx_api_ref_doc = self.ApiReferenceDocumentSPDX(api, dbi.session)
        api_api_ref_doc_rel = Relationship(
            spdx_id=f"REL_{spdx_api_ref_doc.spdx_id}_{spdx_api.spdx_id}",
            from_element=spdx_api_ref_doc.spdx_id,
            relationship_type=RelationshipType.DESCRIBES,
            to=[spdx_api.spdx_id],
        )

        self.add_files_to_payload([spdx_api, spdx_api_ref_doc])
        self.add_files_to_payload([api_api_ref_doc_rel])

        # ApiSwRequirement
        api_sw_requirements = (
            dbi.session.query(ApiSwRequirementModel).filter(ApiSwRequirementModel.api_id == api.id).all()
        )
        for asr in api_sw_requirements:
            # ApiSwRequirement
            spdx_asr_snippet = self.SnippetSPDX(asr, dbi.session)
            spdx_asr_snippet_rel = Relationship(
                spdx_id=f"REL_{spdx_api_ref_doc.spdx_id}_{spdx_asr_snippet.spdx_id}",
                from_element=spdx_api_ref_doc.spdx_id,
                relationship_type=RelationshipType.CONTAINS,
                to=[spdx_asr_snippet.spdx_id],
            )
            spdx_sr = self.SwRequirementSPDX(asr.sw_requirement, dbi.session)
            spdx_asr_sr_rel = Relationship(
                spdx_id=f"REL_{spdx_sr.spdx_id}_{spdx_asr_snippet.spdx_id}",
                from_element=spdx_sr.spdx_id,
                completeness=self.get_completeness(asr.coverage),
                relationship_type=RelationshipType.REQUIREMENT_FOR,
                to=[spdx_asr_snippet.spdx_id],
            )

            self.add_files_to_payload([spdx_asr_snippet])
            self.add_files_to_payload([spdx_sr])
            self.add_files_to_payload([spdx_asr_snippet_rel, spdx_asr_sr_rel])

            child_files, child_relationships = self.get_x_sr_children(api, asr, spdx_sr, dbi)
            self.add_files_to_payload(child_files)
            self.add_files_to_payload(child_relationships)

        # ApiTestSpecification
        api_test_specifications = (
            dbi.session.query(ApiTestSpecificationModel).filter(ApiTestSpecificationModel.api_id == api.id).all()
        )
        for ats in api_test_specifications:
            spdx_ats_snippet = self.SnippetSPDX(ats, dbi.session)
            spdx_ats_snippet_rel = Relationship(
                spdx_id=f"REL_{spdx_api_ref_doc.spdx_id}_{spdx_ats_snippet.spdx_id}",
                from_element=spdx_api_ref_doc.spdx_id,
                relationship_type=RelationshipType.CONTAINS,
                to=[spdx_ats_snippet.spdx_id],
            )
            spdx_ts = self.TestSpecificationSPDX(ats.test_specification, dbi.session)
            spdx_ats_ts_rel = Relationship(
                spdx_id=f"REL_{spdx_ts.spdx_id}_{spdx_ats_snippet.spdx_id}",
                from_element=spdx_ts.spdx_id,
                completeness=self.get_completeness(ats.coverage),
                relationship_type=RelationshipType.TEST,
                to=[spdx_ats_snippet.spdx_id],
            )

            self.add_files_to_payload([spdx_ats_snippet])
            self.add_files_to_payload([spdx_ts])
            self.add_files_to_payload([spdx_ats_snippet_rel, spdx_ats_ts_rel])

            # TestSpecificationTestCase
            ts_tcs = (
                dbi.session.query(TestSpecificationTestCaseModel)
                .filter(TestSpecificationTestCaseModel.test_specification_mapping_api_id == ats.id)
                .all()
            )
            for ts_tc in ts_tcs:
                spdx_tc = self.TestCaseSPDX(ts_tc.test_case, self.TEST_SPECIFICATION_SPDX_ID_PREFIX, dbi.session)
                spdx_ts_tc_rel = Relationship(
                    spdx_id=f"REL_{spdx_ts.spdx_id}_{spdx_tc.spdx_id}",
                    from_element=spdx_ts.spdx_id,
                    completeness=self.get_completeness(ts_tc.coverage),
                    relationship_type=RelationshipType.SPECIFICATION_FOR,
                    to=[spdx_tc.spdx_id],
                )
                self.add_files_to_payload([spdx_tc])
                self.add_files_to_payload([spdx_ts_tc_rel])

                # Test Runs
                spdx_trs, spdx_trs_rel = self.get_test_runs(api.id, ts_tc, spdx_tc, dbi)
                self.add_files_to_payload(spdx_trs)
                self.add_files_to_payload(spdx_trs_rel)

        # ApiTestCase
        api_test_cases = dbi.session.query(ApiTestCaseModel).filter(ApiTestCaseModel.api_id == api.id).all()
        for atc in api_test_cases:
            spdx_atc_snippet = self.SnippetSPDX(atc, dbi.session)
            spdx_atc_snippet_rel = Relationship(
                spdx_id=f"REL_{spdx_api_ref_doc.spdx_id}_{spdx_atc_snippet.spdx_id}",
                from_element=spdx_api_ref_doc.spdx_id,
                relationship_type=RelationshipType.CONTAINS,
                to=[spdx_atc_snippet.spdx_id],
            )
            spdx_tc = self.TestCaseSPDX(atc.test_case, self.API_SPDX_ID_PREFIX, dbi.session)
            spdx_atc_tc_rel = Relationship(
                spdx_id=f"REL_{spdx_tc.spdx_id}_{spdx_atc_snippet.spdx_id}",
                from_element=spdx_tc.spdx_id,
                completeness=self.get_completeness(atc.coverage),
                relationship_type=RelationshipType.TEST_CASE,
                to=[spdx_atc_snippet.spdx_id],
            )

            self.add_files_to_payload([spdx_atc_snippet])
            self.add_files_to_payload([spdx_tc])
            self.add_files_to_payload([spdx_atc_snippet_rel, spdx_atc_tc_rel])

            # Test Runs
            spdx_trs, spdx_trs_rel = self.get_test_runs(api.id, atc, spdx_tc, dbi)
            self.add_files_to_payload(spdx_trs)
            self.add_files_to_payload(spdx_trs_rel)

        # ApiJustification
        api_justifications = (
            dbi.session.query(ApiJustificationModel).filter(ApiJustificationModel.api_id == api.id).all()
        )
        for aj in api_justifications:
            spdx_aj_snippet = self.SnippetSPDX(aj, dbi.session)
            spdx_aj_snippet_rel = Relationship(
                spdx_id=f"REL_{spdx_api_ref_doc.spdx_id}_{spdx_aj_snippet.spdx_id}",
                from_element=spdx_api_ref_doc.spdx_id,
                relationship_type=RelationshipType.CONTAINS,
                to=[spdx_aj_snippet.spdx_id],
            )
            spdx_j = self.JustificationSPDX(aj.justification, dbi.session)
            spdx_aj_j_rel = Relationship(
                spdx_id=f"REL_{spdx_j.spdx_id}_{spdx_aj_snippet.spdx_id}",
                from_element=spdx_j.spdx_id,
                completeness=self.get_completeness(aj.coverage),
                relationship_type=RelationshipType.DESCRIBES,
                to=[spdx_aj_snippet.spdx_id],
            )

            self.add_files_to_payload([spdx_aj_snippet])
            self.add_files_to_payload([spdx_j])
            self.add_files_to_payload([spdx_aj_snippet_rel, spdx_aj_j_rel])

        # ApiDocument
        api_documents = dbi.session.query(ApiDocumentModel).filter(ApiDocumentModel.api_id == api.id).all()
        for adoc in api_documents:
            spdx_adoc_snippet = self.SnippetSPDX(adoc, dbi.session)
            spdx_adoc_snippet_rel = Relationship(
                spdx_id=f"REL_{spdx_api_ref_doc.spdx_id}_{spdx_adoc_snippet.spdx_id}",
                from_element=spdx_api_ref_doc.spdx_id,
                relationship_type=RelationshipType.CONTAINS,
                to=[spdx_adoc_snippet.spdx_id],
            )
            spdx_doc = self.DocumentSPDX(adoc.document, dbi.session)
            spdx_adoc_doc_rel = Relationship(
                spdx_id=f"REL_{spdx_doc.spdx_id}_{spdx_adoc_snippet.spdx_id}",
                from_element=spdx_doc.spdx_id,
                completeness=self.get_completeness(adoc.coverage),
                relationship_type=self.get_relationship_from_str(adoc.document.spdx_relation),
                to=[spdx_adoc_snippet.spdx_id],
            )

            self.add_files_to_payload([spdx_adoc_snippet])
            self.add_files_to_payload([spdx_doc])
            self.add_files_to_payload([spdx_adoc_snippet_rel, spdx_adoc_doc_rel])

    def export(self, filepath):
        """Export payload into json"""
        json_ld_writer.write_payload(self.payload, filepath)
