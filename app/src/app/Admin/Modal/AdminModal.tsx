import React from 'react'
import { Button, Divider, Hint, HintBody, Modal, ModalVariant, Text, TextContent, TextVariants } from '@patternfly/react-core'
import * as Constants from '@app/Constants/constants'
import { encode as base64_encode } from 'base-64'
import CopyIcon from '@patternfly/react-icons/dist/esm/icons/copy-icon'
import { useAuth } from '../../User/AuthProvider'

export interface AdminModalProps {
  modalShowState
  setModalShowState
  user
}

export const AdminModal: React.FunctionComponent<AdminModalProps> = ({
  modalShowState = false,
  setModalShowState,
  user
}: AdminModalProps) => {
  const [isModalOpen, setIsModalOpen] = React.useState(false)
  const [messageValue, setMessageValue] = React.useState('')
  const [newPassword, setNewPassword] = React.useState('')
  const [submitEnable, setSubmitEnable] = React.useState(false)

  const auth = useAuth()

  const generatePassword = () => {
    let charset = ''
    let newPasswordValue = ''
    const passwordLength = 20

    charset += '!@#_-'
    charset += '0123456789'
    charset += 'abcdefghijklmnopqrstuvwxyz'
    charset += 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'

    for (let i = 0; i < passwordLength; i++) {
      newPasswordValue += charset.charAt(Math.floor(Math.random() * charset.length))
    }

    setNewPassword(newPasswordValue)
    return newPasswordValue
  }

  const handleModalToggle = () => {
    const new_state = !modalShowState
    setModalShowState(new_state)
    setIsModalOpen(new_state)
  }

  React.useEffect(() => {
    setIsModalOpen(modalShowState)
    if (modalShowState == false) {
      setSubmitEnable(false)
      setMessageValue('')
    } else {
      setSubmitEnable(true)
      generatePassword()
    }
  }, [modalShowState])

  const copyTextToClipboard = async (text: string) => {
    if (navigator.clipboard && window.isSecureContext) {
      try {
        await navigator.clipboard.writeText(text)
        console.log('Copied with Clipboard API')
      } catch (err) {
        console.error('Clipboard API failed, using fallback', err)
        Constants.fallbackCopyTextToClipboard(text)
      }
    } else {
      Constants.fallbackCopyTextToClipboard(text)
    }
  }

  const resetUserPassword = () => {
    const data = {
      'user-id': auth.userId, // The one that request the change
      token: auth.token, // The one that request the change
      'target-user': {
        // The one that will be changed
        id: user.id,
        password: base64_encode(newPassword)
      }
    }

    fetch(Constants.API_BASE_URL + Constants.API_ADMIN_RESET_USER_PASSWORD_ENDPOINT, {
      method: 'PUT',
      headers: Constants.JSON_HEADER,
      body: JSON.stringify(data)
    })
      .then((response) => {
        if (response.status !== 200) {
          setSubmitEnable(false)
          setMessageValue(response.statusText)
        } else {
          setSubmitEnable(false)
          setMessageValue('Changes saved')
        }
      })
      .catch((err) => {
        setMessageValue(err.toString())
      })
  }

  return (
    <React.Fragment>
      <Modal
        id='admin-modal-id'
        width={Constants.MODAL_WIDTH}
        bodyAriaLabel='Admin modal'
        tabIndex={0}
        variant={ModalVariant.large}
        title={'Reset user password'}
        description={''}
        isOpen={isModalOpen}
        onClose={handleModalToggle}
        actions={[
          <Button
            key='confirm'
            id='btn-user-reset-password-confirm'
            variant='primary'
            isDisabled={!submitEnable}
            onClick={resetUserPassword}
          >
            Confirm
          </Button>,
          <Button
            key='copy'
            id='btn-user-reset-password-copy'
            variant='secondary'
            icon={<CopyIcon />}
            ouiaId='btn-user-reset-password-copy'
            onClick={() => copyTextToClipboard(newPassword)}
          >
            Copy to Clipboard
          </Button>,
          <Button id='btn-user-reset-password-cancel' key='cancel' variant='link' onClick={handleModalToggle}>
            Cancel
          </Button>
        ]}
      >
        <TextContent>
          <Text component={TextVariants.p}>
            Set new password `
            <i>
              <b id='b-new-password'>{newPassword}</b>
            </i>
            ` for user <b>{user.email}</b>.
          </Text>
        </TextContent>

        {messageValue ? (
          <React.Fragment>
            <br />
            <Divider />
            <br />
            <Hint>
              <HintBody>{messageValue}</HintBody>
            </Hint>
          </React.Fragment>
        ) : (
          <span></span>
        )}
      </Modal>
    </React.Fragment>
  )
}
