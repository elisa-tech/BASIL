const { defineConfig } = require("cypress");

module.exports = defineConfig({
  e2e: {
    // Point to the correct directories in app/cypress/
    specPattern: "app/cypress/e2e/**/*.cy.{js,jsx,ts,tsx}",
    supportFile: "app/cypress/support/e2e.js",
    fixturesFolder: "app/cypress/fixtures",
    screenshotsFolder: "app/cypress/screenshots",
    videosFolder: "app/cypress/videos",
    downloadsFolder: "app/cypress/downloads",

    setupNodeEvents(on, config) {
      // implement node event listeners here
      return config
    },
  },
});
