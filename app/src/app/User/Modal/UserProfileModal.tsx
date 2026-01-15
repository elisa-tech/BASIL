import React from 'react'
import { useAuth } from '@app/User/AuthProvider'
import {
  Button,
  FormGroup,
  FormHelperText,
  HelperText,
  HelperTextItem,
  Hint,
  HintBody,
  Modal,
  ModalVariant,
  Tab,
  TabContent,
  TabContentBody,
  TabTitleText,
  Tabs,
  TextInput
} from '@patternfly/react-core'
import * as Constants from '@app/Constants/constants'

export interface UserProfileModalProps {
  modalShowState
  setModalShowState
}

export const UserProfileModal: React.FunctionComponent<UserProfileModalProps> = ({
  modalShowState = false,
  setModalShowState
}: UserProfileModalProps) => {
  const auth = useAuth()
  const [isModalOpen, setIsModalOpen] = React.useState(false)
  const [modalFormSubmitState, setModalFormSubmitState] = React.useState('waiting')

  const [profileUsernameValue, setProfileUsernameValue] = React.useState(auth.userName || '')
  const [validatedProfileUsernameValue, setValidatedProfileUsernameValue] = React.useState<Constants.validate>('error')

  const [currentPasswordValue, setCurrentPasswordValue] = React.useState('')
  const [validatedCurrentPasswordValue, setValidatedCurrentPasswordValue] = React.useState<Constants.validate>('error')
  const [newPasswordValue, setNewPasswordValue] = React.useState('')
  const [validatedNewPasswordValue, setValidatedNewPasswordValue] = React.useState<Constants.validate>('error')
  const [confirmPasswordValue, setConfirmPasswordValue] = React.useState('')
  const [validatedConfirmPasswordValue, setValidatedConfirmPasswordValue] = React.useState<Constants.validate>('error')

  const [activeTabKey, setActiveTabKey] = React.useState<string | number>(0)
  const [messageValue, setMessageValue] = React.useState<string>('')

  // Toggle currently active tab
  const handleTabClick = (event: React.MouseEvent | React.KeyboardEvent | MouseEvent, tabIndex: string | number) => {
    setActiveTabKey(tabIndex)
  }

  const handleModalToggle = () => {
    const new_state = !modalShowState
    setModalShowState(new_state)
    setIsModalOpen(new_state)
  }

  React.useEffect(() => {
    setIsModalOpen(modalShowState)
    if (modalShowState) {
      setMessageValue('')
    }
  }, [modalShowState])

  const comparePasswords = () => {
    if (newPasswordValue != confirmPasswordValue) {
      setValidatedConfirmPasswordValue('error')
    } else {
      setValidatedConfirmPasswordValue('success')
    }
  }

  React.useEffect(() => {
    if (profileUsernameValue == '') {
      setValidatedProfileUsernameValue('error')
    } else if (profileUsernameValue.includes(' ')) {
      setValidatedProfileUsernameValue('error')
    } else if (profileUsernameValue.length < 4) {
      setValidatedProfileUsernameValue('error')
    } else {
      setValidatedProfileUsernameValue('success')
    }
  }, [profileUsernameValue])

  React.useEffect(() => {
    if (currentPasswordValue == '') {
      setValidatedCurrentPasswordValue('error')
    } else if (currentPasswordValue.includes(' ')) {
      setValidatedCurrentPasswordValue('error')
    } else if (currentPasswordValue.length < 4) {
      setValidatedCurrentPasswordValue('error')
    } else {
      setValidatedCurrentPasswordValue('success')
      comparePasswords()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentPasswordValue])

  React.useEffect(() => {
    if (newPasswordValue == '') {
      setValidatedNewPasswordValue('error')
    } else if (newPasswordValue.includes(' ')) {
      setValidatedNewPasswordValue('error')
    } else if (newPasswordValue.length < 4) {
      setValidatedNewPasswordValue('error')
    } else {
      setValidatedNewPasswordValue('success')
      comparePasswords()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [newPasswordValue])

  React.useEffect(() => {
    if (confirmPasswordValue == '') {
      setValidatedConfirmPasswordValue('error')
    } else if (confirmPasswordValue.includes(' ')) {
      setValidatedConfirmPasswordValue('error')
    } else if (confirmPasswordValue.length < 4) {
      setValidatedConfirmPasswordValue('error')
    } else {
      setValidatedConfirmPasswordValue('success')
      comparePasswords()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [confirmPasswordValue])

  const handleProfileUsernameValueChange = (_ev, value) => {
    setProfileUsernameValue(value)
  }

  const handleCurrentPasswordValueChange = (_ev, value) => {
    setCurrentPasswordValue(value)
  }

  const handleNewPasswordValueChange = (_ev, value) => {
    setNewPasswordValue(value)
  }

  const handleConfirmPasswordValueChange = (_ev, value) => {
    setConfirmPasswordValue(value)
  }

  const profileInfoRef = React.createRef<HTMLElement>()
  const editPasswordRef = React.createRef<HTMLElement>()

  const EditUserProfile = (_username, _password) => {
    setMessageValue('')
    if (!auth.isLogged()) {
      return
    }

    const url = Constants.API_BASE_URL + Constants.API_USER_ENDPOINT
    let data = {
      'user-id': auth.userId,
      token: auth.token
    }

    if (_username != null && _username != undefined) {
      if (_username == auth.userName) {
        setMessageValue('The username you selected is your current one. No changes needed.')
        return
      }
      if (validatedProfileUsernameValue != 'success') {
        return
      }
      data['username'] = _username
    }

    if (_password != null && _password != undefined) {
      if (validatedCurrentPasswordValue != 'success') {
        return
      }
      if (validatedNewPasswordValue != 'success') {
        return
      }
      if (validatedConfirmPasswordValue != 'success') {
        return
      }
      if (currentPasswordValue == newPasswordValue) {
        setMessageValue('The password you selected is your current one. No changes needed.')
        return
      }
      data['password'] = _password
    }

    let status: number = 0
    let status_text: string = ''

    fetch(url, {
      method: 'PUT',
      headers: Constants.JSON_HEADER,
      body: JSON.stringify(data)
    })
      .then((response) => {
        status = response.status
        status_text = response.statusText
        if (status !== 200) {
          return response.text()
        } else {
          return response.json()
        }
      })
      .then((data) => {
        if (status != 200) {
          setMessageValue(Constants.getResponseErrorMessage(status, status_text, data))
        } else {
          setMessageValue(data['message'])
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
        bodyAriaLabel='UserProfileModal'
        aria-label='user profile modal'
        tabIndex={0}
        variant={ModalVariant.default}
        title='User Profile'
        description={'Edit your profile information'}
        isOpen={isModalOpen}
        onClose={handleModalToggle}
        actions={[]}
      >
        {messageValue ? (
          <Hint>
            <HintBody>{messageValue}</HintBody>
          </Hint>
        ) : (
          ''
        )}
        <Tabs activeKey={activeTabKey} onSelect={handleTabClick} aria-label='Add a New/Existing Test Case' role='region'>
          <Tab
            eventKey={0}
            id='tab-user-profile-info'
            title={<TabTitleText>Profile</TabTitleText>}
            tabContentId='tabUserProfile'
            tabContentRef={profileInfoRef}
          />
          <Tab
            eventKey={1}
            id='tab-user-edit-password'
            title={<TabTitleText>Edit Password</TabTitleText>}
            tabContentId='tabUserEditPassword'
            tabContentRef={editPasswordRef}
          />
        </Tabs>
        <div>
          <TabContent eventKey={0} id='tabUserProfile' ref={profileInfoRef} hidden={0 !== activeTabKey}>
            <TabContentBody hasPadding>
              <FormGroup label='Username' isRequired fieldId={`input-user-profile-username`}>
                <TextInput
                  isRequired
                  id={`input-user-profile-username`}
                  value={profileUsernameValue}
                  onChange={(_ev, value) => handleProfileUsernameValueChange(_ev, value)}
                />
                {validatedProfileUsernameValue !== 'success' && (
                  <FormHelperText>
                    <HelperText>
                      <HelperTextItem variant='error'>
                        {validatedProfileUsernameValue === 'error' ? 'This field is mandatory' : ''}
                      </HelperTextItem>
                    </HelperText>
                  </FormHelperText>
                )}
              </FormGroup>
              <br></br>
              <FormGroup label='Email' fieldId={`input-user-profile-email`}>
                <TextInput id={`input-user-profile-email`} readOnlyVariant={'default'} value={auth.userEmail} />
              </FormGroup>
              <br></br>
              <br></br>
              <Button id='btn-user-profile-save' onClick={() => EditUserProfile(profileUsernameValue, null)}>
                Save
              </Button>
            </TabContentBody>
          </TabContent>
          <TabContent eventKey={1} id='tabUserEditPassword' ref={editPasswordRef} hidden={1 !== activeTabKey}>
            <TabContentBody hasPadding>
              <FormGroup label='Current Password' isRequired fieldId={`input-user-edit-password-current`}>
                <TextInput
                  isRequired
                  type={'password'}
                  id={`input-user-edit-password-current`}
                  value={currentPasswordValue}
                  onChange={(_ev, value) => handleCurrentPasswordValueChange(_ev, value)}
                />
                {validatedCurrentPasswordValue !== 'success' && (
                  <FormHelperText>
                    <HelperText>
                      <HelperTextItem variant='error'>
                        {validatedCurrentPasswordValue === 'error' ? 'This field is mandatory' : ''}
                      </HelperTextItem>
                    </HelperText>
                  </FormHelperText>
                )}
              </FormGroup>
              <br></br>
              <FormGroup label='New Password' isRequired fieldId={`input-user-edit-password-new`}>
                <TextInput
                  isRequired
                  type={'password'}
                  id={`input-user-edit-password-new`}
                  value={newPasswordValue}
                  onChange={(_ev, value) => handleNewPasswordValueChange(_ev, value)}
                />
                {validatedNewPasswordValue !== 'success' && (
                  <FormHelperText>
                    <HelperText>
                      <HelperTextItem variant='error'>
                        {validatedNewPasswordValue === 'error' ? 'This field is mandatory' : ''}
                      </HelperTextItem>
                    </HelperText>
                  </FormHelperText>
                )}
              </FormGroup>
              <br></br>
              <FormGroup label='Confirm New Password' isRequired fieldId={`input-user-edit-password-confirm`}>
                <TextInput
                  isRequired
                  type={'password'}
                  id={`input-user-edit-password-confirm`}
                  value={confirmPasswordValue}
                  onChange={(_ev, value) => handleConfirmPasswordValueChange(_ev, value)}
                />
                {validatedConfirmPasswordValue !== 'success' && (
                  <FormHelperText>
                    <HelperText>
                      <HelperTextItem variant='error'>
                        {validatedConfirmPasswordValue === 'error' ? 'This field is mandatory' : ''}
                      </HelperTextItem>
                    </HelperText>
                  </FormHelperText>
                )}
              </FormGroup>
              <br></br>
              <br></br>
              <Button id='btn-user-edit-password-save' onClick={() => EditUserProfile(null, newPasswordValue)}>
                Save
              </Button>
            </TabContentBody>
          </TabContent>
        </div>
      </Modal>
    </React.Fragment>
  )
}
