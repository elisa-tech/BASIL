"""SPDX 2.3 / BASIL UI relationship names → SPDX 3.0.1 RelationshipType."""

from spdx_manager import (
    SPDX_2_TO_3_RELATIONSHIP,
    SpdxRelationshipType,
    normalize_spdx_relationship_type,
)

# Pre-1.8.12 BASIL UI dropdown values (SPDX 2-style).
_BASIL_UI_SPDX_2_NAMES = [
    "AFFECTS",
    "AMENDS",
    "ANCESTOR",
    "AVAILABLE_FROM",
    "BUILD_DEPENDENCY",
    "BUILD_TOOL",
    "COORDINATED_BY",
    "CONTAINS",
    "CONFIG_OF",
    "COPY",
    "DATA_FILE",
    "DEPENDENCY_MANIFEST",
    "DEPENDS_ON",
    "DESCENDANT",
    "DESCRIBES",
    "DEV_DEPENDENCY",
    "DEV_TOOL",
    "DISTRIBUTION_ARTIFACT",
    "DOCUMENTATION",
    "DOES_NOT_AFFECT",
    "DYNAMIC_LINK",
    "EXAMPLE",
    "EVIDENCE_FOR",
    "EXPANDED_FROM_ARCHIVE",
    "EXPLOIT_CREATED_BY",
    "FILE_ADDED",
    "FILE_DELETED",
    "FILE_MODIFIED",
    "FIXED_BY",
    "FIXED_IN",
    "FOUND_BY",
    "GENERATES",
    "HAS_ASSESSMENT_FOR",
    "HAS_ASSOCIATED_VULNERABILITY",
    "HOST_OF",
    "INPUT_OF",
    "INVOKED_BY",
    "METAFILE",
    "ON_BEHALF_OF",
    "OPTIONAL_COMPONENT",
    "OPTIONAL_DEPENDENCY",
    "OTHER",
    "OUTPUT_OF",
    "PACKAGES",
    "PATCH",
    "PREREQUISITE",
    "PROVIDED_DEPENDENCY",
    "PUBLISHED_BY",
    "REPORTED_BY",
    "REPUBLISHED_BY",
    "REQUIREMENT_FOR",
    "RUNTIME_DEPENDENCY",
    "SPECIFICATION_FOR",
    "STATIC_LINK",
    "TEST",
    "TEST_CASE",
    "TEST_DEPENDENCY",
    "TEST_TOOL",
    "TESTED_ON",
    "TRAINED_ON",
    "UNDER_INVESTIGATION_FOR",
    "VARIANT",
]


def test_mapping_targets_are_spdx_3_01_types():
    valid = {member.value for member in SpdxRelationshipType}
    for source, target in SPDX_2_TO_3_RELATIONSHIP.items():
        assert target in valid, f"{source} maps to unknown SPDX 3.0.1 type {target!r}"


def test_all_legacy_ui_names_map_to_spdx_3():
    for name in _BASIL_UI_SPDX_2_NAMES:
        normalized = normalize_spdx_relationship_type(name)
        assert normalized in {member.value for member in SpdxRelationshipType}
        assert normalized == normalize_spdx_relationship_type(name.lower())


def test_normalize_passthrough_spdx_3_camel_case():
    for member in SpdxRelationshipType:
        assert normalize_spdx_relationship_type(member.value) == member.value


def test_normalize_common_aliases():
    assert normalize_spdx_relationship_type("DOCUMENTATION") == "hasDocumentation"
    assert normalize_spdx_relationship_type("DOCUMENTATION_OF") == "hasDocumentation"
    assert normalize_spdx_relationship_type("SPECIFICATION_FOR") == "hasSpecification"
    assert normalize_spdx_relationship_type("INPUT_OF") == "hasInput"
    assert normalize_spdx_relationship_type("OUTPUT_OF") == "hasOutput"
    assert normalize_spdx_relationship_type("DESCRIBES") == "describes"
    assert normalize_spdx_relationship_type("relates-to") == "other"
    assert normalize_spdx_relationship_type("") == "other"
    assert normalize_spdx_relationship_type(None) == "other"
    assert normalize_spdx_relationship_type("not-a-real-type") == "other"
