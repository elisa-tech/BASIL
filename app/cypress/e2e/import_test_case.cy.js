/// <reference types="cypress" />

import '../support/e2e.ts'
import api_data_fixture from '../fixtures/api.json'
import const_data from '../fixtures/consts.json'
import { createUniqWorkItems } from '../support/utils.js'

// Create uniq work items
// Appending to each dictionary of the fixture data a date string to a target field
let api_data = createUniqWorkItems(api_data_fixture, ['api'])

describe('Test Case Import', () => {
  beforeEach(() => {
    cy.login_admin()
  })

  it('Add SW Component', () => {
    //Add SW Component
    cy.get('#btn-add-sw-component').click()
    cy.fill_form_api('0', 'add', api_data.first, true, false)
    cy.get('#btn-modal-api-confirm').click()
    cy.wait(2000)
    //Check Sw component has been created
    cy.filter_api_from_dashboard(api_data.first)
  })

  it('Scan tmt repository and import from json', () => {
    let id

    // Select the api from the list
    cy.filter_api_from_dashboard(api_data.first)

    cy.get(const_data.api.table_listing_id)
      .find('tbody')
      .find('tr')
      .eq(0)
      .find('td')
      .eq(1)
      .invoke('text')
      .then((elem) => {
        id = elem
        cy.visit(const_data.app_base_url + '/mapping/' + id)
        cy.wait(const_data.long_wait)
        cy.get('#btn-mapping-new-test-case').click()
        cy.get('#pf-tab-3-tab-btn-test-case-import').click()
        cy.get('#btn-test-case-import-scan-remote-repository').click()
        cy.get('#input-test-case-import-repository-url')
          .type('{selectAll}{del}')
          .type(const_data.import.test_cases.repository)
          .should('have.value', const_data.import.test_cases.repository)
        cy.get('#input-test-case-import-repository-branch')
          .type('{selectAll}{del}')
          .type(const_data.import.test_cases.branch)
          .should('have.value', const_data.import.test_cases.branch)
        cy.get('#btn-test-case-import-scan-remote-repository-submit').click()

        // Need time to clone the repo and generate the json
        cy.wait(120000)

        // Refresh User files list
        cy.get('#btn-test-case-import-select-from-user-files').click()
        cy.wait(const_data.fast_wait)
        cy.get('#btn-test-case-import-refresh-user-files').click()
        cy.wait(const_data.long_wait)

        // Import from json - select first option that ends with .json
        cy.get('#select-test-case-import-from-user-files').find('option').should('have.length.greaterThan', 0)
        cy.get('#select-test-case-import-from-user-files')
          .find('option')
          .filter((index, option) => option.value.endsWith('.json'))
          .first()
          .then((firstJsonOption) => {
            cy.get('#select-test-case-import-from-user-files').select(firstJsonOption.val())
          })

        cy.get('#btn-test-case-import-select-from-user-files-submit').click()
        cy.wait(const_data.mid_wait)

        // Check that the test has been loaded
        let row = cy
          .get('#table-test-cases-import')
          .find('tbody')
          .find('tr')
          .find('td')
          .contains(const_data.import.test_cases.test_case.name)
        row.parent('tr').find('td').eq(0).find('input').check().should('be.checked')

        // Submit the import
        cy.get('#btn-test-case-import-submit').click()

        // Move to the Existing Test Cases tab
        cy.get('#pf-tab-2-tab-btn-test-case-existing').click()

        cy.get('#input-search-test-cases-existing')
          .type('{selectAll}{del}')
          .type(const_data.import.test_cases.test_case.title)
          .type('{enter}')

        cy.get('#list-existing-test-cases').find('li').should('have.length.greaterThan', 0)
      })
  })
})
