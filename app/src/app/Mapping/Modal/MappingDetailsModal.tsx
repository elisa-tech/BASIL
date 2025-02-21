import React from 'react'
import ReactMarkdown from 'react-markdown'
import * as Constants from '@app/Constants/constants'
import { Button, Modal, ModalVariant, Text, TextContent, TextList, TextListItem } from '@patternfly/react-core'

export interface MappingDeleteModalProps {
  modalShowState
  setModalShowState
  modalTitle: string
  modalDescription: string
  modalData
}

export const MappingDetailsModal: React.FunctionComponent<MappingDeleteModalProps> = ({
  modalShowState = false,
  setModalShowState,
  modalTitle = '',
  modalDescription = '',
  modalData
}: MappingDeleteModalProps) => {
  const [isModalOpen, setIsModalOpen] = React.useState(false)

  const handleModalToggle = () => {
    const new_state = !modalShowState
    setModalShowState(new_state)
    setIsModalOpen(new_state)
  }

  React.useEffect(() => {
    setIsModalOpen(modalShowState)
  }, [modalShowState])

  const getDetails = () => {
    if (modalData == undefined) {
      return ''
    }
    if (modalData.length == 0) {
      return ''
    } else {
      return modalData.map((version, versionIndex) => (
        <React.Fragment key={versionIndex}>
          <TextContent>
            <TextList>
              {Object.keys(version).map((key, index) => (
                <TextListItem key={index}>
                  <em>
                    <b>{Constants.capitalizeFirstWithoutHashes(key)}</b>:{' '}
                  </em>
                  <Text>
                    <ReactMarkdown>{version[key].toString()}</ReactMarkdown>
                  </Text>
                </TextListItem>
              ))}
            </TextList>
          </TextContent>
        </React.Fragment>
      ))
    }
  }

  return (
    <React.Fragment>
      <Modal
        width={Constants.MODAL_WIDTH}
        bodyAriaLabel='MappingDetailsModal'
        aria-label='mapping details modal'
        tabIndex={0}
        variant={ModalVariant.large}
        title={modalTitle}
        description={modalDescription}
        isOpen={isModalOpen}
        onClose={handleModalToggle}
        actions={[
          <Button key='cancel' variant='link' onClick={handleModalToggle}>
            Cancel
          </Button>
        ]}
      >
        {getDetails()}
      </Modal>
    </React.Fragment>
  )
}
