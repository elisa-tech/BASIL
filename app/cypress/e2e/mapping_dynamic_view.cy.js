/// <reference types="cypress" />

import '../support/e2e.js'
import api_data_fixture from '../fixtures/api.json'
import const_data from '../fixtures/consts.json'
import sr_data_fixture from '../fixtures/sw_requirement.json'
import tc_data_fixture from '../fixtures/test_case.json'
import j_data_fixture from '../fixtures/justification.json'
import { createUniqWorkItems } from '../support/utils.js'

let api_data = createUniqWorkItems(api_data_fixture, ['api'])
let sr_data = createUniqWorkItems(sr_data_fixture, ['title'])
let tc_data = createUniqWorkItems(tc_data_fixture, ['title'])
let j_data = createUniqWorkItems(j_data_fixture, ['description'])

describe('Dynamic View Mapping', () => {
  beforeEach(() => {
    cy.login_admin()
  })

  it('Add SW Component', () => {
    cy.get('#btn-add-sw-component').click()
    cy.fill_form_api('0', 'add', api_data.first, true, false)
    cy.get('#btn-modal-api-confirm').click()
    cy.wait(2000)
    cy.filter_api_from_dashboard(api_data.first)
  })

  it('Switch to Dynamic View with no work items', () => {
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
        cy.visit(const_data.app_base_url + '/mapping/' + id)
        cy.wait(const_data.long_wait)

        cy.get(const_data.mapping.select_view_id).select('dynamic-view', { force: true })
        cy.wait(const_data.long_wait)

        cy.get('#table-dynamic-view').should('exist')
        cy.get('#table-dynamic-view').contains('No work items mapped to this specification.')
      })
  })

  it('Dynamic View shows mapped Software Requirement', () => {
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
        cy.visit(const_data.app_base_url + '/mapping/' + id)
        cy.wait(const_data.long_wait)

        cy.assign_work_item(-1, 0, '', 'sw-requirement', sr_data.first)

        cy.get(const_data.mapping.select_view_id).select('dynamic-view', { force: true })
        cy.wait(const_data.long_wait)

        cy.get('#table-dynamic-view').should('exist')
        cy.get('#table-dynamic-view').find('.pf-v5-c-card').should('have.length.greaterThan', 0)
        cy.get('#table-dynamic-view').contains('h3', 'Software Requirements')
        cy.get('#table-dynamic-view').contains('h5', sr_data.first.title)

        cy.get(const_data.mapping.select_view_id).select('sw-requirements', { force: true })
        cy.wait(const_data.long_wait)

        cy.delete_work_item(0, 'sw-requirement')
        cy.wait(const_data.long_wait)
      })
  })

  it('Dynamic View shows mapped Justification', () => {
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
        cy.visit(const_data.app_base_url + '/mapping/' + id)
        cy.wait(const_data.long_wait)

        cy.assign_work_item(-1, 0, '', 'justification', j_data.first)

        cy.get(const_data.mapping.select_view_id).select('dynamic-view', { force: true })
        cy.wait(const_data.long_wait)

        cy.get('#table-dynamic-view').should('exist')
        cy.get('#table-dynamic-view').contains('h3', 'Justifications')
        cy.get('#table-dynamic-view').contains(j_data.first.description)

        cy.get(const_data.mapping.select_view_id).select('sw-requirements', { force: true })
        cy.wait(const_data.long_wait)

        cy.delete_work_item(0, 'justification')
        cy.wait(const_data.long_wait)
      })
  })

  it('Dynamic View card selection highlights snippets', () => {
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
        cy.visit(const_data.app_base_url + '/mapping/' + id)
        cy.wait(const_data.long_wait)

        cy.assign_work_item(-1, 0, '', 'sw-requirement', sr_data.second)

        cy.get(const_data.mapping.select_view_id).select('dynamic-view', { force: true })
        cy.wait(const_data.long_wait)

        cy.get('#table-dynamic-view').find('.pf-v5-c-card').first().click()
        cy.wait(const_data.fast_wait)

        cy.get('#table-dynamic-view').contains('button', 'Show full document').should('exist')

        cy.get('#table-dynamic-view').contains('button', 'Show full document').scrollIntoView().click({ force: true })
        cy.wait(const_data.fast_wait)

        cy.get('#table-dynamic-view').contains('button', 'Show full document').should('not.exist')

        cy.get(const_data.mapping.select_view_id).select('sw-requirements', { force: true })
        cy.wait(const_data.long_wait)

        cy.delete_work_item(0, 'sw-requirement')
        cy.wait(const_data.long_wait)
      })
  })

  it('Dynamic View shows multiple work item types', () => {
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
        cy.visit(const_data.app_base_url + '/mapping/' + id)
        cy.wait(const_data.long_wait)

        cy.assign_work_item(-1, 0, '', 'sw-requirement', sr_data.third)

        cy.get(const_data.mapping.select_view_id).select('test-cases', { force: true })
        cy.wait(const_data.long_wait)

        cy.assign_work_item(-1, 0, '', 'test-case', tc_data.first)

        cy.get(const_data.mapping.select_view_id).select('dynamic-view', { force: true })
        cy.wait(const_data.long_wait)

        cy.get('#table-dynamic-view').should('exist')
        cy.get('#table-dynamic-view').contains('h3', 'Software Requirements')
        cy.get('#table-dynamic-view').contains('h5', sr_data.third.title)
        cy.get('#table-dynamic-view').contains('h3', 'Test Cases')
        cy.get('#table-dynamic-view').contains('h5', tc_data.first.title)

        cy.get(const_data.mapping.select_view_id).select('test-cases', { force: true })
        cy.wait(const_data.long_wait)
        cy.delete_work_item(0, 'test-case')
        cy.wait(const_data.long_wait)

        cy.get(const_data.mapping.select_view_id).select('sw-requirements', { force: true })
        cy.wait(const_data.long_wait)
        cy.delete_work_item(0, 'sw-requirement')
        cy.wait(const_data.long_wait)
      })
  })

  it('Dynamic View displays specification content', () => {
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
        cy.visit(const_data.app_base_url + '/mapping/' + id)
        cy.wait(const_data.long_wait)

        cy.get(const_data.mapping.select_view_id).select('dynamic-view', { force: true })
        cy.wait(const_data.long_wait)

        cy.get('#table-dynamic-view').find('pre').should('exist')
        cy.get('#table-dynamic-view').find('pre').invoke('text').should('have.length.greaterThan', 0)
      })
  })
})
