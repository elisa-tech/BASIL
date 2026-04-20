import React from 'react'
import { useAuth } from '@app/User/AuthProvider'
import * as Constants from '@app/Constants/constants'
import { Button, Checkbox, Flex, FlexItem, Modal, ModalVariant, Spinner } from '@patternfly/react-core'

export interface APIExportHTMLModalProps {
  api
  mappingView
  modalShowState
  setModalShowState
  HTMLContent
  HTMLFilename
  setHTMLContent
  exportToHTMLFormat
}

export const APIExportHTMLModal: React.FunctionComponent<APIExportHTMLModalProps> = ({
  api,
  mappingView,
  modalShowState = false,
  setModalShowState,
  HTMLContent = '',
  HTMLFilename,
  setHTMLContent,
  exportToHTMLFormat
}: APIExportHTMLModalProps) => {
  const auth = useAuth()
  const [isModalOpen, setIsModalOpen] = React.useState(false)

  const [exportJustifications, setExportJustifications] = React.useState<boolean>(true)
  const [exportDocuments, setExportDocuments] = React.useState<boolean>(true)
  const [exportTestSpecifications, setExportTestSpecifications] = React.useState<boolean>(true)
  const [exportTestCases, setExportTestCases] = React.useState<boolean>(true)
  const [exportTestRuns, setExportTestRuns] = React.useState<boolean>(true)
  const [exportComments, setExportComments] = React.useState<boolean>(true)
  const [exportTools, setExportTools] = React.useState<boolean>(true)
  const [isDownloading, setIsDownloading] = React.useState<string | null>(null)

  React.useEffect(() => {
    setIsModalOpen(modalShowState)
  }, [modalShowState])

  React.useEffect(() => {
    if (mappingView === Constants._TSs) {
      setExportTestSpecifications(true)
    } else if (mappingView === Constants._TCs) {
      setExportTestCases(true)
    } else if (mappingView === Constants._Js) {
      setExportJustifications(true)
    }
  }, [mappingView])

  const handleModalToggle = () => {
    const new_state = !modalShowState
    setExportJustifications(true)
    setExportDocuments(true)
    setExportTestSpecifications(true)
    setExportTestCases(true)
    setExportTestRuns(true)
    setExportComments(true)
    setExportTools(true)
    if (new_state == false) {
      setHTMLContent('')
    }
    setModalShowState(new_state)
    setIsModalOpen(new_state)
  }

  const reloadHTMLExport = () => {
    setHTMLContent('Loading... Please wait...')
    const configExport = {
      include_justifications: exportJustifications,
      include_documents: exportDocuments,
      include_test_specifications: exportTestSpecifications,
      include_test_cases: exportTestCases,
      include_test_runs: exportTestRuns,
      include_comments: exportComments,
      include_tools: exportTools
    }

    exportToHTMLFormat('html', configExport)
  }

  const handleChange = (event: React.FormEvent<HTMLInputElement>, checked: boolean) => {
    const target = event.currentTarget
    const name = target.name

    switch (name) {
      case 'check-export-justifications':
        setExportJustifications(checked)
        break
      case 'check-export-documents':
        setExportDocuments(checked)
        break
      case 'check-export-test-specifications':
        setExportTestSpecifications(checked)
        break
      case 'check-export-test-cases':
        setExportTestCases(checked)
        break
      case 'check-export-test-runs':
        setExportTestRuns(checked)
        break
      case 'check-export-comments':
        setExportComments(checked)
        break
      case 'check-export-tools':
        setExportTools(checked)
        break
      default:
        // eslint-disable-next-line no-console
        console.log(name)
    }
  }

  const downloadFile = (file_type: string = 'html') => {
    if (!auth.isLogged() || isDownloading) {
      return
    }

    setIsDownloading(file_type)

    const curr_date = new Date()
    const file_name = HTMLFilename.replace(/\.[^/.]+$/, '.' + file_type)
    const download_name = api.api + '-' + curr_date.toISOString().replaceAll(':', '') + '.' + file_type

    let query_string = '?api-id=' + api.id
    query_string += '&user-id=' + auth.userId
    query_string += '&token=' + auth.token
    query_string += '&filename=' + file_name
    query_string += '&mapping-view=' + mappingView

    const configExport = {
      include_justifications: exportJustifications,
      include_documents: exportDocuments,
      include_test_specifications: exportTestSpecifications,
      include_test_cases: exportTestCases,
      include_test_runs: exportTestRuns,
      include_comments: exportComments,
      include_tools: exportTools
    }

    for (const key in configExport) {
      query_string += '&' + key + '=' + configExport[key]
    }

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
      .finally(() => {
        setIsDownloading(null)
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
                <Button
                  variant='link'
                  onClick={() => downloadFile('html')}
                  id='btn-download-html-file'
                  isDisabled={isDownloading !== null}
                  icon={isDownloading === 'html' ? <Spinner size='sm' /> : undefined}
                >
                  {isDownloading === 'html' ? 'Generating HTML…' : 'Download HTML'}
                </Button>
              </FlexItem>
              <FlexItem>
                <Button
                  variant='link'
                  onClick={() => downloadFile('pdf')}
                  id='btn-download-pdf-file'
                  isDisabled={isDownloading !== null}
                  icon={isDownloading === 'pdf' ? <Spinner size='sm' /> : undefined}
                >
                  {isDownloading === 'pdf' ? 'Generating PDF…' : 'Download PDF'}
                </Button>
              </FlexItem>
              <FlexItem>
                <Flex
                  direction={{ default: 'row' }}
                  flexWrap={{ default: 'wrap' }}
                  alignItems={{ default: 'alignItemsCenter' }}
                  spaceItems={{ default: 'spaceItemsMd' }}
                >
                  {mappingView !== Constants._Js && (
                    <Checkbox
                      id='checkbox-export-justifications'
                      label='Justifications'
                      isChecked={exportJustifications}
                      name='check-export-justifications'
                      onChange={handleChange}
                    />
                  )}
                  <Checkbox
                    id='checkbox-export-documents'
                    label='Documents'
                    isChecked={exportDocuments}
                    name='check-export-documents'
                    onChange={handleChange}
                  />
                  {mappingView !== Constants._TSs && (
                    <Checkbox
                      id='checkbox-export-test-specifications'
                      label='Test Specifications'
                      isChecked={exportTestSpecifications}
                      name='check-export-test-specifications'
                      onChange={handleChange}
                    />
                  )}
                  {mappingView !== Constants._TCs && (
                    <Checkbox
                      id='checkbox-export-test-cases'
                      label='Test Cases'
                      isChecked={exportTestCases}
                      name='check-export-test-cases'
                      onChange={handleChange}
                    />
                  )}
                  {exportTestCases && (
                    <Checkbox
                      id='checkbox-export-test-runs'
                      label='Test Runs'
                      isChecked={exportTestRuns}
                      name='check-export-test-runs'
                      onChange={handleChange}
                    />
                  )}
                  <Checkbox
                    id='checkbox-export-comments'
                    label='Comments'
                    isChecked={exportComments}
                    name='check-export-comments'
                    onChange={handleChange}
                  />
                  <Checkbox
                    id='checkbox-export-tools'
                    label='Tools'
                    isChecked={exportTools}
                    name='check-export-tools'
                    onChange={handleChange}
                  />
                  <Button variant='link' onClick={() => reloadHTMLExport()} id='btn-reload-html-export'>
                    Reload HTML Export
                  </Button>
                </Flex>
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
