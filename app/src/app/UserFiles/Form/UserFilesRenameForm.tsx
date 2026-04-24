import React from 'react'
import * as Constants from '../../Constants/constants'
import { Form, FormGroup, Hint, HintBody, TextInput } from '@patternfly/react-core'
import { useAuth } from '../../User/AuthProvider'

export interface UserFilesRenameFormProps {
  modalFormSubmitState
  setModalSubmit
  modalRelativePath
  modalFileName
  loadFiles: () => void
  closeModal: () => void
}

export const UserFilesRenameForm: React.FunctionComponent<UserFilesRenameFormProps> = ({
  modalFormSubmitState = 'waiting',
  setModalSubmit,
  modalRelativePath,
  modalFileName,
  loadFiles,
  closeModal
}: UserFilesRenameFormProps) => {
  const auth = useAuth()
  const [newName, setNewName] = React.useState('')
  const [messageValue, setMessageValue] = React.useState('')

  React.useEffect(() => {
    setNewName(modalFileName.current || '')
  }, [modalFileName])

  React.useEffect(() => {
    if (modalFormSubmitState == 'submitted') {
      handleSubmit()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [modalFormSubmitState])

  const handleSubmit = () => {
    setModalSubmit('waiting')
    setMessageValue('')

    if (!newName.trim()) {
      setMessageValue('Name is required')
      return
    }

    const sourcePath = modalRelativePath.current
    const parentDir = sourcePath.includes('/') ? sourcePath.substring(0, sourcePath.lastIndexOf('/')) : ''
    const destination = parentDir ? parentDir + '/' + newName : newName

    if (destination === sourcePath) {
      setMessageValue('New name is the same as the current name')
      return
    }

    Constants.moveUserFile(
      auth,
      sourcePath,
      destination,
      () => {
        loadFiles()
        closeModal()
      },
      (err) => setMessageValue(err)
    )
  }

  return (
    <Form>
      <Hint>
        <HintBody>
          Renaming: <strong>{modalFileName.current}</strong>
        </HintBody>
      </Hint>
      <FormGroup label='New name' isRequired fieldId='input-rename-name'>
        <TextInput
          isRequired
          type='text'
          id='input-rename-name'
          value={newName}
          onChange={(_event, value) => setNewName(value)}
          placeholder='Enter new name'
        />
      </FormGroup>
      {messageValue ? (
        <Hint>
          <HintBody>{messageValue}</HintBody>
        </Hint>
      ) : (
        ''
      )}
    </Form>
  )
}
