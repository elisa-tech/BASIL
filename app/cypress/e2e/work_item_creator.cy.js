/// <reference types="cypress" />
/**
 * Work item creator
 *
 * The cards of the mapping views show who created each work item, with the
 * avatar of that user. Work items only carry the username of their creator,
 * so the avatar of another user is read by username.
 */
import '../support/e2e.js'
import api_data_fixture from '../fixtures/api.json'
import const_data from '../fixtures/consts.json'
import sr_data_fixture from '../fixtures/sw_requirement.json'
import { createUniqWorkItems } from '../support/utils.js'

let api_data = createUniqWorkItems(api_data_fixture, ['api'])
let sr_data = createUniqWorkItems(sr_data_fixture, ['title'])

const uiTimeout = 20000
const OTHER_USERNAME = 'another_creator'
// 1x1 transparent PNG
const OTHER_USER_AVATAR =
  'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=='

const visitMapping = (apiId, view) => {
  cy.visit(const_data.app_base_url + '/mapping/' + apiId)
  cy.wait(const_data.long_wait)
  if (view) {
    cy.get(const_data.mapping.select_view_id, { timeout: uiTimeout }).select(view, { force: true })
    cy.wait(const_data.long_wait)
  }
}

// Give every work item of a mapping response another creator
const replaceCreator = (value, from, to) => {
  if (Array.isArray(value)) {
    value.forEach((item) => replaceCreator(item, from, to))
  } else if (value && typeof value === 'object') {
    Object.keys(value).forEach((key) => {
      if (key === 'created_by' && value[key] === from) {
        value[key] = to
      } else {
        replaceCreator(value[key], from, to)
      }
    })
  }
}

describe(
  'Work item creator',
  {
    defaultCommandTimeout: 15000,
    requestTimeout: 15000,
    viewportWidth: 1280,
    viewportHeight: 900,
    scrollBehavior: 'center'
  },
  () => {
    let apiId

    beforeEach(() => {
      cy.login_admin()
    })

    it('Setup: create a SW Component with a Software Requirement', () => {
      cy.get('#btn-add-sw-component').click()
      cy.fill_form_api('0', 'add', api_data.first, true, false)
      cy.get('#btn-modal-api-confirm').click()
      cy.wait(2000)
      cy.filter_api_from_dashboard(api_data.first)
      cy.get(const_data.api.table_listing_id)
        .find('tbody')
        .find('tr')
        .eq(0)
        .find('td')
        .eq(1)
        .invoke('text')
        .then((id) => {
          apiId = String(id).trim()
          visitMapping(apiId)
          cy.assign_work_item(-1, 0, '', 'sw-requirement', sr_data.first)
        })
    })

    it('The card shows its creator, with the avatar of the current user', () => {
      visitMapping(apiId)
      cy.get('#header-user-avatar')
        .invoke('attr', 'src')
        .then((src) => {
          cy.get(const_data.mapping.table_matching_id, { timeout: uiTimeout })
            .find('.created-by-label', { timeout: uiTimeout })
            .first()
            .should('contain.text', const_data.users.admin.username)
            .find('.user-avatar-icon')
            .should('have.attr', 'src', src)
        })
    })

    it('The dynamic view shows the creator too', () => {
      visitMapping(apiId, 'dynamic-view')
      cy.get('#table-dynamic-view', { timeout: uiTimeout })
        .find('.created-by-label', { timeout: uiTimeout })
        .first()
        .should('contain.text', const_data.users.admin.username)
    })

    it('The card shows the avatar of another creator', () => {
      cy.intercept({ method: 'GET', url: /\/mapping\/api\/sw-requirements\?/ }, (req) => {
        req.continue((res) => {
          replaceCreator(res.body, const_data.users.admin.username, OTHER_USERNAME)
        })
      })
      cy.intercept(
        { method: 'GET', url: new RegExp('/user/avatar\\?.*target-username=' + OTHER_USERNAME) },
        { statusCode: 200, body: { type: 'custom', data: OTHER_USER_AVATAR } }
      ).as('otherCreatorAvatar')
      visitMapping(apiId)
      cy.wait('@otherCreatorAvatar')
      cy.get(const_data.mapping.table_matching_id, { timeout: uiTimeout })
        .find('.created-by-label', { timeout: uiTimeout })
        .first()
        .should('contain.text', OTHER_USERNAME)
        .find('.user-avatar-icon')
        .should('have.attr', 'src', OTHER_USER_AVATAR)
    })

    it('Cleanup: delete the Software Requirement', () => {
      visitMapping(apiId)
      cy.delete_work_item(0, 'sw-requirement')
    })
  }
)
