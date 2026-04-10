import React from 'react'
import {
  Button,
  DescriptionList,
  DescriptionListDescription,
  DescriptionListGroup,
  DescriptionListTerm,
  Form,
  FormGroup,
  Hint,
  HintBody,
  Modal,
  ModalVariant,
  TextInput
} from '@patternfly/react-core'
import * as Constants from '@app/Constants/constants'
import { useAuth } from '@app/User/AuthProvider'

export interface APINewVersionModalProps {
  api
  modalShowState
  setModalShowState
  modalTitle
  modalDescription
}

export const APINewVersionModal: React.FunctionComponent<APINewVersionModalProps> = ({
  api,
  modalShowState = false,
  setModalShowState,
  modalTitle = '',
  modalDescription = ''
}: APINewVersionModalProps) => {
  const auth = useAuth()
  const [isModalOpen, setIsModalOpen] = React.useState(false)
  const [messageValue, setMessageValue] = React.useState('')
  const [newVersionValue, setNewVersionValue] = React.useState('')

  const handleModalToggle = () => {
    const new_state = !modalShowState
    setModalShowState(new_state)
    setIsModalOpen(new_state)
  }

  React.useEffect(() => {
    setIsModalOpen(modalShowState)
    if (modalShowState == false) {
      setMessageValue('')
      setNewVersionValue('')
    }
  }, [modalShowState])

  const submitNewVersion = () => {
    if (!api) {
      return
    }
    if (!auth.isLogged()) {
      setMessageValue(Constants.SESSION_EXPIRED_MESSAGE)
      return
    }

    const trimmed = newVersionValue.trim()
    if (!trimmed) {
      setMessageValue('Software component library version is mandatory.')
      return
    }

    setMessageValue('')

    const data = {
      'api-id': api.id,
      'new-version': trimmed,
      'user-id': auth.userId,
      token: auth.token
    }

    let status
    let status_text
    fetch(Constants.API_BASE_URL + Constants.API_APIS_NEW_VERSION_ENDPOINT, {
      method: 'POST',
      headers: Constants.JSON_HEADER,
      body: JSON.stringify(data)
    })
      .then((response) => {
        status = response.status
        status_text = response.statusText
        if (!Constants.isHttpSuccessStatus(status)) {
          return response.text()
        } else {
          window.location.replace('/?currentLibrary=' + encodeURIComponent(api.library))
          return response.json()
        }
      })
      .then((data) => {
        if (!Constants.isHttpSuccessStatus(status)) {
          setMessageValue(Constants.getResponseErrorMessage(status, status_text, data))
        }
      })
      .catch((err) => {
        setMessageValue(err.toString())
      })
  }

  return (
    <React.Fragment>
      <Modal
        width={Constants.MODAL_WIDTH}
        bodyAriaLabel='APINewVersionModal'
        aria-label='api new version modal'
        tabIndex={0}
        variant={ModalVariant.large}
        title={modalTitle}
        description={modalDescription}
        isOpen={isModalOpen}
        onClose={handleModalToggle}
        actions={[
          <Button key='confirm' id='btn-modal-api-confirm' variant='primary' onClick={submitNewVersion}>
            Confirm
          </Button>,
          <Button id='btn-api-new-version-cancel' key='cancel' variant='link' onClick={handleModalToggle}>
            Cancel
          </Button>
        ]}
      >
        {api ? (
          <Form>
            <DescriptionList>
              <DescriptionListGroup>
                <DescriptionListTerm>Software component name</DescriptionListTerm>
                <DescriptionListDescription>{api.api}</DescriptionListDescription>
              </DescriptionListGroup>
              <DescriptionListGroup>
                <DescriptionListTerm>Library</DescriptionListTerm>
                <DescriptionListDescription>{api.library}</DescriptionListDescription>
              </DescriptionListGroup>
              <DescriptionListGroup>
                <DescriptionListTerm>Current version</DescriptionListTerm>
                <DescriptionListDescription>{api.library_version}</DescriptionListDescription>
              </DescriptionListGroup>
            </DescriptionList>
            <FormGroup label='New version' fieldId='input-api-new-version'>
              <TextInput
                id={'input-api-fork-library-version-' + api.id}
                value={newVersionValue}
                onChange={(_e, v) => setNewVersionValue(v)}
                type='text'
                aria-label='New software component library version'
              />
            </FormGroup>
            {messageValue ? (
              <Hint>
                <HintBody>{messageValue}</HintBody>
              </Hint>
            ) : null}
          </Form>
        ) : null}
      </Modal>
    </React.Fragment>
  )
}
