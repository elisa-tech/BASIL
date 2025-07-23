import React from 'react'
import * as Constants from '../../Constants/constants'
import { Dropdown, DropdownItem, DropdownList, MenuToggle, MenuToggleElement } from '@patternfly/react-core'
import { useAuth } from '../../User/AuthProvider'
import EllipsisVIcon from '@patternfly/react-icons/dist/esm/icons/ellipsis-v-icon'

export interface ApiMenuKebabProps {
  setModalInfo
  setModalCheckSpecInfo
  setModalDeleteInfo
  setModalManageUserPermissionsInfo
  setModalNotificationInfo
  apiData
}

export const ApiMenuKebab: React.FunctionComponent<ApiMenuKebabProps> = ({
  setModalInfo,
  setModalCheckSpecInfo,
  setModalDeleteInfo,
  setModalManageUserPermissionsInfo,
  apiData,
  setModalNotificationInfo
}: ApiMenuKebabProps) => {
  const auth = useAuth()
  const [isOpen, setIsOpen] = React.useState(false)

  const onToggleClick = () => {
    setIsOpen(!isOpen)
  }

  const onSelect = () => {
    setIsOpen(false)
  }

  const writePermissionRequest = (api_id) => {
    //let response_status
    let response_data

    const url = Constants.API_BASE_URL + Constants.API_REQUEST_WRITE_PERMISSION_ENDPOINT
    const data = {
      'api-id': api_id,
      'user-id': auth.userId,
      token: auth.token
    }

    fetch(url, {
      method: 'PUT',
      headers: Constants.JSON_HEADER,
      body: JSON.stringify(data)
    })
      .then((response) => {
        response_data = response.json()
        if (!response.ok) {
          throw new Error(`HTTP error! Status: ${response.status}`)
        } else {
          location.reload()
        }
        return response_data
      })
      .catch((err) => {
        setModalNotificationInfo('HTTP Error', 'Api is not available, application failed to fetch data.', true)
        console.error('Fetch error:', err)
      })
  }

  const toggleUserNotifications = (api_id) => {
    //let response_status
    let response_data

    const url = Constants.API_BASE_URL + '/user/notifications'
    const data = { 'api-id': api_id, notifications: 1 - apiData.notifications, 'user-id': auth.userId, token: auth.token }
    fetch(url, {
      method: 'PUT',
      headers: Constants.JSON_HEADER,
      body: JSON.stringify(data)
    })
      .then((response) => {
        //response_status = response.status
        response_data = response.json()
        if (response.status !== 200) {
          return
        } else {
          location.reload()
        }
        return response_data
      })
      .catch((err) => {
        console.log(err.message)
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
        {auth.isLogged() && apiData['permissions'].indexOf('e') > 0 ? (
          <DropdownItem
            value={0}
            id={'btn-menu-api-check-spec-' + apiData.id}
            key='action check different spec'
            onClick={() => setModalCheckSpecInfo(apiData, true)}
          >
            Check Spec
          </DropdownItem>
        ) : (
          ''
        )}

        {auth.isLogged() && apiData['permissions'].indexOf('e') > 0 ? (
          <DropdownItem
            value={1}
            id={'btn-menu-api-delete-' + apiData.id}
            className='danger-text'
            key='action delete'
            onClick={() =>
              setModalDeleteInfo(
                apiData,
                true,
                'Delete ' + apiData.api + ' and all related work items and mapping information?',
                'Do you want to delete selected api and all related work items and mapping information?'
              )
            }
          >
            Delete
          </DropdownItem>
        ) : (
          ''
        )}

        {auth.isLogged() && apiData['permissions'].indexOf('m') > 0 ? (
          <DropdownItem
            value={0}
            id={'btn-menu-api-manage-permissions-' + apiData.id}
            key='action manage user permissions'
            onClick={() => setModalManageUserPermissionsInfo(apiData, true)}
          >
            Manage User Permissions
          </DropdownItem>
        ) : (
          ''
        )}

        {auth.isLogged() && apiData['permissions'].indexOf('e') > 0 ? (
          <DropdownItem
            value={2}
            id={'btn-menu-api-new-version-' + apiData.id}
            key='action new version'
            onClick={() =>
              setModalInfo(
                apiData,
                true,
                'api',
                'POST',
                'fork',
                'Create a new Version of "' + apiData.api + '" from "' + apiData.library + '"',
                'Information are prepopulated with the current version'
              )
            }
          >
            New Version
          </DropdownItem>
        ) : (
          ''
        )}

        {!auth.isGuest() &&
        apiData?.['write_permission_request'] === 0 &&
        apiData?.['permissions'].indexOf('m') < 0 &&
        apiData?.['permissions'].indexOf('w') < 0 ? (
          <DropdownItem
            value={0}
            id={'btn-menu-api-write-premission-request-' + apiData.id}
            key='action write permission request'
            onClick={() => writePermissionRequest(apiData.id)}
          >
            Request write permission
          </DropdownItem>
        ) : (
          ''
        )}

        {auth.isLogged() ? (
          <DropdownItem
            value={0}
            id={'btn-menu-api-toggle-notifications-' + apiData.id}
            key='action manage user notifications'
            onClick={() => toggleUserNotifications(apiData.id)}
          >
            {apiData.notifications == 1 ? 'Disable notifications' : 'Enable notifications'}
          </DropdownItem>
        ) : (
          ''
        )}
      </DropdownList>
    </Dropdown>
  )
}
