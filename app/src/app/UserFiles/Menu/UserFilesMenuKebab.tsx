import React from 'react'
import { Dropdown, DropdownItem, DropdownList, MenuToggle, MenuToggleElement } from '@patternfly/react-core'
import { useAuth } from '../../User/AuthProvider'
import EllipsisVIcon from '@patternfly/react-icons/dist/esm/icons/ellipsis-v-icon'

export interface UserFilesMenuKebabProps {
  modalAction
  modalFileName
  modalRelativePath
  userFile
  setModalShowState
}

export const UserFilesMenuKebab: React.FunctionComponent<UserFilesMenuKebabProps> = ({
  userFile,
  modalAction,
  modalFileName,
  modalRelativePath,
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

  const openModal = (action: string) => {
    modalAction.current = action
    modalFileName.current = userFile.name
    modalRelativePath.current = userFile.relative_path
    setModalShowState(true)
  }

  const isDirectory = userFile.type === 'directory'

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
            {!isDirectory && (
              <DropdownItem
                value={0}
                id={'btn-menu-user-file-edit-' + userFile.index}
                key={'action user file edit ' + userFile.index}
                onClick={() => openModal('edit')}
              >
                Edit
              </DropdownItem>
            )}
            <DropdownItem
              value={0}
              id={'btn-menu-user-file-rename-' + userFile.index}
              key={'action user file rename ' + userFile.index}
              onClick={() => openModal('rename')}
            >
              Rename
            </DropdownItem>
            <DropdownItem
              value={0}
              id={'btn-menu-user-file-move-' + userFile.index}
              key={'action user file move ' + userFile.index}
              onClick={() => openModal('move')}
            >
              Move
            </DropdownItem>
            <DropdownItem
              value={0}
              id={'btn-menu-user-file-delete-' + userFile.index}
              key={'action user file delete ' + userFile.index}
              onClick={() => openModal('delete')}
              style={{ color: '#c9190b' }}
            >
              Delete
            </DropdownItem>
          </>
        ) : (
          ''
        )}
      </DropdownList>
    </Dropdown>
  )
}
