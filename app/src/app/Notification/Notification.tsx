import React from 'react'
import {
  NotificationDrawer,
  NotificationDrawerBody,
  NotificationDrawerHeader,
  NotificationDrawerList,
  NotificationDrawerListItem,
  NotificationDrawerListItemBody,
  NotificationDrawerListItemHeader,
  Dropdown,
  DropdownList,
  DropdownItem,
  MenuToggle,
  MenuToggleElement
} from '@patternfly/react-core'
import * as Constants from '../Constants/constants'
import EllipsisVIcon from '@patternfly/react-icons/dist/esm/icons/ellipsis-v-icon'
import { useAuth } from '@app/User/AuthProvider'

interface Notification {
  api: string
  notification: string
  read_by?: string
  url: string
}

export interface NotificationDrawerBasicProps {
  notifications
  notificationDrawerExpanded
  setNotificationDrawerExpanded
}
export const NotificationDrawerBasic: React.FunctionComponent<NotificationDrawerBasicProps> = ({
  notifications,
  notificationDrawerExpanded,
  setNotificationDrawerExpanded
}: NotificationDrawerBasicProps) => {
  let auth = useAuth()
  const [isOpenHeaderDropdown, setIsOpenHeaderDropdown] = React.useState(false)
  const [isOpenMap, setIsOpenMap] = React.useState(new Array(notifications.length).fill(false))

  const onToggle = (index: number) => () => {
    let currentState = isOpenMap[index]
    let newStates = new Array(notifications.length).fill(false)
    newStates[index] = !currentState
    setIsOpenHeaderDropdown(false)
    setIsOpenMap(newStates)
  }

  const toggleNotificationDrawer = () => {
    setNotificationDrawerExpanded(!notificationDrawerExpanded)
  }

  const toggleHeaderDropdown = () => {
    setIsOpenMap(new Array(notifications.length).fill(false))
    setIsOpenHeaderDropdown(!isOpenHeaderDropdown)
  }

  const onSelect = (notification_id) => {
    setIsOpenMap(new Array(notifications.length).fill(false))
  }

  const onSelectHeaderDropdown = () => {}

  const onDrawerClose = (_event: React.MouseEvent<Element, MouseEvent> | KeyboardEvent) => {
    toggleNotificationDrawer()
    setIsOpenMap(new Array(notifications.length).fill(false))
  }

  const onNotificationSelect = (notification) => {
    location.href = notification['url']
  }

  const clearNotification = (notification_id) => {
    let response_status
    let response_data

    let url = Constants.API_BASE_URL + '/user/notifications'
    let data = { 'user-id': auth.userId, token: auth.token }

    if (notification_id != null) {
      data['id'] = notification_id
    }

    fetch(url, {
      method: 'DELETE',
      headers: {
        Accept: 'application/json',
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(data)
    })
      .then((response) => {
        response_status = response.status
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

  const getNotifications = () => {
    if (notifications == null || notifications == undefined) {
      return ''
    }
    if (notifications?.length == 0) {
      return ''
    } else {
      return notifications.map((notification, notificationIndex) => (
        <NotificationDrawerListItem
          onClick={(ev: any) => ev.preventDefault()}
          key={'notification-drawer-list-item-' + notification['id']}
          variant={notification['category']}
        >
          <NotificationDrawerListItemHeader variant={notification['category']} title={notification['title']} srTitle='Info notification:'>
            <Dropdown
              onSelect={() => onSelect(notification['id'])}
              isOpen={isOpenMap[notificationIndex]}
              onOpenChange={() => onToggle(notificationIndex)}
              popperProps={{ position: 'right' }}
              toggle={(toggleRef: React.Ref<MenuToggleElement>) => (
                <MenuToggle
                  ref={toggleRef}
                  isExpanded={isOpenMap[notificationIndex]}
                  onClick={onToggle(notificationIndex)}
                  variant='plain'
                  aria-label={`Basic example notification 1 kebab toggle`}
                >
                  <EllipsisVIcon aria-hidden='true' />
                </MenuToggle>
              )}
            >
              <DropdownList>
                <DropdownItem
                  to='#default-link2'
                  // Prevent the default onClick functionality for example purposes
                  onClick={() => clearNotification(notification['id'])}
                >
                  Mark as read
                </DropdownItem>
                {notification['url'] != '' ? (
                  <DropdownItem
                    to='#default-link2'
                    // Prevent the default onClick functionality for example purposes
                    onClick={() => onNotificationSelect(notification)}
                  >
                    Open url
                  </DropdownItem>
                ) : (
                  ''
                )}
              </DropdownList>
            </Dropdown>
          </NotificationDrawerListItemHeader>
          <NotificationDrawerListItemBody timestamp={notification.created_at}>{notification.description}</NotificationDrawerListItemBody>
        </NotificationDrawerListItem>
      ))
    }
  }

  return (
    <NotificationDrawer>
      <NotificationDrawerHeader count={notifications?.length | 0} onClose={onDrawerClose}>
        {notifications?.length > 0 ? (
          <Dropdown
            onSelect={onSelectHeaderDropdown}
            isOpen={isOpenHeaderDropdown}
            onOpenChange={() => setIsOpenHeaderDropdown(false)}
            popperProps={{ position: 'right' }}
            toggle={(toggleRef: React.Ref<MenuToggleElement>) => (
              <MenuToggle
                ref={toggleRef}
                isExpanded={isOpenHeaderDropdown}
                onClick={toggleHeaderDropdown}
                variant='plain'
                aria-label={`Basic example header kebab toggle`}
              >
                <EllipsisVIcon aria-hidden='true' />
              </MenuToggle>
            )}
          >
            <DropdownList>
              <DropdownItem
                to='#default-link2'
                // Prevent the default onClick functionality for example purposes
                onClick={() => clearNotification(null)}
              >
                Mark all as read
              </DropdownItem>
            </DropdownList>
          </Dropdown>
        ) : (
          ''
        )}
      </NotificationDrawerHeader>
      <NotificationDrawerBody>
        <NotificationDrawerList aria-label='Notifications in the basic example'>{getNotifications()}</NotificationDrawerList>
      </NotificationDrawerBody>
    </NotificationDrawer>
  )
}
