import React from 'react';
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
} from '@patternfly/react-core';
import * as Constants from '../Constants/constants'
import EllipsisVIcon from '@patternfly/react-icons/dist/esm/icons/ellipsis-v-icon';
import { useAuth } from '@app/User/AuthProvider'

interface Notification {
  api: string;
  notification: string;
  read_by?: string;
  url: string;
}

export interface NotificationDrawerBasicProps {
  notifications
  notificationDrawerExpanded
  setNotificationDrawerExpanded
}
export const NotificationDrawerBasic: React.FunctionComponent<NotificationDrawerBasicProps> = ({
  notifications,
  notificationDrawerExpanded,
  setNotificationDrawerExpanded,
}:NotificationDrawerBasicProps) => {
  let auth = useAuth();
  const [isOpenMap, setIsOpenMap] = React.useState(new Array(7).fill(false));
  const onToggle = (index: number) => () => {
    const newState = [...isOpenMap.slice(0, index), !isOpenMap[index], ...isOpenMap.slice(index + 1)];
    setIsOpenMap(newState);
  };

  const toggleNotificationDrawer = () => {
    setNotificationDrawerExpanded(!notificationDrawerExpanded)
  }

  const onSelect = () => {
    setIsOpenMap(new Array(7).fill(false));
  };

  const onDrawerClose = (_event: React.MouseEvent<Element, MouseEvent> | KeyboardEvent) => {
    console.log("close drawer")
    toggleNotificationDrawer()
    setIsOpenMap(new Array(7).fill(false));
  };

  const [isOpen0, isOpen1, isOpen2, isOpen3, isOpen4, isOpen5, isOpen6] = isOpenMap;

  const dropdownItems = (
    <>
      <DropdownItem>Action</DropdownItem>
      <DropdownItem
        to="#default-link2"
        // Prevent the default onClick functionality for example purposes
        onClick={(ev: any) => ev.preventDefault()}
      >
        Link
      </DropdownItem>
      <DropdownItem isDisabled>Disabled Action</DropdownItem>
      <DropdownItem isDisabled to="#default-link4">
        Disabled Link
      </DropdownItem>
    </>
  );

  const getNotifications = () => {
    if (notifications == null){
      return ''
    }
    if (notifications?.length == 0) {
      return ''
    } else {
      return notifications.map((notification, notificationIndex) => (
        <NotificationDrawerListItem variant={notification['category']}>
          <NotificationDrawerListItemHeader
            variant={notification['category']}
            title={notification['title']}
            srTitle="Info notification:"
          >
            <Dropdown
              onSelect={onSelect}
              isOpen={isOpen1}
              onOpenChange={() => setIsOpenMap(new Array(7).fill(false))}
              popperProps={{ position: 'right' }}
              toggle={(toggleRef: React.Ref<MenuToggleElement>) => (
                <MenuToggle
                  ref={toggleRef}
                  isExpanded={isOpen0}
                  onClick={onToggle(1)}
                  variant="plain"
                  aria-label={`Basic example notification 1 kebab toggle`}
                >
                  <EllipsisVIcon aria-hidden="true" />
                </MenuToggle>
              )}
            >
              <DropdownList>{dropdownItems}</DropdownList>
            </Dropdown>
          </NotificationDrawerListItemHeader>
          <NotificationDrawerListItemBody timestamp={notification.created_at}>
            {notification.description}
          </NotificationDrawerListItemBody>
        </NotificationDrawerListItem>
      )
    )}
  }

  return (
    <NotificationDrawer>
      <NotificationDrawerHeader count={notifications?.length | 0} onClose={onDrawerClose}>
        <Dropdown
          onSelect={onSelect}
          isOpen={isOpen0}
          onOpenChange={() => setIsOpenMap(new Array(7).fill(false))}
          popperProps={{ position: 'right' }}
          toggle={(toggleRef: React.Ref<MenuToggleElement>) => (
            <MenuToggle
              ref={toggleRef}
              isExpanded={isOpen0}
              onClick={onToggle(0)}
              variant="plain"
              aria-label={`Basic example header kebab toggle`}
            >
              <EllipsisVIcon aria-hidden="true" />
            </MenuToggle>
          )}
        >
          <DropdownList>{dropdownItems}</DropdownList>
        </Dropdown>
      </NotificationDrawerHeader>
      <NotificationDrawerBody>
        <NotificationDrawerList aria-label="Notifications in the basic example">
          {getNotifications()}
        </NotificationDrawerList>
      </NotificationDrawerBody>
    </NotificationDrawer>
  );
};
