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

export interface APIExportSPDXModalProps {
  api
  modalShowState
  setModalShowState
  SPDXContent
  SPDXFilename
  setSPDXContent
}

export const APIExportSPDXModal: React.FunctionComponent<APIExportSPDXModalProps> = ({
  api,
  modalShowState = false,
  setModalShowState,
  SPDXContent = '',
  SPDXFilename,
  setSPDXContent
}: APIExportSPDXModalProps) => {
  const auth = useAuth()
  const [isModalOpen, setIsModalOpen] = React.useState(false)
  const [copied, setCopied] = React.useState(false)
  const [imgSrc, setImgSrc] = React.useState<string>('')
  const [activeTabKey, setActiveTabKey] = React.useState<string | number>(0)

  // Toggle currently active tab
  const handleTabClick = (event: React.MouseEvent | React.KeyboardEvent | MouseEvent, tabIndex: string | number) => {
    setActiveTabKey(tabIndex)
    if (tabIndex == 1) {
      if (!imgSrc) {
        downloadFile('png', true)
      }
    }
  }

  const clipboardCopyFunc = (event, text) => {
    navigator.clipboard.writeText(text.toString())
  }

  const onClick = (event, text) => {
    clipboardCopyFunc(event, text)
    setCopied(true)
  }

  React.useEffect(() => {
    setIsModalOpen(modalShowState)
    if (modalShowState) {
      setActiveTabKey(0)
      setImgSrc('')
    }
  }, [modalShowState])

  const handleModalToggle = () => {
    const new_state = !modalShowState
    if (new_state == false) {
      setSPDXContent('')
    }
    setModalShowState(new_state)
    setIsModalOpen(new_state)
  }

  const downloadFile = (file_type: string = 'jsonld', loadStreamOnly: boolean = false) => {
    if (!auth.isLogged()) {
      return
    }

    const curr_date = new Date()
    const file_name = SPDXFilename.replace(/\.[^/.]+$/, '.' + file_type)
    const download_name = api.api + '-' + curr_date.toISOString().replaceAll(':', '') + '.' + file_type

    let query_string = '?api-id=' + api.id
    query_string += '&user-id=' + auth.userId
    query_string += '&token=' + auth.token
    query_string += '&filename=' + file_name

    fetch(Constants.API_BASE_URL + Constants.API_SPDX_API_EXPORT_DOWNLOAD_ENDPOINT + query_string)
      .then((response) => {
        if (!response.ok) {
          throw new Error('Network response was not ok')
        }
        return response.blob()
      })
      .then((blob) => {
        const url = window.URL.createObjectURL(blob)
        if (loadStreamOnly == false) {
          const a = document.createElement('a')
          a.href = url
          a.download = download_name
          document.body.appendChild(a)
          a.click()
          a.remove()
          window.URL.revokeObjectURL(url)
        } else {
          if (file_type == 'png') {
            setImgSrc(url)
          }
        }
      })
      .catch((error) => {
        console.error('Download error:', error)
      })
  }

  const actions = (
    <React.Fragment>
      <CodeBlockAction>
        <ClipboardCopyButton
          id='basic-copy-button'
          textId='code-content'
          aria-label='Copy to clipboard'
          onClick={(e) => onClick(e, SPDXContent)}
          exitDelay={copied ? 1500 : 600}
          maxWidth='110px'
          variant='plain'
          onTooltipHidden={() => setCopied(false)}
        >
          {copied ? 'Successfully copied to clipboard!' : 'Copy to clipboard'}
        </ClipboardCopyButton>
      </CodeBlockAction>
    </React.Fragment>
  )

  const spdxExportJsonldRef = React.createRef<HTMLElement>()
  const spxdExportGraphMapRef = React.createRef<HTMLElement>()

  return (
    <React.Fragment>
      <Modal
        width={Constants.MODAL_WIDTH}
        bodyAriaLabel='APIExportSPDXModal'
        aria-label='api export spdx modal'
        tabIndex={0}
        variant={ModalVariant.large}
        title='SPDX Data'
        description='Export of selected library work items and relationships'
        isOpen={isModalOpen}
        onClose={handleModalToggle}
        actions={[
          <Button key='cancel' variant='link' onClick={handleModalToggle}>
            Close
          </Button>
        ]}
      >
        <Tabs activeKey={activeTabKey} onSelect={handleTabClick} aria-label='SPDX Export tabs' role='region'>
          <Tab
            eventKey={0}
            id='tab-btn-spdx-export-jsonld'
            title={<TabTitleText>JSONLD</TabTitleText>}
            tabContentId='tabSPDXExportJSONLD'
            tabContentRef={spdxExportJsonldRef}
          />
          <Tab
            eventKey={1}
            id='tab-btn-spdx-export-graph-map'
            title={<TabTitleText>Map</TabTitleText>}
            tabContentId='tabSPDXExportGraphMap'
            tabContentRef={spxdExportGraphMapRef}
          />
        </Tabs>
        <div>
          <TabContent eventKey={0} id='tabSpdxExportJsonld' ref={spdxExportJsonldRef} hidden={0 !== activeTabKey}>
            <TabContentBody hasPadding>
              <Flex>
                <FlexItem>
                  <Button variant='link' onClick={() => downloadFile('jsonld')}>
                    Download JSONLD
                  </Button>
                </FlexItem>
                <FlexItem>
                  <CodeBlock actions={actions}>
                    <CodeBlockCode id='code-content'>{SPDXContent}</CodeBlockCode>
                  </CodeBlock>
                </FlexItem>
              </Flex>
            </TabContentBody>
          </TabContent>
          <TabContent eventKey={1} id='tabSpxdExportGraphMap' ref={spxdExportGraphMapRef} hidden={1 !== activeTabKey}>
            <TabContentBody>
              {imgSrc ? (
                <React.Fragment>
                  <Flex direction={{ default: 'column' }}>
                    <FlexItem>
                      <Flex>
                        <FlexItem>
                          <Button variant='link' onClick={() => downloadFile('png')}>
                            Download .png Map
                          </Button>
                        </FlexItem>
                        <FlexItem>|</FlexItem>
                        <FlexItem>
                          <Button variant='link' onClick={() => downloadFile('dot')}>
                            Download .dot Map
                          </Button>
                        </FlexItem>
                      </Flex>
                    </FlexItem>
                    <FlexItem>
                      <img src={imgSrc} alt='Traceability map' width={'100%'} />
                    </FlexItem>
                  </Flex>
                </React.Fragment>
              ) : (
                'Loading image...'
              )}
            </TabContentBody>
          </TabContent>
        </div>
      </Modal>
    </React.Fragment>
  )
}
