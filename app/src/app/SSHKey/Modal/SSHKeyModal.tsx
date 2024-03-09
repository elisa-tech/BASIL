import React from 'react'
import { Button, Modal, ModalVariant } from '@patternfly/react-core'
import { SSHKeyForm } from '../Form/SSHKeyForm'

export interface SSHKeyModalProps {
  modalShowState
  setModalShowState
}

export const SSHKeyModal: React.FunctionComponent<SSHKeyModalProps> = ({ modalShowState = false, setModalShowState }: SSHKeyModalProps) => {
  const [isModalOpen, setIsModalOpen] = React.useState(false)
  const [modalFormSubmitState, setModalFormSubmitState] = React.useState('waiting')

  const setModalSubmit = (state) => {
    setModalFormSubmitState(state || 'waiting')
  }

  const handleModalToggle = () => {
    const new_state = !modalShowState
    setModalShowState(new_state)
    setIsModalOpen(new_state)
  }

  React.useEffect(() => {
    setIsModalOpen(modalShowState)
  }, [modalShowState])

  return (
    <React.Fragment>
      <Modal
        bodyAriaLabel='Scrollable modal content'
        tabIndex={0}
        variant={ModalVariant.large}
        title={'Add a new SSH Key'}
        description={''}
        isOpen={isModalOpen}
        onClose={handleModalToggle}
        actions={[
          <Button
            key='confirm'
            id='btn-user-ssh-key-add-confirm'
            variant='primary'
            isDisabled={false}
            onClick={() => setModalFormSubmitState('submitted')}
          >
            Confirm
          </Button>,
          <Button id='btn-user-ssh-key-add-cancel' key='cancel' variant='link' onClick={handleModalToggle}>
            Cancel
          </Button>
        ]}
      >
        <SSHKeyForm modalFormSubmitState={modalFormSubmitState} setModalSubmit={setModalSubmit} />
      </Modal>
    </React.Fragment>
  )
}
