/// <reference types="cypress" />

import '../support/e2e.js'
import const_data from '../fixtures/consts.json'

// 1x1 transparent PNG
const PNG_BASE64 = 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=='

const openAvatarTab = () => {
  cy.get('#header-user-avatar').click({ force: true })
  cy.wait(const_data.fast_wait)
  cy.contains('button', 'Profile').click({ force: true })
  cy.wait(const_data.fast_wait)
  cy.get('[id*="tab-user-edit-avatar"]').click({ force: true })
  cy.wait(const_data.fast_wait)
}

const saveAvatar = () => {
  cy.get('#btn-user-avatar-save').click({ force: true })
  cy.wait(const_data.mid_wait)
  cy.contains('Avatar updated').should('exist')
}

const closeProfile = () => {
  cy.get('button[aria-label="Close"]').click({ force: true })
  cy.wait(const_data.fast_wait)
}

describe('User Avatar', { testIsolation: false }, () => {
  before(() => {
    cy.login_admin()
  })

  it('Choose a builtin avatar', () => {
    openAvatarTab()
    cy.get('#btn-user-avatar-green').click({ force: true })
    cy.get('#btn-user-avatar-green').should('have.attr', 'aria-pressed', 'true')
    saveAvatar()
    cy.get('#user-avatar-preview')
      .invoke('attr', 'src')
      .then((src) => {
        closeProfile()
        cy.get('#header-user-avatar').should('have.attr', 'src', src)
      })
  })

  it('Keep the avatar after a page reload', () => {
    cy.reload()
    cy.wait(const_data.mid_wait)
    openAvatarTab()
    cy.get('#btn-user-avatar-green').should('have.attr', 'aria-pressed', 'true')
    closeProfile()
  })

  it('Upload an avatar', () => {
    openAvatarTab()
    cy.get('#tabUserEditAvatar .pf-v5-c-file-upload input[type="file"]').selectFile(
      {
        contents: Cypress.Buffer.from(PNG_BASE64, 'base64'),
        fileName: 'avatar.png',
        mimeType: 'image/png'
      },
      { force: true }
    )
    cy.wait(const_data.fast_wait)
    cy.get('#user-avatar-preview')
      .should('have.attr', 'src')
      .and('match', /^data:image\/png;base64,/)
    saveAvatar()
    closeProfile()
    cy.get('#header-user-avatar')
      .should('have.attr', 'src')
      .and('match', /^data:image\/png;base64,/)
  })

  it('Reject an unsupported file', () => {
    openAvatarTab()
    cy.get('#tabUserEditAvatar .pf-v5-c-file-upload input[type="file"]').selectFile(
      {
        contents: Cypress.Buffer.from('not an image'),
        fileName: 'avatar.txt',
        mimeType: 'text/plain'
      },
      { force: true }
    )
    cy.wait(const_data.fast_wait)
    cy.get('#user-avatar-upload-helper').should('contain.text', 'Supported formats are PNG, JPEG, GIF and WebP')
    closeProfile()
  })

  it('Reset to the default avatar', () => {
    openAvatarTab()
    cy.get('#btn-user-avatar-default').click({ force: true })
    saveAvatar()
    cy.get('#btn-user-avatar-default').should('have.attr', 'aria-pressed', 'true')
    closeProfile()
  })
})
