import * as React from 'react'
import { Table, Tbody, Td, Th, Thead, Tr } from '@patternfly/react-table'
import { UserFilesMenuKebab } from './Menu/UserFilesMenuKebab'
import FileIcon from '@patternfly/react-icons/dist/esm/icons/file-icon'
import FolderIcon from '@patternfly/react-icons/dist/esm/icons/folder-icon'
import { Button } from '@patternfly/react-core'
import { UserFilePath } from './UserFilePath'

export interface UserFilesSearchResultsTableProps {
  modalAction
  modalFileName
  modalRelativePath
  userFiles
  setModalShowState
  searchValue: string
  isSearching: boolean
  navigateTo: (path: string) => void
}

const getFolderPath = (relativePath: string) => {
  const separatorIndex = relativePath.lastIndexOf('/')
  return separatorIndex === -1 ? '' : relativePath.substring(0, separatorIndex)
}

const UserFilesSearchResultsTable: React.FunctionComponent<UserFilesSearchResultsTableProps> = ({
  userFiles,
  modalAction,
  modalFileName,
  modalRelativePath,
  setModalShowState,
  searchValue,
  isSearching,
  navigateTo
}: UserFilesSearchResultsTableProps) => {
  const getTable = () => {
    if (isSearching) {
      return (
        <Tbody>
          <Tr>
            <Td colSpan={4} style={{ textAlign: 'center', color: '#6a6e73', padding: '24px' }}>
              Searching...
            </Td>
          </Tr>
        </Tbody>
      )
    }

    if (userFiles.length === 0) {
      return (
        <Tbody>
          <Tr>
            <Td colSpan={4} style={{ textAlign: 'center', color: '#6a6e73', padding: '24px' }}>
              Nothing matches &quot;{searchValue}&quot; in any of your folders
            </Td>
          </Tr>
        </Tbody>
      )
    }

    return userFiles.map((userFile) => {
      const isDirectory = userFile.type === 'directory'
      // Opening a folder result browses it, opening a file result browses the
      // folder holding it, which is the only place its neighbours are visible.
      const destination = isDirectory ? userFile.relative_path : getFolderPath(userFile.relative_path)
      return (
        <Tbody key={userFile.relative_path}>
          <Tr>
            <Td dataLabel='type' style={{ width: '32px' }}>
              {isDirectory ? <FolderIcon style={{ color: '#f0ab00' }} /> : <FileIcon style={{ color: '#6a6e73' }} />}
            </Td>
            <Td dataLabel='filename'>
              <Button
                variant='link'
                isInline
                id={'btn-user-file-search-result-' + userFile.index}
                onClick={() => navigateTo(destination)}
                title={isDirectory ? 'Open this folder' : 'Open the folder of this file'}
              >
                <UserFilePath relativePath={userFile.relative_path} matchIndices={userFile.match_indices} />
              </Button>
            </Td>
            <Td dataLabel='updated_at'>{userFile.updated_at}</Td>
            <Td dataLabel='actions'>
              <UserFilesMenuKebab
                modalAction={modalAction}
                modalFileName={modalFileName}
                modalRelativePath={modalRelativePath}
                userFile={userFile}
                setModalShowState={setModalShowState}
              />
            </Td>
          </Tr>
        </Tbody>
      )
    })
  }

  return (
    <React.Fragment>
      <Table id='table-user-files-search-results' aria-label='User files search results table' variant='compact'>
        <Thead>
          <Tr>
            <Th style={{ width: '32px' }}></Th>
            <Th>Path</Th>
            <Th>Updated at</Th>
            <Th>Actions</Th>
          </Tr>
        </Thead>
        {getTable()}
      </Table>
    </React.Fragment>
  )
}

export { UserFilesSearchResultsTable }
