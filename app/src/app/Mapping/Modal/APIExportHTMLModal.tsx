import React from 'react'
import { useAuth } from '@app/User/AuthProvider'
import * as Constants from '@app/Constants/constants'
import {
  Button,
  ClipboardCopyButton,
  CodeBlock,
  CodeBlockAction,
  CodeBlockCode,
  Flex,
  FlexItem,
  Modal,
  ModalVariant,
  Tab,
  TabContent,
  TabContentBody,
  Tabs,
  TabTitleText
} from '@patternfly/react-core'

export interface APIExportHTMLModalProps {
  api
  mappingView
  modalShowState
  setModalShowState
  HTMLContent
  HTMLFilename
  setHTMLContent
}

export const APIExportHTMLModal: React.FunctionComponent<APIExportHTMLModalProps> = ({
  api,
  mappingView,
  modalShowState = false,
  setModalShowState,
  HTMLContent = '',
  HTMLFilename,
  setHTMLContent
}: APIExportHTMLModalProps) => {
  const auth = useAuth()
  const [isModalOpen, setIsModalOpen] = React.useState(false)

  React.useEffect(() => {
    setIsModalOpen(modalShowState)
  }, [modalShowState])

  const handleModalToggle = () => {
    const new_state = !modalShowState
    if (new_state == false) {
      setHTMLContent('')
    }
    setModalShowState(new_state)
    setIsModalOpen(new_state)
  }

  const downloadFile = (file_type: string = 'html') => {
    if (!auth.isLogged()) {
      return
    }

    const curr_date = new Date()
    const file_name = HTMLFilename.replace(/\.[^/.]+$/, '.' + file_type)
    const download_name = api.api + '-' + curr_date.toISOString().replaceAll(':', '') + '.' + file_type

    let query_string = '?api-id=' + api.id
    query_string += '&user-id=' + auth.userId
    query_string += '&token=' + auth.token
    query_string += '&filename=' + file_name
    query_string += '&mapping-view=' + mappingView

    fetch(Constants.API_BASE_URL + Constants.API_HTML_API_EXPORT_DOWNLOAD_ENDPOINT + query_string)
      .then((response) => {
        if (!response.ok) {
          throw new Error('Network response was not ok')
        }
        return response.blob()
      })
      .then((blob) => {
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = download_name
        document.body.appendChild(a)
        a.click()
        a.remove()
        window.URL.revokeObjectURL(url)
      })
      .catch((error) => {
        console.error('Download error:', error)
      })
  }

  return (
    <React.Fragment>
      <Modal
        width={Constants.MODAL_WIDTH}
        bodyAriaLabel='APIExportHTMLModal'
        aria-label='api export html modal'
        tabIndex={0}
        variant={ModalVariant.large}
        title='HTML Data'
        description='Export of selected library work items and relationships'
        isOpen={isModalOpen}
        onClose={handleModalToggle}
      >
        <Flex>
          <FlexItem>
            <Flex>
              <FlexItem>
                <Button variant='link' onClick={() => downloadFile('html')} id='btn-download-html-file'>
                  Download HTML
                </Button>
              </FlexItem>
              <FlexItem>
                <Button variant='link' onClick={() => downloadFile('pdf')} id='btn-download-pdf-file'>
                  Download PDF
                </Button>
              </FlexItem>
            </Flex>
          </FlexItem>
        </Flex>

        <hr></hr>
        <br></br>
        <br></br>

        <iframe
          title='export-html'
          id='iframe-export-html'
          style={{ width: '100%', height: '70vh' }}
          srcDoc={HTMLContent}
          sandbox='allow-scripts allow-same-origin'
        >
          <p>Your browser does not support iframes.</p>
        </iframe>
      </Modal>
    </React.Fragment>
  )
}
