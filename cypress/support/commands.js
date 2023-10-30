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

Cypress.Commands.add('clear_db', () => {
  cy.request('http://localhost:5000/test-support/init-db');
  cy.wait(3000);
})

Cypress.Commands.add('fill_form_api', (_id, _action, _obj, type_before_check, clear_before_type) => {
  let i;
   let curr_key;
   let curr_key_hashes;
   for (i = 0; i<Object.keys(_obj).length; i++){
     curr_key = Object.keys(_obj)[i];
     curr_key_hashes = curr_key.replaceAll('_', '-');
     if(type_before_check == true){
       if (clear_before_type == true){
         cy.get('#input-api-' + _action + '-' + curr_key_hashes  + '-' + _id)
           .type('{selectAll}{del}').type(_obj[curr_key]).should('have.value', _obj[curr_key]);
       } else {
         cy.get('#input-api-' + _action + '-' + curr_key_hashes  + '-' + _id)
           .type(_obj[curr_key]).should('have.value', _obj[curr_key]);
       }
     } else {
       cy.get('#input-api-' + _action + '-' + curr_key_hashes  + '-' + _id)
         .should('have.value', _obj[curr_key]);
     }
   }
})

Cypress.Commands.add('fill_form', (_id, _obj_type, _action, _obj, type_before_check, clear_before_type) => {
  let i;
  let curr_key;
  let curr_key_hashes;
  for (i = 0; i<Object.keys(_obj).length; i++){
    curr_key = Object.keys(_obj)[i];
    curr_key_hashes = curr_key.replaceAll('_', '-');
    if(type_before_check == true){
      if (clear_before_type == true){
        cy.get('#input-' + _obj_type + '-' + _action + '-' + curr_key_hashes  + '-' + _id)
          .type('{selectAll}{del}').type(_obj[curr_key]).should('have.value', _obj[curr_key]);
      } else {
        cy.get('#input-' + _obj_type + '-' + _action + '-' + curr_key_hashes  + '-' + _id)
          .type(_obj[curr_key]).should('have.value', _obj[curr_key]);
      }
    } else {
      cy.get('#input-' + _obj_type + '-' + _action + '-' + curr_key_hashes  + '-' + _id)
        .should('have.value', _obj[curr_key]);
    }
  }
})