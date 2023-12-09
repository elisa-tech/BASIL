/// <reference types="cypress" />

import '../support/e2e.js'
import api_data from '../fixtures/api.json';
import const_data from '../fixtures/consts.json';
import j_data from '../fixtures/justification.json';
import sr_data from '../fixtures/sw_requirement.json';
import tc_data from '../fixtures/test_case.json';
import ts_data from '../fixtures/test_specification.json';

describe('SW Components Dashboard testing', () => {
  beforeEach(() => {
    // Cypress starts out with a blank slate for each test
    // so we must tell it to visit our website with the `cy.visit()` command.
    // Since we want to visit the same URL at the start of all our tests,
    // we include it in our beforeEach function so that it runs before each test
    cy.visit(const_data.app_base_url);
    cy.wait(const_data.long_wait);
  })

  it('Add SW Component', () => {
    //Delete and Init the database
    cy.clear_db();
    //Reload Page
    cy.visit(const_data.app_base_url);
    cy.wait(const_data.long_wait);
    //Add SW Component
    cy.get('#btn-add-sw-component').click();
    cy.fill_form_api('0', 'add', api_data.first, true, false);
    cy.get('#btn-modal-api-confirm').click();
    //Check Sw component has been created
    cy.get(const_data.api.table_listing_id).find('tbody').find('tr').should('have.length', 2);
  })
  /*

  it('Unmatching Sw Requirement', () => {
    let id;
    cy.get(const_data.api.table_listing_id).find('tbody').find('tr').should('have.length', 2);
    cy.get(const_data.api.table_listing_id).find('tbody').find('tr').eq(0).find('td').eq(1).invoke('text').then(elem => {
        id = elem;
        cy.visit(const_data.app_base_url + '/mapping/' + id);
        cy.wait(const_data.long_wait);
        cy.get(const_data.mapping.table_unmatching_id).find('tbody').find('tr').should('have.length', 0);
        cy.get('#btn-mapping-new-sw-requirement').click();
        cy.fill_form('sw-requirement', 'add', sr_data.first, true, true);
        cy.get('#pf-tab-1-tab-btn-sw-requirement-mapping-section').click();
        cy.get('#btn-section-set-unmatching').click();
        cy.get('#pf-tab-0-tab-btn-sw-requirement-data').click();
        cy.get('#btn-mapping-sw-requirement-submit').click();
        cy.get(const_data.mapping.table_unmatching_id).find('tbody').find('tr').should('have.length', 1);
        //Edit
        cy.get(const_data.mapping.table_unmatching_id).find('tbody').find('tr').eq(0).find('td').eq(1).find('button').click();
        cy.get('#btn-menu-unmapped-edit-1').click();
        cy.fill_form('sw-requirement', 'edit', sr_data.first_mod, true, true);
        cy.get('#btn-mapping-sw-requirement-submit').click();
        cy.get(const_data.mapping.table_unmatching_id).find('tbody').find('tr').should('have.length', 1);
        //Delete
        cy.get(const_data.mapping.table_unmatching_id).find('tbody').find('tr').eq(0).find('td').eq(1).find('button').click();
        cy.get('#btn-menu-unmapped-delete-1').click();
        cy.get('#btn-mapping-delete-confirm').click();
        cy.get(const_data.mapping.table_unmatching_id).find('tbody').find('tr').should('have.length', 0);
    });
  })
 */

  it('Matching New Sw Requirement', () => {
    let id;
    cy.get(const_data.api.table_listing_id).find('tbody').find('tr').should('have.length', 2);
    cy.get(const_data.api.table_listing_id).find('tbody').find('tr').eq(0).find('td').eq(1).invoke('text').then(elem => {
        id = elem;
        cy.visit(const_data.app_base_url + '/mapping/' + id);
        cy.wait(const_data.long_wait);

        cy.assign_work_item(-1, 0, '', 'sw-requirement', sr_data.first);
        cy.edit_work_item(0, 'sw-requirement', sr_data.first_mod);
        cy.assign_work_item(0, 1, 'sw-requirement', 'test-specification', ts_data.first);
        cy.edit_work_item(1, 'test-specification', ts_data.first_mod);
        cy.assign_work_item(1, 2, 'test-specification', 'test-case', tc_data.first);
        cy.edit_work_item(2, 'test-case', tc_data.first_mod);
        cy.assign_work_item(0, 3, 'sw-requirement', 'test-case', tc_data.second);
        cy.edit_work_item(3, 'test-case', tc_data.second_mod);

        cy.delete_work_item(3, 'test-case');
        cy.delete_work_item(2, 'test-case');
        cy.delete_work_item(1, 'test-specification');
        cy.delete_work_item(0, 'sw-requirement');
    })
  })

  it('Existing Sw Requirement', () => {
    let id;
    cy.get(const_data.api.table_listing_id).find('tbody').find('tr').should('have.length', 2);
    cy.get(const_data.api.table_listing_id).find('tbody').find('tr').eq(0).find('td').eq(1).invoke('text').then(elem => {
        id = elem;
        cy.visit(const_data.app_base_url + '/mapping/' + id);
        cy.wait(const_data.long_wait);

        cy.assign_existing_work_item(-1, 0, '', 'sw-requirement', 1);
        cy.edit_work_item(0, 'sw-requirement', sr_data.first);

        cy.assign_existing_work_item(0, 1, 'sw-requirement', 'test-specification', 1);
        cy.edit_work_item(1, 'test-specification', ts_data.first);

        cy.assign_existing_work_item(1, 2, 'test-specification', 'test-case', 1);
        cy.edit_work_item(2, 'test-case', tc_data.first);

        cy.assign_existing_work_item(0, 3, 'sw-requirement', 'test-case', 2);
        cy.edit_work_item(3, 'test-case', tc_data.second);

        cy.delete_work_item(3, 'test-case');
        cy.delete_work_item(2, 'test-case');
        cy.delete_work_item(1, 'test-specification');
        cy.delete_work_item(0, 'sw-requirement');
    })
  })
})
