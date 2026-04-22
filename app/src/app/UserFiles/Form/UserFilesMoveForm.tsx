import React from 'react'
import * as Constants from '../../Constants/constants'
import { Form, FormGroup, Hint, HintBody, TextInput } from '@patternfly/react-core'
import { useAuth } from '../../User/AuthProvider'

export interface UserFilesMoveFormProps {
  modalFormSubmitState
  setModalSubmit
  modalRelativePath
  modalFileName
  loadFiles: () => void
  closeModal: () => void
}

export const UserFilesMoveForm: React.FunctionComponent<UserFilesMoveFormProps> = ({
  modalFormSubmitState = 'waiting',
  setModalSubmit,
  modalRelativePath,
  modalFileName,
  loadFiles,
  closeModal
}: UserFilesMoveFormProps) => {
  const auth = useAuth()
  const [destinationFolder, setDestinationFolder] = React.useState('')
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

    const sourcePath = modalRelativePath.current
    const fileName = modalFileName.current
    const destination = destinationFolder.trim() ? destinationFolder.trim() + '/' + fileName : fileName

    if (destination === sourcePath) {
      setMessageValue('Destination is the same as the current location')
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
          Moving: <strong>{modalRelativePath.current}</strong>
        </HintBody>
      </Hint>
      <FormGroup label='Destination folder' fieldId='input-move-destination'>
        <TextInput
          type='text'
          id='input-move-destination'
          value={destinationFolder}
          onChange={(_event, value) => setDestinationFolder(value)}
          placeholder='e.g. folder/subfolder (empty for root)'
        />
      </FormGroup>
      <Hint>
        <HintBody>Leave empty to move to root. Use &quot;/&quot; to separate nested folders.</HintBody>
      </Hint>
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
