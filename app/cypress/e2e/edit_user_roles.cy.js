/// <reference types="cypress" />

import '../support/e2e.ts'
import const_data from '../fixtures/consts.json'
import user_data from '../fixtures/users.json'

describe('Edit user role', () => {
  it('Edit user ROLE', () => {
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

    // Check USER role
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
      .contains('span', 'Set as USER')
      .click()

    cy.get('#table-user-management')
      .find('tr') // find all rows
      .contains('td[data-label="username"]', user_data.user1.username)
      .parents('tr') // go up to the row
      .find('td[data-label="role"]')
      .should('have.text', 'USER')

    cy.get('#table-user-management')
      .find('tr') // find all rows
      .contains('td[data-label="username"]', user_data.user2.username)
      .parents('tr') // go up to the row
      .find('td[data-label="role"]')
      .should('have.text', 'GUEST')

    cy.get('#table-user-management')
      .find('tr') // find all rows
      .contains('td[data-label="username"]', user_data.user3.username)
      .parents('tr') // go up to the row
      .find('td[data-label="role"]')
      .should('have.text', 'GUEST')

    // Check ADMIN role
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
      .contains('span', 'Set as ADMIN')
      .click()

    cy.get('#table-user-management')
      .find('tr') // find all rows
      .contains('td[data-label="username"]', user_data.user1.username)
      .parents('tr') // go up to the row
      .find('td[data-label="role"]')
      .should('have.text', 'ADMIN')

    cy.get('#table-user-management')
      .find('tr') // find all rows
      .contains('td[data-label="username"]', user_data.user2.username)
      .parents('tr') // go up to the row
      .find('td[data-label="role"]')
      .should('have.text', 'GUEST')

    cy.get('#table-user-management')
      .find('tr') // find all rows
      .contains('td[data-label="username"]', user_data.user3.username)
      .parents('tr') // go up to the row
      .find('td[data-label="role"]')
      .should('have.text', 'GUEST')

    // Check GUEST role
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
      .contains('span', 'Set as GUEST')
      .click()

    cy.get('#table-user-management')
      .find('tr') // find all rows
      .contains('td[data-label="username"]', user_data.user1.username)
      .parents('tr') // go up to the row
      .find('td[data-label="role"]')
      .should('have.text', 'GUEST')

    cy.get('#table-user-management')
      .find('tr') // find all rows
      .contains('td[data-label="username"]', user_data.user2.username)
      .parents('tr') // go up to the row
      .find('td[data-label="role"]')
      .should('have.text', 'GUEST')

    cy.get('#table-user-management')
      .find('tr') // find all rows
      .contains('td[data-label="username"]', user_data.user3.username)
      .parents('tr') // go up to the row
      .find('td[data-label="role"]')
      .should('have.text', 'GUEST')
  })
})
