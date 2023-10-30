from spdx_tools.spdx.model import (Document, CreationInfo, Checksum, ChecksumAlgorithm, File,
                                    Package, FileType, Relationship, RelationshipType, Snippet)
from spdx_tools.spdx.validation.document_validator import validate_full_spdx_document
from spdx_tools.spdx.writer.write_anything import write_file
import os, sys
import hashlib, json
import datetime


from db import db_orm
from db.models.api import ApiModel
from db.models.api_sw_requirement import ApiSwRequirementModel
from db.models.api_test_specification import ApiTestSpecificationModel
from db.models.api_test_case import ApiTestCaseModel
from db.models.api_justification import ApiJustificationModel
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
        tmp = Snippet(spdx_id=f"API-SR-{asr_dict['relation_id']}",
                           comment=f"Software Requirement mapping a Snippet of Software Specification",
                           file_spdx_id=asr_dict['api']['raw_specification_url'],
                           byte_range=(asr_dict['offset'], asr_dict['offset'] + len(asr_dict['section'])),
                           name=f"Sw Requirement {asr_dict['sw_requirement']['id']} mapping Api snippet {asr_dict['relation_id']}",
                           attribution_texts=[f"section: {asr_dict['section']}",
                                              f"offset: {asr_dict['offset']}",
                                              f"coverage: {asr_dict['coverage']}"
                                              f"version: {asr_dict['version']}",
                                              f"created: {asr_dict['updated_at']}"])
        return tmp

    def ApiTestSpecificationSPDX(self, _ats, _dbsession):
        ats_dict = _ats.as_dict(full_data=True, db_session=_dbsession)

        tmp = Snippet(spdx_id=f"API-TS-{ats_dict['relation_id']}",
                           comment=f"Test Specification mapping a Snippet of Software Specification",
                           file_spdx_id=ats_dict['api']['raw_specification_url'],
                           byte_range=(ats_dict['offset'], ats_dict['offset'] + len(ats_dict['section'])),
                           name=f"Test Specification {ats_dict['test_specification']['id']} mapping Api snippet {ats_dict['relation_id']}",
                           attribution_texts=[f"section: {ats_dict['section']}",
                                              f"offset: {ats_dict['offset']}",
                                              f"coverage: {ats_dict['coverage']}"
                                              f"version: {ats_dict['version']}",
                                              f"created: {ats_dict['updated_at']}"])
        return tmp

    def ApiTestCaseSPDX(self, _atc, _dbsession):
        atc_dict = _atc.as_dict(full_data=True, db_session=_dbsession)

        tmp = Snippet(spdx_id=f"API-TC-{atc_dict['relation_id']}",
                           comment=f"Test Case mapping a Snippet of Software Specification",
                           file_spdx_id=atc_dict['api']['raw_specification_url'],
                           byte_range=(atc_dict['offset'], atc_dict['offset'] + len(atc_dict['section'])),
                           name=f"Test Case {atc_dict['test_case']['id']} mapping Api snippet {atc_dict['relation_id']}",
                           attribution_texts=[f"section: {atc_dict['section']}",
                                              f"offset: {atc_dict['offset']}",
                                              f"coverage: {atc_dict['coverage']}"
                                              f"version: {atc_dict['version']}",
                                              f"created: {atc_dict['updated_at']}"])
        return tmp

    def ApiJustificationSPDX(self, _js, _dbsession):
        js_dict = _js.as_dict(full_data=True, db_session=_dbsession)

        tmp = Snippet(spdx_id=f"API-JUST-{js_dict['relation_id']}",
                      comment=f"Justification mapping a Snippet of Software Specification",
                      file_spdx_id=js_dict['api']['raw_specification_url'],
                      byte_range=(js_dict['offset'], js_dict['offset'] + len(js_dict['section'])),
                      name=f"Justification {js_dict['justification']['id']} mapping Api snippet {js_dict['relation_id']}",
                      attribution_texts=[f"section: {js_dict['section']}",
                                          f"offset: {js_dict['offset']}",
                                          f"version: {js_dict['version']}",
                                          f"created: {js_dict['updated_at']}"])
        return tmp

    def SwRequirementSPDX(self, _sr, _dbsession):
        sr_dict = _sr.as_dict(full_data=True, db_session=_dbsession)

        tmp = File(spdx_id=f"SR-{sr_dict['id']}",
                    name=f"{sr_dict['title']}",
                    checksums=[Checksum(ChecksumAlgorithm.MD5, self.dict_hash(sr_dict))],
                    attribution_texts=[f"title: {sr_dict['title']}",
                                       f"description: {sr_dict['description']}",
                                       f"version: {sr_dict['version']}",
                                       f"created: {sr_dict['updated_at']}",],
                    file_types=[FileType.TEXT],
                    comment="Software Requirement")
        return tmp

    def TestSpecificationSPDX(self, _ts, _dbsession):
        ts_dict = _ts.as_dict(full_data=True, db_session=_dbsession)
        print(f"ts_dict: {ts_dict}")
        tmp = File(spdx_id=f"TS-{ts_dict['id']}",
                   name=f"{ts_dict['title']}",
                   checksums=[Checksum(ChecksumAlgorithm.MD5, self.dict_hash(ts_dict))],
                   attribution_texts=[f"title: {ts_dict['title']}",
                                      f"test_description: {ts_dict['test_description']}",
                                      f"preconditions: {ts_dict['preconditions']}",
                                      f"expected_behavior: {ts_dict['expected_behavior']}",
                                      f"version: {ts_dict['version']}",
                                      f"created: {ts_dict['updated_at']}"],
                   file_types=[FileType.TEXT],
                   comment="Test Specification")
        return tmp

    def TestCaseSPDX(self, _tc, _dbsession):
        tc_dict = _tc.as_dict(full_data=True, db_session=_dbsession)

        tmp = File(spdx_id=f"TC-{tc_dict['id']}",
                   name=f"{tc_dict['title']}",
                   checksums=[Checksum(ChecksumAlgorithm.MD5, self.dict_hash(tc_dict))],
                   attribution_texts=[f"title: {tc_dict['title']}",
                                      f"description: {tc_dict['description']}",
                                      f"repository: {tc_dict['repository']}",
                                      f"relative_path: {tc_dict['relative_path']}",
                                      f"version: {tc_dict['version']}",
                                      f"created: {tc_dict['updated_at']}"],
                   file_types=[FileType.TEXT],
                   comment="Test Case")
        return tmp

    def JustificationSPDX(self, _js, _dbsession):
        js_dict = _js.as_dict(full_data=True, db_session=_dbsession)

        tmp = File(spdx_id=f"JUST-{js_dict['id']}",
                   name=f"{js_dict['description']}",
                   checksums=[Checksum(ChecksumAlgorithm.MD5, self.dict_hash(js_dict))],
                   attribution_texts=[f"description: {js_dict['description']}",
                                      f"version: {js_dict['version']}",
                                      f"created: {js_dict['updated_at']}"],
                   file_types=[FileType.TEXT],
                   comment="Justification")
        return tmp

    def add_api_to_export(self, api_id):
        dbi = db_orm.DbInterface()
        api = dbi.session.query(ApiModel).filter(ApiModel.id == api_id).one()

        api_sw_requirements = dbi.session.query(ApiSwRequirementModel).filter(
            ApiSwRequirementModel.api_id == api_id
        ).all()


        spdx_api = File(spdx_id=f"API-{api.id}",
                        comment=f"Software Component - category: {api.category} - library: {api.library} - library version: {api.library_version}",
                        checksums=[Checksum(ChecksumAlgorithm.MD5, self.dict_hash(api.as_dict()))],
                        name=f"{api.api}")

        self.document.files += [spdx_api]

        # ApiSwRequirement
        for asr in api_sw_requirements:
            #ApiSwRequirement
            spdx_asr = self.ApiSwRequirementSPDX(asr, dbi.session)
            api_asr_rel = Relationship(f"API-{api.id}",
                                      RelationshipType.GENERATES,
                                      f"API-SR-{asr.id}")
            spdx_sr = self.SwRequirementSPDX(asr.sw_requirement, dbi.session)
            asr_sr_rel = Relationship(f"SR-{asr.sw_requirement.id}",
                                      RelationshipType.REQUIREMENT_DESCRIPTION_FOR,
                                      f"API-SR-{asr.id}")

            #SwRequirementTestSpecification
            sr_tss = dbi.session.query(SwRequirementTestSpecificationModel).filter(
                SwRequirementTestSpecificationModel.sw_requirement_mapping_api_id == asr.id
            ).all()
            for sr_ts in sr_tss:
                spdx_ts = self.TestSpecificationSPDX(sr_ts.test_specification, dbi.session)
                asr_ts_rel = Relationship(f"TS-{sr_ts.test_specification.id}",
                                          RelationshipType.TEST_OF,
                                          f"API-SR-{asr.id}")
                self.document.files += [spdx_ts]
                self.document.relationships += [asr_ts_rel]

                # TestSpecificationTestCase
                ts_tcs = dbi.session.query(TestSpecificationTestCaseModel).filter(
                    TestSpecificationTestCaseModel.test_specification_mapping_sw_requirement_id == sr_ts.id
                ).all()
                for ts_tc in ts_tcs:
                    spdx_tc = self.TestCaseSPDX(ts_tc.test_case, dbi.session)
                    asr_tc_rel = Relationship(f"TC-{ts_tc.test_case.id}",
                                              RelationshipType.TEST_CASE_OF,
                                              f"API-SR-{asr.id}")
                    ts_tc_rel = Relationship(f"TS-{sr_ts.test_specification.id}",
                                             RelationshipType.SPECIFICATION_FOR,
                                             f"TC-{ts_tc.test_case.id}",)
                    self.document.files += [spdx_tc]
                    self.document.relationships += [asr_tc_rel, ts_tc_rel]

            self.document.snippets += [spdx_asr]
            self.document.files += [spdx_sr]
            self.document.relationships += [api_asr_rel, asr_sr_rel]

        # ApiTestSpecification
        api_test_specifications = dbi.session.query(ApiTestSpecificationModel).filter(
            ApiTestSpecificationModel.api_id == api_id
        ).all()
        for ats in api_test_specifications:
            spdx_ats = self.ApiTestSpecificationSPDX(ats, dbi.session)
            api_ats_rel = Relationship(f"API-{api.id}",
                                       RelationshipType.GENERATES,
                                       f"API-TS-{ats.id}")
            spdx_ts = self.TestSpecificationSPDX(ats.test_specification, dbi.session)
            ats_ts_rel = Relationship(f"TS-{ats.test_specification.id}",
                                      RelationshipType.TEST_OF,
                                      f"API-TS-{ats.id}")

            # TestSpecificationTestCase
            ts_tcs = dbi.session.query(TestSpecificationTestCaseModel).filter(
                TestSpecificationTestCaseModel.test_specification_mapping_api_id == ats.id
            ).all()
            for ts_tc in ts_tcs:
                spdx_tc = self.TestCaseSPDX(ts_tc.test_case, dbi.session)
                asr_tc_rel = Relationship(f"TC-{ts_tc.test_case.id}",
                                          RelationshipType.TEST_CASE_OF,
                                          f"API-TS-{ats.id}")
                ts_tc_rel = Relationship(f"TS-{ats.test_specification.id}",
                                         RelationshipType.SPECIFICATION_FOR,
                                         f"TC-{ts_tc.test_case.id}", )
                self.document.files += [spdx_tc]
                self.document.relationships += [asr_tc_rel, ts_tc_rel]

        # ApiTestCase
        api_test_cases = dbi.session.query(ApiTestCaseModel).filter(
            ApiTestCaseModel.api_id == api_id
        ).all()
        for atc in api_test_cases:
            spdx_ats = self.ApiTestCaseSPDX(atc, dbi.session)
            api_atc_rel = Relationship(f"API-{api.id}",
                                       RelationshipType.GENERATES,
                                       f"API-TC-{atc.id}")
            spdx_tc = self.TestCaseSPDX(atc.test_case, dbi.session)
            atc_tc_rel = Relationship(f"TC-{atc.test_case.id}",
                                      RelationshipType.TEST_CASE_OF,
                                      f"API-TC-{atc.id}")
            self.document.files += [spdx_tc]
            self.document.relationships += [api_atc_rel, atc_tc_rel]

        # ApiJustification
        api_justifications = dbi.session.query(ApiJustificationModel).filter(
            ApiJustificationModel.api_id == api_id
        ).all()
        for aj in api_justifications:
            spdx_aj = self.ApiJustificationSPDX(aj, dbi.session)
            api_js_rel = Relationship(f"API-{api.id}",
                                       RelationshipType.GENERATES,
                                       f"API-JUST-{aj.id}")
            spdx_j = self.JustificationSPDX(aj.justification, dbi.session)
            aj_j_rel = Relationship(f"JUST-{aj.justification.id}",
                                      RelationshipType.DESCRIBES,
                                      f"API-JUST-{aj.id}")
            self.document.files += [spdx_j]
            self.document.relationships += [api_js_rel, aj_j_rel]

    def export(self, filepath):
        validation_messages = validate_full_spdx_document(self.document)
        for validation_message in validation_messages:
            print(validation_message.validation_message)

        # if there are no validation messages, the document is valid
        # and we can safely serialize it without validating again
        #if not validation_messages:
        write_file(self.document, filepath, validate=False)
