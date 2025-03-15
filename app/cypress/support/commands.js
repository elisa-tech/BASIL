// ***********************************************
// This example commands.js shows you how to
// create various custom commands and overwrite
// existing commands.
//
// For more comprehensive examples of custom
// commands please read more here:
// https://on.cypress.io/custom-commands
// ***********************************************
//
//
// -- This is a parent command --
// Cypress.Commands.add('login', (email, password) => { ... })
//
//
// -- This is a child command --
// Cypress.Commands.add('drag', { prevSubject: 'element'}, (subject, options) => { ... })
//
//
// -- This is a dual command --
// Cypress.Commands.add('dismiss', { prevSubject: 'optional'}, (subject, options) => { ... })
//
//
// -- This will overwrite an existing command --
// Cypress.Commands.overwrite('visit', (originalFn, url, options) => { ... })

import const_data from '../fixtures/consts.json'

export function registerCommands() {
  Cypress.Commands.add('clear_db', () => {
    cy.request(const_data.api_base_url + '/test-support/init-db')
    cy.wait(const_data.long_wait)
  })

  Cypress.Commands.add('login_admin', () => {
    cy.visit(const_data.app_base_url + '/login')
    cy.wait(const_data.mid_wait)
    cy.url().should('eq', const_data.app_base_url + '/login')

    //Fill form
    cy.get(const_data.login.input_username).type(const_data.users.admin.username).should('have.value', const_data.users.admin.username)
    cy.get(const_data.login.input_password)
      .type(const_data.users.admin.password)
      .should('have.value', const_data.users.admin.password)
      .type('{enter}')
    cy.wait(const_data.mid_wait)

    // Redirected and logged in
    cy.url().should('eq', const_data.app_base_url + '/')
    cy.contains('span[class^="pf-v5-c-menu-toggle__text"]', const_data.users.admin.username)
    cy.get('span.pf-v5-c-masthead__toggle').find('button').click()
  })

  Cypress.Commands.add('filter_api_from_dashboard', (api) => {
    cy.visit(const_data.app_base_url + '?currentLibrary=' + api.library)
    cy.wait(1500)
    cy.get(const_data.api.input_search_id).type('{selectAll}{del}' + api.api + '{enter}')
    cy.wait(1500)
    cy.get(const_data.api.table_listing_id).find('tbody').find('tr').find('td').contains(api.api)
    cy.get(const_data.api.table_listing_id).find('tbody').find('tr').find('td').contains(api['library-version'])
  })

  Cypress.Commands.add('fill_form_api', (_id, _action, _obj, type_before_check, clear_before_type) => {
    let i
    let curr_key
    let curr_key_hashes
    for (i = 0; i < Object.keys(_obj).length; i++) {
      curr_key = Object.keys(_obj)[i]
      curr_key_hashes = curr_key.replaceAll('_', '-')
      if (type_before_check == true) {
        if (clear_before_type == true) {
          cy.get('#input-api-' + _action + '-' + curr_key_hashes + '-' + _id)
            .type('{selectAll}{del}')
            .type(_obj[curr_key])
            .should('have.value', _obj[curr_key])
        } else {
          cy.get('#input-api-' + _action + '-' + curr_key_hashes + '-' + _id)
            .type(_obj[curr_key])
            .should('have.value', _obj[curr_key])
        }
      } else {
        cy.get('#input-api-' + _action + '-' + curr_key_hashes + '-' + _id).should('have.value', _obj[curr_key])
      }
    }
  })

  Cypress.Commands.add('fill_form', (_obj_type, _action, _obj, type_before_check, clear_before_type) => {
    let i
    let curr_key
    let curr_key_hashes
    for (i = 0; i < Object.keys(_obj).length; i++) {
      curr_key = Object.keys(_obj)[i]
      curr_key_hashes = curr_key.replaceAll('_', '-')
      let field_type = 'input'
      if (_obj_type == 'document') {
        if (['spdx_relation', 'file', 'type'].includes(curr_key)) {
          field_type = 'select'
        }
      }
      if (type_before_check == true) {
        if (clear_before_type == true) {
          if (field_type == 'input') {
            if (_obj_type == 'document' && ['url'].includes(curr_key)) {
              // Some fields are calling the API on each change in cypress and that is
              // overloading the api
              cy.get('[id*="input-' + _obj_type + '-' + _action + '-' + curr_key_hashes + '-"]')
                .clear()
                .invoke('val', _obj[curr_key])
                .type('{end} {backspace}')
                .should('have.value', _obj[curr_key])
            } else {
              cy.get('[id*="input-' + _obj_type + '-' + _action + '-' + curr_key_hashes + '-"]')
                .type('{selectAll}{del}')
                .type(_obj[curr_key])
                .should('have.value', _obj[curr_key])
            }
          }
        } else {
          if (field_type == 'input') {
            if (_obj_type == 'document' && ['url'].includes(curr_key)) {
              // Some fields are calling the API on each change in cypress and that is
              // overloading the api
              cy.get('[id*="input-' + _obj_type + '-' + _action + '-' + curr_key_hashes + '-"]')
                .invoke('val', _obj[curr_key])
                .type('{end} {backspace}')
                .should('have.value', _obj[curr_key])
            } else {
              cy.get('[id*="input-' + _obj_type + '-' + _action + '-' + curr_key_hashes + '-"]')
                .type(_obj[curr_key])
                .should('have.value', _obj[curr_key])
            }
          }
        }
      } else {
        if (field_type == 'input') {
          cy.get('[id*="input-' + _obj_type + '-' + _action + '-' + curr_key_hashes + '-"]').should('have.value', _obj[curr_key])
        }
      }

      if (field_type == 'select') {
        cy.get('[id*="select-' + _obj_type + '-' + _action + '-' + curr_key_hashes + '-"]')
          .select(_obj[curr_key])
          .should('have.value', _obj[curr_key])
      }
    }
  })

  Cypress.Commands.add('check_work_item', (_index, _type, _obj) => {
    let i = 0
    let card

    //Type Check
    card = cy.get(const_data.mapping.table_matching_id).find('tbody').find('tr').eq(0).find('td').eq(1).find('[class=pf-v5-c-card]')

    card.each(($el, index, $list) => {
      if (index == _index) {
        cy.wrap($el)
          .find('h2')
          .filter(':contains(' + const_data.work_item_types[_type]['mapping-label'] + ')')
          .should('have.length.greaterThan', 0)
      }
    })

    //Title Check
    card = cy.get(const_data.mapping.table_matching_id).find('tbody').find('tr').eq(0).find('td').eq(1).find('[class=pf-v5-c-card]')

    card.each(($el, index, $list) => {
      if (index == _index) {
        if (_type == 'justification') {
          cy.wrap($el).find('p').last().should('have.text', _obj.description)
        } else {
          cy.get('h5')
            .should('have.length.greaterThan', 0)
            .filter(':contains(' + _obj.title + ')')
            .should('have.length.greaterThan', 0)
        }
      }
    })

    //Description Check
    card = cy.get(const_data.mapping.table_matching_id).find('tbody').find('tr').eq(0).find('td').eq(1).find('[class=pf-v5-c-card]')

    card.each(($el, index, $list) => {
      if (index == _index) {
        if (_type == 'test-case' || _type == 'sw-requirement') {
          cy.wrap($el)
            .find('p[class="work-item-detail-text"]')
            .filter(':contains(' + _obj.description + ')')
            .should('have.length.greaterThan', 0)
        } else if (_type == 'test-specification') {
          cy.wrap($el)
            .find('p[class="work-item-detail-text"]')
            .filter(':contains(' + _obj.test_description + ')')
            .should('have.length.greaterThan', 0)
        }
      }
    })
  })

  Cypress.Commands.add('delete_work_item', (_index, _type) => {
    // Index 0 based
    let i = 0
    let card

    //Click Toggle Menu
    card = cy.get(const_data.mapping.table_matching_id).find('tbody').find('tr').eq(0).find('td').eq(1).find('[class=pf-v5-c-card]')

    card.find('button[class*="pf-v5-c-menu-toggle"]').each(($el, index, $list) => {
      // $el is a wrapped jQuery element
      if (index == _index) {
        console.log('index: ' + index)
        cy.wrap($el).click()
      } else {
        // do something else
      }
    })

    //Click Delete Button
    card = cy.get(const_data.mapping.table_matching_id).find('tbody').find('tr').eq(0).find('td').eq(1).find('[class=pf-v5-c-card]')

    card.each(($el, index, $list) => {
      // $el is a wrapped jQuery element
      if (index == _index) {
        console.log('index: ' + index)
        cy.wrap($el)
          .find('button[id^="btn-menu-' + _type + '-delete"]')
          .click()
        cy.get('#btn-mapping-delete-confirm').click()
      } else {
        // do something else
      }
    })
  })

  Cypress.Commands.add('assign_work_item', (_parent_index, _index, _parent_type, _type, _obj) => {
    // Index 0 based
    let i = 0
    let card

    if (_parent_index > -1) {
      //Click Toggle Menu
      card = cy.get(const_data.mapping.table_matching_id).find('tbody').find('tr').eq(0).find('td').eq(1).find('[class=pf-v5-c-card]')

      card.find('button[class*="pf-v5-c-menu-toggle"]').each(($el, index, $list) => {
        // $el is a wrapped jQuery element
        if (index == _parent_index) {
          cy.wrap($el).click()
        } else {
          // do something else
        }
      })

      //Click Assign Button
      card = cy.get(const_data.mapping.table_matching_id).find('tbody').find('tr').eq(0).find('td').eq(1).find('[class=pf-v5-c-card]')

      card.each(($el, index, $list) => {
        // $el is a wrapped jQuery element
        if (index == _parent_index) {
          cy.wrap($el)
            .find('button[id*="btn-menu-' + _parent_type + '-assign-' + _type + '-"]')
            .click()
        } else {
          // do something else
        }
      })
    } else {
      cy.get(const_data.mapping.table_matching_id).find('tbody').find('tr').eq(0).find('td').eq(0).find('button').click()
      cy.get('#btn-mapping-section-' + _type + '-0').click()
    }

    //Fill Form Data and Submit
    cy.fill_form(_type, 'add', _obj, true, true)

    // In case of text document I have to select a section and an offset
    if (_type == 'document') {
      if (_obj.type == 'text') {
        cy.get('button[id*="btn-document-"][id*="-load-file-content-"]').click({ force: true })
        cy.wait(const_data.long_wait * 2)
        cy.get('button[id*="btn-document-"][id*="-section-set-full-"]').click()
        cy.wait(const_data.fast_wait)
      }
    }
    cy.wait(const_data.long_wait * 3)
    cy.get('#btn-mapping-' + _type + '-submit').click()
    cy.wait(const_data.long_wait * 3)

    //Check Added Values
    cy.check_work_item(_parent_index, _type, _obj)
  })

  Cypress.Commands.add('import_sw_requirement', (api_data, import_file, sw_requirement) => {
    let id

    // Select the api from the list
    cy.filter_api_from_dashboard(api_data)

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
        cy.get('#btn-mapping-new-sw-requirement').click()
        cy.get('#pf-tab-3-tab-btn-sw-requirement-import').click()

        cy.get('#sw-requirement-file-upload-filename').selectFile(import_file, { action: 'drag-drop' })

        // Check the first requirment in the table
        let row = cy.get('#table-sw-requirement-import').find('tbody').find('tr').find('td').contains(sw_requirement.title)
        row.parent('tr').eq(0).find('td').eq(0).find('input').check().should('be.checked')

        // Submit the import
        cy.get('#btn-sw-requirement-import-submit').click()

        // Move to the Existing Test Cases tab
        cy.get('#pf-tab-2-tab-btn-sw-requirement-existing').click()

        cy.get('#input-search-sw-requirement-existing').type('{selectAll}{del}').type(sw_requirement.title).type('{enter}')

        cy.get('#list-existing-sw-requirements').find('li').should('have.length.greaterThan', 0)
      })
  })

  Cypress.Commands.add('assign_existing_work_item', (_parent_index, _index, _parent_type, _type, _obj_index) => {
    // Index 0 based
    let i = 0
    let card

    if (_parent_index > -1) {
      //Click Toggle Menu
      card = cy.get(const_data.mapping.table_matching_id).find('tbody').find('tr').eq(0).find('td').eq(1).find('[class=pf-v5-c-card]')

      card.find('button[class*="pf-v5-c-menu-toggle"]').each(($el, index, $list) => {
        // $el is a wrapped jQuery element
        if (index == _parent_index) {
          cy.wrap($el).click()
        } else {
          // do something else
        }
      })

      //Click Assign Button
      card = cy.get(const_data.mapping.table_matching_id).find('tbody').find('tr').eq(0).find('td').eq(1).find('[class=pf-v5-c-card]')

      card.each(($el, index, $list) => {
        // $el is a wrapped jQuery element
        if (index == _parent_index) {
          cy.wrap($el)
            .find('button[id*="btn-menu-' + _parent_type + '-assign-' + _type + '-"]')
            .click()
        } else {
          // do something else
        }
      })
    } else {
      cy.get(const_data.mapping.table_matching_id).find('tbody').find('tr').eq(0).find('td').eq(0).find('button').click()
      cy.get('#btn-mapping-section-' + _type + '-0').click()
    }

    //Fill Form Data and Submit
    cy.get('button[class=pf-v5-c-tabs__link]').filter(':contains("Existing")').click()
    cy.wait(500)
    cy.get('#list-existing-' + _type + '-item-' + _obj_index).click()
    cy.get('#input-' + _type + '-coverage-existing')
      .clear()
      .type('50')
      .should('have.value', '50')
    cy.get('#btn-mapping-existing-' + _type + '-submit').click()
    cy.wait(2000)
  })

  Cypress.Commands.add('edit_work_item', (_index, _type, _obj) => {
    // Index 0 based
    let i = 0
    let card

    //Click Toggle Menu
    card = cy.get(const_data.mapping.table_matching_id).find('tbody').find('tr').eq(0).find('td').eq(1).find('[class=pf-v5-c-card]')

    card.find('button[class*="pf-v5-c-menu-toggle"]').each(($el, index, $list) => {
      // $el is a wrapped jQuery element
      if (index == _index) {
        cy.wrap($el).click()
      } else {
        // do something else
      }
    })

    //Click Edit Button
    card = cy.get(const_data.mapping.table_matching_id).find('tbody').find('tr').eq(0).find('td').eq(1).find('[class=pf-v5-c-card]')

    card.each(($el, index, $list) => {
      // $el is a wrapped jQuery element
      if (index == _index) {
        console.log('index: ' + index)
        cy.wrap($el)
          .find('button[id^="btn-menu-' + _type + '-edit"]')
          .click()
        cy.fill_form(_type, 'edit', _obj, true, true)
        cy.get('#btn-mapping-' + _type + '-submit').click()
        cy.wait(const_data.long_wait)
        cy.check_work_item(_index, _type, _obj)
      } else {
        // do something else
      }
    })
  })
}
