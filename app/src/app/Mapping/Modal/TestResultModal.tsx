import * as React from 'react'
import * as Constants from '../../Constants/constants'
import {
  Button,
  CodeBlock,
  CodeBlockCode,
  Modal,
  ModalVariant,
  SearchInput,
  Tab,
  TabContent,
  TabContentBody,
  TabTitleText,
  Tabs
} from '@patternfly/react-core'
import { Divider, Hint, HintBody, Text, TextContent, TextVariants } from '@patternfly/react-core'
import { Table, Tbody, Td, Th, Thead, Tr } from '@patternfly/react-table'
import ProcessAutomationIcon from '@patternfly/react-icons/dist/esm/icons/process-automation-icon'
import BugIcon from '@patternfly/react-icons/dist/esm/icons/bug-icon'
import { TestRunBugForm } from '../Form/TestRunBugForm'
import { useAuth } from '../../User/AuthProvider'

export interface TestResultModalProps {
  api
  modalShowState: boolean
  modalRelationData
  parentType
  setModalShowState
}

export const TestResultModal: React.FunctionComponent<TestResultModalProps> = ({
  api,
  modalShowState,
  modalRelationData,
  parentType,
  setModalShowState
}: TestResultModalProps) => {
  const auth = useAuth()
  const [isModalOpen, setIsModalOpen] = React.useState(false)
  // eslint-disable-next-line  @typescript-eslint/no-explicit-any
  const [testResults, setTestResults] = React.useState<any[]>([])
  // eslint-disable-next-line  @typescript-eslint/no-explicit-any
  const [selectedTestResult, setSelectedTestResult] = React.useState<any>({})
  const [selectedTestResultArtifacts, setSelectedTestResultArtifacts] = React.useState([])
  const [selectedTestResultLogExec, setSelectedTestResultLogExec] = React.useState('')
  const [selectedTestResultLogTxt, setSelectedTestResultLogTxt] = React.useState('')
  const [selectedTestResultLogStd, setSelectedTestResultLogStd] = React.useState('')
  const [messageValue, setMessageValue] = React.useState('')
  const [searchValue, setSearchValue] = React.useState('')

  /*
  interface TestRunConfig {
    id: number
    title: string
    git_repo_ref: string | null
    provision_type: string | null
    provision_guest: string | null
    provision_guest_port: string | null
    ssh_key: string | null
    created_at: string | null
  }

  interface TestRun {
    id: number
    title: string
    note: string | null
    test_run_config: TestRunConfig
    created_at: string | null
  }
  */

  const columnNames = {
    id: 'ID',
    title: 'Repositories',
    sut: 'SUT',
    result: 'Result',
    date: 'Date',
    bug: 'Bug',
    actions: 'Actions'
  }

  const handleSelectedTestRun = (testRun) => {
    setSelectedTestResult(testRun)
  }

  const onChangeSearchValue = (value) => {
    setSearchValue(value)
  }

  React.useEffect(() => {
    loadTestResult(searchValue)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchValue])

  React.useEffect(() => {
    loadCurrentTestRunLogTxt()
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
      loadTestResult(searchValue)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [modalShowState])

  const loadTestResult = (filter) => {
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

  const loadCurrentTestRunLogTxt = () => {
    if (api?.permissions.indexOf('r') < 0) {
      return
    }
    if (Object.keys(selectedTestResult).length == 0 || selectedTestResult == null) {
      return
    }
    if (api == null) {
      return
    }
    let url = Constants.API_BASE_URL + '/mapping/api/test-run/log'
    url += '?user-id=' + auth.userId
    url += '&token=' + auth.token
    url += '&api-id=' + api.id
    url += '&id=' + selectedTestResult.id
    if (searchValue != undefined) {
      url += '&search=' + searchValue
    }

    fetch(url)
      .then((res) => res.json())
      .then((data) => {
        setSelectedTestResultArtifacts(data['artifacts'])
        setSelectedTestResultLogTxt(data['log_txt'])
        setSelectedTestResultLogStd(data['stdout_stderr'])
        setSelectedTestResultLogExec(data['log_exec'])
      })
      .catch((err) => {
        console.log(err.message)
      })
  }

  const [activeTabKey, setActiveTabKey] = React.useState<string | number>(0)
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

  const requestTestRun = (test_run) => {
    const mapping_to = Constants._TC_ + Constants._M_ + parentType.replaceAll('-', '_')
    const mapping_id = modalRelationData['relation_id']
    setMessageValue('')
    const tmpConf = test_run.config
    tmpConf['from_db'] = 1

    const data = {
      'api-id': api.id,
      title: test_run.title,
      note: test_run.note,
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

  const testRunListRef = React.createRef<HTMLElement>()
  const testRunDetailsRef = React.createRef<HTMLElement>()
  const testRunDetailsLogTxtRef = React.createRef<HTMLElement>()
  const testRunDetailsLogStdRef = React.createRef<HTMLElement>()
  const testRunArtifactsRef = React.createRef<HTMLElement>()
  const testRunBugRef = React.createRef<HTMLElement>()
  const testRunDetailsLogExecRef = React.createRef<HTMLElement>()

  return (
    <React.Fragment>
      <Modal
        bodyAriaLabel='Scrollable modal content'
        tabIndex={0}
        variant={ModalVariant.large}
        title={`Test Result`}
        description={``}
        isOpen={isModalOpen}
        onClose={handleModalToggle}
      >
        <Tabs activeKey={activeTabKey} onSelect={handleTabClick} aria-label='Add a New/Existing Test Specification' role='region'>
          <Tab
            eventKey={0}
            id='tab-btn-test-runs-list'
            title={<TabTitleText>Test Runs</TabTitleText>}
            tabContentId='tabTestRunsList'
            tabContentRef={testRunListRef}
          />
          <Tab
            eventKey={1}
            id='tab-btn-test-run-details'
            title={<TabTitleText>info</TabTitleText>}
            tabContentId='tabTestRunDetails'
            tabContentRef={testRunDetailsRef}
          />
          <Tab
            eventKey={2}
            id='tab-btn-test-run-details-log-exec'
            title={<TabTitleText>execution log</TabTitleText>}
            tabContentId='tabTestRunDetailsLogExec'
            tabContentRef={testRunDetailsLogExecRef}
          />
          <Tab
            eventKey={3}
            id='tab-btn-test-run-details-log-txt'
            title={<TabTitleText>log.txt</TabTitleText>}
            tabContentId='tabTestRunDetailsLogTxt'
            tabContentRef={testRunDetailsLogTxtRef}
          />
          <Tab
            eventKey={4}
            id='tab-btn-test-run-details-log-std'
            title={<TabTitleText>stdout/stderr</TabTitleText>}
            tabContentId='tabTestRunDetailsLogStd'
            tabContentRef={testRunDetailsLogStdRef}
          />
          <Tab
            eventKey={5}
            id='tab-btn-test-run-bug'
            title={<TabTitleText>Report a Bug</TabTitleText>}
            tabContentId='tabTestRunBug'
            tabContentRef={testRunBugRef}
          />
          <Tab
            eventKey={6}
            id='tab-btn-test-run-artifacts'
            title={<TabTitleText>Artifacts</TabTitleText>}
            tabContentId='tabTestRunArtifacts'
            tabContentRef={testRunArtifactsRef}
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

          <TabContent eventKey={0} id='tabContentTestCaseForm' ref={testRunListRef}>
            <br />
            <SearchInput
              placeholder='Search'
              value={searchValue}
              onChange={(_event, value) => onChangeSearchValue(value)}
              onClear={() => onChangeSearchValue('')}
              style={{ width: '400px' }}
            />
            <br />
            <TabContentBody hasPadding>
              <Table aria-label='Clickable table'>
                <Thead>
                  <Tr>
                    <Th>{columnNames.id}</Th>
                    <Th>{columnNames.title}</Th>
                    <Th>{columnNames.sut}</Th>
                    <Th>{columnNames.result}</Th>
                    <Th>{columnNames.date}</Th>
                    <Th>{columnNames.bug}</Th>
                    <Th>{columnNames.actions}</Th>
                  </Tr>
                </Thead>
                <Tbody>
                  {testResults &&
                    testResults.map((testResult) => (
                      <Tr
                        key={testResult.id}
                        onRowClick={() => handleSelectedTestRun(testResult)}
                        isSelectable
                        isClickable
                        isRowSelected={selectedTestResult === testResult}
                      >
                        <Td dataLabel={columnNames.id}>{testResult.id}</Td>
                        <Td dataLabel={columnNames.title}>{testResult.title}</Td>
                        <Td dataLabel={columnNames.sut}>
                          {testResult.config.provision_type == 'connect' ? testResult.config.provision_guest : 'container'}
                        </Td>
                        <Td dataLabel={columnNames.result}>{testResult?.result}</Td>
                        <Td dataLabel={columnNames.date}>{testResult.created_at}</Td>
                        <Td dataLabel={columnNames.bug}>{testResult.bugs?.length > 0 ? <BugIcon /> : ''}</Td>
                        <Td dataLabel={columnNames.actions}>
                          {api?.permissions.indexOf('w') >= 0 ? (
                            <>
                              <Button
                                variant='plain'
                                aria-label='Action'
                                onClick={() => {
                                  requestTestRun(testResult)
                                }}
                              >
                                <ProcessAutomationIcon /> Re-run
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
          <TabContent eventKey={1} id='tabContentTestResultDetails' ref={testRunDetailsRef} hidden>
            <TabContentBody hasPadding>
              <TextContent>
                <Text component={TextVariants.h3}>Test Run {selectedTestResult.id}</Text>
              </TextContent>
              <br />
              <TextContent>
                <Text component={TextVariants.p}>
                  <b>UID:</b> {selectedTestResult.uid}
                </Text>
                <Text component={TextVariants.p}>
                  <b>Title:</b> {selectedTestResult.title}
                </Text>
                <Text component={TextVariants.p}>
                  <b>Note:</b> {selectedTestResult.note}
                </Text>
                <Text component={TextVariants.p}>
                  <b>Bugs:</b> {selectedTestResult.bugs}
                </Text>
                <Text component={TextVariants.p}>
                  <b>Result:</b> {selectedTestResult.result}
                </Text>
                <Text component={TextVariants.p}>
                  <b>Data:</b> {selectedTestResult.created_at}
                </Text>
                {selectedTestResult.config == null || (
                  <>
                    <Text component={TextVariants.p}>
                      <b>Test run configuration:</b> {selectedTestResult.config?.title}
                    </Text>
                    {selectedTestResult.config.provision_type == 'connect' ? (
                      <>
                        <Text component={TextVariants.p}>
                          <b>Provision:</b> connect
                        </Text>
                        <Text component={TextVariants.p}>
                          <b>Git branch/commit:</b> {selectedTestResult.config.git_repo_ref}
                        </Text>
                        <Text component={TextVariants.p}>
                          <b>Guest:</b> {selectedTestResult.config.provision_guest}
                        </Text>
                        <Text component={TextVariants.p}>
                          <b>Port:</b> {selectedTestResult.config.provision_guest_port}
                        </Text>
                        <Text component={TextVariants.p}>
                          <b>SSH Key:</b> {selectedTestResult.config.ssh_key_id}
                        </Text>
                      </>
                    ) : (
                      <Text component={TextVariants.p}>
                        <b>Provision:</b> container
                      </Text>
                    )}
                    <Text component={TextVariants.p}>
                      <b>Context variables:</b> {selectedTestResult.config.context_vars}
                    </Text>
                    <Text component={TextVariants.p}>
                      <b>Environment variables:</b> {selectedTestResult.config.environment_vars}
                    </Text>
                  </>
                )}
              </TextContent>
            </TabContentBody>
          </TabContent>
          <TabContent eventKey={2} id='tabContentTestResultLogExecSection' ref={testRunDetailsLogExecRef} hidden>
            <TabContentBody hasPadding>
              <TextContent>
                <Text component={TextVariants.h3}>Test Run {selectedTestResult.id}</Text>
              </TextContent>
              <br />
              <CodeBlock>
                <CodeBlockCode id='log-exec'>{selectedTestResultLogExec}</CodeBlockCode>
              </CodeBlock>
            </TabContentBody>
          </TabContent>
          <TabContent eventKey={3} id='tabContentTestResultLogTxtSection' ref={testRunDetailsLogTxtRef} hidden>
            <TabContentBody hasPadding>
              <TextContent>
                <Text component={TextVariants.h3}>Test Run {selectedTestResult.id}</Text>
              </TextContent>
              <br />
              <CodeBlock>
                <CodeBlockCode id='log-txt'>{selectedTestResultLogTxt}</CodeBlockCode>
              </CodeBlock>
            </TabContentBody>
          </TabContent>
          <TabContent eventKey={4} id='tabContentTestResultLogStdSection' ref={testRunDetailsLogStdRef} hidden>
            <TabContentBody hasPadding>
              <TextContent>
                <Text component={TextVariants.h3}>Test Run {selectedTestResult.id}</Text>
              </TextContent>
              <br />
              <CodeBlock>
                <CodeBlockCode id='log-std'>{selectedTestResultLogStd}</CodeBlockCode>
              </CodeBlock>
            </TabContentBody>
          </TabContent>
          <TabContent eventKey={5} id='tabContentTestResultBug' ref={testRunBugRef} hidden>
            <TabContentBody hasPadding>
              <TestRunBugForm api={api} modalTestRun={selectedTestResult} modalRelationData={modalRelationData} parentType={parentType} />
            </TabContentBody>
          </TabContent>
          <TabContent eventKey={6} id='tabContentTestResultArtifacts' ref={testRunArtifactsRef} hidden>
            <TabContentBody hasPadding>
              <TextContent>
                <Text component={TextVariants.h3}>$TMT_PLAN_DATA Directory</Text>
              </TextContent>
              <br />
              {(selectedTestResultArtifacts &&
                selectedTestResultArtifacts.map((artifact, index) => (
                  <Button key={index} component='a' href={getArtifactUrl(artifact)} target='_blank' variant='link'>
                    {artifact}
                  </Button>
                ))) || (
                <TextContent>
                  <Text component={TextVariants.p}>empty</Text>
                </TextContent>
              )}
            </TabContentBody>
          </TabContent>
        </div>
      </Modal>
    </React.Fragment>
  )
}
