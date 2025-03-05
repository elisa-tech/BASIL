import * as React from 'react'
import * as Constants from '../Constants/constants'
import { Button, Divider, Flex, FlexItem, Hint, HintBody, PageSection } from '@patternfly/react-core'
import { Editor } from '@monaco-editor/react'
import { useAuth } from '../User/AuthProvider'
export interface AdminSettingsProps {}

const AdminSettings: React.FunctionComponent = () => {
  const [settingsContent, setSettingsContent] = React.useState('')
  const [messageValue, setMessageValue] = React.useState('')
  const auth = useAuth()
  const ADMIN_SETTINGS_ENDPOINT = '/admin/settings'

  const onChange = (value) => {
    setSettingsContent(value)
    setMessageValue('')
  }

  const onEditorDidMount = () => {
    //
    loadSettings()
  }

  const loadSettings = () => {
    setMessageValue('')
    setSettingsContent('')

    let url = Constants.API_BASE_URL + ADMIN_SETTINGS_ENDPOINT
    url += '?user-id=' + auth.userId
    url += '&token=' + auth.token
    fetch(url)
      .then((res) => {
        if (!res.ok) {
          setMessageValue('Error loading Settings')
          return ''
        } else {
          return res.json()
        }
      })
      .then((data) => {
        setSettingsContent(data['content'])
      })
      .catch((err) => {
        console.log(err.message)
      })
  }

  const saveSettings = () => {
    setMessageValue('')

    const url = Constants.API_BASE_URL + ADMIN_SETTINGS_ENDPOINT
    const data = { content: settingsContent, 'user-id': auth.userId, token: auth.token }
    fetch(url, {
      method: 'PUT',
      headers: Constants.JSON_HEADER,
      body: JSON.stringify(data)
    })
      .then((response) => {
        if (response.status !== 200) {
          setMessageValue(response.statusText)
        } else {
          loadSettings()
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
        value={settingsContent}
        onChange={onChange}
        theme={'vs-dark'}
        onMount={onEditorDidMount}
        height='800px'
        options={{
          fontSize: 20
        }}
      />

      <Divider />
      <br />

      <Flex>
        <FlexItem>
          <Button
            onClick={() => {
              loadSettings()
            }}
          >
            Reload
          </Button>
        </FlexItem>
        <FlexItem>
          <Button
            onClick={() => {
              saveSettings()
            }}
          >
            Save
          </Button>
        </FlexItem>
      </Flex>
    </PageSection>
  )
}

export { AdminSettings }
