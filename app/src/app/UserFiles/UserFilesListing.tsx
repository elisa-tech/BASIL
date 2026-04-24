import * as React from 'react'
import { Table, Tbody, Td, Th, Thead, Tr } from '@patternfly/react-table'
import { UserFilesMenuKebab } from './Menu/UserFilesMenuKebab'
import FolderIcon from '@patternfly/react-icons/dist/esm/icons/folder-icon'
import FileIcon from '@patternfly/react-icons/dist/esm/icons/file-icon'
import { Button } from '@patternfly/react-core'

export interface UserFilesListingTableProps {
  modalAction
  modalFileName
  modalRelativePath
  userFiles
  setModalShowState
  currentPath: string
  navigateTo: (path: string) => void
}

const UserFilesListingTable: React.FunctionComponent<UserFilesListingTableProps> = ({
  userFiles,
  modalAction,
  modalFileName,
  modalRelativePath,
  setModalShowState,
  currentPath,
  navigateTo
}: UserFilesListingTableProps) => {
  const getTable = () => {
    if (userFiles.length === 0) {
      return (
        <Tbody>
          <Tr>
            <Td colSpan={4} style={{ textAlign: 'center', color: '#6a6e73', padding: '24px' }}>
              This folder is empty
            </Td>
          </Tr>
        </Tbody>
      )
    } else {
      return userFiles.map((userFile) => (
        <Tbody key={userFile.index}>
          <Tr>
            <Td dataLabel='type' style={{ width: '32px' }}>
              {userFile.type === 'directory' ? <FolderIcon style={{ color: '#f0ab00' }} /> : <FileIcon style={{ color: '#6a6e73' }} />}
            </Td>
            <Td dataLabel='filename'>
              {userFile.type === 'directory' ? (
                <Button
                  variant='link'
                  isInline
                  onClick={() => {
                    const newPath = currentPath ? currentPath + '/' + userFile.name : userFile.name
                    navigateTo(newPath)
                  }}
                  style={{ fontWeight: 600 }}
                >
                  {userFile.name}
                </Button>
              ) : (
                userFile.name
              )}
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
      ))
    }
  }

  return (
    <React.Fragment>
      <Table id='table-user-files' aria-label='User files table' variant='compact'>
        <Thead>
          <Tr>
            <Th style={{ width: '32px' }}></Th>
            <Th>Name</Th>
            <Th>Updated at</Th>
            <Th>Actions</Th>
          </Tr>
        </Thead>
        {getTable()}
      </Table>
    </React.Fragment>
  )
}

export { UserFilesListingTable }
