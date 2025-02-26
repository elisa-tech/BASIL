import * as React from 'react'
import logo from '@app/bgimages/basil.svg'
import background_image from '@app/bgimages/background.svg'
import { Button, Icon, ListItem, ListVariant, LoginFooterItem, LoginForm, LoginMainFooterBandItem, LoginPage } from '@patternfly/react-core'
import { Redirect, useLocation } from 'react-router-dom'
import ExclamationCircleIcon from '@patternfly/react-icons/dist/esm/icons/exclamation-circle-icon'
import { useAuth } from '../User/AuthProvider'
import * as Constants from '../Constants/constants'

const Login: React.FunctionComponent = () => {
  const location = useLocation()
  const auth = useAuth()
  const [showHelperText, setShowHelperText] = React.useState(false)
  const [helperText, setHelperText] = React.useState('')
  const [username, setUsername] = React.useState('')
  const [isValidUsername, setIsValidUsername] = React.useState(true)
  const [password, setPassword] = React.useState('')
  const [isValidPassword, setIsValidPassword] = React.useState(true)

  React.useEffect(() => {
      const query_params = Constants.getSearchParamsDict()
      if (Object.keys(query_params).includes("from")){
        if (query_params["from"] == "reset-password"){
          setHelperText('Your password has been reset. You can now login with the new password.')
          setShowHelperText(true)
        }
      }
      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [])

  const handleUsernameChange = (_event: React.FormEvent<HTMLInputElement>, value: string) => {
    setUsername(value)
    setHelperText('')
    setShowHelperText(false)
  }

  const handlePasswordChange = (_event: React.FormEvent<HTMLInputElement>, value: string) => {
    setPassword(value)
    setHelperText('')
    setShowHelperText(false)
  }

  const onLoginButtonClick = (event: React.MouseEvent<HTMLButtonElement, MouseEvent>) => {
    event.preventDefault()
    setIsValidUsername(!!username)
    setIsValidPassword(!!password)
    if (!username || !password) {
      setHelperText('Invalid credentials')
      setShowHelperText(true)
      return
    } else {
      setShowHelperText(false)
    }
    auth.loginAction({ email: username, password: password })
  }

  const onResetPassword = () => {
    if (!username) {
      setHelperText('Invalid email')
      setShowHelperText(true)
      return
    }
    const url = Constants.API_BASE_URL + Constants.API_USER_RESET_PASSWORD_ENDPOINT
    const data = {
      "email": username
    }

    fetch(url, {
      method: 'POST',
      headers: Constants.JSON_HEADER,
      body: JSON.stringify(data)
    })
    .then((res) => {
      if (!res.ok){
        return res.text()
      } else {
        return res.json()
      }
    })
    .then((data) => {
        if (Object.keys(data).includes("message")){
          setHelperText(data["message"])
        } else {
          setHelperText(data)
        }
        setShowHelperText(true)
    })
    .catch((err) => {
      setHelperText(err.message)
      setShowHelperText(true)
      console.log(err.message)
    })
  }

  React.useEffect(() => {
    if (typeof auth.loginMessage != 'undefined') {
      if (auth.loginMessage.length > 0) {
        setShowHelperText(true)
        setHelperText(auth.loginMessage)
      }
    }
  }, [auth.loginMessage])

  const signUpForAccountMessage = (
    <LoginMainFooterBandItem>
      Need an account? <a href='/signin'>Sign up.</a>
    </LoginMainFooterBandItem>
  )

  const forgotCredentials = (
    <LoginMainFooterBandItem>
      Forgot username or password? <Button variant='link' onClick={() => onResetPassword()}>Reset your password</Button>
    </LoginMainFooterBandItem>)

  const listItem = (
    <React.Fragment>
      <ListItem>
        <LoginFooterItem href='https://www.elisa.tech/'>ELISA</LoginFooterItem>
      </ListItem>
      <ListItem>
        <LoginFooterItem href='https://github.com/elisa-tech/BASIL'>Source Code (GitHub)</LoginFooterItem>
      </ListItem>
      <ListItem>
        <LoginFooterItem href='https://basil-the-fusa-spice.readthedocs.io/en/latest'>Documentation</LoginFooterItem>
      </ListItem>
    </React.Fragment>
  )

  const loginForm = (
    <LoginForm
      showHelperText={showHelperText}
      helperText={helperText} //'Invalid login credentials.'
      helperTextIcon={<Icon size={'md'}><ExclamationCircleIcon /></Icon>}
      usernameLabel='Email'
      usernameValue={username}
      onChangeUsername={handleUsernameChange}
      isValidUsername={isValidUsername}
      passwordLabel='Password'
      passwordValue={password}
      onChangePassword={handlePasswordChange}
      isValidPassword={isValidPassword}
      rememberMeLabel=''
      onLoginButtonClick={onLoginButtonClick}
      loginButtonLabel='Log in'
    />
  )

  return (
    <LoginPage
      footerListVariants={ListVariant.inline}
      brandImgSrc={logo}
      brandImgAlt='BASIL | The FuSa Spice'
      backgroundImgSrc={background_image}
      footerListItems={listItem}
      textContent='A Software Quality Management Tool.'
      loginTitle='Log in to your account'
      loginSubtitle=''
      socialMediaLoginContent=''
      socialMediaLoginAriaLabel=''
      signUpForAccountMessage={signUpForAccountMessage}
      forgotCredentials={forgotCredentials}
    >
      {!auth.isLogged() ? (
        loginForm
      ) : (
        <Redirect
          to={{
            pathname: '/',
            state: { from: location }
          }}
        />
      )}
    </LoginPage>
  )
}

export { Login }
