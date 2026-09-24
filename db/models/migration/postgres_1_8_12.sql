BEGIN;

-- SPDX author signature: unique identity used as Person.name in SBOM exports.
-- Each existing user gets a distinct UUID; new users receive one in UserModel.__init__.

ALTER TABLE users ADD COLUMN IF NOT EXISTS spdx_signature VARCHAR(255);

UPDATE users
SET spdx_signature = gen_random_uuid()::text
WHERE spdx_signature IS NULL OR btrim(spdx_signature) = '';

ALTER TABLE users ALTER COLUMN spdx_signature SET NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS users_spdx_signature_key ON users (spdx_signature);

-- SPDX 2.3 / BASIL UI relationship names → SPDX 3.0.1 RelationshipType (camelCase).
-- Mapping: https://spdx.github.io/using/diffs-from-previous-editions/
-- Keep in sync with SPDX_2_TO_3_RELATIONSHIP in api/spdx_manager.py
-- Applied to documents and documents_history. Unknown leftovers become 'other'.

DROP TABLE IF EXISTS spdx_2_to_3;
CREATE TEMP TABLE spdx_2_to_3 (
    from_type TEXT PRIMARY KEY,
    to_type TEXT NOT NULL
);

INSERT INTO spdx_2_to_3 (from_type, to_type) VALUES
    -- Official SPDX 2.3
    ('AMENDS', 'amendedBy'),
    ('ANCESTOR_OF', 'ancestorOf'),
    ('BUILD_DEPENDENCY_OF', 'dependsOn'),
    ('BUILD_TOOL_OF', 'usesTool'),
    ('CONTAINED_BY', 'contains'),
    ('CONTAINS', 'contains'),
    ('COPY_OF', 'copiedTo'),
    ('DATA_FILE_OF', 'hasDataFile'),
    ('DEPENDENCY_MANIFEST_OF', 'hasDependencyManifest'),
    ('DEPENDENCY_OF', 'dependsOn'),
    ('DEPENDS_ON', 'dependsOn'),
    ('DESCENDANT_OF', 'descendantOf'),
    ('DESCRIBED_BY', 'describes'),
    ('DESCRIBES', 'describes'),
    ('DEV_DEPENDENCY_OF', 'dependsOn'),
    ('DEV_TOOL_OF', 'usesTool'),
    ('DISTRIBUTION_ARTIFACT', 'hasDistributionArtifact'),
    ('DOCUMENTATION_OF', 'hasDocumentation'),
    ('DYNAMIC_LINK', 'hasDynamicLink'),
    ('EXAMPLE_OF', 'hasExample'),
    ('EXPANDED_FROM_ARCHIVE', 'expandsTo'),
    ('FILE_ADDED', 'hasAddedFile'),
    ('FILE_DELETED', 'hasDeletedFile'),
    ('FILE_MODIFIED', 'modifiedBy'),
    ('GENERATED_FROM', 'generates'),
    ('GENERATES', 'generates'),
    ('HAS_PREREQUISITE', 'hasPrerequisite'),
    ('METAFILE_OF', 'hasMetadata'),
    ('OPTIONAL_COMPONENT_OF', 'hasOptionalComponent'),
    ('OPTIONAL_DEPENDENCY_OF', 'hasOptionalDependency'),
    ('OTHER', 'other'),
    ('PACKAGE_OF', 'packagedBy'),
    ('PATCH_FOR', 'patchedBy'),
    ('PATCH_APPLIED', 'patchedBy'),
    ('PREREQUISITE_FOR', 'hasPrerequisite'),
    ('PROVIDED_DEPENDENCY_OF', 'hasProvidedDependency'),
    ('REQUIREMENT_DESCRIPTION_FOR', 'hasRequirement'),
    ('RUNTIME_DEPENDENCY_OF', 'dependsOn'),
    ('SPECIFICATION_FOR', 'hasSpecification'),
    ('STATIC_LINK', 'hasStaticLink'),
    ('TEST_CASE_OF', 'hasTestCase'),
    ('TEST_DEPENDENCY_OF', 'dependsOn'),
    ('TEST_OF', 'hasTest'),
    ('TEST_TOOL_OF', 'usesTool'),
    ('VARIANT_OF', 'hasVariant'),
    -- BASIL UI SPDX 2-style abbreviations
    ('AFFECTS', 'affects'),
    ('ANCESTOR', 'ancestorOf'),
    ('AVAILABLE_FROM', 'availableFrom'),
    ('BUILD_DEPENDENCY', 'dependsOn'),
    ('BUILD_TOOL', 'usesTool'),
    ('COORDINATED_BY', 'coordinatedBy'),
    ('CONFIG_OF', 'configures'),
    ('COPY', 'copiedTo'),
    ('DATA_FILE', 'hasDataFile'),
    ('DEPENDENCY_MANIFEST', 'hasDependencyManifest'),
    ('DESCENDANT', 'descendantOf'),
    ('DEV_DEPENDENCY', 'dependsOn'),
    ('DEV_TOOL', 'usesTool'),
    ('DOCUMENTATION', 'hasDocumentation'),
    ('DOES_NOT_AFFECT', 'doesNotAffect'),
    ('EXAMPLE', 'hasExample'),
    ('EVIDENCE_FOR', 'hasEvidence'),
    ('EXPLOIT_CREATED_BY', 'exploitCreatedBy'),
    ('FIXED_BY', 'fixedBy'),
    ('FIXED_IN', 'fixedIn'),
    ('FOUND_BY', 'foundBy'),
    ('HAS_ASSESSMENT_FOR', 'hasAssessmentFor'),
    ('HAS_ASSOCIATED_VULNERABILITY', 'hasAssociatedVulnerability'),
    ('HOST_OF', 'hasHost'),
    ('INPUT_OF', 'hasInput'),
    ('INVOKED_BY', 'invokedBy'),
    ('METAFILE', 'hasMetadata'),
    ('ON_BEHALF_OF', 'delegatedTo'),
    ('OPTIONAL_COMPONENT', 'hasOptionalComponent'),
    ('OPTIONAL_DEPENDENCY', 'hasOptionalDependency'),
    ('OUTPUT_OF', 'hasOutput'),
    ('PACKAGES', 'packagedBy'),
    ('PATCH', 'patchedBy'),
    ('PREREQUISITE', 'hasPrerequisite'),
    ('PROVIDED_DEPENDENCY', 'hasProvidedDependency'),
    ('PUBLISHED_BY', 'publishedBy'),
    ('REPORTED_BY', 'reportedBy'),
    ('REPUBLISHED_BY', 'republishedBy'),
    ('REQUIREMENT_FOR', 'hasRequirement'),
    ('RUNTIME_DEPENDENCY', 'dependsOn'),
    ('TEST', 'hasTest'),
    ('TEST_CASE', 'hasTestCase'),
    ('TEST_DEPENDENCY', 'dependsOn'),
    ('TEST_TOOL', 'usesTool'),
    ('TESTED_ON', 'testedOn'),
    ('TRAINED_ON', 'trainedOn'),
    ('UNDER_INVESTIGATION_FOR', 'underInvestigationFor'),
    ('VARIANT', 'hasVariant'),
    -- Informal BASIL values
    ('RELATES_TO', 'other'),
    ('RELATED_TO', 'other'),
    -- SPDX 3.0.1 enum member names (HAS_DOCUMENTATION → hasDocumentation)
    ('AMENDED_BY', 'amendedBy'),
    ('CONFIGURES', 'configures'),
    ('COPIED_TO', 'copiedTo'),
    ('DELEGATED_TO', 'delegatedTo'),
    ('EXPANDS_TO', 'expandsTo'),
    ('HAS_ADDED_FILE', 'hasAddedFile'),
    ('HAS_CONCLUDED_LICENSE', 'hasConcludedLicense'),
    ('HAS_DATA_FILE', 'hasDataFile'),
    ('HAS_DECLARED_LICENSE', 'hasDeclaredLicense'),
    ('HAS_DELETED_FILE', 'hasDeletedFile'),
    ('HAS_DEPENDENCY_MANIFEST', 'hasDependencyManifest'),
    ('HAS_DISTRIBUTION_ARTIFACT', 'hasDistributionArtifact'),
    ('HAS_DOCUMENTATION', 'hasDocumentation'),
    ('HAS_DYNAMIC_LINK', 'hasDynamicLink'),
    ('HAS_EVIDENCE', 'hasEvidence'),
    ('HAS_EXAMPLE', 'hasExample'),
    ('HAS_HOST', 'hasHost'),
    ('HAS_INPUT', 'hasInput'),
    ('HAS_METADATA', 'hasMetadata'),
    ('HAS_OPTIONAL_COMPONENT', 'hasOptionalComponent'),
    ('HAS_OPTIONAL_DEPENDENCY', 'hasOptionalDependency'),
    ('HAS_OUTPUT', 'hasOutput'),
    ('HAS_PROVIDED_DEPENDENCY', 'hasProvidedDependency'),
    ('HAS_REQUIREMENT', 'hasRequirement'),
    ('HAS_SPECIFICATION', 'hasSpecification'),
    ('HAS_STATIC_LINK', 'hasStaticLink'),
    ('HAS_TEST', 'hasTest'),
    ('HAS_TEST_CASE', 'hasTestCase'),
    ('HAS_VARIANT', 'hasVariant'),
    ('MODIFIED_BY', 'modifiedBy'),
    ('PACKAGED_BY', 'packagedBy'),
    ('PATCHED_BY', 'patchedBy'),
    ('SERIALIZED_IN_ARTIFACT', 'serializedInArtifact'),
    ('USES_TOOL', 'usesTool');

UPDATE documents AS d
SET spdx_relation = m.to_type
FROM spdx_2_to_3 AS m
WHERE d.spdx_relation IS NOT NULL
  AND btrim(d.spdx_relation) <> ''
  AND replace(replace(upper(btrim(d.spdx_relation)), ' ', '_'), '-', '_') = m.from_type
  AND d.spdx_relation IS DISTINCT FROM m.to_type;

UPDATE documents_history AS d
SET spdx_relation = m.to_type
FROM spdx_2_to_3 AS m
WHERE d.spdx_relation IS NOT NULL
  AND btrim(d.spdx_relation) <> ''
  AND replace(replace(upper(btrim(d.spdx_relation)), ' ', '_'), '-', '_') = m.from_type
  AND d.spdx_relation IS DISTINCT FROM m.to_type;

UPDATE documents
SET spdx_relation = 'other'
WHERE spdx_relation IS NOT NULL
  AND btrim(spdx_relation) <> ''
  AND spdx_relation NOT IN (
    'affects', 'amendedBy', 'ancestorOf', 'availableFrom', 'configures', 'contains',
    'coordinatedBy', 'copiedTo', 'delegatedTo', 'dependsOn', 'descendantOf', 'describes',
    'doesNotAffect', 'expandsTo', 'exploitCreatedBy', 'fixedBy', 'fixedIn', 'foundBy',
    'generates', 'hasAddedFile', 'hasAssessmentFor', 'hasAssociatedVulnerability',
    'hasConcludedLicense', 'hasDataFile', 'hasDeclaredLicense', 'hasDeletedFile',
    'hasDependencyManifest', 'hasDistributionArtifact', 'hasDocumentation',
    'hasDynamicLink', 'hasEvidence', 'hasExample', 'hasHost', 'hasInput', 'hasMetadata',
    'hasOptionalComponent', 'hasOptionalDependency', 'hasOutput', 'hasPrerequisite',
    'hasProvidedDependency', 'hasRequirement', 'hasSpecification', 'hasStaticLink',
    'hasTest', 'hasTestCase', 'hasVariant', 'invokedBy', 'modifiedBy', 'other',
    'packagedBy', 'patchedBy', 'publishedBy', 'reportedBy', 'republishedBy',
    'serializedInArtifact', 'testedOn', 'trainedOn', 'underInvestigationFor', 'usesTool'
  );

UPDATE documents_history
SET spdx_relation = 'other'
WHERE spdx_relation IS NOT NULL
  AND btrim(spdx_relation) <> ''
  AND spdx_relation NOT IN (
    'affects', 'amendedBy', 'ancestorOf', 'availableFrom', 'configures', 'contains',
    'coordinatedBy', 'copiedTo', 'delegatedTo', 'dependsOn', 'descendantOf', 'describes',
    'doesNotAffect', 'expandsTo', 'exploitCreatedBy', 'fixedBy', 'fixedIn', 'foundBy',
    'generates', 'hasAddedFile', 'hasAssessmentFor', 'hasAssociatedVulnerability',
    'hasConcludedLicense', 'hasDataFile', 'hasDeclaredLicense', 'hasDeletedFile',
    'hasDependencyManifest', 'hasDistributionArtifact', 'hasDocumentation',
    'hasDynamicLink', 'hasEvidence', 'hasExample', 'hasHost', 'hasInput', 'hasMetadata',
    'hasOptionalComponent', 'hasOptionalDependency', 'hasOutput', 'hasPrerequisite',
    'hasProvidedDependency', 'hasRequirement', 'hasSpecification', 'hasStaticLink',
    'hasTest', 'hasTestCase', 'hasVariant', 'invokedBy', 'modifiedBy', 'other',
    'packagedBy', 'patchedBy', 'publishedBy', 'reportedBy', 'republishedBy',
    'serializedInArtifact', 'testedOn', 'trainedOn', 'underInvestigationFor', 'usesTool'
  );

DROP TABLE IF EXISTS spdx_2_to_3;

COMMIT;
