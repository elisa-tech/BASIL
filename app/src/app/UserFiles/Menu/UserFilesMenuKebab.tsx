import React from 'react'
import { Dropdown, DropdownItem, DropdownList, MenuToggle, MenuToggleElement } from '@patternfly/react-core'
import * as Constants from '../../Constants/constants'
import { useAuth } from '../../User/AuthProvider'
import EllipsisVIcon from '@patternfly/react-icons/dist/esm/icons/ellipsis-v-icon'

export interface UserFilesMenuKebabProps {
  modalAction
  modalFileName
  userFile
  setModalShowState
}

export const UserFilesMenuKebab: React.FunctionComponent<UserFilesMenuKebabProps> = ({
  userFile,
  modalAction,
  modalFileName,
  setModalShowState
}: UserFilesMenuKebabProps) => {
  const auth = useAuth()
  const [isOpen, setIsOpen] = React.useState(false)

  const onToggleClick = () => {
    setIsOpen(!isOpen)
  }

  const onSelect = () => {
    setIsOpen(false)
  }

  const editUserFile = (_filename: string) => {
    console.log('editUserFile - filename: ' + modalFileName.current)
    modalAction.current = 'edit'
    modalFileName.current = _filename
    setModalShowState(true)
  }

  const deleteUserFile = () => {
    const data = {
      'user-id': auth.userId, // The one that request the change
      token: auth.token, // The one that request the change
      filename: userFile.filename // The one that will be changed
    }

    fetch(Constants.API_BASE_URL + Constants.API_USER_FILES_ENDPOINT, {
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
          <>
            <DropdownItem
              value={0}
              id={'btn-menu-user-file-delete-' + userFile.index}
              key={'action user file delete ' + userFile.index}
              onClick={() => deleteUserFile()}
            >
              Delete
            </DropdownItem>
            <DropdownItem
              value={0}
              id={'btn-menu-user-file-edit-' + userFile.index}
              key={'action user file edit ' + userFile.index}
              onClick={() => editUserFile(userFile.filename)}
            >
              Edit
            </DropdownItem>
          </>
        ) : (
          ''
        )}
      </DropdownList>
    </Dropdown>
  )
}
