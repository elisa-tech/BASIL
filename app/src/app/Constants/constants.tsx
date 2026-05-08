export const API_BASE_URL = 'http://localhost:5000'
export const BASIL_VERSION = '1.8.12'
export const TESTING_FARM_COMPOSES_URL = 'https://api.dev.testing-farm.io/v0.1/composes'
export const force_reload = true

const GITHUB_REPO_RELEASES_URL = 'https://api.github.com/repos/elisa-tech/BASIL/releases/latest'
const COOKIE_BASIL_LASTEST_RELEASE_VERSION = 'basil-latest-release-version'

export const _A = 'api'
export const _D = 'document'
export const _Ds = 'documents'
export const _J = 'justification'
export const _Js = 'justifications'
export const _M_ = '_mapping_'
export const _DV = 'dynamic-view'
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

export const NO_SECTION_SELECTED_MESSAGE = 'No section selected, please select one from the `Mapping Section` tab.'
export const UNVALID_REF_DOCUMENT_SECTION_MESSAGE =
  'Section of the Reference Document is mandatory. Open the Mapping Section tab to select it.'
export const MODAL_WIDTH = '80%'

export const REFRESH_INTERVAL = 60 // seconds
export const DEFAULT_VIEW = _SRs
export const DEFAULT_PER_PAGE = 10
export type validate = 'success' | 'warning' | 'error' | 'error2' | 'default' | 'indeterminate' | 'undefined'

export const PATH_SEP = '/'
export const API_USER_ENDPOINT = '/user'
export const API_USER_APIS_ENDPOINT = '/user/apis'
export const API_USER_PERMISSIONS_API_ENDPOINT = '/user/permissions/api'
export const API_USER_PERMISSIONS_API_COPY_ENDPOINT = '/user/permissions/copy'
export const API_USER_FILES_ENDPOINT = '/user/files'
export const API_USER_FILES_FOLDER_ENDPOINT = '/user/files/folder'
export const API_USER_FILES_CONTENT_ENDPOINT = '/user/files/content'
export const API_USER_RESET_PASSWORD_ENDPOINT = '/user/reset-password'
export const API_USER_SIGNIN_ENDPOINT = '/user/signin'
export const API_ADMIN_RESET_USER_PASSWORD_ENDPOINT = '/admin/reset-user-password'
export const API_SW_REQUIREMENT_IMPORT_ENDPOINT = '/import/sw-requirements'
export const API_TEST_CASE_IMPORT_GENERATE_JSON_ENDPOINT = '/import/test-cases-generate-json'
export const API_TEST_CASE_IMPORT_ENDPOINT = '/import/test-cases'
export const API_REQUEST_WRITE_PERMISSION_ENDPOINT = '/apis/write-permission-request'
export const API_AI_HEALTH_CHECK_ENDPOINT = '/ai/health-check'
export const API_AI_SUGGEST_SW_REQ_METADATA_ENDPOINT = '/ai/suggest/sw-requirement/metadata'
export const API_AI_SUGGEST_TEST_CASE_IMPLEMENTATION_ENDPOINT = '/ai/suggest/test-case/implementation'
export const API_AI_SUGGEST_TEST_CASE_METADATA_ENDPOINT = '/ai/suggest/test-case/metadata'
export const API_AI_SUGGEST_TEST_SPEC_METADATA_ENDPOINT = '/ai/suggest/test-specification/metadata'
export const API_SPDX_API_EXPORT_ENDPOINT = '/spdx/apis'
export const API_HTML_API_EXPORT_ENDPOINT = '/html/apis'
export const API_SPDX_API_EXPORT_DOWNLOAD_ENDPOINT = '/spdx/apis/export-download'
export const API_HTML_API_EXPORT_DOWNLOAD_ENDPOINT = '/html/apis/export-download'
export const API_CUSTOM_ACTIONS_ENDPOINT = '/custom-actions'
export const API_TEST_RUN_LOG_ENDPOINT = '/mapping/api/test-run/log'
export const API_TEST_RUN_ARTIFACTS_ENDPOINT = '/mapping/api/test-run/artifacts'
export const API_TEST_RUN_ARTIFACT_CONTENT_ENDPOINT = '/mapping/api/test-run/artifact-content'
export const API_TEST_CASE_LOCAL_FILE_IMPLEMENTATION_ENDPOINT = '/test-cases/local-file-implementation'

/** Align with api/api_response.py: success responses are 200 OK or 201 CREATED (and other 2xx). */
export const HTTP_OK = 200
export const HTTP_CREATED = 201
export const isHttpSuccessStatus = (status: number): boolean => Number.isFinite(status) && status >= 200 && status < 300

/** Base path for listing unmapped work items: `/mapping/api/{specifications|test-cases|...}` */
export const API_MAPPING_API_BASE = `${PATH_SEP}mapping${PATH_SEP}api`
export const buildMappingApiResourcePath = (resourceSuffix: string): string => `${API_MAPPING_API_BASE}/${resourceSuffix}`

/** Nested mapping CRUD under a parent work item, e.g. `/mapping/sw-requirement/sw-requirements` */
export const buildMappingParentWorkItemsPath = (parentKebabType: string, workItemsPluralSegment: string): string =>
  `${PATH_SEP}mapping${PATH_SEP}${parentKebabType}${PATH_SEP}${workItemsPluralSegment}`

/** DELETE mapping row: `/mapping/{parentType}/{workItemType}s` */
export const buildMappingDeletePath = (parentType: string, workItemType: string): string =>
  `${PATH_SEP}mapping${PATH_SEP}${parentType}${PATH_SEP}${workItemType}s`

/** Fork: `/fork/{parentType}/{workItemType}` */
export const buildForkPath = (parentType: string, workItemType: string): string =>
  `${PATH_SEP}fork${PATH_SEP}${parentType}${PATH_SEP}${workItemType}`

export const API_ALERT_ENDPOINT = '/alert'
export const API_USER_LOGIN_ENDPOINT = '/user/login'
export const API_USER_NOTIFICATIONS_ENDPOINT = '/user/notifications'
export const API_USER_ROLE_ENDPOINT = '/user/role'
export const API_USER_ENABLE_ENDPOINT = '/user/enable'
export const API_USER_SSH_KEY_ENDPOINT = '/user/ssh-key'
export const API_LIBRARIES_ENDPOINT = '/libraries'
export const API_APIS_ENDPOINT = '/apis'
export const API_APIS_HISTORY_ENDPOINT = '/apis/history'
export const API_APIS_NEW_VERSION_ENDPOINT = '/apis/new-version'
export const API_APIS_CHECK_SPECIFICATION_ENDPOINT = '/apis/check-specification'
export const API_APIS_FIX_SPECIFICATION_WARNINGS_ENDPOINT = '/apis/fix-specification-warnings'
export const API_API_SPECIFICATIONS_ENDPOINT = '/api-specifications'
export const API_REMOTE_DOCUMENTS_ENDPOINT = '/remote-documents'
export const API_COMMENTS_ENDPOINT = '/comments'
export const API_MAPPING_HISTORY_ENDPOINT = '/mapping/history'
export const API_MAPPING_USAGE_ENDPOINT = '/mapping/usage'
export const API_MAPPING_API_LAST_COVERAGE_ENDPOINT = '/mapping/api/last-coverage'
export const API_TEST_RUN_CONFIGS_ENDPOINT = '/mapping/api/test-run-configs'
export const API_TEST_RUNS_ENDPOINT = '/mapping/api/test-runs'
export const API_TEST_RUNS_EXTERNAL_ENDPOINT = '/mapping/api/test-runs/external'
export const API_TEST_RUN_PLUGINS_PRESETS_ENDPOINT = '/mapping/api/test-run-plugins-presets'
export const API_JUSTIFICATIONS_ROOT_ENDPOINT = '/justifications'
export const API_TEST_SPECIFICATIONS_ROOT_ENDPOINT = '/test-specifications'
export const API_SW_REQUIREMENTS_ROOT_ENDPOINT = '/sw-requirements'
export const API_TEST_CASES_ROOT_ENDPOINT = '/test-cases'
export const API_DOCUMENTS_ROOT_ENDPOINT = '/documents'
export const API_VERSION_ENDPOINT = '/version'
export const API_TRACEABILITY_SCANNER_SETTINGS_ENDPOINT = '/traceability-scanner/settings'
export const API_TRACEABILITY_SCANNER_SCAN_ENDPOINT = '/traceability-scanner/scan'
export const API_TRACEABILITY_SCANNER_LOGS_ENDPOINT = '/traceability-scanner/logs'
export const API_ADMIN_TEST_RUN_PLUGINS_PRESETS_ENDPOINT = '/admin/test-run-plugins-presets'
export const API_ADMIN_SETTINGS_ENDPOINT = '/admin/settings'

/** GET `/{type}s` for top-level work item collections (e.g. `sw-requirement` -> `/sw-requirements`). */
export const buildWorkItemRootListPath = (workItemKebabSingular: string): string => `${PATH_SEP}${workItemKebabSingular}s`

export const FORM_COMPLETION_LABEL = 'Completion (how much of the parent is covered by this work item) [0-100]:'

export const JSON_HEADER = {
  Accept: 'application/json',
  'Content-Type': 'application/json'
}

export const getMappingTableName = (workItemType: string, parentType: string) => {
  let parent_table = workItemType + _M_ + parentType
  parent_table = parent_table.replaceAll('-', '_')
  return parent_table
}

export const getSearchParamsDict = () => {
  //Return a dictionary with key value based on search params querystring
  let ret = {}
  const search = window.location.search
  const search_params = new URLSearchParams(search)
  const params_keys = Array.from(search_params.keys())
  const params_values = Array.from(search_params.values())
  for (let i = 0; i < params_keys.length; i++) {
    ret[params_keys[i]] = params_values[i]
  }
  return ret
}

export const validateCoverage = (coverage, setValidatedCoverage) => {
  if (coverage === '') {
    setValidatedCoverage('error')
  } else if (/^\d+$/.test(coverage)) {
    if (coverage >= 0 && coverage <= 100) {
      setValidatedCoverage('success')
    } else {
      setValidatedCoverage('error')
    }
  } else {
    setValidatedCoverage('error')
  }
}

export const getResponseErrorMessage = (status, status_text, message) => {
  let ret: string = status_text
  ret += '(' + status.toString() + '): '
  ret += message
  return ret
}

export const document_type = [
  { value: 'file', label: 'file', disabled: false },
  { value: 'text', label: 'text', disabled: false }
]

export const provision_type = [
  { value: '', label: '', disabled: false },
  { value: 'container', label: 'Container', disabled: false },
  { value: 'connect', label: 'SSH', disabled: false }
]

export const testing_farm_archs = [
  { value: 'x86_64', label: 'x86_64', diasbled: false },
  { value: 'aarch64', label: 'aarch64', diasbled: false },
  { value: 's390x', label: 's390x', diasbled: false },
  { value: 'ppc64le', label: 'ppc64le', diasbled: false }
]

export const gitlab_ci_plugin = 'gitlab_ci'
export const github_actions_plugin = 'github_actions'
export const kernel_ci_plugin = 'KernelCI'
export const LAVA_plugin = 'LAVA'
export const testing_farm_plugin = 'testing_farm'
export const tmt_plugin = 'tmt'

export const test_run_plugins = [
  { value: tmt_plugin, label: 'tmt', disabled: false, trigger: true, fetch: false },
  { value: testing_farm_plugin, label: 'Testing Farm', disabled: false, trigger: true, fetch: false },
  { value: github_actions_plugin, label: 'github actions', disabled: false, trigger: true, fetch: true },
  { value: gitlab_ci_plugin, label: 'gitlab ci', disabled: false, trigger: true, fetch: true },
  { value: kernel_ci_plugin, label: 'KernelCI', disabled: false, trigger: false, fetch: true },
  { value: LAVA_plugin, label: 'LAVA', disabled: false, trigger: true, fetch: true }
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

export const SESSION_EXPIRED_MESSAGE = 'Session expired, please login in again.'

export const getFilenameFromFilepath = (filepath: string) => {
  return filepath.split(PATH_SEP).pop()
}

export const loadUserFiles = (_auth, _setFiles, _filter = '', _path = '', _recursive = false) => {
  if (!_auth.isLogged()) {
    return
  }
  let url = API_BASE_URL + API_USER_FILES_ENDPOINT
  url += '?user-id=' + _auth.userId
  url += '&token=' + _auth.token
  url += '&filter=' + (_filter ? _filter : '')
  if (_path) {
    url += '&path=' + encodeURIComponent(_path)
  }
  if (_recursive) {
    url += '&recursive=true'
  }
  fetch(url, {
    method: 'GET',
    headers: JSON_HEADER
  })
    .then((res) => res.json())
    .then((data) => {
      for (let i = 0; i < data.length; i++) {
        data[i]['filename'] = data[i]['name'] || getFilenameFromFilepath(data[i]['filepath'])
      }
      _setFiles(data)
    })
    .catch((err) => {
      console.log(err.message)
    })
}

export const createUserFolder = (_auth, _foldername, _onSuccess, _onError) => {
  const data = {
    'user-id': _auth.userId,
    token: _auth.token,
    foldername: _foldername
  }
  fetch(API_BASE_URL + API_USER_FILES_FOLDER_ENDPOINT, {
    method: 'POST',
    headers: JSON_HEADER,
    body: JSON.stringify(data)
  })
    .then((response) => {
      if (!isHttpSuccessStatus(response.status)) {
        response
          .json()
          .then((body) => _onError(body?.message || response.statusText))
          .catch(() => _onError(response.statusText))
      } else {
        _onSuccess()
      }
    })
    .catch((err) => _onError(err.toString()))
}

export const moveUserFile = (_auth, _source, _destination, _onSuccess, _onError) => {
  const data = {
    'user-id': _auth.userId,
    token: _auth.token,
    source: _source,
    destination: _destination
  }
  fetch(API_BASE_URL + API_USER_FILES_ENDPOINT, {
    method: 'PUT',
    headers: JSON_HEADER,
    body: JSON.stringify(data)
  })
    .then((response) => {
      if (!isHttpSuccessStatus(response.status)) {
        response
          .json()
          .then((body) => _onError(body?.message || response.statusText))
          .catch(() => _onError(response.statusText))
      } else {
        _onSuccess()
      }
    })
    .catch((err) => _onError(err.toString()))
}

export const deleteUserFile = (_auth, _filename, _onSuccess, _onError) => {
  const data = {
    'user-id': _auth.userId,
    token: _auth.token,
    filename: _filename
  }
  fetch(API_BASE_URL + API_USER_FILES_ENDPOINT, {
    method: 'DELETE',
    headers: JSON_HEADER,
    body: JSON.stringify(data)
  })
    .then((response) => {
      if (!isHttpSuccessStatus(response.status)) {
        response
          .json()
          .then((body) => _onError(body?.message || response.statusText))
          .catch(() => _onError(response.statusText))
      } else {
        _onSuccess()
      }
    })
    .catch((err) => _onError(err.toString()))
}

export const loadFileContent = (_auth, _filename, _setMessage, _setContent) => {
  if (!_filename) {
    return
  }

  if (_filename == '') {
    return
  }

  _setMessage('')
  _setContent('')

  let url = API_BASE_URL + API_USER_FILES_CONTENT_ENDPOINT
  url += '?user-id=' + _auth.userId
  url += '&token=' + _auth.token
  url += '&filename=' + encodeURIComponent(_filename)
  fetch(url)
    .then((res) => {
      if (!res.ok) {
        _setMessage('Error loading content of ' + _filename)
        return ''
      } else {
        return res.json()
      }
    })
    .then((data) => {
      _setContent(data['filecontent'])
    })
    .catch((err) => {
      _setMessage(err.message)
      console.log(err.message)
    })
}

export async function checkEndpoint(urlToCheck, setIsUrlAvailable) {
  try {
    const response = await fetch(urlToCheck)
    setIsUrlAvailable(response.ok) // true if status is 2xx
  } catch (error) {
    console.error('Error checking endpoint:', error)
    setIsUrlAvailable(false)
  }
}

export const percentageStringFormat = (x: number): string => {
  return new Intl.NumberFormat('en-US', {
    minimumFractionDigits: 1,
    maximumFractionDigits: 1
  }).format(x)
}

export const capitalizeFirstWithoutHashes = (_string: string) => {
  let tmp = _string.split('-').join(' ')
  tmp = tmp.split('_').join(' ')
  return tmp.charAt(0).toUpperCase() + tmp.slice(1)
}

export const extend_config_with_plugin_vars = (config) => {
  if (Object.keys(config).indexOf('plugin_vars') < 0) {
    return config
  }
  const vars_str = config['plugin_vars']
  const kv = vars_str.split(';')
  let tmp
  for (let i = 0; i < kv.length; i++) {
    tmp = kv[i].split('=')
    if (tmp.length == 2) {
      config[tmp[0].trim()] = tmp[1].trim()
    }
  }
  return config
}

export const get_config_plugin_var = (_config, _varname) => {
  const tmp_config = extend_config_with_plugin_vars(_config)
  if (Object.keys(tmp_config).indexOf(_varname) > -1) {
    return tmp_config[_varname]
  }
  return ''
}

export const getSelectionOffset = () => {
  // Get current selection and return the offset indide the parent element
  const selection = window.getSelection()
  let startOffset = -1
  if (selection) {
    if (!selection.isCollapsed) {
      const range = selection.getRangeAt(0)
      startOffset = range.startOffset
    }
  }
  return startOffset
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

export const getLimitedText = (_text, _length) => {
  if (_text == undefined) {
    return ''
  }
  if (_length == 0) {
    return _text
  }
  if (_text.length > _length) {
    return _text.substr(0, _length) + '...'
  }
  return _text
}

export const _trim = (_var) => {
  try {
    if (_var == undefined) {
      return ''
    } else {
      return String(_var).trim()
    }
  } catch {
    return ''
  }
}

export const fallbackCopyTextToClipboard = (text) => {
  const textArea = document.createElement('textarea')
  textArea.value = text

  textArea.style.position = 'fixed'
  textArea.style.top = '0px'
  textArea.style.left = '0px'
  textArea.style.opacity = '0'
  textArea.style.pointerEvents = 'none'
  textArea.style.zIndex = '-1'

  document.body.appendChild(textArea)
  textArea.focus()
  textArea.select()

  try {
    const successful = document.execCommand('copy')
    console.log('Fallback: Copying was ' + (successful ? 'successful' : 'unsuccessful'))
  } catch (err) {
    console.error('Fallback: Copy command failed', err)
  }

  document.body.removeChild(textArea)
}

export const isNotEmptyString = (_input) => {
  if (typeof _input === 'string' && _input.trim() !== '') {
    return true
  }
  return false
}

export const removeExtension = (filename: string, extension: string) => {
  return filename.endsWith(extension) ? filename.slice(0, -extension.length) : filename
}

export const isValidId = (id_str: string) => {
  return /^\d+$/.test(id_str) && Number(id_str) > 0 && Number.isSafeInteger(Number(id_str))
}

export const setCookie = (name, value, days) => {
  const date = new Date()
  date.setTime(date.getTime() + days * 24 * 60 * 60 * 1000)
  const expires = 'expires=' + date.toUTCString()
  document.cookie = `${name}=${value}; ${expires}; path=/`
}

export const getCookieValue = (name) => {
  const cookies = document.cookie.split(';')

  for (let cookie of cookies) {
    const [key, value] = cookie.trim().split('=')
    if (key === name) {
      return decodeURIComponent(value)
    }
  }

  return undefined
}

// Compare semantic versions (e.g. "1.8.0" < "1.9.0")
export const isNewerVersion = (latest: string = '', current: string = '') => {
  const latestParts = latest.split('.').map(Number)
  const currentParts = current.split('.').map(Number)

  for (let i = 0; i < latestParts.length; i++) {
    if ((latestParts[i] || 0) > (currentParts[i] || 0)) return true
    if ((latestParts[i] || 0) < (currentParts[i] || 0)) return false
  }
  return false
}

export const checkNewVersionAvailable = (setNewVersionAvailable) => {
  const value = getCookieValue(COOKIE_BASIL_LASTEST_RELEASE_VERSION)

  if (value !== undefined) {
    setNewVersionAvailable(isNewerVersion(value, BASIL_VERSION))
    return
  } else {
    fetch(GITHUB_REPO_RELEASES_URL)
      .then((res) => {
        if (!res.ok) {
          setNewVersionAvailable(false)
          throw new Error('Unable to read last release from github')
        } else {
          return res.json()
        }
      })
      .then((data) => {
        if (!data || typeof data !== 'object' || !data.tag_name) {
          throw new Error('`tag_name` not found in GitHub response')
        }
        const tag = data.tag_name.replace(/^v/, '') // strip "v" if release is like "v1.9.0"
        setCookie(COOKIE_BASIL_LASTEST_RELEASE_VERSION, tag, 1) // expires in 1 day
        setNewVersionAvailable(isNewerVersion(tag, BASIL_VERSION))
      })
      .catch((err) => {
        console.error('ERROR: ' + err.message)
        setNewVersionAvailable(false)
      })
  }
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

export const normalizeKeys = (obj: any) => {
  /* Normalize object keys by replacing _ with - */
  const normalizedObj = {}
  for (const key in obj) {
    normalizedObj[key.replace('_', '-')] = obj[key]
  }
  return normalizedObj
}

export const hasPermission = (permissions: string, permission: string): boolean => {
  /*  Check if the user has the given permission */
  if (permissions === undefined || permissions === null) {
    return false
  }
  if (permission === undefined || permission === null) {
    return false
  }
  if (permission.length !== 1) {
    return false
  }
  if (permissions.length === 0) {
    return false
  }
  return permissions.includes(permission)
}

export const hasReadPermission = (api: any): boolean => {
  if (api == undefined || api == null) {
    return false
  }
  if (api.permissions == undefined || api.permissions == null) {
    return false
  }
  return hasPermission(api.permissions, 'r')
}

export const hasWritePermission = (api: any): boolean => {
  if (api == undefined || api == null) {
    return false
  }
  if (api.permissions == undefined || api.permissions == null) {
    return false
  }
  return hasPermission(api.permissions, 'w')
}

export const hasEditPermission = (api: any): boolean => {
  if (api == undefined || api == null) {
    return false
  }
  if (api.permissions == undefined || api.permissions == null) {
    return false
  }
  return hasPermission(api.permissions, 'e')
}

export const hasManagePermission = (api: any): boolean => {
  if (api == undefined || api == null) {
    return false
  }
  if (api.permissions == undefined || api.permissions == null) {
    return false
  }
  return hasPermission(api.permissions, 'm')
}

export const hasDeletePermission = (api: any): boolean => {
  if (api == undefined || api == null) {
    return false
  }
  if (api.permissions == undefined || api.permissions == null) {
    return false
  }
  return hasPermission(api.permissions, 'd')
}
