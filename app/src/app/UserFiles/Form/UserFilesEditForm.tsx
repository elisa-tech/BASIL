import * as React from 'react'
import * as Constants from '@app/Constants/constants'
import { Divider, Hint, HintBody, PageSection } from '@patternfly/react-core'
import { Editor } from '@monaco-editor/react'
import { useAuth } from '@app/User/AuthProvider'

export interface UserFilesEditFormProps {
  modalFormSubmitState
  setModalSubmit
  modalFileName
}

export const UserFilesEditForm: React.FunctionComponent<UserFilesEditFormProps> = ({
  modalFormSubmitState = 'waiting',
  setModalSubmit,
  modalFileName
}: UserFilesEditFormProps) => {
  const [fileContent, setFileContent] = React.useState('')
  const [messageValue, setMessageValue] = React.useState('')
  const auth = useAuth()

  const onChange = (value) => {
    setFileContent(value)
    setMessageValue('')
  }

  const onEditorDidMount = () => {
    //
    if (modalFileName) {
      Constants.loadFileContent(auth, modalFileName.current, setMessageValue, setFileContent)
    }
  }

  React.useEffect(() => {
    if (modalFormSubmitState == 'submitted') {
      saveFileContent()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [modalFormSubmitState])

  const saveFileContent = () => {
    setModalSubmit('waiting')
    setMessageValue('')

    const url = Constants.API_BASE_URL + Constants.API_USER_FILES_CONTENT_ENDPOINT
    const data = {
      filename: modalFileName.current,
      filecontent: fileContent,
      'user-id': auth.userId,
      token: auth.token
    }
    fetch(url, {
      method: 'PUT',
      headers: Constants.JSON_HEADER,
      body: JSON.stringify(data)
    })
      .then((response) => {
        if (response.status !== 200) {
          setMessageValue(response.statusText)
        } else {
          if (modalFileName) {
            Constants.loadFileContent(auth, modalFileName.current, setMessageValue, setFileContent)
          }
          setMessageValue('SAVED')
        }
      })
      .catch((err) => {
        setMessageValue(err.toString())
        console.log(err.toString())
      })
  }

  return (
    <PageSection isFilled>
      <div>
        {messageValue ? (
          <>
            <Divider />
            <Hint>
              <HintBody>{messageValue}</HintBody>
            </Hint>
            <br />
          </>
        ) : (
          ''
        )}
      </div>

      <Editor
        language={'yaml'}
        value={fileContent}
        onChange={onChange}
        theme={'vs-dark'}
        onMount={onEditorDidMount}
        height='800px'
        options={{
          fontSize: 20
        }}
      />
    </PageSection>
  )
}
