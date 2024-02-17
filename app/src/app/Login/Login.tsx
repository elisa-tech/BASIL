import * as React from 'react';
import * as Constants from '../Constants/constants';
import logo from '@app/bgimages/basil.svg';
import {
  LoginFooterItem,
  LoginForm,
  LoginMainFooterBandItem,
  LoginMainFooterLinksItem,
  LoginPage,
  ListItem,
  ListVariant
} from '@patternfly/react-core';
import { Redirect, useHistory, useLocation } from "react-router-dom";
import ExclamationCircleIcon from '@patternfly/react-icons/dist/esm/icons/exclamation-circle-icon';
import { useAuth } from '@app/User/AuthProvider';

const Login: React.FunctionComponent = () => {
  const location = useLocation();
  let auth = useAuth();
  const [showHelperText, setShowHelperText] = React.useState(false);
  const [helperText, setHelperText] = React.useState('');
  const [username, setUsername] = React.useState('');
  const [isValidUsername, setIsValidUsername] = React.useState(true);
  const [password, setPassword] = React.useState('');
  const [isValidPassword, setIsValidPassword] = React.useState(true);

  const handleUsernameChange = (_event: React.FormEvent<HTMLInputElement>, value: string) => {
    setUsername(value);
    setHelperText('');
  };

  const handlePasswordChange = (_event: React.FormEvent<HTMLInputElement>, value: string) => {
    setPassword(value);
    setHelperText('');
  };

  const onLoginButtonClick = (event: React.MouseEvent<HTMLButtonElement, MouseEvent>) => {
    event.preventDefault();
    setIsValidUsername(!!username);
    setIsValidPassword(!!password);
    if (!username || !password){
      setHelperText('Invalid credentials');
      setShowHelperText(true);
      return;
    }
    auth.loginAction({"email": username, "password": password});
    setHelperText(auth.loginMessage);
    setShowHelperText(true);
  };

  const signUpForAccountMessage = (
    <LoginMainFooterBandItem>
      Need an account? <a href="/signin">Sign up.</a>
    </LoginMainFooterBandItem>
  );

  const forgotCredentials = (
    <LoginMainFooterBandItem>
      Forgot username or password? Please contact your BASIL admin.
    </LoginMainFooterBandItem>
  );

  const listItem = (
    <React.Fragment>
      <ListItem>
        <LoginFooterItem href="https://www.elisa.tech/">ELISA</LoginFooterItem>
      </ListItem>
      <ListItem>
        <LoginFooterItem href="https://github.com/elisa-tech/BASIL">Source Code (GitHub)</LoginFooterItem>
      </ListItem>
      <ListItem>
        <LoginFooterItem href="https://basil-the-fusa-spice.readthedocs.io/en/latest">Documentation</LoginFooterItem>
      </ListItem>
    </React.Fragment>
  );

  const loginForm = (
    <LoginForm
      showHelperText={showHelperText}
      helperText="Invalid login credentials."
      helperTextIcon={<ExclamationCircleIcon />}
      usernameLabel="Username"
      usernameValue={username}
      onChangeUsername={handleUsernameChange}
      isValidUsername={isValidUsername}
      passwordLabel="Password"
      passwordValue={password}
      onChangePassword={handlePasswordChange}
      isValidPassword={isValidPassword}
      rememberMeLabel=""
      onLoginButtonClick={onLoginButtonClick}
      loginButtonLabel="Log in"
    />
  );

  return (
    <LoginPage
      footerListVariants={ListVariant.inline}
      brandImgSrc={logo}
      brandImgAlt="BASIL | The FuSa Spice"
      backgroundImgSrc="/assets/images/pfbg-icon.svg"
      footerListItems={listItem}
      textContent="A Software Quality Management Tool."
      loginTitle="Log in to your account"
      loginSubtitle=""
      socialMediaLoginContent=""
      socialMediaLoginAriaLabel=""
      signUpForAccountMessage={signUpForAccountMessage}
      forgotCredentials={forgotCredentials}
    >
      { !auth.isLogged() ?
        (loginForm) :
        (<Redirect to={{
              pathname: "/",
              state: { from: location }
            }} />)
       }
    </LoginPage>
  );
};

export { Login };
