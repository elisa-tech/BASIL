import _ from 'lodash'
import * as React from 'react'
import * as Constants from '../../Constants/constants'
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
}

export const TestRunModal: React.FunctionComponent<TestRunModalProps> = ({
  api,
  modalRelationData,
  modalShowState,
  parentType,
  setModalShowState
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
    if (titleValue.trim() === '') {
      setValidatedTitleValue('error')
    } else {
      setValidatedTitleValue('success')
    }
  }, [titleValue])

  const handleSelectExistingTestConfig = (config) => {
    let config_copy = _.cloneDeep(config)
    if (['gitlab_ci', 'github_actions'].indexOf(config_copy['plugin']) > -1) {
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
    let url = Constants.API_BASE_URL + '/user/ssh-key'
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

    let url = Constants.API_BASE_URL + '/mapping/api/test-run-configs'
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

  React.useEffect(() => {
    if (Object.keys(testRunConfig).length > 0) {
      document.getElementById('pf-tab-1-tab-btn-test-run-config-data')?.click()
    }
  }, [testRunConfig])

  const validateConfig = () => {
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
    if (testRunConfig['title'].trim() == '') {
      setMessageValue('Test Configuration Title is mandatory')
      setActiveTabKey(1)
      return false
    }
    if (testRunConfig['plugin'].trim() == 'tmt') {
      if (testRunConfig['plugin_preset'].trim() == '') {
        if (testRunConfig['provision_type'].trim() == '') {
          setMessageValue('Test Configuration Provision Type is mandatory')
          setActiveTabKey(1)
          return false
        } else if (testRunConfig['provision_type'].trim() == 'connect') {
          if (testRunConfig['provision_guest'].trim() == '') {
            setMessageValue('Test Configuration Hostname or IP address is mandatory')
            setActiveTabKey(1)
            return false
          }
          if (testRunConfig['provision_guest_port'].trim() == '') {
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
    } else if (testRunConfig['plugin'].trim() == 'gitlab_ci') {
      if (testRunConfig['plugin_preset'].trim() == '') {
        if (testRunConfig['url'].trim() == '') {
          setMessageValue('Test Configuration Url is mandatory')
          setActiveTabKey(1)
          return false
        }
        if (testRunConfig['project_id'].trim() == '') {
          setMessageValue('Test Configuration Project ID is mandatory')
          setActiveTabKey(1)
          return false
        }
        if (testRunConfig['trigger_token'].trim() == '') {
          setMessageValue('Test Configuration Trigger Token is mandatory')
          setActiveTabKey(1)
          return false
        }
        if (testRunConfig['private_token'].trim() == '') {
          setMessageValue('Test Configuration Private Token is mandatory')
          setActiveTabKey(1)
          return false
        }
      }
    } else if (testRunConfig['plugin'].trim() == 'github_actions') {
      if (testRunConfig['plugin_preset'].trim() == '') {
        if (testRunConfig['url'].trim() == '') {
          setMessageValue('Test Configuration Url is mandatory')
          setActiveTabKey(1)
          return false
        }
        if (testRunConfig['private_token'].trim() == '') {
          setMessageValue('Test Configuration Private Token is mandatory')
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
      title: titleValue.trim(),
      notes: notesValue.trim(),
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
          handleModalToggle()
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
        bodyAriaLabel='TestRunModal'
        aria-label='test run modal'
        tabIndex={0}
        variant={ModalVariant.large}
        title='Test Run'
        description={``}
        isOpen={isModalOpen}
        onClose={handleModalToggle}
        actions={[
          <Button key='run' variant='primary' onClick={handleRun}>
            Run
          </Button>,
          <Button key='cancel' variant='secondary' onClick={handleModalToggle}>
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
