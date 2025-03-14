/// <reference types="cypress" />
import api_data from '../fixtures/api.json'
import const_data from '../fixtures/consts.json'

const first_api_mod_new_version = '1.0.2rev1'

for (let i = 0; i < Object.keys(api_data).length; i++) {
  let current_key = Object.keys(api_data)[i]
  console.log(current_key)
  api_data[current_key].api = api_data[current_key].api + ' ' + Date.now().toString()
}

describe('SW Components Dashboard testing', () => {
  beforeEach(() => {
    cy.login_admin()
  })

  it('Add SW Component', () => {
    //Add SW Component
    cy.get('#btn-add-sw-component').click()
    cy.fill_form_api('0', 'add', api_data.first, true, false)
    cy.get('#btn-modal-api-confirm').click()
    cy.wait(const_data.long_wait)
    cy.filter_api_from_dashboard(api_data.first)
  })

  it('Edit SW Component', () => {
    let id

    cy.filter_api_from_dashboard(api_data.first)

    cy.get(const_data.api.table_listing_id)
      .find('tbody')
      .find('tr')
      .eq(0)
      .find('td')
      .eq(1)
      .invoke('text')
      .then((elem) => {
        id = elem
        cy.get('#td-expand-' + id)
          .find('button')
          .click({ force: true })

        //Fill form with modified data
        cy.fill_form_api(id, 'edit', api_data.first_mod, true, true)
        cy.get('#btn-api-form-reset').click()
        //Check that reset button works
        cy.fill_form_api(id, 'edit', api_data.first, false, false)
        //Fill form with modified data
        cy.fill_form_api(id, 'edit', api_data.first_mod, true, true)
        cy.get('#btn-api-form-submit').click()
      })

    cy.wait(const_data.long_wait)

    // Select the modified api from the list
    cy.filter_api_from_dashboard(api_data.first_mod)
  })

  it('Create a new version of an existing Sw Component', () => {
    let id

    // Select the modified api from the list
    cy.filter_api_from_dashboard(api_data.first_mod)

    cy.get(const_data.api.table_listing_id).find('tbody').find('tr').eq(0).find('td').last().find('button').click({ force: true })
    cy.wait(const_data.long_wait)
    cy.get(const_data.api.table_listing_id)
      .find('tbody')
      .find('tr')
      .eq(0)
      .find('td')
      .eq(1)
      .invoke('text')
      .then((elem) => {
        id = elem
        cy.get('#btn-menu-api-new-version-' + id).click({ force: true })
        //Fill new version
        cy.get('#input-api-fork-library-version-' + id)
          .type(first_api_mod_new_version)
          .should('have.value', first_api_mod_new_version)
      })
    cy.get('#btn-modal-api-confirm').click()
  })

  it('Search field should filter the SW Components', () => {
    // All api - empty search string
    cy.get('#input-api-list-search').type('{selectAll}{del}{enter}')
    cy.wait(const_data.long_wait)
    cy.get(const_data.api.table_listing_id).find('tbody').find('tr').should('have.length.greaterThan', 1)

    // Single match
    cy.filter_api_from_dashboard(api_data.first_mod)

    // No match
    cy.get('#input-api-list-search').type('{selectAll}{del}<NO MATCH STRING>{enter}')
    cy.wait(const_data.long_wait)
    cy.get(const_data.api.table_listing_id).find('tbody').should('not.exist')
  })

  it('Delete SW Component', () => {
    let id
    // There should be 2 apis, related to 2 different versions

    // Select the apis from the list
    cy.filter_api_from_dashboard(api_data.first_mod)

    for (let i = 0; i < 2; i++) {
      // Two apis, for two versions
      // Kebab Menu Click
      cy.get(const_data.api.table_listing_id).find('tbody').find('tr').eq(0).find('td').last().find('button').click({ force: true })

      cy.wait(const_data.long_wait)

      cy.get(const_data.api.table_listing_id)
        .find('tbody')
        .find('tr')
        .eq(0)
        .find('td')
        .eq(1)
        .invoke('text')
        .then((elem) => {
          id = elem
          cy.get('#btn-menu-api-delete-' + id).click({ force: true })
          cy.get('#btn-api-delete-confirm').click({ force: true })
        })

      //We delete the first api in the list so we should filter to the one we want to delete
      //Type the api name again
      cy.wait(const_data.long_wait)
      cy.get('#input-api-list-search').type('{selectAll}{del}' + api_data.first_mod.api + '{enter}')
      cy.wait(const_data.long_wait)
    }

    // No matches on modified api name (both version deleted)
    cy.visit(const_data.app_base_url + '?currentLibrary=' + api_data.first_mod.library)
    cy.wait(const_data.long_wait)
    cy.get('#input-api-list-search').type('{selectAll}{del}' + api_data.first_mod.api + '{enter}')
    cy.wait(const_data.long_wait)
    cy.get(const_data.api.table_listing_id).find('tbody').should('not.exist')
  })
})
