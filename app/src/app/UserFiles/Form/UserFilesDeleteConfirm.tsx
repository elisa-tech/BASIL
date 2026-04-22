import React from 'react'
import * as Constants from '../../Constants/constants'
import { Hint, HintBody } from '@patternfly/react-core'
import { useAuth } from '../../User/AuthProvider'

export interface UserFilesDeleteConfirmProps {
  modalFormSubmitState
  setModalSubmit
  modalRelativePath
  modalFileName
  loadFiles: () => void
  closeModal: () => void
}

export const UserFilesDeleteConfirm: React.FunctionComponent<UserFilesDeleteConfirmProps> = ({
  modalFormSubmitState = 'waiting',
  setModalSubmit,
  modalRelativePath,
  modalFileName,
  loadFiles,
  closeModal
}: UserFilesDeleteConfirmProps) => {
  const auth = useAuth()
  const [messageValue, setMessageValue] = React.useState('')

  React.useEffect(() => {
    if (modalFormSubmitState == 'submitted') {
      handleSubmit()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [modalFormSubmitState])

  const handleSubmit = () => {
    setModalSubmit('waiting')
    setMessageValue('')

    Constants.deleteUserFile(
      auth,
      modalRelativePath.current,
      () => {
        loadFiles()
        closeModal()
      },
      (err) => setMessageValue(err)
    )
  }

  return (
    <div>
      <p style={{ marginBottom: '16px' }}>
        Are you sure you want to delete <strong>{modalFileName.current}</strong>?
      </p>
      <p style={{ color: '#6a6e73' }}>This action cannot be undone. If this is a folder, all contents will be permanently deleted.</p>
      {messageValue ? (
        <Hint>
          <HintBody>{messageValue}</HintBody>
        </Hint>
      ) : (
        ''
      )}
    </div>
  )
}
