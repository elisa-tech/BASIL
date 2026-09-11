//https://dev.to/miracool/how-to-manage-user-authentication-with-react-js-3ic5
import * as React from 'react'
import * as Constants from '../Constants/constants'
import { createContext, useContext, useState } from 'react'

// eslint-disable-next-line  @typescript-eslint/no-explicit-any
const AuthContext = createContext<any>({
  /* ... */
})

const AuthProvider = ({ children }) => {
  /*
  type ResponseData = {
    id: string
    token: string
    error: string
  }
  */

  const [userId, setUserId] = useState(localStorage.getItem('uId') || '')
  const [userRole, setUserRole] = useState(localStorage.getItem('uRole') || '')
  const [userName, setUserName] = useState(localStorage.getItem('uName') || '')
  const [userEmail, setUserEmail] = useState(localStorage.getItem('uEmail') || '')
  const [spdxSignature, setSpdxSignature] = useState(localStorage.getItem('uSpdxSignature') || '')
  const [token, setToken] = useState(localStorage.getItem('uToken') || '')
  const [loginMessage, setLoginMessage] = useState('')

  React.useEffect(() => {
    localStorage.setItem('uId', userId == null ? '' : userId)
    localStorage.setItem('uName', userName == null ? '' : userName)
    localStorage.setItem('uEmail', userEmail == null ? '' : userEmail)
    localStorage.setItem('uRole', userRole == null ? '' : userRole)
    localStorage.setItem('uSpdxSignature', spdxSignature == null ? '' : spdxSignature)
    localStorage.setItem('uToken', token == null ? '' : token)
  }, [userId, userRole, userEmail, userName, spdxSignature, token])

  const loginAction = (data) => {
    setLoginMessage('')
    try {
      const requestOptions = {
        method: 'POST',
        headers: Constants.JSON_HEADER,
        body: JSON.stringify(data)
      }
      fetch(Constants.API_BASE_URL + Constants.API_USER_LOGIN_ENDPOINT, requestOptions)
        .then((res) => {
          return res.json()
        })
        .then((response_data) => {
          if (typeof response_data == 'object') {
            //if (response_data.hasOwnProperty('token')) {
            if (Object.prototype.hasOwnProperty.call(response_data, 'token')) {
              const nextEmail = response_data['email'] == null ? '' : String(response_data['email'])
              const nextName = response_data['username'] == null ? '' : String(response_data['username'])
              const nextId = response_data['id'] == null ? '' : String(response_data['id'])
              const nextRole = response_data['role'] == null ? '' : String(response_data['role'])
              const nextSignature = response_data['spdx_signature'] == null ? '' : String(response_data['spdx_signature'])
              const nextToken = response_data['token'] == null ? '' : String(response_data['token'])
              localStorage.setItem('uEmail', nextEmail)
              localStorage.setItem('uName', nextName)
              localStorage.setItem('uId', nextId)
              localStorage.setItem('uRole', nextRole)
              localStorage.setItem('uSpdxSignature', nextSignature)
              localStorage.setItem('uToken', nextToken)
              setUserEmail(nextEmail)
              setUserName(nextName)
              setUserId(nextId)
              setUserRole(nextRole)
              setSpdxSignature(nextSignature)
              setToken(nextToken)
              setLoginMessage('Logged with success.')
              window.location.href = '/'
            } else {
              setLoginMessage(response_data)
            }
          } else {
            setLoginMessage(response_data)
          }
        })
        .catch((err) => {
          console.log(err)
          setLoginMessage('Error: ' + err)
        })
    } catch (err) {
      console.log(err)
      setLoginMessage('Error: ' + err)
    }
  }

  const logOut = () => {
    console.log('logout')
    setUserEmail('')
    setUserName('')
    setUserId('')
    setUserRole('')
    setSpdxSignature('')
    setToken('')
    localStorage.removeItem('uEmail')
    localStorage.removeItem('uName')
    localStorage.removeItem('uId')
    localStorage.removeItem('uToken')
    localStorage.removeItem('uRole')
    localStorage.removeItem('uSpdxSignature')
    window.location.href = '/'
  }

  const isLogged = () => {
    if (
      userId != '' &&
      userId != null &&
      userEmail != '' &&
      userEmail != null &&
      token != '' &&
      token != null &&
      userRole != '' &&
      userRole != null
    ) {
      return true
    } else {
      //logOut();
      return false
    }
  }

  const isGuest = () => {
    if (isLogged()) {
      if (userRole == 'GUEST') {
        return true
      } else {
        return false
      }
    } else {
      return true
    }
  }

  const isAdmin = () => {
    if (isLogged()) {
      if (userRole == 'ADMIN') {
        return true
      } else {
        return false
      }
    } else {
      return false
    }
  }

  return (
    <AuthContext.Provider
      value={{
        token,
        userEmail,
        userName,
        userId,
        userRole,
        spdxSignature,
        setSpdxSignature,
        loginAction,
        loginMessage,
        logOut,
        isLogged,
        isAdmin,
        isGuest
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export default AuthProvider

export const useAuth = () => {
  return useContext(AuthContext)
}
