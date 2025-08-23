# CHANGE LOG

## 1.7.x

- API Testing extended to support user management
- LAVA (Linaro Automated Validation Architecture) Test Run Pluing
- Fix npm vulnerabilities
- Extended to other browsers other than Chrome
- Data Auto Refresh (Notification, Test Runs)
- Email notification: support for SMTP_SSL and introduction of HTML template
- Fix UI issues in mapping view for specifications with long lines
- Fix bug on deletion of all the notifications
- Uniform percentage values format
- Expose user username instead of user email
- Added test cases to the e2e suite
- Added test cases to the api unit test suite
- Send write permission requests from within the application
- Added notification filters for software component owners and list of users
- Add in-app AI suggestions using openai API
- Support LAVA Test execution using a file from user files
- Links to ELISA Discord

## 1.6.x

- SPDX export based on Model 3
- Software Requirements import from SPDX Model 3 BASIL files, StrictDoc, yaml json, csv and xlsx
- Deployment script
- Containerfile to deploy the API project on Debian
- Moved sqlite3 db to db/sqlite3 to simplify volume mapping
- Enabled e2e testing for Login in CI
- Updated scripts and documentation to use podman
- tmt support to execute tests from files stored in the API machine
- User files managament (user can upload files to reuse as ref docs, documents or test cases)
- Form key events management
- Fix conflicts in work item mapping
- UI refinement: table compact, icons alignment, modal buttons and form validations
- User permission management via UI and possibility to copy user permission across different software components
- Reset password via email
- Email server configurable from UI by admin users
- Re-enabled e2e Testing (moved under app/ folder)
- Fix api/api.py parent api calculation for mapping nested under sw requirements
- Fix user permission check in api/api.py to better support GUEST role access
- Test Case import from remote repository (tmt)

## 1.5.x

- Test Run Plugins
  Adding support for Gitlab CI, GitHub Actions, Testing Farm and KernelCI
  as external test environment. It will be possible to navigate results and to
  trigger test execution in such environments.
- Test Run Plugins Presets. Admin will be able to define some presets configurations
  for each supported test run plugins. Users can override same value filing test requests.
- Highlight current page on the sidebar menu

## 1.4.x

- Api pagination
- By default, sort api by name, library_version instead of by id
- Show and manage unmapped Document
- Avoid to increase the api version on case of last_coverage (field used as cached coverage value) changes
- Fix warning of Document work items
- Fix document link
- Fix Dockerfile-api to init tmt to configure test execution framework

## 1.3.x

- Document work item

## 1.2.x

- Test Case execution via tmt
- User SSH Keys management
- SW Component Default View
- BASIL Version available at api endpoint

## 1.1.x

- Markdown support
- Notification
- User Management
