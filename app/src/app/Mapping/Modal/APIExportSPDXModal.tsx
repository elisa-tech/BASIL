import React from 'react'
import { useAuth } from '@app/User/AuthProvider'
import * as Constants from '@app/Constants/constants'
import {
  Button,
  Checkbox,
  ClipboardCopyButton,
  CodeBlock,
  CodeBlockAction,
  CodeBlockCode,
  Flex,
  FlexItem,
  Modal,
  ModalVariant,
  Spinner,
  Tab,
  TabContent,
  TabContentBody,
  TabTitleText,
  Tabs
} from '@patternfly/react-core'

interface SPDXTestRunConfig {
  id: number
  title?: string
  plugin?: string
}

export interface APIExportSPDXModalProps {
  api
  modalShowState
  setModalShowState
  SPDXContent
  SPDXFilename
  setSPDXContent
  SPDXContentLoading
  exportToSPDXFormat
}

export const APIExportSPDXModal: React.FunctionComponent<APIExportSPDXModalProps> = ({
  api,
  modalShowState = false,
  setModalShowState,
  SPDXContent = '',
  SPDXFilename,
  setSPDXContent,
  SPDXContentLoading = false,
  exportToSPDXFormat
}: APIExportSPDXModalProps) => {
  const auth = useAuth()
  const [isModalOpen, setIsModalOpen] = React.useState(false)
  const [copied, setCopied] = React.useState(false)
  const [imgSrc, setImgSrc] = React.useState<string>('')
  const [activeTabKey, setActiveTabKey] = React.useState<string | number>(0)
  const [exportComments, setExportComments] = React.useState<boolean>(true)
  const [exportTestRuns, setExportTestRuns] = React.useState<boolean>(true)
  const [testRunConfigs, setTestRunConfigs] = React.useState<SPDXTestRunConfig[]>([])
  const [selectedConfigIds, setSelectedConfigIds] = React.useState<number[]>([])
  const [configsLoading, setConfigsLoading] = React.useState<boolean>(false)

  const hasExport = SPDXContent !== '' && SPDXContent !== 'Loading... Please wait...'

  const resetOptions = () => {
    setExportComments(true)
    setExportTestRuns(true)
    setSelectedConfigIds([])
    setImgSrc('')
    setActiveTabKey(0)
  }

  const loadTestRunConfigs = () => {
    if (!auth.isLogged()) {
      return
    }
    setConfigsLoading(true)
    let url = Constants.API_BASE_URL + Constants.API_SPDX_API_TEST_RUN_CONFIGS_ENDPOINT
    url += '?api-id=' + api.id
    url += '&user-id=' + auth.userId
    url += '&token=' + auth.token
    fetch(url)
      .then((res) => res.json())
      .then((data) => {
        setTestRunConfigs(Array.isArray(data) ? data : [])
      })
      .catch((err) => {
        console.error(err.message)
        setTestRunConfigs([])
      })
      .finally(() => {
        setConfigsLoading(false)
      })
  }

  React.useEffect(() => {
    setIsModalOpen(modalShowState)
    if (modalShowState) {
      resetOptions()
      loadTestRunConfigs()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [modalShowState])

  const handleTabClick = (_event: React.MouseEvent | React.KeyboardEvent | MouseEvent, tabIndex: string | number) => {
    setActiveTabKey(tabIndex)
    if (tabIndex == 1 && hasExport && !imgSrc) {
      downloadFile('png', true)
    }
  }

  const clipboardCopyFunc = (_event, text) => {
    navigator.clipboard.writeText(text.toString())
  }

  const onClick = (event, text) => {
    clipboardCopyFunc(event, text)
    setCopied(true)
  }

  const handleModalToggle = () => {
    const new_state = !modalShowState
    if (new_state == false) {
      setSPDXContent('')
      resetOptions()
    }
    setModalShowState(new_state)
    setIsModalOpen(new_state)
  }

  const toggleConfig = (configId: number, checked: boolean) => {
    setSelectedConfigIds((current) => {
      if (checked) {
        return current.includes(configId) ? current : [...current, configId]
      }
      return current.filter((id) => id !== configId)
    })
  }

  const generateExport = () => {
    setImgSrc('')
    setActiveTabKey(0)
    setSPDXContent('Loading... Please wait...')
    const configExport: Record<string, string | boolean> = {
      include_comments: exportComments,
      include_test_runs: exportTestRuns,
      test_run_config_id: selectedConfigIds.join(',')
    }
    exportToSPDXFormat('jsonld', configExport)
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
        title='SPDX Export'
        description='Choose what to include, then generate the SPDX JSON-LD and traceability map'
        isOpen={isModalOpen}
        onClose={handleModalToggle}
        actions={[
          <Button key='cancel' variant='link' onClick={handleModalToggle}>
            Close
          </Button>
        ]}
      >
        <Flex direction={{ default: 'column' }} spaceItems={{ default: 'spaceItemsMd' }}>
          <FlexItem>
            <Flex
              direction={{ default: 'row' }}
              flexWrap={{ default: 'wrap' }}
              alignItems={{ default: 'alignItemsCenter' }}
              spaceItems={{ default: 'spaceItemsMd' }}
            >
              <Checkbox
                id='checkbox-spdx-export-comments'
                label='Comments'
                isChecked={exportComments}
                name='check-spdx-export-comments'
                onChange={(_event, checked) => setExportComments(checked)}
              />
              <Checkbox
                id='checkbox-spdx-export-test-runs'
                label='Test Runs'
                isChecked={exportTestRuns}
                name='check-spdx-export-test-runs'
                onChange={(_event, checked) => setExportTestRuns(checked)}
              />
              <Button
                variant='primary'
                onClick={generateExport}
                id='btn-generate-spdx-export'
                isDisabled={SPDXContentLoading || configsLoading}
                icon={SPDXContentLoading ? <Spinner size='sm' /> : undefined}
              >
                {SPDXContentLoading ? 'Generating…' : 'Generate'}
              </Button>
            </Flex>
          </FlexItem>
          {exportTestRuns && (
            <FlexItem>
              <div id='spdx-export-test-run-configs'>
                <strong>Test Run Configurations</strong>
                <p>Select the configurations whose Test Runs should be included. None selected means no Test Runs.</p>
                {configsLoading ? (
                  <Spinner size='md' />
                ) : testRunConfigs.length === 0 ? (
                  <p>No Test Run configurations are used by this software component.</p>
                ) : (
                  <Flex direction={{ default: 'column' }} spaceItems={{ default: 'spaceItemsXs' }}>
                    {testRunConfigs.map((config) => (
                      <FlexItem key={config.id}>
                        <Checkbox
                          id={'checkbox-spdx-test-run-config-' + config.id}
                          label={`${config.title || 'Untitled'} (${config.plugin || 'plugin'}) #${config.id}`}
                          isChecked={selectedConfigIds.includes(config.id)}
                          name={'check-spdx-test-run-config-' + config.id}
                          onChange={(_event, checked) => toggleConfig(config.id, checked)}
                        />
                      </FlexItem>
                    ))}
                  </Flex>
                )}
              </div>
            </FlexItem>
          )}
        </Flex>

        {hasExport && (
          <React.Fragment>
            <hr></hr>
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
          </React.Fragment>
        )}
      </Modal>
    </React.Fragment>
  )
}
