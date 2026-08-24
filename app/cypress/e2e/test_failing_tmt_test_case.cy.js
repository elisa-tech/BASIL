/// <reference types="cypress" />

/**
 * Test Run (Local test file) Creation and Verification E2E Test
 *
 *  NOTE: This test is configured to be run on API deployed as a container
 *        due to that the base path is /BASIL-API/
 *
 * This test suite validates the complete test run workflow:
 * 1. Create a software component and test case
 * 2. Add test case to user files
 * 3. Create a test run via the test case kebab menu "Run" option
 * 4. Verify the test run appears in the test results table
 * 5. Verify the test run failed
 * 6. Verify test run details are accessible and properly displayed
 * 7. Clean up test data (test runs and test cases)
 *
 * The test covers the end-to-end user experience of creating and managing test runs
 * in the BASIL test management system, ensuring proper integration between the frontend
 * UI and backend API for test execution workflows.
 *
 * Prerequisites:
 * - API should run with env variables
 *   + BASIL_TESTING=1
 *   + BASIL_ADMIN_PASSWORD=dummy_password
 * - BASIL frontend running on http://localhost:9056
 * - BASIL API running on http://localhost:5005
 * - Admin user configured with credentials from consts.json
 * - Clean database state (no conflicting test data)
 *
 * To run: `npx cypress run --spec "cypress/e2e/test_failing_tmt_test_case.cy.js"`
 * To debug: `npx cypress open` and select this test file
 */

import '../support/e2e.js'
import api_data_fixture from '../fixtures/api.json'
import const_data from '../fixtures/consts.json'
import { createUniqWorkItems } from '../support/utils.js'

// Create unique work items
let api_data = createUniqWorkItems(api_data_fixture, ['api'])

// Test Case data
const basil_root_path = Cypress.config('projectRoot').replace('/app', '/')
const test_case_file = basil_root_path + 'examples/tmt/local/tmt-dummy-failing-test.fmf'
const deployment_base_path = '/BASIL-API'
const test_case_filename = 'tmt-dummy-failing-test.fmf'

const test_case_data = {
  title: 'Failing TMT Test ' + new Date().getTime(),
  description: 'Test case for dummy failing TMT test',
  repository: deployment_base_path,
  relative_path: ''
}

// Test run data
const test_run_data = {
  title: 'E2E Test Run ' + new Date().getTime(),
  notes: 'Cypress end-to-end test run validation'
}

const test_run_config_data = {
  title: 'E2E Test Run Config ' + new Date().getTime(),
  plugin: 'tmt',
  provision_type: 'container',
  context_vars: 'plan_type=local'
}

const uiTimeout = 20000
const inProgressStatuses = ['running', 'created', 'pending']
const maxResultChecks = 24

const bindTestCaseToAdminUserFiles = () => {
  cy.window().then((win) => {
    const userId = win.localStorage.getItem('uId')
    expect(userId, 'admin user id from login session').to.be.a('string').and.not.equal('')
    test_case_data.relative_path = `/api/user-files/${userId}/${test_case_filename}`
  })
}

const openTestCaseResults = (mappingId, title) => {
  cy.visit(const_data.app_base_url + '/mapping/' + mappingId)
  cy.wait(const_data.long_wait)
  cy.get(const_data.mapping.select_view_id, { timeout: uiTimeout }).select('test-cases', { force: true })
  cy.wait(const_data.long_wait)

  cy.get('h5', { timeout: uiTimeout })
    .contains(title)
    .scrollIntoView()
    .parents('.pf-v5-c-card__body')
    .find('button[class*="menu-toggle"]')
    .click()

  cy.get('[id*="btn-menu-test-case-"]').contains(const_data.test_run.results_button_text).click()
  cy.get(const_data.test_run.results_modal_id, { timeout: uiTimeout }).should('be.visible')
  cy.get('[id*="tab-btn-test-runs-list"]').should('have.attr', 'aria-selected', 'true')
}

describe(
  'Test Run Creation and Verification',
  {
    defaultCommandTimeout: 15000,
    requestTimeout: 15000,
    viewportWidth: 1280,
    viewportHeight: 900,
    scrollBehavior: 'center'
  },
  () => {
    let apiId

    beforeEach(() => {
      cy.login_admin()
      bindTestCaseToAdminUserFiles()
    })

    it('Setup: Create SW Component', () => {
      // Add SW Component
      cy.get('#btn-add-sw-component').click()
      cy.fill_form_api('0', 'add', api_data.first, true, false)
      cy.get('#btn-modal-api-confirm').click()
      cy.wait(2000)

      // Check SW component has been created and get its ID
      cy.filter_api_from_dashboard(api_data.first)
      cy.get(const_data.api.table_listing_id)
        .find('tbody')
        .find('tr')
        .eq(0)
        .find('td')
        .eq(1)
        .invoke('text')
        .then((id) => {
          apiId = String(id).trim()

          // Navigate to mapping page
          cy.visit(const_data.app_base_url + '/mapping/' + apiId)
          cy.wait(const_data.long_wait)

          // Switch to test cases view
          cy.get(const_data.mapping.select_view_id).select('test-cases', { force: true })
          cy.wait(const_data.long_wait)
        })
    })

    it('Add Test Case to user files', () => {
      cy.add_test_case_to_user_files(test_case_file)
      cy.get('#table-user-files', { timeout: uiTimeout }).should('contain.text', test_case_filename)
    })

    it('Create Test Run via Test Case Menu', () => {
      // Navigate to mapping page with existing test case
      cy.visit(const_data.app_base_url + '/mapping/' + apiId)
      cy.wait(const_data.long_wait)

      // Switch to test cases view
      cy.get(const_data.mapping.select_view_id).select('test-cases', { force: true })
      cy.wait(const_data.long_wait)

      // Create test case for failing test
      expect(test_case_data.relative_path, 'user-files relative path').to.include('/api/user-files/')

      cy.assign_work_item(-1, 0, '', 'test-case', test_case_data)
      cy.wait(const_data.mid_wait)

      // Wait for the new test case card to appear (failing test case path can be slower)
      cy.get('.pf-v5-c-card').contains('h5', test_case_data.title, { timeout: uiTimeout }).should('be.visible')
      cy.wait(const_data.fast_wait)

      // Create test run for test
      cy.get('h5').contains(test_case_data.title).parents('.pf-v5-c-card__body').find('button[class*="menu-toggle"]').click()

      cy.get('[id*="btn-menu-test-case-"]').contains('Run').click()

      // Fill test run
      cy.get(const_data.test_run.modal_id).should('be.visible')

      cy.get('[id*="input-test-run-add-title"]').clear().type(test_run_data.title)

      cy.get('[id*="input-test-run-add-notes"]').clear().type(test_run_data.notes)

      // Switch to Test Run Config tab
      cy.get('[id*="tab-btn-test-run-config-data"]').click()
      cy.wait(const_data.fast_wait)

      // Configure test run config settings
      cy.get('[id*="input-test-run-config-title-"]')
        .clear()
        .type('Config for ' + test_run_data.title)

      cy.get('[id*="select-test-run-config-plugin-"]').select(test_run_config_data.plugin)

      cy.get('[id*="select-test-run-config-provision-type-"]').select(test_run_config_data.provision_type)

      cy.get('[id*="input-test-run-config-context-vars-"]').clear().type(test_run_config_data.context_vars)

      // Submit test run
      cy.get(const_data.test_run.form_submit_button_id).click()
      cy.wait(const_data.long_wait)
    })

    it('Verify Test Run failed', function () {
      let check_iterations = 0

      const checkResult = () => {
        check_iterations++
        if (check_iterations > maxResultChecks) {
          throw new Error('Test run did not reach failed status before timeout')
        }

        openTestCaseResults(apiId, test_case_data.title)

        cy.get(const_data.test_run.results_table_id, { timeout: uiTimeout })
          .should('be.visible')
          .contains('tbody tr', test_run_data.title, { timeout: uiTimeout })
          .find('td span[class*="pf-v5-c-label"]')
          .invoke('text')
          .then((raw) => {
            const text = raw.toLowerCase()

            if (text.includes('fail')) {
              return
            }

            if (inProgressStatuses.some((status) => text.includes(status))) {
              cy.wait(5000)
              cy.then(() => {
                checkResult()
              })
              return
            }

            throw new Error(`Test run finished with status "${text.trim()}". Expected: "fail"`)
          })
      }

      checkResult()
    })

    it('Verify Test Run Details', () => {
      openTestCaseResults(apiId, test_case_data.title)
      cy.wait(const_data.long_wait)

      // Click on our test run row to see details
      cy.get(const_data.test_run.results_table_id, { timeout: uiTimeout })
        .should('be.visible')
        .contains('tbody tr', test_run_data.title)
        .click()

      // Click Details button
      cy.get('button').contains(const_data.test_run.details_button_text).click()

      // Verify Test Run Details Modal opens
      cy.get(const_data.test_run.details_modal_id).should('be.visible')

      // Verify Info tab shows test run details
      cy.get('[id*="tab-btn-test-run-details"]').should('have.attr', 'aria-selected', 'true')

      // Verify test run information is displayed
      cy.get('h3').should('contain.text', 'Test Run')
      cy.get('p').should('contain.text', test_run_data.title)
      cy.get('p').should('contain.text', test_run_data.notes)

      // Test other tabs are available
      cy.get('[id*="tab-btn-test-run-details-log"]').should('be.visible')
      cy.get('[id*="tab-btn-test-run-bugs-fixes-notes"]').should('be.visible')
      cy.get('[id*="tab-btn-test-run-artifacts"]').should('be.visible')

      // Click on Log tab
      cy.get('[id*="tab-btn-test-run-details-log"]').click()
      cy.wait(const_data.fast_wait)

      // Verify log section is visible
      cy.get('pre#code-block-test-run-details-log.pf-v5-c-code-block__pre', { timeout: uiTimeout })
        .scrollIntoView()
        .within(() => {
          // Check for a code tag inside the pre
          cy.get('code').should('exist')
          // TMT exit code 0/1 is recorded as EXECUTION RESULT pass; the actual test result is fail
          cy.get('code')
            .should('contain.text', 'EXECUTION RESULT: pass')
            .should('contain.text', 'summary: 1 test failed')
            .should('contain.text', 'total: 1 test failed')
        })
    })

    it('Cleanup: Delete Test Run and Test Case', () => {
      openTestCaseResults(apiId, test_case_data.title)

      // Delete the test run
      cy.get(const_data.test_run.results_table_id + ' tbody tr')
        .contains(test_run_data.title)
        .parents('tr')
        .within(() => {
          cy.get('button').contains('Delete').click()
        })

      // Confirm deletion if prompted
      cy.get('body').then(($body) => {
        if ($body.find('button').filter(':contains("Confirm")').length > 0) {
          cy.get('button').contains('Confirm').click()
        }
      })

      cy.wait(const_data.mid_wait)

      // Close test results modal
      cy.get(const_data.test_run.results_modal_id).find('button[aria-label="Close"]').click()

      // Delete the test case
      cy.delete_work_item(0, 'test-case')
      cy.wait(const_data.mid_wait)

      // Verify test case is deleted
      cy.contains('h2', 'Test Case').should('not.exist')
    })
  }
)
