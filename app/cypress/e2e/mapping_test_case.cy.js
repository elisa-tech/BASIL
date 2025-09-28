/// <reference types="cypress" />

import '../support/e2e.js'
import api_data_fixture from '../fixtures/api.json'
import const_data from '../fixtures/consts.json'
import tc_data_fixture from '../fixtures/test_case.json'
import { createUniqWorkItems } from '../support/utils.js'

// Create uniq work items
// Appending to each dictionary of the fixture data a date string to a target field
let api_data = createUniqWorkItems(api_data_fixture, ['api'])
let tc_data = createUniqWorkItems(tc_data_fixture, ['title'])

describe('Test Case Mapping', () => {
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

  it('Unmatching Test Case', () => {
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
        cy.get(const_data.mapping.select_view_id).select('test-cases', {
          force: true
        })
        cy.wait(const_data.long_wait)
        cy.get(const_data.mapping.table_unmatching_id).find('tbody').find('tr').should('have.length', 0)
        cy.get('#btn-mapping-new-test-case').click()
        cy.fill_form('test-case', 'add', tc_data.first, true, true)
        cy.get('#pf-tab-1-tab-btn-test-case-mapping-section').click()
        cy.get('#btn-section-set-unmatching').click()
        cy.get('#pf-tab-0-tab-btn-test-case-data').click()
        cy.get('#btn-mapping-test-case-submit').click()
        cy.wait(const_data.mid_wait)
        cy.get(const_data.mapping.table_unmatching_id).find('tbody').find('tr').should('have.length', 1)
        //Edit
        cy.get(const_data.mapping.table_unmatching_id).find('tbody').find('tr').eq(0).find('td').eq(1).find('button').click()
        cy.get('[id*=btn-menu-unmapped-edit-]').eq(0).click()
        cy.fill_form('test-case', 'edit', tc_data.first_mod, true, true)
        cy.get('#btn-mapping-test-case-submit').click()
        cy.get(const_data.mapping.table_unmatching_id).find('tbody').find('tr').should('have.length', 1)
        //Delete
        cy.get(const_data.mapping.table_unmatching_id).find('tbody').find('tr').eq(0).find('td').eq(1).find('button').click()
        cy.get('[id*=btn-menu-unmapped-delete-]').eq(0).click()
        cy.get('#btn-mapping-delete-confirm').click()
        cy.get(const_data.mapping.table_unmatching_id).find('tbody').find('tr').should('have.length', 0)
      })
  })

  it('Matching New Test Case', () => {
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
        cy.get(const_data.mapping.select_view_id).select('test-cases', {
          force: true
        })
        cy.wait(const_data.long_wait)
        cy.assign_work_item(-1, 0, '', 'test-case', tc_data.first)
        cy.edit_work_item(0, 'test-case', tc_data.first_mod)
        cy.delete_work_item(0, 'test-case')
      })
  })

  it('Existing Test Case', () => {
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
        cy.get(const_data.mapping.select_view_id).select('test-cases', {
          force: true
        })
        cy.wait(const_data.long_wait)
        //Add Existing Test Case
        cy.assign_existing_work_item(-1, 0, '', 'test-case', 1)
        cy.edit_work_item(0, 'test-case', tc_data.first)
        cy.delete_work_item(0, 'test-case')
      })
  })
})
