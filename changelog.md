# CHANGE LOG

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
