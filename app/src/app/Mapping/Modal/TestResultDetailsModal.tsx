import * as React from 'react'
import * as Constants from '@app/Constants/constants'
import {
  Button,
  CodeBlock,
  CodeBlockCode,
  Divider,
  Hint,
  HintBody,
  Label,
  Modal,
  ModalVariant,
  Tab,
  TabContent,
  TabContentBody,
  TabTitleText,
  Tabs,
  Text,
  TextContent,
  TextVariants
} from '@patternfly/react-core'
import { Table, Tbody, Td, Th, Thead, Tr } from '@patternfly/react-table'
import { Editor } from '@monaco-editor/react'
import CheckCircleIcon from '@patternfly/react-icons/dist/esm/icons/check-circle-icon'
import InfoCircleIcon from '@patternfly/react-icons/dist/esm/icons/info-circle-icon'
import ExclamationCircleIcon from '@patternfly/react-icons/dist/esm/icons/exclamation-circle-icon'
import { TestRunBugForm } from '../Form/TestRunBugForm'
import { useAuth } from '../../User/AuthProvider'
import { AutoRefresh } from '@app/Common/AutoRefresh/AutoRefresh'

const ARTIFACT_VIEWABLE_EXTENSIONS = [
  'c',
  'cc',
  'cpp',
  'csv',
  'fmf',
  'gcov',
  'info',
  'json',
  'log',
  'md',
  'pl',
  'py',
  'rst',
  'sh',
  'txt',
  'yaml',
  'yml'
]

const isArtifactViewable = (filename: string): boolean => {
  if (!filename || !filename.trim()) return false
  const lastDot = filename.lastIndexOf('.')
  if (lastDot === -1) return true // no extension, e.g. Makefile
  const ext = filename.slice(lastDot + 1).toLowerCase()
  return ARTIFACT_VIEWABLE_EXTENSIONS.includes(ext)
}

export interface TestResultDetailsModalProps {
  api
  modalShowState: boolean
  modalRelationData
  parentType
  setModalShowState
  setTestResultsModalShowState
  loadTestResults
  currentTestResult
}

export const TestResultDetailsModal: React.FunctionComponent<TestResultDetailsModalProps> = ({
  api,
  modalShowState,
  modalRelationData,
  parentType,
  setModalShowState,
  setTestResultsModalShowState,
  loadTestResults,
  currentTestResult
}: TestResultDetailsModalProps) => {
  const auth = useAuth()
  const [isModalOpen, setIsModalOpen] = React.useState(false)
  // eslint-disable-next-line  @typescript-eslint/no-explicit-any
  const [selectedTestResultArtifacts, setSelectedTestResultArtifacts] = React.useState([])

  // eslint-disable-next-line  @typescript-eslint/no-unused-vars
  const [selectedTestResultLogExec, setSelectedTestResultLogExec] = React.useState('')
  const [selectedTestResultLog, setSelectedTestResultLog] = React.useState('')
  const [selectedTestResultResult, setSelectedTestResultResult] = React.useState(null)
  const [selectedTestResultStatus, setSelectedTestResultStatus] = React.useState(null)
  const [selectedTestResultReport, setSelectedTestResultReport] = React.useState(null)
  const [messageValue, setMessageValue] = React.useState('')
  const [activeTabKey, setActiveTabKey] = React.useState<string | number>(0)
  const [artifactViewing, setArtifactViewing] = React.useState<string | null>(null)
  const [artifactContent, setArtifactContent] = React.useState<string>('')
  const [artifactContentLoading, setArtifactContentLoading] = React.useState(false)
  const [artifactContentError, setArtifactContentError] = React.useState<string | null>(null)

  React.useEffect(() => {
    loadCurrentTestRunLog()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentTestResult])

  const handleModalToggle = () => {
    const new_state = !modalShowState
    setModalShowState(new_state)
    setIsModalOpen(new_state)
    if (new_state == false) {
      setMessageValue('')
    }
  }

  React.useEffect(() => {
    setIsModalOpen(modalShowState)
    if (!modalShowState) {
      setActiveTabKey(0)
      setArtifactContent('')
      setArtifactContentError(null)
      setArtifactContentLoading(false)
      setArtifactViewing(null)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [modalShowState])

  const navigateReport = (url) => {
    if (typeof url !== 'undefined' && url != null) {
      window.open(url, '_blank', 'noreferrer')
    }
  }

  const loadCurrentTestRunLog = () => {
    if (api?.permissions.indexOf('r') < 0) {
      return
    }
    if (Object.keys(currentTestResult).length == 0 || currentTestResult == null) {
      return
    }
    if (api == null) {
      return
    }
    let url = Constants.API_BASE_URL + Constants.API_TEST_RUN_LOG_ENDPOINT
    url += '?user-id=' + auth.userId
    url += '&token=' + auth.token
    url += '&api-id=' + api.id
    url += '&id=' + currentTestResult.id

    fetch(url)
      .then((res) => res.json())
      .then((data) => {
        setSelectedTestResultArtifacts(data['artifacts'] ? data['artifacts'].sort() : [])
        setSelectedTestResultLog(data['log'])
        setSelectedTestResultLogExec(data['log_exec'])
        setSelectedTestResultReport(data['report'])
        setSelectedTestResultStatus(data['status'])
        setSelectedTestResultResult(data['result'])
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
    let url = Constants.API_BASE_URL + Constants.API_TEST_RUN_ARTIFACTS_ENDPOINT
    url += '?api-id=' + api.id
    url += '&user-id=' + auth.userId
    url += '&token=' + auth.token
    url += '&id=' + currentTestResult.id
    url += '&artifact=' + artifact
    return url
  }

  const getArtifactContentUrl = () => {
    if (!artifactViewing) return ''
    let url = Constants.API_BASE_URL + Constants.API_TEST_RUN_ARTIFACT_CONTENT_ENDPOINT
    url += '?api-id=' + api.id
    url += '&user-id=' + auth.userId
    url += '&token=' + auth.token
    url += '&id=' + currentTestResult.id
    url += '&artifact=' + encodeURIComponent(artifactViewing)
    return url
  }

  const loadArtifactContent = () => {
    if (!artifactViewing || api?.permissions.indexOf('r') < 0) return
    setArtifactContentLoading(true)
    setArtifactContentError(null)
    fetch(getArtifactContentUrl())
      .then((res) => res.json())
      .then((data) => {
        setArtifactContent(data.content != null ? data.content : '')
        if (data.error) setArtifactContentError(data.error)
      })
      .catch((err) => {
        setArtifactContentError(err.message)
        setArtifactContent('')
      })
      .finally(() => setArtifactContentLoading(false))
  }

  React.useEffect(() => {
    if (artifactViewing) {
      loadArtifactContent()
    } else {
      setArtifactContent('')
      setArtifactContentError(null)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [artifactViewing])

  const backToArtifactsList = () => {
    setArtifactViewing(null)
  }

  const backToTheList = () => {
    setModalShowState(false)
    setTestResultsModalShowState(true)
  }

  const testRunDetailsRef = React.createRef<HTMLElement>()
  const testRunDetailsLogRef = React.createRef<HTMLElement>()
  const testRunArtifactsRef = React.createRef<HTMLElement>()
  const testRunBugsFixesNotesRef = React.createRef<HTMLElement>()

  return (
    <React.Fragment>
      <Modal
        width={Constants.MODAL_WIDTH}
        bodyAriaLabel='TestResultDetailsModal'
        aria-label='test result details modal'
        tabIndex={0}
        variant={ModalVariant.large}
        title='Test Result Details'
        description={<AutoRefresh loadRows={loadTestResults} showCountdown={true} />}
        isOpen={isModalOpen}
        onClose={handleModalToggle}
      >
        {currentTestResult.status != 'completed' ? (
          <>
            <Button
              onClick={() => {
                loadCurrentTestRunLog()
              }}
            >
              Refresh
            </Button>
            &nbsp;
          </>
        ) : (
          ''
        )}
        <Button
          onClick={() => {
            backToTheList()
          }}
        >
          Back to the list
        </Button>
        <Tabs activeKey={activeTabKey} onSelect={handleTabClick} aria-label='Test Run Details Tabs' role='region'>
          <Tab
            eventKey={0}
            id='tab-btn-test-run-details'
            title={<TabTitleText>Info</TabTitleText>}
            tabContentId='tabTestRunDetails'
            tabContentRef={testRunDetailsRef}
          />
          <Tab
            eventKey={1}
            id='tab-btn-test-run-details-log'
            title={<TabTitleText>Log</TabTitleText>}
            tabContentId='tabTestRunDetailsLog'
            tabContentRef={testRunDetailsLogRef}
          />
          <Tab
            eventKey={2}
            id='tab-btn-test-run-bugs-fixes-notes'
            title={<TabTitleText>Edit Bugs/Fixes/Notes</TabTitleText>}
            tabContentId='tabTestRunBugsFixesNotes'
            tabContentRef={testRunBugsFixesNotesRef}
          />
          <Tab
            eventKey={3}
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
        </div>
        <TabContent eventKey={0} id='tabContentTestResultDetails' ref={testRunDetailsRef} hidden={0 !== activeTabKey}>
          <TabContentBody hasPadding>
            <TextContent>
              <Text component={TextVariants.h3}>Test Run {currentTestResult.id}</Text>
            </TextContent>
            <br />
            <TextContent>
              <Text component={TextVariants.p}>
                <b>Title: </b> {currentTestResult.title}
              </Text>
              <Text component={TextVariants.p}>
                <b>Result: </b>
                {(() => {
                  if (selectedTestResultResult == null) {
                    return (
                      <Label icon={<CheckCircleIcon />} color='purple'>
                        {selectedTestResultStatus}
                      </Label>
                    )
                  } else {
                    if (selectedTestResultResult == 'pass') {
                      return (
                        <Label icon={<CheckCircleIcon />} color='green'>
                          {selectedTestResultResult}
                        </Label>
                      )
                    } else if (selectedTestResultResult == 'fail') {
                      return (
                        <Label icon={<ExclamationCircleIcon />} color='red'>
                          {selectedTestResultResult}
                        </Label>
                      )
                    } else {
                      return (
                        <Label icon={<InfoCircleIcon />} color='orange'>
                          {selectedTestResultResult}
                        </Label>
                      )
                    }
                  }
                })()}
              </Text>
              {(() => {
                if (currentTestResult?.config?.plugin != 'tmt') {
                  if (selectedTestResultReport != null) {
                    return (
                      <Text component={TextVariants.p}>
                        <b>Link: </b>
                        <Button variant='link' onClick={() => navigateReport(currentTestResult.report)}>
                          {currentTestResult.report}
                        </Button>
                      </Text>
                    )
                  } else {
                    return ''
                  }
                } else {
                  return ''
                }
              })()}
              <Text component={TextVariants.p}>
                <b>UID: </b> {currentTestResult?.uid}
              </Text>
              <Text component={TextVariants.p}>
                <b>Bugs: </b> {currentTestResult?.bugs}
              </Text>
              <Text component={TextVariants.p}>
                <b>Fixes: </b> {currentTestResult?.fixes}
              </Text>
              <Text component={TextVariants.p}>
                <b>Notes: </b> {currentTestResult?.notes}
              </Text>
              <Text component={TextVariants.p}>
                <b>Data: </b> {currentTestResult?.created_at}
              </Text>
              <Text component={TextVariants.p}>
                <b>Test run configuration: </b> {currentTestResult?.config?.title}
              </Text>
              <Text component={TextVariants.p}>
                <b>Plugin: </b> {currentTestResult?.config?.plugin}
              </Text>
              <Text component={TextVariants.p}>
                <b>Plugin preset: </b> {currentTestResult?.config?.plugin_preset}
              </Text>
              <Text component={TextVariants.p}>
                <b>Git branch/commit: </b> {currentTestResult?.config?.git_repo_ref}
              </Text>
              {(() => {
                if (currentTestResult?.config?.plugin == 'tmt') {
                  if (currentTestResult.config.provision_type == 'connect') {
                    return (
                      <>
                        <Text component={TextVariants.p}>
                          <b>Provision: </b> connect
                        </Text>
                        <Text component={TextVariants.p}>
                          <b>Guest: </b> {currentTestResult.config.provision_guest}
                        </Text>
                        <Text component={TextVariants.p}>
                          <b>Port: </b> {currentTestResult.config.provision_guest_port}
                        </Text>
                        <Text component={TextVariants.p}>
                          <b>SSH Key: </b> {currentTestResult.config.ssh_key_id}
                        </Text>
                        <Text component={TextVariants.p}>
                          <b>Context variables: </b> {currentTestResult.config.context_vars}
                        </Text>
                      </>
                    )
                  } else {
                    return (
                      <>
                        <Text component={TextVariants.p}>
                          <b>Provision: </b>container
                        </Text>
                        <Text component={TextVariants.p}>
                          <b>Context variables: </b>
                          {currentTestResult.config.context_vars}
                        </Text>
                      </>
                    )
                  }
                } else if (currentTestResult?.config?.plugin == 'gitlab_ci') {
                  return (
                    <>
                      <Text component={TextVariants.p}>
                        <b>Project ID: </b>
                        {Constants.get_config_plugin_var(currentTestResult.config, 'project_id')}
                      </Text>
                      <Text component={TextVariants.p}>
                        <b>Url: </b>
                        <Button
                          variant='link'
                          onClick={() => navigateReport(Constants.get_config_plugin_var(currentTestResult.config, 'url'))}
                        >
                          {Constants.get_config_plugin_var(currentTestResult.config, 'url')}
                        </Button>
                      </Text>
                      <Text component={TextVariants.p}>
                        <b>Stage: </b>
                        {Constants.get_config_plugin_var(currentTestResult.config, 'stage')}
                      </Text>
                      <Text component={TextVariants.p}>
                        <b>Job: </b>
                        {Constants.get_config_plugin_var(currentTestResult.config, 'job')}
                      </Text>
                    </>
                  )
                } else if (currentTestResult?.config?.plugin == 'github_actions') {
                  return (
                    <>
                      <Text component={TextVariants.p}>
                        <b>Workflow ID: </b>
                        {Constants.get_config_plugin_var(currentTestResult.config, 'workflow_id')}
                      </Text>
                      <Text component={TextVariants.p}>
                        <b>Url: </b>
                        <Button
                          variant='link'
                          onClick={() => navigateReport(Constants.get_config_plugin_var(currentTestResult.config, 'url'))}
                        >
                          {Constants.get_config_plugin_var(currentTestResult.config, 'url')}
                        </Button>
                      </Text>
                      <Text component={TextVariants.p}>
                        <b>Job: </b>
                        {Constants.get_config_plugin_var(currentTestResult.config, 'job')}
                      </Text>
                    </>
                  )
                } else {
                  return ''
                }
              })()}
              <Text component={TextVariants.p}>
                <b>Variables: </b> {currentTestResult?.config?.environment_vars}
              </Text>
            </TextContent>
          </TabContentBody>
        </TabContent>
        <TabContent eventKey={1} id='tabContentTestResultLogSection' ref={testRunDetailsLogRef} hidden={1 !== activeTabKey}>
          <TabContentBody hasPadding>
            <AutoRefresh loadRows={loadCurrentTestRunLog} showCountdown={false} />
            <TextContent>
              <Text component={TextVariants.h3}>Test Run {currentTestResult.id}</Text>
            </TextContent>
            <br />
            <CodeBlock>
              <CodeBlockCode id='code-block-test-run-details-log'>
                {(() => {
                  const hasLog = Constants.isNotEmptyString(selectedTestResultLog)
                  const hasExec = Constants.isNotEmptyString(selectedTestResultLogExec)
                  if (hasLog) {
                    if (currentTestResult.status == 'running' && hasExec) {
                      return selectedTestResultLog + '\n------------------------------\n' + selectedTestResultLogExec
                    }
                    return selectedTestResultLog
                  }
                  return selectedTestResultLogExec
                })()}
              </CodeBlockCode>
            </CodeBlock>
          </TabContentBody>
        </TabContent>
        <TabContent eventKey={2} id='tabContentTestResultBug' ref={testRunBugsFixesNotesRef} hidden={2 !== activeTabKey}>
          <TabContentBody hasPadding>
            <TestRunBugForm api={api} modalTestRun={currentTestResult} modalRelationData={modalRelationData} parentType={parentType} />
          </TabContentBody>
        </TabContent>
        <TabContent eventKey={3} id='tabContentTestResultArtifacts' ref={testRunArtifactsRef} hidden={3 !== activeTabKey}>
          <TabContentBody hasPadding>
            {selectedTestResultArtifacts && selectedTestResultArtifacts.length > 0 ? (
              artifactViewing ? (
                <>
                  <Button variant='link' onClick={backToArtifactsList} style={{ paddingLeft: 0 }}>
                    Back to artifacts list
                  </Button>
                  <br />
                  {artifactContentError && (
                    <>
                      <Hint>
                        <HintBody>{artifactContentError}</HintBody>
                      </Hint>
                      <br />
                    </>
                  )}
                  {artifactContentLoading ? (
                    <TextContent>
                      <Text component={TextVariants.p}>Loading…</Text>
                    </TextContent>
                  ) : (
                    <Editor
                      height='400px'
                      theme='vs-dark'
                      value={artifactContent}
                      language='plaintext'
                      options={{
                        readOnly: true,
                        domReadOnly: true,
                        minimap: { enabled: false }
                      }}
                    />
                  )}
                </>
              ) : (
                <Table aria-label='Artifacts table' variant='compact'>
                  <Thead>
                    <Tr>
                      <Th>Name</Th>
                      <Th>Created at</Th>
                      <Th>Actions</Th>
                    </Tr>
                  </Thead>
                  <Tbody>
                    {selectedTestResultArtifacts.map((artifact, index) => (
                      <Tr key={'artifact-' + index}>
                        <Td dataLabel='Name'>{artifact}</Td>
                        <Td dataLabel='Created at'>—</Td>
                        <Td dataLabel='Actions'>
                          {isArtifactViewable(artifact) && (
                            <>
                              <Button variant='link' isInline onClick={() => setArtifactViewing(artifact)}>
                                View
                              </Button>
                              {' · '}
                            </>
                          )}
                          <Button
                            variant='link'
                            isInline
                            component='a'
                            href={getArtifactUrl(artifact)}
                            target='_blank'
                            rel='noopener noreferrer'
                          >
                            Download
                          </Button>
                        </Td>
                      </Tr>
                    ))}
                  </Tbody>
                </Table>
              )
            ) : (
              <TextContent>
                <Text component={TextVariants.p}>empty</Text>
              </TextContent>
            )}
          </TabContentBody>
        </TabContent>
      </Modal>
    </React.Fragment>
  )
}
