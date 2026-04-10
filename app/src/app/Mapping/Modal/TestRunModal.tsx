import _ from 'lodash'
import * as React from 'react'
import * as Constants from '@app/Constants/constants'
import {
  Button,
  Divider,
  Hint,
  HintBody,
  Modal,
  ModalVariant,
  Tab,
  TabContent,
  TabContentBody,
  TabTitleText,
  Tabs
} from '@patternfly/react-core'
import { TestRunForm } from '../Form/TestRunForm'
import { TestRunConfigForm } from '../Form/TestRunConfigForm'
import { TestRunConfigSearch } from '../Search/TestRunConfigSearch'
import { useAuth } from '../../User/AuthProvider'

export interface TestRunModalProps {
  api
  modalRelationData
  modalShowState: boolean
  parentType
  setModalShowState
  setTestResultsModalShowState
}

export const TestRunModal: React.FunctionComponent<TestRunModalProps> = ({
  api,
  modalRelationData,
  modalShowState,
  parentType,
  setModalShowState,
  setTestResultsModalShowState
}: TestRunModalProps) => {
  const auth = useAuth()
  const [infoLabel, setInfoLabel] = React.useState('new')
  const [isModalOpen, setIsModalOpen] = React.useState(false)
  const [testRunConfigs, setTestRunConfigs] = React.useState([])
  const [sshKeys, setSshKeys] = React.useState([])
  // eslint-disable-next-line  @typescript-eslint/no-explicit-any
  const [testRunConfig, setTestRunConfig] = React.useState<any>({})

  const [titleValue, setTitleValue] = React.useState('')
  const [validatedTitleValue, setValidatedTitleValue] = React.useState<Constants.validate>('error')
  const [notesValue, setNotesValue] = React.useState('')
  const [messageValue, setMessageValue] = React.useState('')

  const resetForms = () => {
    setTitleValue('')
    setNotesValue('')
    setTestRunConfig({})
  }

  const handleModalToggle = () => {
    const new_state = !modalShowState
    setModalShowState(new_state)
    setIsModalOpen(new_state)
  }

  const handleTitleValueChange = (value: string) => {
    setTitleValue(value)
  }

  const handleNotesValueChange = (value: string) => {
    setNotesValue(value)
  }

  React.useEffect(() => {
    if (Constants._trim(titleValue) === '') {
      setValidatedTitleValue('error')
    } else {
      setValidatedTitleValue('success')
    }
  }, [titleValue])

  const handleSelectExistingTestConfig = (config) => {
    let config_copy = _.cloneDeep(config)
    if ([Constants.gitlab_ci_plugin, Constants.github_actions_plugin, Constants.LAVA_plugin].indexOf(config_copy['plugin']) > -1) {
      config_copy = Constants.extend_config_with_plugin_vars(config_copy)
    }
    setTestRunConfig(config_copy)
  }

  React.useEffect(() => {
    setIsModalOpen(modalShowState)
    if (modalShowState == true) {
      setActiveTabKey(0)
    }
  }, [modalShowState])

  const loadSSHKeys = () => {
    let url = Constants.API_BASE_URL + Constants.API_USER_SSH_KEY_ENDPOINT
    url += '?user-id=' + auth.userId
    url += '&token=' + auth.token

    fetch(url)
      .then((res) => res.json())
      .then((data) => {
        setSshKeys(data)
      })
      .catch((err) => {
        console.log(err.message)
      })
  }

  const loadTestRunConfigs = (searchValue) => {
    if (auth.isGuest()) {
      return
    }

    let url = Constants.API_BASE_URL + Constants.API_TEST_RUN_CONFIGS_ENDPOINT
    url = url + '?user-id=' + auth.userId
    url = url + '&token=' + auth.token
    if (searchValue != undefined) {
      url = url + '&search=' + searchValue
    }
    fetch(url)
      .then((res) => res.json())
      .then((data) => {
        setTestRunConfigs(data)
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

  const newItemRef = React.createRef<HTMLElement>()
  const sectionItemsRef = React.createRef<HTMLElement>()
  const existingItemsRef = React.createRef<HTMLElement>()

  const validateConfig = () => {
    if (!validatedTitleValue) {
      setMessageValue('Test Run title is not defined')
      setActiveTabKey(0)
      return false
    }
    if (testRunConfig == null) {
      setMessageValue('Test Configuration is not defined')
      setActiveTabKey(1)
      return false
    }
    if (testRunConfig['from_db'] == 1) {
      return true
    }
    if (Object.keys(testRunConfig).indexOf('title') < 0) {
      setMessageValue('Test Configuration is not defined')
      setActiveTabKey(1)
      return false
    }
    if (Constants._trim(testRunConfig['title']) == '') {
      setMessageValue('Test Configuration Title is mandatory')
      setActiveTabKey(1)
      return false
    }
    if (Constants._trim(testRunConfig['plugin']) == Constants.tmt_plugin) {
      if (Constants._trim(testRunConfig['plugin_preset']) == '') {
        if (Constants._trim(testRunConfig['provision_type']) == '') {
          setMessageValue('Test Configuration Provision Type is mandatory')
          setActiveTabKey(1)
          return false
        } else if (Constants._trim(testRunConfig['provision_type']) == 'connect') {
          if (Constants._trim(testRunConfig['provision_guest']) == '') {
            setMessageValue('Test Configuration Hostname or IP address is mandatory')
            setActiveTabKey(1)
            return false
          }
          if (Constants._trim(testRunConfig['provision_guest_port']) == '') {
            setMessageValue('Test Configuration Provision Guest Port is mandatory')
            setActiveTabKey(1)
            return false
          }
          if (testRunConfig['ssh_key'] == 0) {
            setMessageValue('Test Configuration SSH Key is mandatory')
            setActiveTabKey(1)
            return false
          }
        }
      }
    } else if (Constants._trim(testRunConfig['plugin']) == Constants.gitlab_ci_plugin) {
      if (Constants._trim(testRunConfig['plugin_preset']) == '') {
        if (Constants._trim(testRunConfig['url']) == '') {
          setMessageValue('Test Configuration Url is mandatory')
          setActiveTabKey(1)
          return false
        }
        if (Constants._trim(testRunConfig['project_id']) == '') {
          setMessageValue('Test Configuration Project ID is mandatory')
          setActiveTabKey(1)
          return false
        }
        if (Constants._trim(testRunConfig['trigger_token']) == '') {
          setMessageValue('Test Configuration Trigger Token is mandatory')
          setActiveTabKey(1)
          return false
        }
        if (Constants._trim(testRunConfig['private_token']) == '') {
          setMessageValue('Test Configuration Private Token is mandatory')
          setActiveTabKey(1)
          return false
        }
      }
    } else if (Constants._trim(testRunConfig['plugin']) == Constants.github_actions_plugin) {
      if (Constants._trim(testRunConfig['plugin_preset']) == '') {
        if (Constants._trim(testRunConfig['url']) == '') {
          setMessageValue('Test Configuration Url is mandatory')
          setActiveTabKey(1)
          return false
        }
        if (Constants._trim(testRunConfig['private_token']) == '') {
          setMessageValue('Test Configuration Private Token is mandatory')
          setActiveTabKey(1)
          return false
        }
      }
    } else if (Constants._trim(testRunConfig['plugin']) == Constants.testing_farm_plugin) {
      if (Constants._trim(testRunConfig['plugin_preset']) == '') {
        if (Constants._trim(testRunConfig['url']) == '') {
          setMessageValue('Testing Farm Url is mandatory')
          setActiveTabKey(1)
          return false
        }
        if (Constants._trim(testRunConfig['private_token']) == '') {
          setMessageValue('Testing Farm Token is mandatory')
          setActiveTabKey(1)
          return false
        }
        if (Constants._trim(testRunConfig['compose']) == '') {
          setMessageValue('Testing Farm Compose is mandatory')
          setActiveTabKey(1)
          return false
        }
        if (Constants._trim(testRunConfig['arch']) == '') {
          setMessageValue('Testing Farm Architecture is mandatory')
          setActiveTabKey(1)
          return false
        }
        if (Constants._trim(testRunConfig['git_repo_ref']) == '') {
          setMessageValue('Test Configuration Git repo Ref is mandatory')
          setActiveTabKey(1)
          return false
        }
      }
    }
    return true
  }

  const handleRun = () => {
    if (validatedTitleValue != 'success') {
      setMessageValue('Test Run Title is mandatory.')
      setActiveTabKey(0)
      return
    } else if (validateConfig() == false) {
      return
    }

    if (parentType == '' || parentType == null) {
      setMessageValue('Error in the mapping data')
      return
    }

    if (modalRelationData == null || modalRelationData == undefined) {
      setMessageValue('Error in the mapping data')
      return
    }

    const mapping_to = Constants._TC_ + Constants._M_ + parentType.replaceAll('-', '_')
    const mapping_id = modalRelationData['relation_id']
    setMessageValue('')

    const data = {
      'api-id': api.id,
      title: Constants._trim(titleValue),
      notes: Constants._trim(notesValue),
      'test-run-config': testRunConfig,
      'user-id': auth.userId,
      token: auth.token,
      mapped_to_type: mapping_to,
      mapped_to_id: mapping_id
    }

    fetch(Constants.API_BASE_URL + Constants.API_TEST_RUNS_ENDPOINT, {
      method: 'POST',
      headers: Constants.JSON_HEADER,
      body: JSON.stringify(data)
    })
      .then((response) => {
        if (!Constants.isHttpSuccessStatus(response.status)) {
          setMessageValue(response.statusText)
        } else {
          handleModalToggle()
          setTestResultsModalShowState(true)
          setMessageValue('')
          resetForms()
        }
      })
      .catch((err) => {
        setMessageValue(err.toString())
      })
  }

  return (
    <React.Fragment>
      <Modal
        width={Constants.MODAL_WIDTH}
        bodyAriaLabel='TestRunModal'
        aria-label='test run modal'
        tabIndex={0}
        variant={ModalVariant.large}
        title='Test Run'
        description={``}
        isOpen={isModalOpen}
        onClose={handleModalToggle}
        actions={[
          <Button id='btn-test-run-add-submit' key='run' variant='primary' onClick={() => handleRun()}>
            Run
          </Button>,
          <Button id='btn-test-run-add-cancel' key='cancel' variant='secondary' onClick={() => handleModalToggle()}>
            Cancel
          </Button>
        ]}
      >
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
        <Tabs activeKey={activeTabKey} onSelect={handleTabClick} aria-label='Add a New/Existing Test Specification' role='region'>
          <Tab
            eventKey={0}
            id='tab-btn-test-run-data'
            title={<TabTitleText>Test Run Data</TabTitleText>}
            tabContentId='tabNewTestRun'
            tabContentRef={newItemRef}
          />
          <Tab
            eventKey={1}
            id='tab-btn-test-run-config-data'
            title={<TabTitleText>Test Run Config</TabTitleText>}
            tabContentId='tabSection'
            tabContentRef={sectionItemsRef}
          />
          <Tab
            eventKey={2}
            id='tab-btn-test-run-config-existing'
            title={<TabTitleText>Existing Test Run Config</TabTitleText>}
            tabContentId='tabExistingTestRunConfig'
            tabContentRef={existingItemsRef}
          />
        </Tabs>
        <div>
          <TabContent eventKey={0} id='tabContentTestRunForm' ref={newItemRef} hidden={0 !== activeTabKey}>
            <TabContentBody hasPadding>
              <TestRunForm
                titleValue={titleValue}
                notesValue={notesValue}
                validatedTitleValue={validatedTitleValue}
                handleTitleValueChange={handleTitleValueChange}
                handleNotesValueChange={handleNotesValueChange}
              />
            </TabContentBody>
          </TabContent>
          <TabContent eventKey={1} id='tabContentTestRunConfig' ref={sectionItemsRef} hidden={1 !== activeTabKey}>
            <TabContentBody hasPadding>
              <TestRunConfigForm
                api={api}
                loadSSHKeys={loadSSHKeys}
                sshKeys={sshKeys}
                testRunConfig={testRunConfig}
                setTestRunConfig={setTestRunConfig}
                infoLabel={infoLabel}
                setInfoLabel={setInfoLabel}
              />
            </TabContentBody>
          </TabContent>
          <TabContent eventKey={2} id='tabContentTestRunConfigExisting' ref={existingItemsRef} hidden={2 !== activeTabKey}>
            <TabContentBody hasPadding>
              <TestRunConfigSearch
                handleSelectExistingTestConfig={handleSelectExistingTestConfig}
                loadTestRunConfigs={loadTestRunConfigs}
                modalShowState={modalShowState}
                testRunConfigs={testRunConfigs}
                setInfoLabel={setInfoLabel}
                setActiveTabKey={setActiveTabKey}
              />
            </TabContentBody>
          </TabContent>
        </div>
      </Modal>
    </React.Fragment>
  )
}
