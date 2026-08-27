/** @type {import('jest').Config} */
module.exports = {
  testEnvironment: 'node',
  transform: {
    '^.+\\.tsx?$': ['ts-jest', { isolatedModules: true }]
  },
  // .ts unit tests (e.g. constants.test.ts). The existing App RTL suite is .tsx.
  testMatch: ['**/?(*.)+(test).ts']
}
