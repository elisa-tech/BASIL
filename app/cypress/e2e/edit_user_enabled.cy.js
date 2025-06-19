/// <reference types="cypress" />

import '../support/e2e.ts'
import const_data from '../fixtures/consts.json'
import user_data from '../fixtures/users.json'

describe('Edit user enabled', () => {
  it('Edit user Enabled', () => {
    // Reset testing database
    cy.clear_db()

    for (const user_key in user_data) {
      const user = user_data[user_key]

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
    }

    cy.login_admin()

    cy.get('#nav-item-user-management').click()
    cy.wait(const_data.mid_wait)

    // Check USER Disable
    cy.get('#table-user-management')
      .find('tr') // find all rows
      .contains('td[data-label="username"]', user_data.user1.username)
      .parents('tr') // go up to the row
      .within(() => {
        // now scoped to the correct row
        cy.get('td[data-label="actions"] button').click() // click the button in the last column
      })

    cy.get('#table-user-management')
      .find('tr') // find all rows
      .find('td[data-label="actions"]')
      .find('button')
      .contains('span', 'Disable')
      .click()

    cy.get('#table-user-management')
      .find('tr') // find all rows
      .contains('td[data-label="username"]', user_data.user1.username)
      .parents('tr') // go up to the row
      .find('td[data-label="enabled"]')
      .find('input[type="checkbox"]')
      .should('not.be.checked')

    cy.get('#table-user-management')
      .find('tr') // find all rows
      .contains('td[data-label="username"]', user_data.user2.username)
      .parents('tr') // go up to the row
      .find('td[data-label="enabled"]')
      .find('input[type="checkbox"]')
      .should('be.checked')

    cy.get('#table-user-management')
      .find('tr') // find all rows
      .contains('td[data-label="username"]', user_data.user3.username)
      .parents('tr') // go up to the row
      .find('td[data-label="enabled"]')
      .find('input[type="checkbox"]')
      .should('be.checked')

    // Check user cannot login
    cy.logout()
    cy.visit(const_data.app_base_url + '/login')
    cy.wait(const_data.long_wait)
    cy.url().should('eq', const_data.app_base_url + '/login')

    cy.get(const_data.login.input_username).type(user_data.user1.email).should('have.value', user_data.user1.email)
    cy.get(const_data.login.input_password).type(user_data.user1.password).should('have.value', user_data.user1.password).type('{enter}')
    cy.wait(const_data.long_wait)
    cy.url().should('eq', const_data.app_base_url + '/login')

    // Check USER enabled
    cy.login_admin()

    cy.get('#nav-item-user-management').click()
    cy.wait(const_data.mid_wait)

    cy.get('#table-user-management')
      .find('tr') // find all rows
      .contains('td[data-label="username"]', user_data.user1.username)
      .parents('tr') // go up to the row
      .within(() => {
        // now scoped to the correct row
        cy.get('td[data-label="actions"] button').click() // click the button in the last column
      })

    cy.get('#table-user-management')
      .find('tr') // find all rows
      .find('td[data-label="actions"]')
      .find('button')
      .contains('span', 'Enable')
      .click()

    cy.get('#table-user-management')
      .find('tr') // find all rows
      .contains('td[data-label="username"]', user_data.user1.username)
      .parents('tr') // go up to the row
      .find('td[data-label="enabled"]')
      .find('input[type="checkbox"]')
      .should('be.checked')

    cy.get('#table-user-management')
      .find('tr') // find all rows
      .contains('td[data-label="username"]', user_data.user2.username)
      .parents('tr') // go up to the row
      .find('td[data-label="enabled"]')
      .find('input[type="checkbox"]')
      .should('be.checked')

    cy.get('#table-user-management')
      .find('tr') // find all rows
      .contains('td[data-label="username"]', user_data.user3.username)
      .parents('tr') // go up to the row
      .find('td[data-label="enabled"]')
      .find('input[type="checkbox"]')
      .should('be.checked')
  })
})
