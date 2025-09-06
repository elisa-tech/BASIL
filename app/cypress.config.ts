import { defineConfig } from 'cypress'
import failFastPlugin from 'cypress-fail-fast/plugin'

export default defineConfig({
  e2e: {
    setupNodeEvents(on, config) {
      failFastPlugin(on, config)
      return config
    },
  },
})
