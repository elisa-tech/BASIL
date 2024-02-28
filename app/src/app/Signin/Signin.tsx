import * as React from 'react'
import * as Constants from '../Constants/constants'
import logo from '@app/bgimages/basil.svg'
import {
  Form,
  FormGroup,
  TextInput,
  Checkbox,
  Popover,
  ActionGroup,
  Button,
  Divider,
  Radio,
  HelperText,
  HelperTextItem,
  FormHelperText,
  PageGroup,
  PageSection,
  PageSectionVariants,
  Panel,
  PanelHeader,
  PanelMain,
  PanelMainBody,
  Flex,
  FlexItem,
  Text,
  TextVariants
} from '@patternfly/react-core'
import ExclamationCircleIcon from '@patternfly/react-icons/dist/esm/icons/exclamation-circle-icon'
import { useAuth } from '@app/User/AuthProvider'

const Signin: React.FunctionComponent = () => {
  let auth = useAuth()
  const [alertMessage, setAlertMessage] = React.useState('')
  const [email, setEmail] = React.useState('')
  const [password, setPassword] = React.useState('')
  const [passwordConfirm, setPasswordConfirm] = React.useState('')
  const [validateEmailValue, setValidateEmailValue] = React.useState<Constants.validate>('default')
  const [validatePasswordValue, setValidatePassworValue] = React.useState<Constants.validate>('default')
  const [validatePasswordConfirmValue, setValidatePasswordConfirmValue] = React.useState<Constants.validate>('default')
  const [validatePasswordValues, setValidatePasswordValues] = React.useState<Constants.validate>('default')

  const handlePasswordChange = (_event, password: string) => {
    setPassword(password)
  }

  const handlePasswordConfirmChange = (_event, password: string) => {
    setPasswordConfirm(password)
  }

  const handleEmailChange = (_event, email: string) => {
    setEmail(email)
  }

  const isEmail = (email) => /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,4}$/i.test(email)

  const comparePasswords = () => {
    if (password != passwordConfirm) {
      setValidatePasswordValues('error')
    } else {
      setValidatePasswordValues('success')
    }
  }

  React.useEffect(() => {
    if (email.trim() === '') {
      setValidateEmailValue('error')
    } else if (!isEmail(email)) {
      setValidateEmailValue('error2')
    } else {
      setValidateEmailValue('success')
    }
  }, [email])

  React.useEffect(() => {
    if (password.trim() === '') {
      setValidatePassworValue('error')
    } else {
      setValidatePassworValue('success')
      comparePasswords()
    }
  }, [password])

  React.useEffect(() => {
    if (passwordConfirm.trim() === '') {
      setValidatePasswordConfirmValue('error')
    } else {
      setValidatePasswordConfirmValue('success')
      comparePasswords()
    }
  }, [passwordConfirm])

  const resetForm = () => {
    setEmail('')
    setPassword('')
    setPasswordConfirm('')
  }

  const formSubmit = () => {
    if (auth.isLogged()) {
      setAlertMessage('You are already loogin in as ' + auth.userEmail)
      return
    }

    if (validateEmailValue != 'success') {
      setAlertMessage('Email is mandatory.')
      return
    } else if (validatePasswordValue != 'success') {
      setAlertMessage('Passord is mandatory.')
      return
    } else if (validatePasswordConfirmValue != 'success') {
      setAlertMessage('Password Confirm is mandatory.')
      return
    } else if (validatePasswordValues != 'success') {
      setAlertMessage('Password fields are not the same.')
      return
    } else {
      setAlertMessage('')
    }

    let data = { email: email, password: password }

    fetch(Constants.API_BASE_URL + '/user/signin', {
      method: 'POST',
      headers: {
        Accept: 'application/json',
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(data)
    })
      .then((response) => {
        if (response.status !== 200) {
          setAlertMessage(response.statusText)
        } else {
          setAlertMessage('User configured!')
          window.location.href = '/login'
        }
      })
      .catch((err) => {
        setAlertMessage(err.toString())
        console.log(err.message)
      })
  }

  return (
    <PageGroup stickyOnBreakpoint={{ default: 'top' }} hasShadowBottom>
      <PageSection variant={PageSectionVariants.light}>
        <Panel>
          <PanelHeader>
            <Text component={TextVariants.h1}>Sign In</Text>
            {alertMessage !== '' && (
              <FormHelperText>
                <HelperText>
                  <HelperTextItem variant='error'>{alertMessage}</HelperTextItem>
                </HelperText>
              </FormHelperText>
            )}
          </PanelHeader>
          <Divider />
          <PanelMain>
            <PanelMainBody>
              <Flex>
                <FlexItem align={{ default: 'alignLeft' }}>
                  <Form isWidthLimited>
                    <FormGroup label='Email' isRequired fieldId='signin-form-email-01'>
                      <TextInput
                        isRequired
                        type='email'
                        id='signin-form-email-01'
                        name='signin-form-email-01'
                        value={email}
                        onChange={handleEmailChange}
                      />
                      {validateEmailValue !== 'success' && (
                        <FormHelperText>
                          <HelperText>
                            <HelperTextItem variant='error'>
                              {validateEmailValue === 'error' ? 'This field is mandatory' : ''}
                            </HelperTextItem>
                          </HelperText>
                        </FormHelperText>
                      )}
                    </FormGroup>
                    <FormGroup label='Password' isRequired fieldId='signin-form-password-02'>
                      <TextInput
                        isRequired
                        type='password'
                        id='signin-form-password-02'
                        name='signin-form-password-02'
                        value={password}
                        onChange={handlePasswordChange}
                      />
                      {validatePasswordValue !== 'success' && (
                        <FormHelperText>
                          <HelperText>
                            <HelperTextItem variant='error'>
                              {validatePasswordValue === 'error' ? 'This field is mandatory' : ''}
                            </HelperTextItem>
                          </HelperText>
                        </FormHelperText>
                      )}
                    </FormGroup>
                    <FormGroup label='Password Confirm' isRequired fieldId='signin-form-password-confirm-03'>
                      <TextInput
                        isRequired
                        type='password'
                        id='signin-form-password-confirm-03'
                        name='signin-form-password-confirm-03'
                        value={passwordConfirm}
                        onChange={handlePasswordConfirmChange}
                      />
                      {validatePasswordConfirmValue !== 'success' && (
                        <FormHelperText>
                          <HelperText>
                            <HelperTextItem variant='error'>
                              {validatePasswordConfirmValue === 'error' ? 'This field is mandatory' : ''}
                            </HelperTextItem>
                          </HelperText>
                        </FormHelperText>
                      )}
                      {validatePasswordValues !== 'success' && (
                        <FormHelperText>
                          <HelperText>
                            <HelperTextItem variant='error'>
                              {validatePasswordValues === 'error' ? 'Passwords are not the same. Please check.' : ''}
                            </HelperTextItem>
                          </HelperText>
                        </FormHelperText>
                      )}
                    </FormGroup>
                    <ActionGroup>
                      <Button variant='primary' onClick={() => formSubmit()}>
                        Submit
                      </Button>
                      <Button onClick={() => resetForm()} variant='secondary'>
                        Reset
                      </Button>
                    </ActionGroup>
                  </Form>
                </FlexItem>
              </Flex>
            </PanelMainBody>
          </PanelMain>
        </Panel>
      </PageSection>
    </PageGroup>
  )
}

export { Signin }
