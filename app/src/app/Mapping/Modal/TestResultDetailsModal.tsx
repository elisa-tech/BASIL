import * as React from 'react'
import * as Constants from '../../Constants/constants'
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
import CheckCircleIcon from '@patternfly/react-icons/dist/esm/icons/check-circle-icon'
import InfoCircleIcon from '@patternfly/react-icons/dist/esm/icons/info-circle-icon'
import ExclamationCircleIcon from '@patternfly/react-icons/dist/esm/icons/exclamation-circle-icon'
import { TestRunBugForm } from '../Form/TestRunBugForm'
import { useAuth } from '../../User/AuthProvider'

export interface TestResultDetailsModalProps {
  api
  modalShowState: boolean
  modalRelationData
  parentType
  setModalShowState
  setTestResultsModalShowState
  currentTestResult
}

export const TestResultDetailsModal: React.FunctionComponent<TestResultDetailsModalProps> = ({
  api,
  modalShowState,
  modalRelationData,
  parentType,
  setModalShowState,
  setTestResultsModalShowState,
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
    let url = Constants.API_BASE_URL + '/mapping/api/test-run/log'
    url += '?user-id=' + auth.userId
    url += '&token=' + auth.token
    url += '&api-id=' + api.id
    url += '&id=' + currentTestResult.id

    fetch(url)
      .then((res) => res.json())
      .then((data) => {
        setSelectedTestResultArtifacts(data['artifacts'])
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
    let url = Constants.API_BASE_URL + '/mapping/api/test-run/artifacts'
    url += '?api-id=' + api.id
    url += '&user-id=' + auth.userId
    url += '&token=' + auth.token
    url += '&id=' + currentTestResult.id
    url += '&artifact=' + artifact
    return url
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
        bodyAriaLabel='TestResultDetailsModal'
        aria-label='test result details modal'
        tabIndex={0}
        variant={ModalVariant.large}
        title='Test Result Details'
        description={``}
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
            <TextContent>
              <Text component={TextVariants.h3}>Test Run {currentTestResult.id}</Text>
            </TextContent>
            <br />
            <CodeBlock>
              <CodeBlockCode id='code-block-test-run-details-log'>
                {selectedTestResultLog}
                {currentTestResult.status == 'running' ? '\n------------------------------\n' + selectedTestResultLogExec : ''}
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
      </Modal>
    </React.Fragment>
  )
}
