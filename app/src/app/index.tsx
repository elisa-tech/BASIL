import * as React from 'react';
import '@patternfly/react-core/dist/styles/base.css';
import { BrowserRouter as Router } from 'react-router-dom';
import { AppLayout } from '@app/AppLayout/AppLayout';
import { AppRoutes } from '@app/routes';
import '@app/app.css';

const App: React.FunctionComponent = () => {

  const [notificationCount, setNotificationCount] = React.useState(0);

  return(
  <Router>
    <AppLayout notificationCount={notificationCount}>
      <AppRoutes notificationCount={notificationCount} setNotificationCount={setNotificationCount} />
    </AppLayout>
  </Router>
  )
}
export default App;
