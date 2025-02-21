import React from 'react'
import * as Constants from '@app/Constants/constants'
import { Button, Hint, HintBody, Modal, ModalVariant } from '@patternfly/react-core'
import { useAuth } from '../../User/AuthProvider'

export interface MappingDeleteModalProps {
  api
  modalShowState: boolean
  setModalShowState
  modalTitle
  modalDescription
  workItemType
  parentType
  relationData
  loadMappingData
}

export const MappingDeleteModal: React.FunctionComponent<MappingDeleteModalProps> = ({
  api,
  modalShowState = false,
  setModalShowState,
  modalTitle = '',
  modalDescription = '',
  workItemType,
  parentType,
  relationData,
  loadMappingData
}: MappingDeleteModalProps) => {
  const auth = useAuth()
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

  const deleteMapping = () => {
    const data = { 'api-id': api.id, 'relation-id': relationData.relation_id, 'user-id': auth.userId, token: auth.token }

    fetch(Constants.API_BASE_URL + '/mapping/' + parentType + '/' + workItemType + 's', {
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
          loadMappingData(Constants.force_reload)
          handleModalToggle()
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
        bodyAriaLabel='MappingDeleteModal'
        aria-label='mapping delete modal'
        tabIndex={0}
        variant={ModalVariant.large}
        title={modalTitle}
        description={modalDescription}
        isOpen={isModalOpen}
        onClose={handleModalToggle}
        actions={[
          <Button id='btn-mapping-delete-confirm' key='confirm' variant='primary' onClick={deleteMapping}>
            Confirm
          </Button>,
          <Button id='btn-mapping-delete-cancel' key='cancel' variant='link' onClick={handleModalToggle}>
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
