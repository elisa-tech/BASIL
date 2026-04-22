import React from 'react'
import * as Constants from '../../Constants/constants'
import { Form, FormGroup, Hint, HintBody, TextInput } from '@patternfly/react-core'
import { useAuth } from '../../User/AuthProvider'

export interface UserFilesCreateFolderFormProps {
  modalFormSubmitState
  setModalSubmit
  currentPath: string
  loadFiles: () => void
  closeModal: () => void
}

export const UserFilesCreateFolderForm: React.FunctionComponent<UserFilesCreateFolderFormProps> = ({
  modalFormSubmitState = 'waiting',
  setModalSubmit,
  currentPath,
  loadFiles,
  closeModal
}: UserFilesCreateFolderFormProps) => {
  const auth = useAuth()
  const [folderName, setFolderName] = React.useState('')
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

    if (!folderName.trim()) {
      setMessageValue('Folder name is required')
      return
    }

    const fullPath = currentPath ? currentPath + '/' + folderName : folderName

    Constants.createUserFolder(
      auth,
      fullPath,
      () => {
        loadFiles()
        closeModal()
      },
      (err) => setMessageValue(err)
    )
  }

  return (
    <Form>
      {currentPath && (
        <Hint>
          <HintBody>Creating folder in: {currentPath}/</HintBody>
        </Hint>
      )}
      <FormGroup label='Folder name' isRequired fieldId='input-create-folder-name'>
        <TextInput
          isRequired
          type='text'
          id='input-create-folder-name'
          value={folderName}
          onChange={(_event, value) => setFolderName(value)}
          placeholder='Enter folder name'
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
