import * as React from 'react'
import * as Constants from '../Constants/constants'
import { ExpandableRowContent, Table, Tbody, Td, Th, Thead, Tr } from '@patternfly/react-table'
import { Button, Flex, FlexItem, Text, TextContent, TextList, TextListItem, TextVariants } from '@patternfly/react-core'
import { APIForm } from './Form/APIForm'
import { ApiMenuKebab } from './Menu/ApiMenuKebab'
import { LeavesProgressBar } from '../Custom/LeavesProgressBar'
import { useAuth } from '@app/User/AuthProvider'
import { AttentionBellIcon } from '@patternfly/react-icons/dist/esm/icons/attention-bell-icon'

interface APIHistoryData {
  versionNumber: number
  id?: string
  description?: string
  notes?: string
}

interface APIDetailsData {
  url?: string
  library?: string
  branch?: string
  fileMatchCriteria: string
}

interface DataObject {
  id: string
  api: string
  coverage: 0 | 25 | 50 | 75 | 100
  history: APIHistoryData[]
  details: APIDetailsData
}

export interface APIListingTableProps {
  setModalInfo
  apis
  setModalCheckSpecInfo
  setModalDeleteInfo
  setModalManageUserPermissionsInfo
}

const APIListingTable: React.FunctionComponent<APIListingTableProps> = ({
  setModalInfo,
  setModalCheckSpecInfo,
  setModalDeleteInfo,
  setModalManageUserPermissionsInfo,
  apis
}: APIListingTableProps) => {
  let auth = useAuth()
  const [expandedRepoNames, setExpandedRepoNames] = React.useState<string[]>([])
  const setRepoExpanded = (repo: DataObject, isExpanding = true) =>
    setExpandedRepoNames((prevExpanded) => {
      const otherExpandedRepoNames = prevExpanded.filter((r) => r !== repo.id)
      return isExpanding ? [...otherExpandedRepoNames, repo.id] : otherExpandedRepoNames
    })
  const isRepoExpanded = (repo: DataObject) => expandedRepoNames.includes(repo.id)
  const [currentApiID, setCurrentApiID] = React.useState(0)
  const [currentApiHistory, setCurrentApiHistory] = React.useState([])

  React.useEffect(() => {
    const url = Constants.API_BASE_URL + '/apis/history?api-id=' + currentApiID
    fetch(url)
      .then((res) => res.json())
      .then((data) => {
        setCurrentApiHistory(data)
      })
      .catch((err) => {
        console.log(err.message)
      })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentApiID])

  const columnNames = {
    id: 'ID',
    api: 'API',
    library_version: 'Version',
    created_by: 'Owner',
    category: 'Category',
    coverage: 'Coverage',
    notifications: 'Notifications',
    actions: 'Actions'
  }

  const getHistory = () => {
    if (currentApiHistory.length == 0) {
      return ''
    } else {
      return currentApiHistory.map((version, versionIndex) => (
        <React.Fragment key={versionIndex}>
          <Text component={TextVariants.h3}>
            Version {version['version']} - {version['created_at']}
          </Text>
          <TextList>
            {Object.keys(version['object']).map((key, index) => (
              <TextListItem key={index}>
                <em>{key}: </em>
                {version['object'][key]}
              </TextListItem>
            ))}
          </TextList>
        </React.Fragment>
      ))
    }
  }

  const getTable = () => {
    if (apis.length == 0) {
      return ''
    } else {
      return apis.map((dataRow, rowIndex) => (
        <Tbody key={dataRow.id} isExpanded={isRepoExpanded(dataRow)}>
          <Tr>
            <Td
              id={'td-expand-' + dataRow.id}
              expand={{
                rowIndex,
                isExpanded: isRepoExpanded(dataRow),
                onToggle: () => {
                  setCurrentApiID(dataRow.id)
                  setRepoExpanded(dataRow, !isRepoExpanded(dataRow))
                },
                expandId: 'composable-expandable-example'
              }}
            />
            <Td dataLabel={columnNames.id}>{dataRow.id}</Td>
            <Td dataLabel={columnNames.api}>
              <Button variant='link' component='a' href={'mapping/' + dataRow.id}>
                {dataRow.api}
              </Button>
            </Td>
            <Td dataLabel={columnNames.library_version}>{dataRow.library_version}</Td>
            <Td dataLabel={columnNames.created_by}>{dataRow.created_by}</Td>
            <Td dataLabel={columnNames.category}>{dataRow.category}</Td>
            <Td dataLabel={columnNames.coverage}>
              <LeavesProgressBar progressValue={dataRow.covered} progressId={'api-coverage-' + dataRow.id} />
            </Td>
            <Td dataLabel={columnNames.notifications}>{dataRow.notifications == 1 ? <AttentionBellIcon /> : ''}</Td>
            <Td dataLabel={columnNames.actions}>
              <ApiMenuKebab
                setModalInfo={setModalInfo}
                setModalCheckSpecInfo={setModalCheckSpecInfo}
                setModalDeleteInfo={setModalDeleteInfo}
                setModalManageUserPermissionsInfo={setModalManageUserPermissionsInfo}
                apiData={dataRow}
              />
            </Td>
          </Tr>
          <Tr isExpanded={isRepoExpanded(dataRow)}>
            <Td colSpan={Object.keys(columnNames).length + 1}>
              <ExpandableRowContent>
                <Flex>
                  <FlexItem flex={{ default: 'flex_1' }}>
                    <TextContent tabIndex={0} style={{ height: '460px', overflowY: 'scroll' }}>
                      <Text component={TextVariants.h2}>API History</Text>
                      {getHistory()}
                    </TextContent>
                  </FlexItem>
                  <FlexItem flex={{ default: 'flex_1' }}>
                    {auth.isLogged() && dataRow['permissions'].indexOf('e') > 0 ? (
                      <APIForm formAction={'edit'} formVerb={'PUT'} formData={dataRow} />
                    ) : (
                      ''
                    )}
                  </FlexItem>
                </Flex>
              </ExpandableRowContent>
            </Td>
          </Tr>
        </Tbody>
      ))
    }
  }

  return (
    <Table id='table-api-listing' aria-label='Api Listing table'>
      <Thead>
        <Tr>
          <Th />
          <Th>{columnNames.id}</Th>
          <Th>{columnNames.api}</Th>
          <Th>{columnNames.library_version}</Th>
          <Th>{columnNames.created_by}</Th>
          <Th>{columnNames.category}</Th>
          <Th>{columnNames.coverage}</Th>
          <Th>{columnNames.notifications}</Th>
          <Th>{columnNames.actions}</Th>
        </Tr>
      </Thead>
      {getTable()}
    </Table>
  )
}

export { APIListingTable }
