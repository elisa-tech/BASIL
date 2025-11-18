import React from 'react'
import { Button, CodeBlock, CodeBlockCode, Modal, ModalVariant } from '@patternfly/react-core'
import * as Constants from '@app/Constants/constants'
import { useAuth } from '@app/User/AuthProvider'
import { AutoRefresh } from '@app/Common/AutoRefresh/AutoRefresh'

export interface ModalTraceabilityLogProps {
  modalLogContent
  modalLogFilename
  modalShowState
  listTraceabilityScans
  setModalShowState
  toggleNotificationModal
  getTraceabilityScanLog
}

export const ModalTraceabilityLog: React.FunctionComponent<ModalTraceabilityLogProps> = ({
  modalLogContent,
  modalLogFilename,
  modalShowState = false,
  listTraceabilityScans,
  setModalShowState,
  toggleNotificationModal,
  getTraceabilityScanLog
}: ModalTraceabilityLogProps) => {
  const [isModalOpen, setIsModalOpen] = React.useState(false)

  const TRACEABILITY_SCANNER_LOGS_ENDPOINT = '/traceability-scanner/logs'
  const auth = useAuth()

  const handleModalToggle = () => {
    const new_state = !modalShowState
    setModalShowState(new_state)
    setIsModalOpen(new_state)
  }

  React.useEffect(() => {
    setIsModalOpen(modalShowState)
  }, [modalShowState])

  const deleteTraceabilityScanLog = (scanId: string) => {
    toggleNotificationModal('', '')

    let url = Constants.API_BASE_URL + TRACEABILITY_SCANNER_LOGS_ENDPOINT
    const data = {
      'user-id': auth.userId,
      token: auth.token,
      'scan-id': scanId
    }
    fetch(url, {
      method: 'DELETE',
      headers: Constants.JSON_HEADER,
      body: JSON.stringify(data)
    })
      .then(async (res) => {
        if (!res.ok) {
          throw new Error(res.statusText)
        }
        const contentType = res.headers.get('content-type') || ''
        const text = await res.text()
        const data = contentType.includes('application/json') && text ? JSON.parse(text) : {}
        return data
      })
      .then((data) => {
        toggleNotificationModal(
          'Result',
          data && data['status'] == 'success' ? 'Traceability scan log deleted successfully' : 'Error deleting traceability scan log'
        )
        listTraceabilityScans()
        setModalShowState(false)
      })
      .catch((err) => {
        toggleNotificationModal('Error', err.toString())
        console.log(err.toString())
      })
  }

  return (
    <React.Fragment>
      <Modal
        width={Constants.MODAL_WIDTH}
        bodyAriaLabel='ModalTraceabilityLog'
        aria-label='modal traceability log'
        tabIndex={0}
        variant={ModalVariant.large}
        title='Traceability Scan Log'
        description={''}
        isOpen={isModalOpen}
        onClose={handleModalToggle}
        actions={[
          <Button
            id='btn-traceability-scan-delete-log-file'
            key='delete'
            variant='link'
            onClick={() => deleteTraceabilityScanLog(modalLogFilename)}
          >
            Delete log file
          </Button>,
          <Button id='btn-traceability-scan-close' key='close' variant='link' onClick={handleModalToggle}>
            Close
          </Button>
        ]}
      >
        <AutoRefresh loadRows={() => getTraceabilityScanLog(modalLogFilename)} showCountdown={true} />
        <br />
        <br />
        <CodeBlock>
          <CodeBlockCode>{modalLogContent}</CodeBlockCode>
        </CodeBlock>
      </Modal>
    </React.Fragment>
  )
}
