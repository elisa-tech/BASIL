import * as React from 'react'
import * as Constants from '@app/Constants/constants'
import { Editor } from '@monaco-editor/react'
import { Button, Flex, FlexItem, Hint, HintBody, Modal, ModalVariant, Text, TextContent, TextVariants } from '@patternfly/react-core'
import { useAuth } from '@app/User/AuthProvider'

export interface TestCaseImplementationModalProps {
  isOpen: boolean
  onClose: () => void
  api: { id: number; permissions?: string }
  testCase: { id: number }
  relationTo: string
  relationId: number
}

export const TestCaseImplementationModal: React.FunctionComponent<TestCaseImplementationModalProps> = ({
  isOpen,
  onClose,
  api,
  testCase,
  relationTo,
  relationId
}: TestCaseImplementationModalProps) => {
  const auth = useAuth()
  const [content, setContent] = React.useState<string>('')
  const [loading, setLoading] = React.useState(false)
  const [error, setError] = React.useState<string | null>(null)
  const [editorFontSize, setEditorFontSize] = React.useState(16)

  const increaseEditorFont = () => setEditorFontSize((f) => Math.min(f + 2, 40))
  const decreaseEditorFont = () => setEditorFontSize((f) => Math.max(f - 2, 8))

  const loadContent = React.useCallback(() => {
    if (!api?.id || !testCase?.id || !relationTo || relationId == null) {
      return
    }
    if (api == null || api.permissions == null || api.permissions.indexOf('r') < 0) {
      return
    }
    setLoading(true)
    setError(null)
    const params = new URLSearchParams()
    params.append('user-id', String(auth.userId))
    params.append('token', auth.token)
    params.append('api-id', String(api.id))
    params.append('relation-id', String(relationId))
    params.append('relation-to', relationTo)
    params.append('test-case-id', String(testCase.id))
    const url = Constants.API_BASE_URL + Constants.API_TEST_CASE_LOCAL_FILE_IMPLEMENTATION_ENDPOINT + '?' + params.toString()
    fetch(url)
      .then((res) => {
        if (!res.ok) {
          if (res.status === 404) {
            return Promise.reject(new Error('Local file implementation not found.'))
          }
          return res.text().then((t) => Promise.reject(new Error(t || res.statusText)))
        }
        return res.text()
      })
      .then((text) => {
        // If the server sent JSON-encoded text (e.g. "\n" as literal), normalize to real newlines
        const normalized =
          typeof text === 'string' && /\\n/.test(text) && !/\n/.test(text)
            ? text.replace(/\\n/g, '\n').replace(/\\r/g, '\r').replace(/\\t/g, '\t')
            : text
        setContent(normalized)
      })
      .catch((err) => {
        setError(err?.message || 'Failed to load implementation.')
        setContent('')
      })
      .finally(() => setLoading(false))
  }, [api?.id, api?.permissions, auth.userId, auth.token, testCase?.id, relationTo, relationId])

  React.useEffect(() => {
    if (isOpen && testCase?.id != null) {
      loadContent()
    }
  }, [isOpen, testCase?.id, loadContent])

  React.useEffect(() => {
    if (!isOpen) {
      setContent('')
      setError(null)
    }
  }, [isOpen])

  return (
    <Modal
      width={Constants.MODAL_WIDTH}
      bodyAriaLabel='TestCaseImplementationModal'
      aria-label='test case implementation modal'
      tabIndex={0}
      variant={ModalVariant.large}
      title='Test Case Implementation (local file)'
      isOpen={isOpen}
      onClose={onClose}
    >
      {error && (
        <>
          <Hint>
            <HintBody>{error}</HintBody>
          </Hint>
          <br />
        </>
      )}
      {loading ? (
        <TextContent>
          <Text component={TextVariants.p}>Loading…</Text>
        </TextContent>
      ) : (
        <>
          <Flex>
            <FlexItem>
              <Button onClick={decreaseEditorFont} variant='secondary'>
                Font −
              </Button>
            </FlexItem>
            <FlexItem>
              <Button onClick={increaseEditorFont} variant='secondary'>
                Font +
              </Button>
            </FlexItem>
          </Flex>
          <br />

          <Editor
            height='500px'
            theme='vs-dark'
            value={content}
            language='plaintext'
            options={{
              readOnly: true,
              domReadOnly: true,
              fontSize: editorFontSize,
              minimap: { enabled: false }
            }}
          />
        </>
      )}
    </Modal>
  )
}
