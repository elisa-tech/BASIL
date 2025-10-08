import datetime
import hashlib
import json
import logging
import os
import sys
from graphviz import Digraph
from pathlib import Path
from typing import List, Optional, Union

from sqlalchemy import desc

currentdir = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(1, os.path.dirname(currentdir))

from db.db_orm import DbInterface  # noqa E402
from db.models.api import ApiModel  # noqa E402
from db.models.api_document import ApiDocumentModel  # noqa E402
from db.models.api_justification import ApiJustificationModel  # noqa E402
from db.models.api_sw_requirement import ApiSwRequirementModel  # noqa E402
from db.models.api_test_case import ApiTestCaseModel  # noqa E402
from db.models.api_test_specification import ApiTestSpecificationModel  # noqa E402
from db.models.document import DocumentModel  # noqa E402
from db.models.justification import JustificationModel  # noqa E402
from db.models.sw_requirement import SwRequirementModel  # noqa E402
from db.models.sw_requirement_sw_requirement import SwRequirementSwRequirementModel  # noqa E402
from db.models.sw_requirement_test_case import SwRequirementTestCaseModel  # noqa E402
from db.models.sw_requirement_test_specification import SwRequirementTestSpecificationModel  # noqa E402
from db.models.test_case import TestCaseModel  # noqa E402
from db.models.test_run import TestRunModel  # noqa E402
from db.models.test_specification import TestSpecificationModel  # noqa E402
from db.models.test_specification_test_case import TestSpecificationTestCaseModel  # noqa E402
from db.models.user import UserModel  # noqa E402

logger = logging.getLogger(__name__)

# Developed and validated with https://spdx.github.io/spdx-spec/v3.0.1/rdf/schema.json

BASIL_TOOL_URL = "https://github.com/elisa-tech/BASIL"
SPDX_CONTEXT_URL = "https://spdx.org/rdf/3.0.1/spdx-context.jsonld"
DATETIME_STR_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
SPDX_SPEC_VERSION = "3.0.1"


class SPDXMD5Hash:
    def __init__(self, hash_value: str = ""):
        self.hash_value = hash_value

    def to_dict(self):
        return {
            "type": "Hash",
            "algorithm": "md5",
            "hashValue": self.hash_value,
        }


class SPDXCreationInfo:

    def __init__(
        self, spdx_id: str = "", created_by=[], created_using=[], created: datetime.datetime = datetime.datetime.now()
    ):
        self.spdx_id = spdx_id
        self.spec_version = SPDX_SPEC_VERSION
        self._created_by = created_by
        self._created_using = created_using
        self.created = created

    @property
    def created_by(self):
        return self._created_by

    @created_by.setter
    def created_by(self, created_by):
        self._created_by = created_by

    @property
    def created_using(self):
        return self._created_using

    @created_using.setter
    def created_using(self, created_using):
        self._created_using = created_using

    def to_dict(self):
        return {
            "@id": self.spdx_id,
            "type": "CreationInfo",
            "specVersion": self.spec_version,
            "createdBy": [item.spdx_id for item in self.created_by],
            "createdUsing": [item.spdx_id for item in self.created_using],
            "created": self.created.strftime(DATETIME_STR_FORMAT),
        }


class SPDXRelationship:

    relationships = [
        "affects",
        "amendedBy",
        "ancestorOf",
        "availableFrom",
        "configures",
        "contains",
        "coordinatedBy",
        "copiedTo",
        "delegatedTo",
        "dependsOn",
        "descendantOf",
        "describes",
        "doesNotAffect",
        "expandsTo",
        "exploitCreatedBy",
        "fixedBy",
        "fixedIn",
        "foundBy",
        "generates",
        "hasAddedFile",
        "hasAssessmentFor",
        "hasAssociatedVulnerability",
        "hasConcludedLicense",
        "hasDataFile",
        "hasDeclaredLicense",
        "hasDeletedFile",
        "hasDependencyManifest",
        "hasDistributionArtifact",
        "hasDocumentation",
        "hasDynamicLink",
        "hasEvidence",
        "hasExample",
        "hasHost",
        "hasInput",
        "hasMetadata",
        "hasOptionalComponent",
        "hasOptionalDependency",
        "hasOutput",
        "hasPrerequisite",
        "hasProvidedDependency",
        "hasRequirement",
        "hasSpecification",
        "hasStaticLink",
        "hasTest",
        "hasTestCase",
        "hasVariant",
        "invokedBy",
        "modifiedBy",
        "other",
        "packagedBy",
        "patchedBy",
        "publishedBy",
        "reportedBy",
        "republishedBy",
        "serializedInArtifact",
        "testedOn",
        "trainedOn",
        "underInvestigationFor",
        "usesTool",
    ]

    def __init__(
        self,
        spdx_id: str = "",
        from_element=None,  # SPDX object
        to=[],  # list of SPDX objects
        relationship_type: str = "",
        completeness: int = 0,
        creation_info: SPDXCreationInfo = None,
    ):
        self.spdx_id = spdx_id
        self.from_element = from_element
        self.to = to
        self.relationship_type = relationship_type
        self.completeness = completeness
        self.creation_info = creation_info

    def to_dict(self):
        return {
            "type": "Relationship",
            "spdxId": self.spdx_id,
            "from": self.from_element.spdx_id,
            "to": [item.spdx_id for item in self.to],
            "relationshipType": self.relationship_type,
            "completeness": self.completeness,
            "creationInfo": self.creation_info.spdx_id,
        }


class SPDXTool:
    def __init__(self, spdx_id: str = "", name: str = "", creation_info: SPDXCreationInfo = None):
        self.spdx_id = spdx_id
        self.name = name
        self.creation_info = creation_info

    def to_dict(self):
        return {"type": "Tool", "spdxId": self.spdx_id, "name": self.name, "creationInfo": self.creation_info.spdx_id}


class SPDXAnnotation:
    def __init__(
        self,
        spdx_id: str = "",
        name: str = "",
        subject: str = "",
        object: dict = {},
        creation_info: SPDXCreationInfo = None,
    ):
        self.spdx_id = f"{spdx_id}"
        self.name = name
        self.subject = subject
        self.statement = json.dumps(object)
        self.creation_info = creation_info

    def to_dict(self):
        return {
            "type": "Annotation",
            "annotationType": "other",
            "spdxId": self.spdx_id,
            "subject": self.subject.spdx_id,
            "statement": self.statement,
            "creationInfo": self.creation_info.spdx_id,
        }


class SPDXPerson:
    def __init__(self, spdx_id: str = "", name: str = "", creation_info: SPDXCreationInfo = None):
        self.spdx_id = f"{spdx_id}"
        self.name = name
        self.creation_info = creation_info

    def to_dict(self):
        return {
            "type": "Person",
            "spdxId": self.spdx_id,
            "name": self.name,
            "creationInfo": self.creation_info.spdx_id,
        }


class SPDXFile:

    supported_puposes = [
        "application",
        "archive",
        "bom",
        "configuration",
        "container",
        "data",
        "device",
        "deviceDriver",
        "diskImage",
        "documentation",
        "evidence",
        "executable",
        "file",
        "filesystemImage",
        "firmware",
        "framework",
        "install",
        "library",
        "manifest",
        "model",
        "module",
        "operatingSystem",
        "other",
        "patch",
        "platform",
        "requirement",
        "source",
        "specification",
        "test",
    ]

    def __init__(
        self,
        spdx_id: str = "",
        name: str = "",
        comment: str = "",
        description: str = "",
        purpose: str = "",
        copyright_text: str = "",
        verified_using: List[SPDXMD5Hash] = [],
        creation_info: SPDXCreationInfo = None,
    ):

        self.spdx_id = f"{spdx_id}"
        self.name = name
        self.comment = comment
        self.description = description
        self._purpose = purpose if purpose in self.supported_puposes else "other"
        self.copyright_text = copyright_text
        self.verified_using = verified_using
        self.creation_info = creation_info

    @property
    def purpose(self):
        return self._purpose

    @purpose.setter
    def purpose(self, purpose):
        self._purpose = purpose if purpose in self.supported_puposes else "other"

    def to_dict(self):
        return {
            "type": "software_File",
            "spdxId": self.spdx_id,
            "software_copyrightText": "",
            "software_primaryPurpose": self.purpose,
            "name": self.name,
            "comment": self.comment,
            "description": self.description,
            "verifiedUsing": [item.to_dict() for item in self.verified_using],
            "creationInfo": self.creation_info.spdx_id,
        }


class PositiveIntegerRange:
    """beginIntegerRange minimum value is 1
    BASIL snippets are 0 based instead of 1
    so the first char in a text in BASIL has index 0
    while for a beginIntegerRange it is 1"""

    def __init__(self, begin: int = 0, end: int = 0):
        self.beginIntegerRange = begin
        self.endIntegerRange = end

    def to_dict(self):
        return {
            "type": "PositiveIntegerRange",
            "beginIntegerRange": min(self.beginIntegerRange, 1),
            "endIntegerRange": self.endIntegerRange,
        }


class SPDXSnippet:
    def __init__(
        self,
        spdx_id: str = "",
        from_file=None,  # SPDX object
        name: str = "",
        comment: str = "",
        description: str = "",
        byte_range: PositiveIntegerRange = None,
        creation_info: SPDXCreationInfo = None,
    ):
        self.spdx_id = spdx_id
        self.name = name
        self.from_file = from_file
        self.comment = comment
        self.description = description
        self.byte_range = byte_range
        self.creation_info = creation_info

    def to_dict(self):
        return {
            "type": "software_Snippet",
            "spdxId": self.spdx_id,
            "name": self.name,
            "comment": self.comment,
            "description": self.description,
            "software_byteRange": self.byte_range.to_dict(),
            "software_snippetFromFile": self.from_file.spdx_id,
            "creationInfo": self.creation_info.spdx_id,
        }


class SPDXPackage:
    def __init__(
        self,
        spdx_id: str = "",
        name: str = "",
        copyright_text: str = "",
        download_location: str = "",
        verified_using: List[SPDXMD5Hash] = [],
        home_page: str = "",
        primary_purpose: str = "",
        originated_by: List[str] = [],
        creation_info: SPDXCreationInfo = None,
    ):
        self.spdx_id = spdx_id
        self.name = name
        self.copyright_text = copyright_text
        self.download_location = download_location
        self.verified_using = verified_using
        self.home_page = home_page
        self.primary_purpose = primary_purpose
        self.originated_by = originated_by
        self.creation_info = creation_info

    def to_dict(self):
        return {
            "type": "software_Package",
            "spdxId": self.spdx_id,
            "name": self.name,
            "software_copyrightText": self.copyright_text,
            "software_downloadLocation": self.download_location,
            "software_homePage": self.home_page,
            "software_primaryPurpose": self.primary_purpose,
            "verifiedUsing": [item.to_dict() for item in self.verified_using],
            "originatedBy": self.originated_by,
            "creationInfo": self.creation_info.spdx_id,
        }


class SPDXPackageVerificationCode:
    def __init__(self, spdx_id: str = "", name: str = "", creation_info: SPDXCreationInfo = None):
        self.spdx_id = spdx_id
        self.name = name
        self.creation_info = creation_info

    def to_dict(self):
        return {
            "type": "PackageVerificationCode",
            "spdxId": self.spdx_id,
            "name": self.name,
            "creationInfo": self.creation_info.spdx_id,
        }


class SPDXLicense:
    def __init__(self, spdx_id: str = "", license: str = "", creation_info: SPDXCreationInfo = None):
        self.spdx_id = spdx_id
        self.license = license
        self.creation_info = creation_info

    def to_dict(self):
        return {
            "type": "simplelicensing_LicenseExpression",
            "spdxId": self.spdx_id,
            "simplelicensing_licenseExpression": self.license or "NOASSERTION",
            "creationInfo": self.creation_info.spdx_id,
        }


class SPDXDocument:
    def __init__(
        self,
        spdx_id: str = "",
        name: str = "",
        data_license: SPDXLicense = None,
        root_element: List[str] = [],
        creation_info: SPDXCreationInfo = None,
    ):
        self.spdx_id = spdx_id
        self.name = name
        self.data_license = data_license
        self.root_element = root_element
        self.creation_info = creation_info

    def to_dict(self):
        return {
            "type": "SpdxDocument",
            "spdxId": f"spdx:document:{self.spdx_id}",
            "dataLicense": self.data_license.spdx_id,
            "rootElement": self.root_element,
            "name": self.name,
            "creationInfo": self.creation_info.spdx_id,
        }


class SPDXManager:

    sbom = []
    sbom_creation_info = None
    tool = None

    def __init__(
        self,
        user: UserModel = None,
        library_name: str = "",
        apis: List[ApiModel] = None,
        include_test_runs: bool = True,
        test_runs_limit: int = 20,
        dbi: DbInterface = None,
    ):
        self.sbom = []
        self.include_test_runs = include_test_runs
        self.test_runs_limit = test_runs_limit

        spdx_document_id = f"spdx:document:basil:export:{library_name.strip()}"

        self.sbom_creation_info = SPDXCreationInfo(
            spdx_id=self.make_spdx_id("sbom_creation_info"),
            created_by=[],
            created=datetime.datetime.now(),
            created_using="",
        )

        sbom_spdx_person = SPDXPerson(
            spdx_id=f"spdx:person:basil:user:{user.id}",
            name=user.username,
            creation_info=self.sbom_creation_info,
        )

        self.tool = SPDXTool(
            spdx_id=BASIL_TOOL_URL,
            name="BASIL",
            creation_info=self.sbom_creation_info,
        )

        self.sbom_creation_info.created_by = [sbom_spdx_person]
        self.sbom_creation_info.created_using = [self.tool]

        spdx_license = SPDXLicense(
            spdx_id=f"spdx:license:{library_name}",
            license="NOASSERTION",
            creation_info=self.sbom_creation_info,
        )

        # SBOM
        document = SPDXDocument(
            spdx_id=spdx_document_id,
            name=f"BASIL SBOM export for library {library_name}",
            data_license=spdx_license,
            root_element=[],
            creation_info=self.sbom_creation_info,
        )

        # Library
        library_spdx_id = f"spdx:file:basil:library:{library_name}"
        library_dict = {"name": library_name}

        library_hash = self.make_hash_object(data_dict=library_dict)

        library = SPDXFile(
            spdx_id=library_spdx_id,
            name=f"Library {library_name}",
            comment=f"BASIL Library {library_name}",
            description=f"BASIL Library {library_name}",
            purpose="library",
            copyright_text="",
            verified_using=[library_hash],
            creation_info=self.sbom_creation_info,
        )

        library_annotation = SPDXAnnotation(
            spdx_id=f"spdx:annotation:basil:library:{library_name}",
            name=f"Annotation for BASIL Library '{library_name}'",
            subject=library,
            object=library_dict,
            creation_info=self.sbom_creation_info,
        )

        self.add_to_sbom(self.sbom_creation_info)
        self.add_to_sbom(sbom_spdx_person)
        self.add_to_sbom(self.tool)
        self.add_to_sbom(spdx_license)
        self.add_to_sbom(library)
        self.add_to_sbom(library_annotation)
        document.root_element.append(library.spdx_id)

        added_apis = []
        for api in apis:
            api_creation_info, api_person, spdx_api = self.addApi(api, dbi.session)
            added_apis.append(spdx_api)

        if added_apis:
            self.addRelationship(from_element=library, to=added_apis, relationship_type="contains")

        self.add_to_sbom(document)

    def add_to_sbom(self, element):
        """
        Prevent duplicate definition in the sbom.
        That can happen for example with Person
        """
        spdx_id = element.spdx_id
        if not spdx_id:
            return

        if element not in self.sbom:
            # check the element id doesn't exists yet
            # use the internal spdx_id for all items (covers both spdxId and @id in serialized form)
            ids = {item.spdx_id for item in self.sbom}
            if spdx_id not in ids:
                self.sbom.append(element)

    @staticmethod
    def make_spdx_id(identifier: str) -> str:
        """Create a properly formatted SPDX blank node ID for JSON-LD"""
        return f"_:{identifier}"

    def getCreationInfoAndPerson(
        self,
        item_id: str = "",
        created_at: datetime.datetime = datetime.datetime.now(),
        created_by: str = "",
        add_to_sbom: bool = True,
    ):

        creation_info = SPDXCreationInfo(
            spdx_id=self.make_spdx_id(f"creation_info_{item_id}"), created_by=[], created_using=[], created=created_at
        )
        spdx_person_id = f"spdx:person:basil:user:{created_by.id}"
        person = SPDXPerson(
            spdx_id=f"{spdx_person_id}", name=created_by.username, creation_info=self.sbom_creation_info
        )

        creation_info.created_by = [person]
        creation_info.created_using = [self.tool]

        if add_to_sbom:
            self.add_to_sbom(creation_info)
            self.add_to_sbom(person)

        return (creation_info, person)

    def make_hash_object(self, data_dict: dict = {}) -> SPDXMD5Hash:
        """Create a Hash object"""
        dhash = hashlib.md5()
        # We need to sort arguments so {'a': 1, 'b': 2} is
        # the same as {'b': 2, 'a': 1}
        encoded = json.dumps(data_dict, sort_keys=True).encode()
        dhash.update(encoded)
        tmp_hash = SPDXMD5Hash(hash_value=dhash.hexdigest())
        return tmp_hash

    def clean_api_relation_dict(self, relation_dict):
        """Remove unwanted keys from a dictionary of a relation to api"""
        unwanted_keys = ["api", "document", "justification", "sw_requirement", "test_case", "test_specification"]
        for key in unwanted_keys:
            if key in relation_dict.keys():
                relation_dict.pop(key, None)
        return relation_dict

    def getSnippetIndex(self) -> int:
        """Get next id of a relationship"""
        relationships = [item for item in self.sbom if isinstance(item, SPDXSnippet)]
        return len(relationships) + 1

    def getRelationshipIndex(self) -> int:
        """Get next id of a relationship"""
        relationships = [item for item in self.sbom if isinstance(item, SPDXRelationship)]
        return len(relationships) + 1

    def get_completeness(self, coverage: int = -1) -> str:
        """Return RelationshipCompleteness based on the mapping coverage percentage"""
        if coverage >= 100:
            return "complete"
        else:
            if coverage >= 0:
                return "incomplete"
        return "noAssertion"

    def getSnippetFromSBOM(self, snippet: SPDXSnippet):
        """Check if the selected snippet already exists in the SBOM
        return True and the existing SPDXSnippet if it exists, otherwise will return False and the argument SPDXSnippet
        """
        sbom_snippets = [item for item in self.sbom if isinstance(item, SPDXSnippet)]
        for curr_snippet in sbom_snippets:
            if snippet.name == curr_snippet.name:
                if (
                    snippet.byte_range.beginIntegerRange == curr_snippet.byte_range.beginIntegerRange
                    and snippet.byte_range.endIntegerRange == curr_snippet.byte_range.endIntegerRange
                ):
                    return True, curr_snippet
        return False, snippet

    def addSnippet(self, spdx_api_file=None, spdx_api_ref_doc_file=None, mapping=None, dbsession=None):
        """In BASIL, Software Component Reference Document are
        split in Snippets and each Snippet is assigned to work items.
        This function create SPDX Snippet class describing snippet of the reference document
        """
        mapping_to_id_prefix = ""

        if isinstance(mapping, ApiDocumentModel):
            mapping_to_id_prefix = "document"
            mapping_to_id = mapping.document_id
        elif isinstance(mapping, ApiSwRequirementModel):
            mapping_to_id_prefix = "software-requirement"
            mapping_to_id = mapping.sw_requirement_id
        elif isinstance(mapping, ApiTestSpecificationModel):
            mapping_to_id_prefix = "test-specification"
            mapping_to_id = mapping.test_specification_id
        elif isinstance(mapping, ApiTestCaseModel):
            mapping_to_id_prefix = "test-case"
            mapping_to_id = mapping.test_case_id
        elif isinstance(mapping, ApiJustificationModel):
            mapping_to_id_prefix = "justification"
            mapping_to_id = mapping.justification_id

        mapping_dict = mapping.as_dict(full_data=True, db_session=dbsession)
        api_dict = mapping_dict["api"]
        api = api_dict["api"]
        api_id = api_dict["id"]
        relation_id = mapping_dict["relation_id"]
        mapping_dict = self.clean_api_relation_dict(mapping_dict)

        snippet_id = f"spdx:snippet:api:{api_id}:{self.getSnippetIndex()}"

        creation_info, person = self.getCreationInfoAndPerson(
            item_id=snippet_id, created_by=mapping.created_by, created_at=mapping.created_at, add_to_sbom=True
        )

        snippet = SPDXSnippet(
            spdx_id=snippet_id,
            from_file=spdx_api_ref_doc_file,
            name=mapping.api.raw_specification_url,
            comment=f"Snippet of api {api} reference document",
            byte_range=PositiveIntegerRange(
                mapping_dict["offset"] + 1, mapping_dict["offset"] + len(mapping_dict["section"]) + 1
            ),
            creation_info=creation_info,
        )

        snippet_annotation = SPDXAnnotation(
            spdx_id=f"spdx:annotation:snippet:api:"
            f"{api_id}:{mapping_to_id_prefix}:{mapping_to_id}:relation-id:{relation_id}",
            name=f"Annotation for BASIL API {api} snippet",
            subject=snippet,
            object=mapping_dict,
            creation_info=creation_info,
        )

        snippet_in_sbom, sbom_snippet = self.getSnippetFromSBOM(snippet=snippet)

        if not snippet_in_sbom:
            self.add_to_sbom(sbom_snippet)
            self.add_to_sbom(snippet_annotation)

        self.addRelationship(
            from_element=spdx_api_file,
            to=[sbom_snippet],
            relationship_type="contains",
            completeness_percentage=mapping.coverage,
        )

        return sbom_snippet

    def addApi(self, api=None, dbsession=None):
        """This function create SPDX File class describing a BASIL Software Component"""
        api_dict = api.as_dict(full_data=True, db_session=dbsession)
        api_dict["__tablename__"] = api.__tablename__

        file_api_hash = self.make_hash_object(data_dict=api_dict)
        file_api_id = f"spdx:file:basil:api:{api_dict['id']}"

        creation_info, person = self.getCreationInfoAndPerson(
            item_id=file_api_id, created_by=api.created_by, created_at=api.created_at, add_to_sbom=True
        )

        file_api = SPDXFile(
            spdx_id=file_api_id,
            name=api.api,
            comment=f"BASIL Software Component id {api.id}",
            description=f"BASIL Software Component id {api.id}",
            purpose="module",
            copyright_text="",
            verified_using=[file_api_hash],
            creation_info=creation_info,
        )

        file_api_annotation = SPDXAnnotation(
            spdx_id=f"spdx:annotation:basil:api:{api_dict['id']}",
            name=f"Annotation for BASIL API {api.api} with ID {api.id}",
            subject=file_api,
            object=api_dict,
            creation_info=creation_info,
        )

        # Reference Document
        file_api_ref_doc_id = f"spdx:file:basil:api:reference-document:{api_dict['id']}"
        file_api_ref_doc_dict = {"url": api.raw_specification_url, "content": ""}
        file_api_ref_doc_hash = self.make_hash_object(data_dict=file_api_ref_doc_dict)
        file_api_ref_doc = SPDXFile(
            spdx_id=file_api_ref_doc_id,
            name=api.raw_specification_url,
            comment=f"BASIL Reference Document for Software Component {api.api}",
            description=f"BASIL Reference Document for Software Component {api.api} of library {api.library}",
            purpose="specification",
            copyright_text="",
            verified_using=[file_api_ref_doc_hash],
            creation_info=creation_info,
        )

        file_api_ref_doc_annotation = SPDXAnnotation(
            spdx_id=f"spdx:annotation:basil:api:reference-document:{api_dict['id']}",
            name=f"Annotation for BASIL Reference Document for API {api.api} with url {api.raw_specification_url}",
            subject=file_api_ref_doc,
            object=file_api_ref_doc_dict,
            creation_info=creation_info,
        )

        self.add_to_sbom(file_api)
        self.add_to_sbom(file_api_annotation)

        self.add_to_sbom(file_api_ref_doc)
        self.add_to_sbom(file_api_ref_doc_annotation)

        self.addRelationship(from_element=file_api, to=[file_api_ref_doc], relationship_type="hasDocumentation")

        self.addApiSwRequirements(spdx_api=file_api, spdx_api_ref_doc=file_api_ref_doc, api=api, dbsession=dbsession)

        self.addApiTestSpecifications(
            spdx_api=file_api, spdx_api_ref_doc=file_api_ref_doc, api=api, dbsession=dbsession
        )

        self.addApiTestCases(spdx_api=file_api, spdx_api_ref_doc=file_api_ref_doc, api=api, dbsession=dbsession)

        self.addApiDocuments(spdx_api=file_api, spdx_api_ref_doc=file_api_ref_doc, api=api, dbsession=dbsession)

        self.addApiJustifications(spdx_api=file_api, spdx_api_ref_doc=file_api_ref_doc, api=api, dbsession=dbsession)
        return (creation_info, person, file_api)

    def addRelationship(
        self, from_element: str = "", to: List[str] = [], relationship_type: str = "", completeness_percentage: int = 0
    ):
        relationship = SPDXRelationship(
            spdx_id=f"spdx:relationship:{self.getRelationshipIndex()}",
            from_element=from_element,
            to=to,
            relationship_type=relationship_type,
            completeness=self.get_completeness(completeness_percentage),
            creation_info=self.sbom_creation_info,
        )
        self.add_to_sbom(relationship)

    def addSwRequirement(self, software_requirement: SwRequirementModel = None, dbsession=None):
        """This function create SPDX File class describing a BASIL Software Requirement"""

        sr_dict = software_requirement.as_dict(full_data=True, db_session=dbsession)
        sr_dict["__tablename__"] = software_requirement.__tablename__
        sr_id = f"spdx:file:basil:software-requirement:{software_requirement.id}"
        sr_hash = self.make_hash_object(data_dict=sr_dict)

        creation_info, person = self.getCreationInfoAndPerson(
            item_id=sr_id,
            created_by=software_requirement.created_by,
            created_at=software_requirement.created_at,
            add_to_sbom=True,
        )

        sr_file = SPDXFile(
            spdx_id=sr_id,
            name=software_requirement.title,
            comment=f"BASIL Software Requirement ID {software_requirement.id}",
            description=software_requirement.description,
            purpose="requirement",
            copyright_text="",
            verified_using=[sr_hash],
            creation_info=creation_info,
        )

        sr_annotation = SPDXAnnotation(
            spdx_id=f"spdx:annotation:basil:software-requirement:{software_requirement.id}",
            name=f"Annotation for BASIL Software Requirement {software_requirement.id}",
            subject=sr_file,
            object=sr_dict,
            creation_info=creation_info,
        )

        self.add_to_sbom(sr_file)
        self.add_to_sbom(sr_annotation)
        return sr_file

    def addTestSpecification(self, test_specification: TestSpecificationModel = None, dbsession=None):
        """This function create SPDX File class describing a BASIL Test Specification"""
        ts_dict = test_specification.as_dict(full_data=True, db_session=dbsession)
        ts_dict["__tablename__"] = test_specification.__tablename__
        ts_id = f"spdx:file:basil:test-specification:{test_specification.id}"
        ts_hash = self.make_hash_object(data_dict=ts_dict)

        creation_info, person = self.getCreationInfoAndPerson(
            item_id=ts_id,
            created_by=test_specification.created_by,
            created_at=test_specification.created_at,
            add_to_sbom=True,
        )

        ts_file = SPDXFile(
            spdx_id=ts_id,
            name=test_specification.title,
            comment=f"BASIL Test Specification ID {test_specification.id}",
            description=test_specification.test_description,
            purpose="specification",
            copyright_text="",
            verified_using=[ts_hash],
            creation_info=creation_info,
        )

        ts_annotation = SPDXAnnotation(
            spdx_id=f"spdx:annotation:basil:test-specification:{test_specification.id}",
            name=f"Annotation for BASIL Test Specification {test_specification.id}",
            subject=ts_file,
            object=ts_dict,
            creation_info=creation_info,
        )

        self.add_to_sbom(ts_file)
        self.add_to_sbom(ts_annotation)
        return ts_file

    def addTestCase(self, test_case: TestCaseModel = None, dbsession=None):
        """This function create SPDX File class describing a BASIL Test Case"""
        tc_dict = test_case.as_dict(full_data=True, db_session=dbsession)
        tc_dict["__tablename__"] = test_case.__tablename__
        tc_id = f"spdx:file:basil:test-case:{test_case.id}"
        tc_hash = self.make_hash_object(data_dict=tc_dict)

        creation_info, person = self.getCreationInfoAndPerson(
            item_id=tc_id, created_by=test_case.created_by, created_at=test_case.created_at, add_to_sbom=True
        )

        tc_file = SPDXFile(
            spdx_id=tc_id,
            name=test_case.title,
            comment=f"BASIL Test Case ID {test_case.id}",
            description=test_case.description,
            purpose="test",
            copyright_text="",
            verified_using=[tc_hash],
            creation_info=creation_info,
        )

        tc_annotation = SPDXAnnotation(
            spdx_id=f"spdx:annotation:basil:test-case:{test_case.id}",
            name=f"Annotation for BASIL Test Case {test_case.id}",
            subject=tc_file,
            object=tc_dict,
            creation_info=creation_info,
        )

        self.add_to_sbom(tc_file)
        self.add_to_sbom(tc_annotation)
        return tc_file

    def addDocument(self, document: DocumentModel = None, dbsession=None):
        """This function create SPDX File class describing a BASIL Document"""
        doc_dict = document.as_dict(full_data=True, db_session=dbsession)
        doc_dict["__tablename__"] = document.__tablename__
        doc_id = f"spdx:file:basil:document:{document.id}"
        doc_hash = self.make_hash_object(data_dict=doc_dict)

        creation_info, person = self.getCreationInfoAndPerson(
            item_id=doc_id, created_by=document.created_by, created_at=document.created_at, add_to_sbom=True
        )

        doc_file = SPDXFile(
            spdx_id=doc_id,
            name=document.title,
            comment=f"BASIL Document ID {document.id}",
            description=document.description,
            purpose="documentation",
            copyright_text="",
            verified_using=[doc_hash],
            creation_info=creation_info,
        )

        doc_annotation = SPDXAnnotation(
            spdx_id=f"spdx:annotation:basil:document:{document.id}",
            name=f"Annotation for BASIL Document {document.id}",
            subject=doc_file,
            object=doc_dict,
            creation_info=creation_info,
        )

        self.add_to_sbom(doc_file)
        self.add_to_sbom(doc_annotation)
        return doc_file

    def addJustification(self, justification: JustificationModel = None, dbsession=None):
        """This function create SPDX File class describing a BASIL Document"""
        js_dict = justification.as_dict(full_data=True, db_session=dbsession)
        js_dict["__tablename__"] = justification.__tablename__
        js_id = f"spdx:file:basil:justification:{justification.id}"
        js_hash = self.make_hash_object(data_dict=js_dict)

        creation_info, person = self.getCreationInfoAndPerson(
            item_id=js_id,
            created_by=justification.created_by,
            created_at=justification.created_at,
            add_to_sbom=True,
        )

        js_file = SPDXFile(
            spdx_id=js_id,
            name=f"justification {justification.id}",
            comment=f"BASIL Justification ID {justification.id}",
            description=justification.description,
            purpose="evidence",
            copyright_text="",
            verified_using=[js_hash],
            creation_info=creation_info,
        )

        js_annotation = SPDXAnnotation(
            spdx_id=f"spdx:annotation:basil:justification:{justification.id}",
            name=f"Annotation for BASIL Justification {justification.id}",
            subject=js_file,
            object=js_dict,
            creation_info=creation_info,
        )

        self.add_to_sbom(js_file)
        self.add_to_sbom(js_annotation)
        return js_file

    def addTestRuns(self, spdx_tc: SPDXFile = None, mapping_to: str = "", mapping_id: int = 0, dbsession=None):
        if not self.include_test_runs:
            logger.warning("Skip Test Runs as per export configuration")

        added_test_runs = []
        test_runs_query = (
            dbsession.query(TestRunModel)
            .filter(TestRunModel.mapping_to == mapping_to)
            .filter(TestRunModel.mapping_id == mapping_id)
            .order_by(desc(TestRunModel.id))
        )

        if self.test_runs_limit > 0:
            logger.info(f"Limiting test runs to {self.test_runs_limit} as per export configuration")
            test_runs_query = test_runs_query.limit(self.test_runs_limit)

        test_runs = test_runs_query.all()

        for test_run in test_runs:
            tmp = self.addTestRun(test_run=test_run, dbsession=dbsession)
            added_test_runs.append(tmp)

        if added_test_runs:
            self.addRelationship(from_element=spdx_tc, to=added_test_runs, relationship_type="hasEvidence")

    def addTestRun(self, test_run: TestRunModel = None, dbsession=None):
        """This function create SPDX File class describing a BASIL Test Run"""
        tr_dict = test_run.as_dict(full_data=True)
        tr_dict["__tablename__"] = test_run.__tablename__
        tr_id = f"spdx:file:basil:test-run:{test_run.id}"
        tr_hash = self.make_hash_object(data_dict=tr_dict)

        creation_info, person = self.getCreationInfoAndPerson(
            item_id=tr_id, created_by=test_run.created_by, created_at=test_run.created_at, add_to_sbom=True
        )

        tr_file = SPDXFile(
            spdx_id=tr_id,
            name=test_run.title,
            comment=f"BASIL Test Run ID {test_run.id}",
            description=test_run.notes,
            purpose="evidence",
            copyright_text="",
            verified_using=[tr_hash],
            creation_info=creation_info,
        )

        tr_annotation = SPDXAnnotation(
            spdx_id=f"spdx:annotation:basil:test-run:{test_run.id}",
            name=f"Annotation for BASIL Test Run {test_run.id}",
            subject=tr_file,
            object=tr_dict,
            creation_info=creation_info,
        )

        self.add_to_sbom(tr_file)
        self.add_to_sbom(tr_annotation)
        return tr_file

    def addSoftwareRequirementNestedElements(
        self,
        api: ApiModel = None,
        xsr: Optional[Union[ApiSwRequirementModel, SwRequirementSwRequirementModel]] = None,
        spdx_sr: SPDXFile = None,  # SPDX object of SwRequirement from xsr.sw_requriement
        dbsession=None,
    ):
        """In BASIL user can create a complex hierarchy of Software Requirements.
        Moreover we can assign other work items to each Software Requirement in the chain.
        This method navigate the hierarchy and return all the work items

        :param api: software component where the mapping is defined
        :param xsr: Sw Requirement mapping model instance
        :param spdx_sr: SwRequirementSPDX instance
        :param dbi: Database interface instance
        :return:
        """
        if isinstance(xsr, ApiSwRequirementModel):
            mapping_field = f"{ApiSwRequirementModel.__tablename__}"
            mapping_field_id = f"{mapping_field}_id"
        elif isinstance(xsr, SwRequirementSwRequirementModel):
            mapping_field = f"{SwRequirementSwRequirementModel.__tablename__}"
            mapping_field_id = f"{mapping_field}_id"
        else:
            return

        # SwRequirementSwRequirementModel
        sr_srs = (
            dbsession.query(SwRequirementSwRequirementModel)
            .filter(getattr(SwRequirementSwRequirementModel, mapping_field_id) == xsr.id)
            .all()
        )
        for sr_sr in sr_srs:
            spdx_sr_sr = self.addSwRequirement(software_requirement=sr_sr.sw_requirement, dbsession=dbsession)
            self.addRelationship(
                from_element=spdx_sr,
                to=[spdx_sr_sr],
                relationship_type="hasRequirement",
                completeness_percentage=xsr.coverage,
            )

            # SwRequirementTestSpecification
            self.addSwRequirementTestSpecifications(
                spdx_sr=spdx_sr_sr, mapping_to=mapping_field, mapping_id=xsr.id, dbsession=dbsession
            )

            # SwRequirementTestCases
            self.addSwRequirementTestCases(
                spdx_sr=spdx_sr_sr, mapping_to=mapping_field, mapping_id=xsr.id, dbsession=dbsession
            )

            self.addSoftwareRequirementNestedElements(api=api, xsr=sr_sr, spdx_sr=spdx_sr_sr, dbsession=dbsession)

    def addApiSwRequirements(self, spdx_api=None, spdx_api_ref_doc=None, api: ApiModel = None, dbsession=None):
        """Collect all the work items of a BASIL Software Component and their relationships
        and add them to the class payload"""

        # ApiSwRequirement
        api_sw_requirements = (
            dbsession.query(ApiSwRequirementModel).filter(ApiSwRequirementModel.api_id == api.id).all()
        )
        for asr in api_sw_requirements:
            # ApiSwRequirement
            spdx_asr_snippet = self.addSnippet(
                spdx_api_file=spdx_api, spdx_api_ref_doc_file=spdx_api_ref_doc, mapping=asr, dbsession=dbsession
            )
            spdx_sr = self.addSwRequirement(software_requirement=asr.sw_requirement, dbsession=dbsession)
            self.addRelationship(
                from_element=spdx_asr_snippet,
                to=[spdx_sr],
                relationship_type="hasRequirement",
                completeness_percentage=asr.coverage,
            )

            self.addSoftwareRequirementNestedElements(api=api, xsr=asr, spdx_sr=spdx_sr, dbsession=dbsession)

    def addApiTestSpecifications(self, spdx_api=None, spdx_api_ref_doc=None, api: ApiModel = None, dbsession=None):
        """..."""

        # ApiTestSpecifications
        api_test_specification = (
            dbsession.query(ApiTestSpecificationModel).filter(ApiTestSpecificationModel.api_id == api.id).all()
        )
        for ats in api_test_specification:
            # ApiTestSpecification
            spdx_ats_snippet = self.addSnippet(
                spdx_api_file=spdx_api, spdx_api_ref_doc_file=spdx_api_ref_doc, mapping=ats, dbsession=dbsession
            )
            spdx_ts = self.addTestSpecification(test_specification=ats.test_specification, dbsession=dbsession)
            self.addRelationship(
                from_element=spdx_ats_snippet,
                to=[spdx_ts],
                relationship_type="hasSpecification",
                completeness_percentage=ats.coverage,
            )

            # TestSpecificationTestCases mapping to ApiTestSpecification
            mapping_to = ApiTestSpecificationModel.__tablename__
            self.addTestSpecificationTestCases(
                spdx_ts=spdx_ts, mapping_to=mapping_to, mapping_id=ats.id, dbsession=dbsession
            )

    def addSwRequirementTestSpecifications(
        self, spdx_sr=None, mapping_to: str = "", mapping_id: int = 0, dbsession=None
    ):

        if mapping_to not in [ApiSwRequirementModel.__tablename__, SwRequirementSwRequirementModel.__tablename__]:
            return

        mapping_field_id = f"{mapping_to}_id"

        # SwRequirementTestSpecificationModel
        sr_tss = (
            dbsession.query(SwRequirementTestSpecificationModel)
            .filter(getattr(SwRequirementTestSpecificationModel, mapping_field_id) == mapping_id)
            .all()
        )
        for sr_ts in sr_tss:
            spdx_ts = self.addTestSpecification(test_specification=sr_ts.test_specification, dbsession=dbsession)
            self.addRelationship(
                from_element=spdx_sr,
                to=[spdx_ts],
                relationship_type="hasSpecification",
                completeness_percentage=sr_ts.coverage,
            )

            # TestSpecificationTestCaseModel
            self.addTestSpecificationTestCases(
                spdx_ts=spdx_ts, mapping_to=sr_ts.__tablename__, mapping_id=sr_ts.id, dbsession=dbsession
            )

    def addSwRequirementTestCases(self, spdx_sr=None, mapping_to: str = "", mapping_id: int = 0, dbsession=None):
        if mapping_to not in [ApiSwRequirementModel.__tablename__, SwRequirementSwRequirementModel.__tablename__]:
            return

        mapping_field_id = f"{mapping_to}_id"
        sw_requirement_test_cases = (
            dbsession.query(SwRequirementTestCaseModel)
            .filter(getattr(SwRequirementTestCaseModel, mapping_field_id) == mapping_id)
            .all()
        )

        for sr_tc in sw_requirement_test_cases:
            spdx_tc = self.addTestCase(test_case=sr_tc.test_case, dbsession=dbsession)
            self.addRelationship(
                from_element=spdx_sr, to=[spdx_tc], relationship_type="hasTest", completeness_percentage=sr_tc.coverage
            )

            # Test Runs
            self.addTestRuns(
                spdx_tc=spdx_tc,
                mapping_to=SwRequirementTestCaseModel.__tablename__,
                mapping_id=sr_tc.id,
                dbsession=dbsession,
            )

    def addTestSpecificationTestCases(self, spdx_ts=None, mapping_to: str = "", mapping_id: int = 0, dbsession=None):
        if mapping_to == ApiTestSpecificationModel.__tablename__:
            test_specification_test_cases = (
                dbsession.query(TestSpecificationTestCaseModel)
                .filter(TestSpecificationTestCaseModel.test_specification_mapping_api_id == mapping_id)
                .all()
            )
        elif mapping_to == SwRequirementTestSpecificationModel.__tablename__:
            test_specification_test_cases = (
                dbsession.query(TestSpecificationTestCaseModel)
                .filter(TestSpecificationTestCaseModel.test_specification_mapping_sw_requirement_id == mapping_id)
                .all()
            )
        else:
            return

        for ts_tc in test_specification_test_cases:
            spdx_tc = self.addTestCase(test_case=ts_tc.test_case, dbsession=dbsession)
            self.addRelationship(
                from_element=spdx_ts, to=[spdx_tc], relationship_type="hasTest", completeness_percentage=ts_tc.coverage
            )

            # Test Runs
            self.addTestRuns(
                spdx_tc=spdx_tc,
                mapping_to=TestSpecificationTestCaseModel.__tablename__,
                mapping_id=ts_tc.id,
                dbsession=dbsession,
            )

    def addApiTestCases(self, spdx_api=None, spdx_api_ref_doc=None, api: ApiModel = None, dbsession=None):
        # ApiTestCases
        api_test_cases = dbsession.query(ApiTestCaseModel).filter(ApiTestCaseModel.api_id == api.id).all()
        for atc in api_test_cases:
            # ApiTestCase
            spdx_atc_snippet = self.addSnippet(
                spdx_api_file=spdx_api, spdx_api_ref_doc_file=spdx_api_ref_doc, mapping=atc, dbsession=dbsession
            )
            spdx_tc = self.addTestCase(test_case=atc.test_case, dbsession=dbsession)
            self.addRelationship(
                from_element=spdx_atc_snippet,
                to=[spdx_tc],
                relationship_type="hasTest",
                completeness_percentage=atc.coverage,
            )

            # Test Runs
            self.addTestRuns(
                spdx_tc=spdx_tc, mapping_to=ApiTestCaseModel.__tablename__, mapping_id=atc.id, dbsession=dbsession
            )

    def addApiDocuments(self, spdx_api=None, spdx_api_ref_doc=None, api: ApiModel = None, dbsession=None):
        # ApiDocuments
        api_documents = dbsession.query(ApiDocumentModel).filter(ApiDocumentModel.api_id == api.id).all()
        for adoc in api_documents:
            # ApiDocument
            spdx_adoc_snippet = self.addSnippet(
                spdx_api_file=spdx_api, spdx_api_ref_doc_file=spdx_api_ref_doc, mapping=adoc, dbsession=dbsession
            )
            spdx_doc = self.addDocument(document=adoc.document, dbsession=dbsession)
            self.addRelationship(
                from_element=spdx_adoc_snippet,
                to=[spdx_doc],
                relationship_type="hasDocumentation",  # TODO: Read the relationship from the document mapping
                completeness_percentage=adoc.coverage,
            )

    def addApiJustifications(self, spdx_api=None, spdx_api_ref_doc=None, api: ApiModel = None, dbsession=None):
        # ApiJustifications
        api_justifications = (
            dbsession.query(ApiJustificationModel).filter(ApiJustificationModel.api_id == api.id).all()
        )
        for ajs in api_justifications:
            # ApiJustification
            spdx_ajs_snippet = self.addSnippet(
                spdx_api_file=spdx_api, spdx_api_ref_doc_file=spdx_api_ref_doc, mapping=ajs, dbsession=dbsession
            )
            spdx_js = self.addJustification(justification=ajs.justification, dbsession=dbsession)
            self.addRelationship(
                from_element=spdx_ajs_snippet,
                to=[spdx_js],
                relationship_type="hasEvidence",
                completeness_percentage=ajs.coverage,
            )

    def generate_diagraph(self, output_file: str = ""):
        """
        Generate a directed graph from a list of edges and save it as a PNG.

        Parameters:
        - edges: list of dicts with keys 'from', 'to', and 'type'
        - output_file: output PNG file name
        """

        def get_file_node_color(node):
            purpose_colors = {
                "library": "brown",
                "snippet": "yellow",
                "reference document": "magenta",
                "software component": "gray",
                "software requirement": "red",
                "justification": "green",
                "document": "cyan",
                "test specification": "blue",
                "test case": "orange",
                "test run": "purple",
            }

            if hasattr(node, "comment"):
                for cKey in purpose_colors.keys():
                    if cKey in node.comment.lower():
                        return purpose_colors[cKey]
            return "white"

        # Track added edges
        added_edges = set()

        # Function to safely add edges
        def add_edge(src, dst, label):
            key = (src, dst, label)
            if key not in added_edges:
                added_edges.add(key)

        # Create a directed graph
        dot = Digraph(format="png")
        dot.attr(rankdir="TB")
        added_nodes = {}

        # Add edges with appropriate colors
        relationships = [item for item in self.sbom if isinstance(item, SPDXRelationship)]

        for relationship in relationships:
            if not [item for item in relationship.to if isinstance(item, SPDXFile)]:
                continue

            for to_relationship in relationship.to:
                from_node = relationship.from_element
                from_node_str = from_node.spdx_id.replace(":", "_")
                from_color = get_file_node_color(from_node)

                to_node = to_relationship
                to_node_str = to_node.spdx_id.replace(":", "_")
                to_color = get_file_node_color(to_node)

                # Add 'from' node with color based on type
                if from_node_str not in added_nodes:
                    dot.node(from_node_str, style="filled", fillcolor=from_color)
                    added_nodes[from_node_str] = from_color

                # Add 'to' node with color based on type
                if to_node_str not in added_nodes:
                    dot.node(to_node_str, style="filled", fillcolor=to_color)
                    added_nodes[to_node_str] = to_color

                if isinstance(to_node, SPDXSnippet):
                    from_file_str = to_node.from_file.spdx_id.replace(":", "_")
                    if from_file_str not in added_nodes:
                        dot.node(from_file_str, style="filled", fillcolor="yellow")
                        added_nodes[from_file_str] = "yellow"
                    add_edge(from_file_str, to_node_str, "contains")

                if isinstance(from_node, SPDXSnippet):
                    from_file_str = from_node.from_file.spdx_id.replace(":", "_")
                    if from_file_str not in added_nodes:
                        dot.node(from_file_str, style="filled", fillcolor="yellow")
                        added_nodes[from_file_str] = "yellow"
                    add_edge(from_file_str, from_node_str, "contains")

                # Add edge without special color
                add_edge(from_node_str, to_node_str, label=relationship.relationship_type)

        # Populate dot edges
        for edge in sorted(added_edges):
            dot.edge(edge[0], edge[1], label=edge[2])

        # --- Legend Subgraph ---
        legend = Digraph(name="cluster_legend")
        legend.attr(label="Legend", fontsize="12", style="dashed")
        legend.attr("node", shape="box", style="filled", width="1")

        # Create legend nodes
        legend.node("library", label="Library", shape="box", style="filled", fillcolor="brown")
        legend.node("software_component", label="Software Component", shape="box", style="filled", fillcolor="gray")
        legend.node("reference_document", label="Reference Document", shape="box", style="filled", fillcolor="magenta")
        legend.node("snippet", label="Snippet", shape="box", style="filled", fillcolor="yellow")
        legend.node("justification", label="Justification", shape="box", style="filled", fillcolor="green")
        legend.node("document", label="Document", shape="box", style="filled", fillcolor="cyan")
        legend.node("software_requirement", label="Software Requirement", shape="box", style="filled", fillcolor="red")
        legend.node("test_specification", label="Test Specification", shape="box", style="filled", fillcolor="blue")
        legend.node("test_case", label="Test Case", shape="box", style="filled", fillcolor="orange")
        legend.node("test_run", label="Test Run", shape="box", style="filled", fillcolor="purple")

        # Stack legend nodes vertically
        legend.edge("library", "software_component", style="invis", weight="100")
        legend.edge("software_component", "reference_document", style="invis", weight="100")
        legend.edge("reference_document", "snippet", style="invis", weight="100")
        legend.edge("snippet", "justification", style="invis", weight="100")
        legend.edge("justification", "document", style="invis", weight="100")
        legend.edge("document", "software_requirement", style="invis", weight="100")
        legend.edge("software_requirement", "test_specification", style="invis", weight="100")
        legend.edge("test_specification", "test_case", style="invis", weight="100")
        legend.edge("test_case", "test_run", style="invis", weight="100")

        dot.subgraph(legend)

        dot_filepath = f"{output_file}.dot"
        logger.info(f"Creating .dot file at {dot_filepath}")
        with open(dot_filepath, "w") as f:
            f.write(dot.source)

        # Save to file
        dot.render(filename=output_file, cleanup=True)

    def export(self, filepath):
        """Export payload into json"""
        json_data = {"@context": SPDX_CONTEXT_URL, "@graph": []}

        for item in self.sbom:
            json_data["@graph"].append(item.to_dict())

        json_data["@graph"] = sorted(json_data["@graph"], key=lambda d: d["type"], reverse=False)

        if not filepath.endswith(".jsonld"):
            filepath += ".jsonld"

        try:
            with open(filepath, "w") as f:
                json.dump(json_data, f, indent=2)

            latest_diagraph_filepath = Path(filepath).with_name("latest")

            self.generate_diagraph(latest_diagraph_filepath)

        except Exception as e:
            logger.warning(f"Could not write sbom data to {filepath}: {e}")
