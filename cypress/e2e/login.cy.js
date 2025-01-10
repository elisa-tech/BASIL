/// <reference types="cypress" />

import "../support/e2e.js";
import api_data from "../fixtures/api.json";
import const_data from "../fixtures/consts.json";

describe("Login", () => {
  it("Check login", () => {
    cy.visit(const_data.app_base_url + "/login");
    cy.wait(const_data.long_wait);
    cy.url().should("eq", const_data.app_base_url + "/login");

    //Fill form
    cy.get(const_data.login.input_username)
      .type(const_data.users.admin.username)
      .should("have.value", const_data.users.admin.username);
    cy.get(const_data.login.input_password)
      .type(const_data.users.admin.password)
      .should("have.value", const_data.users.admin.password)
      .type("{enter}");
    cy.wait(const_data.long_wait);

    // Redirected and logged in
    cy.url().should("eq", const_data.app_base_url + "/");
    cy.contains(
      'span[class^="pf-v5-c-menu-toggle__text"]',
      const_data.users.admin.username,
    );
  });
});
