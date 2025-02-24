import * as React from 'react'
import * as Constants from '../Constants/constants'
import { Button, Card, CardBody, Flex, FlexItem, PageSection, Title } from '@patternfly/react-core'
import { SSHKeyListingTable } from './SSHKeyListing'
import { SSHKeyModal } from './Modal/SSHKeyModal'
import { useAuth } from '../User/AuthProvider'

const SSHKey: React.FunctionComponent = () => {
  const auth = useAuth()
  const [sshKeys, setSshKeys] = React.useState([])
  const [modalShowState, setModalShowState] = React.useState(false)

  const loadSSHKeys = () => {
    if (!auth.isLogged()) {
      return
    }
    let url
    url = Constants.API_BASE_URL + '/user/ssh-key'
    url += '?user-id=' + auth.userId
    url += '&token=' + auth.token
    fetch(url, {
      method: 'GET',
      headers: Constants.JSON_HEADER
    })
      .then((res) => res.json())
      .then((data) => {
        setSshKeys(data)
      })
      .catch((err) => {
        console.log(err.message)
      })
  }

  React.useEffect(() => {
    loadSSHKeys()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  return (
    <PageSection isFilled>
      <Card>
        <CardBody>
          <Flex>
            <Flex>
              <FlexItem>
                <Title headingLevel='h1'>SSH Keys</Title>
              </FlexItem>
            </Flex>
            <Flex align={{ default: 'alignRight' }}>
              <FlexItem>
                {!auth.isGuest() ? (
                  <Button id='btn-add-ssh-key' variant='primary' onClick={() => setModalShowState(true)}>
                    Add SSH Key
                  </Button>
                ) : (
                  ''
                )}
              </FlexItem>
            </Flex>
          </Flex>
          <SSHKeyListingTable sshKeys={sshKeys} />
        </CardBody>
      </Card>
      <SSHKeyModal modalShowState={modalShowState} setModalShowState={setModalShowState} />
    </PageSection>
  )
}

export { SSHKey }
