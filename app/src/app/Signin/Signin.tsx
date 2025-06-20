import * as React from 'react'
import * as Constants from '../Constants/constants'
import {
  ActionGroup,
  Bullseye,
  Button,
  Divider,
  Flex,
  FlexItem,
  Form,
  FormGroup,
  FormHelperText,
  HelperText,
  HelperTextItem,
  PageGroup,
  PageSection,
  PageSectionVariants,
  Panel,
  PanelHeader,
  PanelMain,
  PanelMainBody,
  TextInput,
  Title
} from '@patternfly/react-core'
import { useAuth } from '../User/AuthProvider'

const Signin: React.FunctionComponent = () => {
  const auth = useAuth()
  const [alertMessage, setAlertMessage] = React.useState('')
  const [usernameValue, setUsernameValue] = React.useState('')
  const [emailValue, setEmailValue] = React.useState('')
  const [passwordValue, setPasswordValue] = React.useState('')
  const [passwordConfirmValue, setPasswordConfirmValue] = React.useState('')
  const [validateUsernameValue, setValidateUsernameValue] = React.useState<Constants.validate>('default')
  const [validateEmailValue, setValidateEmailValue] = React.useState<Constants.validate>('default')
  const [validatePasswordValue, setValidatePassworValue] = React.useState<Constants.validate>('default')
  const [validatePasswordConfirmValue, setValidatePasswordConfirmValue] = React.useState<Constants.validate>('default')
  const [validatePasswordValues, setValidatePasswordValues] = React.useState<Constants.validate>('default')

  const handlePasswordChange = (_event, password: string) => {
    setPasswordValue(password)
  }

  const handlePasswordConfirmChange = (_event, confirm_password: string) => {
    setPasswordConfirmValue(confirm_password)
  }

  const handleUsernameChange = (_event, username: string) => {
    setUsernameValue(username)
  }

  const handleEmailChange = (_event, email: string) => {
    setEmailValue(email)
  }

  const isEmail = (email) => /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,4}$/i.test(email)

  const comparePasswords = () => {
    if (passwordValue != passwordConfirmValue) {
      setValidatePasswordValues('error')
    } else {
      setValidatePasswordValues('success')
    }
  }

  React.useEffect(() => {
    if (usernameValue == '') {
      setValidateUsernameValue('error')
    } else if (usernameValue.includes(' ')) {
      setValidateUsernameValue('error')
    } else if (usernameValue.length < 4) {
      setValidateUsernameValue('error')
    } else {
      setValidateUsernameValue('success')
    }
  }, [usernameValue])

  React.useEffect(() => {
    if (emailValue == '') {
      setValidateEmailValue('error')
    } else if (emailValue.includes(' ')) {
      setValidateEmailValue('error')
    } else if (!isEmail(emailValue)) {
      setValidateEmailValue('error')
    } else {
      setValidateEmailValue('success')
    }
  }, [emailValue])

  React.useEffect(() => {
    if (passwordValue == '') {
      setValidatePassworValue('error')
    } else if (passwordValue.includes(' ')) {
      setValidatePassworValue('error')
    } else if (passwordValue.length < 4) {
      setValidatePassworValue('error')
    } else {
      setValidatePassworValue('success')
      comparePasswords()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [passwordValue])

  React.useEffect(() => {
    if (passwordConfirmValue == '') {
      setValidatePasswordConfirmValue('error')
    } else if (passwordConfirmValue.includes(' ')) {
      setValidatePasswordConfirmValue('error')
    } else if (passwordConfirmValue.length < 4) {
      setValidatePasswordConfirmValue('error')
    } else {
      setValidatePasswordConfirmValue('success')
      comparePasswords()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [passwordConfirmValue])

  const resetForm = () => {
    setUsernameValue('has been reset')
    setEmailValue('has been reset')
    setPasswordValue('')
    setPasswordConfirmValue('')
  }

  const formSubmit = () => {
    if (auth.isLogged()) {
      setAlertMessage('You are already loogin in as ' + auth.userEmail)
      return
    }

    if (validateEmailValue != 'success') {
      setAlertMessage('Email is not valid')
      return
    } else if (validateUsernameValue != 'success') {
      setAlertMessage('Username is not valid, It must be at least 4 chars, space char is not allowed')
      return
    } else if (validatePasswordValue != 'success') {
      setAlertMessage('Passord is not valid')
      return
    } else if (validatePasswordConfirmValue != 'success') {
      setAlertMessage('Confirm password is not valid')
      return
    } else if (validatePasswordValues != 'success') {
      setAlertMessage('Password fields are not the same')
      return
    } else {
      setAlertMessage('')
    }

    const data = {
      email: emailValue,
      password: passwordValue,
      username: usernameValue
    }

    let status
    let status_text
    fetch(Constants.API_BASE_URL + Constants.API_USER_SIGNIN_ENDPOINT, {
      method: 'POST',
      headers: Constants.JSON_HEADER,
      body: JSON.stringify(data)
    })
      .then((response) => {
        status = response.status
        status_text = response.statusText
        if (response.status == 200) {
          setAlertMessage('User created!')
          window.location.href = '/login'
          return response.json()
        } else {
          return response.json()
        }
      })
      .then((data) => {
        if (status != 200) {
          setAlertMessage(Constants.getResponseErrorMessage(status, status_text, data))
        }
      })
      .catch((err) => {
        setAlertMessage(err.toString())
        console.log(err.message)
      })
  }

  return (
    <PageGroup stickyOnBreakpoint={{ default: 'top' }} hasShadowBottom>
      <PageSection variant={PageSectionVariants.dark}>
        <Bullseye>
          <Panel variant='raised'>
            <PanelHeader>
              <Title headingLevel='h1'>Sign In</Title>
              {alertMessage !== '' && (
                <FormHelperText>
                  <HelperText>
                    <HelperTextItem variant='warning'>{alertMessage}</HelperTextItem>
                  </HelperText>
                </FormHelperText>
              )}
            </PanelHeader>
            <Divider />
            <PanelMain>
              <PanelMainBody>
                <Flex>
                  <FlexItem align={{ default: 'alignLeft' }}>
                    <Form isHorizontal>
                      <FormGroup label='Email' isRequired fieldId='signin-form-email'>
                        <TextInput isRequired type='email' id='signin-form-email' value={emailValue} onChange={handleEmailChange} />
                        {validateEmailValue !== 'success' && (
                          <FormHelperText>
                            <HelperText>
                              <HelperTextItem variant='warning'>
                                {validateEmailValue === 'error'
                                  ? 'This field is mandatory, the current value is not valid. It must be an email address and space char is not allowed.'
                                  : ''}
                              </HelperTextItem>
                            </HelperText>
                          </FormHelperText>
                        )}
                      </FormGroup>
                      <FormGroup label='Username' isRequired fieldId='signin-form-username'>
                        <TextInput isRequired type='text' id='signin-form-username' value={usernameValue} onChange={handleUsernameChange} />
                        {validateUsernameValue !== 'success' && (
                          <FormHelperText>
                            <HelperText>
                              <HelperTextItem variant='warning'>
                                {validateUsernameValue === 'error'
                                  ? 'This field is mandatory, the current value is not valid. It must be at least 4 chars and space char is not allowed.'
                                  : ''}
                              </HelperTextItem>
                            </HelperText>
                          </FormHelperText>
                        )}
                      </FormGroup>
                      <FormGroup label='Password' isRequired fieldId='signin-form-password'>
                        <TextInput
                          isRequired
                          type='password'
                          id='signin-form-password'
                          value={passwordValue}
                          onChange={handlePasswordChange}
                        />
                        {validatePasswordValue !== 'success' && (
                          <FormHelperText>
                            <HelperText>
                              <HelperTextItem variant='warning'>
                                {validatePasswordValue === 'error'
                                  ? 'This field is mandatory, the current value is not valid. It should be at least 4 chars and space char is not allowed.'
                                  : ''}
                              </HelperTextItem>
                            </HelperText>
                          </FormHelperText>
                        )}
                      </FormGroup>
                      <FormGroup label='Password Confirm' isRequired fieldId='signin-form-password-confirm'>
                        <TextInput
                          isRequired
                          type='password'
                          id='signin-form-password-confirm'
                          value={passwordConfirmValue}
                          onChange={handlePasswordConfirmChange}
                        />
                        {validatePasswordConfirmValue !== 'success' && (
                          <FormHelperText>
                            <HelperText>
                              <HelperTextItem variant='warning'>
                                {validatePasswordConfirmValue === 'error'
                                  ? 'This field is mandatory, the current value is not valid. It should be at least 4 chars and space char is not allowed.'
                                  : ''}
                              </HelperTextItem>
                            </HelperText>
                          </FormHelperText>
                        )}
                        {validatePasswordValues !== 'success' && (
                          <FormHelperText>
                            <HelperText>
                              <HelperTextItem variant='warning'>
                                {validatePasswordValues === 'error' ? 'Passwords are not the same. Please check.' : ''}
                              </HelperTextItem>
                            </HelperText>
                          </FormHelperText>
                        )}
                      </FormGroup>
                      <ActionGroup>
                        <Button id='form-signin-submit' variant='primary' onClick={() => formSubmit()}>
                          Submit
                        </Button>
                        <Button id='form-signin-reset' onClick={() => resetForm()} variant='secondary'>
                          Reset
                        </Button>
                      </ActionGroup>
                    </Form>
                  </FlexItem>
                </Flex>
              </PanelMainBody>
            </PanelMain>
          </Panel>
        </Bullseye>
      </PageSection>
    </PageGroup>
  )
}

export { Signin }
