/// <reference types="cypress" />

import '../support/e2e.js'
import const_data from '../fixtures/consts.json'
import user_data from '../fixtures/users.json'

const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i
const USER1_SIGNATURE = 'user1 SPDX author signature'

const registerUser = (user) => {
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

const loginUser = (user) => {
  cy.visit(const_data.app_base_url + '/login')
  cy.wait(const_data.long_wait)
  cy.url().should('eq', const_data.app_base_url + '/login')
  cy.get(const_data.login.input_username).clear().type(user.email).should('have.value', user.email)
  cy.get(const_data.login.input_password)
    .clear()
    .type(user.password)
    .should('have.value', user.password)
    .type('{enter}')
  cy.wait(const_data.long_wait)
  cy.url().should('eq', const_data.app_base_url + '/')
  cy.get('header .pf-v5-c-toolbar__item .pf-v5-c-menu-toggle__text').should('contain.text', user.username)
}

const openSpdxSignatureTab = () => {
  cy.get('header').find('div.pf-v5-c-masthead__content').find('button.pf-v5-c-menu-toggle').click()
  cy.get('#btn-header-user-profile').click({ force: true })
  cy.get('div[role="dialog"]').should('contain.text', 'User Profile')
  cy.contains('.pf-v5-c-tabs__item', 'SPDX Signature').click()
  cy.get('#input-user-edit-spdx-signature').should('be.visible')
}

const closeUserProfileModal = () => {
  cy.get('div[role="dialog"]').find('button[aria-label="Close"]').click({ force: true })
  cy.get('div[role="dialog"]').should('not.exist')
}

describe('Edit user SPDX signature', () => {
  it('Lets a user change the default signature and rejects duplicates', () => {
    cy.clear_db()

    registerUser(user_data.user1)
    registerUser(user_data.user2)

    loginUser(user_data.user1)
    openSpdxSignatureTab()

    cy.get('#input-user-edit-spdx-signature')
      .invoke('val')
      .should('match', UUID_RE)

    cy.intercept('PUT', '**/user').as('saveSpdxSignature')
    cy.get('#input-user-edit-spdx-signature').clear().type(USER1_SIGNATURE).should('have.value', USER1_SIGNATURE)
    cy.get('#btn-user-edit-spdx-signature-save').click()
    cy.wait('@saveSpdxSignature').its('response.statusCode').should('eq', 200)
    cy.get('div[role="dialog"]').should('contain.text', 'Your SPDX author signature has been saved.')
    cy.window().then((win) => {
      expect(win.localStorage.getItem('uSpdxSignature')).to.eq(USER1_SIGNATURE)
    })

    closeUserProfileModal()

    openSpdxSignatureTab()
    cy.get('#input-user-edit-spdx-signature').should('have.value', USER1_SIGNATURE)
    closeUserProfileModal()

    cy.logout()
    loginUser(user_data.user2)
    openSpdxSignatureTab()

    cy.intercept('PUT', '**/user').as('saveDuplicateSpdxSignature')
    cy.get('#input-user-edit-spdx-signature').clear().type(USER1_SIGNATURE).should('have.value', USER1_SIGNATURE)
    cy.get('#btn-user-edit-spdx-signature-save').click()
    cy.wait('@saveDuplicateSpdxSignature').its('response.statusCode').should('eq', 400)
    cy.get('div[role="dialog"]').should('contain.text', 'already in use')
  })
})
