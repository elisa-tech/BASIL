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

describe('Document Mapping', () => {
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

  it('Unmatching Document', () => {
    // Select the api from the list
    cy.filter_api_from_dashboard(api_data.first)

    cy.get(const_data.api.table_listing_id)
      .find('tbody')
      .find('tr')
      .eq(0)
      .find('td')
      .eq(1)
      .invoke('text')
      .then((api_id) => {
        cy.visit(const_data.app_base_url + '/mapping/' + api_id)
        cy.wait(const_data.long_wait)
        cy.get(const_data.mapping.table_unmatching_id).find('tbody').find('tr').should('have.length', 0)
        cy.get('#btn-mapping-new-document').click({ force: true })
        cy.fill_form('document', 'add', doc_data.first, true, true)
        cy.get('#pf-tab-1-tab-btn-document-mapping-section').click()
        cy.get('#btn-section-set-unmatching').click()
        cy.get('#pf-tab-0-tab-btn-document-data').click()
        cy.get('#btn-mapping-document-submit').click()
        cy.get(const_data.mapping.table_unmatching_id).find('tbody').find('tr').should('have.length', 1)
        //Edit
        cy.get(const_data.mapping.table_unmatching_id).find('tbody').find('tr').eq(0).find('td').eq(1).find('button').click()
        cy.get('[id*=btn-menu-unmapped-edit-]').eq(0).click()
        cy.fill_form('document', 'edit', doc_data.first_mod, true, true)
        cy.get('#btn-mapping-document-submit').click()
        cy.get(const_data.mapping.table_unmatching_id).find('tbody').find('tr').should('have.length', 1)
        //Delete
        cy.get(const_data.mapping.table_unmatching_id).find('tbody').find('tr').eq(0).find('td').eq(1).find('button').click()
        cy.get('[id*=btn-menu-unmapped-delete-]').eq(0).click()
        cy.get('#btn-mapping-delete-confirm').click()
        cy.get(const_data.mapping.table_unmatching_id).find('tbody').find('tr').should('have.length', 0)
      })
  })

  it('Matching New File Document', () => {
    // Select the api from the list
    cy.filter_api_from_dashboard(api_data.first)

    cy.get(const_data.api.table_listing_id)
      .find('tbody')
      .find('tr')
      .eq(0)
      .find('td')
      .eq(1)
      .invoke('text')
      .then((api_id) => {
        cy.visit(const_data.app_base_url + '/mapping/' + api_id)
        cy.wait(const_data.long_wait)
        cy.assign_work_item(-1, 0, '', 'document', doc_data.first)
        cy.edit_work_item(0, 'document', doc_data.first_mod)
        cy.delete_work_item(0, 'document')
      })
  })

  it('Matching New Text Document', () => {
    // Select the api from the list
    cy.filter_api_from_dashboard(api_data.first)

    cy.get(const_data.api.table_listing_id)
      .find('tbody')
      .find('tr')
      .eq(0)
      .find('td')
      .eq(1)
      .invoke('text')
      .then((api_id) => {
        cy.visit(const_data.app_base_url + '/mapping/' + api_id)
        cy.wait(const_data.long_wait)
        cy.assign_work_item(-1, 0, '', 'document', doc_data.second)
        cy.edit_work_item(0, 'document', doc_data.second_mod)
        cy.delete_work_item(0, 'document')
      })
  })

  it('Matching Existing File Document', () => {
    // Select the api from the list
    cy.filter_api_from_dashboard(api_data.first)

    cy.get(const_data.api.table_listing_id)
      .find('tbody')
      .find('tr')
      .eq(0)
      .find('td')
      .eq(1)
      .invoke('text')
      .then((api_id) => {
        cy.visit(const_data.app_base_url + '/mapping/' + api_id)
        cy.wait(const_data.long_wait)
        //Add Existing Test Case
        cy.assign_existing_work_item(-1, 0, '', 'document', 1)
        cy.edit_work_item(0, 'document', doc_data.first)
        cy.delete_work_item(0, 'document')
      })
  })
})
