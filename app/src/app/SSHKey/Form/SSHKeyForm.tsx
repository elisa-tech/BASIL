import React from 'react'
import * as Constants from '../../Constants/constants'
import { Form, FormGroup, FormHelperText, HelperText, HelperTextItem, Hint, HintBody, TextArea, TextInput } from '@patternfly/react-core'
import { useAuth } from '../../User/AuthProvider'

export interface SSHKeyFormProps {
  modalFormSubmitState: string
  setModalSubmit?
}

export const SSHKeyForm: React.FunctionComponent<SSHKeyFormProps> = ({
  modalFormSubmitState = 'waiting',
  setModalSubmit
}: SSHKeyFormProps) => {
  const auth = useAuth()
  const [titleValue, setTitleValue] = React.useState('')
  const [validatedTitleValue, setValidatedTitleValue] = React.useState<Constants.validate>('error')

  const [sshKeyValue, setSshKeyValue] = React.useState('')
  const [validatedSshKeyValue, setValidatedSshKeyValue] = React.useState<Constants.validate>('error')

  const [messageValue, setMessageValue] = React.useState('')

  React.useEffect(() => {
    setModalSubmit('waiting')
    if (titleValue == undefined) {
      setTitleValue('')
    } else {
      if (titleValue.trim() === '') {
        setValidatedTitleValue('error')
      } else {
        setValidatedTitleValue('success')
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [titleValue])

  React.useEffect(() => {
    setModalSubmit('waiting')
    if (sshKeyValue == undefined) {
      setSshKeyValue('')
    } else {
      if (sshKeyValue.trim() === '') {
        setValidatedSshKeyValue('error')
      } else {
        setValidatedSshKeyValue('success')
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sshKeyValue])

  React.useEffect(() => {
    if (modalFormSubmitState == 'submitted') {
      handleSubmit()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [modalFormSubmitState])

  const handleTitleValueChange = (_event, value: string) => {
    setTitleValue(value)
  }

  const handleSshKeyValueChange = (_event, value: string) => {
    setSshKeyValue(value)
  }

  const handleSubmit = () => {
    if (validatedTitleValue != 'success') {
      setMessageValue('Title is mandatory.')
      setModalSubmit('waiting')
      return
    } else if (validatedSshKeyValue != 'success') {
      setMessageValue('SSH Key value is mandatory')
      setModalSubmit('waiting')
      return
    }

    setMessageValue('')

    const data = {
      'user-id': auth.userId,
      token: auth.token,
      title: titleValue,
      ssh_key: sshKeyValue
    }

    fetch(Constants.API_BASE_URL + '/user/ssh-key', {
      method: 'POST',
      headers: {
        Accept: 'application/json',
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(data)
    })
      .then((response) => {
        if (response.status !== 200) {
          setMessageValue(response.statusText)
          setModalSubmit('waiting')
        } else {
          location.reload()
        }
      })
      .catch((err) => {
        setMessageValue(err.toString())
        setModalSubmit('waiting')
      })
  }

  return (
    <Form>
      <FormGroup label='Title:' isRequired fieldId={`input-ssh-key-title-add`}>
        <TextInput
          isRequired
          id={`input-input-ssh-key-title-add`}
          name={`input-ssh-key-title-add`}
          value={titleValue || ''}
          onChange={(_ev, value) => handleTitleValueChange(_ev, value)}
        />
        {validatedTitleValue !== 'success' && (
          <FormHelperText>
            <HelperText>
              <HelperTextItem variant='error'>{validatedTitleValue === 'error' ? 'Title field is mandatory' : ''}</HelperTextItem>
            </HelperText>
          </FormHelperText>
        )}
      </FormGroup>

      <FormGroup label='SSH Key' isRequired fieldId={`input-ssh-key-add-key`}>
        <TextArea
          isRequired
          resizeOrientation='vertical'
          aria-label='SSH Key add key value'
          id={`input-ssh-key-add-key`}
          name={`input-ssh-key-add-key`}
          value={sshKeyValue || ''}
          onChange={(_ev, value) => handleSshKeyValueChange(_ev, value)}
        />
        {validatedSshKeyValue !== 'success' && (
          <FormHelperText>
            <HelperText>
              <HelperTextItem variant='error'>{validatedSshKeyValue === 'error' ? 'This field is mandatory' : ''}</HelperTextItem>
            </HelperText>
          </FormHelperText>
        )}
      </FormGroup>

      {messageValue ? (
        <>
          <Hint>
            <HintBody>{messageValue}</HintBody>
          </Hint>
          <br />
        </>
      ) : (
        ''
      )}
    </Form>
  )
}
