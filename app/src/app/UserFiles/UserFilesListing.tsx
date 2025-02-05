import * as React from 'react'
import { Table, Tbody, Td, Th, Thead, Tr } from '@patternfly/react-table'
import { UserFilesMenuKebab } from './Menu/UserFilesMenuKebab'

export interface UserFilesListingTableProps {
  modalAction
  modalFileName
  userFiles
  setModalShowState
}

const UserFilesListingTable: React.FunctionComponent<UserFilesListingTableProps> = ({
  userFiles,
  modalAction,
  modalFileName,
  setModalShowState
}: UserFilesListingTableProps) => {
  const getTable = () => {
    if (userFiles.length == 0) {
      return ''
    } else {
      return userFiles.map((userFile) => (
        <Tbody key={userFile.index}>
          <Tr>
            <Td dataLabel='filename'>{userFile.filename}</Td>
            <Td dataLabel='updated_at'>{userFile.updated_at}</Td>
            <Td dataLabel='actions'>
              <UserFilesMenuKebab
                modalAction={modalAction}
                modalFileName={modalFileName}
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
