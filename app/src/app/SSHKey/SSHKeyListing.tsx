import * as React from 'react'
import { Table, Tbody, Td, Th, Thead, Tr } from '@patternfly/react-table'
import { SSHKeyMenuKebab } from './Menu/SSHKeyMenuKebab'
import { SSHKeyModal } from './Modal/SSHKeyModal'

export interface SSHKeysListingTableProps {
  sshKeys
}

const SSHKeyListingTable: React.FunctionComponent<SSHKeysListingTableProps> = ({ sshKeys }: SSHKeysListingTableProps) => {
  const [modalShowState, setModalShowState] = React.useState(false)

  const getTable = () => {
    if (sshKeys.length == 0) {
      return ''
    } else {
      return sshKeys.map((sshKey) => (
        <Tbody key={sshKey.id}>
          <Tr>
            <Td dataLabel='title'>{sshKey.title}</Td>
            <Td dataLabel='created_at'>{sshKey.created_at}</Td>
            <Td dataLabel='actions'>
              <SSHKeyMenuKebab sshKey={sshKey} />
            </Td>
          </Tr>
        </Tbody>
      ))
    }
  }

  return (
    <React.Fragment>
      <Table id='table-user-ssh-keys' aria-label='User ssh keys table'>
        <Thead>
          <Tr>
            <Th>Name</Th>
            <Th>Created at</Th>
            <Th>Actions</Th>
          </Tr>
        </Thead>
        {getTable()}
      </Table>
      <SSHKeyModal modalShowState={modalShowState} setModalShowState={setModalShowState} />
    </React.Fragment>
  )
}

export { SSHKeyListingTable }
