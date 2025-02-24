import React from 'react'
import { Button, Hint, HintBody, Modal, ModalVariant } from '@patternfly/react-core'
import * as Constants from '@app/Constants/constants'

export interface APIDeleteModalProps {
  api
  modalShowState
  setModalShowState
  modalTitle
  modalDescription
}

export const APIDeleteModal: React.FunctionComponent<APIDeleteModalProps> = ({
  api,
  modalShowState = false,
  setModalShowState,
  modalTitle = '',
  modalDescription = ''
}: APIDeleteModalProps) => {
  const [isModalOpen, setIsModalOpen] = React.useState(false)
  const [messageValue, setMessageValue] = React.useState('')

  const handleModalToggle = () => {
    const new_state = !modalShowState
    setModalShowState(new_state)
    setIsModalOpen(new_state)
  }

  React.useEffect(() => {
    setIsModalOpen(modalShowState)
    if (modalShowState == false) {
      setMessageValue('')
    }
  }, [modalShowState])

  const deleteApi = () => {
    const data = {
      'api-id': api.id,
      api: api.api,
      library: api.library,
      'library-version': api.library_version,
      category: api.category,
      'raw-specification-url': api.raw_specification_url,
      'implementation-file': api.implementation_file,
      'implementation-file-from-row': api.implementation_file_from_row,
      'implementation-file-to-row': api.implementation_file_to_row,
      tags: api.tags
    }
    fetch(Constants.API_BASE_URL + '/apis', {
      method: 'DELETE',
      headers: Constants.JSON_HEADER,
      body: JSON.stringify(data)
    })
      .then((response) => {
        if (response.status !== 200) {
          setMessageValue(response.statusText)
        } else {
          location.reload()
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
        bodyAriaLabel='APIDeleteModal'
        aria-label='api delete modal'
        tabIndex={0}
        variant={ModalVariant.large}
        title={modalTitle}
        description={modalDescription}
        isOpen={isModalOpen}
        onClose={handleModalToggle}
        actions={[
          <Button key='confirm' id='btn-api-delete-confirm' variant='primary' onClick={deleteApi}>
            Confirm
          </Button>,
          <Button id='btn-api-delete-cancel' key='cancel' variant='link' onClick={handleModalToggle}>
            Cancel
          </Button>
        ]}
      >
        {messageValue ? (
          <Hint>
            <HintBody>{messageValue}</HintBody>
          </Hint>
        ) : (
          <span></span>
        )}
      </Modal>
    </React.Fragment>
  )
}
