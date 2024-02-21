import React from 'react'
import { Button, Modal, ModalVariant, Text, TextContent, TextList, TextListItem, TextVariants } from '@patternfly/react-core'

export interface MappingHistoryModalProps {
  modalShowState
  setModalShowState
  modalTitle: string
  modalDescription: string
  modalData
}

export const MappingHistoryModal: React.FunctionComponent<MappingHistoryModalProps> = ({
  modalShowState = false,
  setModalShowState,
  modalTitle = '',
  modalDescription = '',
  modalData
}: MappingHistoryModalProps) => {
  const [isModalOpen, setIsModalOpen] = React.useState(false)

  React.useEffect(() => {
    setIsModalOpen(modalShowState)
  }, [modalShowState])

  const handleModalToggle = () => {
    const new_state = !modalShowState
    setModalShowState(new_state)
    setIsModalOpen(new_state)
  }

  const getHistory = () => {
    if (modalData == undefined) {
      return ''
    }
    if (modalData.length == 0) {
      return ''
    } else {
      return modalData.map((version, versionIndex) => (
        <React.Fragment key={versionIndex}>
          <TextContent>
            <Text component={TextVariants.h3}>
              Version {version.version} - {version.created_at}
            </Text>
            <TextList>
              {Object.keys(version.object).map((key, index) => (
                <TextListItem key={index}>
                  <Text component={TextVariants.p} className='work-item-detail-text'>
                    <em>
                      <b>{key}</b>:{' '}
                    </em>
                    {version.object[key]}
                  </Text>
                </TextListItem>
              ))}
            </TextList>
            <TextList>
              <Text component={TextVariants.p} className='work-item-detail-text'>
                {Object.keys(version.mapping).map((key, index) => (
                  <TextListItem key={index}>
                    <em>
                      <b>{key}</b>:{' '}
                    </em>
                    {version.mapping[key]}
                  </TextListItem>
                ))}
              </Text>
            </TextList>
          </TextContent>
        </React.Fragment>
      ))
    }
  }

  return (
    <React.Fragment>
      <Modal
        bodyAriaLabel='Scrollable modal content'
        tabIndex={0}
        variant={ModalVariant.large}
        title={modalTitle}
        description={modalDescription}
        isOpen={isModalOpen}
        onClose={handleModalToggle}
        actions={[
          <Button key='cancel' variant='link' onClick={handleModalToggle}>
            Close
          </Button>
        ]}
      >
        {getHistory()}
      </Modal>
    </React.Fragment>
  )
}
