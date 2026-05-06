/// <reference types="cypress" />

import '../support/e2e.js'
import const_data from '../fixtures/consts.json'

const UNIQUE = Date.now().toString()

describe('User Files - Nested Folder Support', { testIsolation: false }, () => {
  before(() => {
    cy.login_admin()
  })

  it('Navigate to User Files page', () => {
    cy.get('#nav-item-user-files').click()
    cy.wait(const_data.long_wait)
    cy.url().should('include', '/user-files')
    cy.get('#table-user-files').should('exist')
  })

  it('Create a folder', () => {
    cy.get('#btn-create-user-folder').click()
    cy.wait(const_data.fast_wait)
    cy.get('#input-create-folder-name').type('test_folder_' + UNIQUE)
    cy.get('#btn-user-file-modal-confirm').click()
    cy.wait(const_data.long_wait)
    cy.get('#table-user-files')
      .find('tbody')
      .contains('test_folder_' + UNIQUE)
      .should('exist')
  })

  it('Navigate into folder via click', () => {
    cy.get('#table-user-files')
      .find('tbody')
      .contains('test_folder_' + UNIQUE)
      .click({ force: true })
    cy.wait(const_data.mid_wait)
    cy.get('#breadcrumb-0').should('contain.text', 'test_folder_' + UNIQUE)
    cy.get('#table-user-files').find('tbody').should('contain.text', 'empty')
  })

  it('Upload file inside nested folder', () => {
    cy.get('#btn-add-user-file').click()
    cy.wait(const_data.fast_wait)
    cy.get('.pf-v5-c-file-upload input[type="file"]').selectFile(
      {
        contents: Cypress.Buffer.from('key: value'),
        fileName: 'nested_file_' + UNIQUE + '.yaml',
        mimeType: 'text/yaml'
      },
      { force: true }
    )
    cy.wait(const_data.mid_wait)
    cy.get('#btn-user-file-modal-confirm').click()
    cy.wait(const_data.long_wait)
    cy.get('#table-user-files')
      .find('tbody')
      .contains('nested_file_' + UNIQUE + '.yaml')
      .should('exist')
  })

  it('Navigate back to root via breadcrumb', () => {
    cy.get('#breadcrumb-root').click({ force: true })
    cy.wait(const_data.mid_wait)
    cy.get('#table-user-files')
      .find('tbody')
      .contains('test_folder_' + UNIQUE)
      .should('exist')
  })

  it('Create a subfolder for move test', () => {
    cy.get('#btn-create-user-folder').click()
    cy.wait(const_data.fast_wait)
    cy.get('#input-create-folder-name').type('move_dest_' + UNIQUE)
    cy.get('#btn-user-file-modal-confirm').click()
    cy.wait(const_data.long_wait)
    cy.get('#table-user-files')
      .find('tbody')
      .contains('move_dest_' + UNIQUE)
      .should('exist')
  })

  it('Upload a file at root for move test', () => {
    cy.get('#btn-add-user-file').click()
    cy.wait(const_data.fast_wait)
    cy.get('.pf-v5-c-file-upload input[type="file"]').selectFile(
      {
        contents: Cypress.Buffer.from('to be moved'),
        fileName: 'movable_' + UNIQUE + '.txt',
        mimeType: 'text/plain'
      },
      { force: true }
    )
    cy.wait(const_data.mid_wait)
    cy.get('#btn-user-file-modal-confirm').click()
    cy.wait(const_data.long_wait)
    cy.get('#table-user-files')
      .find('tbody')
      .contains('movable_' + UNIQUE + '.txt')
      .should('exist')
  })

  it('Move file into folder', () => {
    cy.get('#table-user-files')
      .find('tbody')
      .contains('movable_' + UNIQUE + '.txt')
      .parents('tr')
      .find('button[aria-label="kebab dropdown toggle"]')
      .click()
    cy.wait(const_data.fast_wait)
    cy.get('[id^="btn-menu-user-file-move-"]').click()
    cy.wait(const_data.fast_wait)
    cy.get('#input-move-destination').type('move_dest_' + UNIQUE)
    cy.get('#btn-user-file-modal-confirm').click()
    cy.wait(const_data.long_wait)
    cy.get('#table-user-files')
      .find('tbody')
      .contains('movable_' + UNIQUE + '.txt')
      .should('not.exist')

    cy.get('#table-user-files')
      .find('tbody')
      .contains('move_dest_' + UNIQUE)
      .click({ force: true })
    cy.wait(const_data.mid_wait)
    cy.get('#table-user-files')
      .find('tbody')
      .contains('movable_' + UNIQUE + '.txt')
      .should('exist')
    cy.get('#breadcrumb-root').click({ force: true })
    cy.wait(const_data.mid_wait)
  })

  it('Rename a folder', () => {
    cy.get('#table-user-files')
      .find('tbody')
      .contains('move_dest_' + UNIQUE)
      .parents('tr')
      .find('button[aria-label="kebab dropdown toggle"]')
      .click()
    cy.wait(const_data.fast_wait)
    cy.get('[id^="btn-menu-user-file-rename-"]').click()
    cy.wait(const_data.fast_wait)
    cy.get('#input-rename-name')
      .clear()
      .type('renamed_' + UNIQUE)
    cy.get('#btn-user-file-modal-confirm').click()
    cy.wait(const_data.long_wait)
    cy.get('#table-user-files')
      .find('tbody')
      .contains('renamed_' + UNIQUE)
      .should('exist')
    cy.get('#table-user-files')
      .find('tbody')
      .contains('move_dest_' + UNIQUE)
      .should('not.exist')
  })

  it('Delete a folder', () => {
    cy.get('#table-user-files')
      .find('tbody')
      .contains('renamed_' + UNIQUE)
      .parents('tr')
      .find('button[aria-label="kebab dropdown toggle"]')
      .click()
    cy.wait(const_data.fast_wait)
    cy.get('[id^="btn-menu-user-file-delete-"]').click()
    cy.wait(const_data.fast_wait)
    cy.get('#btn-user-file-modal-confirm').click()
    cy.wait(const_data.long_wait)
    cy.get('#table-user-files')
      .find('tbody')
      .contains('renamed_' + UNIQUE)
      .should('not.exist')
  })

  it('Delete test folder', () => {
    cy.get('#table-user-files')
      .find('tbody')
      .contains('test_folder_' + UNIQUE)
      .parents('tr')
      .find('button[aria-label="kebab dropdown toggle"]')
      .click()
    cy.wait(const_data.fast_wait)
    cy.get('[id^="btn-menu-user-file-delete-"]').click()
    cy.wait(const_data.fast_wait)
    cy.get('#btn-user-file-modal-confirm').click()
    cy.wait(const_data.long_wait)
    cy.get('#table-user-files')
      .find('tbody')
      .contains('test_folder_' + UNIQUE)
      .should('not.exist')
  })
})
