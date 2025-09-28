/// <reference types="cypress" />

import '../support/e2e.js'
import const_data from '../fixtures/consts.json'
import user_data from '../fixtures/users.json'

describe('Reset user password', () => {
  const user = user_data.user1
  const table_id_user_management = 'table-user-management'
  const div_role_dialog = 'dialog'
  const data_label_username = 'username'
  const data_label_actions = 'actions'
  const btn_text_reset = 'Reset Password'
  const btn_text_confirm = 'Confirm'
  const btn_text_copy = 'Copy to Clipboard'
  const header_text = 'Reset user password'
  const msg_success = 'Changes saved'
  const b_new_password = 'b-new-password'

  it('Reset user password', () => {
    // Reset testing database
    cy.clear_db()

    cy.visit(const_data.app_base_url)
    cy.wait(const_data.long_wait)

    cy.get('#nav-item-signin').click()
    cy.wait(const_data.mid_wait)
    cy.get('#signin-form-email').clear().type(user.email).should('have.value', user.email)
    cy.get('#signin-form-username').clear().type(user.username).should('have.value', user.username)
    cy.get('#signin-form-password').clear().type(user.password).should('have.value', user.password)
    cy.get('#signin-form-password-confirm').clear().type(user.password).should('have.value', user.password)
    cy.get('#form-signin-submit').click()
    cy.wait(const_data.long_wait)
    cy.url().should('eq', const_data.app_base_url + '/login')

    cy.login_admin()

    cy.get('#nav-item-user-management').click()
    cy.wait(const_data.mid_wait)

    // Check USER Disable
    cy.get('#' + table_id_user_management)
      .find('tr') // find all rows
      .contains('td[data-label="' + data_label_username + '"]', user_data.user1.username)
      .parents('tr') // go up to the row
      .within(() => {
        // now scoped to the correct row
        cy.get('td[data-label="' + data_label_actions + '"] button').click() // click the button in the last column
      })

    cy.get('#' + table_id_user_management)
      .find('tr') // find all rows
      .find('td[data-label="' + data_label_actions + '"]')
      .find('button')
      .contains('span', btn_text_reset)
      .click()

    cy.get('div[role="' + div_role_dialog + '"]')
      .find('header h1 span')
      .should('have.text', header_text)

    // Click Reset Password button
    cy.get('div[role="' + div_role_dialog + '"]')
      .find('footer button')
      .contains(btn_text_confirm)
      .click()

    cy.get('div').contains(msg_success).should('exist')

    //Check Copy to clipboard
    // Stub clipboard before the test starts
    cy.window().then((win) => {
      cy.stub(win.navigator.clipboard, 'writeText').as('clipboardWrite')
    })

    // Trigger the copy action (like clicking a "Copy" button)
    cy.get('div[role="' + div_role_dialog + '"]')
      .find('footer button')
      .contains(btn_text_copy)
      .click()

    // Check what was attempted to be copied
    cy.get('#' + b_new_password)
      .invoke('text')
      .then((expectedText) => {
        cy.get('@clipboardWrite').should('have.been.calledWith', expectedText.trim())
      })
  })
})
