# Software Requirements Import Feature

## Overview

BASIL provides a flexible import feature that allows users to import Software Requirements from various file formats. This feature supports both BASIL-exported files and third-party formats, making it easy to migrate requirements from different tools or import bulk requirements data.

## Supported File Formats

The import feature supports the following file formats:

| Format | Extensions | Description |
|--------|-----------|-------------|
| JSON (Simple) | `.json` | Simple JSON array or object with title and description fields |
| JSON (BASIL SPDX) | `.json`, `.jsonld` | BASIL-exported SPDX JSON-LD format with @graph structure |
| JSON (StrictDoc) | `.json`, `.jsonld` | StrictDoc SPDX JSON-LD export format |
| CSV | `.csv` | Semicolon-delimited CSV with header row |
| YAML | `.yaml`, `.yml` | YAML list format with key-value pairs |
| Excel | `.xlsx` | Excel spreadsheet format |

## How to Use

### Step 1: Access the Import Feature

1. Navigate to the **Mapping** section in BASIL
2. Click the **"Add Software Component"** button
3. In the modal that opens, select the **"Import"** tab

### Step 2: Upload Your File

1. Drag and drop your file into the upload area, or click to browse
2. The system will automatically detect the file format based on the extension
3. Once uploaded, the file will be parsed automatically

### Step 3: Review and Select Requirements

1. After successful parsing, a table will display all detected requirements
2. Review the requirements in the table (ID, Title, Description)
3. Select the requirements you want to import using:
   - Individual checkboxes for specific requirements
   - **Select All** button to select all requirements
   - **Shift+Click** to select a range of requirements

### Step 4: Import

1. Click the **"Import"** button
2. Wait for the confirmation message: "Requirements imported!"
3. The imported requirements will now be available in your project

## File Format Specifications

### 1. Simple JSON Format

The simplest format uses a JSON array of objects with `title` and `description` fields.

**Mandatory Fields:**
- `title` (required) - The requirement title
- `description` (required) - The requirement description

**Optional Fields:**
- `id` (optional) - An identifier for the requirement

**Example (`reqs.json`):**
```json
[
  {
    "id": "REQ1",
    "title": "User Authentication",
    "description": "The system shall provide user authentication using username and password"
  },
  {
    "title": "Data Encryption",
    "description": "All sensitive data shall be encrypted at rest and in transit"
  },
  {
    "id": "REQ3",
    "title": "Session Timeout",
    "description": "User sessions shall automatically expire after 30 minutes of inactivity"
  }
]
```

**Single Object Format:**
```json
{
  "title": "Single Requirement",
  "description": "This is a single requirement example"
}
```

### 2. CSV Format

CSV files should be semicolon-delimited with a header row containing column names.

**Format Requirements:**
- Delimiter: semicolon (`;`)
- Header row: Must contain `title` and `description` (case-insensitive)
- Optional fields: `id`

**Example (`reqs.csv`):**
```csv
;;;;;;
;id;title;description;;;
;REQ1;User Authentication;The system shall provide user authentication using username and password;;;
;REQ2;Data Encryption;All sensitive data shall be encrypted at rest and in transit;;;
;REQ3;Session Timeout;User sessions shall automatically expire after 30 minutes of inactivity;;;
```

**Minimal Format:**
```csv
title;description
User Authentication;The system shall provide user authentication using username and password
Data Encryption;All sensitive data shall be encrypted at rest and in transit
Session Timeout;User sessions shall automatically expire after 30 minutes of inactivity
```

### 3. YAML Format

YAML files should contain a list of requirements as key-value pairs.

**Format Requirements:**
- List format (array of objects)
- Each object must have `title` and `description` keys
- Multi-line descriptions supported using `|` syntax

**Example (`reqs.yaml`):**
```yaml
- id: REQ1
  title: User Authentication
  description: |
    The system shall provide user authentication using username and password.
    Authentication credentials shall be validated against the user database.

- title: Data Encryption
  description: |
    All sensitive data shall be encrypted at rest and in transit.
    Encryption shall use industry-standard algorithms (AES-256).

- id: REQ3
  title: Session Timeout
  description: User sessions shall automatically expire after 30 minutes of inactivity
```

**Single Object Format:**
```yaml
title: Single Requirement
description: This is a single requirement example
```

### 4. Excel (XLSX) Format

Excel files should have a worksheet with column headers and data rows.

**Format Requirements:**
- Column headers in the first row: `title`, `description` (case-insensitive)
- Optional column: `id`
- Data rows follow the header row

**Example Structure:**

| id | title | description |
|----|-------|-------------|
| REQ1 | User Authentication | The system shall provide user authentication using username and password |
| REQ2 | Data Encryption | All sensitive data shall be encrypted at rest and in transit |
| REQ3 | Session Timeout | User sessions shall automatically expire after 30 minutes of inactivity |

### 5. BASIL SPDX JSON-LD Format (Export/Import)

BASIL's native export format uses SPDX JSON-LD with a `@graph` structure.

**Format Characteristics:**
- Uses SPDX 3.0.1 context
- Requirements represented as `software_File` with `software_primaryPurpose: "requirement"`
- Requirement data stored in associated Annotation statements
- Supports roundtrip export/import

**Example Structure:**
```json
{
  "@context": "https://spdx.org/rdf/3.0.1/spdx-context.jsonld",
  "@graph": [
    {
      "type": "Annotation",
      "annotationType": "other",
      "spdxId": "spdx:annotation:basil:software-requirement:1",
      "subject": "spdx:file:basil:software-requirement:1",
      "statement": "{\"id\": 1, \"title\": \"User Authentication\", \"description\": \"The system shall provide user authentication...\"}"
    },
    {
      "type": "software_File",
      "software_primaryPurpose": "requirement",
      "spdxId": "spdx:file:basil:software-requirement:1"
    }
  ]
}
```

### 6. StrictDoc SPDX JSON-LD Format

Import requirements exported from StrictDoc in SPDX JSON-LD format.

**Format Characteristics:**
- Uses SPDX context
- Requirements identified as Snippets with name starting with "Requirement '"
- Extracts id, title, and description from snippet data

**Example Structure:**
```json
{
  "@context": "https://spdx.org/rdf/3.0.1/spdx-context.jsonld",
  "@graph": [
    {
      "type": "Snippet",
      "spdxId": "spdx:snippet:req1",
      "name": "Requirement 'REQ1'",
      "snippetFromFile": "spdx:file:document",
      "comment": "User Authentication",
      "description": "The system shall provide user authentication using username and password"
    }
  ]
}
```

## Important Notes

### Data Validation
- All requirements must have both `title` and `description` fields
- Empty or missing mandatory fields will cause the requirement to be filtered out
- The `id` field is optional and not used for duplicate detection

### Duplicate Handling
- **Note:** The import feature does NOT check for duplicate requirements
- If you import the same file multiple times, duplicate requirements will be created
- Review existing requirements before importing to avoid duplicates

### User Attribution
- All imported requirements are automatically attributed to the user performing the import
- The `created_by` field is set to the importing user
- The `edited_by` field is initially set to the same user

### Requirement Status
- All imported requirements start with status **"NEW"**
- You can change the status after import using the requirement editing features

### Permissions
- Only users with **write permissions** can import requirements
- Guest users cannot import requirements
- Session must be active during import

## Troubleshooting

### "Error loading data"

**Possible causes:**
- Invalid file format
- Missing mandatory fields (title or description)
- Malformed JSON, YAML, or CSV syntax

**Solutions:**
1. Verify your file follows one of the supported formats above
2. Ensure all requirements have both `title` and `description` fields
3. Validate JSON/YAML syntax using an online validator
4. Check that CSV uses semicolon delimiters

### "Please, select at least one row."

**Cause:** No requirements selected before clicking Import

**Solution:** Select one or more requirements using checkboxes before clicking Import

### "Session expired, please login in again."

**Cause:** Your authentication session has expired

**Solution:** Log out and log back in to BASIL, then retry the import

### No requirements shown after file upload

**Possible causes:**
- File contains no valid requirements
- All requirements missing mandatory fields
- File encoding issues

**Solutions:**
1. Open your file in a text editor and verify the content
2. Ensure file is UTF-8 encoded
3. Check that at least one requirement has both title and description
4. Try a simple test file with one requirement to verify the import works

### Import button not responding

**Cause:** Backend API not available or network issue

**Solution:**
1. Check that the BASIL API is running
2. Verify network connectivity
3. Check browser console for error messages
4. Refresh the page and try again

## API Reference (For Developers)

### Endpoint
```
POST/PUT /import/sw-requirements
```

### POST Method - Preview Requirements

**Purpose:** Extract and preview requirements from file before import

**Request Body:**
```json
{
  "file_name": "reqs.json",
  "file_content": "base64_or_text_content"
}
```

**Response (200 OK):**
```json
{
  "sw_requirements": [
    {
      "id": "REQ1",
      "title": "User Authentication",
      "description": "The system shall provide user authentication..."
    }
  ]
}
```

**Error Responses:**
- `400 Bad Request` - Missing required fields
- `401 Unauthorized` - Invalid or expired session

### PUT Method - Create Requirements

**Purpose:** Create selected requirements in the database

**Request Body:**
```json
{
  "file_content": "original_file_content",
  "items": [
    {
      "id": "REQ1",
      "title": "User Authentication",
      "description": "The system shall provide user authentication..."
    }
  ],
  "user-id": "123",
  "token": "auth_token"
}
```

**Response (200 OK):**
```json
{
  "sw_requirements": [
    {
      "id": 1,
      "title": "User Authentication",
      "description": "The system shall provide user authentication...",
      "status": "NEW",
      "created_by_id": 123,
      "created_at": "2025-11-17T10:30:00",
      "updated_at": "2025-11-17T10:30:00"
    }
  ]
}
```

**Error Responses:**
- `400 Bad Request` - Missing required fields
- `401 Unauthorized` - Invalid session or insufficient permissions

### Backend Implementation

**Location:** `api/import_manager.py`

**Key Class:** `ImportSwRequirements`

**Parser Methods:**
- `JsonToSelect()` - Simple JSON parsing
- `BasilSPDXJsonRequirementsToSelect()` - BASIL SPDX format
- `StrictDocJsonRequirementsToSelect()` - StrictDoc SPDX format
- `CSVToSelect()` - CSV parsing
- `YAMLToSelect()` - YAML parsing
- `XlsxToSelect()` - Excel parsing

**Database Model:** `db/models/sw_requirement.py` - `SwRequirementModel`

### Frontend Implementation

**Location:** `app/src/app/Mapping/Import/SwRequirementImport.tsx`

**Component:** `SwRequirementImport`

**Features:**
- File upload with drag-and-drop
- Automatic format detection
- Preview table with selection
- Bulk operations (Select All/Deselect All)
- Range selection with Shift+Click

## Example Workflows

### Workflow 1: Import from Simple JSON

1. Create a `requirements.json` file:
```json
[
  {
    "title": "Security Requirement",
    "description": "The system shall implement role-based access control"
  },
  {
    "title": "Performance Requirement",
    "description": "The system shall respond to user requests within 2 seconds"
  }
]
```

2. Open BASIL and navigate to Mapping section
3. Click "Add Software Component" → "Import" tab
4. Upload `requirements.json`
5. Review the 2 requirements in the table
6. Click "Select All" then "Import"
7. Verify success message

### Workflow 2: Import from CSV Spreadsheet

1. Open Excel or any spreadsheet application
2. Create columns: `title` and `description`
3. Add your requirements as rows
4. Save as CSV with semicolon delimiter
5. Upload to BASIL Import feature
6. Select desired requirements
7. Click Import

### Workflow 3: Migrate from StrictDoc

1. Export requirements from StrictDoc in SPDX JSON-LD format
2. Upload the exported `.spdx.jsonld` file to BASIL
3. BASIL automatically detects StrictDoc format
4. Review parsed requirements
5. Select and import

## Testing

The import feature includes comprehensive E2E tests using Cypress.

**Test File:** `app/cypress/e2e/import_sw_requirement.cy.js`

**Test Coverage:**
- CSV import
- Simple JSON import
- StrictDoc SPDX import
- YAML import
- Excel (XLSX) import
- BASIL SPDX JSON-LD import

**Running Tests:**
```bash
cd app
npm run test:e2e
```

## See Also

- [CLAUDE.md](CLAUDE.md) - Development setup and architecture
- [README.md](README.md) - General BASIL documentation
- SPDX Specification: https://spdx.org/
- StrictDoc Documentation: https://strictdoc.readthedocs.io/