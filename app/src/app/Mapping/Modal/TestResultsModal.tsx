import _ from 'lodash'
import * as React from 'react'
import * as Constants from '@app/Constants/constants'
import {
  Button,
  Divider,
  Flex,
  FlexItem,
  FormGroup,
  FormSelect,
  FormSelectOption,
  Hint,
  HintBody,
  Label,
  Modal,
  ModalVariant,
  SearchInput,
  Tab,
  TabContent,
  TabContentBody,
  TabTitleText,
  Tabs,
  Text,
  TextInput
} from '@patternfly/react-core'
import { Table, Tbody, Td, Th, Thead, Tr } from '@patternfly/react-table'
import ProcessAutomationIcon from '@patternfly/react-icons/dist/esm/icons/process-automation-icon'
import BugIcon from '@patternfly/react-icons/dist/esm/icons/bug-icon'
import CheckCircleIcon from '@patternfly/react-icons/dist/esm/icons/check-circle-icon'
import CheckIcon from '@patternfly/react-icons/dist/esm/icons/check-icon'
import InfoCircleIcon from '@patternfly/react-icons/dist/esm/icons/info-circle-icon'
import ExclamationCircleIcon from '@patternfly/react-icons/dist/esm/icons/exclamation-circle-icon'
import ExternalLinkSquareAltIcon from '@patternfly/react-icons/dist/esm/icons/external-link-square-alt-icon'
import EyeIcon from '@patternfly/react-icons/dist/esm/icons/eye-icon'
import ImportIcon from '@patternfly/react-icons/dist/esm/icons/import-icon'
import TimesIcon from '@patternfly/react-icons/dist/esm/icons/times-icon'
import { useAuth } from '../../User/AuthProvider'

export interface TestResultsModalProps {
  api
  modalShowState: boolean
  modalRelationData
  parentType
  setModalShowState
  setTestResultDetailsModalShowState
  setCurrentTestResult
}

export const TestResultsModal: React.FunctionComponent<TestResultsModalProps> = ({
  api,
  modalShowState,
  modalRelationData,
  parentType,
  setModalShowState,
  setTestResultDetailsModalShowState,
  setCurrentTestResult
}: TestResultsModalProps) => {
  const auth = useAuth()
  const [isModalOpen, setIsModalOpen] = React.useState(false)
  // eslint-disable-next-line  @typescript-eslint/no-explicit-any
  const [testResults, setTestResults] = React.useState<any[]>([])
  // eslint-disable-next-line  @typescript-eslint/no-explicit-any
  const [externalTestResults, setExternalTestResults] = React.useState<any[]>([])
  // eslint-disable-next-line  @typescript-eslint/no-explicit-any
  const [selectedTestResult, setSelectedTestResult] = React.useState<any>({})
  const [messageValue, setMessageValue] = React.useState('')
  const [searchValue, setSearchValue] = React.useState('')
  const [pluginValue, setPluginValue] = React.useState('')
  const [pluginPresetValue, setPluginPresetValue] = React.useState('')
  const [pluginPresetsValue, setPluginPresetsValue] = React.useState([])
  const [activeTabKey, setActiveTabKey] = React.useState<string | number>(0)
  const [filterKey, setFilterKey] = React.useState('')
  const [filterValue, setFilterValue] = React.useState('')

  const [searchEnabled, setSearchEnabled] = React.useState(true)
  const [externalSearchEnabled, setExternalSearchEnabled] = React.useState(true)

  const columnNames = {
    id: 'ID',
    title: 'Repositories',
    sut: 'SUT',
    result: 'Result',
    date: 'Date',
    bugs_fixes: 'Bugs/Fixes',
    actions: 'Actions'
  }

  const externalColumnNames = {
    id: 'ID',
    project: 'Project',
    ref: 'Ref',
    details: 'Details',
    status: 'Status',
    date: 'Date',
    actions: 'Actions'
  }

  const githubActionsFilterTemplate = {
    actor: null,
    conclusion: null,
    event: null,
    head_sha: null,
    ref: null,
    workflow_id: null,
    job: null,
    page: null,
    per_page: null
  }

  const gitlabCIFilterTemplate = {
    id: null,
    project_id: null,
    stage: null,
    job: null,
    ref: null,
    sha: null,
    source: null,
    status: null,
    updated_after: null,
    updated_before: null
  }

  const kernelCIFilterTemplate = {
    id: null,
    name: null,
    owner: null,
    result: null,
    created_after: null,
    created_before: null,
    data__test_source: null,
    data__test_revision: null,
    data__platform: null,
    data__device: null,
    data__job_id: null,
    data__kernel_revision__tree: null,
    data__kernel_revision__url: null,
    data__kernel_revision__branch: null,
    data__kernel_revision__commit: null,
    data__kernel_revision__commit_tags: null,
    data__arch: null,
    data__config_full: null,
    data__defconfig: null,
    offset: null,
    limit: null
  }

  const LAVAFilterTemplate = {
    id: null,
    page: null,
    project: null,
    ref: null,
    details: null,
    status: null
  }

  const [gitlabCiFilter, setGitlabCIFilter] = React.useState(gitlabCIFilterTemplate)
  const [githubActionsFilter, setGithubActionsFilter] = React.useState(githubActionsFilterTemplate)
  const [kernelCIFilter, setKernelCIFilter] = React.useState(kernelCIFilterTemplate)
  const [LAVAFilter, setLAVAFilter] = React.useState(LAVAFilterTemplate)

  const load_plugin_presets = (_plugin) => {
    let url = Constants.API_BASE_URL + '/mapping/api/test-run-plugins-presets?plugin=' + _plugin
    url += '&api-id=' + api.id

    if (auth.isLogged()) {
      url += '&user-id=' + auth.userId + '&token=' + auth.token
    } else {
      return
    }

    fetch(url)
      .then((res) => res.json())
      .then((data) => {
        setPluginPresetsValue(data)
      })
      .catch((err) => {
        console.log(err.message)
      })
  }

  const handleSelectedTestResult = (testResult) => {
    setSelectedTestResult(testResult)
  }

  const handlePluginChange = (_event, value: string) => {
    setPluginValue(value)
    load_plugin_presets(value)
  }

  const handlePluginPresetChange = (_event, value: string) => {
    setPluginPresetValue(value)
  }

  const handleFilterKeyChange = (_event, value: string) => {
    setFilterKey(value)
  }

  const handleFilterValueChange = (_event, value: string) => {
    setFilterValue(value)
  }

  const onChangeSearchValue = (value) => {
    setSearchValue(value)
  }

  const addFilter = () => {
    if (pluginValue == Constants.kernel_ci_plugin) {
      const tmp = _.cloneDeep(kernelCIFilter)
      tmp[filterKey] = filterValue + '' // cast to string
      setKernelCIFilter(tmp)
    } else if (pluginValue == Constants.gitlab_ci_plugin) {
      const tmp = _.cloneDeep(gitlabCiFilter)
      tmp[filterKey] = filterValue + '' // cast to string
      setGitlabCIFilter(tmp)
    } else if (pluginValue == Constants.github_actions_plugin) {
      const tmp = _.cloneDeep(githubActionsFilter)
      tmp[filterKey] = filterValue + '' // cast to string
      setGithubActionsFilter(tmp)
    } else if (pluginValue == Constants.LAVA_plugin) {
      const tmp = _.cloneDeep(LAVAFilter)
      tmp[filterKey] = filterValue + '' // cast to string
      setLAVAFilter(tmp)
    } else {
      return
    }
    setFilterKey('')
    setFilterValue('')
  }

  const removeFilter = (filterKey) => {
    if (pluginValue == Constants.kernel_ci_plugin) {
      const tmp = _.cloneDeep(kernelCIFilter)
      tmp[filterKey] = null
      setKernelCIFilter(tmp)
    } else if (pluginValue == Constants.gitlab_ci_plugin) {
      const tmp = _.cloneDeep(gitlabCiFilter)
      tmp[filterKey] = null
      setGitlabCIFilter(tmp)
    } else if (pluginValue == Constants.github_actions_plugin) {
      const tmp = _.cloneDeep(githubActionsFilter)
      tmp[filterKey] = null
      setGithubActionsFilter(tmp)
    } else if (pluginValue == Constants.LAVA_plugin) {
      const tmp = _.cloneDeep(LAVAFilter)
      tmp[filterKey] = null
      setLAVAFilter(tmp)
    } else {
      return
    }
  }

  React.useEffect(() => {
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedTestResult])

  const handleModalToggle = () => {
    const new_state = !modalShowState
    setModalShowState(new_state)
    setIsModalOpen(new_state)
    if (new_state == false) {
      setTestResults([])
      setMessageValue('')
    }
  }

  React.useEffect(() => {
    setIsModalOpen(modalShowState)
    if (modalShowState == true) {
      loadTestResults()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [modalShowState])

  React.useEffect(() => {
    loadTestResults()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTabKey])

  const importExternalTestResult = (testResult) => {
    const mapping_to = Constants._TC_ + Constants._M_ + parentType.replaceAll('-', '_')
    const mapping_id = modalRelationData['relation_id']
    setMessageValue('')

    const testRunConfig = {
      environment_vars: '',
      project_id: '',
      git_repo_ref: '',
      id: 0,
      plugin: pluginValue,
      plugin_preset: pluginPresetValue,
      title: pluginValue + ' - ' + pluginPresetValue,
      job: '',
      stage: '',
      trigger_token: '',
      private_token: '',
      url: '',
      workflow_id: ''
    }

    let notes = 'project: ' + testResult.project
    notes += ' - url: ' + testResult.web_url
    notes += ' - created_at: ' + testResult.created_at
    notes += ' - id: ' + testResult.id

    const data = {
      'api-id': api.id,
      status: 'completed',
      result: testResult.status,
      title: pluginValue + ' ' + testResult.project + ' ' + testResult.id,
      notes: notes,
      report: testResult.web_url,
      'test-run-config': testRunConfig,
      'user-id': auth.userId,
      token: auth.token,
      mapped_to_type: mapping_to,
      mapped_to_id: mapping_id
    }

    fetch(Constants.API_BASE_URL + '/mapping/api/test-runs', {
      method: 'POST',
      headers: Constants.JSON_HEADER,
      body: JSON.stringify(data)
    })
      .then((response) => {
        if (response.status !== 200) {
          setMessageValue(response.statusText)
        } else {
          // Move to the BASIL internal test results page
          setActiveTabKey(0)
          setMessageValue('')
        }
      })
      .catch((err) => {
        setMessageValue(err.toString())
      })
  }

  const loadTestResults = () => {
    setMessageValue('')
    setTestResults([]) // clean the list before showing it again
    setSearchEnabled(false)
    const filter = searchValue
    if (api?.permissions.indexOf('r') < 0) {
      return
    }
    if (api == null) {
      return
    }
    const mapping_to = Constants._TC_ + Constants._M_ + parentType.replaceAll('-', '_')
    let url = Constants.API_BASE_URL + '/mapping/api/test-runs'
    url += '?user-id=' + auth.userId
    url += '&token=' + auth.token
    url += '&api-id=' + api.id
    url += '&mapped_to_type=' + mapping_to
    url += '&mapped_to_id=' + modalRelationData['relation_id']
    if (filter != null) {
      url += '&search=' + filter
    }

    fetch(url)
      .then((res) => {
        if (!res.ok) {
          setMessageValue('Error loading Test Results')
          return []
        } else {
          return res.json()
        }
      })
      .then((data) => {
        setTestResults(data)
        setSearchEnabled(true)
      })
      .catch((err) => {
        console.log(err.message)
        setSearchEnabled(true)
      })
  }

  const loadExternalTestResults = () => {
    setMessageValue('')
    setExternalTestResults([]) // clean the list
    setExternalSearchEnabled(false)
    if (api?.permissions.indexOf('r') < 0) {
      return
    }
    if (api == null) {
      return
    }

    const params: string[] = []
    let currentFilter = null
    if (pluginValue == Constants.kernel_ci_plugin) {
      currentFilter = _.cloneDeep(kernelCIFilter)
    } else if (pluginValue == Constants.gitlab_ci_plugin) {
      currentFilter = _.cloneDeep(gitlabCiFilter)
    } else if (pluginValue == Constants.github_actions_plugin) {
      currentFilter = _.cloneDeep(githubActionsFilter)
    } else if (pluginValue == Constants.LAVA_plugin) {
      currentFilter = _.cloneDeep(LAVAFilter)
    }
    if (currentFilter != null) {
      for (let i = 0; i < Object.keys(currentFilter).length; i++) {
        const filterKey: string = Object.keys(currentFilter)[i]
        if (currentFilter[filterKey] != null) {
          params.push(filterKey + '=' + currentFilter[filterKey])
        }
      }
    }

    const mapping_to = Constants._TC_ + Constants._M_ + parentType.replaceAll('-', '_')
    let url = Constants.API_BASE_URL + '/mapping/api/test-runs/external'
    url += '?user-id=' + auth.userId
    url += '&params=' + params.join(';')
    url += '&plugin=' + pluginValue
    url += '&preset=' + pluginPresetValue
    url += '&token=' + auth.token
    url += '&api-id=' + api.id
    url += '&mapped_to_type=' + mapping_to
    url += '&mapped_to_id=' + modalRelationData['relation_id']

    fetch(url)
      .then((res) => {
        if (!res.ok) {
          setMessageValue('Error loading external Test Results')
          return []
        } else {
          return res.json()
        }
      })
      .then((data) => {
        if (Array.isArray(data)) {
          setExternalTestResults(data)
          setExternalSearchEnabled(true)
        } else {
          setMessageValue('Error loading external Test Results')
        }
      })
      .catch((err) => {
        console.log(err.message)
        setMessageValue('Error loading external Test Results: ' + err.message)
        setExternalSearchEnabled(true)
      })
  }

  // Toggle currently active tab
  const handleTabClick = (event: React.MouseEvent | React.KeyboardEvent | MouseEvent, tabIndex: string | number) => {
    setActiveTabKey(tabIndex)
  }

  const requestTestResult = (test_run) => {
    const mapping_to = Constants._TC_ + Constants._M_ + parentType.replaceAll('-', '_')
    const mapping_id = modalRelationData['relation_id']
    setMessageValue('')
    const tmpConf = test_run.config
    tmpConf['from_db'] = 1

    const data = {
      'api-id': api.id,
      title: test_run.title,
      notes: test_run.notes,
      'test-run-config': tmpConf,
      'user-id': auth.userId,
      token: auth.token,
      mapped_to_type: mapping_to,
      mapped_to_id: mapping_id
    }

    fetch(Constants.API_BASE_URL + '/mapping/api/test-runs', {
      method: 'POST',
      headers: Constants.JSON_HEADER,
      body: JSON.stringify(data)
    })
      .then((response) => {
        if (response.status !== 200) {
          setMessageValue(response.statusText)
        } else {
          loadTestResults()
          setMessageValue('')
        }
      })
      .catch((err) => {
        setMessageValue(err.toString())
      })
  }

  const handleTestResultDetailsClick = (testResult) => {
    setCurrentTestResult(testResult)
    setModalShowState(false)
    setTestResultDetailsModalShowState(true)
  }

  const deleteTestResult = (test_run) => {
    const test_run_label = document.getElementById('test-result-delete-label-' + test_run.id)
    if (typeof test_run_label === 'undefined' || test_run_label == null) {
      return
    } else {
      if (test_run_label.innerHTML == 'Delete') {
        test_run_label.innerHTML = 'Confirm'
        return
      }
    }
    const mapping_to = Constants._TC_ + Constants._M_ + parentType.replaceAll('-', '_')
    const mapping_id = modalRelationData['relation_id']
    setMessageValue('')
    const tmpConf = test_run.config
    tmpConf['from_db'] = 1

    const data = {
      'api-id': api.id,
      id: test_run.id,
      'user-id': auth.userId,
      token: auth.token,
      mapped_to_type: mapping_to,
      mapped_to_id: mapping_id
    }

    fetch(Constants.API_BASE_URL + '/mapping/api/test-runs', {
      method: 'DELETE',
      headers: Constants.JSON_HEADER,
      body: JSON.stringify(data)
    })
      .then((response) => {
        if (response.status !== 200) {
          setMessageValue(response.statusText)
        } else {
          loadTestResults()
          setMessageValue('')
        }
      })
      .catch((err) => {
        setMessageValue(err.toString())
      })
  }

  const testResultListRef = React.createRef<HTMLElement>()
  const testResultExternalListRef = React.createRef<HTMLElement>()

  return (
    <React.Fragment>
      <Modal
        width={Constants.MODAL_WIDTH}
        bodyAriaLabel='testResultModal'
        aria-label='test result modal'
        tabIndex={0}
        variant={ModalVariant.large}
        title='Test Results'
        description={``}
        isOpen={isModalOpen}
        onClose={handleModalToggle}
      >
        <div>
          {messageValue ? (
            <>
              <Divider />
              <Hint>
                <HintBody>{messageValue}</HintBody>
              </Hint>
              <br />
            </>
          ) : (
            ''
          )}
        </div>
        <Tabs activeKey={activeTabKey} onSelect={handleTabClick} aria-label='Add a New/Existing Test Specification' role='region'>
          <Tab
            eventKey={0}
            id='tab-btn-test-runs-list'
            title={<TabTitleText>Test Runs</TabTitleText>}
            tabContentId='tabtestResultsList'
            tabContentRef={testResultListRef}
          />
          <Tab
            eventKey={1}
            id='tab-btn-external-test-run-list'
            title={<TabTitleText>External Test Runs</TabTitleText>}
            tabContentId='tabtestResultDetails'
            tabContentRef={testResultExternalListRef}
          />
        </Tabs>
        <TabContent eventKey={0} id='tabContenttestResultList' ref={testResultListRef} hidden={0 !== activeTabKey}>
          <br />
          <Flex>
            <FlexItem>
              <SearchInput
                placeholder='Search'
                value={searchValue}
                onChange={(_event, value) => onChangeSearchValue(value)}
                onClear={() => onChangeSearchValue('')}
                style={{ width: '400px' }}
              />
            </FlexItem>
            <FlexItem>
              <Button
                variant='primary'
                aria-label='Action'
                isDisabled={searchEnabled == false}
                onClick={() => {
                  loadTestResults()
                }}
              >
                Search
              </Button>
            </FlexItem>
          </Flex>
          <br />
          <TabContentBody hasPadding>
            <Table aria-label='BASIL Test Results Table' variant='compact'>
              <Thead>
                <Tr>
                  <Th>{columnNames.id}</Th>
                  <Th>{columnNames.title}</Th>
                  <Th>{columnNames.sut}</Th>
                  <Th>{columnNames.result}</Th>
                  <Th>{columnNames.date}</Th>
                  <Th>{columnNames.bugs_fixes}</Th>
                  <Th>{columnNames.actions}</Th>
                </Tr>
              </Thead>
              <Tbody>
                {typeof testResults == 'object' &&
                  testResults.map((testResult) => (
                    <Tr
                      key={testResult.id}
                      onRowClick={() => handleSelectedTestResult(testResult)}
                      isRowSelected={selectedTestResult === testResult}
                    >
                      <Td dataLabel={columnNames.id}>{testResult.id}</Td>
                      <Td dataLabel={columnNames.title}>{testResult.title}</Td>
                      <Td dataLabel={columnNames.sut}>
                        {(() => {
                          if (testResult.config.plugin == 'tmt') {
                            if (testResult.config.provision_type == 'connect') {
                              return testResult.config.provision_guest
                            } else {
                              return 'container'
                            }
                          } else {
                            return testResult.config.plugin
                          }
                        })()}
                      </Td>
                      <Td dataLabel={columnNames.result}>
                        {(() => {
                          if (testResult?.result == null) {
                            return (
                              <Label icon={<CheckCircleIcon />} color='purple'>
                                {testResult?.status}
                              </Label>
                            )
                          } else {
                            if (testResult?.result == 'pass') {
                              return (
                                <Label icon={<CheckCircleIcon />} color='green'>
                                  {testResult?.result}
                                </Label>
                              )
                            } else if (testResult?.result == 'fail') {
                              return (
                                <Label icon={<ExclamationCircleIcon />} color='red'>
                                  {testResult?.result}
                                </Label>
                              )
                            } else {
                              return (
                                <Label icon={<InfoCircleIcon />} color='orange'>
                                  {testResult?.result}
                                </Label>
                              )
                            }
                          }
                        })()}
                      </Td>
                      <Td dataLabel={columnNames.date}>{testResult.created_at}</Td>
                      <Td dataLabel={columnNames.bugs_fixes}>
                        {testResult.bugs?.length > 0 ? <BugIcon /> : ''}
                        &nbsp;
                        {testResult.fixes?.length > 0 ? <CheckIcon /> : ''}
                      </Td>
                      <Td dataLabel={columnNames.actions}>
                        {(() => {
                          if (api?.permissions.indexOf('w') >= 0) {
                            for (let iPlugin = 0; iPlugin < Constants.test_run_plugins.length; iPlugin++) {
                              if (Constants.test_run_plugins[iPlugin].value == testResult.config.plugin) {
                                if (Constants.test_run_plugins[iPlugin].trigger == true) {
                                  return (
                                    <Button
                                      variant='plain'
                                      aria-label='Action'
                                      onClick={() => {
                                        requestTestResult(testResult)
                                      }}
                                    >
                                      <Flex>
                                        <FlexItem spacer={{ default: 'spacerXs' }}>
                                          <ProcessAutomationIcon />
                                        </FlexItem>
                                        <FlexItem spacer={{ default: 'spacerMd' }}>
                                          <Text>Re-run</Text>
                                        </FlexItem>
                                      </Flex>
                                    </Button>
                                  )
                                }
                              }
                            }
                            return ''
                          } else {
                            return ''
                          }
                        })()}

                        {(() => {
                          if (api?.permissions.indexOf('w') >= 0) {
                            return (
                              <>
                                <Button
                                  variant='plain'
                                  aria-label='Action'
                                  onClick={() => {
                                    deleteTestResult(testResult)
                                  }}
                                >
                                  <Flex>
                                    <FlexItem spacer={{ default: 'spacerXs' }}>
                                      <TimesIcon />
                                    </FlexItem>
                                    <FlexItem spacer={{ default: 'spacerMd' }}>
                                      <Text id={'test-result-delete-label-' + testResult.id}>Delete</Text>
                                    </FlexItem>
                                  </Flex>
                                </Button>
                                <Button
                                  variant='plain'
                                  aria-label='Action'
                                  onClick={() => {
                                    handleTestResultDetailsClick(testResult)
                                  }}
                                >
                                  <Flex>
                                    <FlexItem spacer={{ default: 'spacerXs' }}>
                                      <EyeIcon />
                                    </FlexItem>
                                    <FlexItem spacer={{ default: 'spacerMd' }}>
                                      <Text>Details</Text>
                                    </FlexItem>
                                  </Flex>
                                </Button>
                              </>
                            )
                          } else {
                            return ''
                          }
                        })()}
                      </Td>
                    </Tr>
                  ))}
              </Tbody>
            </Table>
          </TabContentBody>
        </TabContent>

        <TabContent eventKey={1} id='tabContentTestResultExternalList' ref={testResultExternalListRef} hidden={1 !== activeTabKey}>
          <br />
          <Flex>
            <FlexItem>
              <FormGroup label='Plugin' isRequired fieldId={`select-test-run-external-plugin`}>
                <FormSelect
                  value={pluginValue}
                  id={`select-test-run-external-plugin`}
                  onChange={handlePluginChange}
                  aria-label='External Test Run Plugin'
                >
                  <FormSelectOption isDisabled={false} key={0} value={``} label={`Select a Plugin`} />
                  {Constants.test_run_plugins.map((option, index) => (
                    <FormSelectOption isDisabled={!option.fetch} key={index + 1} value={option.value} label={option.label} />
                  ))}
                </FormSelect>
              </FormGroup>
            </FlexItem>
            <FlexItem>
              <FormGroup label='Plugin Presets' isRequired fieldId={`select-test-run-external-plugin-preset`}>
                <FormSelect
                  value={pluginPresetValue}
                  id={`select-test-run-external-plugin-preset`}
                  onChange={handlePluginPresetChange}
                  aria-label='External Test Run Plugin Preset'
                >
                  <FormSelectOption isDisabled={false} key={0} value={``} label={`Select a preset`} />
                  {pluginPresetsValue.map((option, index) => (
                    <FormSelectOption isDisabled={false} key={index + 1} value={option} label={option} />
                  ))}
                </FormSelect>
              </FormGroup>
            </FlexItem>
            <FlexItem>
              <FormGroup label='Filter Key' fieldId={`select-test-run-external-filter-key`}>
                <FormSelect
                  value={filterKey}
                  id={`select-test-run-external-filter-key`}
                  onChange={handleFilterKeyChange}
                  aria-label='Filter Key'
                >
                  <FormSelectOption isDisabled={false} key={0} value={``} label={`Select a Key`} />
                  {(() => {
                    let currentFilter
                    if (pluginValue == Constants.kernel_ci_plugin) {
                      currentFilter = _.cloneDeep(kernelCIFilter)
                    } else if (pluginValue == Constants.gitlab_ci_plugin) {
                      currentFilter = _.cloneDeep(gitlabCiFilter)
                    } else if (pluginValue == Constants.github_actions_plugin) {
                      currentFilter = _.cloneDeep(githubActionsFilter)
                    } else if (pluginValue == Constants.LAVA_plugin) {
                      currentFilter = _.cloneDeep(LAVAFilter)
                    } else {
                      return ''
                    }
                    return Object.keys(currentFilter)
                      .sort()
                      .map((fKey, fIndex) => (
                        <FormSelectOption
                          isDisabled={currentFilter[fKey] != null}
                          key={fIndex + 1}
                          value={fKey}
                          label={fKey.split('__').join(' -> ')}
                        />
                      ))
                  })()}
                </FormSelect>
              </FormGroup>
            </FlexItem>
            <FlexItem>
              <FormGroup label='Filter Value' fieldId={`input-test-run-external-filter-value`}>
                <TextInput
                  id={`input-test-run-external-filter-key`}
                  name={`input-test-run-external-filter-key`}
                  placeholder={`value`}
                  value={filterValue}
                  onChange={(_ev, value) => handleFilterValueChange(_ev, value)}
                />
              </FormGroup>
            </FlexItem>
            <FlexItem>
              <Button
                variant='secondary'
                aria-label='Add filter'
                isDisabled={filterKey == '' || filterValue == ''}
                onClick={() => {
                  addFilter()
                }}
              >
                Add Filter
              </Button>
            </FlexItem>
          </Flex>
          <br />
          <Flex>
            {(() => {
              const validFilters: string[] = []
              let currentFilter
              if (pluginValue == Constants.kernel_ci_plugin) {
                currentFilter = _.cloneDeep(kernelCIFilter)
              } else if (pluginValue == Constants.gitlab_ci_plugin) {
                currentFilter = _.cloneDeep(gitlabCiFilter)
              } else if (pluginValue == Constants.github_actions_plugin) {
                currentFilter = _.cloneDeep(githubActionsFilter)
              } else if (pluginValue == Constants.LAVA_plugin) {
                currentFilter = _.cloneDeep(LAVAFilter)
              } else {
                return ''
              }
              for (let i = 0; i < Object.keys(currentFilter).length; i++) {
                const filterKey: string = Object.keys(currentFilter)[i]
                if (currentFilter[filterKey] != null) {
                  validFilters.push(filterKey)
                }
              }
              return validFilters.map((fKey, fIndex) => (
                <Label key={fIndex} onClose={() => removeFilter(fKey)}>
                  {fKey}: {currentFilter[fKey]}
                </Label>
              ))
            })()}
          </Flex>
          <br />
          <Flex>
            <FlexItem>
              <Button
                variant='primary'
                aria-label='Search'
                isDisabled={pluginValue == '' || pluginPresetValue == '' || externalSearchEnabled == false}
                onClick={() => {
                  loadExternalTestResults()
                }}
              >
                Search
              </Button>
            </FlexItem>
          </Flex>
          <br />
          <TabContentBody hasPadding>
            <Table aria-label='External Test Run table' variant='compact'>
              <Thead>
                <Tr>
                  <Th>#</Th>
                  <Th>{externalColumnNames.id}</Th>
                  <Th>{externalColumnNames.project}</Th>
                  <Th>{externalColumnNames.ref}</Th>
                  <Th>{externalColumnNames.details}</Th>
                  <Th>{externalColumnNames.status}</Th>
                  <Th>{externalColumnNames.date}</Th>
                </Tr>
              </Thead>
              <Tbody>
                {typeof externalTestResults == 'object' &&
                  externalTestResults.map((testResult, testResultIndex) => (
                    <Tr key={testResult.id}>
                      <Td dataLabel='index'>{testResultIndex + 1}</Td>
                      <Td dataLabel={externalColumnNames.id}>
                        <Button
                          onClick={() => {
                            window.open(testResult.web_url, '_blank')?.focus()
                          }}
                          variant='link'
                          icon={<ExternalLinkSquareAltIcon />}
                          iconPosition='right'
                        >
                          {testResult.id}
                        </Button>
                      </Td>
                      <Td dataLabel={externalColumnNames.project}>{testResult?.project || ''}</Td>
                      <Td dataLabel={externalColumnNames.ref}>{testResult?.ref || ''}</Td>
                      <Td dataLabel={externalColumnNames.ref}>{testResult?.details || ''}</Td>
                      <Td dataLabel={externalColumnNames.status}>
                        {(() => {
                          if (['fail'].indexOf(testResult?.status) > -1) {
                            return (
                              <Label icon={<CheckCircleIcon />} color='red'>
                                {testResult?.status}
                              </Label>
                            )
                          } else if (['pass'].indexOf(testResult?.status) > -1) {
                            return (
                              <Label icon={<CheckCircleIcon />} color='green'>
                                {testResult?.status}
                              </Label>
                            )
                          } else {
                            return (
                              <Label icon={<ExclamationCircleIcon />} color='orange'>
                                {testResult?.status}
                              </Label>
                            )
                          }
                        })()}
                      </Td>
                      <Td dataLabel={externalColumnNames.date}>{testResult?.created_at || ''}</Td>

                      <Td dataLabel={externalColumnNames.actions}>
                        {api?.permissions.indexOf('w') >= 0 ? (
                          <>
                            <Button
                              variant='plain'
                              aria-label='Action'
                              onClick={() => {
                                importExternalTestResult(testResult)
                              }}
                            >
                              <ImportIcon /> <Text id={'test-run-external-import-label-' + testResult.id}>Import</Text>
                            </Button>
                          </>
                        ) : (
                          ''
                        )}
                      </Td>
                    </Tr>
                  ))}
              </Tbody>
            </Table>
          </TabContentBody>
        </TabContent>
      </Modal>
    </React.Fragment>
  )
}
