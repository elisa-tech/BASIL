import * as React from 'react'
import * as Constants from '../Constants/constants'
import { Button, Card, CardBody, Flex, FlexItem, PageSection, Title } from '@patternfly/react-core'
import { UserFilesListingTable } from './UserFilesListing'
import { UserFilesModal } from './Modal/UserFilesModal'
import { useAuth } from '../User/AuthProvider'

const UserFiles: React.FunctionComponent = () => {
  const auth = useAuth()

  const modal_action = React.useRef('add')
  const modal_filename = React.useRef('') // to be used for edit form

  const [userFiles, setUserFiles] = React.useState([])
  const [modalShowState, setModalShowState] = React.useState(false)

  React.useEffect(() => {
    Constants.loadUserFiles(auth, setUserFiles)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const addFile = () => {
    modal_action.current = 'add'
    modal_filename.current = ''
    setModalShowState(true)
  }

  return (
    <PageSection isFilled>
      <Card>
        <CardBody>
          <Flex>
            <Flex>
              <FlexItem>
                <Title headingLevel='h1'>User Files</Title>
              </FlexItem>
            </Flex>
            <Flex align={{ default: 'alignRight' }}>
              <FlexItem>
                {!auth.isGuest() ? (
                  <Button id='btn-add-user-file' variant='primary' onClick={() => addFile()}>
                    Add File
                  </Button>
                ) : (
                  ''
                )}
              </FlexItem>
            </Flex>
          </Flex>
          <UserFilesListingTable
            modalAction={modal_action}
            modalFileName={modal_filename}
            setModalShowState={setModalShowState}
            userFiles={userFiles}
          />
        </CardBody>
      </Card>
      <UserFilesModal
        modalAction={modal_action}
        modalFileName={modal_filename}
        modalShowState={modalShowState}
        setModalShowState={setModalShowState}
      />
    </PageSection>
  )
}

export { UserFiles }
