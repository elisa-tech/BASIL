import * as React from 'react'
import * as Constants from '../Constants/constants'
import { Card, CardBody, Flex, FlexItem, PageSection, Title } from '@patternfly/react-core'
import { AdminListingTable } from './AdminListingTable'
import { useAuth } from '../User/AuthProvider'

const Admin: React.FunctionComponent = () => {
  const auth = useAuth()
  const [users, setUsers] = React.useState([])

  const loadUsers = () => {
    if (!auth.isLogged() || !auth.isAdmin()) {
      return
    }
    let url
    url = Constants.API_BASE_URL + '/user'
    url += '?user-id=' + auth.userId
    url += '&token=' + auth.token
    fetch(url, {
      method: 'GET',
      headers: {
        Accept: 'application/json',
        'Content-Type': 'application/json'
      }
    })
      .then((res) => res.json())
      .then((data) => {
        setUsers(data)
      })
      .catch((err) => {
        console.log(err.message)
      })
  }

  React.useEffect(() => {
    loadUsers()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  return (
    <PageSection isFilled>
      <Card>
        <CardBody>
          <Flex>
            <Flex>
              <FlexItem>
                <Title headingLevel='h1'>Admin Panel - Users</Title>
              </FlexItem>
            </Flex>
          </Flex>
          <AdminListingTable users={users} />
        </CardBody>
      </Card>
    </PageSection>
  )
}

export { Admin }
