//https://dev.to/miracool/how-to-manage-user-authentication-with-react-js-3ic5
import * as React from 'react'
import * as Constants from '../Constants/constants'
import { createContext, useContext, useState } from 'react'
import { DEFAULT_AVATAR, UserAvatarData } from './Avatar/UserAvatar'

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
  const [token, setToken] = useState(localStorage.getItem('uToken') || '')
  const [loginMessage, setLoginMessage] = useState('')
  const [userAvatar, setUserAvatar] = useState<UserAvatarData>(DEFAULT_AVATAR)

  React.useEffect(() => {
    localStorage.setItem('uId', userId == null ? '' : userId)
    localStorage.setItem('uName', userName == null ? '' : userName)
    localStorage.setItem('uEmail', userEmail == null ? '' : userEmail)
    localStorage.setItem('uRole', userRole == null ? '' : userRole)
    localStorage.setItem('uToken', token == null ? '' : token)
  }, [userId, userRole, userEmail, userName, token])

  const loadUserAvatar = React.useCallback(() => {
    if (!userId || !token) {
      setUserAvatar(DEFAULT_AVATAR)
      return
    }
    let url = Constants.API_BASE_URL + Constants.API_USER_AVATAR_ENDPOINT
    url += '?user-id=' + userId
    url += '&token=' + token
    fetch(url, { method: 'GET', headers: Constants.JSON_HEADER })
      .then((res) => (res.ok ? res.json() : DEFAULT_AVATAR))
      .then((data) => setUserAvatar(data))
      .catch(() => setUserAvatar(DEFAULT_AVATAR))
  }, [userId, token])

  React.useEffect(() => {
    loadUserAvatar()
  }, [loadUserAvatar])

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
              setUserEmail(response_data['email'])
              setUserName(response_data['username'])
              setUserId(response_data['id'])
              setUserRole(response_data['role'])
              setToken(response_data['token'])
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
    setToken('')
    localStorage.removeItem('uEmail')
    localStorage.removeItem('uName')
    localStorage.removeItem('uId')
    localStorage.removeItem('uToken')
    localStorage.removeItem('uRole')
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
        userAvatar,
        setUserAvatar,
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
