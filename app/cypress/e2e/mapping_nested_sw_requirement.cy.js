/// <reference types="cypress" />

import '../support/e2e.ts'
import api_data from '../fixtures/api.json'
import const_data from '../fixtures/consts.json'
import sr_data from '../fixtures/sw_requirement.json'
import tc_data from '../fixtures/test_case.json'
import ts_data from '../fixtures/test_specification.json'

// Create uniq work items
for (let i = 0; i < Object.keys(api_data).length; i++) {
  let current_key = Object.keys(api_data)[i]
  console.log(current_key)
  api_data[current_key].api = api_data[current_key].api + ' ' + Date.now().toString()
}

for (let i = 0; i < Object.keys(sr_data).length; i++) {
  let current_key = Object.keys(sr_data)[i]
  sr_data[current_key].title = sr_data[current_key].title + ' ' + Date.now().toString()
}

for (let i = 0; i < Object.keys(ts_data).length; i++) {
  let current_key = Object.keys(ts_data)[i]
  ts_data[current_key].title = ts_data[current_key].title + ' ' + Date.now().toString()
}

for (let i = 0; i < Object.keys(tc_data).length; i++) {
  let current_key = Object.keys(tc_data)[i]
  tc_data[current_key].title = tc_data[current_key].title + ' ' + Date.now().toString()
}

describe('Nested Software Requirement Mapping', () => {
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
    cy.get('#input-api-list-search').type('{selectAll}{del}' + api_data.first.api + '{enter}')
    cy.wait(2000)
    cy.get(const_data.api.table_listing_id).find('tbody').find('tr').find('td').contains(api_data.first.api)
  })

  it('Matching Nested Sw Requirements', () => {
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

        cy.assign_work_item(-1, 0, '', 'sw-requirement', sr_data.first)
        cy.edit_work_item(0, 'sw-requirement', sr_data.first_mod)

        cy.assign_work_item(0, 1, 'sw-requirement', 'sw-requirement', sr_data.second)
        cy.edit_work_item(1, 'sw-requirement', sr_data.second_mod)

        cy.assign_work_item(1, 2, 'sw-requirement', 'sw-requirement', sr_data.third)
        cy.edit_work_item(2, 'sw-requirement', sr_data.third_mod)

        cy.assign_work_item(2, 3, 'sw-requirement', 'test-specification', ts_data.first)
        cy.edit_work_item(3, 'test-specification', ts_data.first_mod)

        cy.assign_work_item(3, 4, 'test-specification', 'test-case', tc_data.first)
        cy.edit_work_item(4, 'test-case', tc_data.first_mod)

        cy.assign_work_item(2, 5, 'sw-requirement', 'test-case', tc_data.second)
        cy.edit_work_item(5, 'test-case', tc_data.second_mod)

        cy.assign_work_item(1, 6, 'sw-requirement', 'test-specification', ts_data.second)
        cy.edit_work_item(6, 'test-specification', ts_data.second_mod)

        cy.assign_work_item(6, 7, 'test-specification', 'test-case', tc_data.third)
        cy.edit_work_item(7, 'test-case', tc_data.third_mod)

        cy.assign_work_item(1, 8, 'sw-requirement', 'test-case', tc_data.fourth)
        cy.edit_work_item(8, 'test-case', tc_data.fourth_mod)

        cy.assign_work_item(0, 9, 'sw-requirement', 'test-specification', ts_data.third)
        cy.edit_work_item(9, 'test-specification', ts_data.third_mod)

        cy.assign_work_item(9, 10, 'test-specification', 'test-case', tc_data.fifth)
        cy.edit_work_item(10, 'test-case', tc_data.fifth_mod)

        cy.assign_work_item(0, 11, 'sw-requirement', 'test-case', tc_data.sixth)
        cy.edit_work_item(11, 'test-case', tc_data.sixth_mod)

        cy.delete_work_item(11, 'test-case')
        cy.delete_work_item(10, 'test-case')
        cy.delete_work_item(9, 'test-specification')
        cy.delete_work_item(8, 'test-case')
        cy.delete_work_item(7, 'test-case')
        cy.delete_work_item(6, 'test-specification')
        cy.delete_work_item(5, 'test-case')
        cy.delete_work_item(4, 'test-case')
        cy.delete_work_item(3, 'test-specification')
        cy.delete_work_item(2, 'sw-requirement')
        cy.delete_work_item(1, 'sw-requirement')
        cy.delete_work_item(0, 'sw-requirement')
      })
  })

  it('Matching Existing Nested Sw Requirements', () => {
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

        cy.assign_work_item(-1, 0, '', 'sw-requirement', sr_data.first)
        cy.edit_work_item(0, 'sw-requirement', sr_data.first_mod)

        cy.assign_existing_work_item(0, 1, 'sw-requirement', 'sw-requirement', 2)
        cy.edit_work_item(1, 'sw-requirement', sr_data.second)

        cy.assign_existing_work_item(1, 2, 'sw-requirement', 'sw-requirement', 3)
        cy.edit_work_item(2, 'sw-requirement', sr_data.third)

        cy.assign_existing_work_item(2, 3, 'sw-requirement', 'test-specification', 1)
        cy.edit_work_item(3, 'test-specification', ts_data.first)

        cy.assign_existing_work_item(3, 4, 'test-specification', 'test-case', 1)
        cy.edit_work_item(4, 'test-case', tc_data.first)

        cy.assign_existing_work_item(2, 5, 'sw-requirement', 'test-case', 2)
        cy.edit_work_item(5, 'test-case', tc_data.second)

        cy.assign_existing_work_item(1, 6, 'sw-requirement', 'test-specification', 2)
        cy.edit_work_item(6, 'test-specification', ts_data.second)

        cy.assign_existing_work_item(6, 7, 'test-specification', 'test-case', 3)
        cy.edit_work_item(7, 'test-case', tc_data.third)

        cy.assign_existing_work_item(1, 8, 'sw-requirement', 'test-case', 4)
        cy.edit_work_item(8, 'test-case', tc_data.fourth)

        cy.assign_existing_work_item(0, 9, 'sw-requirement', 'test-specification', 3)
        cy.edit_work_item(9, 'test-specification', ts_data.third)

        cy.assign_existing_work_item(9, 10, 'test-specification', 'test-case', 5)
        cy.edit_work_item(10, 'test-case', tc_data.fifth)

        cy.assign_existing_work_item(0, 11, 'sw-requirement', 'test-case', 6)
        cy.edit_work_item(11, 'test-case', tc_data.sixth)
      })
  })
})
