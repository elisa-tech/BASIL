import * as React from 'react'
import { NavLink, useLocation } from 'react-router-dom'
import {
  Brand,
  Button,
  Masthead,
  MastheadBrand,
  MastheadContent,
  MastheadMain,
  MastheadToggle,
  Nav,
  NavExpandable,
  NavItem,
  NavList,
  Page,
  PageSidebar,
  PageSidebarBody,
  SkipToContent
} from '@patternfly/react-core'
import { IAppRoute, IAppRouteGroup, routes } from '@app/routes'
import BarsIcon from '@patternfly/react-icons/dist/esm/icons/bars-icon'
import { HeaderToolbar } from './HeaderToolbar'
import { NotificationDrawerBasic } from '../Notification/Notification'
import logo from '@app/bgimages/basil.svg'
import * as Constants from '../Constants/constants'
import { useAuth } from '@app/User/AuthProvider'

interface IAppLayout {
  children: React.ReactNode
  notificationCount: number
}

const AppLayout: React.FunctionComponent<IAppLayout> = ({ children, notificationCount }) => {
  let auth = useAuth();
  const [sidebarOpen, setSidebarOpen] = React.useState(true)
  const [notificationDrawerExpanded, setNotificationDrawerExpanded] = React.useState(false)
  const [notifications, setNotifications] = React.useState<Notification>([]);
  React.useEffect(() => {
    loadNotifications()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  React.useEffect(() => {
    console.log("notifications: " + notifications.length)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [notifications])

  const loadNotifications = () => {

    if (!auth.isLogged()){
      return;
    }

    let url = Constants.API_BASE_URL + '/user/notifications?'
    url += '&user-id=' + auth.userId + '&token=' + auth.token

    fetch(url)
      .then((res) => res.json())
      .then((data) => {
        setNotifications(data)
      })
      .catch((err) => {
        console.log(err.message)
      })
  }

  const Header = (
    <Masthead>
      <MastheadToggle>
        <Button variant='plain' onClick={() => setSidebarOpen(!sidebarOpen)} aria-label='Global navigation'>
          <BarsIcon />
        </Button>
      </MastheadToggle>
      <MastheadMain>
        <MastheadBrand>
          <Brand src={logo} alt='BASIL - The FuSa Spice' widths={{ default: '40px', sm: '60px', md: '220px' }}></Brand>
        </MastheadBrand>
      </MastheadMain>
      <MastheadContent>
        <HeaderToolbar
          notificationCount={notifications.length}
          notificationDrawerExpanded={notificationDrawerExpanded}
          setNotificationDrawerExpanded={setNotificationDrawerExpanded} />
      </MastheadContent>
    </Masthead>
  )

  const location = useLocation()

  const renderNavItem = (route: IAppRoute, index: number) => (
    <NavItem key={`${route.label}-${index}`} id={`${route.label}-${index}`} isActive={route.path === location.pathname}>
      <NavLink exact={route.exact} to={route.path}>
        {route.label}
      </NavLink>
    </NavItem>
  )

  const renderNavGroup = (group: IAppRouteGroup, groupIndex: number) => (
    <NavExpandable
      key={`${group.label}-${groupIndex}`}
      id={`${group.label}-${groupIndex}`}
      title={group.label}
      isActive={group.routes.some((route) => route.path === location.pathname)}
    >
      {group.routes.map((route, idx) => route.label && renderNavItem(route, idx))}
    </NavExpandable>
  )

  const Navigation = (
    <Nav id='nav-primary-simple' theme='dark'>
      <NavList id='nav-list-simple'>
        {routes.map((route, idx) => route.label && (!route.routes ? renderNavItem(route, idx) : renderNavGroup(route, idx)))}
      </NavList>
    </Nav>
  )

  const Sidebar = (
    <PageSidebar theme='dark'>
      <PageSidebarBody>{Navigation}</PageSidebarBody>
    </PageSidebar>
  )


  const pageId = 'primary-app-container'

  const PageSkipToContent = (
    <SkipToContent
      onClick={(event) => {
        event.preventDefault()
        const primaryContentContainer = document.getElementById(pageId)
        primaryContentContainer && primaryContentContainer.focus()
      }}
      href={`#${pageId}`}
    >
      Skip to Content
    </SkipToContent>
  )
  return (
    <Page mainContainerId={pageId}
          header={Header}
          notificationDrawer={<NotificationDrawerBasic
                                notifications={notifications}
                                notificationDrawerExpanded={notificationDrawerExpanded}
                                setNotificationDrawerExpanded={setNotificationDrawerExpanded} />}
          sidebar={sidebarOpen && Sidebar}
          isNotificationDrawerExpanded={notificationDrawerExpanded}
          skipToContent={PageSkipToContent}>
      {children}
    </Page>
  )
}

export { AppLayout }
