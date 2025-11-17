import * as React from 'react'
import * as Constants from '../Constants/constants'
import {
  Button,
  Divider,
  Flex,
  FlexItem,
  Form,
  FormGroup,
  FormSelect,
  FormSelectOption,
  Hint,
  HintBody,
  PageSection,
  Tooltip
} from '@patternfly/react-core'
import { Editor } from '@monaco-editor/react'
import { useAuth } from '../User/AuthProvider'
import { ModalTraceabilityLog } from './Modal/ModalTraceabilityLog'
import { ModalNotification } from '@app/Common/Modal/ModalNotification'
export interface TraceabilityScannerProps {}

const TraceabilityScanner: React.FunctionComponent = () => {
  const [settingsContent, setSettingsContent] = React.useState('')

  const [notificationModalShowState, setNotificationModalShowState] = React.useState(false)
  const [notificationMessage, setNotificationMessage] = React.useState('')
  const [notificationTitle, setNotificationTitle] = React.useState('')
  const [editorFontSize, setEditorFontSize] = React.useState(16)

  const [scanIds, setScanIds] = React.useState([])
  const [selectedScanId, setSelectedScanId] = React.useState('')
  const [scanLog, setScanLog] = React.useState('')
  const [scanLogModalShowState, setScanLogModalShowState] = React.useState(false)

  const auth = useAuth()
  const TRACEABILITY_SCANNER_SETTINGS_ENDPOINT = '/traceability-scanner/settings'
  const TRACEABILITY_SCANNER_ENDPOINT = '/traceability-scanner/scan'
  const TRACEABILITY_SCANNER_LOGS_ENDPOINT = '/traceability-scanner/logs'

  const increaseEditorFont = () => setEditorFontSize((f) => Math.min(f + 2, 40))
  const decreaseEditorFont = () => setEditorFontSize((f) => Math.max(f - 2, 8))

  const toggleNotificationModal = (title: string, message: string) => {
    if (title == '' || message == '') {
      setNotificationModalShowState(false)
      setNotificationMessage('')
      setNotificationTitle('')
    } else {
      setNotificationTitle(title)
      setNotificationMessage(message)
      setNotificationModalShowState(true)
    }
  }

  const onChange = (value) => {
    setSettingsContent(value)
    toggleNotificationModal('', '')
  }

  const onEditorDidMount = () => {
    //
    loadSettings()
  }

  const loadSettings = () => {
    toggleNotificationModal('', '')
    setSettingsContent('')

    let url = Constants.API_BASE_URL + TRACEABILITY_SCANNER_SETTINGS_ENDPOINT
    url += '?user-id=' + auth.userId
    url += '&token=' + auth.token
    fetch(url)
      .then((res) => {
        if (!res.ok) {
          toggleNotificationModal('Error', 'Error loading Settings')
          return ''
        } else {
          return res.json()
        }
      })
      .then((data) => {
        setSettingsContent(data['content'])
      })
      .catch((err) => {
        console.log(err.message)
      })
  }

  const saveSettings = () => {
    toggleNotificationModal('', '')

    const url = Constants.API_BASE_URL + TRACEABILITY_SCANNER_SETTINGS_ENDPOINT
    const data = { content: settingsContent, 'user-id': auth.userId, token: auth.token }
    fetch(url, {
      method: 'PUT',
      headers: Constants.JSON_HEADER,
      body: JSON.stringify(data)
    })
      .then((response) => {
        if (response.status !== 200) {
          toggleNotificationModal('Error', response.statusText)
        } else {
          loadSettings()
          toggleNotificationModal('Success', 'Settings saved')
        }
      })
      .catch((err) => {
        toggleNotificationModal('Error', err.toString())
        console.log(err.toString())
      })
  }

  const scanTraceability = () => {
    toggleNotificationModal('', '')

    const url = Constants.API_BASE_URL + TRACEABILITY_SCANNER_ENDPOINT
    const data = { 'user-id': auth.userId, token: auth.token }
    fetch(url, {
      method: 'POST',
      headers: Constants.JSON_HEADER,
      body: JSON.stringify(data)
    })
      .then((response) => {
        if (!response.ok) {
          throw new Error(response.statusText)
        }
        return response.json()
      })
      .then((data) => {
        loadSettings()
        const logfile = data && data['logfile'] ? data['logfile'] : ''
        const msg = logfile ? 'Traceability scan started. Log file: ' + logfile : 'Traceability scan started.'
        toggleNotificationModal('Success', msg)
        listTraceabilityScans()
      })
      .catch((err) => {
        toggleNotificationModal('Error', err.toString())
        console.log(err.toString())
      })
  }

  const listTraceabilityScans = () => {
    let url = Constants.API_BASE_URL + TRACEABILITY_SCANNER_ENDPOINT
    url += '?user-id=' + auth.userId
    url += '&token=' + auth.token
    fetch(url, {
      method: 'GET',
      headers: Constants.JSON_HEADER
    })
      .then((res) => res.json())
      .then((data) => {
        setScanIds(data['content'])
      })
      .catch((err) => {
        console.log(err.message)
      })
  }

  const getTraceabilityScanLog = (scanId: string) => {
    toggleNotificationModal('', '')

    let url = Constants.API_BASE_URL + TRACEABILITY_SCANNER_LOGS_ENDPOINT
    url += '?user-id=' + auth.userId
    url += '&token=' + auth.token
    url += '&scan-id=' + scanId
    fetch(url, {
      method: 'GET',
      headers: Constants.JSON_HEADER
    })
      .then((res) => res.json())
      .then((data) => {
        setScanLog(data['content'])
        setScanLogModalShowState(true)
      })
      .catch((err) => {
        console.log(err.message)
      })
  }

  React.useEffect(() => {
    listTraceabilityScans()
  }, [])

  React.useEffect(() => {
    if (selectedScanId) {
      getTraceabilityScanLog(selectedScanId)
    }
  }, [selectedScanId])

  return (
    <PageSection isFilled>
      <Form>
        <FormGroup label='Select a traceability scan to get the log' fieldId='select-traceability-scanner-logs'>
          <FormSelect id='select-traceability-scanner-logs' value={selectedScanId} onChange={(_event, value) => setSelectedScanId(value)}>
            <FormSelectOption value='' label='Select a scan' />
            {scanIds.map((scanId) => (
              <FormSelectOption key={scanId} value={scanId} label={scanId} />
            ))}
          </FormSelect>
        </FormGroup>

        <FormGroup label='Traceability scanner configuration' fieldId='traceability-scanner-config'>
          <Flex>
            <FlexItem>
              <Button onClick={decreaseEditorFont} variant='secondary'>
                Font −
              </Button>
            </FlexItem>
            <FlexItem>
              <Button onClick={increaseEditorFont} variant='secondary'>
                Font +
              </Button>
            </FlexItem>
          </Flex>
          <br />

          <Editor
            wrapperProps={{ id: 'traceability-scanner-config' }}
            language={'yaml'}
            value={settingsContent}
            onChange={onChange}
            theme={'vs-dark'}
            onMount={onEditorDidMount}
            height='800px'
            options={{
              fontSize: editorFontSize
            }}
          />
        </FormGroup>
      </Form>

      <Divider />
      <br />

      <Flex>
        <FlexItem>
          <Button
            onClick={() => {
              loadSettings()
            }}
          >
            Reload
          </Button>
        </FlexItem>
        <FlexItem>
          <Button
            onClick={() => {
              saveSettings()
            }}
          >
            Save
          </Button>
        </FlexItem>
        <FlexItem>
          <Tooltip content='Scan using saved configuration file. It will skip temporary changes.'>
            <Button
              isDisabled={!settingsContent}
              onClick={() => {
                scanTraceability()
              }}
            >
              Scan (With saved configuration)
            </Button>
          </Tooltip>
        </FlexItem>
      </Flex>

      <ModalTraceabilityLog
        listTraceabilityScans={listTraceabilityScans}
        modalLogContent={scanLog}
        modalLogFilename={selectedScanId}
        modalShowState={scanLogModalShowState}
        setModalShowState={setScanLogModalShowState}
        toggleNotificationModal={toggleNotificationModal}
      />
      <ModalNotification
        modalShowState={notificationModalShowState}
        setModalShowState={setNotificationModalShowState}
        modalTitle={notificationTitle}
        modalMessage={notificationMessage}
      />
    </PageSection>
  )
}

export { TraceabilityScanner }
