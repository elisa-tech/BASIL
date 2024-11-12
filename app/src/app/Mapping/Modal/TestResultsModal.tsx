import * as React from 'react'
import * as Constants from '../../Constants/constants'
import {
  Button,
  CodeBlock,
  CodeBlockCode,
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
  TextContent,
  TextInput,
  TextVariants
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
  const [selectedExternalTestResult, setSelectedExternalTestResult] = React.useState<any>({})
  const [messageValue, setMessageValue] = React.useState('')
  const [searchValue, setSearchValue] = React.useState('')
  const [pluginValue, setPluginValue] = React.useState('')
  const [pluginPresetValue, setPluginPresetValue] = React.useState('')
  const [pluginRefValue, setPluginRefValue] = React.useState('')
  const [pluginParamsValue, setPluginParamsValue] = React.useState('')
  const [pluginPresetsValue, setPluginPresetsValue] = React.useState([])
  const [activeTabKey, setActiveTabKey] = React.useState<string | number>(0)

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
    status: 'Status',
    date: 'Date',
    actions: 'Actions'
  }

  const load_plugin_presets = (_plugin) => {
    let url = Constants.API_BASE_URL + '/mapping/api/test-run-plugin-presets?plugin=' + _plugin
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

  const handlePluginRefValueChange = (_event, value: string) => {
    setPluginRefValue(value)
  }

  const handlePluginParamsValueChange = (_event, value: string) => {
    setPluginParamsValue(value)
  }

  const onChangeSearchValue = (value) => {
    setSearchValue(value)
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
      headers: {
        Accept: 'application/json',
        'Content-Type': 'application/json'
      },
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
    let filter = searchValue
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
      .then((res) => res.json())
      .then((data) => {
        setTestResults(data)
      })
      .catch((err) => {
        console.log(err.message)
      })
  }

  const loadExternalTestResults = () => {
    if (api?.permissions.indexOf('r') < 0) {
      return
    }
    if (api == null) {
      return
    }
    const mapping_to = Constants._TC_ + Constants._M_ + parentType.replaceAll('-', '_')
    let url = Constants.API_BASE_URL + '/mapping/api/test-runs/external'
    url += '?user-id=' + auth.userId
    url += '&params=' + pluginParamsValue
    url += '&plugin=' + pluginValue
    url += '&preset=' + pluginPresetValue
    url += '&ref=' + pluginRefValue
    url += '&token=' + auth.token
    url += '&api-id=' + api.id
    url += '&mapped_to_type=' + mapping_to
    url += '&mapped_to_id=' + modalRelationData['relation_id']

    fetch(url)
      .then((res) => res.json())
      .then((data) => {
        setExternalTestResults(data)
      })
      .catch((err) => {
        console.log(err.message)
      })
  }

  // Toggle currently active tab
  const handleTabClick = (event: React.MouseEvent | React.KeyboardEvent | MouseEvent, tabIndex: string | number) => {
    setActiveTabKey(tabIndex)
  }

  const getArtifactUrl = (artifact) => {
    let url = Constants.API_BASE_URL + '/mapping/api/test-run/artifacts'
    url += '?api-id=' + api.id
    url += '&user-id=' + auth.userId
    url += '&token=' + auth.token
    url += '&id=' + selectedTestResult.id
    url += '&artifact=' + artifact
    return url
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
      headers: {
        Accept: 'application/json',
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(data)
    })
      .then((response) => {
        if (response.status !== 200) {
          setMessageValue(response.statusText)
        } else {
          handleModalToggle()
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
      headers: {
        Accept: 'application/json',
        'Content-Type': 'application/json'
      },
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
        bodyAriaLabel='testResultModal'
        aria-label='test result modal'
        tabIndex={0}
        variant={ModalVariant.large}
        title='Test Result'
        description={``}
        isOpen={isModalOpen}
        onClose={handleModalToggle}
      >
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
                  {testResults &&
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
                          {api?.permissions.indexOf('w') >= 0 ? (
                            <>
                              <Button
                                variant='plain'
                                aria-label='Action'
                                onClick={() => {
                                  requestTestResult(testResult)
                                }}
                              >
                                <ProcessAutomationIcon /> Re-run
                              </Button>
                              <Button
                                variant='plain'
                                aria-label='Action'
                                onClick={() => {
                                  deleteTestResult(testResult)
                                }}
                              >
                                <TimesIcon /> <Text id={'test-result-delete-label-' + testResult.id}>Delete</Text>
                              </Button>
                              <Button
                                variant='plain'
                                aria-label='Action'
                                onClick={() => {
                                  handleTestResultDetailsClick(testResult)
                                }}
                              >
                                <EyeIcon /> Details
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
                      <FormSelectOption isDisabled={option.value == 'tmt'} key={index + 1} value={option.value} label={option.label} />
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
                <FormGroup label='Ref' fieldId={`input-test-run-external-plugin-ref`}>
                  <TextInput
                    id={`input-test-run-external-plugin-ref`}
                    name={`input-test-run-external-plugin-ref`}
                    value={pluginRefValue || ''}
                    onChange={(_ev, value) => handlePluginRefValueChange(_ev, value)}
                  />
                </FormGroup>
              </FlexItem>
              <FlexItem>
                <FormGroup label='Parameters' fieldId={`input-test-run-external-plugin-params`}>
                  <TextInput
                    id={`input-test-run-external-plugin-params`}
                    name={`input-test-run-external-plugin-params`}
                    placeholder={`example: param1=value1;param2=value2`}
                    value={pluginParamsValue || ''}
                    onChange={(_ev, value) => handlePluginParamsValueChange(_ev, value)}
                  />
                </FormGroup>
              </FlexItem>
              <FlexItem>
                <Button
                  variant='primary'
                  aria-label='Action'
                  isDisabled={pluginValue == '' || pluginPresetValue == ''}
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
                    <Th>{externalColumnNames.id}</Th>
                    <Th>{externalColumnNames.project}</Th>
                    <Th>{externalColumnNames.ref}</Th>
                    <Th>{externalColumnNames.status}</Th>
                    <Th>{externalColumnNames.date}</Th>
                  </Tr>
                </Thead>
                <Tbody>
                  {externalTestResults &&
                    externalTestResults.map((testResult) => (
                      <Tr key={testResult.id}>
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
                        <Td dataLabel={externalColumnNames.project}>{testResult.project}</Td>
                        <Td dataLabel={externalColumnNames.ref}>{testResult.ref}</Td>
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
                        <Td dataLabel={externalColumnNames.date}>{testResult.created_at}</Td>

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
        </div>
      </Modal>
    </React.Fragment>
  )
}
