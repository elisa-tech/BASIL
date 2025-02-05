import * as React from 'react'
import { Route, RouteComponentProps, Switch, useLocation } from 'react-router-dom'
import { Dashboard } from '@app/Dashboard/Dashboard'
import { Admin } from '@app/Admin/Admin'
import { AdminTestRunPluginPresets } from '@app/Admin/AdminTestRunPluginPresets'
import { Login } from '@app/Login/Login'
import { Mapping } from '@app/Mapping/Mapping'
import { NotFound } from '@app/NotFound/NotFound'
import { Signin } from '@app/Signin/Signin'
import { SSHKey } from '@app/SSHKey/SSHKey'
import { UserFiles } from './UserFiles/UserFiles'
import { useDocumentTitle } from '@app/utils/useDocumentTitle'

let routeFocusTimer: number
export interface IAppRoute {
  label?: string // Excluding the label will exclude the route from the nav sidebar in AppLayout
  /* eslint-disable @typescript-eslint/no-explicit-any */
  component: React.ComponentType<RouteComponentProps<any>> | React.ComponentType<any>
  /* eslint-enable @typescript-eslint/no-explicit-any */
  exact?: boolean
  path: string
  title: string
  routes?: undefined
}

export interface IAppRouteGroup {
  label: string
  routes: IAppRoute[]
}

export type AppRouteConfig = IAppRoute | IAppRouteGroup
const routes: AppRouteConfig[] = [
  {
    component: Dashboard,
    exact: true,
    label: 'SW Components',
    path: '/',
    title: 'BASIL | The Fusa Spice | Software Components'
  },
  {
    component: Login,
    exact: true,
    label: 'Login',
    path: '/login',
    title: 'BASIL | The Fusa Spice | Login'
  },
  {
    component: Mapping,
    exact: true,
    label: 'SW Specification Mapping',
    path: '/mapping/:api_id',
    title: 'BASIL | The Fusa Spice | Software Component Specification Mapping'
  },
  {
    component: Signin,
    exact: true,
    label: 'Sign In',
    path: '/signin',
    title: 'BASIL | The Fusa Spice | Sign In'
  },
  {
    component: Admin,
    exact: true,
    label: 'User Management',
    path: '/admin',
    title: 'BASIL | The Fusa Spice | Admin | User Management'
  },
  {
    component: AdminTestRunPluginPresets,
    exact: true,
    label: 'Test Run Plugins Presets',
    path: '/plugins-presets',
    title: 'BASIL | The Fusa Spice | Admin | Test Run Plugins Presets'
  },
  {
    component: SSHKey,
    exact: true,
    label: 'SSH Keys',
    path: '/ssh-keys',
    title: 'BASIL | The Fusa Spice | User | SSH Keys'
  },
  {
    component: UserFiles,
    exact: true,
    label: 'User Files',
    path: '/user-files',
    title: 'BASIL | The Fusa Spice | User | Files'
  }
]

// a custom hook for sending focus to the primary content container
// after a view has loaded so that subsequent press of tab key
// sends focus directly to relevant content
// may not be necessary if https://github.com/ReactTraining/react-router/issues/5210 is resolved
const useA11yRouteChange = () => {
  const { pathname } = useLocation()
  React.useEffect(() => {
    routeFocusTimer = window.setTimeout(() => {
      const mainContainer = document.getElementById('primary-app-container')
      if (mainContainer) {
        mainContainer.focus()
      }
    }, 50)
    return () => {
      window.clearTimeout(routeFocusTimer)
    }
  }, [pathname])
}

const RouteWithTitleUpdates = ({ component: Component, title, ...rest }: IAppRoute) => {
  useA11yRouteChange()
  useDocumentTitle(title)

  function routeWithTitle(routeProps: RouteComponentProps) {
    return <Component {...rest} {...routeProps} />
  }

  return <Route render={routeWithTitle} {...rest} />
}

const PageNotFound = ({ title }: { title: string }) => {
  useDocumentTitle(title)
  return <Route component={NotFound} />
}

const flattenedRoutes: IAppRoute[] = routes.reduce(
  (flattened, route) => [...flattened, ...(route.routes ? route.routes : [route])],
  [] as IAppRoute[]
)

const AppRoutes = (): React.ReactElement => (
  <Switch>
    {flattenedRoutes.map(({ path, exact, component, title }, idx) => (
      <RouteWithTitleUpdates path={path} exact={exact} component={component} key={idx} title={title} />
    ))}
    <PageNotFound title='404 Page Not Found' />
  </Switch>
)

export { AppRoutes, routes }
