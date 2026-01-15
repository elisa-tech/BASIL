# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

BASIL (The FuSa Spice) is an open-source software quality management tool for managing work item traceability in functional safety contexts. It consists of:
- **API** - Python Flask backend with REST API
- **APP** - React frontend with PatternFly UI
- **DB** - PostgreSQL database with SQLAlchemy ORM

## Quick Start

### First-Time Setup

1. **Install PDM** (Python package manager):
   ```bash
   pip install pdm
   ```

2. **Install dependencies**:
   ```bash
   pdm install                    # Backend dependencies
   cd app && npm install          # Frontend dependencies
   ```

3. **Set up PostgreSQL**:
   - Install PostgreSQL 15+ from https://www.postgresql.org/download/
   - Run the initialization script:
     ```bash
     psql -U postgres -f init_postgres.sql
     ```
   - This creates the `basil-admin` user and `basil`/`test` databases

4. **Configure environment** (edit `.env` file):
   ```bash
   BASIL_DB_PORT=5432
   BASIL_DB_PASSWORD=test123
   BASIL_TESTING=1
   ```

5. **Initialize database schema**:
   ```bash
   cd db/models
   pdm run python3 init_db.py test
   ```

### Run Demo (Windows)

**Easy way** - Use the batch file:
```cmd
start_api.bat
```

**Or manually**:
```bash
# Terminal 1: Start backend API
pdm run python3 api/api.py

# Terminal 2: Start frontend
cd app
npm run start:dev
```

**Access the application:**
- Frontend: http://localhost:9000
- Backend API: http://localhost:5000
- Login: `admin` / `dummy_password`

## Development Commands

### Database Initialization
```bash
# Initialize the database (run from project root)
cd db/models
pdm run python3 init_db.py
# Creates db/sqlite3/basil.db (default) or connects to PostgreSQL if configured
```

### API (Backend)
```bash
# Install dependencies (run from project root)
pdm install

# Run development server
pdm run python3 api/api.py

# Run tests
pdm run pytest

# Run linter
pdm run flake8
```

### APP (Frontend)
```bash
# Install dependencies (run from app directory)
cd app
npm install

# Run development server (port 9000)
npm run start:dev

# Build for production
npm run build

# Run linter
npm run lint

# Format code
npm run format

# Run type checking
npm run type-check

# Run all CI checks (type-check + lint + test)
npm run ci-checks
```

### End-to-End Testing
```bash
# Run Cypress E2E tests (run from app directory)
# Note: Backend must be running on port 5000, frontend on port 9000
cd app
npx cypress run

# Open Cypress interactive mode
npx cypress open
```

**Before running Cypress tests, ensure:**
- API is running: `pdm run python3 api/api.py` (default port 5000)
- Frontend is running: `cd app && npm run start:dev` (default port 9000)
- Configuration in `cypress/fixtures/consts.json` matches your ports (both should be on port 5000 and 9000)

### Deployment
```bash
# Deploy with Podman containers (run from project root)
./run_demo.sh -b 5000 -u 'http://localhost' -f 9000 -p 'admin_password' -w 'db_password'

# Parameters:
# -b: API port (default 5000)
# -f: Frontend port (default 9000)
# -u: Base URL (e.g., http://192.168.1.15)
# -p: Admin password
# -w: PostgreSQL password
# -d: API distro (fedora or debian, default fedora)
# -t: Testing mode (1 to enable)
```

## Architecture

### API Architecture (Flask + SQLAlchemy)

**Core Pattern: RESTful Resource-Based API**
- `api/api.py` contains ~60 Flask-RESTful resources organized by domain
- Each resource handles HTTP methods (GET/POST/PUT/DELETE) for specific endpoints
- Database connection managed via `db/db_orm.py` with request-scoped sessions

**Database Models** (`db/models/`):
- **Base class**: `DbBase` - Common fields (id, title, description, status, timestamps)
- **Work items**: `ApiModel`, `SwRequirementModel`, `TestSpecificationModel`, `TestCaseModel`, `DocumentModel`, `JustificationModel`
- **Mapping models**: Many-to-many relationships with metadata (e.g., `ApiSwRequirementModel`, `SwRequirementTestCaseModel`)
- **History tracking**: Each model has a `*HistoryModel` variant for version tracking
- **Test execution**: `TestRunModel`, `TestRunConfigModel` for test infrastructure

**Permission System**:
- Per-API user-based access control (read, write, delete, manage permissions)
- Stored as JSON string arrays of user IDs in API model
- Helper functions: `get_api_user_permissions()`, decorators like `@check_api_user_write_permission`

**Test Infrastructure Integration**:
- Plugin-based test runner framework in `api/testrun*.py`
- Base class: `TestRunnerBasePlugin` with abstract lifecycle methods
- Implementations: `tmt`, `LAVA`, `GitHub Actions`, `GitLab CI`, `Testing Farm`
- Configuration via `TestRunConfig` with presets in `api/configs/testrun_plugin_presets.yaml`

**Key API Modules**:
- `api/spdx_manager.py` - SPDX 3.0 SBOM import/export
- `api/import_manager.py` - Import requirements/test cases from various formats
- `api/ai.py` - OpenAI integration for AI suggestions
- `api/notifier.py` - User notification system

### Frontend Architecture (React + PatternFly)

**State Management**:
- `AuthProvider` Context (in `app/src/app/User/AuthProvider.tsx`) for global auth state
- Component-level state using React hooks (useState, useEffect)
- No Redux; state passed via props or Context API

**Routing**:
- Centralized route configuration in `app/src/app/routes.tsx`
- React Router DOM v5 for client-side routing
- Key routes: `/` (Dashboard), `/mapping/:api_id` (Mapping view), `/admin` (User management)

**Component Organization**:
```
app/src/app/
├── Admin/              # User management
├── AppLayout/          # Main layout with nav/header
├── Common/             # Shared components (Alert, Modal)
├── Dashboard/          # API listing
├── Mapping/            # Core mapping visualization & forms
├── Login/              # Authentication
├── User/               # Auth context
├── SSHKey/             # SSH key management
└── UserFiles/          # File management
```

**API Communication**:
- Uses fetch API with base URL from `Constants.API_BASE_URL`
- Authentication via query parameters (user-id, token)
- Typical pattern: GET/POST/DELETE with JSON payloads

**UI Framework**:
- PatternFly React v5 for all UI components
- Custom modals for forms (20+ modal types in Mapping view)
- Tables with expandable rows for hierarchical data

### Database Schema

**PostgreSQL-based** (default: SQLite for development):
- Connection configured via environment variables:
  - `BASIL_DB_PORT` (default: 5432)
  - `BASIL_DB_PASSWORD`
- Database name: `basil` (production) or `test` (testing)

**Key Relationships**:
- APIs have many Software Requirements, Test Specifications, Documents
- Software Requirements can have parent/child relationships (hierarchical)
- Test Specifications map to Test Cases
- Software Requirements map to Test Cases (direct traceability)
- All mappings store coverage percentage and offset/section matching data

## Testing

### Backend Tests (pytest)
```bash
# Run from project root
pdm run pytest

# Configuration in pyproject.toml:
# - pythonpath includes api/
# - testpaths set to api/test/
```

Test categories:
- API endpoint tests (`api/test/test_api.py`)
- Mapping validation (`test_*_mapping.py`)
- Import functionality (`test_sw_requirement_import.py`)
- External integrations (`test_testrun_*.py`)

### Frontend Tests (Jest)
```bash
cd app
npm test              # Run Jest tests
npm test -- -u        # Update snapshots
npm run test:watch    # Watch mode
npm run test:coverage # Coverage report
```

**Jest Configuration:**
- Config file: `app/jest.config.js`
- Setup file: `app/src/setupTests.ts`
- Babel config: `app/babel.config.js`
- Mocks: `app/__mocks__/`

**Key features:**
- TypeScript/JSX support via ts-jest and babel-jest
- PatternFly React components transformed
- Fetch API polyfilled (whatwg-fetch)
- Auth context mocked in tests
- CSS modules and assets mocked

**Current status (as of last run):**
- 216 backend tests passing ✅
- Frontend tests configured and running ✅

### E2E Tests (Cypress)
```bash
# Run from app directory
cd app
npx cypress run          # Headless mode
npx cypress open         # Interactive mode
```

Configuration in `app/cypress.config.js`:
- Specs: `cypress/e2e/**/*.cy.{js,jsx,ts,tsx}`
- Fixtures: `cypress/fixtures/`
- Support: `cypress/support/e2e.js`

## Pre-commit Hooks

Configured in `.pre-commit-config.yaml`:
1. `flake8` - Python linting
2. `prettier` - JavaScript/TypeScript formatting
3. `eslint` - React linting
4. `sphinx-build` - Documentation validation
5. `tmt lint` - Test metadata linting
6. `app_build` - Frontend build validation
7. `version_check` - Version consistency check

## Environment Variables

**Configuration file:** `.env` (create in project root)

**API**:
- `BASIL_DB_PORT` - PostgreSQL port (default: 5432)
- `BASIL_DB_PASSWORD` - Database password
- `BASIL_TESTING` - Set to `1` for test mode
- `BASIL_ADMIN_PASSWORD` - Initial admin user password
- `OPENAI_API_KEY` - For AI features (optional)

**Frontend**:
- `API_ENDPOINT` - Backend API URL (build-time)
- `APP_PORT` - Frontend server port (build-time)

**Windows Startup Scripts:**
- `start_api.bat` - Batch file to start API with environment variables
- `start_api.ps1` - PowerShell script to start API
- `init_postgres.sql` - PostgreSQL database initialization script

## Key Development Notes

### When Adding New Work Item Types
1. Create model in `db/models/` extending `DbBase`
2. Create history model variant
3. Add mapping model to relate it to APIs
4. Create Flask-RESTful Resource in `api/api.py`
5. Add React components in `app/src/app/Mapping/`
6. Update type definitions if using TypeScript

### When Adding Test Runner Plugins
1. Create plugin class extending `TestRunnerBasePlugin` in `api/testrun_*.py`
2. Implement required methods: `validate()`, `run()`, `get_result()`
3. Add preset configuration to `api/configs/testrun_plugin_presets.yaml`
4. Register plugin in TestRun resource handler

### Database Migrations
Database schema changes are managed via:
1. Update model classes in `db/models/`
2. Run `db/models/init_db.py` to recreate schema (development)
3. For production, use migration scripts in `db/models/migration/`

### Specification Mapping
When a user maps a specification section to a work item:
- Store offset/section in mapping model (e.g., `ApiSwRequirementModel.offset`, `ApiSwRequirementModel.section`)
- Use `get_split_sections()` to extract specification text
- Validate mappings with `check_direct_work_items_against_another_spec_file()`
- Update coverage percentage after changes

### Permission Checking
Always check permissions before modifying work items:
```python
from api.api import check_user_api_write_permissions
permission_level = check_user_api_write_permissions(api_id, user_id, session)
if permission_level == "none":
    return {"msg": "Permission denied"}, 403
```

## Documentation

- **[SOFTWARE_REQUIREMENTS_IMPORT.md](SOFTWARE_REQUIREMENTS_IMPORT.md)** - Comprehensive guide for the Software Requirements import feature
  - Supported file formats (JSON, CSV, YAML, XLSX, BASIL SPDX, StrictDoc SPDX)
  - Step-by-step user guide
  - File format specifications with examples
  - Troubleshooting section
  - API reference for developers

## Important Files

- `api/api.py` - Main API with all endpoints (~60 resources)
- `db/db_orm.py` - Database connection management
- `db/models/init_db.py` - Database initialization
- `app/src/app/routes.tsx` - Frontend route configuration
- `app/src/app/User/AuthProvider.tsx` - Authentication context
- `app/jest.config.js` - Jest unit test configuration
- `app/babel.config.js` - Babel transpilation config for Jest
- `app/cypress.config.js` - Cypress E2E test config
- `run_demo.sh` - Deployment script (Linux/Mac)
- `start_api.bat` / `start_api.ps1` - Windows startup scripts
- `.env` - Environment configuration
- `init_postgres.sql` - PostgreSQL setup script
- `pyproject.toml` - Python dependencies and project metadata
- `app/package.json` - Frontend dependencies and scripts

## Python Version Compatibility

**Supported:** Python 3.9 - 3.13
**Tested on:** Python 3.13.5

**Key dependency notes:**
- SQLAlchemy 2.0.44+ required for Python 3.13 (upgraded from 2.0.19)
- All tests passing on Python 3.13 with updated dependencies

## Common Issues & Solutions

### PostgreSQL Connection Issues
If you see "connection refused" errors:
1. Ensure PostgreSQL is running
2. Check `BASIL_DB_PASSWORD` in `.env` matches your PostgreSQL password
3. Verify the `basil-admin` user exists: `psql -U postgres -c "\du"`

### Frontend Test Issues
If Jest can't parse files:
- Ensure `app/jest.config.js` exists
- Check `app/babel.config.js` is present
- Verify `whatwg-fetch` is installed: `npm list whatwg-fetch`

### Cypress Port Mismatch
Cypress expects:
- Frontend on port 9000
- Backend on port 5000
Update `app/cypress/fixtures/consts.json` if using different ports

## Development Workflow

1. **Start backend**: `pdm run python3 api/api.py`
2. **Start frontend**: `cd app && npm run start:dev`
3. **Run backend tests**: `pdm run pytest`
4. **Run frontend tests**: `cd app && npm test`
5. **Run E2E tests**: `cd app && npx cypress open` (with both services running)
