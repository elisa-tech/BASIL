//https://dev.to/miracool/how-to-manage-user-authentication-with-react-js-3ic5
import * as React from 'react';
import * as Constants from '../Constants/constants';
import { useContext, createContext, useState } from "react";
import { Redirect, useHistory } from "react-router-dom";

const AuthContext = createContext<any>({ /* ... */});

const AuthProvider = ({ children }) => {
  type ResponseData = {
    id: string;
    token: string;
    error: string;
  };

  let history = useHistory();
  const [userId, setUserId] = useState(localStorage.getItem("uId") || "");
  const [userRole, setUserRole] = useState(localStorage.getItem("uRole") || "");
  const [userEmail, setUserEmail] = useState(localStorage.getItem("uEmail") || "");
  const [token, setToken] = useState(localStorage.getItem("uToken") || "");
  const [loginState, setLoginState] = useState('waiting');
  const [loginMessage, setLoginMessage] = useState('');
  const loginAction = (data) => {
    try {
      let request_status = 0;
      let response_message = '';
      setLoginState('requested');
      const requestOptions = {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(data)
      };
      fetch(Constants.API_BASE_URL + '/user/login', requestOptions)
          .then(response => {
              request_status = response.status;
              response_message = response.statusText + ": ";
              return response.json();
            })
          .then(response_data => {
            if (typeof(response_data) == 'object'){
              if (response_data.hasOwnProperty("token")) {
                  setUserEmail(response_data.email);
                  setUserId(response_data.id);
                  setUserRole(response_data.role);
                  setToken(response_data.token);
                  localStorage.setItem("uEmail", response_data.email);
                  localStorage.setItem("uId", response_data.id);
                  localStorage.setItem("uRole", response_data.role);
                  localStorage.setItem("uToken", response_data.token);
                  setLoginState('done');
              } else {
                setLoginMessage(response_message + 'Invalid credentials');
                setLoginState('error');
              }
            } else {
              if (typeof(response_data) == 'string') {
                setLoginMessage(response_message + response_data);
                setLoginState('error');
              }
            }
          })
          .catch((err) => {
            console.log(err);
            setLoginState('error');
          })
    } catch (err) {
      console.log(err);
      setLoginState('error');
    }
  };

  const logOut = () => {
    console.log("logout");
    setUserEmail("");
    setUserId("");
    setUserRole("");
    setToken("");
    localStorage.removeItem("uEmail");
    localStorage.removeItem("uId");
    localStorage.removeItem("uToken");
    localStorage.removeItem("uRole");
    return <Redirect to={{
          pathname: "/dashboard",
          state: { from: location }
        }} />;
  };

  const isLogged = () => {
    //console.log("isLogged");
    //console.log(':::::: id:' + userId + ' email:' + userEmail + ' toekn:' + token + ' role:' + userRole);
    if ((userId != "") && (typeof(userId) != undefined) &&
        (userEmail != "") && (typeof(userEmail) != undefined) &&
        (token != "") && (typeof(token) != undefined) &&
        (userRole != "") && (typeof(userRole) != undefined)) {
      return true;
    } else {
      logOut();
      return false;
    }
  }

  const isAdmin = () => {
    if (isLogged()) {
      if (userRole == "ADMIN") {
        return true;
      } else {
        return false;
      }
    } else {
      return false;
    }
  }

  return (
    <AuthContext.Provider value={{ token, userEmail, userId, userRole, loginAction, logOut, isLogged, isAdmin }}>
      {children}
    </AuthContext.Provider>
  );

};

export default AuthProvider;

export const useAuth = () => {
  return useContext(AuthContext);
};
