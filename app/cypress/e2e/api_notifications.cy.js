/// <reference types="cypress" />
import api_data_fixture from '../fixtures/api.json'
import const_data from '../fixtures/consts.json'
import { createUniqWorkItems } from '../support/utils.js'

// Create uniq work items
// Appending to each dictionary of the fixture data a date string to a target field
let api_data = createUniqWorkItems(api_data_fixture, ['api'])

describe('Api Notifications', () => {
  const table_id_api = 'table-api-listing'
  const data_label_actions = 'Actions'
  const data_label_name = 'Name'
  const data_label_notifications = 'Notifications'
  const btn_text_enable = 'Enable notifications'
  const btn_text_disable = 'Disable notifications'

  beforeEach(() => {
    cy.login_admin()
  })

  it('Enable/Disable', () => {
    //Add SW Component
    cy.get('#btn-add-sw-component').click()
    cy.fill_form_api('0', 'add', api_data.first, true, false)
    cy.get('#btn-modal-api-confirm').click()

    // Filter api list to have the new added in the current page
    cy.wait(const_data.long_wait)
    cy.filter_api_from_dashboard(api_data.first)

    // Enable
    cy.get('#' + table_id_api)
      .find('tr') // find all rows
      .contains('td[data-label="' + data_label_name + '"]', api_data.first.api)
      .parents('tr') // go up to the row
      .within(() => {
        // now scoped to the correct row
        cy.get('td[data-label="' + data_label_actions + '"] button').click() // click the button in the last column
      })

    cy.get('#' + table_id_api)
      .find('tr') // find all rows
      .find('td[data-label="' + data_label_actions + '"]')
      .find('button')
      .contains('span', btn_text_enable)
      .click()

    // Filter api list to have the new added in the current page
    cy.wait(const_data.long_wait)
    cy.filter_api_from_dashboard(api_data.first)

    cy.get('#' + table_id_api)
      .find('tr') // find all rows
      .find('td[data-label="' + data_label_notifications + '"]')
      .get('[data-icon="notification"]')
      .should('exist')

    // Disable
    cy.get('#' + table_id_api)
      .find('tr') // find all rows
      .contains('td[data-label="' + data_label_name + '"]', api_data.first.api)
      .parents('tr') // go up to the row
      .within(() => {
        // now scoped to the correct row
        cy.get('td[data-label="' + data_label_actions + '"] button').click() // click the button in the last column
      })

    cy.get('#' + table_id_api)
      .find('tr') // find all rows
      .find('td[data-label="' + data_label_actions + '"]')
      .find('button')
      .contains('span', btn_text_disable)
      .click()

    // Filter api list to have the new added in the current page
    cy.wait(const_data.long_wait)
    cy.filter_api_from_dashboard(api_data.first)

    cy.get('#' + table_id_api)
      .find('tr') // find all rows
      .find('td[data-label="' + data_label_notifications + '"]')
      .get('[data-icon="notification"]')
      .should('not.exist')
  })
})
