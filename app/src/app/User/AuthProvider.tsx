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
  const [userEmail, setUserEmail] = useState(localStorage.getItem('uEmail') || '')
  const [token, setToken] = useState(localStorage.getItem('uToken') || '')

  React.useEffect(() => {
    localStorage.setItem('uId', userId == null ? '' : userId)
    localStorage.setItem('uEmail', userEmail == null ? '' : userEmail)
    localStorage.setItem('uRole', userRole == null ? '' : userRole)
    localStorage.setItem('uToken', token == null ? '' : token)
  }, [userId, userRole, userEmail, token])

  const loginAction = (data) => {
    try {
      const requestOptions = {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      }
      fetch(Constants.API_BASE_URL + '/user/login', requestOptions)
        .then((response) => {
          return response.json()
        })
        .then((response_data) => {
          if (typeof response_data == 'object') {
            //if (response_data.hasOwnProperty('token')) {
            if (Object.prototype.hasOwnProperty.call(response_data, 'token')) {
              setUserEmail(response_data['email'])
              setUserId(response_data['id'])
              setUserRole(response_data['role'])
              setToken(response_data['token'])
              window.location.href = '/'
            }
          }
        })
        .catch((err) => {
          console.log(err)
        })
    } catch (err) {
      console.log(err)
    }
  }

  const logOut = () => {
    console.log('logout')
    setUserEmail('')
    setUserId('')
    setUserRole('')
    setToken('')
    localStorage.removeItem('uEmail')
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
    <AuthContext.Provider value={{ token, userEmail, userId, userRole, loginAction, logOut, isLogged, isAdmin, isGuest }}>
      {children}
    </AuthContext.Provider>
  )
}

export default AuthProvider

export const useAuth = () => {
  return useContext(AuthContext)
}
