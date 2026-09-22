/// <reference types="cypress" />

import '../support/e2e.js'
import const_data from '../fixtures/consts.json'

const UNIQUE = Date.now().toString()
const downloadedPath = (filename) => `${Cypress.config('downloadsFolder')}/${filename}`

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
    cy.get('.pf-v5-c-file-upload textarea').should('not.have.value', '')
    cy.get('#btn-user-file-modal-confirm').click()
    cy.wait(const_data.long_wait)
    cy.get('#table-user-files')
      .find('tbody')
      .contains('nested_file_' + UNIQUE + '.yaml')
      .should('exist')
  })

  it('Download a nested file from the context menu', () => {
    cy.intercept('GET', '**/user/files/download*').as('downloadUserFile')
    cy.get('#table-user-files')
      .find('tbody')
      .contains('nested_file_' + UNIQUE + '.yaml')
      .parents('tr')
      .find('button[aria-label="kebab dropdown toggle"]')
      .click()
    cy.wait(const_data.fast_wait)
    cy.get('[id^="btn-menu-user-file-download-"]').should('contain.text', 'Download').click()
    cy.wait('@downloadUserFile').its('response.statusCode').should('eq', 200)
    cy.readFile(downloadedPath('nested_file_' + UNIQUE + '.yaml'), { timeout: 15000 }).should(
      'contain',
      'key: value'
    )
  })

  it('Navigate back to root via breadcrumb', () => {
    cy.get('#breadcrumb-root').click({ force: true })
    cy.wait(const_data.mid_wait)
    cy.get('#table-user-files')
      .find('tbody')
      .contains('test_folder_' + UNIQUE)
      .should('exist')
  })

  it('Download a folder as a tarball from the context menu', () => {
    cy.intercept('GET', '**/user/files/download*').as('downloadUserFolder')
    cy.get('#table-user-files')
      .find('tbody')
      .contains('test_folder_' + UNIQUE)
      .parents('tr')
      .find('button[aria-label="kebab dropdown toggle"]')
      .click()
    cy.wait(const_data.fast_wait)
    cy.get('[id^="btn-menu-user-file-download-"]').should('contain.text', 'Download as .tar.gz').click()
    cy.wait('@downloadUserFolder').its('response.statusCode').should('eq', 200)
    cy.readFile(downloadedPath('test_folder_' + UNIQUE + '.tar.gz'), {
      encoding: null,
      timeout: 15000
    }).should((buffer) => {
      expect(buffer.length).to.be.greaterThan(0)
    })
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
    cy.get('.pf-v5-c-file-upload textarea').should('not.have.value', '')
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

  it('Search user files across all folders', () => {
    // nested_file_<UNIQUE>.yaml lives inside test_folder_<UNIQUE> while the
    // browsed folder is Home, so it can only be found by the backend search,
    // not by filtering the current listing.
    cy.get('#input-user-files-search input').type('nested_file_' + UNIQUE, { force: true })
    cy.wait(const_data.long_wait)
    cy.get('#table-user-files-search-results')
      .find('tbody')
      .contains('nested_file_' + UNIQUE + '.yaml')
      .should('exist')
  })

  it('Search results show the full relative path of each entry', () => {
    cy.get('#table-user-files-search-results')
      .find('tbody')
      .should('contain.text', 'test_folder_' + UNIQUE + '/nested_file_' + UNIQUE + '.yaml')
  })

  it('Search matches the folders of a file, not only its name', () => {
    // The query names the folder only; the file inside it has to be returned
    // because the whole relative path is searched.
    cy.get('#input-user-files-search input')
      .clear({ force: true })
      .type('test_folder_' + UNIQUE + '/nested', { force: true })
    cy.wait(const_data.long_wait)
    cy.get('#table-user-files-search-results')
      .find('tbody')
      .contains('nested_file_' + UNIQUE + '.yaml')
      .should('exist')
  })

  it('Search returns folders too', () => {
    cy.get('#input-user-files-search input')
      .clear({ force: true })
      .type('test_folder_' + UNIQUE, { force: true })
    cy.wait(const_data.long_wait)
    // The folder itself is a result, on top of the file it contains.
    cy.get('#table-user-files-search-results')
      .find('tbody tr')
      .contains('td', new RegExp('^test_folder_' + UNIQUE + '$'))
      .should('exist')
  })

  it('Search matches characters that are not adjacent', () => {
    // "tfnf<UNIQUE>" is not a substring of anything: the characters only
    // appear in that order along test_folder_<UNIQUE>/nested_file_<UNIQUE>.
    cy.get('#input-user-files-search input').clear({ force: true }).type('tfnf' + UNIQUE, { force: true })
    cy.wait(const_data.long_wait)
    cy.get('#table-user-files-search-results')
      .find('tbody')
      .contains('nested_file_' + UNIQUE + '.yaml')
      .should('exist')
  })

  it('Search highlights the characters that matched', () => {
    cy.get('#input-user-files-search input')
      .clear({ force: true })
      .type('nested_file_' + UNIQUE, { force: true })
    cy.wait(const_data.long_wait)
    cy.get('#table-user-files-search-results')
      .find('tbody tr')
      .first()
      .find('span')
      .filter((index, element) => element.style.backgroundColor !== '' && element.style.backgroundColor !== 'transparent')
      .should('have.length.greaterThan', 0)
  })

  it('Search is case insensitive', () => {
    cy.get('#input-user-files-search input')
      .clear({ force: true })
      .type('NESTED_FILE_' + UNIQUE, { force: true })
    cy.wait(const_data.long_wait)
    cy.get('#table-user-files-search-results')
      .find('tbody')
      .contains('nested_file_' + UNIQUE + '.yaml')
      .should('exist')
  })

  it('Search without matches', () => {
    cy.get('#input-user-files-search input')
      .clear({ force: true })
      .type('no_match_' + UNIQUE, { force: true })
    cy.wait(const_data.long_wait)
    cy.get('#table-user-files-search-results').find('tbody').should('contain.text', 'Nothing matches')
  })

  it('Open the folder of a search result', () => {
    cy.get('#input-user-files-search input')
      .clear({ force: true })
      .type('nested_file_' + UNIQUE, { force: true })
    cy.wait(const_data.long_wait)
    cy.get('[id^="btn-user-file-search-result-"]').first().click({ force: true })
    cy.wait(const_data.mid_wait)
    cy.get('#breadcrumb-0').should('contain.text', 'test_folder_' + UNIQUE)
    cy.get('#input-user-files-search input').should('have.value', '')
    cy.get('#table-user-files')
      .find('tbody')
      .contains('nested_file_' + UNIQUE + '.yaml')
      .should('exist')
  })

  it('Clear the search to get back to the folder listing', () => {
    cy.get('#breadcrumb-root').click({ force: true })
    cy.wait(const_data.mid_wait)
    cy.get('#input-user-files-search input')
      .clear({ force: true })
      .type('nested_file_' + UNIQUE, { force: true })
    cy.wait(const_data.long_wait)
    cy.get('#table-user-files').should('not.exist')
    cy.get('#input-user-files-search button[aria-label="Reset"]').click({ force: true })
    cy.wait(const_data.mid_wait)
    cy.get('#table-user-files-search-results').should('not.exist')
    cy.get('#table-user-files')
      .find('tbody')
      .contains('test_folder_' + UNIQUE)
      .should('exist')
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
