import React from 'react'
import { Button, Modal, ModalVariant } from '@patternfly/react-core'
import { UserFilesAddForm } from '../Form/UserFilesAddForm'
import { UserFilesEditForm } from '../Form/UserFilesEditForm'

export interface UserFilesModalProps {
  modalAction
  modalFileName
  modalShowState
  setModalShowState
}

export const UserFilesModal: React.FunctionComponent<UserFilesModalProps> = ({
  modalAction,
  modalFileName,
  modalShowState = false,
  setModalShowState
}: UserFilesModalProps) => {
  const [isModalOpen, setIsModalOpen] = React.useState(false)
  const [modalFormSubmitState, setModalFormSubmitState] = React.useState('waiting')
  const [fileContent, setFileContent] = React.useState('')
  const [fileName, setFileName] = React.useState('')

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
        bodyAriaLabel='UserFilesModal'
        aria-label='user files modal'
        tabIndex={0}
        variant={ModalVariant.large}
        title='Add a new File'
        description={''}
        isOpen={isModalOpen}
        onClose={handleModalToggle}
        actions={[
          <Button
            key='confirm'
            id='btn-user-file-add-confirm'
            variant='primary'
            isDisabled={false}
            onClick={() => setModalFormSubmitState('submitted')}
          >
            Confirm
          </Button>,
          <Button id='btn-user-file-add-cancel' key='cancel' variant='link' onClick={handleModalToggle}>
            Cancel
          </Button>
        ]}
      >
        {modalAction.current == 'add' ? (
          <UserFilesAddForm
            modalFormSubmitState={modalFormSubmitState}
            setModalSubmit={setModalSubmit}
            fileName={fileName}
            fileContent={fileContent}
            setFileName={setFileName}
            setFileContent={setFileContent}
          />
        ) : (
          <UserFilesEditForm modalFormSubmitState={modalFormSubmitState} setModalSubmit={setModalSubmit} modalFileName={modalFileName} />
        )}
      </Modal>
    </React.Fragment>
  )
}
