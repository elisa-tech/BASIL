import React from 'react'
import { Dropdown, DropdownItem, DropdownList, MenuToggle, MenuToggleElement } from '@patternfly/react-core'
import * as Constants from '../../Constants/constants'
import { useAuth } from '../../User/AuthProvider'
import EllipsisVIcon from '@patternfly/react-icons/dist/esm/icons/ellipsis-v-icon'

export interface SSHKeyMenuKebabProps {
  sshKey
}

export const SSHKeyMenuKebab: React.FunctionComponent<SSHKeyMenuKebabProps> = ({ sshKey }: SSHKeyMenuKebabProps) => {
  const auth = useAuth()
  const [isOpen, setIsOpen] = React.useState(false)

  const onToggleClick = () => {
    setIsOpen(!isOpen)
  }

  const onSelect = () => {
    setIsOpen(false)
  }

  const deleteSSHKey = () => {
    const data = {
      'user-id': auth.userId, // The one that request the change
      token: auth.token, // The one that request the change
      id: sshKey.id // The one that will be changed
    }

    fetch(Constants.API_BASE_URL + '/user/ssh-key', {
      method: 'DELETE',
      headers: Constants.JSON_HEADER,
      body: JSON.stringify(data)
    })
      .then((response) => {
        if (response.status !== 200) {
          console.log(response.status)
        } else {
          location.reload()
        }
      })
      .catch((err) => {
        console.log(err)
      })
  }

  return (
    <Dropdown
      popperProps={{ position: 'right' }}
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
        {auth.isLogged() && !auth.isGuest() ? (
          <DropdownItem
            value={0}
            id={'btn-menu-user-ssh-key-delete-' + sshKey.id}
            key={'action user ssh key delete ' + sshKey.id}
            onClick={() => deleteSSHKey()}
          >
            Delete
          </DropdownItem>
        ) : (
          ''
        )}
      </DropdownList>
    </Dropdown>
  )
}
