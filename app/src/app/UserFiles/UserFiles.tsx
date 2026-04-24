import * as React from 'react'
import * as Constants from '../Constants/constants'
import { Breadcrumb, BreadcrumbItem, Button, Card, CardBody, Flex, FlexItem, PageSection, Title } from '@patternfly/react-core'
import { UserFilesListingTable } from './UserFilesListing'
import { UserFilesModal } from './Modal/UserFilesModal'
import { useAuth } from '../User/AuthProvider'
import FolderIcon from '@patternfly/react-icons/dist/esm/icons/folder-open-icon'

const UserFiles: React.FunctionComponent = () => {
  const auth = useAuth()

  const modal_action = React.useRef('add')
  const modal_filename = React.useRef('')
  const modal_relative_path = React.useRef('')

  const [currentPath, setCurrentPath] = React.useState('')
  const [userFiles, setUserFiles] = React.useState([])
  const [modalShowState, setModalShowState] = React.useState(false)

  const loadFiles = React.useCallback(() => {
    Constants.loadUserFiles(auth, setUserFiles, '', currentPath)
  }, [auth, currentPath])

  React.useEffect(() => {
    loadFiles()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentPath])

  const addFile = () => {
    modal_action.current = 'add'
    modal_filename.current = ''
    modal_relative_path.current = ''
    setModalShowState(true)
  }

  const createFolder = () => {
    modal_action.current = 'create-folder'
    modal_filename.current = ''
    modal_relative_path.current = ''
    setModalShowState(true)
  }

  const navigateTo = (path: string) => {
    setCurrentPath(path)
  }

  const breadcrumbSegments = currentPath ? currentPath.split('/').filter(Boolean) : []

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
                  <>
                    <Button id='btn-create-user-folder' variant='secondary' onClick={createFolder} style={{ marginRight: '8px' }}>
                      <FolderIcon /> New Folder
                    </Button>
                    <Button id='btn-add-user-file' variant='primary' onClick={addFile}>
                      Add File
                    </Button>
                  </>
                ) : (
                  ''
                )}
              </FlexItem>
            </Flex>
          </Flex>

          <Breadcrumb style={{ margin: '12px 0' }}>
            <BreadcrumbItem
              id='breadcrumb-root'
              to='#'
              onClick={(e) => {
                e.preventDefault()
                navigateTo('')
              }}
              isActive={currentPath === ''}
            >
              Home
            </BreadcrumbItem>
            {breadcrumbSegments.map((segment, idx) => {
              const partialPath = breadcrumbSegments.slice(0, idx + 1).join('/')
              const isLast = idx === breadcrumbSegments.length - 1
              return (
                <BreadcrumbItem
                  key={partialPath}
                  id={`breadcrumb-${idx}`}
                  to='#'
                  onClick={(e) => {
                    e.preventDefault()
                    if (!isLast) navigateTo(partialPath)
                  }}
                  isActive={isLast}
                >
                  {segment}
                </BreadcrumbItem>
              )
            })}
          </Breadcrumb>

          <UserFilesListingTable
            modalAction={modal_action}
            modalFileName={modal_filename}
            modalRelativePath={modal_relative_path}
            setModalShowState={setModalShowState}
            userFiles={userFiles}
            currentPath={currentPath}
            navigateTo={navigateTo}
          />
        </CardBody>
      </Card>
      <UserFilesModal
        modalAction={modal_action}
        modalFileName={modal_filename}
        modalRelativePath={modal_relative_path}
        modalShowState={modalShowState}
        setModalShowState={setModalShowState}
        currentPath={currentPath}
        loadFiles={loadFiles}
      />
    </PageSection>
  )
}

export { UserFiles }
