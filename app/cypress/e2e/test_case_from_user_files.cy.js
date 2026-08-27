/// <reference types="cypress" />

/**
 * Test Case implementation from User Files
 *
 * Covers every mapping parent that uses TestCaseForm (and therefore
 * splitUserFileToTmtPath):
 * - Test Case mapped to the Software Component (API)
 * - Test Case mapped to a Test Specification
 * - Test Case mapped to a Software Requirement
 *
 * For each parent, add and edit via "From user files" and assert the saved
 * repository + relative-path match splitUserFileToTmtPath().
 */

import '../support/e2e.js'
import api_data_fixture from '../fixtures/api.json'
import const_data from '../fixtures/consts.json'
import sr_data_fixture from '../fixtures/sw_requirement.json'
import tc_data_fixture from '../fixtures/test_case.json'
import ts_data_fixture from '../fixtures/test_specification.json'
import { createUniqWorkItems } from '../support/utils.js'

let api_data = createUniqWorkItems(api_data_fixture, ['api'])
let ts_data = createUniqWorkItems(ts_data_fixture, ['title'])
let sr_data = createUniqWorkItems(sr_data_fixture, ['title'])
let tc_data = createUniqWorkItems(tc_data_fixture, ['title'])

const unique = Date.now().toString()
const userFileName = 'tmt-dummy-test-' + unique + '.fmf'
const basil_root_path = Cypress.config('projectRoot').replace('/app', '/')
const sourceTestFile = basil_root_path + 'examples/tmt/local/tmt-dummy-test.fmf'

const uiTimeout = 20000

const visitMapping = (apiId, view) => {
  cy.visit(const_data.app_base_url + '/mapping/' + apiId)
  cy.wait(const_data.long_wait)
  if (view) {
    cy.get(const_data.mapping.select_view_id, { timeout: uiTimeout }).select(view, { force: true })
    cy.wait(const_data.long_wait)
  }
}

describe(
  'Test Case from user files',
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
    })

    it('Setup: Create SW Component', () => {
      cy.get('#btn-add-sw-component').click()
      cy.fill_form_api('0', 'add', api_data.first, true, false)
      cy.get('#btn-modal-api-confirm').click()
      cy.wait(2000)

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
        })
    })

    it('Upload a TMT user file', () => {
      cy.readFile(sourceTestFile).then((contents) => {
        cy.get('#nav-item-user-files').click()
        cy.wait(const_data.long_wait)
        cy.get('#btn-add-user-file').click()
        cy.wait(const_data.fast_wait)
        cy.get('#user-file-upload-browse-button').selectFile(
          {
            contents: Cypress.Buffer.from(contents),
            fileName: userFileName,
            mimeType: 'text/plain'
          },
          { action: 'drag-drop' }
        )
        cy.get('#btn-user-file-modal-confirm').click()
        cy.wait(const_data.long_wait)
        cy.get('#table-user-files', { timeout: uiTimeout }).should('contain.text', userFileName)
      })
    })

    it('Add and edit Test Case from user files mapped to the Software Component', () => {
      visitMapping(apiId, 'test-cases')
      cy.assign_test_case_from_user_file(-1, 0, '', tc_data.first, userFileName)
      cy.edit_test_case_from_user_file(0, tc_data.first_mod, userFileName)
      cy.delete_work_item(0, 'test-case')
    })

    it('Add and edit Test Case from user files mapped to a Test Specification', () => {
      visitMapping(apiId, 'test-specifications')
      cy.assign_work_item(-1, 0, '', 'test-specification', ts_data.first)
      cy.assign_test_case_from_user_file(0, 1, 'test-specification', tc_data.second, userFileName)
      cy.edit_test_case_from_user_file(1, tc_data.second_mod, userFileName)
      cy.delete_work_item(1, 'test-case')
      cy.delete_work_item(0, 'test-specification')
    })

    it('Add and edit Test Case from user files mapped to a Software Requirement', () => {
      visitMapping(apiId)
      cy.assign_work_item(-1, 0, '', 'sw-requirement', sr_data.first)
      cy.assign_test_case_from_user_file(0, 1, 'sw-requirement', tc_data.third, userFileName)
      cy.edit_test_case_from_user_file(1, tc_data.third_mod, userFileName)
      cy.delete_work_item(1, 'test-case')
      cy.delete_work_item(0, 'sw-requirement')
    })
  }
)
