import * as React from 'react'
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
import BarsIcon from '@patternfly/react-icons/dist/esm/icons/bars-icon'
import { HeaderToolbar } from './HeaderToolbar'
import { NotificationDrawerBasic } from '../Notification/Notification'
import logo from '@app/bgimages/basil.svg'
import * as Constants from '../Constants/constants'
import { useAuth } from '../User/AuthProvider'

interface IAppLayout {
  children: React.ReactNode
}

const AppLayout: React.FunctionComponent<IAppLayout> = ({ children }) => {
  const auth = useAuth()
  const [sidebarOpen, setSidebarOpen] = React.useState(true)
  const [notificationDrawerExpanded, setNotificationDrawerExpanded] = React.useState(false)
  const [notifications, setNotifications] = React.useState<Notification[]>([])
  //const [activeGroup, setActiveGroup] = React.useState('')
  //const [activeItem, setActiveItem] = React.useState('ungrouped_item-1')
  const [libraries, setLibraries] = React.useState([])
  const [fetchNotificationCount, setFetchNotificationCount] = React.useState(0)
  const [fetchLibrariesCount, setFetchLibrariesCount] = React.useState(0)

  /*
  const onNavigationSelect = (
    _event: React.FormEvent<HTMLInputElement>,
    result: { itemId: number | string; groupId: number | string | null }
  ) => {
    setActiveGroup(result.groupId as string)
    setActiveItem(result.itemId as string)
  }
  */

  React.useEffect(() => {
    loadNotifications()
    if (libraries.length == 0) {
      loadLibraries()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const loadLibraries = () => {
    if (fetchLibrariesCount > 1) {
      return
    }
    setFetchLibrariesCount(fetchLibrariesCount + 1)
    fetch(Constants.API_BASE_URL + '/libraries')
      .then((res) => res.json())
      .then((data) => {
        setLibraries(data)
      })
      .catch((err) => {
        console.log(err.message)
      })
  }

  const loadNotifications = () => {
    if (fetchNotificationCount > 1) {
      return
    }
    setFetchNotificationCount(fetchNotificationCount + 1)

    if (!auth.isLogged()) {
      return
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
          setNotificationDrawerExpanded={setNotificationDrawerExpanded}
        />
      </MastheadContent>
    </Masthead>
  )

  const navigate = (url) => {
    window.open(url, '_blank', 'noreferrer')
  }

  const redirect = (url) => {
    window.location.href = url
  }

  const getLibrariesNavItems = () => {
    return libraries.map((library, index) => (
      <NavItem
        key={'nav-group-libraries-item-1' + index}
        preventDefault
        id='mixed-1'
        to='#mixed-1'
        onClick={() => redirect('/?currentLibrary=' + library)}
        itemId={'nav-group-libraries-item-1' + index}
        isActive={false}
      >
        {library}
      </NavItem>
    ))
  }

  const Navigation = (
    <Nav aria-label='Mixed global'>
      <NavList>
        <NavItem
          preventDefault
          id='nav-item-home'
          to='#nav-item-home'
          onClick={() => redirect('/')}
          itemId='ungrouped-item-1'
          isActive={false}
        >
          Home
        </NavItem>

        {!auth.isLogged() ? (
          <NavItem
            preventDefault
            id='nav-item-login'
            to='#nav-item-login'
            onClick={() => redirect('/login')}
            itemId='ungrouped-item-2'
            isActive={false}
          >
            Login
          </NavItem>
        ) : (
          ''
        )}

        {!auth.isLogged() ? (
          <NavItem
            preventDefault
            id='nav-item-signin'
            to='#nav-item-signin'
            onClick={() => redirect('/signin')}
            itemId='ungrouped-item-3'
            isActive={false}
          >
            Sign In
          </NavItem>
        ) : (
          ''
        )}

        {auth.isLogged() && auth.isAdmin() ? (
          <NavItem
            preventDefault
            id='nav-item-user-management'
            to='#nav-item-user-management'
            onClick={() => redirect('/admin')}
            itemId='ungrouped-item-4'
            isActive={false}
          >
            User Management
          </NavItem>
        ) : (
          ''
        )}

        {auth.isLogged() && !auth.isGuest() ? (
          <NavItem
            preventDefault
            id='nav-item-user-ssh-keys'
            to='#nav-item-user-ssh-keys'
            onClick={() => redirect('/ssh-keys')}
            itemId='ungrouped-item-5'
            isActive={false}
          >
            SSH Keys
          </NavItem>
        ) : (
          ''
        )}

        <NavExpandable title='Libraries' groupId='nav-group-libraries' isActive={false}>
          {getLibrariesNavItems()}
        </NavExpandable>
        <NavExpandable title='Useful Links' groupId='nav-useful-links' isActive={false}>
          <NavItem
            preventDefault
            id='nav-useful-links-elisa'
            to='#nav-useful-links-elisa'
            onClick={() => navigate('https://elisa.tech/')}
            groupId='nav-useful-links'
            itemId='nav-useful-links-item-1'
            isActive={false}
          >
            ELISA
          </NavItem>
          <NavItem
            preventDefault
            id='nav-useful-links-documentation'
            to='#nav-useful-links-documentation'
            onClick={() => navigate('https://basil-the-fusa-spice.readthedocs.io/')}
            groupId='nav-useful-links'
            itemId='nav-useful-links-item-2'
            isActive={false}
          >
            Documentation
          </NavItem>
          <NavItem
            preventDefault
            id='nav-useful-links-basil-github'
            to='#nav-useful-links-basil-github'
            onClick={() => navigate('https://github.com/elisa-tech/BASIL')}
            groupId='nav-useful-links'
            itemId='nav-useful-links-item-3'
            isActive={false}
          >
            BASIL github
          </NavItem>
          <NavItem
            preventDefault
            id='nav-useful-links-contribute'
            to='#nav-useful-links-contribute'
            onClick={() => navigate('https://github.com/elisa-tech/BASIL/issues')}
            groupId='nav-useful-links'
            itemId='nav-useful-links-item-4'
            isActive={false}
          >
            Contribute
          </NavItem>
          <NavItem
            preventDefault
            id='nav-useful-links-report-a-bug'
            to='#nav-useful-links-report-a-bug'
            onClick={() => navigate('https://github.com/elisa-tech/BASIL/issues/new')}
            groupId='nav-useful-links'
            itemId='nav-useful-links-item-5'
            isActive={false}
          >
            Report a bug
          </NavItem>
        </NavExpandable>
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
    <Page
      mainContainerId={pageId}
      header={Header}
      notificationDrawer={
        <NotificationDrawerBasic
          notifications={notifications}
          notificationDrawerExpanded={notificationDrawerExpanded}
          setNotificationDrawerExpanded={setNotificationDrawerExpanded}
        />
      }
      sidebar={sidebarOpen && Sidebar}
      isNotificationDrawerExpanded={notificationDrawerExpanded}
      skipToContent={PageSkipToContent}
    >
      {children}
    </Page>
  )
}

export { AppLayout }
