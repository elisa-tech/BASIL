/// <reference types="cypress" />
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
    cy.wait(3000);
  });

  it("BASIL comes with no SW Components", () => {
    //Delete and Init the database
    cy.clear_db();
    //Reload page
    cy.visit(const_data.app_base_url);
    cy.wait(3000);
    cy.get(const_data.api.table_listing_id).find("tbody").should("not.exist");
  });

  it("Add SW Component", () => {
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

  it("Edit SW Component", () => {
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
        cy.get("#td-expand-" + id)
          .find("button")
          .click({ force: true });

        //Fill form with modified data
        cy.fill_form_api("1", "edit", api_data.first_mod, true, true);
        cy.get("#btn-api-form-reset").click();
        //Check that reset button works
        cy.fill_form_api("1", "edit", api_data.first, false, false);
        //Fill form with modified data
        cy.fill_form_api("1", "edit", api_data.first_mod, true, true);
        cy.get("#btn-api-form-submit").click();
      });
  });

  it("Check Table is updated", () => {
    cy.get(const_data.api.table_listing_id)
      .find("tbody")
      .find("tr")
      .should("have.length", 2);
    cy.get(const_data.api.table_listing_id)
      .find("tbody")
      .find("tr")
      .eq(0)
      .find("td")
      .eq(2)
      .invoke("text")
      .then((elem) => {
        expect(elem).equal(api_data.first_mod["api"]);
      });
  });

  it("Create a new version of an existing Sw Component", () => {
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
      .eq(6)
      .find("button")
      .click({ force: true });
    cy.wait(1000);
    cy.get(const_data.api.table_listing_id)
      .find("tbody")
      .find("tr")
      .eq(0)
      .find("td")
      .eq(1)
      .invoke("text")
      .then((elem) => {
        id = elem;
        cy.get("#btn-menu-api-new-version-" + id).click({ force: true });
        //Fill new version
        cy.get("#input-api-fork-library-version-" + id)
          .type(api_data.first_api_mod_new_version)
          .should("have.value", api_data.first_api_mod_new_version);
      });
    cy.get("#btn-modal-api-confirm").click();
    cy.get(const_data.api.table_listing_id)
      .find("tbody")
      .find("tr")
      .should("have.length", 4);
  });

  it("Search field should filter the SW Components", () => {
    cy.get(const_data.api.table_listing_id)
      .find("tbody")
      .find("tr")
      .should("have.length", 4);
    cy.get("#input-api-list-search").type(
      api_data.first_mod["library-version"] + " {del}",
    );
    cy.wait(2000);
    cy.get(const_data.api.table_listing_id)
      .find("tbody")
      .find("tr")
      .should("have.length", 2);
    cy.get("#input-api-list-search").type("{selectAll}{del}----------- {del}");
    cy.wait(2000);
    cy.get(const_data.api.table_listing_id).find("tbody").should("not.exist");
    cy.get("#input-api-list-search").type("{selectAll}{del}");
  });

  it("Delete SW Component", () => {
    let id;
    cy.get(const_data.api.table_listing_id)
      .find("tbody")
      .find("tr")
      .eq(0)
      .find("td")
      .eq(6)
      .find("button")
      .click({ force: true });
    cy.wait(2000);
    cy.get(const_data.api.table_listing_id)
      .find("tbody")
      .find("tr")
      .eq(0)
      .find("td")
      .eq(1)
      .invoke("text")
      .then((elem) => {
        id = elem;
        cy.get("#btn-menu-api-delete-" + id).click({ force: true });
        cy.get("#btn-api-delete-confirm").click({ force: true });
        cy.get(const_data.api.table_listing_id)
          .find("tbody")
          .find("tr")
          .should("have.length", 2);
      });
    cy.get(const_data.api.table_listing_id)
      .find("tbody")
      .find("tr")
      .eq(0)
      .find("td")
      .eq(6)
      .find("button")
      .click({ force: true });
    cy.wait(2000);
    cy.get(const_data.api.table_listing_id)
      .find("tbody")
      .find("tr")
      .eq(0)
      .find("td")
      .eq(1)
      .invoke("text")
      .then((elem) => {
        id = elem;
        cy.get("#btn-menu-api-delete-" + id).click({ force: true });
        cy.get("#btn-api-delete-confirm").click({ force: true });
        cy.get(const_data.api.table_listing_id)
          .find("tbody")
          .should("not.exist");
      });
  });
});
