/// <reference types="cypress" />

import "../support/e2e.js";
import api_data from "../fixtures/api.json";
import const_data from "../fixtures/consts.json";
import j_data from "../fixtures/justification.json";
import sr_data from "../fixtures/sw_requirement.json";
import tc_data from "../fixtures/test_case.json";
import ts_data from "../fixtures/test_specification.json";

describe("SW Components Dashboard testing", () => {
  beforeEach(() => {
    // Cypress starts out with a blank slate for each test
    // so we must tell it to visit our website with the `cy.visit()` command.
    // Since we want to visit the same URL at the start of all our tests,
    // we include it in our beforeEach function so that it runs before each test
    cy.visit(const_data.app_base_url);
    cy.wait(const_data.long_wait);
  });

  it("Add SW Component", () => {
    //Delete and Init the database
    cy.clear_db();
    //Reload Page
    cy.visit(const_data.app_base_url);
    cy.wait(const_data.long_wait);
    //Add SW Component
    cy.get("#btn-add-sw-component").click();
    cy.fill_form_api("0", "add", api_data.first, true, false);
    cy.get("#btn-modal-api-confirm").click();
    //Check Sw component has been created
    cy.get(const_data.api.table_listing_id)
      .find("tbody")
      .find("tr")
      .should("have.length", 2);
  });

  it("Unmatching Test Specification", () => {
    let id;
    cy.get(const_data.api.table_listing_id)
      .find("tbody")
      .find("tr")
      .should("have.length", 2);
    cy.get(const_data.api.table_listing_id)
      .find("tbody")
      .find("tr")
      .eq(0)
      .find("td")
      .eq(1)
      .invoke("text")
      .then((elem) => {
        id = elem;
        cy.visit(const_data.app_base_url + "/mapping/" + id);
        cy.wait(const_data.long_wait);
        cy.get(const_data.mapping.select_view_id).select(
          "test-specifications",
          { force: true },
        );
        cy.wait(const_data.long_wait);
        cy.get(const_data.mapping.table_unmatching_id)
          .find("tbody")
          .find("tr")
          .should("have.length", 0);
        cy.get("#btn-mapping-new-test-specification").click();
        cy.fill_form("test-specification", "add", ts_data.first, true, true);
        cy.get("#pf-tab-1-tab-btn-test-specification-mapping-section").click();
        cy.get("#btn-section-set-unmatching").click();
        cy.get("#pf-tab-0-tab-btn-test-specification-data").click();
        cy.get("#btn-mapping-test-specification-submit").click();
        cy.get(const_data.mapping.table_unmatching_id)
          .find("tbody")
          .find("tr")
          .should("have.length", 1);
        //Edit
        cy.get(const_data.mapping.table_unmatching_id)
          .find("tbody")
          .find("tr")
          .eq(0)
          .find("td")
          .eq(1)
          .find("button")
          .click();
        cy.get("#btn-menu-unmapped-edit-1").click();
        cy.fill_form(
          "test-specification",
          "edit",
          ts_data.first_mod,
          true,
          true,
        );
        cy.get("#btn-mapping-test-specification-submit").click();
        cy.get(const_data.mapping.table_unmatching_id)
          .find("tbody")
          .find("tr")
          .should("have.length", 1);
        //Delete
        cy.get(const_data.mapping.table_unmatching_id)
          .find("tbody")
          .find("tr")
          .eq(0)
          .find("td")
          .eq(1)
          .find("button")
          .click();
        cy.get("#btn-menu-unmapped-delete-1").click();
        cy.get("#btn-mapping-delete-confirm").click();
        cy.get(const_data.mapping.table_unmatching_id)
          .find("tbody")
          .find("tr")
          .should("have.length", 0);
      });
  });

  it("Matching New Test Specification", () => {
    let id;
    cy.get(const_data.api.table_listing_id)
      .find("tbody")
      .find("tr")
      .should("have.length", 2);
    cy.get(const_data.api.table_listing_id)
      .find("tbody")
      .find("tr")
      .eq(0)
      .find("td")
      .eq(1)
      .invoke("text")
      .then((elem) => {
        id = elem;
        cy.visit(const_data.app_base_url + "/mapping/" + id);
        cy.wait(const_data.long_wait);
        cy.get(const_data.mapping.select_view_id).select(
          "test-specifications",
          { force: true },
        );
        cy.wait(const_data.long_wait);
        cy.assign_work_item(-1, 0, "", "test-specification", ts_data.first);
        cy.edit_work_item(0, "test-specification", ts_data.first_mod);
        cy.assign_work_item(
          0,
          1,
          "test-specification",
          "test-case",
          tc_data.first,
        );
        cy.edit_work_item(1, "test-case", tc_data.first_mod);
        cy.delete_work_item(1, "test-case");
        cy.delete_work_item(0, "test-specification");
      });
  });

  it("Existing Test Specification", () => {
    let id;
    cy.get(const_data.api.table_listing_id)
      .find("tbody")
      .find("tr")
      .should("have.length", 2);
    cy.get(const_data.api.table_listing_id)
      .find("tbody")
      .find("tr")
      .eq(0)
      .find("td")
      .eq(1)
      .invoke("text")
      .then((elem) => {
        id = elem;
        cy.visit(const_data.app_base_url + "/mapping/" + id);
        cy.wait(const_data.long_wait);
        cy.get(const_data.mapping.select_view_id).select(
          "test-specifications",
          { force: true },
        );
        cy.wait(const_data.long_wait);
        //Add Existing Test Specification
        cy.assign_existing_work_item(-1, 0, "", "test-specification", 1);
        cy.edit_work_item(0, "test-specification", ts_data.first);

        cy.assign_existing_work_item(
          0,
          1,
          "test-specification",
          "test-case",
          1,
        );
        cy.edit_work_item(1, "test-case", tc_data.first);

        cy.delete_work_item(1, "test-case");
        cy.delete_work_item(0, "test-specification");
      });
  });
});
