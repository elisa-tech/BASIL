import datetime
import hashlib
import json

from spdx_tools.spdx.model import (Checksum, ChecksumAlgorithm, CreationInfo, Document, File, FileType, Relationship,
                                   RelationshipType, Snippet)
from spdx_tools.spdx.validation.document_validator import validate_full_spdx_document
from spdx_tools.spdx.writer.write_anything import write_file

from db import db_orm
from db.models.api import ApiModel
from db.models.api_justification import ApiJustificationModel
from db.models.api_sw_requirement import ApiSwRequirementModel
from db.models.api_test_case import ApiTestCaseModel
from db.models.api_test_specification import ApiTestSpecificationModel
from db.models.sw_requirement_sw_requirement import SwRequirementSwRequirementModel
from db.models.sw_requirement_test_case import SwRequirementTestCaseModel
from db.models.sw_requirement_test_specification import SwRequirementTestSpecificationModel
from db.models.test_specification_test_case import TestSpecificationTestCaseModel


class SPDXManager():

    document = None

    def __init__(self, document_name):
        ci = CreationInfo(spdx_id=document_name,
                          spdx_version="",
                          name=document_name,
                          document_namespace=document_name,
                          creators=[],
                          created=datetime.datetime.now())
        self.document = Document(ci)

    def dict_hash(self, dictionary) -> str:
        """MD5 hash of a dictionary."""
        dhash = hashlib.md5()
        # We need to sort arguments so {'a': 1, 'b': 2} is
        # the same as {'b': 2, 'a': 1}
        encoded = json.dumps(dictionary, sort_keys=True).encode()
        dhash.update(encoded)
        return dhash.hexdigest()

    def ApiSwRequirementSPDX(self, _asr, _dbsession):
        asr_dict = _asr.as_dict(full_data=True, db_session=_dbsession)
        tmp = Snippet(spdx_id=f"SNIPPET-API-SR-{asr_dict['relation_id']}",
                      comment="Software Requirement mapping a Snippet of Software Specification",
                      file_spdx_id=asr_dict['api']['raw_specification_url'],
                      byte_range=(asr_dict['offset'], asr_dict['offset'] + len(asr_dict['section'])),
                      name=f"Sw Requirement {asr_dict['sw_requirement']['id']} mapping "
                      f"Api snippet {asr_dict['relation_id']}",
                      attribution_texts=[f"section: {asr_dict['section']}",
                                         f"offset: {asr_dict['offset']}",
                                         f"coverage: {asr_dict['coverage']}",
                                         f"version: {asr_dict['version']}",
                                         f"created_at: {asr_dict['updated_at']}"])
        return tmp

    def ApiTestSpecificationSPDX(self, _ats, _dbsession):
        ats_dict = _ats.as_dict(full_data=True, db_session=_dbsession)

        tmp = Snippet(spdx_id=f"SNIPPET-API-TS-{ats_dict['relation_id']}",
                      comment="Test Specification mapping a Snippet of Software Specification",
                      file_spdx_id=ats_dict['api']['raw_specification_url'],
                      byte_range=(ats_dict['offset'], ats_dict['offset'] + len(ats_dict['section'])),
                      name=f"Test Specification {ats_dict['test_specification']['id']} "
                      f"mapping Api snippet {ats_dict['relation_id']}",
                      attribution_texts=[f"section: {ats_dict['section']}",
                                         f"offset: {ats_dict['offset']}",
                                         f"coverage: {ats_dict['coverage']}",
                                         f"version: {ats_dict['version']}",
                                         f"created_at: {ats_dict['updated_at']}"])
        return tmp

    def ApiTestCaseSPDX(self, _atc, _dbsession):
        atc_dict = _atc.as_dict(full_data=True, db_session=_dbsession)

        tmp = Snippet(spdx_id=f"SNIPPET-API-TC-{atc_dict['relation_id']}",
                      comment="Test Case mapping a Snippet of Software Specification",
                      file_spdx_id=atc_dict['api']['raw_specification_url'],
                      byte_range=(atc_dict['offset'], atc_dict['offset'] + len(atc_dict['section'])),
                      name=f"Test Case {atc_dict['test_case']['id']} mapping "
                      f"Api snippet {atc_dict['relation_id']}",
                      attribution_texts=[f"section: {atc_dict['section']}",
                                         f"offset: {atc_dict['offset']}",
                                         f"coverage: {atc_dict['coverage']}",
                                         f"version: {atc_dict['version']}",
                                         f"created_at:{atc_dict['updated_at']}"])
        return tmp

    def ApiJustificationSPDX(self, _js, _dbsession):
        js_dict = _js.as_dict(full_data=True, db_session=_dbsession)

        tmp = Snippet(spdx_id=f"SNIPPET-API-JUST-{js_dict['relation_id']}",
                      comment="Justification mapping a Snippet of Software Specification",
                      file_spdx_id=js_dict['api']['raw_specification_url'],
                      byte_range=(js_dict['offset'], js_dict['offset'] + len(js_dict['section'])),
                      name=f"Justification {js_dict['justification']['id']} mapping "
                           f"Api snippet {js_dict['relation_id']}",
                      attribution_texts=[f"section: {js_dict['section']}",
                                         f"offset: {js_dict['offset']}",
                                         f"version: {js_dict['version']}",
                                         f"created_at: {js_dict['updated_at']}"])
        return tmp

    def SwRequirementSPDX(self, _spdx_id, _sr, _dbsession):
        sr_dict = _sr.as_dict(full_data=True, db_session=_dbsession)

        tmp = File(spdx_id=_spdx_id,
                   name=f"{sr_dict['title']}",
                   checksums=[Checksum(ChecksumAlgorithm.MD5, self.dict_hash(sr_dict))],
                   attribution_texts=[f"id: {sr_dict['id']}",
                                      f"title: {sr_dict['title']}",
                                      f"description: {sr_dict['description']}",
                                      f"version: {sr_dict['version']}",
                                      f"created_at: {sr_dict['updated_at']}",],
                   file_types=[FileType.TEXT],
                   comment="Software Requirement")
        return tmp

    def TestSpecificationSPDX(self, _spdx_id, _ts, _dbsession):
        ts_dict = _ts.as_dict(full_data=True, db_session=_dbsession)
        print(f"ts_dict: {ts_dict}")
        tmp = File(spdx_id=_spdx_id,
                   name=f"{ts_dict['title']}",
                   checksums=[Checksum(ChecksumAlgorithm.MD5, self.dict_hash(ts_dict))],
                   attribution_texts=[f"id: {ts_dict['id']}",
                                      f"title: {ts_dict['title']}",
                                      f"test_description: {ts_dict['test_description']}",
                                      f"preconditions: {ts_dict['preconditions']}",
                                      f"expected_behavior: {ts_dict['expected_behavior']}",
                                      f"version: {ts_dict['version']}",
                                      f"created_at: {ts_dict['updated_at']}"],
                   file_types=[FileType.TEXT],
                   comment="Test Specification")
        return tmp

    def TestCaseSPDX(self, _spdx_id, _tc, _dbsession):
        tc_dict = _tc.as_dict(full_data=True, db_session=_dbsession)

        tmp = File(spdx_id=_spdx_id,
                   name=f"{tc_dict['title']}",
                   checksums=[Checksum(ChecksumAlgorithm.MD5, self.dict_hash(tc_dict))],
                   attribution_texts=[f"id: {tc_dict['id']}",
                                      f"title: {tc_dict['title']}",
                                      f"description: {tc_dict['description']}",
                                      f"repository: {tc_dict['repository']}",
                                      f"relative_path: {tc_dict['relative_path']}",
                                      f"version: {tc_dict['version']}",
                                      f"created_at: {tc_dict['updated_at']}"],
                   file_types=[FileType.TEXT],
                   comment="Test Case")
        return tmp

    def JustificationSPDX(self, _spdx_id, _js, _dbsession):
        js_dict = _js.as_dict(full_data=True, db_session=_dbsession)

        tmp = File(spdx_id=_spdx_id,
                   name=f"{js_dict['description']}",
                   checksums=[Checksum(ChecksumAlgorithm.MD5, self.dict_hash(js_dict))],
                   attribution_texts=[f"id: {js_dict['id']}",
                                      f"description: {js_dict['description']}",
                                      f"version: {js_dict['version']}",
                                      f"created_at: {js_dict['updated_at']}"],
                   file_types=[FileType.TEXT],
                   comment="Justification")
        return tmp

    def get_x_sr_children(self, xsr, dbi):

        files = []
        relationships = []

        if isinstance(xsr, ApiSwRequirementModel):
            mapping_field_id = 'sw_requirement_mapping_api_id'
            mapping_spdx_id = 'API'
        elif isinstance(xsr, SwRequirementSwRequirementModel):
            mapping_field_id = 'sw_requirement_mapping_sw_requirement_id'
            mapping_spdx_id = 'SR'
        else:
            return files, relationships

        # SwRequirementSwRequirementModel
        sr_srs = dbi.session.query(SwRequirementSwRequirementModel).filter(
            getattr(SwRequirementSwRequirementModel, mapping_field_id) == xsr.id
        ).all()
        for sr_sr in sr_srs:
            spdx_sr_id = f'SR-SR-{sr_sr.id}'
            spdx_sr = self.SwRequirementSPDX(spdx_sr_id, sr_sr.sw_requirement, dbi.session)
            sr_sr_rel = Relationship(f"{mapping_spdx_id}-SR-{xsr.id}",
                                     RelationshipType.REQUIREMENT_DESCRIPTION_FOR,
                                     spdx_sr_id)
            files += [spdx_sr]
            relationships += [sr_sr_rel]

            child_files, child_relationships = self.get_x_sr_children(sr_sr, dbi)
            files += child_files
            relationships += child_relationships

        # SwRequirementTestSpecificationModel
        sr_tss = dbi.session.query(SwRequirementTestSpecificationModel).filter(
            getattr(SwRequirementTestSpecificationModel, mapping_field_id) == xsr.id
        ).all()
        for sr_ts in sr_tss:
            spdx_ts_id = f"SR-TS-{sr_ts.id}"
            spdx_ts = self.TestSpecificationSPDX(spdx_ts_id, sr_ts.test_specification, dbi.session)
            asr_ts_rel = Relationship(spdx_ts_id,
                                      RelationshipType.TEST_OF,
                                      f"{mapping_spdx_id}-SR-{xsr.id}")
            files += [spdx_ts]
            relationships += [asr_ts_rel]

            # TestSpecificationTestCaseModel
            ts_tcs = dbi.session.query(TestSpecificationTestCaseModel).filter(
                TestSpecificationTestCaseModel.test_specification_mapping_sw_requirement_id == sr_ts.id
            ).all()
            for ts_tc in ts_tcs:
                spdx_tc_id = f"TS-TC-{ts_tc.id}"
                spdx_tc = self.TestCaseSPDX(spdx_tc_id, ts_tc.test_case, dbi.session)
                ts_tc_rel = Relationship(f"SR-TS-{sr_ts.id}",
                                         RelationshipType.SPECIFICATION_FOR,
                                         spdx_tc_id)
                files += [spdx_tc]
                relationships += [ts_tc_rel]

        # SwRequirementTestCaseModel
        sr_tcs = dbi.session.query(SwRequirementTestCaseModel).filter(
            getattr(SwRequirementTestCaseModel, mapping_field_id) == xsr.id
        ).all()
        for sr_tc in sr_tcs:
            spdx_tc_id = f'SR-TC-{sr_tc.id}'
            spdx_tc = self.TestCaseSPDX(spdx_tc_id, sr_tc.test_case, dbi.session)
            xsr_tc_rel = Relationship(spdx_tc_id,
                                      RelationshipType.TEST_CASE_OF,
                                      f"{mapping_spdx_id}-SR-{xsr.id}")
            files += [spdx_tc]
            relationships += [xsr_tc_rel]

        return files, relationships

    def add_api_to_export(self, api_id):
        dbi = db_orm.DbInterface()
        api = dbi.session.query(ApiModel).filter(ApiModel.id == api_id).one()

        api_sw_requirements = dbi.session.query(ApiSwRequirementModel).filter(
            ApiSwRequirementModel.api_id == api_id
        ).all()

        spdx_api = File(spdx_id=f"API-{api.id}",
                        comment="Software Component",
                        checksums=[Checksum(ChecksumAlgorithm.MD5, self.dict_hash(api.as_dict()))],
                        name=f"{api.api}",
                        attribution_texts=[f"category: {api.category}",
                                           f"library: {api.library}",
                                           f"library_version: {api.library_version}",
                                           f"implementation_file: {api.implementation_file}",
                                           f"implementation_file_from_row: {api.implementation_file_from_row}",
                                           f"implementation_file_to_row: {api.implementation_file_to_row}",
                                           f"raw_specification_url: {api.raw_specification_url}",
                                           f"tags: {api.tags}",
                                           f"created_at: {api.created_at}"],
                        file_types=[FileType.TEXT],
                        )

        self.document.files += [spdx_api]

        # ApiSwRequirement
        for asr in api_sw_requirements:
            # ApiSwRequirement
            spdx_asr_id = f'API-SR-{asr.id}'
            spdx_asr = self.ApiSwRequirementSPDX(asr, dbi.session)
            api_asr_rel = Relationship(f"API-{api.id}",
                                       RelationshipType.GENERATES,
                                       f'SNIPPET-API-SR-{asr.id}')
            spdx_sr = self.SwRequirementSPDX(spdx_asr_id, asr.sw_requirement, dbi.session)
            asr_sr_rel = Relationship(spdx_asr_id,
                                      RelationshipType.REQUIREMENT_DESCRIPTION_FOR,
                                      f'SNIPPET-API-SR-{asr.id}')

            self.document.snippets += [spdx_asr]
            self.document.files += [spdx_sr]
            self.document.relationships += [api_asr_rel, asr_sr_rel]

            child_files, child_relationships = self.get_x_sr_children(asr, dbi)
            self.document.files += child_files
            self.document.relationships += child_relationships

        # ApiTestSpecification
        api_test_specifications = dbi.session.query(ApiTestSpecificationModel).filter(
            ApiTestSpecificationModel.api_id == api_id
        ).all()
        for ats in api_test_specifications:
            spdx_ats_id = f'API-TS-{ats.id}'
            spdx_ats = self.ApiTestSpecificationSPDX(ats, dbi.session)
            api_ats_rel = Relationship(f"API-{api.id}",
                                       RelationshipType.GENERATES,
                                       f"SNIPPET-API-TS-{ats.id}")
            spdx_ts = self.TestSpecificationSPDX(spdx_ats_id, ats.test_specification, dbi.session)
            ats_ts_rel = Relationship(spdx_ats_id,
                                      RelationshipType.TEST_OF,
                                      f"SNIPPET-API-TS-{ats.id}")

            # TestSpecificationTestCase
            ts_tcs = dbi.session.query(TestSpecificationTestCaseModel).filter(
                TestSpecificationTestCaseModel.test_specification_mapping_api_id == ats.id
            ).all()
            for ts_tc in ts_tcs:
                spdx_tc_id = f'TS-TC-{ts_tc.id}'
                spdx_tc = self.TestCaseSPDX(spdx_tc_id, ts_tc.test_case, dbi.session)
                ts_tc_rel = Relationship(spdx_ats_id,
                                         RelationshipType.SPECIFICATION_FOR,
                                         spdx_tc_id)
                self.document.files += [spdx_tc]
                self.document.relationships += [ts_tc_rel]

            self.document.snippets += [spdx_ats]
            self.document.files += [spdx_ts]
            self.document.relationships += [api_ats_rel]
            self.document.relationships += [ats_ts_rel]

        # ApiTestCase
        api_test_cases = dbi.session.query(ApiTestCaseModel).filter(
            ApiTestCaseModel.api_id == api_id
        ).all()
        for atc in api_test_cases:
            spdx_atc_id = f'API-TC-{atc.id}'
            spdx_atc = self.ApiTestCaseSPDX(atc, dbi.session)
            api_atc_rel = Relationship(f"API-{api.id}",
                                       RelationshipType.GENERATES,
                                       f"SNIPPET-API-TC-{atc.id}")
            spdx_tc = self.TestCaseSPDX(spdx_atc_id, atc.test_case, dbi.session)
            atc_tc_rel = Relationship(spdx_atc_id,
                                      RelationshipType.TEST_CASE_OF,
                                      f"SNIPPET-API-TC-{atc.id}")

            self.document.snippets += [spdx_atc]
            self.document.files += [spdx_tc]
            self.document.relationships += [api_atc_rel, atc_tc_rel]

        # ApiJustification
        api_justifications = dbi.session.query(ApiJustificationModel).filter(
            ApiJustificationModel.api_id == api_id
        ).all()
        for aj in api_justifications:
            spdx_aj_id = f"API-JUST-{aj.id}"
            spdx_aj = self.ApiJustificationSPDX(aj, dbi.session)
            api_js_rel = Relationship(f"API-{api.id}",
                                      RelationshipType.GENERATES,
                                      f"SNIPPET-API-JUST-{aj.id}")
            spdx_j = self.JustificationSPDX(spdx_aj_id, aj.justification, dbi.session)
            aj_j_rel = Relationship(spdx_aj_id,
                                    RelationshipType.DESCRIBES,
                                    f"SNIPPET-API-JUST-{aj.id}")

            self.document.snippets += [spdx_aj]
            self.document.files += [spdx_j]
            self.document.relationships += [api_js_rel, aj_j_rel]

    def export(self, filepath):
        validation_messages = validate_full_spdx_document(self.document)
        for validation_message in validation_messages:
            print(validation_message.validation_message)

        # if there are no validation messages, the document is valid
        # and we can safely serialize it without validating again
        # if not validation_messages:
        write_file(self.document, filepath, validate=False)
