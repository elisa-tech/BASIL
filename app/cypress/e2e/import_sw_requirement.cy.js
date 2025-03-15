/// <reference types="cypress" />

import '../support/e2e.ts'
import api_data from '../fixtures/api.json'
import const_data from '../fixtures/consts.json'

// Create uniq work items
for (let i = 0; i < Object.keys(api_data).length; i++) {
  let current_key = Object.keys(api_data)[i]
  console.log(current_key)
  api_data[current_key].api = api_data[current_key].api + ' ' + Date.now().toString()
}

describe('Sw Requirement Import', () => {
  beforeEach(() => {
    cy.login_admin()
  })

  it('Add SW Component', () => {
    //Add SW Component
    cy.get('#btn-add-sw-component').click()
    cy.fill_form_api('0', 'add', api_data.first, true, false)
    cy.get('#btn-modal-api-confirm').click()
    cy.wait(2000)
    //Check Sw component has been created
    cy.filter_api_from_dashboard(api_data.first)
  })

  it('Import from csv', () => {
    cy.import_sw_requirement(
      api_data.first,
      const_data.import.sw_requirements.csv.file,
      const_data.import.sw_requirements.csv.sw_requirement
    )
  })

  it('Import from json', () => {
    cy.import_sw_requirement(
      api_data.first,
      const_data.import.sw_requirements.json.file,
      const_data.import.sw_requirements.json.sw_requirement
    )
  })

  it('Import from strictdoc', () => {
    cy.import_sw_requirement(
      api_data.first,
      const_data.import.sw_requirements.strictdoc.file,
      const_data.import.sw_requirements.strictdoc.sw_requirement
    )
  })

  it('Import from yaml', () => {
    cy.import_sw_requirement(
      api_data.first,
      const_data.import.sw_requirements.yaml.file,
      const_data.import.sw_requirements.yaml.sw_requirement
    )
  })

  it('Import from xlsx', () => {
    cy.import_sw_requirement(
      api_data.first,
      const_data.import.sw_requirements.xlsx.file,
      const_data.import.sw_requirements.xlsx.sw_requirement
    )
  })
})
