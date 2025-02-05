import React from 'react'
import * as Constants from '../../Constants/constants'
import { DropEvent, FileUpload } from '@patternfly/react-core'
import { Form, Hint, HintBody } from '@patternfly/react-core'
import { useAuth } from '../../User/AuthProvider'

export interface UserFilesAddFormProps {
  modalFormSubmitState
  setModalSubmit
  fileName
  fileContent
  setFileName
  setFileContent
}

export const UserFilesAddForm: React.FunctionComponent<UserFilesAddFormProps> = ({
  modalFormSubmitState = 'waiting',
  setModalSubmit,
  fileName,
  fileContent,
  setFileName,
  setFileContent
}: UserFilesAddFormProps) => {
  const auth = useAuth()
  const [messageValue, setMessageValue] = React.useState('')

  // File Upload
  const [isLoading, setIsLoading] = React.useState(false)

  /* eslint-disable  @typescript-eslint/no-explicit-any */
  const handleFileInputChange = (_: any, file: File) => {
    setFileName(file.name)
  }

  const handleTextChange = (_event: React.ChangeEvent<HTMLTextAreaElement>, value: string) => {
    setFileContent(value)
  }

  const handleDataChange = (_event: DropEvent, value: string) => {
    setFileContent(value)
  }

  const handleClear = () => {
    setFileName('')
    setFileContent('')
    setMessageValue('Data erased')
  }

  const handleFileReadStarted = () => {
    setIsLoading(true)
  }

  const handleFileReadFinished = () => {
    setIsLoading(false)
  }

  React.useEffect(() => {
    if (modalFormSubmitState == 'submitted') {
      handleSubmit()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [modalFormSubmitState])

  const handleSubmit = () => {
    setModalSubmit('waiting')
    setMessageValue('')

    const data = {
      'user-id': auth.userId,
      token: auth.token,
      filename: fileName,
      filecontent: fileContent
    }

    fetch(Constants.API_BASE_URL + '/user/files', {
      method: 'POST',
      headers: Constants.JSON_HEADER,
      body: JSON.stringify(data)
    })
      .then((response) => {
        if (response.status !== 200) {
          setMessageValue(response.statusText)
        } else {
          window.location.reload()
        }
      })
      .catch((err) => {
        setMessageValue(err.toString())
      })
  }

  return (
    <Form>
      <FileUpload
        id='user-file-upload'
        type='text'
        hideDefaultPreview={false}
        value={fileContent}
        filename={fileName}
        filenamePlaceholder='Drag and drop a file or upload one'
        onFileInputChange={handleFileInputChange}
        onDataChange={handleDataChange}
        onTextChange={handleTextChange}
        onReadStarted={handleFileReadStarted}
        onReadFinished={handleFileReadFinished}
        onClearClick={handleClear}
        isLoading={isLoading}
        allowEditingUploadedText={false}
        browseButtonText='Upload'
      />
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
    </Form>
  )
}
