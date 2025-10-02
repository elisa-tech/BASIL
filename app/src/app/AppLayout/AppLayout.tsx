import * as React from 'react'
import { useLocation } from 'react-router-dom'
import {
  Brand,
  Button,
  Label,
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
  SkipToContent,
  Text
} from '@patternfly/react-core'
import BarsIcon from '@patternfly/react-icons/dist/esm/icons/bars-icon'
import { HeaderToolbar } from './HeaderToolbar'
import { NotificationDrawerBasic } from '../Notification/Notification'
import logo from '@app/bgimages/basil.svg'
import * as Constants from '../Constants/constants'
import { useAuth } from '../User/AuthProvider'
import { AutoRefresh } from '@app/Common/AutoRefresh/AutoRefresh'
import { InfoCircleIcon } from '@patternfly/react-icons'

interface IAppLayout {
  children: React.ReactNode
}

const AppLayout: React.FunctionComponent<IAppLayout> = ({ children }) => {
  const auth = useAuth()
  const location = useLocation()
  const [sidebarOpen, setSidebarOpen] = React.useState(true)
  const [notificationDrawerExpanded, setNotificationDrawerExpanded] = React.useState(false)
  const [notifications, setNotifications] = React.useState<Notification[]>([])
  //const [activeGroup, setActiveGroup] = React.useState('')
  //const [activeItem, setActiveItem] = React.useState('ungrouped_item-1')
  const [libraries, setLibraries] = React.useState([])
  const [fetchNotificationCount, setFetchNotificationCount] = React.useState(0)
  const [fetchLibrariesCount, setFetchLibrariesCount] = React.useState(0)
  const [newVersionAvailabe, setNewVersionAvailable] = React.useState(false)

  const search = window.location.search
  const params = new URLSearchParams(search)
  const queryCurrentLibrary = params.get('currentLibrary')

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
    Constants.checkNewVersionAvailable(setNewVersionAvailable)
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

  const loadNotifications = (force: boolean = false) => {
    if (force == false && fetchNotificationCount > 1) {
      return
    }
    setFetchNotificationCount(fetchNotificationCount + 1)

    if (!auth.isLogged()) {
      return
    }

    let url = Constants.API_BASE_URL + '/user/notifications?'
    url += '&user-id=' + auth.userId + '&token=' + auth.token

    fetch(url)
      .then((response) => {
        if (!response.ok) {
          auth.logOut()
          throw new Error(`HTTP error! Status: ${response.status}`)
        }
        return response.json()
      })
      .then((data) => {
        setNotifications(data)
      })
      .catch((err) => {
        console.error('Fetch error:', err)
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
        <AutoRefresh loadRows={loadNotifications} showCountdown={false} />
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
        key={'nav-group-libraries-item-' + index}
        preventDefault
        id='mixed-1'
        to='#mixed-1'
        onClick={() => redirect('/?currentLibrary=' + library)}
        itemId={'nav-group-libraries-item-' + index}
        isActive={location.pathname == '/' && queryCurrentLibrary == library}
      >
        {library}
      </NavItem>
    ))
  }

  const Navigation = (
    <>
      <Nav aria-label='Mixed global'>
        <NavList>
          <NavItem
            preventDefault
            id='nav-item-home'
            to='#nav-item-home'
            onClick={() => redirect('/')}
            itemId='ungrouped-item-1'
            isActive={location.pathname == '/' && queryCurrentLibrary == null}
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
              isActive={location.pathname == '/login'}
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
              isActive={location.pathname == '/signin'}
            >
              Sign In
            </NavItem>
          ) : (
            ''
          )}

          {auth.isLogged() && auth.isAdmin() ? (
            <>
              <NavItem
                preventDefault
                id='nav-item-user-management'
                to='#nav-item-user-management'
                onClick={() => redirect('/admin')}
                itemId='ungrouped-item-4'
                isActive={location.pathname == '/admin'}
              >
                User Management
              </NavItem>
              <NavItem
                preventDefault
                id='nav-item-test-run-plugins-presets'
                to='#nav-item-test-run-plugins-presets'
                onClick={() => redirect('/plugins-presets')}
                itemId='ungrouped-item-5'
                isActive={location.pathname == '/plugins-presets'}
              >
                Test Run Plugin Presets
              </NavItem>
              <NavItem
                preventDefault
                id='nav-item-settings'
                to='#nav-item-settings'
                onClick={() => redirect('/settings')}
                itemId='ungrouped-item-6'
                isActive={location.pathname == '/settings'}
              >
                Settings
              </NavItem>
            </>
          ) : (
            ''
          )}

          {auth.isLogged() && !auth.isGuest() ? (
            <>
              <NavItem
                preventDefault
                id='nav-item-user-ssh-keys'
                to='#nav-item-user-ssh-keys'
                onClick={() => redirect('/ssh-keys')}
                itemId='ungrouped-item-7'
                isActive={location.pathname == '/ssh-keys'}
              >
                SSH Keys
              </NavItem>
              <NavItem
                preventDefault
                id='nav-item-user-files'
                to='#nav-item-user-files'
                onClick={() => redirect('/user-files')}
                itemId='ungrouped-item-8'
                isActive={location.pathname == '/user-files'}
              >
                User Files
              </NavItem>
            </>
          ) : (
            ''
          )}

          <NavExpandable
            title='Libraries'
            groupId='nav-group-libraries'
            isExpanded={location.pathname == '/' && queryCurrentLibrary != null}
          >
            {getLibrariesNavItems()}
          </NavExpandable>
          <NavExpandable title='Useful Links' groupId='nav-useful-links' isActive={false}>
            <NavItem
              preventDefault
              id='nav-useful-links-contribute'
              to='#nav-useful-links-contribute'
              onClick={() => navigate('https://github.com/elisa-tech/BASIL/issues')}
              groupId='nav-useful-links'
              itemId='nav-useful-links-item-1'
              isActive={false}
            >
              Contribute
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
              id='nav-useful-links-elisa'
              to='#nav-useful-links-elisa'
              onClick={() => navigate('https://elisa.tech/')}
              groupId='nav-useful-links'
              itemId='nav-useful-links-item-3'
              isActive={false}
            >
              ELISA
            </NavItem>
            <NavItem
              preventDefault
              id='nav-useful-links-basil-github'
              to='#nav-useful-links-basil-github'
              onClick={() => navigate('https://github.com/elisa-tech/BASIL')}
              groupId='nav-useful-links'
              itemId='nav-useful-links-item-4'
              isActive={false}
            >
              GitHub
            </NavItem>
            <NavItem
              preventDefault
              id='nav-useful-links-discord'
              to='#nav-useful-links-discord'
              onClick={() => navigate('https://discord.gg/2sCQSTZHTW')}
              groupId='nav-useful-links'
              itemId='nav-useful-links-item-5'
              isActive={false}
            >
              Discord
            </NavItem>
            <NavItem
              preventDefault
              id='nav-useful-links-report-a-bug'
              to='#nav-useful-links-report-a-bug'
              onClick={() => navigate('https://github.com/elisa-tech/BASIL/issues/new')}
              groupId='nav-useful-links'
              itemId='nav-useful-links-item-6'
              isActive={false}
            >
              Report a bug
            </NavItem>
            <NavItem
              preventDefault
              id='nav-useful-links-youtube'
              to='#nav-useful-links-youtube'
              onClick={() => navigate('https://www.youtube.com/@basil-the-fusa-spice')}
              groupId='nav-useful-links'
              itemId='nav-useful-links-item-7'
              isActive={false}
            >
              Youtube
            </NavItem>
          </NavExpandable>
        </NavList>
      </Nav>
      <div style={{ flexGrow: 1 }} />
      <div style={{ padding: '1.5rem', fontSize: '0.8rem', color: '#FFF' }}>
        <Text>Version: {Constants.BASIL_VERSION}</Text>
        {newVersionAvailabe ? (
          <a
            href='https://github.com/elisa-tech/BASIL/releases'
            target='_blank'
            rel='noopener noreferrer'
            style={{ textDecoration: 'none' }}
          >
            <Label isCompact variant='filled' color='green' icon={<InfoCircleIcon />}>
              New version available
            </Label>
          </a>
        ) : (
          ''
        )}
      </div>
    </>
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
