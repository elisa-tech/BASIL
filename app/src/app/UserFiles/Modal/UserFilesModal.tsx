import React from 'react'
import { Button, Modal, ModalVariant } from '@patternfly/react-core'
import { UserFilesAddForm } from '../Form/UserFilesAddForm'
import { UserFilesEditForm } from '../Form/UserFilesEditForm'
import { UserFilesCreateFolderForm } from '../Form/UserFilesCreateFolderForm'
import { UserFilesRenameForm } from '../Form/UserFilesRenameForm'
import { UserFilesMoveForm } from '../Form/UserFilesMoveForm'
import { UserFilesDeleteConfirm } from '../Form/UserFilesDeleteConfirm'
import * as Constants from '@app/Constants/constants'

export interface UserFilesModalProps {
  modalAction
  modalFileName
  modalRelativePath
  modalShowState
  setModalShowState
  currentPath: string
  loadFiles: () => void
}

const MODAL_TITLES = {
  add: 'Add a new File',
  edit: 'Edit File',
  'create-folder': 'Create Folder',
  rename: 'Rename',
  move: 'Move',
  delete: 'Delete'
}

export const UserFilesModal: React.FunctionComponent<UserFilesModalProps> = ({
  modalAction,
  modalFileName,
  modalRelativePath,
  modalShowState = false,
  setModalShowState,
  currentPath,
  loadFiles
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
    if (!new_state) {
      setFileName('')
      setFileContent('')
      setModalFormSubmitState('waiting')
    }
  }

  React.useEffect(() => {
    setIsModalOpen(modalShowState)
  }, [modalShowState])

  const action = modalAction.current
  const title = MODAL_TITLES[action] || 'User File'

  const confirmLabel = action === 'delete' ? 'Delete' : 'Confirm'
  const confirmVariant = action === 'delete' ? 'danger' : 'primary'

  const renderForm = () => {
    switch (action) {
      case 'add':
        return (
          <UserFilesAddForm
            modalFormSubmitState={modalFormSubmitState}
            setModalSubmit={setModalSubmit}
            fileName={fileName}
            fileContent={fileContent}
            setFileName={setFileName}
            setFileContent={setFileContent}
            currentPath={currentPath}
            loadFiles={loadFiles}
            closeModal={handleModalToggle}
          />
        )
      case 'edit':
        return (
          <UserFilesEditForm
            modalFormSubmitState={modalFormSubmitState}
            setModalSubmit={setModalSubmit}
            modalFileName={modalRelativePath}
          />
        )
      case 'create-folder':
        return (
          <UserFilesCreateFolderForm
            modalFormSubmitState={modalFormSubmitState}
            setModalSubmit={setModalSubmit}
            currentPath={currentPath}
            loadFiles={loadFiles}
            closeModal={handleModalToggle}
          />
        )
      case 'rename':
        return (
          <UserFilesRenameForm
            modalFormSubmitState={modalFormSubmitState}
            setModalSubmit={setModalSubmit}
            modalRelativePath={modalRelativePath}
            modalFileName={modalFileName}
            loadFiles={loadFiles}
            closeModal={handleModalToggle}
          />
        )
      case 'move':
        return (
          <UserFilesMoveForm
            modalFormSubmitState={modalFormSubmitState}
            setModalSubmit={setModalSubmit}
            modalRelativePath={modalRelativePath}
            modalFileName={modalFileName}
            loadFiles={loadFiles}
            closeModal={handleModalToggle}
          />
        )
      case 'delete':
        return (
          <UserFilesDeleteConfirm
            modalFormSubmitState={modalFormSubmitState}
            setModalSubmit={setModalSubmit}
            modalRelativePath={modalRelativePath}
            modalFileName={modalFileName}
            loadFiles={loadFiles}
            closeModal={handleModalToggle}
          />
        )
      default:
        return null
    }
  }

  return (
    <React.Fragment>
      <Modal
        width={Constants.MODAL_WIDTH}
        bodyAriaLabel='UserFilesModal'
        aria-label='user files modal'
        tabIndex={0}
        variant={ModalVariant.large}
        title={title}
        description={''}
        isOpen={isModalOpen}
        onClose={handleModalToggle}
        actions={[
          <Button
            key='confirm'
            id='btn-user-file-modal-confirm'
            variant={confirmVariant}
            isDisabled={false}
            onClick={() => setModalFormSubmitState('submitted')}
          >
            {confirmLabel}
          </Button>,
          <Button id='btn-user-file-modal-cancel' key='cancel' variant='link' onClick={handleModalToggle}>
            Cancel
          </Button>
        ]}
      >
        {renderForm()}
      </Modal>
    </React.Fragment>
  )
}
