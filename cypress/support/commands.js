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

import const_data from "../fixtures/consts.json";

Cypress.Commands.add("clear_db", () => {
  cy.request(const_data.api_base_url + "/test-support/init-db");
  cy.wait(const_data.long_wait);
});

Cypress.Commands.add(
  "fill_form_api",
  (_id, _action, _obj, type_before_check, clear_before_type) => {
    let i;
    let curr_key;
    let curr_key_hashes;
    for (i = 0; i < Object.keys(_obj).length; i++) {
      curr_key = Object.keys(_obj)[i];
      curr_key_hashes = curr_key.replaceAll("_", "-");
      if (type_before_check == true) {
        if (clear_before_type == true) {
          cy.get("#input-api-" + _action + "-" + curr_key_hashes + "-" + _id)
            .type("{selectAll}{del}")
            .type(_obj[curr_key])
            .should("have.value", _obj[curr_key]);
        } else {
          cy.get("#input-api-" + _action + "-" + curr_key_hashes + "-" + _id)
            .type(_obj[curr_key])
            .should("have.value", _obj[curr_key]);
        }
      } else {
        cy.get(
          "#input-api-" + _action + "-" + curr_key_hashes + "-" + _id,
        ).should("have.value", _obj[curr_key]);
      }
    }
  },
);

Cypress.Commands.add(
  "fill_form",
  (_obj_type, _action, _obj, type_before_check, clear_before_type) => {
    let i;
    let curr_key;
    let curr_key_hashes;
    for (i = 0; i < Object.keys(_obj).length; i++) {
      curr_key = Object.keys(_obj)[i];
      curr_key_hashes = curr_key.replaceAll("_", "-");
      if (type_before_check == true) {
        if (clear_before_type == true) {
          cy.get(
            '[id*="input-' +
              _obj_type +
              "-" +
              _action +
              "-" +
              curr_key_hashes +
              '-"]',
          )
            .type("{selectAll}{del}")
            .type(_obj[curr_key])
            .should("have.value", _obj[curr_key]);
        } else {
          cy.get(
            '[id*="input-' +
              _obj_type +
              "-" +
              _action +
              "-" +
              curr_key_hashes +
              '-"]',
          )
            .type(_obj[curr_key])
            .should("have.value", _obj[curr_key]);
        }
      } else {
        cy.get(
          '[id*="input-' +
            _obj_type +
            "-" +
            _action +
            "-" +
            curr_key_hashes +
            '-"]',
        ).should("have.value", _obj[curr_key]);
      }
    }
  },
);

Cypress.Commands.add("check_work_item", (_index, _type, _obj) => {
  let i = 0;
  let card;

  //Type Check
  card = cy
    .get(const_data.mapping.table_matching_id)
    .find("tbody")
    .find("tr")
    .eq(0)
    .find("td")
    .eq(1)
    .find("[class=pf-v5-c-card]");

  card.each(($el, index, $list) => {
    if (index == _index) {
      if (_type == "test-case") {
        cy.wrap($el).find("h2").contains("Test Case");
      }
    }
  });

  //Title Check
  card = cy
    .get(const_data.mapping.table_matching_id)
    .find("tbody")
    .find("tr")
    .eq(0)
    .find("td")
    .eq(1)
    .find("[class=pf-v5-c-card]");

  card.each(($el, index, $list) => {
    if (index == _index) {
      if (_type == "justification") {
        cy.wrap($el).find("h5").should("have.text", _obj.description);
      } else {
        cy.wrap($el).find("h5").should("have.text", _obj.title);
      }
    }
  });

  //Description Check
  card = cy
    .get(const_data.mapping.table_matching_id)
    .find("tbody")
    .find("tr")
    .eq(0)
    .find("td")
    .eq(1)
    .find("[class=pf-v5-c-card]");

  card.each(($el, index, $list) => {
    if (index == _index) {
      if (_type == "test-case" || _type == "sw-requirement") {
        cy.wrap($el)
          .find('p[class="work-item-detail-text"]')
          .should("have.text", _obj.description);
      } else if (_type == "test-specification") {
        cy.wrap($el)
          .find('p[class="work-item-detail-text"]')
          .should("have.text", _obj.test_description);
      }
    }
  });
});

Cypress.Commands.add("delete_work_item", (_index, _type) => {
  // Index 0 based
  let i = 0;
  let card;

  //Click Toggle Menu
  card = cy
    .get(const_data.mapping.table_matching_id)
    .find("tbody")
    .find("tr")
    .eq(0)
    .find("td")
    .eq(1)
    .find("[class=pf-v5-c-card]");

  card
    .find('button[class*="pf-v5-c-menu-toggle"]')
    .each(($el, index, $list) => {
      // $el is a wrapped jQuery element
      if (index == _index) {
        console.log("index: " + index);
        cy.wrap($el).click();
      } else {
        // do something else
      }
    });

  //Click Delete Button
  card = cy
    .get(const_data.mapping.table_matching_id)
    .find("tbody")
    .find("tr")
    .eq(0)
    .find("td")
    .eq(1)
    .find("[class=pf-v5-c-card]");

  card.each(($el, index, $list) => {
    // $el is a wrapped jQuery element
    if (index == _index) {
      console.log("index: " + index);
      cy.wrap($el)
        .find('button[id^="btn-menu-' + _type + '-delete"]')
        .click();
      cy.get("#btn-mapping-delete-confirm").click();
    } else {
      // do something else
    }
  });
});

Cypress.Commands.add(
  "assign_work_item",
  (_parent_index, _index, _parent_type, _type, _obj) => {
    // Index 0 based
    let i = 0;
    let card;

    if (_parent_index > -1) {
      //Click Toggle Menu
      card = cy
        .get(const_data.mapping.table_matching_id)
        .find("tbody")
        .find("tr")
        .eq(0)
        .find("td")
        .eq(1)
        .find("[class=pf-v5-c-card]");

      card
        .find('button[class*="pf-v5-c-menu-toggle"]')
        .each(($el, index, $list) => {
          // $el is a wrapped jQuery element
          if (index == _parent_index) {
            cy.wrap($el).click();
          } else {
            // do something else
          }
        });

      //Click Assign Button
      card = cy
        .get(const_data.mapping.table_matching_id)
        .find("tbody")
        .find("tr")
        .eq(0)
        .find("td")
        .eq(1)
        .find("[class=pf-v5-c-card]");

      card.each(($el, index, $list) => {
        // $el is a wrapped jQuery element
        if (index == _parent_index) {
          cy.wrap($el)
            .find(
              'button[id*="btn-menu-' +
                _parent_type +
                "-assign-" +
                _type +
                '-"]',
            )
            .click();
        } else {
          // do something else
        }
      });
    } else {
      cy.get(const_data.mapping.table_matching_id)
        .find("tbody")
        .find("tr")
        .eq(0)
        .find("td")
        .eq(0)
        .find("button")
        .click();
      cy.get("#btn-mapping-section-" + _type + "-0").click();
    }

    //Fill Form Data and Submit
    cy.fill_form(_type, "add", _obj, true, true);
    cy.get("#btn-mapping-" + _type + "-submit").click();
    cy.wait(const_data.long_wait);

    //Check Added Values
    cy.check_work_item(_index, _type, _obj);
  },
);

Cypress.Commands.add(
  "assign_existing_work_item",
  (_parent_index, _index, _parent_type, _type, _obj_index) => {
    // Index 0 based
    let i = 0;
    let card;

    if (_parent_index > -1) {
      //Click Toggle Menu
      card = cy
        .get(const_data.mapping.table_matching_id)
        .find("tbody")
        .find("tr")
        .eq(0)
        .find("td")
        .eq(1)
        .find("[class=pf-v5-c-card]");

      card
        .find('button[class*="pf-v5-c-menu-toggle"]')
        .each(($el, index, $list) => {
          // $el is a wrapped jQuery element
          if (index == _parent_index) {
            cy.wrap($el).click();
          } else {
            // do something else
          }
        });

      //Click Assign Button
      card = cy
        .get(const_data.mapping.table_matching_id)
        .find("tbody")
        .find("tr")
        .eq(0)
        .find("td")
        .eq(1)
        .find("[class=pf-v5-c-card]");

      card.each(($el, index, $list) => {
        // $el is a wrapped jQuery element
        if (index == _parent_index) {
          cy.wrap($el)
            .find(
              'button[id*="btn-menu-' +
                _parent_type +
                "-assign-" +
                _type +
                '-"]',
            )
            .click();
        } else {
          // do something else
        }
      });
    } else {
      cy.get(const_data.mapping.table_matching_id)
        .find("tbody")
        .find("tr")
        .eq(0)
        .find("td")
        .eq(0)
        .find("button")
        .click();
      cy.get("#btn-mapping-section-" + _type + "-0").click();
    }

    //Fill Form Data and Submit
    cy.get("button[class=pf-v5-c-tabs__link]").last().click();
    cy.wait(500);
    cy.get("#list-existing-" + _type + "-item-" + _obj_index).click();
    cy.get("#input-" + _type + "-coverage-0")
      .type("{selectAll}{del}")
      .type("50")
      .should("have.value", "50");
    cy.get("#btn-mapping-existing-" + _type + "-submit").click();
    cy.wait(2000);
  },
);

Cypress.Commands.add("edit_work_item", (_index, _type, _obj) => {
  // Index 0 based
  let i = 0;
  let card;

  //Click Toggle Menu
  card = cy
    .get(const_data.mapping.table_matching_id)
    .find("tbody")
    .find("tr")
    .eq(0)
    .find("td")
    .eq(1)
    .find("[class=pf-v5-c-card]");

  card
    .find('button[class*="pf-v5-c-menu-toggle"]')
    .each(($el, index, $list) => {
      // $el is a wrapped jQuery element
      if (index == _index) {
        cy.wrap($el).click();
      } else {
        // do something else
      }
    });

  //Click Edit Button
  card = cy
    .get(const_data.mapping.table_matching_id)
    .find("tbody")
    .find("tr")
    .eq(0)
    .find("td")
    .eq(1)
    .find("[class=pf-v5-c-card]");

  card.each(($el, index, $list) => {
    // $el is a wrapped jQuery element
    if (index == _index) {
      console.log("index: " + index);
      cy.wrap($el)
        .find('button[id^="btn-menu-' + _type + '-edit"]')
        .click();
      cy.fill_form(_type, "edit", _obj, true, true);
      cy.get("#btn-mapping-" + _type + "-submit").click();
      cy.wait(const_data.long_wait);
      cy.check_work_item(_index, _type, _obj);
    } else {
      // do something else
    }
  });
});
