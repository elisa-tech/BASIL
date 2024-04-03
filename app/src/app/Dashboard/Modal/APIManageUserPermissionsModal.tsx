import React from 'react'
import {
  Button,
  Checkbox,
  DescriptionList,
  DescriptionListDescription,
  DescriptionListGroup,
  DescriptionListTerm,
  Divider,
  Flex,
  FlexItem,
  Hint,
  HintBody,
  Modal,
  ModalVariant,
  SearchInput
} from '@patternfly/react-core'
import * as Constants from '../../Constants/constants'
import { useAuth } from '../../User/AuthProvider'

export interface ManageUserPermissionsProps {
  api
  modalShowState
  setModalShowState
}

export const APIManageUserPermissionsModal: React.FunctionComponent<ManageUserPermissionsProps> = ({
  api,
  modalShowState,
  setModalShowState
}: ManageUserPermissionsProps) => {
  const auth = useAuth()
  const UNSET_USER_EMAIL = ''
  const UNSET_USER_ROLE = ''
  const [userEmailSearchValue, setUserEmailSearchValue] = React.useState('')
  const [userEmail, setUserEmail] = React.useState(UNSET_USER_EMAIL)
  const [userRole, setUserRole] = React.useState(UNSET_USER_ROLE)
  const [userEditPermission, setUserEditPermission] = React.useState(false)
  const [userManagePermission, setUserManagePermission] = React.useState(false)
  const [userReadPermission, setUserReadPermission] = React.useState(false)
  const [userWritePermission, setUserWritePermission] = React.useState(false)
  const [isModalOpen, setIsModalOpen] = React.useState(false)
  const [messageValue, setMessageValue] = React.useState('')

  const onChangeUserEmailSearchValue = (value) => {
    setUserEmailSearchValue(value.trim())
  }

  const handlePermissionChanges = (event: React.FormEvent<HTMLInputElement>, checked: boolean) => {
    const target = event.currentTarget
    const name = target.name

    switch (name) {
      case 'user-permission-check-edit':
        setUserEditPermission(checked)
        break
      case 'user-permission-check-manage':
        setUserManagePermission(checked)
        break
      case 'user-permission-check-read':
        setUserReadPermission(checked)
        break
      case 'user-permission-check-write':
        setUserWritePermission(checked)
        break
      default:
        break
    }
  }

  const handleModalToggle = () => {
    const new_state = !modalShowState
    setModalShowState(new_state)
    setIsModalOpen(new_state)
  }

  React.useEffect(() => {
    setIsModalOpen(modalShowState)
  }, [modalShowState])

  const handleSearchUser = () => {
    //Reset Default
    setMessageValue('')
    setUserEmail(UNSET_USER_EMAIL)
    setUserRole(UNSET_USER_ROLE)
    setUserEditPermission(false)
    setUserManagePermission(false)
    setUserReadPermission(false)
    setUserWritePermission(false)

    //let response_status
    let response_data
    const search_string = userEmailSearchValue.trim()
    let url

    if (search_string.length == 0) {
      setMessageValue('Value not valid.')
      return
    }

    if (search_string == auth.userEmai) {
      setMessageValue('This is the Email of the logged user!')
      return
    }

    url = Constants.API_BASE_URL + '/user/permissions/api?api-id=' + api.id
    url += '&user-id=' + auth.userId + '&token=' + auth.token
    url += '&email=' + userEmailSearchValue
    fetch(url, {
      method: 'GET',
      headers: {
        Accept: 'application/json',
        'Content-Type': 'application/json'
      }
    })
      .then((response) => {
        //response_status = response.status
        response_data = response.json()
        if (response.status !== 200) {
          setMessageValue('Unable to find the user')
          return
        }
        return response_data
      })
      .then((response_data) => {
        setUserEmail(response_data['email'])
        setUserRole(response_data['role'])
        if (response_data['permissions'].indexOf('e') >= 0) {
          setUserEditPermission(true)
        }
        if (response_data['permissions'].indexOf('m') >= 0) {
          setUserManagePermission(true)
        }
        if (response_data['permissions'].indexOf('r') >= 0) {
          setUserReadPermission(true)
        }
        if (response_data['permissions'].indexOf('w') >= 0) {
          setUserWritePermission(true)
        }
      })
      .catch((err) => {
        setMessageValue(err.toString())
        console.log(err.message)
      })
  }

  const handleUserPermissionSubmit = () => {
    let response_data
    let permissions = ''

    if (userEditPermission) {
      permissions += 'e'
    }
    if (userManagePermission) {
      permissions += 'm'
    }
    if (userReadPermission) {
      permissions += 'r'
    }
    if (userWritePermission) {
      permissions += 'w'
    }

    const url = Constants.API_BASE_URL + '/user/permissions/api'
    const data = { 'api-id': api.id, 'user-id': auth.userId, token: auth.token, email: userEmailSearchValue, permissions: permissions }
    fetch(url, {
      method: 'PUT',
      headers: {
        Accept: 'application/json',
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(data)
    })
      .then((response) => {
        response_data = response.json()
        if (response.status !== 200) {
          setMessageValue('Unable to find the user')
          return
        } else {
          setMessageValue('Changes saved!')
        }
        return response_data
      })
      .catch((err) => {
        setMessageValue(err.toString())
        console.log(err.message)
      })
  }

  return (
    <React.Fragment>
      <Modal
        bodyAriaLabel='APIManageUserPermissionsModal'
        aria-label='api manage user permissions modal'
        tabIndex={0}
        variant={ModalVariant.large}
        title='Manage User Permission'
        description={api != null ? 'Current api ' + api.api + ' from ' + api.library + ' ' + api.library_version : ''}
        isOpen={isModalOpen}
        onClose={handleModalToggle}
        actions={[
          <Button key='confirm' variant='primary' onClick={() => handleUserPermissionSubmit()}>
            Confirm
          </Button>,
          <Button key='cancel' variant='link' onClick={handleModalToggle}>
            Cancel
          </Button>
        ]}
      >
        {messageValue ? (
          <div>
            <Hint>
              <HintBody>{messageValue}</HintBody>
            </Hint>
            <br />
          </div>
        ) : (
          <span></span>
        )}

        <Flex>
          <FlexItem>
            <SearchInput
              placeholder='Search User by email address'
              value={userEmailSearchValue}
              onChange={(_event, value) => onChangeUserEmailSearchValue(value)}
              onClear={() => onChangeUserEmailSearchValue('')}
              style={{ width: '400px' }}
            />
          </FlexItem>
          <FlexItem>
            <Button key='search' variant='primary' onClick={() => handleSearchUser()}>
              Search
            </Button>
          </FlexItem>
        </Flex>
        <br />

        {userEmail != UNSET_USER_EMAIL ? (
          <div>
            <br />
            <DescriptionList>
              <DescriptionListGroup>
                <DescriptionListTerm>User Email</DescriptionListTerm>
                <DescriptionListDescription key={'selected-user-email'}>{userEmailSearchValue}</DescriptionListDescription>
              </DescriptionListGroup>
            </DescriptionList>
            <br />
            <Divider />
            <br />
            <Checkbox
              id='user-permission-check-read'
              name='user-permission-check-read'
              label='Read permission'
              isChecked={userReadPermission}
              onChange={handlePermissionChanges}
              description='Permission to read work items and relationships of the selected software component.'
            />
            <Checkbox
              id='user-permission-check-write'
              name='user-permission-check-write'
              label='Write permission'
              isChecked={userWritePermission}
              isDisabled={userRole == 'GUEST' || userRole == UNSET_USER_ROLE}
              onChange={handlePermissionChanges}
              description='Permission to add and edit work items and relationships of the selected software component.'
            />
            <Checkbox
              id='user-permission-check-edit'
              name='user-permission-check-edit'
              label='Edit permission'
              isChecked={userEditPermission}
              isDisabled={userRole == 'GUEST' || userRole == UNSET_USER_ROLE}
              onChange={handlePermissionChanges}
              description='Permission to edit parameters of the selected software component.'
            />
            <Checkbox
              id='user-permission-check-manage'
              name='user-permission-check-manage'
              label='Owner permission'
              isChecked={userManagePermission}
              isDisabled={userRole == 'GUEST' || userRole == UNSET_USER_ROLE}
              onChange={handlePermissionChanges}
              description='Manage user permissions to the selected software component.'
            />
          </div>
        ) : (
          ''
        )}
      </Modal>
    </React.Fragment>
  )
}
