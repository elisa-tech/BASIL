import _ from 'lodash'
import React from 'react'
import {
  Button,
  Flex,
  FlexItem,
  Hint,
  HintBody,
  Modal,
  ModalVariant,
  SearchInput,
  Tabs,
  Tab,
  TabContent,
  TabContentBody,
  TabTitleText
} from '@patternfly/react-core'
import * as Constants from '@app/Constants/constants'
import { Table, Tbody, Td, Th, Thead, Tr } from '@patternfly/react-table'
import { useAuth } from '@app/User/AuthProvider'

export interface ManageUserPermissionsProps {
  api
  modalShowState
  setModalShowState
}

interface UserPermissionInterface {
  id: number
  email: string
  enabled: number
  role: string
  permissions: string
}

interface UserApiInterface {
  id: number
  api: string
  library: string
  library_version: string
  selected: number
}

export const APIManageUserPermissionsModal: React.FunctionComponent<ManageUserPermissionsProps> = ({
  api,
  modalShowState,
  setModalShowState
}: ManageUserPermissionsProps) => {
  const auth = useAuth()
  const UNSET_USER_EMAIL = ''
  const UNSET_USER_ROLE = ''
  const _READ = 'r'
  const _WRITE = 'w'
  const _EDIT = 'e'
  const _OWNER = 'm'

  let usersPermissionsDataLoaded = React.useRef<boolean>(false)
  let userApisDataLoaded = React.useRef<boolean>(false)

  const [userEmailSearchValue, setUserEmailSearchValue] = React.useState('')
  const [userApiSearchValue, setUserApiSearchValue] = React.useState('')
  const [users, setUsers] = React.useState<UserPermissionInterface[]>([])
  const [userApis, setUserApis] = React.useState<UserApiInterface[]>([])
  const [allReadSelected, setAllReadSelected] = React.useState(false)
  const [allWriteSelected, setAllWriteSelected] = React.useState(false)
  const [allEditSelected, setAllEditSelected] = React.useState(false)
  const [allOwnerSelected, setAllOwnerSelected] = React.useState(false)
  const [allUserApisSelected, setAllUserApisSelected] = React.useState(false)

  const [isModalOpen, setIsModalOpen] = React.useState(false)
  const [messageValue, setMessageValue] = React.useState('')

  const [activeTabKey, setActiveTabKey] = React.useState<string | number>(0)

  const usersTabRef = React.createRef<HTMLElement>()
  const cloneTabRef = React.createRef<HTMLElement>()

  React.useEffect(() => {
    setIsModalOpen(modalShowState)
    if (!modalShowState) {
      usersPermissionsDataLoaded.current = false
      userApisDataLoaded.current = false
    } else {
      setActiveTabKey(0)
    }
    setMessageValue('')
  }, [modalShowState])

  React.useEffect(() => {
    if (api) {
      if (!usersPermissionsDataLoaded.current) {
        loadUsers()
      }
      if (!userApisDataLoaded.current) {
        loadUserApis()
      }
    }
  }, [api])

  React.useEffect(() => {
    let allRead = true
    let allWrite = true
    let allEdit = true
    let allOwner = true
    for (let i = 0; i < users.length; i++) {
      if (allRead) {
        if (users[i]['permissions'].indexOf(_READ) < 0) {
          allRead = false
        }
      }
      //Guest can READ
      if (userRoleIsGuest(users[i])) {
        continue
      }
      if (allWrite) {
        if (users[i]['permissions'].indexOf(_WRITE) < 0) {
          allWrite = false
        }
      }
      if (allEdit) {
        if (users[i]['permissions'].indexOf(_EDIT) < 0) {
          allEdit = false
        }
      }
      if (allOwner) {
        if (users[i]['permissions'].indexOf(_OWNER) < 0) {
          allOwner = false
        }
      }
    }
    setAllReadSelected(allRead)
    setAllWriteSelected(allWrite)
    setAllEditSelected(allEdit)
    setAllOwnerSelected(allOwner)
  }, [users])

  React.useEffect(() => {
    let allUserApis = true
    for (let i = 0; i < userApis.length; i++) {
      if (userApis[i]['selected'] != 1) {
        allUserApis = false
        break
      }
    }
    setAllUserApisSelected(allUserApis)
  }, [userApis])

  const onChangeUserEmailSearchValue = (value) => {
    setUserEmailSearchValue(value.trim())
  }

  const onChangeUserApiSearchValue = (value) => {
    setUserApiSearchValue(value.trim())
  }

  const handleModalToggle = () => {
    const new_state = !modalShowState
    setModalShowState(new_state)
    setIsModalOpen(new_state)
  }

  const userRoleIsGuest = (user) => {
    return user['role'].toUpperCase() == 'GUEST'
  }

  const loadUserApis = () => {
    let response_data
    const search_string = userApiSearchValue.trim()
    let url = Constants.API_BASE_URL + Constants.API_USER_APIS_ENDPOINT
    url += '?api-id=' + api.id
    url += '&user-id=' + auth.userId + '&token=' + auth.token
    url += '&search=' + search_string
    fetch(url, {
      method: 'GET',
      headers: Constants.JSON_HEADER
    })
      .then((response) => {
        response_data = response.json()
        if (response.status !== 200) {
          setMessageValue('Unable to find the api')
          return
        }
        return response_data
      })
      .then((response_data) => {
        setUserApis(response_data)
        userApisDataLoaded.current = true
      })
      .catch((err) => {
        setMessageValue(err.toString())
        console.log(err.message)
      })
  }

  const loadUsers = () => {
    let response_data
    const search_string = userEmailSearchValue.trim()
    let url

    if (search_string == auth.userEmai) {
      setMessageValue('This is the Email of the logged user!')
      return
    }

    url = Constants.API_BASE_URL + Constants.API_USER_PERMISSIONS_API_ENDPOINT + '?api-id=' + api.id
    url += '&user-id=' + auth.userId + '&token=' + auth.token
    url += '&search=' + userEmailSearchValue
    fetch(url, {
      method: 'GET',
      headers: Constants.JSON_HEADER
    })
      .then((response) => {
        response_data = response.json()
        if (response.status !== 200) {
          setMessageValue('Unable to find the user')
          return
        }
        return response_data
      })
      .then((response_data) => {
        setUsers(response_data)
        usersPermissionsDataLoaded.current = true
      })
      .catch((err) => {
        setMessageValue(err.toString())
        console.log(err.message)
      })
  }

  const handleSubmit = () => {
    if (activeTabKey == 0) {
      handleUserPermissionSubmit()
    } else {
      handleCopyUserPermissionSubmit()
    }
  }

  const handleCopyUserPermissionSubmit = () => {
    let response_data
    let copy_to: number[] = []
    for (let i = 0; i < userApis.length; i++) {
      if (userApis[i]['selected'] == 1) {
        copy_to.push(userApis[i]['id'])
      }
    }
    if (copy_to.length == 0) {
      setMessageValue('Please select at least one Software Component.')
      return
    }
    const url = Constants.API_BASE_URL + Constants.API_USER_PERMISSIONS_API_COPY_ENDPOINT
    const data = {
      'api-id': api.id,
      'user-id': auth.userId,
      'copy-to': copy_to,
      token: auth.token
    }
    fetch(url, {
      method: 'PUT',
      headers: Constants.JSON_HEADER,
      body: JSON.stringify(data)
    })
      .then((response) => {
        response_data = response.json()
        if (response.status !== 200) {
          setMessageValue('Unable to copy permissions')
          return
        } else {
          setMessageValue('Changes saved!')
          loadUserApis()
        }
        return response_data
      })
      .catch((err) => {
        setMessageValue(err.toString())
        console.log(err.message)
      })
  }

  const handleUserPermissionSubmit = () => {
    let response_data

    const url = Constants.API_BASE_URL + Constants.API_USER_PERMISSIONS_API_ENDPOINT
    const data = { 'api-id': api.id, 'user-id': auth.userId, token: auth.token, email: userEmailSearchValue, permissions: users }
    fetch(url, {
      method: 'PUT',
      headers: Constants.JSON_HEADER,
      body: JSON.stringify(data)
    })
      .then((response) => {
        response_data = response.json()
        if (response.status !== 200) {
          setMessageValue('Unable to find the user')
          return
        } else {
          setMessageValue('Changes saved!')
          loadUsers()
          loadUserApis()
        }
        return response_data
      })
      .catch((err) => {
        setMessageValue(err.toString())
        console.log(err.message)
      })
  }

  const handleUserEmailSearchKeyPress = (event) => {
    if (event.key === 'Enter') {
      loadUsers()
    }
  }

  const handleUserApiSearchKeyPress = (event) => {
    if (event.key === 'Enter') {
      loadUserApis()
    }
  }

  // Toggle currently active tab
  const handleTabClick = (event: React.MouseEvent | React.KeyboardEvent | MouseEvent, tabIndex: string | number) => {
    setActiveTabKey(tabIndex)
  }

  const selectAllUserApis = (isSelecting: boolean) => {
    setMessageValue('')
    let tmp = _.cloneDeep(userApis)
    for (let i = 0; i < tmp.length; i++) {
      tmp[i]['selected'] = isSelecting ? 1 : 0
    }
    setUserApis(tmp)
  }

  const selectAll = (permissionType: string, isSelecting: boolean) => {
    setMessageValue('')
    let tmp = _.cloneDeep(users)
    for (let i = 0; i < tmp.length; i++) {
      if (permissionType != _READ && userRoleIsGuest(tmp[i])) {
        tmp[i]['permissions'] = tmp[i]['permissions'].replace(permissionType, '')
        continue
      }
      if (isSelecting) {
        if (tmp[i]['permissions'].indexOf(permissionType) < 0) {
          tmp[i]['permissions'] = tmp[i]['permissions'] + permissionType
        }
      } else {
        if (tmp[i]['permissions'].indexOf(permissionType) >= 0) {
          tmp[i]['permissions'] = tmp[i]['permissions'].replace(permissionType, '')
        }
      }
    }
    setUsers(tmp)
  }

  const onSelectPermission = (userPermission, permissionType: string, isSelecting: boolean) => {
    // Removing Read permission, will remove also Write permission
    // Adding Write permission, will add also Read permission
    setMessageValue('')
    let tmp = _.cloneDeep(users)
    for (let i = 0; i < tmp.length; i++) {
      if (tmp[i]['id'] == userPermission['id']) {
        if (isSelecting) {
          if (tmp[i]['permissions'].indexOf(permissionType) < 0) {
            tmp[i]['permissions'] = tmp[i]['permissions'] + permissionType
          }
          if (permissionType == _WRITE) {
            if (tmp[i]['permissions'].indexOf(_READ) < 0) {
              tmp[i]['permissions'] = tmp[i]['permissions'] + _READ
            }
          }
        } else {
          if (tmp[i]['permissions'].indexOf(permissionType) >= 0) {
            tmp[i]['permissions'] = tmp[i]['permissions'].replace(permissionType, '')
          }
          if (permissionType == _READ) {
            if (tmp[i]['permissions'].indexOf(_WRITE) >= 0) {
              tmp[i]['permissions'] = tmp[i]['permissions'].replace(_WRITE, '')
            }
          }
        }
        break
      }
    }
    setUsers(tmp)
  }

  const onSelectUserApi = (userApi, isSelecting: boolean) => {
    setMessageValue('')
    let tmp = _.cloneDeep(userApis)
    for (let i = 0; i < tmp.length; i++) {
      if (tmp[i]['id'] == userApi['id']) {
        tmp[i]['selected'] = isSelecting ? 1 : 0
        break
      }
    }
    setUserApis(tmp)
  }

  return (
    <React.Fragment>
      <Modal
        width={Constants.MODAL_WIDTH}
        bodyAriaLabel='APIManageUserPermissionsModal'
        aria-label='api manage user permissions modal'
        tabIndex={0}
        variant={ModalVariant.large}
        title='Manage User Permission'
        description={api != null ? 'Current api ' + api.api + ' from ' + api.library + ' version ' + api.library_version : ''}
        isOpen={isModalOpen}
        onClose={handleModalToggle}
        actions={[
          <Button key='confirm' variant='primary' onClick={() => handleSubmit()}>
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

        <Tabs activeKey={activeTabKey} onSelect={handleTabClick} aria-label='User permission management tabs' role='region'>
          <Tab
            eventKey={0}
            id='tab-btn-user-permissions-users'
            title={<TabTitleText>Users</TabTitleText>}
            tabContentId='tabUserPermissionsUsers'
            tabContentRef={usersTabRef}
          />
          <Tab
            eventKey={1}
            id='tab-btn-user-permissions-clone'
            title={<TabTitleText>Clone to other Sw Components</TabTitleText>}
            tabContentId='tabUserPermissionsClone'
            tabContentRef={cloneTabRef}
          />
        </Tabs>
        <TabContent eventKey={0} id='tabUserPermissionsUsers' ref={usersTabRef} hidden={0 !== activeTabKey}>
          <TabContentBody>
            <br></br>
            <Flex>
              <FlexItem>
                <SearchInput
                  placeholder='Search User by email address'
                  value={userEmailSearchValue}
                  onChange={(_event, value) => onChangeUserEmailSearchValue(value)}
                  onClear={() => onChangeUserEmailSearchValue('')}
                  onKeyUp={handleUserEmailSearchKeyPress}
                  style={{ width: '400px' }}
                />
              </FlexItem>
              <FlexItem>
                <Button key='search' variant='primary' onClick={() => loadUsers()}>
                  Search
                </Button>
              </FlexItem>
            </Flex>

            {users && (
              <div style={{ height: '500px', overflowY: 'scroll' }}>
                <Table aria-label='User permission table' variant='compact'>
                  <Thead>
                    <Tr>
                      <Th width={50}>User</Th>
                      <Th width={10}>Role</Th>
                      <Th
                        width={10}
                        select={{
                          onSelect: (_event, isSelecting) => selectAll(_READ, isSelecting),
                          isSelected: allReadSelected
                        }}
                        aria-label='Read'
                      >
                        Read
                      </Th>
                      <Th
                        width={10}
                        select={{
                          onSelect: (_event, isSelecting) => selectAll(_WRITE, isSelecting),
                          isSelected: allWriteSelected
                        }}
                        aria-label='Write'
                      >
                        Write
                      </Th>
                      <Th
                        width={10}
                        select={{
                          onSelect: (_event, isSelecting) => selectAll(_EDIT, isSelecting),
                          isSelected: allEditSelected
                        }}
                        aria-label='Edit'
                      >
                        Edit
                      </Th>
                      <Th
                        width={10}
                        select={{
                          onSelect: (_event, isSelecting) => selectAll(_OWNER, isSelecting),
                          isSelected: allOwnerSelected
                        }}
                        aria-label='Owner'
                      >
                        Owner
                      </Th>
                    </Tr>
                  </Thead>
                  <Tbody>
                    {users
                      ? users.map((userPermission, rowIndex) => (
                          <Tr key={rowIndex}>
                            <Td dataLabel='user'>{userPermission['email']}</Td>
                            <Td dataLabel='user'>{userPermission['role']}</Td>
                            <Td
                              select={{
                                rowIndex,
                                onSelect: (_event, isSelecting) => onSelectPermission(userPermission, _READ, isSelecting),
                                isSelected: userPermission['permissions'].indexOf(_READ) >= 0
                              }}
                            />
                            <Td
                              select={{
                                rowIndex,
                                isDisabled: userRoleIsGuest(userPermission),
                                onSelect: (_event, isSelecting) => onSelectPermission(userPermission, _WRITE, isSelecting),
                                isSelected: userPermission['permissions'].indexOf(_WRITE) >= 0
                              }}
                            />
                            <Td
                              select={{
                                rowIndex,
                                isDisabled: userRoleIsGuest(userPermission),
                                onSelect: (_event, isSelecting) => onSelectPermission(userPermission, _EDIT, isSelecting),
                                isSelected: userPermission['permissions'].indexOf(_EDIT) >= 0
                              }}
                            />
                            <Td
                              select={{
                                rowIndex,
                                isDisabled: userRoleIsGuest(userPermission),
                                onSelect: (_event, isSelecting) => onSelectPermission(userPermission, _OWNER, isSelecting),
                                isSelected: userPermission['permissions'].indexOf(_OWNER) >= 0
                              }}
                            />
                          </Tr>
                        ))
                      : ''}
                  </Tbody>
                </Table>
              </div>
            )}
          </TabContentBody>
        </TabContent>
        <TabContent eventKey={1} id='tabUserPermissionsClone' ref={cloneTabRef} hidden={1 !== activeTabKey}>
          <TabContentBody>
            <br></br>
            <Flex>
              <FlexItem>
                <SearchInput
                  placeholder='Search'
                  value={userApiSearchValue}
                  onChange={(_event, value) => onChangeUserApiSearchValue(value)}
                  onClear={() => onChangeUserApiSearchValue('')}
                  onKeyUp={handleUserApiSearchKeyPress}
                  style={{ width: '400px' }}
                />
              </FlexItem>
              <FlexItem>
                <Button key='search' variant='primary' onClick={() => loadUserApis()}>
                  Search
                </Button>
              </FlexItem>
            </Flex>

            {userApis && (
              <div style={{ height: '500px', overflowY: 'scroll' }}>
                <Table aria-label='Copy user permission table' variant='compact'>
                  <Thead>
                    <Tr>
                      <Th
                        width={10}
                        select={{
                          onSelect: (_event, isSelecting) => selectAllUserApis(isSelecting),
                          isSelected: allUserApisSelected
                        }}
                        aria-label='Copy to'
                      >
                        Copy to
                      </Th>
                      <Th width={30}>Sw Component</Th>
                      <Th width={30}>Library</Th>
                      <Th width={10}>Version</Th>
                    </Tr>
                  </Thead>
                  <Tbody>
                    {userApis
                      ? userApis.map((userApi, rowIndex) => (
                          <Tr key={rowIndex}>
                            <Td
                              select={{
                                rowIndex,
                                onSelect: (_event, isSelecting) => onSelectUserApi(userApi, isSelecting),
                                isSelected: userApi['selected'] == 1
                              }}
                            />
                            <Td dataLabel='user'>
                              <Button component='a' href={'/mapping/' + userApi['id']} variant='link'>
                                {userApi['api']}
                              </Button>
                            </Td>
                            <Td dataLabel='user'>
                              <Button component='a' href={'/?currentLibrary=' + userApi['library']} variant='link'>
                                {userApi['library']}
                              </Button>
                            </Td>
                            <Td dataLabel='user'>{userApi['library_version']}</Td>
                          </Tr>
                        ))
                      : ''}
                  </Tbody>
                </Table>
              </div>
            )}
          </TabContentBody>
        </TabContent>
      </Modal>
    </React.Fragment>
  )
}
