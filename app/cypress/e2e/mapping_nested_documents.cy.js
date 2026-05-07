/// <reference types="cypress" />

import '../support/e2e.js'
import api_data_fixture from '../fixtures/api.json'
import const_data from '../fixtures/consts.json'
import doc_data_fixture from '../fixtures/document.json'
import { createUniqWorkItems } from '../support/utils.js'

// Create uniq work items
// Appending to each dictionary of the fixture data a date string to a target field
let api_data = createUniqWorkItems(api_data_fixture, ['api'])
let doc_data = createUniqWorkItems(doc_data_fixture, ['title'])

describe('Nested Document Mapping', () => {
  beforeEach(() => {
    cy.login_admin()
  })

  it('Add SW Component', () => {
    // Add SW Component
    cy.get('#btn-add-sw-component').click()
    cy.fill_form_api('0', 'add', api_data.first, true, false)
    cy.get('#btn-modal-api-confirm').click()
    cy.wait(2000)
    // Check Sw component has been created
    cy.get('#input-api-list-search').type('{selectAll}{del}' + api_data.first.api + '{enter}')
    cy.wait(2000)
    cy.get(const_data.api.table_listing_id).find('tbody').find('tr').find('td').contains(api_data.first.api)
  })

  it('Matching Nested Documents', () => {
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

        // Map a new top-level Document to the API
        cy.assign_work_item(-1, 0, '', 'document', doc_data.first)
        cy.edit_work_item(0, 'document', doc_data.first_mod)

        // Map a nested Document under the first Document
        cy.assign_work_item(0, 1, 'document', 'document', doc_data.second)
        cy.edit_work_item(1, 'document', doc_data.second_mod)

        // Clean up in reverse order
        cy.delete_work_item(1, 'document')
        cy.delete_work_item(0, 'document')
      })
  })
})
