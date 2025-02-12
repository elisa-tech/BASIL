import React from 'react'
import * as Constants from '@app/Constants/constants'
import { Button, ClipboardCopyButton, CodeBlock, CodeBlockAction, CodeBlockCode, Modal, ModalVariant } from '@patternfly/react-core'

export interface APIExportSPDXModalProps {
  modalShowState
  setModalShowState
  SPDXContent
  setSPDXContent
}

export const APIExportSPDXModal: React.FunctionComponent<APIExportSPDXModalProps> = ({
  modalShowState = false,
  setModalShowState,
  SPDXContent = '',
  setSPDXContent
}: APIExportSPDXModalProps) => {
  const [isModalOpen, setIsModalOpen] = React.useState(false)
  const [copied, setCopied] = React.useState(false)

  const clipboardCopyFunc = (event, text) => {
    navigator.clipboard.writeText(text.toString())
  }

  const onClick = (event, text) => {
    clipboardCopyFunc(event, text)
    setCopied(true)
  }

  React.useEffect(() => {
    setIsModalOpen(modalShowState)
  }, [modalShowState])

  const handleModalToggle = () => {
    const new_state = !modalShowState
    if (new_state == false) {
      setSPDXContent('')
    }
    setModalShowState(new_state)
    setIsModalOpen(new_state)
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
        <CodeBlock actions={actions}>
          <CodeBlockCode id='code-content'>{SPDXContent}</CodeBlockCode>
        </CodeBlock>
      </Modal>
    </React.Fragment>
  )
}
