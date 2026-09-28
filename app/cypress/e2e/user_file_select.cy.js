/// <reference types="cypress" />

import '../support/e2e.js'
import const_data from '../fixtures/consts.json'

const UNIQUE = Date.now().toString()
const FOLDER = 'picker_' + UNIQUE
const YAML_FILE = 'kernel_requirements_' + UNIQUE + '.yaml'
const TEXT_FILE = 'other_' + UNIQUE + '.txt'
const SUB_FOLDER = 'kernel_folder_' + UNIQUE

// The searchable user file picker, as used for the specification file of a
// software component. The same component serves every form that picks a user
// file.
const PICKER = '[id^="select-api-add-raw-specification-path-"][data-value]'
const LISTBOX = '[id^="select-api-add-raw-specification-path-"][id$="-listbox"]'

describe('User file picker', { testIsolation: false }, () => {
  before(() => {
    cy.login_admin()
  })

  it('Create a folder with two files and a sub folder', () => {
    cy.get('#nav-item-user-files').click()
    cy.wait(const_data.long_wait)
    cy.get('#btn-create-user-folder').click()
    cy.wait(const_data.fast_wait)
    cy.get('#input-create-folder-name').type(FOLDER)
    cy.get('#btn-user-file-modal-confirm').click()
    cy.wait(const_data.long_wait)
    cy.get('#table-user-files').find('tbody').contains(FOLDER).click({ force: true })
    cy.wait(const_data.mid_wait)

    for (const fileName of [YAML_FILE, TEXT_FILE]) {
      cy.get('#btn-add-user-file').click()
      cy.wait(const_data.fast_wait)
      cy.get('#user-file-upload-browse-button').selectFile(
        { contents: Cypress.Buffer.from('x'), fileName: fileName, mimeType: 'text/plain' },
        { action: 'drag-drop' }
      )
      cy.get('.pf-v5-c-file-upload textarea').should('not.have.value', '')
      cy.get('#btn-user-file-modal-confirm').click()
      cy.wait(const_data.long_wait)
    }

    cy.get('#btn-create-user-folder').click()
    cy.wait(const_data.fast_wait)
    cy.get('#input-create-folder-name').type(SUB_FOLDER)
    cy.get('#btn-user-file-modal-confirm').click()
    cy.wait(const_data.long_wait)
    cy.get('#table-user-files').find('tbody').should('contain.text', SUB_FOLDER)
  })

  it('Open the picker of a software component specification', () => {
    cy.get('#nav-item-home').click()
    cy.wait(const_data.long_wait)
    cy.get('#btn-add-sw-component').click()
    cy.wait(const_data.mid_wait)
    cy.contains('button', 'From user files').first().click()
    cy.get(PICKER + ' input').should('be.visible').and('have.attr', 'placeholder', 'Select a file from the list')
    cy.get(PICKER).should('have.attr', 'data-value', '')
  })

  it('Opening it without typing lists the files', () => {
    cy.get(PICKER + ' input').click()
    cy.get(LISTBOX).should('contain.text', FOLDER + '/' + YAML_FILE)
    cy.get(LISTBOX).should('contain.text', FOLDER + '/' + TEXT_FILE)
    cy.get(PICKER + ' input').type('{esc}')
  })

  it('Typing several words in any order narrows the list down', () => {
    cy.get(PICKER + ' input').type('req ' + UNIQUE + ' kernel')
    cy.get(LISTBOX).should('contain.text', FOLDER + '/' + YAML_FILE)
    cy.get(LISTBOX).should('not.contain.text', TEXT_FILE)
  })

  it('Folders found by the search are not offered', () => {
    // "kernel <UNIQUE>" also matches the sub folder, which the backend search
    // returns, but a folder cannot be picked as a file.
    cy.get(PICKER + ' input')
      .clear()
      .type('kernel ' + UNIQUE)
    cy.get(LISTBOX).should('contain.text', YAML_FILE)
    cy.get(LISTBOX).find('li').should('have.length', 1)
    cy.get(LISTBOX).should('not.contain.text', SUB_FOLDER)
  })

  it('The typed words are highlighted', () => {
    cy.get(LISTBOX)
      .find('span')
      .filter((index, element) => element.style.backgroundColor === 'rgb(240, 171, 0)')
      .should('have.length.greaterThan', 0)
  })

  it('Enter picks the only match left', () => {
    cy.get(PICKER + ' input').type('{enter}')
    cy.get(PICKER + ' input').should('have.value', FOLDER + '/' + YAML_FILE)
    cy.get(PICKER)
      .invoke('attr', 'data-value')
      .should('match', new RegExp(YAML_FILE + '$'))
    cy.get(LISTBOX).should('not.exist')
  })

  it('Clear empties the selection', () => {
    cy.get(PICKER).parent().find('button[aria-label="Clear selected file"]').click()
    cy.get(PICKER + ' input').should('have.value', '')
    cy.get(PICKER).should('have.attr', 'data-value', '')
  })

  it('Arrow keys move through the matches', () => {
    cy.get(PICKER + ' input').type(UNIQUE)
    cy.get(LISTBOX).find('li').should('have.length', 2)
    cy.get(LISTBOX)
      .find('li')
      .eq(1)
      .invoke('text')
      .then((secondPath) => {
        cy.get(PICKER + ' input').type('{downarrow}{downarrow}{enter}')
        cy.get(PICKER + ' input').should('have.value', secondPath)
      })
  })

  it('Escape closes the list but not the form around it', () => {
    cy.get(PICKER + ' input').invoke('val').as('selectedPath')
    cy.get(PICKER + ' input').click()
    cy.get(LISTBOX).should('exist')
    cy.get(PICKER + ' input').type('{esc}')
    cy.get(LISTBOX).should('not.exist')
    cy.get('@selectedPath').then((selectedPath) => {
      cy.get(PICKER + ' input').should('be.visible').and('have.value', selectedPath)
    })
  })

  it('Typing something that matches nothing says so', () => {
    cy.get(PICKER + ' input')
      .clear()
      .type('no_match_' + UNIQUE)
    cy.get(LISTBOX).should('contain.text', 'No files match "no_match_' + UNIQUE + '"')
    cy.get(PICKER + ' input').type('{esc}')
  })

  it('While a search is on its way, the list stays and Enter waits for it', () => {
    // Start from no selection, so that picking something shows.
    cy.get(PICKER).parent().find('button[aria-label="Clear selected file"]').click()
    cy.get(PICKER).should('have.attr', 'data-value', '')
    cy.get(PICKER + ' input').type('kernel ' + UNIQUE)
    cy.get(LISTBOX).find('li').should('have.length', 1).and('contain.text', YAML_FILE)

    // Slow the next search down so that its results are still on their way
    // while the checks below run; they only retry for a second, well before
    // the results can arrive.
    cy.intercept({ method: 'GET', url: /\/user\/files\?.*search=/ }, (req) => {
      req.on('response', (res) => {
        res.setDelay(3000)
      })
    }).as('slowSearch')
    cy.get(PICKER + ' input').type(' req')
    // the previous results are still listed rather than emptied
    cy.get(LISTBOX, { timeout: 1000 }).should('contain.text', YAML_FILE).and('not.contain.text', 'Searching')
    // and Enter does not pick from them
    cy.get(PICKER + ' input').type('{enter}')
    cy.get(PICKER, { timeout: 1000 }).should('have.attr', 'data-value', '')

    // Once the results of "kernel <UNIQUE> req" are in, "req" is highlighted
    // too, and Enter picks the match.
    cy.wait('@slowSearch')
    cy.get(LISTBOX)
      .find('span')
      .filter((index, element) => element.style.backgroundColor === 'rgb(240, 171, 0)')
      .should(($highlighted) => {
        expect([...$highlighted].map((element) => element.textContent)).to.include('req')
      })
    cy.get(PICKER + ' input').type('{enter}')
    cy.get(PICKER)
      .invoke('attr', 'data-value')
      .should('match', new RegExp(YAML_FILE + '$'))
  })

  it('Delete the test folder', () => {
    cy.contains('button', 'Cancel').click()
    cy.wait(const_data.fast_wait)
    cy.get('#nav-item-user-files').click()
    cy.wait(const_data.long_wait)
    cy.get('#table-user-files')
      .find('tbody')
      .contains(FOLDER)
      .parents('tr')
      .find('button[aria-label="kebab dropdown toggle"]')
      .click()
    cy.wait(const_data.fast_wait)
    cy.get('[id^="btn-menu-user-file-delete-"]').click()
    cy.wait(const_data.fast_wait)
    cy.get('#btn-user-file-modal-confirm').click()
    cy.wait(const_data.long_wait)
    cy.get('#table-user-files').find('tbody').contains(FOLDER).should('not.exist')
  })
})
