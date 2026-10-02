/// <reference types="cypress" />

import '../support/e2e.js'
import const_data from '../fixtures/consts.json'
import user_data from '../fixtures/users.json'

describe('Edit user username', () => {
  const user = user_data.user1

  const registerAndLogin = () => {
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

    cy.get(const_data.login.input_username).type(user.username).should('have.value', user.username)
    cy.get(const_data.login.input_password)
      .type(user.password)
      .should('have.value', user.password)
      .type('{enter}')
    cy.wait(const_data.long_wait)
    cy.url().should('eq', const_data.app_base_url + '/')
    cy.get('header .pf-v5-c-toolbar__item .pf-v5-c-menu-toggle__text').should('contain.text', user.username)
  }

  const openProfile = () => {
    cy.get('header').find('div.pf-v5-c-masthead__content').find('button.pf-v5-c-menu-toggle').click()
    cy.get('div.pf-v5-c-menu__content').contains('button', 'Profile').click()
    cy.get('[aria-label="user profile modal"]').should('be.visible')
  }

  it('Rejects a username already used by admin', () => {
    registerAndLogin()

    cy.intercept('PUT', '**/user').as('updateUser')

    openProfile()
    cy.get('#input-user-profile-username').clear().type(const_data.users.admin.username).should('have.value', const_data.users.admin.username)
    cy.get('#btn-user-profile-save').click()

    cy.wait('@updateUser').its('response.statusCode').should('eq', 400)
    cy.get('[aria-label="user profile modal"]').should('contain.text', 'Username already in use.')
    cy.get('header .pf-v5-c-toolbar__item .pf-v5-c-menu-toggle__text').should('contain.text', user.username)

    cy.get('#input-user-profile-username').clear().type('user@name').should('have.value', 'user@name')
    cy.get('[aria-label="user profile modal"]').should('contain.text', 'The @ character is not permitted in the username.')
    cy.get('#btn-user-profile-save').click()
    cy.get('@updateUser.all').should('have.length', 1)
    cy.get('header .pf-v5-c-toolbar__item .pf-v5-c-menu-toggle__text').should('contain.text', user.username)
  })

  it('Reloads and shows the new username in the header', () => {
    const newUsername = 'user1renamed'
    registerAndLogin()

    cy.intercept('PUT', '**/user').as('updateUser')
    openProfile()
    cy.get('#input-user-profile-username').clear().type(newUsername).should('have.value', newUsername)
    cy.get('#btn-user-profile-save').click()

    cy.wait('@updateUser').its('response.statusCode').should('eq', 200)
    cy.wait(const_data.long_wait)
    cy.get('header .pf-v5-c-toolbar__item .pf-v5-c-menu-toggle__text').should('contain.text', newUsername)
  })
})
