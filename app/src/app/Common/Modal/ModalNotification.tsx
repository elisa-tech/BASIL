import React from 'react'
import { Modal, ModalVariant } from '@patternfly/react-core'

export interface ModalNotificationProps {
  modalShowState
  setModalShowState
  modalTitle
  modalMessage
}

export const ModalNotification: React.FunctionComponent<ModalNotificationProps> = ({
  modalShowState,
  setModalShowState,
  modalTitle,
  modalMessage
}: ModalNotificationProps) => {
  return (
    <Modal
      variant={ModalVariant.medium}
      isOpen={modalShowState}
      aria-label='modal notification'
      aria-describedby='modal-notification'
      onClose={() => setModalShowState(false)}
    >
      <span id='modal-notification-title'>
        <b>{modalTitle}</b>
      </span>
      <br />
      <br />
      {modalMessage}
    </Modal>
  )
}
