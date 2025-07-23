import * as React from 'react'
import { Table, Tbody, Td, Th, Thead, Tr } from '@patternfly/react-table'
import { Checkbox, Label } from '@patternfly/react-core'
import { AdminMenuKebab } from './Menu/AdminMenuKebab'
import { AdminModal } from './Modal/AdminModal'

export interface AdminListingTableProps {
  users
}

const AdminListingTable: React.FunctionComponent<AdminListingTableProps> = ({ users }: AdminListingTableProps) => {
  const [modalShowState, setModalShowState] = React.useState(false)
  const [modalFormData, setModalFormData] = React.useState('')

  const setModalAdminInfo = (_modalData, _modalShowState) => {
    setModalFormData(_modalData)
    setModalShowState(_modalShowState)
  }

  const getTable = () => {
    if (users.length == 0) {
      return ''
    } else {
      return users.map((user) => (
        <Tbody key={user.id}>
          <Tr>
            <Td dataLabel='enabled'>
              <Checkbox
                id={'checkbox-user-enabled-' + user.id}
                name={'checkbox-user-enabled-' + user.id}
                label=''
                checked={user.enabled == 1 ? true : false}
                isDisabled={true}
              />
            </Td>
            <Td dataLabel='username'>{user.username}</Td>
            <Td dataLabel='email'>{user.email}</Td>
            <Td dataLabel='role'>
              <Label color={user.role == 'GUEST' ? 'red' : user.role == 'ADMIN' ? 'green' : 'blue'}>{user.role}</Label>
            </Td>
            <Td dataLabel='from'>{user.created_at}</Td>
            <Td dataLabel='actions'>
              <AdminMenuKebab setModalAdminInfo={setModalAdminInfo} user={user} />
            </Td>
          </Tr>
        </Tbody>
      ))
    }
  }

  return (
    <React.Fragment>
      <Table variant='compact' id='table-user-management' aria-label='User management table'>
        <Thead>
          <Tr>
            <Th>Enabled</Th>
            <Th>Username</Th>
            <Th>Email</Th>
            <Th>Role</Th>
            <Th>From</Th>
            <Th>Actions</Th>
          </Tr>
        </Thead>
        {getTable()}
      </Table>
      <AdminModal user={modalFormData} modalShowState={modalShowState} setModalShowState={setModalShowState} />
    </React.Fragment>
  )
}

export { AdminListingTable }
