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

  const toggleUserEnable = () => {
    console.log('here')

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
      </DropdownList>
    </Dropdown>
  )
}
