import React from 'react'
import { Dropdown, DropdownItem, DropdownList, MenuToggle, MenuToggleElement } from '@patternfly/react-core'
import * as Constants from '../../Constants/constants'
import { useAuth } from '@app/User/AuthProvider'
import EllipsisVIcon from '@patternfly/react-icons/dist/esm/icons/ellipsis-v-icon'

export interface AdminMenuKebabProps {
  setModalAdminInfo
  user
}

export const AdminMenuKebab: React.FunctionComponent<AdminMenuKebabProps> = ({ setModalAdminInfo, user }: AdminMenuKebabProps) => {
  let auth = useAuth()
  const [isOpen, setIsOpen] = React.useState(false)

  const onToggleClick = () => {
    setIsOpen(!isOpen)
  }

  const onSelect = () => {
    setIsOpen(false)
  }

  const changeUserRole = (role) => {
    const data = {
      'user-id': auth.userId, // The one that request the change
      token: auth.token, // The one that request the change
      email: user.email, // The one that will be changed
      role: role
    }

    fetch(Constants.API_BASE_URL + '/user/role', {
      method: 'PUT',
      headers: {
        Accept: 'application/json',
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(data)
    })
      .then((response) => {
        if (response.status !== 200) {
          //setMessageValue(response.statusText);
        } else {
          location.reload()
        }
      })
      .catch((err) => {
        //setMessageValue(err.toString());
      })
  }

  const toggleUserEnable = () => {
    const data = {
      'user-id': auth.userId, // The one that request the change
      token: auth.token, // The one that request the change
      email: user.email, // The one that will be changed
      enabled: 1 - user.enabled
    }

    fetch(Constants.API_BASE_URL + '/user/enable', {
      method: 'PUT',
      headers: {
        Accept: 'application/json',
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(data)
    })
      .then((response) => {
        if (response.status !== 200) {
          //setMessageValue(response.statusText);
        } else {
          location.reload()
        }
      })
      .catch((err) => {
        //setMessageValue(err.toString());
      })
  }

  return (
    <Dropdown
      isOpen={isOpen}
      onSelect={onSelect}
      onOpenChange={(isOpen: boolean) => setIsOpen(isOpen)}
      toggle={(toggleRef: React.Ref<MenuToggleElement>) => (
        <MenuToggle ref={toggleRef} aria-label='kebab dropdown toggle' variant='plain' onClick={onToggleClick} isExpanded={isOpen}>
          <EllipsisVIcon />
        </MenuToggle>
      )}
      shouldFocusToggleOnSelect
    >
      <DropdownList>
        {auth.isLogged() && auth.isAdmin() ? (
          <DropdownItem
            value={0}
            id={'btn-menu-user-enable-' + user.id}
            key={'action enable user ' + user.id}
            onClick={() => toggleUserEnable()}
          >
            {user.enabled ? 'Disable' : 'Enable'}
          </DropdownItem>
        ) : (
          ''
        )}

        {auth.isLogged() && auth.isAdmin() ? (
          <DropdownItem
            value={0}
            id={'btn-menu-user-reset-password-' + user.id}
            key={'action reset user password' + user.id}
            onClick={() => setModalAdminInfo(user, true)}
          >
            Reset Password
          </DropdownItem>
        ) : (
          ''
        )}

        {auth.isLogged() && auth.isAdmin() && user.role != 'ADMIN' ? (
          <DropdownItem
            value={0}
            id={'btn-menu-user-role-admin-' + user.id}
            key={'action user role admin ' + user.id}
            onClick={() => changeUserRole('ADMIN')}
          >
            Set as ADMIN
          </DropdownItem>
        ) : (
          ''
        )}

        {auth.isLogged() && auth.isAdmin() && user.role != 'GUEST' ? (
          <DropdownItem
            value={0}
            id={'btn-menu-user-role-guest-' + user.id}
            key={'action user role guest ' + user.id}
            onClick={() => changeUserRole('GUEST')}
          >
            Set as GUEST
          </DropdownItem>
        ) : (
          ''
        )}

        {auth.isLogged() && auth.isAdmin() && user.role != 'USER' ? (
          <DropdownItem
            value={0}
            id={'btn-menu-user-role-user' + user.id}
            key={'action user role user ' + user.id}
            onClick={() => changeUserRole('USER')}
          >
            Set as USER
          </DropdownItem>
        ) : (
          ''
        )}
      </DropdownList>

    </Dropdown>
  )
}
