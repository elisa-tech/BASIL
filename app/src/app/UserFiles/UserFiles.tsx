import * as React from 'react'
import * as Constants from '../Constants/constants'
import { Breadcrumb, BreadcrumbItem, Button, Card, CardBody, Flex, FlexItem, PageSection, SearchInput, Title } from '@patternfly/react-core'
import { UserFilesListingTable } from './UserFilesListing'
import { UserFilesSearchResultsTable } from './UserFilesSearchResults'
import { UserFilesModal } from './Modal/UserFilesModal'
import { useAuth } from '../User/AuthProvider'
import FolderIcon from '@patternfly/react-icons/dist/esm/icons/folder-open-icon'

const SEARCH_DEBOUNCE_MS = 400

const UserFiles: React.FunctionComponent = () => {
  const auth = useAuth()

  const modal_action = React.useRef('add')
  const modal_filename = React.useRef('')
  const modal_relative_path = React.useRef('')

  const [currentPath, setCurrentPath] = React.useState('')
  const [userFiles, setUserFiles] = React.useState([])
  const [modalShowState, setModalShowState] = React.useState(false)
  const [searchValue, setSearchValue] = React.useState('')
  const [searchResults, setSearchResults] = React.useState([])
  const [isSearching, setIsSearching] = React.useState(false)
  const [refreshCounter, setRefreshCounter] = React.useState(0)

  const searchTerm = searchValue.trim()
  const isSearchActive = searchTerm !== ''

  const loadFiles = React.useCallback(() => {
    Constants.loadUserFiles(auth, setUserFiles, '', currentPath)
    setRefreshCounter((counter) => counter + 1)
  }, [auth, currentPath])

  React.useEffect(() => {
    loadFiles()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentPath])

  // Searching is done by the backend, from the user root: it walks every
  // folder, matches the query against the whole relative path of each file and
  // folder, and ranks what it finds. So it is not limited to the folder
  // currently browsed, nor to entry names.
  React.useEffect(() => {
    if (!isSearchActive) {
      setSearchResults([])
      setIsSearching(false)
      return
    }

    let cancelled = false
    setIsSearching(true)
    const timeout = setTimeout(() => {
      Constants.searchUserFiles(
        auth,
        (files) => {
          if (cancelled) {
            return
          }
          setSearchResults(files)
          setIsSearching(false)
        },
        searchTerm
      )
    }, SEARCH_DEBOUNCE_MS)

    return () => {
      cancelled = true
      clearTimeout(timeout)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchTerm, refreshCounter])

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
    setSearchValue('')
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

          <SearchInput
            id='input-user-files-search'
            placeholder='Search files and folders'
            value={searchValue}
            onChange={(_event, value) => setSearchValue(value)}
            onClear={() => setSearchValue('')}
            style={{ width: '400px', marginBottom: '12px' }}
          />

          {isSearchActive ? (
            <>
              <div id='user-files-search-summary' style={{ color: '#6a6e73', marginBottom: '12px' }}>
                {isSearching
                  ? `Searching for "${searchTerm}" in all folders...`
                  : `${searchResults.length} result${searchResults.length === 1 ? '' : 's'} matching "${searchTerm}" in all folders`}
              </div>
              <UserFilesSearchResultsTable
                modalAction={modal_action}
                modalFileName={modal_filename}
                modalRelativePath={modal_relative_path}
                setModalShowState={setModalShowState}
                userFiles={searchResults}
                searchValue={searchTerm}
                isSearching={isSearching}
                navigateTo={navigateTo}
              />
            </>
          ) : (
            <UserFilesListingTable
              modalAction={modal_action}
              modalFileName={modal_filename}
              modalRelativePath={modal_relative_path}
              setModalShowState={setModalShowState}
              userFiles={userFiles}
              currentPath={currentPath}
              navigateTo={navigateTo}
            />
          )}
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
