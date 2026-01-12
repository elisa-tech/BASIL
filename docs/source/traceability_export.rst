Traceability Matrix Export
==========================


Available Export Formats
------------------------

- SPDX (JSON-LD, DOT, PNG)
  - Generate SPDX traceability artifacts for an API (graph + data)
  - Endpoints:
    - ``GET /spdx/apis`` (produce files)
    - ``GET /spdx/apis/export-download`` (download a specific file)
- HTML
  - Generate an HTML traceability document for an API mapping view
  - Endpoint: ``GET /html/apis``
- PDF
  - Download a PDF rendering of a previously generated HTML export
  - Endpoint: ``GET /html/apis/export-download`` (use ``filename=<...>.pdf``)


SPDX 3.0.1 Traceability Matrix Export
=====================================

BASIL provides comprehensive traceability matrix export functionality using the SPDX 3.0.1 specification. This document describes how the tool exports traceability data, the schema used, and the validation process.

SPDX 3.0.1 Schema Implementation
--------------------------------

BASIL implements the SPDX 3.0.1 specification to export traceability matrices as JSON-LD documents. The export follows the official SPDX 3.0.1 schema defined at `https://spdx.github.io/spdx-spec/v3.0.1/rdf/schema.json`.

Key Schema Components
~~~~~~~~~~~~~~~~~~~~~

The exported SPDX documents include the following core elements:

- **SPDXDocument**: The root document containing metadata about the export
- **SPDXFile**: Represents work items (software requirements, test specifications, test cases, etc.)
- **SPDXRelationship**: Defines traceability relationships between work items
- **SPDXAnnotation**: Contains detailed work item data from the database
- **SPDXCreationInfo**: Metadata about creation time, tools, and users
- **SPDXPerson**: User information
- **SPDXTool**: Tool information (BASIL)

Work Item Data Mapping to Annotations
--------------------------------------

BASIL maps work item data from the database to SPDX Annotations using the following approach:

Database to Annotation Mapping
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Each work item (software requirement, test specification, test case, justification, document) is exported as:

1. **SPDXFile**: The primary SPDX element representing the work item
2. **SPDXAnnotation**: Contains the complete database record as JSON

Example Annotation Structure
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: json

    {
        "type": "Annotation",
        "annotationType": "other",
        "spdxId": "spdx:annotation:basil:software-requirement:123",
        "subject": "spdx:file:basil:software-requirement:123",
        "statement": "{\"id\": 123, \"title\": \"Requirement Title\", \"description\": \"...\", \"created_by\": 1, ...}",
        "creationInfo": "spdx:creation_info:basil:software-requirement:123"
    }

Traceability Relationships
--------------------------

BASIL exports the following types of traceability relationships:

- **hasDocumentation**: e.g.: API <- Reference document or API Reference document Snippet <- Document
- **hasRequirement**: e.g.:API Reference document Snippet <- Software Requirements or Sw Requirement <- Sw Requirement
- **hasSpecification**: e.g.:API Reference document Snippet <- Test Specifications or Sw Requirement <- Test Specification
- **hasTest**: e.g.: Test Specification <- Test Cases or Sw Requirement <- Test Case ...
- **hasEvidence**: e.g.: Test Cases <- Test Runs
- **contains**: e.g.: Library <- API

Each relationship includes:
- Source and target elements
- Relationship type
- Completeness (complete or incomplete even if BASIL is using percentage values)
- Creation metadata

Traceability Matrix Graph Generation
------------------------------------

BASIL generates visual representations of the traceability matrix:

Graph Generation Features
~~~~~~~~~~~~~~~~~~~~~~~~~~

- **DOT File**: Graphviz DOT format for programmatic graph generation
- **PNG File**: Rendered image of the traceability matrix
- **Legend**: Visual legend showing relationship types and colors

Graph Structure
~~~~~~~~~~~~~~~

The generated graph shows:
- Work items as nodes (requirements, specifications, test cases, test runs)
- Relationships as directed edges
- Color coding for different work item types
- Hierarchical layout from requirements to test runs

Test Run Integration and Limitations
------------------------------------

BASIL extends traceability to include test runs with specific limitations:

Test Run Integration
~~~~~~~~~~~~~~~~~~~~

- Test runs are linked to test cases via ``hasEvidence`` relationships
- Test run data includes execution results, timestamps
- Test runs are ordered by ID (most recent first)

Test Run Limitations
~~~~~~~~~~~~~~~~~~~~

The number of test runs included in the traceability matrix is limited to the **last 5 elements** by default. This limitation is configurable through the ``test_runs_limit`` parameter in the SPDXManager.

Configuration:
- Default limit: 5 test runs per test case
- Configurable via API parameters
- Ordered by creation time (most recent first)

CI Validation with spdx3-validate
---------------------------------

BASIL includes comprehensive validation of exported SPDX documents:

Validation Process
~~~~~~~~~~~~~~~~~~

1. **spdx3-validate Tool**: Uses the official SPDX validation tool
2. **pyshacl Backend**: spdx3-validate uses pyshacl for validation logic
3. **CI Integration**: Automated validation in continuous integration

Validation Features
~~~~~~~~~~~~~~~~~~~

- **Schema Compliance**: Validates against SPDX 3.0.1 schema
- **Relationship Integrity**: Ensures all relationships are valid
- **Data Completeness**: Checks for required fields and metadata
- **Format Validation**: Ensures proper JSON-LD structure

CI Job Configuration
~~~~~~~~~~~~~~~~~~~~

The validation is integrated into the CI pipeline:

.. code-block:: yaml

    - name: Validate SPDX Export
      run: |
        spdx3-validate --json exported_file.jsonld --spdx-version auto


Export API Endpoints
--------------------

BASIL provides the following API endpoints for SPDX export:

- **GET /spdx/apis**: Export jsonld, dot and png for a specific API
- **GET /spdx/apis/export-download**: Download one of the desired file

Parameters:
- ``api-id``: API identifier
- ``user-id``: User identifier
- ``token``: Authentication token
- ``filename``: Output filename
- ``test_runs_limit``: Number of test runs to include [Optional, only for /spdx/apis]

File Outputs
------------

The export process generates multiple files:

1. **JSON-LD File**: Main SPDX document (``.jsonld``)
2. **DOT File**: Graphviz source (``.dot``)
3. **PNG File**: Rendered graph image (``.png``)

All files are stored in user-specific directories:
``api/public/spdx_export/<user-id>/<filename>``

Security Considerations
-----------------------

- **User Isolation**: Each user can only access their own exported files
- **Path Validation**: Prevents directory traversal attacks
- **Authentication**: All exports require valid user authentication
- **File Type Validation**: Only allows specific file extensions

Usage Examples
--------------

Export SPDX for an API:

.. code-block:: bash

    curl -X GET "http://localhost:5000/spdx/apis?api-id=123&user-id=456&token=abc123&filename=my_export"

Download exported file:

.. code-block:: bash

    curl -X GET "http://localhost:5000/spdx/apis/export-download?api-id=123&user-id=456&token=abc123&filename=my_export.jsonld"

The exported SPDX documents provide comprehensive traceability information that can be used for compliance, auditing, and analysis purposes while maintaining full compatibility with the SPDX 3.0.1 specification.
