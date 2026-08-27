import { splitUserFileToTmtPath } from './constants'

describe('splitUserFileToTmtPath', () => {
  test('splits a container user-file path and strips .fmf', () => {
    expect(splitUserFileToTmtPath('/BASIL-API/api/user-files/2/tmt/tmt-dummy-test.fmf')).toEqual({
      repository: '/BASIL-API',
      relativePath: '/api/user-files/2/tmt/tmt-dummy-test'
    })
  })

  test('splits a local checkout user-file path and strips .fmf', () => {
    expect(
      splitUserFileToTmtPath('/Users/dev/BASIL/api/user-files/2/tmt/tmt-dummy-test.fmf')
    ).toEqual({
      repository: '/Users/dev/BASIL',
      relativePath: '/api/user-files/2/tmt/tmt-dummy-test'
    })
  })

  test('keeps a non-fmf remainder unchanged', () => {
    expect(splitUserFileToTmtPath('/BASIL-API/api/user-files/2/notes.txt')).toEqual({
      repository: '/BASIL-API',
      relativePath: '/api/user-files/2/notes.txt'
    })
  })

  test('returns the full path as repository when /api/ is missing', () => {
    expect(splitUserFileToTmtPath('/tmp/outside.fmf')).toEqual({
      repository: '/tmp/outside.fmf',
      relativePath: ''
    })
  })

  test('handles an empty filepath', () => {
    expect(splitUserFileToTmtPath('')).toEqual({
      repository: '',
      relativePath: ''
    })
  })
})
