import React from 'react'
import { Button, Divider, Hint, HintBody, Modal, ModalVariant, Text, TextContent, TextVariants } from '@patternfly/react-core'
import * as Constants from '../../Constants/constants'
import CopyIcon from '@patternfly/react-icons/dist/esm/icons/copy-icon'
import { decode as base64_decode, encode as base64_encode } from 'base-64'
import { useAuth } from '@app/User/AuthProvider'

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

  let auth = useAuth()

  const generatePassword = () => {
    let charset = ''
    let newPasswordValue = ''
    let passwordLength = 20

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

  const resetUserPassword = () => {
    const data = {
      'user-id': auth.userId, // The one that request the change
      token: auth.token, // The one that request the change
      email: user.email, // The one that will be changed
      password: base64_encode(newPassword)
    }

    fetch(Constants.API_BASE_URL + '/user/reset-password', {
      method: 'PUT',
      headers: {
        Accept: 'application/json',
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(data)
    })
      .then((response) => {
        if (response.status !== 200) {
          setSubmitEnable(false)
          setMessageValue(response.statusText)
        } else {
          location.reload()
        }
      })
      .catch((err) => {
        setMessageValue(err.toString())
      })
  }

  return (
    <React.Fragment>
      <Modal
        bodyAriaLabel='Scrollable modal content'
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
            onClick={() => {
              navigator.clipboard.writeText(newPassword)
            }}
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
              <b>{newPassword}</b>
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
