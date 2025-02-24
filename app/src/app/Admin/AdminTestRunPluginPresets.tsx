import * as React from 'react'
import * as Constants from '../Constants/constants'
import { Button, Divider, Flex, FlexItem, Hint, HintBody, PageSection } from '@patternfly/react-core'
import { Editor } from '@monaco-editor/react'
import { useAuth } from '../User/AuthProvider'
export interface AdminTestRunPluginPresetsProps {}

const AdminTestRunPluginPresets: React.FunctionComponent = () => {
  const [presetsContent, setPresetsContent] = React.useState('')
  const [messageValue, setMessageValue] = React.useState('')
  const auth = useAuth()
  const ADMIN_PRESETS_PLUGINS_ENDPOINT = '/admin/test-run-plugins-presets'

  const onChange = (value) => {
    setPresetsContent(value)
    setMessageValue('')
  }

  const onEditorDidMount = () => {
    //
    loadPresetsPlugins()
  }

  const loadPresetsPlugins = () => {
    setMessageValue('')
    setPresetsContent('')

    let url = Constants.API_BASE_URL + ADMIN_PRESETS_PLUGINS_ENDPOINT
    url += '?user-id=' + auth.userId
    url += '&token=' + auth.token
    fetch(url)
      .then((res) => {
        if (!res.ok) {
          setMessageValue('Error loading Test Run Plugins Presets')
          return ''
        } else {
          return res.json()
        }
      })
      .then((data) => {
        setPresetsContent(data['content'])
      })
      .catch((err) => {
        console.log(err.message)
      })
  }

  const savePresetsPlugins = () => {
    setMessageValue('')

    const url = Constants.API_BASE_URL + ADMIN_PRESETS_PLUGINS_ENDPOINT
    const data = { content: presetsContent, 'user-id': auth.userId, token: auth.token }
    fetch(url, {
      method: 'PUT',
      headers: Constants.JSON_HEADER,
      body: JSON.stringify(data)
    })
      .then((response) => {
        if (response.status !== 200) {
          setMessageValue(response.statusText)
        } else {
          loadPresetsPlugins()
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
        value={presetsContent}
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
              loadPresetsPlugins()
            }}
          >
            Reload
          </Button>
        </FlexItem>
        <FlexItem>
          <Button
            onClick={() => {
              savePresetsPlugins()
            }}
          >
            Save
          </Button>
        </FlexItem>
      </Flex>
    </PageSection>
  )
}

export { AdminTestRunPluginPresets }
