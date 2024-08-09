export const API_BASE_URL = 'http://localhost:5000'

export const force_reload = true

export const _A = 'api'
export const _D = 'document'
export const _Ds = 'documents'
export const _J = 'justification'
export const _Js = 'justifications'
export const _M_ = '_mapping_'
export const _RS = 'specifications'
export const _SR = 'sw-requirement'
export const _SRs = 'sw-requirements'
export const _SR_ = 'sw_requirement'
export const _SRs_ = 'sw_requirements'
export const _TC = 'test-case'
export const _TCs = 'test-cases'
export const _TC_ = 'test_case'
export const _TCs_ = 'test_cases'
export const _TS = 'test-specification'
export const _TSs = 'test-specifications'
export const _TS_ = 'test_specification'
export const _TSs_ = 'test_specifications'

export const DEFAULT_VIEW = _SRs
export type validate = 'success' | 'warning' | 'error' | 'error2' | 'default' | 'indeterminate' | 'undefined'

export const document_type = [
  { value: 'file', label: 'file', disabled: false },
  { value: 'text', label: 'text', disabled: false }
]

export const provision_type = [
  { value: '', label: '', disabled: false },
  { value: 'container', label: 'Fedora Container', disabled: false },
  { value: 'connect', label: 'SSH', disabled: false }
]

export const spdx_relations = [
  { value: '', label: 'Select a value', disabled: false },
  { value: 'AFFECTS', label: 'AFFECTS', disabled: false },
  { value: 'AMENDS', label: 'AMENDS', disabled: false },
  { value: 'ANCESTOR', label: 'ANCESTOR', disabled: false },
  { value: 'AVAILABLE_FROM', label: 'AVAILABLE_FROM', disabled: false },
  { value: 'BUILD_DEPENDENCY', label: 'BUILD_DEPENDENCY', disabled: false },
  { value: 'BUILD_TOOL', label: 'BUILD_TOOL', disabled: false },
  { value: 'COORDINATED_BY', label: 'COORDINATED_BY', disabled: false },
  { value: 'CONTAINS', label: 'CONTAINS', disabled: false },
  { value: 'CONFIG_OF', label: 'CONFIG_OF', disabled: false },
  { value: 'COPY', label: 'COPY', disabled: false },
  { value: 'DATA_FILE', label: 'DATA_FILE', disabled: false },
  { value: 'DEPENDENCY_MANIFEST', label: 'DEPENDENCY_MANIFEST', disabled: false },
  { value: 'DEPENDS_ON', label: 'DEPENDS_ON', disabled: false },
  { value: 'DESCENDANT', label: 'DESCENDANT', disabled: false },
  { value: 'DESCRIBES', label: 'DESCRIBES', disabled: false },
  { value: 'DEV_DEPENDENCY', label: 'DEV_DEPENDENCY', disabled: false },
  { value: 'DEV_TOOL', label: 'DEV_TOOL', disabled: false },
  { value: 'DISTRIBUTION_ARTIFACT', label: 'DISTRIBUTION_ARTIFACT', disabled: false },
  { value: 'DOCUMENTATION', label: 'DOCUMENTATION', disabled: false },
  { value: 'DOES_NOT_AFFECT', label: 'DOES_NOT_AFFECT', disabled: false },
  { value: 'DYNAMIC_LINK', label: 'DYNAMIC_LINK', disabled: false },
  { value: 'EXAMPLE', label: 'EXAMPLE', disabled: false },
  { value: 'EVIDENCE_FOR', label: 'EVIDENCE_FOR', disabled: false },
  { value: 'EXPANDED_FROM_ARCHIVE', label: 'EXPANDED_FROM_ARCHIVE', disabled: false },
  { value: 'EXPLOIT_CREATED_BY', label: 'EXPLOIT_CREATED_BY', disabled: false },
  { value: 'FILE_ADDED', label: 'FILE_ADDED', disabled: false },
  { value: 'FILE_DELETED', label: 'FILE_DELETED', disabled: false },
  { value: 'FILE_MODIFIED', label: 'FILE_MODIFIED', disabled: false },
  { value: 'FIXED_BY', label: 'FIXED_BY', disabled: false },
  { value: 'FIXED_IN', label: 'FIXED_IN', disabled: false },
  { value: 'FOUND_BY', label: 'FOUND_BY', disabled: false },
  { value: 'GENERATES', label: 'GENERATES', disabled: false },
  { value: 'HAS_ASSESSMENT_FOR', label: 'HAS_ASSESSMENT_FOR', disabled: false },
  { value: 'HAS_ASSOCIATED_VULNERABILITY', label: 'HAS_ASSOCIATED_VULNERABILITY', disabled: false },
  { value: 'HOST_OF', label: 'HOST_OF', disabled: false },
  { value: 'INPUT_OF', label: 'INPUT_OF', disabled: false },
  { value: 'INVOKED_BY', label: 'INVOKED_BY', disabled: false },
  { value: 'METAFILE', label: 'METAFILE', disabled: false },
  { value: 'ON_BEHALF_OF', label: 'ON_BEHALF_OF', disabled: false },
  { value: 'OPTIONAL_COMPONENT', label: 'OPTIONAL_COMPONENT', disabled: false },
  { value: 'OPTIONAL_DEPENDENCY', label: 'OPTIONAL_DEPENDENCY', disabled: false },
  { value: 'OTHER', label: 'OTHER', disabled: false },
  { value: 'OUTPUT_OF', label: 'OUTPUT_OF', disabled: false },
  { value: 'PACKAGES', label: 'PACKAGES', disabled: false },
  { value: 'PATCH', label: 'PATCH', disabled: false },
  { value: 'PREREQUISITE', label: 'PREREQUISITE', disabled: false },
  { value: 'PROVIDED_DEPENDENCY', label: 'PROVIDED_DEPENDENCY', disabled: false },
  { value: 'PUBLISHED_BY', label: 'PUBLISHED_BY', disabled: false },
  { value: 'REPORTED_BY', label: 'REPORTED_BY', disabled: false },
  { value: 'REPUBLISHED_BY', label: 'REPUBLISHED_BY', disabled: false },
  { value: 'REQUIREMENT_FOR', label: 'REQUIREMENT_FOR', disabled: false },
  { value: 'RUNTIME_DEPENDENCY', label: 'RUNTIME_DEPENDENCY', disabled: false },
  { value: 'SPECIFICATION_FOR', label: 'SPECIFICATION_FOR', disabled: false },
  { value: 'STATIC_LINK', label: 'STATIC_LINK', disabled: false },
  { value: 'TEST', label: 'TEST', disabled: false },
  { value: 'TEST_CASE', label: 'TEST_CASE', disabled: false },
  { value: 'TEST_DEPENDENCY', label: 'TEST_DEPENDENCY', disabled: false },
  { value: 'TEST_TOOL', label: 'TEST_TOOL', disabled: false },
  { value: 'TESTED_ON', label: 'TESTED_ON', disabled: false },
  { value: 'TRAINED_ON', label: 'TRAINED_ON', disabled: false },
  { value: 'UNDER_INVESTIGATION_FOR', label: 'UNDER_INVESTIGATION_FOR', disabled: false },
  { value: 'VARIANT', label: 'VARIANT', disabled: false }
]

export const status_options = [
  { value: 'NEW', label: 'New', disabled: false },
  { value: 'IN PROGRESS', label: 'in Progress', disabled: false },
  { value: 'IN REVIEW', label: 'in Review', disabled: false },
  { value: 'REJECTED', label: 'Rejected', disabled: false },
  { value: 'REWORK', label: 'Rework', disabled: false },
  { value: 'APPROVED', label: 'Approved', disabled: false }
]

export const capitalizeFirstWithoutHashes = (_string: string) => {
  let tmp = _string.split('-').join(' ')
  tmp = tmp.split('_').join(' ')
  return tmp.charAt(0).toUpperCase() + tmp.slice(1)
}

export const tcFormEmpty = {
  coverage: 0,
  description: '',
  id: 0,
  relative_path: '',
  repository: '',
  title: ''
}

export const tsFormEmpty = {
  coverage: 0,
  expected_behavior: '',
  id: 0,
  preconditions: '',
  test_description: '',
  title: ''
}

export const srFormEmpty = {
  coverage: 0,
  description: '',
  id: 0,
  title: ''
}

export const jFormEmpty = {
  coverage: 100,
  description: '',
  id: 0
}

export const docFormEmpty = {
  coverage: 100,
  document_type: 'file',
  description: '',
  id: 0,
  section: '',
  offset: 0,
  spdx_relation: '',
  title: '',
  url: ''
}

export const logObject = (obj) => {
  let i
  let k
  console.log('<----------------------------')
  for (i = 0; i < Object.keys(obj).length; i++) {
    k = Object.keys(obj)[i]
    console.log(k + ' : ' + obj[k])
  }
  console.log('---------------------------->')
}
