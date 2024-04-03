import React from 'react'
import * as Constants from '../../Constants/constants'
import { Button, Hint, HintBody, Modal, ModalVariant } from '@patternfly/react-core'
import { useAuth } from '../../User/AuthProvider'

export interface MappingForkModalProps {
  api
  modalShowState
  setModalShowState
  modalTitle
  modalDescription
  workItemType
  parentType
  relationData
  loadMappingData
}

export const MappingForkModal: React.FunctionComponent<MappingForkModalProps> = ({
  api,
  modalShowState = false,
  setModalShowState,
  modalTitle = '',
  modalDescription = '',
  workItemType,
  parentType,
  relationData,
  loadMappingData
}: MappingForkModalProps) => {
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

  const fork = () => {
    const data = { 'api-id': api.id, 'relation-id': relationData.relation_id, 'user-id': auth.userId, token: auth.token }
    fetch(Constants.API_BASE_URL + '/fork/' + parentType + '/' + workItemType, {
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
        bodyAriaLabel='MappingForkModal'
        aria-label='mapping fork modal'
        tabIndex={0}
        variant={ModalVariant.large}
        title={modalTitle}
        description={modalDescription}
        isOpen={isModalOpen}
        onClose={handleModalToggle}
        actions={[
          <Button key='confirm' variant='primary' onClick={fork}>
            Confirm
          </Button>,
          <Button key='cancel' variant='link' onClick={handleModalToggle}>
            Cancel
          </Button>
        ]}
      >
        {messageValue ? (
          <>
            <Hint>
              <HintBody>{messageValue}</HintBody>
            </Hint>
            <br />
          </>
        ) : (
          ''
        )}
      </Modal>
    </React.Fragment>
  )
}
