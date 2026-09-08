import base64
import datetime
import hashlib
import hmac
import json
import logging
import os
import sys
from enum import Enum
from graphviz import Digraph
from pathlib import Path
from typing import List, Optional, Union

from sqlalchemy import desc

currentdir = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(1, os.path.dirname(currentdir))

from api_utils import (  # noqa E402
    get_test_run_artifacts_dir,
    is_http_url,
    list_test_run_artifacts,
    parse_comma_separated_list,
    read_basil_version,
)
from db.db_orm import DbInterface  # noqa E402
from db.models.api import ApiModel  # noqa E402
from db.models.api_document import ApiDocumentModel  # noqa E402
from db.models.api_justification import ApiJustificationModel  # noqa E402
from db.models.api_sw_requirement import ApiSwRequirementModel  # noqa E402
from db.models.api_test_case import ApiTestCaseModel  # noqa E402
from db.models.api_test_specification import ApiTestSpecificationModel  # noqa E402
from db.models.document import DocumentModel  # noqa E402
from db.models.document_document import DocumentDocumentModel  # noqa E402
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
BASIL_TOOL_NAME = "BASIL"
BASIL_TOOL_PURL = "pkg:github/elisa-tech/BASIL"
SPDX_SPEC_VERSION = "3.0.1"
SPDX_CONTEXT_URL = f"https://spdx.org/rdf/{SPDX_SPEC_VERSION}/spdx-context.jsonld"
DATETIME_STR_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
BASIL_ANNOTATION_VERSION = "2.0"
SPDX_PROFILE_CONFORMANCE = ["core", "software"]
SPDX_SBOM_TYPES = ["design", "source"]
BASIL_VERSION = read_basil_version()
SBOM_SIGNATURE_EXCLUDED_KEYS = ("signature", "signatures")


def _b64url(data: bytes) -> str:
    """Base64url without padding, as used by JWS / ITU-T X.590 JSS."""
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def unsigned_sbom_payload(json_data: dict) -> dict:
    """Return a copy of the JSON-LD payload without in-document signature fields."""
    unsigned = {key: value for key, value in json_data.items() if key not in SBOM_SIGNATURE_EXCLUDED_KEYS}
    graph = []
    for element in unsigned.get("@graph", []):
        graph.append({key: value for key, value in element.items() if key not in SBOM_SIGNATURE_EXCLUDED_KEYS})
    unsigned["@graph"] = graph
    return unsigned


def canonical_sbom_bytes(json_data: dict) -> bytes:
    """Deterministic JSON used as the HMAC message."""
    return json.dumps(json_data, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def make_sbom_author_signature(json_data: dict, user: UserModel) -> Optional[dict]:
    """Build a CISA SBOM author signature (HMAC-SHA256 / HS256) attributable to ``user``.

    SPDX 3.0.1 has no Signature class. Attach ITU-T X.590 JSS fields plus a
    CycloneDX-style ``signature`` object so checkers looking for algorithm+value
    find an author-attributable MAC of the unsigned document.
    """
    if user is None:
        return None
    key_material = ""
    if hasattr(user, "get_spdx_author_signature"):
        key_material = user.get_spdx_author_signature() or ""
    if not key_material:
        key_material = getattr(user, "spdx_signature", None) or getattr(user, "username", None) or ""
    if not key_material:
        return None

    key = key_material.encode("utf-8")
    digest = hmac.new(key, canonical_sbom_bytes(unsigned_sbom_payload(json_data)), hashlib.sha256).digest()
    username = getattr(user, "username", None) or "unknown"
    return {
        "hash_algorithm": "sha-256",
        "algorithm": "HS256",
        "value": _b64url(digest),
        "thumbprint": _b64url(hashlib.sha256(key).digest()),
        "comment": f"BASIL SBOM author signature attributable to {username}",
    }


class SPDXMD5Hash:
    def __init__(self, hash_value: str = ""):
        self.hash_value = hash_value

    def to_dict(self):
        return {
            "type": "Hash",
            "algorithm": "md5",
            "hashValue": self.hash_value,
        }


class SPDXExternalIdentifier:
    """Represents a SPDX 3.0.1 ExternalIdentifier inline object.

    Used to expose BASIL entity IDs and external tracker URLs to SPDX-aware
    tooling without relying on opaque Annotation.statement JSON.

    BASIL entity IDs follow the convention:
        basil:<db_table_name>:<db_row_id>

    where <db_table_name> is the SQLAlchemy __tablename__ of the originating
    model (e.g. "sw_requirements", "test_cases") and <db_row_id> is the
    integer primary key.  Using the table name directly keeps the identifier
    in sync with the database schema and avoids a separate mapping layer.

    Bug/Fix tracker links use the URL (or free-text reference) as
    ``identifier`` and, when the value is an http(s) URL, also set
    ``identifierLocator``.

    Test Run artifacts use:
        basil:test_runs:<id>:artifact:<filename>

    Example:
        identifier = "basil:sw_requirements:42"
        comment    = "BASIL Software Requirement 'My Title' with ID 42"
    """

    def __init__(
        self,
        identifier: str = "",
        comment: str = "",
        identifier_locator: Optional[List[str]] = None,
        external_identifier_type: str = "other",
    ):
        self.identifier = identifier
        self.comment = comment
        self.identifier_locator = identifier_locator or []
        self.external_identifier_type = external_identifier_type

    def to_dict(self):
        result = {
            "type": "ExternalIdentifier",
            "externalIdentifierType": self.external_identifier_type,
            "identifier": self.identifier,
        }
        if self.comment:
            result["comment"] = self.comment
        if self.identifier_locator:
            result["identifierLocator"] = self.identifier_locator
        return result


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


class SpdxRelationshipType(str, Enum):
    """Valid SPDX 3.0.1 relationship types.

    Values are the camelCase strings expected in the serialized JSON-LD output.
    Because this class inherits from ``str``, enum members can be used
    anywhere a plain string is accepted and will serialize correctly.

    Reference: https://spdx.github.io/spdx-spec/v3.0.1/rdf/schema.json
    """

    AFFECTS = "affects"
    AMENDED_BY = "amendedBy"
    ANCESTOR_OF = "ancestorOf"
    AVAILABLE_FROM = "availableFrom"
    CONFIGURES = "configures"
    CONTAINS = "contains"
    COORDINATED_BY = "coordinatedBy"
    COPIED_TO = "copiedTo"
    DELEGATED_TO = "delegatedTo"
    DEPENDS_ON = "dependsOn"
    DESCENDANT_OF = "descendantOf"
    DESCRIBES = "describes"
    DOES_NOT_AFFECT = "doesNotAffect"
    EXPANDS_TO = "expandsTo"
    EXPLOIT_CREATED_BY = "exploitCreatedBy"
    FIXED_BY = "fixedBy"
    FIXED_IN = "fixedIn"
    FOUND_BY = "foundBy"
    GENERATES = "generates"
    HAS_ADDED_FILE = "hasAddedFile"
    HAS_ASSESSMENT_FOR = "hasAssessmentFor"
    HAS_ASSOCIATED_VULNERABILITY = "hasAssociatedVulnerability"
    HAS_CONCLUDED_LICENSE = "hasConcludedLicense"
    HAS_DATA_FILE = "hasDataFile"
    HAS_DECLARED_LICENSE = "hasDeclaredLicense"
    HAS_DELETED_FILE = "hasDeletedFile"
    HAS_DEPENDENCY_MANIFEST = "hasDependencyManifest"
    HAS_DISTRIBUTION_ARTIFACT = "hasDistributionArtifact"
    HAS_DOCUMENTATION = "hasDocumentation"
    HAS_DYNAMIC_LINK = "hasDynamicLink"
    HAS_EVIDENCE = "hasEvidence"
    HAS_EXAMPLE = "hasExample"
    HAS_HOST = "hasHost"
    HAS_INPUT = "hasInput"
    HAS_METADATA = "hasMetadata"
    HAS_OPTIONAL_COMPONENT = "hasOptionalComponent"
    HAS_OPTIONAL_DEPENDENCY = "hasOptionalDependency"
    HAS_OUTPUT = "hasOutput"
    HAS_PREREQUISITE = "hasPrerequisite"
    HAS_PROVIDED_DEPENDENCY = "hasProvidedDependency"
    HAS_REQUIREMENT = "hasRequirement"
    HAS_SPECIFICATION = "hasSpecification"
    HAS_STATIC_LINK = "hasStaticLink"
    HAS_TEST = "hasTest"
    HAS_TEST_CASE = "hasTestCase"
    HAS_VARIANT = "hasVariant"
    INVOKED_BY = "invokedBy"
    MODIFIED_BY = "modifiedBy"
    OTHER = "other"
    PACKAGED_BY = "packagedBy"
    PATCHED_BY = "patchedBy"
    PUBLISHED_BY = "publishedBy"
    REPORTED_BY = "reportedBy"
    REPUBLISHED_BY = "republishedBy"
    SERIALIZED_IN_ARTIFACT = "serializedInArtifact"
    TESTED_ON = "testedOn"
    TRAINED_ON = "trainedOn"
    UNDER_INVESTIGATION_FOR = "underInvestigationFor"
    USES_TOOL = "usesTool"


# SPDX 2.3 (and BASIL UI abbreviations) → SPDX 3.0.1 RelationshipType.
# Official mapping: https://spdx.github.io/using/diffs-from-previous-editions/
# Keys are matched case-insensitively after '-'/' ' → '_'.
SPDX_2_TO_3_RELATIONSHIP = {
    # Official SPDX 2.3 RelationshipType
    "AMENDS": "amendedBy",
    "ANCESTOR_OF": "ancestorOf",
    "BUILD_DEPENDENCY_OF": "dependsOn",
    "BUILD_TOOL_OF": "usesTool",
    "CONTAINED_BY": "contains",
    "CONTAINS": "contains",
    "COPY_OF": "copiedTo",
    "DATA_FILE_OF": "hasDataFile",
    "DEPENDENCY_MANIFEST_OF": "hasDependencyManifest",
    "DEPENDENCY_OF": "dependsOn",
    "DEPENDS_ON": "dependsOn",
    "DESCENDANT_OF": "descendantOf",
    "DESCRIBED_BY": "describes",
    "DESCRIBES": "describes",
    "DEV_DEPENDENCY_OF": "dependsOn",
    "DEV_TOOL_OF": "usesTool",
    "DISTRIBUTION_ARTIFACT": "hasDistributionArtifact",
    "DOCUMENTATION_OF": "hasDocumentation",
    "DYNAMIC_LINK": "hasDynamicLink",
    "EXAMPLE_OF": "hasExample",
    "EXPANDED_FROM_ARCHIVE": "expandsTo",
    "FILE_ADDED": "hasAddedFile",
    "FILE_DELETED": "hasDeletedFile",
    "FILE_MODIFIED": "modifiedBy",
    "GENERATED_FROM": "generates",
    "GENERATES": "generates",
    "HAS_PREREQUISITE": "hasPrerequisite",
    "METAFILE_OF": "hasMetadata",
    "OPTIONAL_COMPONENT_OF": "hasOptionalComponent",
    "OPTIONAL_DEPENDENCY_OF": "hasOptionalDependency",
    "OTHER": "other",
    "PACKAGE_OF": "packagedBy",
    "PATCH_FOR": "patchedBy",
    "PATCH_APPLIED": "patchedBy",
    "PREREQUISITE_FOR": "hasPrerequisite",
    "PROVIDED_DEPENDENCY_OF": "hasProvidedDependency",
    "REQUIREMENT_DESCRIPTION_FOR": "hasRequirement",
    "RUNTIME_DEPENDENCY_OF": "dependsOn",
    "SPECIFICATION_FOR": "hasSpecification",
    "STATIC_LINK": "hasStaticLink",
    "TEST_CASE_OF": "hasTestCase",
    "TEST_DEPENDENCY_OF": "dependsOn",
    "TEST_OF": "hasTest",
    "TEST_TOOL_OF": "usesTool",
    "VARIANT_OF": "hasVariant",
    # BASIL UI SPDX 2-style abbreviations (dropdown values before 1.8.12)
    "AFFECTS": "affects",
    "ANCESTOR": "ancestorOf",
    "AVAILABLE_FROM": "availableFrom",
    "BUILD_DEPENDENCY": "dependsOn",
    "BUILD_TOOL": "usesTool",
    "COORDINATED_BY": "coordinatedBy",
    "CONFIG_OF": "configures",
    "COPY": "copiedTo",
    "DATA_FILE": "hasDataFile",
    "DEPENDENCY_MANIFEST": "hasDependencyManifest",
    "DESCENDANT": "descendantOf",
    "DEV_DEPENDENCY": "dependsOn",
    "DEV_TOOL": "usesTool",
    "DOCUMENTATION": "hasDocumentation",
    "DOES_NOT_AFFECT": "doesNotAffect",
    "EXAMPLE": "hasExample",
    "EVIDENCE_FOR": "hasEvidence",
    "EXPLOIT_CREATED_BY": "exploitCreatedBy",
    "FIXED_BY": "fixedBy",
    "FIXED_IN": "fixedIn",
    "FOUND_BY": "foundBy",
    "HAS_ASSESSMENT_FOR": "hasAssessmentFor",
    "HAS_ASSOCIATED_VULNERABILITY": "hasAssociatedVulnerability",
    "HOST_OF": "hasHost",
    "INPUT_OF": "hasInput",
    "INVOKED_BY": "invokedBy",
    "METAFILE": "hasMetadata",
    "ON_BEHALF_OF": "delegatedTo",
    "OPTIONAL_COMPONENT": "hasOptionalComponent",
    "OPTIONAL_DEPENDENCY": "hasOptionalDependency",
    "OUTPUT_OF": "hasOutput",
    "PACKAGES": "packagedBy",
    "PATCH": "patchedBy",
    "PREREQUISITE": "hasPrerequisite",
    "PROVIDED_DEPENDENCY": "hasProvidedDependency",
    "PUBLISHED_BY": "publishedBy",
    "REPORTED_BY": "reportedBy",
    "REPUBLISHED_BY": "republishedBy",
    "REQUIREMENT_FOR": "hasRequirement",
    "RUNTIME_DEPENDENCY": "dependsOn",
    "TEST": "hasTest",
    "TEST_CASE": "hasTestCase",
    "TEST_DEPENDENCY": "dependsOn",
    "TEST_TOOL": "usesTool",
    "TESTED_ON": "testedOn",
    "TRAINED_ON": "trainedOn",
    "UNDER_INVESTIGATION_FOR": "underInvestigationFor",
    "VARIANT": "hasVariant",
    # Informal values seen in BASIL data / tests
    "RELATES_TO": "other",
    "RELATED_TO": "other",
}

# SPDX 3.0.1 enum member names (HAS_DOCUMENTATION) also resolve to camelCase values.
SPDX_2_TO_3_RELATIONSHIP.update({member.name: member.value for member in SpdxRelationshipType})


def normalize_spdx_relationship_type(
    value: Optional[str], default: str = SpdxRelationshipType.OTHER
) -> str:
    """Return an SPDX 3.0.1 RelationshipType string.

    Accepts SPDX 3.0.1 camelCase, SPDX 2.3 names, and the pre-1.8.12 BASIL UI
    abbreviations. Unknown or empty values fall back to ``default``.
    """
    valid = {member.value for member in SpdxRelationshipType}
    if default not in valid:
        default = SpdxRelationshipType.OTHER

    if value is None:
        return default
    raw = str(value).strip()
    if not raw:
        return default
    if raw in valid:
        return raw

    key = raw.upper().replace(" ", "_").replace("-", "_")
    mapped = SPDX_2_TO_3_RELATIONSHIP.get(key)
    if mapped in valid:
        return mapped
    return default


class SPDXRelationship:

    def __init__(
        self,
        spdx_id: str = "",
        from_element=None,  # SPDX object
        to=[],  # list of SPDX objects
        relationship_type: SpdxRelationshipType = None,
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
    def __init__(
        self,
        spdx_id: str = "",
        name: str = "",
        description: str = "",
        external_identifiers: Optional[List[SPDXExternalIdentifier]] = None,
        creation_info: SPDXCreationInfo = None,
    ):
        self.spdx_id = spdx_id
        self.name = name
        self.description = description
        self.external_identifiers = external_identifiers or []
        self.creation_info = creation_info

    def to_dict(self):
        result = {
            "type": "Tool",
            "spdxId": self.spdx_id,
            "name": self.name,
            "creationInfo": self.creation_info.spdx_id,
        }
        if self.description:
            result["description"] = self.description
        if self.external_identifiers:
            result["externalIdentifier"] = [ei.to_dict() for ei in self.external_identifiers]
        return result


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
        versioned_object = {**object, "basil:annotationVersion": BASIL_ANNOTATION_VERSION}
        self.statement = json.dumps(versioned_object)
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
        external_identifiers: List["SPDXExternalIdentifier"] = [],
        creation_info: SPDXCreationInfo = None,
    ):

        self.spdx_id = f"{spdx_id}"
        self.name = name
        self.comment = comment
        self.description = description
        self._purpose = purpose if purpose in self.supported_puposes else "other"
        self.copyright_text = copyright_text
        self.verified_using = verified_using
        self.external_identifiers = external_identifiers
        self.creation_info = creation_info

    @property
    def purpose(self):
        return self._purpose

    @purpose.setter
    def purpose(self, purpose):
        self._purpose = purpose if purpose in self.supported_puposes else "other"

    def to_dict(self):
        result = {
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
        if self.external_identifiers:
            result["externalIdentifier"] = [ei.to_dict() for ei in self.external_identifiers]
        return result


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
            "beginIntegerRange": max(self.beginIntegerRange, 1),
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
        root_element: Optional[List[str]] = None,
        profile_conformance: Optional[List[str]] = None,
        creation_info: SPDXCreationInfo = None,
    ):
        self.spdx_id = spdx_id
        self.name = name
        self.data_license = data_license
        self.root_element = root_element or []
        self.profile_conformance = profile_conformance or []
        self.creation_info = creation_info

    def to_dict(self):
        result = {
            "type": "SpdxDocument",
            "spdxId": self.spdx_id,
            "dataLicense": self.data_license.spdx_id,
            "rootElement": self.root_element,
            "name": self.name,
            "creationInfo": self.creation_info.spdx_id,
        }
        if self.profile_conformance:
            result["profileConformance"] = self.profile_conformance
        return result


class SPDXSbom:
    """SPDX 3.0.1 software_Sbom collection describing one BASIL library export.

    Carries CISA/SPDX sbomType values so consumers can tell this is a
    design/source traceability BOM rather than a build-time composition SBOM.
    """

    def __init__(
        self,
        spdx_id: str = "",
        name: str = "",
        root_element: Optional[List[str]] = None,
        element: Optional[List[str]] = None,
        sbom_type: Optional[List[str]] = None,
        profile_conformance: Optional[List[str]] = None,
        creation_info: SPDXCreationInfo = None,
    ):
        self.spdx_id = spdx_id
        self.name = name
        self.root_element = root_element or []
        self.element = element or []
        self.sbom_type = sbom_type or []
        self.profile_conformance = profile_conformance or []
        self.creation_info = creation_info

    def to_dict(self):
        result = {
            "type": "software_Sbom",
            "spdxId": self.spdx_id,
            "name": self.name,
            "rootElement": self.root_element,
            "creationInfo": self.creation_info.spdx_id,
        }
        if self.element:
            result["element"] = self.element
        if self.sbom_type:
            result["software_sbomType"] = self.sbom_type
        if self.profile_conformance:
            result["profileConformance"] = self.profile_conformance
        return result


# Traceability map (Graphviz): classify by SPDX id / Python type, not comment text.
GRAPH_NODE_COLORS = {
    "library": "brown",
    "software_component": "gray",
    "reference_document": "magenta",
    "snippet": "yellow",
    "justification": "green",
    "document": "cyan",
    "software_requirement": "red",
    "test_specification": "blue",
    "test_case": "orange",
    "test_run": "purple",
    "bug": "salmon",
    "fix": "olivedrab",
    "artifact": "khaki",
    "other": "white",
}
GRAPH_CONTAINER_KINDS = frozenset({"library", "software_component", "reference_document"})
# When a container (e.g. API) links at a Test Run already created under a Test Case,
# reuse that instance. Independently mapped work items still get a node per parent.
GRAPH_CROSSLINK_KINDS = frozenset({"test_run", "bug", "fix", "artifact"})
_GRAPH_ELEMENT_TYPES = (SPDXFile, SPDXSnippet)


def graphviz_node_id(spdx_id: Optional[str]) -> str:
    """Stable Graphviz node id derived from an SPDX identifier."""
    return (spdx_id or "").replace(":", "_")


def graph_node_kind(node) -> str:
    """Classify a BASIL SPDX element for the traceability map.

    Uses SPDX identifiers (and ``SPDXSnippet``) so comments cannot mis-label
    nodes (e.g. a snippet whose comment mentions "reference document").
    """
    if isinstance(node, SPDXSnippet):
        return "snippet"
    sid = (getattr(node, "spdx_id", None) or "").lower()
    if sid.startswith("spdx:file:basil:test-run:") and ":bug:" in sid:
        return "bug"
    if sid.startswith("spdx:file:basil:test-run:") and ":fix:" in sid:
        return "fix"
    if sid.startswith("spdx:file:basil:test-run:") and ":artifact:" in sid:
        return "artifact"
    prefixes = (
        ("spdx:file:basil:library:", "library"),
        ("spdx:file:basil:api:reference-document:", "reference_document"),
        ("spdx:file:basil:software-requirement:", "software_requirement"),
        ("spdx:file:basil:test-specification:", "test_specification"),
        ("spdx:file:basil:test-case:", "test_case"),
        ("spdx:file:basil:document:", "document"),
        ("spdx:file:basil:justification:", "justification"),
        ("spdx:file:basil:test-run:", "test_run"),
        ("spdx:file:basil:api:", "software_component"),
        ("spdx:snippet:", "snippet"),
    )
    for prefix, kind in prefixes:
        if sid.startswith(prefix):
            return kind
    return "other"


def is_graph_container(node) -> bool:
    """Library, Software Component, and reference document are unique in the map."""
    return graph_node_kind(node) in GRAPH_CONTAINER_KINDS


def is_graph_element(node) -> bool:
    """Work items drawn on the map (files and snippets, not Document/Sbom/Person)."""
    return isinstance(node, _GRAPH_ELEMENT_TYPES)


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
        self.user = user
        self.include_test_runs = include_test_runs
        self.test_runs_limit = test_runs_limit

        library_name = library_name.strip()
        export_name = f"BASIL SBOM export for library {library_name}"
        spdx_document_id = f"spdx:document:basil:export:{library_name}"
        spdx_sbom_id = f"spdx:sbom:basil:export:{library_name}"

        self.sbom_creation_info = SPDXCreationInfo(
            spdx_id=self.make_spdx_id("sbom_creation_info"),
            created_by=[],
            created=datetime.datetime.now(),
            created_using="",
        )

        sbom_spdx_person = SPDXPerson(
            spdx_id=f"spdx:person:basil:user:{user.id}",
            name=user.username or "",
            creation_info=self.sbom_creation_info,
        )

        tool_external_identifiers = []
        if BASIL_VERSION:
            tool_external_identifiers.append(
                SPDXExternalIdentifier(
                    identifier=f"{BASIL_TOOL_PURL}@{BASIL_VERSION}",
                    comment=f"{BASIL_TOOL_NAME} version {BASIL_VERSION}",
                    identifier_locator=[BASIL_TOOL_URL],
                    external_identifier_type="packageUrl",
                )
            )

        self.tool = SPDXTool(
            spdx_id=BASIL_TOOL_URL,
            name=f"{BASIL_TOOL_NAME} {BASIL_VERSION}".strip() if BASIL_VERSION else BASIL_TOOL_NAME,
            description=f"BASIL SPDX {SPDX_SPEC_VERSION} exporter",
            external_identifiers=tool_external_identifiers,
            creation_info=self.sbom_creation_info,
        )

        self.sbom_creation_info.created_by = [sbom_spdx_person]
        self.sbom_creation_info.created_using = [self.tool]

        spdx_license = SPDXLicense(
            spdx_id=f"spdx:license:{library_name}",
            license="NOASSERTION",
            creation_info=self.sbom_creation_info,
        )

        document = SPDXDocument(
            spdx_id=spdx_document_id,
            name=export_name,
            data_license=spdx_license,
            root_element=[],
            profile_conformance=list(SPDX_PROFILE_CONFORMANCE),
            creation_info=self.sbom_creation_info,
        )

        software_sbom = SPDXSbom(
            spdx_id=spdx_sbom_id,
            name=export_name,
            root_element=[],
            sbom_type=list(SPDX_SBOM_TYPES),
            profile_conformance=list(SPDX_PROFILE_CONFORMANCE),
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
        software_sbom.root_element.append(library.spdx_id)
        software_sbom.element.append(library.spdx_id)
        document.root_element.append(software_sbom.spdx_id)

        added_apis = []
        for api in apis:
            api_creation_info, api_person, spdx_api = self.addApi(api, dbi.session)
            added_apis.append(spdx_api)
            software_sbom.element.append(spdx_api.spdx_id)

        if added_apis:
            # Library structurally contains each Software Component, uses them as
            # design/source inputs, and is specified by them (the public API surface).
            for relationship_type in (
                SpdxRelationshipType.CONTAINS,
                SpdxRelationshipType.HAS_INPUT,
                SpdxRelationshipType.HAS_SPECIFICATION,
            ):
                self.addRelationship(
                    from_element=library, to=added_apis, relationship_type=relationship_type
                )

        self.add_to_sbom(software_sbom)
        self.add_to_sbom(document)
        self.addRelationship(
            from_element=document, to=[software_sbom], relationship_type=SpdxRelationshipType.DESCRIBES
        )

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
            spdx_id=f"{spdx_person_id}",
            name=created_by.username or "",
            creation_info=self.sbom_creation_info,
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

    def clean_snippet_annotation_dict(self, relation_dict):
        """Remove fields from a snippet mapping dict that are already represented in
        SPDX properties: offset/section are encoded in software_byteRange; coverage
        is encoded in Relationship.completeness."""
        redundant_keys = ["offset", "section", "coverage"]
        for key in redundant_keys:
            relation_dict.pop(key, None)
        return relation_dict

    @staticmethod
    def clean_entity_annotation_dict(entity_dict):
        """Remove id and title fields that are now represented as ExternalIdentifier
        on the SPDX element, avoiding duplication with opaque annotation JSON."""
        for key in ["id", "title"]:
            entity_dict.pop(key, None)
        return entity_dict

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

        # Read byte range values before stripping redundant fields
        byte_range_begin = mapping_dict["offset"] + 1
        byte_range_end = mapping_dict["offset"] + len(mapping_dict["section"]) + 1
        snippet_annotation_dict = self.clean_snippet_annotation_dict(dict(mapping_dict))

        snippet_id = f"spdx:snippet:api:{api_id}:{self.getSnippetIndex()}"

        creation_info, person = self.getCreationInfoAndPerson(
            item_id=snippet_id, created_by=mapping.created_by, created_at=mapping.created_at, add_to_sbom=True
        )

        snippet = SPDXSnippet(
            spdx_id=snippet_id,
            from_file=spdx_api_ref_doc_file,
            name=mapping.api.raw_specification_url,
            comment=f"Snippet of api {api} reference document",
            byte_range=PositiveIntegerRange(byte_range_begin, byte_range_end),
            creation_info=creation_info,
        )

        snippet_annotation = SPDXAnnotation(
            spdx_id=f"spdx:annotation:snippet:api:"
            f"{api_id}:{mapping_to_id_prefix}:{mapping_to_id}:relation-id:{relation_id}",
            name=f"Annotation for BASIL API {api} snippet",
            subject=snippet,
            object=snippet_annotation_dict,
            creation_info=creation_info,
        )

        snippet_in_sbom, sbom_snippet = self.getSnippetFromSBOM(snippet=snippet)

        if not snippet_in_sbom:
            self.add_to_sbom(sbom_snippet)
            self.add_to_sbom(snippet_annotation)

        self.addRelationship(
            from_element=spdx_api_file,
            to=[sbom_snippet],
            relationship_type=SpdxRelationshipType.CONTAINS,
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
            external_identifiers=[
                SPDXExternalIdentifier(
                    identifier=f"basil:{api.__tablename__}:{api.id}",
                    comment=f"BASIL Software Component '{api.api}' with ID {api.id}",
                )
            ],
            creation_info=creation_info,
        )

        api_annotation_dict = self.clean_entity_annotation_dict(dict(api_dict))
        file_api_annotation = SPDXAnnotation(
            spdx_id=f"spdx:annotation:basil:api:{api_dict['id']}",
            name=f"Annotation for BASIL API {api.api} with ID {api.id}",
            subject=file_api,
            object=api_annotation_dict,
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

        # The reference document is both documentation of the Software Component
        # and its specification (File.purpose is already "specification").
        for relationship_type in (
            SpdxRelationshipType.HAS_DOCUMENTATION,
            SpdxRelationshipType.HAS_SPECIFICATION,
        ):
            self.addRelationship(
                from_element=file_api, to=[file_api_ref_doc], relationship_type=relationship_type
            )

        self.addApiSwRequirements(spdx_api=file_api, spdx_api_ref_doc=file_api_ref_doc, api=api, dbsession=dbsession)

        self.addApiTestSpecifications(
            spdx_api=file_api, spdx_api_ref_doc=file_api_ref_doc, api=api, dbsession=dbsession
        )

        self.addApiTestCases(spdx_api=file_api, spdx_api_ref_doc=file_api_ref_doc, api=api, dbsession=dbsession)

        self.addApiDocuments(spdx_api=file_api, spdx_api_ref_doc=file_api_ref_doc, api=api, dbsession=dbsession)

        self.addApiJustifications(spdx_api=file_api, spdx_api_ref_doc=file_api_ref_doc, api=api, dbsession=dbsession)
        return (creation_info, person, file_api)

    def addRelationship(
        self,
        from_element=None,
        to: list = [],
        relationship_type: SpdxRelationshipType = None,
        completeness_percentage: int = 0,
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
            external_identifiers=[
                SPDXExternalIdentifier(
                    identifier=f"basil:{software_requirement.__tablename__}:{software_requirement.id}",
                    comment=(
                        f"BASIL Software Requirement '{software_requirement.title}'"
                        f" with ID {software_requirement.id}"
                    ),
                )
            ],
            creation_info=creation_info,
        )

        sr_annotation_dict = self.clean_entity_annotation_dict(dict(sr_dict))
        sr_annotation = SPDXAnnotation(
            spdx_id=f"spdx:annotation:basil:software-requirement:{software_requirement.id}",
            name=f"Annotation for BASIL Software Requirement {software_requirement.id}",
            subject=sr_file,
            object=sr_annotation_dict,
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
            external_identifiers=[
                SPDXExternalIdentifier(
                    identifier=f"basil:{test_specification.__tablename__}:{test_specification.id}",
                    comment=f"BASIL Test Specification '{test_specification.title}' with ID {test_specification.id}",
                )
            ],
            creation_info=creation_info,
        )

        ts_annotation_dict = self.clean_entity_annotation_dict(dict(ts_dict))
        ts_annotation = SPDXAnnotation(
            spdx_id=f"spdx:annotation:basil:test-specification:{test_specification.id}",
            name=f"Annotation for BASIL Test Specification {test_specification.id}",
            subject=ts_file,
            object=ts_annotation_dict,
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
            external_identifiers=[
                SPDXExternalIdentifier(
                    identifier=f"basil:{test_case.__tablename__}:{test_case.id}",
                    comment=f"BASIL Test Case '{test_case.title}' with ID {test_case.id}",
                )
            ],
            creation_info=creation_info,
        )

        tc_annotation_dict = self.clean_entity_annotation_dict(dict(tc_dict))
        tc_annotation = SPDXAnnotation(
            spdx_id=f"spdx:annotation:basil:test-case:{test_case.id}",
            name=f"Annotation for BASIL Test Case {test_case.id}",
            subject=tc_file,
            object=tc_annotation_dict,
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
            external_identifiers=[
                SPDXExternalIdentifier(
                    identifier=f"basil:{document.__tablename__}:{document.id}",
                    comment=f"BASIL Document '{document.title}' with ID {document.id}",
                )
            ],
            creation_info=creation_info,
        )

        doc_annotation_dict = self.clean_entity_annotation_dict(dict(doc_dict))
        doc_annotation = SPDXAnnotation(
            spdx_id=f"spdx:annotation:basil:document:{document.id}",
            name=f"Annotation for BASIL Document {document.id}",
            subject=doc_file,
            object=doc_annotation_dict,
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
            external_identifiers=[
                SPDXExternalIdentifier(
                    identifier=f"basil:{justification.__tablename__}:{justification.id}",
                    comment=f"BASIL Justification with ID {justification.id}",
                )
            ],
            creation_info=creation_info,
        )

        js_annotation_dict = self.clean_entity_annotation_dict(dict(js_dict))
        js_annotation = SPDXAnnotation(
            spdx_id=f"spdx:annotation:basil:justification:{justification.id}",
            name=f"Annotation for BASIL Justification {justification.id}",
            subject=js_file,
            object=js_annotation_dict,
            creation_info=creation_info,
        )

        self.add_to_sbom(js_file)
        self.add_to_sbom(js_annotation)
        return js_file

    def addTestRuns(
        self,
        spdx_tc: SPDXFile = None,
        mapping_to: str = "",
        mapping_id: int = 0,
        dbsession=None,
        spdx_api: SPDXFile = None,
    ):
        if not self.include_test_runs:
            logger.warning("Skip Test Runs as per export configuration")
            return

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

        added_test_runs = []
        test_run_files = []
        for test_run in test_runs:
            tr_file = self.addTestRun(test_run=test_run, dbsession=dbsession)
            added_test_runs.append(tr_file)
            test_run_files.append((test_run, tr_file))

        if added_test_runs:
            # Link the Test Run to its Test Case / Software Component before
            # attaching bug/fix/artifact outputs so JSON-LD consumers walk
            # TC → TR → outputs instead of seeing an unparented run.
            for relationship_type in (
                SpdxRelationshipType.GENERATES,
                SpdxRelationshipType.HAS_TEST,
                SpdxRelationshipType.HAS_OUTPUT,
            ):
                self.addRelationship(
                    from_element=spdx_tc, to=added_test_runs, relationship_type=relationship_type
                )
            if spdx_api:
                self.addRelationship(
                    from_element=spdx_api,
                    to=added_test_runs,
                    relationship_type=SpdxRelationshipType.HAS_TEST,
                )
                for spdx_tr in added_test_runs:
                    self.addRelationship(
                        from_element=spdx_tr,
                        to=[spdx_api],
                        relationship_type=SpdxRelationshipType.TESTED_ON,
                    )
            for test_run, tr_file in test_run_files:
                self.addTestRunBugAndFixOutputs(
                    spdx_tr=tr_file, test_run=test_run, creation_info=tr_file.creation_info
                )
                self.addTestRunArtifacts(
                    spdx_tr=tr_file, test_run=test_run, creation_info=tr_file.creation_info
                )

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
            external_identifiers=[
                SPDXExternalIdentifier(
                    identifier=f"basil:{test_run.__tablename__}:{test_run.id}",
                    comment=f"BASIL Test Run '{test_run.title}' with ID {test_run.id}",
                )
            ],
            creation_info=creation_info,
        )

        tr_annotation_dict = self.clean_entity_annotation_dict(dict(tr_dict))
        tr_annotation = SPDXAnnotation(
            spdx_id=f"spdx:annotation:basil:test-run:{test_run.id}",
            name=f"Annotation for BASIL Test Run {test_run.id}",
            subject=tr_file,
            object=tr_annotation_dict,
            creation_info=creation_info,
        )

        self.add_to_sbom(tr_file)
        self.add_to_sbom(tr_annotation)
        return tr_file

    def addTestRunBugOrFix(
        self,
        test_run: TestRunModel = None,
        kind: str = "bug",
        ref: str = "",
        index: int = 1,
        creation_info: SPDXCreationInfo = None,
    ):
        """Create an SPDX File for one Bug or Fix reference from a Test Run.

        The Element carries an ExternalIdentifier whose ``identifier`` is the
        reference string (typically a tracker URL). http(s) URLs also set
        ``identifierLocator``.
        """
        kind_label = "Bug" if kind == "bug" else "Fix"
        purpose = "other" if kind == "bug" else "patch"
        spdx_id = f"spdx:file:basil:test-run:{test_run.id}:{kind}:{index}"
        data_dict = {
            "kind": kind,
            "ref": ref,
            "test_run_id": test_run.id,
            "index": index,
        }
        ref_hash = self.make_hash_object(data_dict=data_dict)
        locator = [ref] if is_http_url(ref) else []

        ref_file = SPDXFile(
            spdx_id=spdx_id,
            name=ref,
            comment=f"BASIL {kind_label}",
            description=f"{kind_label} linked from BASIL Test Run {test_run.id}",
            purpose=purpose,
            copyright_text="",
            verified_using=[ref_hash],
            external_identifiers=[
                SPDXExternalIdentifier(
                    identifier=ref,
                    comment=f"BASIL Test Run {test_run.id} {kind_label}",
                    identifier_locator=locator,
                )
            ],
            creation_info=creation_info,
        )
        self.add_to_sbom(ref_file)
        return ref_file

    def addTestRunBugAndFixOutputs(
        self,
        spdx_tr: SPDXFile = None,
        test_run: TestRunModel = None,
        creation_info: SPDXCreationInfo = None,
    ):
        """Emit Bug/Fix Elements from test_runs.bugs / test_runs.fixes.

        Each reference becomes its own SPDX File with an ExternalIdentifier.
        Each is linked from the Test Run with a dedicated 1-to-1 ``hasOutput``
        relationship.
        """
        for kind, column_value in (("bug", test_run.bugs), ("fix", test_run.fixes)):
            refs = parse_comma_separated_list(column_value)
            for index, ref in enumerate(refs, start=1):
                spdx_ref = self.addTestRunBugOrFix(
                    test_run=test_run,
                    kind=kind,
                    ref=ref,
                    index=index,
                    creation_info=creation_info,
                )
                self.addRelationship(
                    from_element=spdx_tr,
                    to=[spdx_ref],
                    relationship_type=SpdxRelationshipType.HAS_OUTPUT,
                )

    def addTestRunArtifact(
        self,
        test_run: TestRunModel = None,
        artifact_name: str = "",
        index: int = 1,
        creation_info: SPDXCreationInfo = None,
    ):
        """Create an SPDX File for one Test Run artifact on disk.

        Artifacts live under ``TEST_RUNS_BASE_DIR/<uid>/api/tmt-plan/data/``.
        ``verifiedUsing`` prefers an MD5 of the file contents when readable;
        otherwise a metadata hash is used.
        """
        artifacts_dir = get_test_run_artifacts_dir(test_run.uid)
        artifact_path = os.path.join(artifacts_dir, artifact_name)
        spdx_id = f"spdx:file:basil:test-run:{test_run.id}:artifact:{index}"

        content_hash = None
        if os.path.isfile(artifact_path):
            try:
                dhash = hashlib.md5()
                with open(artifact_path, "rb") as artifact_file:
                    for chunk in iter(lambda: artifact_file.read(1024 * 1024), b""):
                        dhash.update(chunk)
                content_hash = SPDXMD5Hash(hash_value=dhash.hexdigest())
            except OSError as e:
                logger.warning(f"Unable to hash artifact {artifact_path}: {e}")

        if content_hash is None:
            content_hash = self.make_hash_object(
                data_dict={
                    "artifact_name": artifact_name,
                    "test_run_id": test_run.id,
                    "index": index,
                }
            )

        artifact_file = SPDXFile(
            spdx_id=spdx_id,
            name=artifact_name,
            comment="BASIL Artifact",
            description=f"Artifact '{artifact_name}' from BASIL Test Run {test_run.id}",
            purpose="evidence",
            copyright_text="",
            verified_using=[content_hash],
            external_identifiers=[
                SPDXExternalIdentifier(
                    identifier=f"basil:{test_run.__tablename__}:{test_run.id}:artifact:{artifact_name}",
                    comment=f"BASIL Test Run {test_run.id} Artifact '{artifact_name}'",
                )
            ],
            creation_info=creation_info,
        )
        self.add_to_sbom(artifact_file)
        return artifact_file

    def addTestRunArtifacts(
        self,
        spdx_tr: SPDXFile = None,
        test_run: TestRunModel = None,
        creation_info: SPDXCreationInfo = None,
    ):
        """Emit SPDX Files for Test Run artifacts and link them 1-to-many.

        Each on-disk artifact becomes an SPDX File (purpose ``evidence``).
        The Test Run is linked to all artifacts with both ``hasOutput`` and
        ``hasEvidence`` relationships (one relationship of each type covering
        the full artifact list).
        """
        artifact_names = list_test_run_artifacts(test_run.uid)
        if not artifact_names:
            return

        added_artifacts = []
        for index, artifact_name in enumerate(artifact_names, start=1):
            added_artifacts.append(
                self.addTestRunArtifact(
                    test_run=test_run,
                    artifact_name=artifact_name,
                    index=index,
                    creation_info=creation_info,
                )
            )

        self.addRelationship(
            from_element=spdx_tr,
            to=added_artifacts,
            relationship_type=SpdxRelationshipType.HAS_OUTPUT,
        )
        self.addRelationship(
            from_element=spdx_tr,
            to=added_artifacts,
            relationship_type=SpdxRelationshipType.HAS_EVIDENCE,
        )

    def addDocumentsNestedElements(
        self,
        api: ApiModel = None,
        xdoc: Optional[Union[ApiDocumentModel, DocumentDocumentModel]] = None,
        spdx_doc: SPDXFile = None,  # SPDX object of Document from xdoc.document
        dbsession=None,
    ):
        """In BASIL user can create a complex hierarchy of Documents.
        Moreover we can assign other work items to each Document in the chain.
        This method navigate the hierarchy and return all the work items

        :param api: software component where the mapping is defined
        :param xdoc: Document mapping model instance
        :param spdx_doc: DocumentSPDX instance
        :param dbi: Database interface instance
        :return:
        """
        if isinstance(xdoc, ApiDocumentModel):
            mapping_field = f"{ApiDocumentModel.__tablename__}"
            mapping_field_id = f"{mapping_field}_id"
        elif isinstance(xdoc, DocumentDocumentModel):
            mapping_field = f"{DocumentDocumentModel.__tablename__}"
            mapping_field_id = f"{mapping_field}_id"
        else:
            return

        # DocumentDocumentModel
        doc_docs = (
            dbsession.query(DocumentDocumentModel)
            .filter(getattr(DocumentDocumentModel, mapping_field_id) == xdoc.id)
            .all()
        )
        for doc_doc in doc_docs:
            spdx_doc_doc = self.addDocument(document=doc_doc.document, dbsession=dbsession)
            for relationship_type in (
                SpdxRelationshipType.HAS_DOCUMENTATION,
                SpdxRelationshipType.CONTAINS,
            ):
                self.addRelationship(
                    from_element=spdx_doc,
                    to=[spdx_doc_doc],
                    relationship_type=relationship_type,
                    completeness_percentage=doc_doc.coverage,
                )

            # DocumentDocument
            self.addDocumentsNestedElements(
                api=api, xdoc=doc_doc, spdx_doc=spdx_doc_doc, dbsession=dbsession
            )

    def addSoftwareRequirementNestedElements(
        self,
        api: ApiModel = None,
        xsr: Optional[Union[ApiSwRequirementModel, SwRequirementSwRequirementModel]] = None,
        spdx_sr: SPDXFile = None,  # SPDX object of SwRequirement from xsr.sw_requriement
        dbsession=None,
        spdx_api: SPDXFile = None,
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
            for relationship_type in (
                SpdxRelationshipType.HAS_REQUIREMENT,
                SpdxRelationshipType.CONTAINS,
            ):
                self.addRelationship(
                    from_element=spdx_sr,
                    to=[spdx_sr_sr],
                    relationship_type=relationship_type,
                    completeness_percentage=xsr.coverage,
                )

            # SwRequirementTestSpecification
            self.addSwRequirementTestSpecifications(
                spdx_sr=spdx_sr_sr,
                mapping_to=SwRequirementSwRequirementModel.__tablename__,
                mapping_id=sr_sr.id,
                dbsession=dbsession,
                spdx_api=spdx_api,
            )

            # SwRequirementTestCases
            self.addSwRequirementTestCases(
                spdx_sr=spdx_sr_sr,
                mapping_to=SwRequirementSwRequirementModel.__tablename__,
                mapping_id=sr_sr.id,
                dbsession=dbsession,
                spdx_api=spdx_api,
            )

            self.addSoftwareRequirementNestedElements(
                api=api, xsr=sr_sr, spdx_sr=spdx_sr_sr, dbsession=dbsession, spdx_api=spdx_api
            )

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
                relationship_type=SpdxRelationshipType.HAS_REQUIREMENT,
                completeness_percentage=asr.coverage,
            )

            # SwRequirementTestSpecifications for this SW Requirement
            self.addSwRequirementTestSpecifications(
                spdx_sr=spdx_sr,
                mapping_to=ApiSwRequirementModel.__tablename__,
                mapping_id=asr.id,
                dbsession=dbsession,
                spdx_api=spdx_api,
            )

            # SwRequirementTestCases for this SW Requirement
            self.addSwRequirementTestCases(
                spdx_sr=spdx_sr,
                mapping_to=ApiSwRequirementModel.__tablename__,
                mapping_id=asr.id,
                dbsession=dbsession,
                spdx_api=spdx_api,
            )

            self.addSoftwareRequirementNestedElements(
                api=api, xsr=asr, spdx_sr=spdx_sr, dbsession=dbsession, spdx_api=spdx_api
            )

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
                relationship_type=SpdxRelationshipType.HAS_SPECIFICATION,
                completeness_percentage=ats.coverage,
            )

            # TestSpecificationTestCases mapping to ApiTestSpecification
            mapping_to = ApiTestSpecificationModel.__tablename__
            self.addTestSpecificationTestCases(
                spdx_ts=spdx_ts,
                mapping_to=mapping_to,
                mapping_id=ats.id,
                dbsession=dbsession,
                spdx_api=spdx_api,
            )

    def addSwRequirementTestSpecifications(
        self, spdx_sr=None, mapping_to: str = "", mapping_id: int = 0, dbsession=None, spdx_api=None
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
                relationship_type=SpdxRelationshipType.HAS_SPECIFICATION,
                completeness_percentage=sr_ts.coverage,
            )

            # TestSpecificationTestCaseModel
            self.addTestSpecificationTestCases(
                spdx_ts=spdx_ts,
                mapping_to=sr_ts.__tablename__,
                mapping_id=sr_ts.id,
                dbsession=dbsession,
                spdx_api=spdx_api,
            )

    def addSwRequirementTestCases(
        self, spdx_sr=None, mapping_to: str = "", mapping_id: int = 0, dbsession=None, spdx_api=None
    ):
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
                from_element=spdx_sr,
                to=[spdx_tc],
                relationship_type=SpdxRelationshipType.HAS_TEST_CASE,
                completeness_percentage=sr_tc.coverage
            )

            # Test Runs
            self.addTestRuns(
                spdx_tc=spdx_tc,
                mapping_to=SwRequirementTestCaseModel.__tablename__,
                mapping_id=sr_tc.id,
                dbsession=dbsession,
                spdx_api=spdx_api,
            )

    def addTestSpecificationTestCases(
        self, spdx_ts=None, mapping_to: str = "", mapping_id: int = 0, dbsession=None, spdx_api=None
    ):
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
                from_element=spdx_ts,
                to=[spdx_tc],
                relationship_type=SpdxRelationshipType.HAS_TEST_CASE,
                completeness_percentage=ts_tc.coverage
            )

            # Test Runs
            self.addTestRuns(
                spdx_tc=spdx_tc,
                mapping_to=TestSpecificationTestCaseModel.__tablename__,
                mapping_id=ts_tc.id,
                dbsession=dbsession,
                spdx_api=spdx_api,
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
                relationship_type=SpdxRelationshipType.HAS_TEST_CASE,
                completeness_percentage=atc.coverage,
            )

            # Test Runs
            self.addTestRuns(
                spdx_tc=spdx_tc,
                mapping_to=ApiTestCaseModel.__tablename__,
                mapping_id=atc.id,
                dbsession=dbsession,
                spdx_api=spdx_api,
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
                # TODO: Read the relationship from the document mapping
                relationship_type=SpdxRelationshipType.HAS_DOCUMENTATION,
                completeness_percentage=adoc.coverage,
            )

            self.addDocumentsNestedElements(api=api, xdoc=adoc, spdx_doc=spdx_doc, dbsession=dbsession)

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
                relationship_type=SpdxRelationshipType.HAS_EVIDENCE,
                completeness_percentage=ajs.coverage,
            )

    def generate_diagraph(self, output_file: str = ""):
        """Write a Graphviz traceability map (``.dot`` and ``.png``).

        ``output_file`` is the path without suffix; files are
        ``{output_file}.dot`` and ``{output_file}.png``.
        Multiple SPDX relationship types between the same pair become one
        edge labeled ``a,b,c``. Test Run outputs are attached after the run
        is placed under its Test Case so they are not orphaned.
        """

        last_instance = {}
        added_nodes = {}
        # One visual edge per node pair; multiple SPDX types become "a,b,c".
        added_edges = {}

        def register_instance(label, instance_id):
            last_instance[label] = instance_id

        def from_is_ready(node):
            """Defer edges until the source has a mapping-tree instance.

            Test Run → bug/fix/artifact is emitted before Test Case → Test Run,
            so the run must not become an orphan node.
            """
            if is_graph_container(node):
                return True
            return graphviz_node_id(node.spdx_id) in last_instance

        def add_node(instance_id, node):
            if instance_id in added_nodes:
                return
            kind = graph_node_kind(node)
            color = GRAPH_NODE_COLORS.get(kind, "white")
            dot.node(
                instance_id,
                label=graphviz_node_id(node.spdx_id),
                style="filled",
                fillcolor=color,
            )
            added_nodes[instance_id] = color

        def resolve_from(node):
            label = graphviz_node_id(node.spdx_id)
            if is_graph_container(node):
                register_instance(label, label)
                return label
            return last_instance[label]

        def resolve_to(from_id, from_node, to_node):
            label = graphviz_node_id(to_node.spdx_id)
            if is_graph_container(to_node):
                register_instance(label, label)
                return label
            if not is_graph_container(from_node):
                instance_id = f"{from_id}__{label}"
                register_instance(label, instance_id)
                return instance_id
            # Container → derived artifact already in the mapping tree (API hasTest
            # Test Run): reuse that instance. Mapped work items still duplicate.
            if graph_node_kind(to_node) in GRAPH_CROSSLINK_KINDS and label in last_instance:
                return last_instance[label]
            instance_id = f"{from_id}__{label}"
            register_instance(label, instance_id)
            return instance_id

        def add_edge(src, dst, rel_label):
            key = (src, dst)
            labels = added_edges.setdefault(key, [])
            if rel_label not in labels:
                labels.append(rel_label)

        def link_snippet_to_source_file(snippet, snippet_instance_id):
            from_file = getattr(snippet, "from_file", None)
            if from_file is None or not getattr(from_file, "spdx_id", None):
                return
            file_id = graphviz_node_id(from_file.spdx_id)
            register_instance(file_id, file_id)
            add_node(file_id, from_file)
            add_edge(file_id, snippet_instance_id, SpdxRelationshipType.CONTAINS.value)

        def emit_relationship(relationship):
            from_node = relationship.from_element
            rel_label = (
                relationship.relationship_type.value
                if isinstance(relationship.relationship_type, Enum)
                else str(relationship.relationship_type)
            )
            for to_node in relationship.to or []:
                if not is_graph_element(to_node):
                    continue
                from_id = resolve_from(from_node)
                to_id = resolve_to(from_id, from_node, to_node)
                add_node(from_id, from_node)
                add_node(to_id, to_node)
                add_edge(from_id, to_id, rel_label)
                if isinstance(to_node, SPDXSnippet):
                    link_snippet_to_source_file(to_node, to_id)
                if isinstance(from_node, SPDXSnippet):
                    link_snippet_to_source_file(from_node, from_id)

        dot = Digraph(format="png")
        dot.attr(rankdir="TB")

        pending = []
        for relationship in self.sbom:
            if not isinstance(relationship, SPDXRelationship):
                continue
            from_node = relationship.from_element
            if not is_graph_element(from_node):
                continue
            if from_is_ready(from_node):
                emit_relationship(relationship)
            else:
                pending.append(relationship)

        progress = True
        while pending and progress:
            progress = False
            still_pending = []
            for relationship in pending:
                if from_is_ready(relationship.from_element):
                    emit_relationship(relationship)
                    progress = True
                else:
                    still_pending.append(relationship)
            pending = still_pending

        for src, dst in sorted(added_edges):
            dot.edge(src, dst, label=",".join(added_edges[(src, dst)]))

        legend = Digraph(name="cluster_legend")
        legend.attr(label="Legend", fontsize="12", style="dashed")
        legend.attr("node", shape="box", style="filled", width="1")
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
        legend.node("bug", label="Bug", shape="box", style="filled", fillcolor="salmon")
        legend.node("fix", label="Fix", shape="box", style="filled", fillcolor="olivedrab")
        legend.node("artifact", label="Artifact", shape="box", style="filled", fillcolor="khaki")
        legend.edge("library", "software_component", style="invis", weight="100")
        legend.edge("software_component", "reference_document", style="invis", weight="100")
        legend.edge("reference_document", "snippet", style="invis", weight="100")
        legend.edge("snippet", "justification", style="invis", weight="100")
        legend.edge("justification", "document", style="invis", weight="100")
        legend.edge("document", "software_requirement", style="invis", weight="100")
        legend.edge("software_requirement", "test_specification", style="invis", weight="100")
        legend.edge("test_specification", "test_case", style="invis", weight="100")
        legend.edge("test_case", "test_run", style="invis", weight="100")
        legend.edge("test_run", "bug", style="invis", weight="100")
        legend.edge("bug", "fix", style="invis", weight="100")
        legend.edge("fix", "artifact", style="invis", weight="100")
        dot.subgraph(legend)

        dot_filepath = f"{output_file}.dot"
        logger.info(f"Creating .dot file at {dot_filepath}")
        with open(dot_filepath, "w") as f:
            f.write(dot.source)

        try:
            dot.render(filename=str(output_file), cleanup=True)
        except Exception as e:
            logger.warning(f"Could not render PNG for {output_file}: {e}")

    def _attach_author_signature(self, json_data: dict) -> dict:
        """Attach an SBOM author signature to the JSON-LD document and SpdxDocument."""
        signature_block = make_sbom_author_signature(json_data, self.user)
        if not signature_block:
            return json_data

        jsf_signature = {
            "algorithm": signature_block["algorithm"],
            "value": signature_block["value"],
        }
        json_data["signature"] = jsf_signature
        json_data["signatures"] = [signature_block]
        for element in json_data.get("@graph", []):
            if element.get("type") == "SpdxDocument":
                element["signature"] = jsf_signature
        return json_data

    def export(self, filepath):
        """Export payload into json"""
        json_data = {"@context": SPDX_CONTEXT_URL, "@graph": []}

        for item in self.sbom:
            json_data["@graph"].append(item.to_dict())

        json_data["@graph"] = sorted(json_data["@graph"], key=lambda d: d["type"], reverse=False)
        json_data = self._attach_author_signature(json_data)

        if not filepath.endswith(".jsonld"):
            filepath += ".jsonld"

        try:
            with open(filepath, "w") as f:
                json.dump(json_data, f, indent=2)

            graph_filepath = Path(filepath).with_suffix("")
            self.generate_diagraph(graph_filepath)

        except Exception as e:
            logger.warning(f"Could not write sbom data to {filepath}: {e}")
