import * as React from 'react'
import * as Constants from '@app/Constants/constants'
import {
  ActionGroup,
  Button,
  Divider,
  FileUpload,
  Flex,
  FlexItem,
  FormGroup,
  FormHelperText,
  FormSelect,
  FormSelectOption,
  Grid,
  GridItem,
  HelperText,
  HelperTextItem,
  Hint,
  HintBody,
  TextInput
} from '@patternfly/react-core'
import { Table, Tbody, Td, Th, Thead, Tr } from '@patternfly/react-table'
import { useAuth } from '@app/User/AuthProvider'

interface TestCase {
  description: string
  id: number
  index: number
  title: string
  relative_path: string
  repository: string
}

export interface TestCaseImportProps {
  loadTestCases
}

export const TestCaseImport: React.FunctionComponent<TestCaseImportProps> = ({ loadTestCases }: TestCaseImportProps) => {
  const auth = useAuth()
  const generateJsonUrl = Constants.API_BASE_URL + Constants.API_TEST_CASE_IMPORT_GENERATE_JSON_ENDPOINT
  const importUrl = Constants.API_BASE_URL + Constants.API_TEST_CASE_IMPORT_ENDPOINT
  const [messageValue, setMessageValue] = React.useState('')
  const [statusValue, setStatusValue] = React.useState('waiting')

  // Table
  const [workItems, setWorkItems] = React.useState<TestCase[]>([])

  const [selectedIndexes, setSelectedIndexes] = React.useState<number[]>([])
  const areAllRowsSelected = selectedIndexes.length === workItems.length
  const [shifting, setShifting] = React.useState(false)
  const [recentSelectedRowIndex, setRecentSelectedRowIndex] = React.useState<number | null>(null)

  const [currentView, setCurrentView] = React.useState('')
  const SELECT_USER_FILE_VIEW = 'select-user-file-view'
  const SCAN_TEST_REPOSITORY_VIEW = 'scan-test-repository-view'

  const [selectedUserFile, setSelectedUserFile] = React.useState('')
  const [validatedSelectedUserFiles, setValidatedSelectedUserFiles] = React.useState<Constants.validate>('error')

  const [repositoryUrl, setRepositoryUrl] = React.useState('')
  const [validatedRepositoryUrl, setValidatedRepositoryUrl] = React.useState<Constants.validate>('error')

  const [repositoryBranch, setRepositoryBranch] = React.useState('')
  const [validatedRepositoryBranch, setValidatedRepositoryBranch] = React.useState<Constants.validate>('error')

  const [userFiles, setUserFiles] = React.useState([])

  const isRowSelected = (_index) => selectedIndexes.includes(_index)

  const setRowSelected = (row: TestCase, isSelecting = true) =>
    setSelectedIndexes((prevSelected) => {
      const otherSelectedRows = prevSelected.filter((r) => r !== row.index)
      return isSelecting ? [...otherSelectedRows, row.index] : otherSelectedRows
    })

  const onSelectRow = (row: TestCase, rowIndex: number, isSelecting: boolean) => {
    // If the user is shift + selecting the checkboxes, then all intermediate checkboxes should be selected
    if (shifting && recentSelectedRowIndex !== null) {
      const numberSelected = rowIndex - recentSelectedRowIndex
      const intermediateIndexes =
        numberSelected > 0
          ? Array.from(new Array(numberSelected + 1), (_x, i) => i + recentSelectedRowIndex)
          : Array.from(new Array(Math.abs(numberSelected) + 1), (_x, i) => i + rowIndex)
      intermediateIndexes.forEach((index) => setRowSelected(workItems[index], isSelecting))
    } else {
      setRowSelected(row, isSelecting)
    }
    setRecentSelectedRowIndex(rowIndex)
    setMessageValue('')
  }

  const selectAllRows = (isSelecting = true) => setSelectedIndexes(isSelecting ? workItems.map((r) => r.index) : [])

  const handleSelectedUserFileChange = (event, value) => {
    setSelectedUserFile(value)
  }

  const handleRepositoryUrlChange = (event, value) => {
    setRepositoryUrl(value)
  }

  const handleRepositoryBranchChange = (event, value) => {
    setRepositoryBranch(value)
  }

  React.useEffect(() => {
    if (currentView == '') {
      setCurrentView(SELECT_USER_FILE_VIEW)
    }
    if (userFiles.length == 0) {
      Constants.loadUserFiles(auth, setUserFiles)
    }

    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Shift') {
        setShifting(true)
      }
    }
    const onKeyUp = (e: KeyboardEvent) => {
      if (e.key === 'Shift') {
        setShifting(false)
      }
    }
    document.addEventListener('keydown', onKeyDown)
    document.addEventListener('keyup', onKeyUp)

    return () => {
      document.removeEventListener('keydown', onKeyDown)
      document.removeEventListener('keyup', onKeyUp)
    }
  }, [])

  const columnNames = {
    id: 'ID',
    relative_path: 'Relative Path',
    title: 'Title',
    description: 'Description'
  }

  const resetForm = () => {
    setRepositoryUrl('')
    setRepositoryBranch('')
    setSelectedUserFile('')
    setWorkItems([])
    setSelectedIndexes([])
  }

  const handleLoadTestCaseSubmit = () => {
    if (validatedSelectedUserFiles != 'success') {
      setMessageValue('Please select a file from the list.')
      return
    }

    if (!auth.isLogged()) {
      setMessageValue(Constants.SESSION_EXPIRED_MESSAGE)
      return
    }

    setWorkItems([])

    const data = {
      file_name: selectedUserFile,
      'user-id': auth.userId,
      token: auth.token
    }

    let status
    let status_text

    fetch(importUrl, {
      method: 'POST',
      headers: Constants.JSON_HEADER,
      body: JSON.stringify(data)
    })
      .then((response) => {
        status = response.status
        status_text = response.statusText
        if (status !== 200) {
          return response.text()
        } else {
          return response.json()
        }
      })
      .then((data) => {
        if (status !== 200) {
          setMessageValue(Constants.getResponseErrorMessage(status, status_text, data))
        } else {
          const test_cases: TestCase[] = []
          for (let i = 0; i < data['test_cases'].length; i++) {
            const test_case: TestCase = {
              id: data['test_cases'][i].id,
              index: i,
              title: data['test_cases'][i].title,
              description: data['test_cases'][i].description,
              repository: data['test_cases'][i].repository,
              relative_path: data['test_cases'][i].relative_path
            }
            test_cases.push(test_case)
          }
          setWorkItems(test_cases)
          if (test_cases.length > 0) {
            setMessageValue('Data loaded')
          }
        }
      })
      .catch((err) => {
        console.log(err.message)
        setMessageValue(err.message)
        setWorkItems([])
      })
  }

  React.useEffect(() => {
    setMessageValue('')
    let isValid = true
    if (repositoryUrl.trim() == '') {
      setValidatedRepositoryUrl('error')
      isValid = false
    } else {
      if (!repositoryUrl.startsWith('http')) {
        setValidatedRepositoryUrl('error')
        isValid = false
      }
      if (!repositoryUrl.endsWith('.git')) {
        setValidatedRepositoryUrl('error')
        isValid = false
      }
    }
    if (isValid) {
      setValidatedRepositoryUrl('success')
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [repositoryUrl])

  React.useEffect(() => {
    setMessageValue('')
    if (repositoryBranch.trim() == '') {
      setValidatedRepositoryBranch('error')
    } else {
      setValidatedRepositoryBranch('success')
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [repositoryBranch])

  React.useEffect(() => {
    if (selectedUserFile == '') {
      setValidatedSelectedUserFiles('error')
    } else {
      setValidatedSelectedUserFiles('success')
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedUserFile])

  React.useEffect(() => {
    if (statusValue == 'submitted') {
      handleSubmit()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [statusValue])

  const handleSwComponentImplementationFileKeyUp = (event) => {
    if (event.key === 'Enter') {
      handleSubmit()
    }
  }

  const handleScanSubmit = () => {
    if (validatedRepositoryUrl != 'success') {
      setMessageValue('Repository url is mandatory.')
      return
    } else if (validatedRepositoryBranch != 'success') {
      setMessageValue('Repository branch is mandatory.')
      return
    }

    if (!auth.isLogged()) {
      setMessageValue(Constants.SESSION_EXPIRED_MESSAGE)
      return
    }

    setMessageValue('')

    const data = {
      repository: repositoryUrl,
      branch: repositoryBranch,
      'user-id': auth.userId,
      token: auth.token
    }

    let status
    let status_text

    fetch(generateJsonUrl, {
      method: 'POST',
      headers: Constants.JSON_HEADER,
      body: JSON.stringify(data)
    })
      .then((response) => {
        status = response.status
        status_text = response.statusText
        setStatusValue('waiting')
        if (status !== 200) {
          return response.text()
        } else {
          loadTestCases('')
          return response.json()
        }
      })
      .then((data) => {
        if (status !== 200) {
          setMessageValue(Constants.getResponseErrorMessage(status, status_text, data))
        } else {
          setMessageValue('Test Repository Scan requested. The process can take some time depending on the repository. Check your files!')
        }
      })
      .catch((err) => {
        setStatusValue('waiting')
        setMessageValue(err.toString())
      })
  }

  const handleSubmit = () => {
    if (selectedIndexes.length == 0) {
      setMessageValue('Please, select at least one row.')
      return
    }

    if (!auth.isLogged()) {
      setMessageValue(Constants.SESSION_EXPIRED_MESSAGE)
      return
    }

    const items: TestCase[] = []
    for (let i = 0; i < workItems.length; i++) {
      if (selectedIndexes.includes(workItems[i].index)) {
        items.push(workItems[i])
      }
    }

    setMessageValue('')

    const data = {
      items: items,
      'user-id': auth.userId,
      token: auth.token
    }

    fetch(importUrl, {
      method: 'PUT',
      headers: Constants.JSON_HEADER,
      body: JSON.stringify(data)
    })
      .then((response) => {
        if (response.status !== 200) {
          setMessageValue(response.statusText)
          setStatusValue('waiting')
        } else {
          setStatusValue('waiting')
          setMessageValue('Test Cases imported!')
        }
      })
      .catch((err) => {
        setStatusValue('waiting')
        setMessageValue(err.toString())
      })
  }

  return (
    <React.Fragment>
      <Flex direction={{ default: 'column' }} gap={{ default: 'gap2xl' }}>
        <Flex gap={{ default: 'gap2xl' }}>
          <FlexItem>
            <Button
              id={`btn-test-case-import-select-from-user-files`}
              variant='secondary'
              onClick={() => setCurrentView(SELECT_USER_FILE_VIEW)}
              isDisabled={currentView == SELECT_USER_FILE_VIEW}
            >
              Select from user files
            </Button>
          </FlexItem>
          <FlexItem>
            <Button
              id={`btn-test-case-import-scan-remote-repository`}
              variant='secondary'
              onClick={() => setCurrentView(SCAN_TEST_REPOSITORY_VIEW)}
              isDisabled={currentView == SCAN_TEST_REPOSITORY_VIEW}
            >
              Scan remote repository
            </Button>
          </FlexItem>
        </Flex>
        {currentView == SELECT_USER_FILE_VIEW ? (
          <Grid hasGutter>
            <GridItem span={6}>
              <FormSelect
                value={selectedUserFile}
                id={`select-test-case-import-from-user-files`}
                onChange={(event, value) => handleSelectedUserFileChange(event, value)}
                aria-label='User file for test case import'
              >
                <FormSelectOption key={0} value={''} label={'Select a file from the list'} />
                {userFiles.map((userFile, index) => (
                  <FormSelectOption key={index + 1} value={userFile['filepath']} label={userFile['filename']} />
                ))}
              </FormSelect>
            </GridItem>
            <GridItem span={4}>
              <Flex>
                <FlexItem>
                  <Button
                    id={`btn-test-case-import-refresh-user-files`}
                    variant='secondary'
                    onClick={() => Constants.loadUserFiles(auth, setUserFiles)}
                  >
                    Refresh Files List
                  </Button>
                </FlexItem>
                <FlexItem>
                  <Button
                    id={`btn-test-case-import-select-from-user-files-submit`}
                    variant='primary'
                    onClick={() => handleLoadTestCaseSubmit()}
                  >
                    Load Test Cases From File
                  </Button>
                </FlexItem>
              </Flex>
            </GridItem>
          </Grid>
        ) : (
          <Grid hasGutter span={4}>
            <GridItem>
              <TextInput
                isRequired
                placeholder='Test Repository Url'
                id={`input-test-case-import-repository-url`}
                value={repositoryUrl}
                onChange={(event, value) => handleRepositoryUrlChange(event, value)}
              />
              {validatedRepositoryUrl !== 'success' && (
                <FormHelperText>
                  <HelperText>
                    <HelperTextItem variant='error'>{validatedRepositoryUrl === 'error' ? 'This field is mandatory' : ''}</HelperTextItem>
                  </HelperText>
                </FormHelperText>
              )}
            </GridItem>
            <GridItem>
              <TextInput
                isRequired
                placeholder='Test Repository Branch'
                id={`input-test-case-import-repository-branch`}
                value={repositoryBranch}
                onChange={(event, value) => handleRepositoryBranchChange(event, value)}
              />
              {validatedRepositoryBranch !== 'success' && (
                <FormHelperText>
                  <HelperText>
                    <HelperTextItem variant='error'>
                      {validatedRepositoryBranch === 'error' ? 'This field is mandatory' : ''}
                    </HelperTextItem>
                  </HelperText>
                </FormHelperText>
              )}
            </GridItem>
            <GridItem>
              <Button id={`btn-test-case-import-scan-remote-repository-submit`} variant='primary' onClick={() => handleScanSubmit()}>
                Scan
              </Button>
            </GridItem>
          </Grid>
        )}
      </Flex>

      <br />
      <Divider></Divider>
      <br />

      {messageValue ? (
        <>
          <Hint>
            <HintBody>{messageValue}</HintBody>
          </Hint>
          <br />
        </>
      ) : (
        ''
      )}

      <div style={{ minHeight: '400px', overflowY: 'scroll' }}>
        {workItems.length > 0 ? (
          <Table id={`table-test-cases-import`} variant='compact' aria-label='Test Case import table'>
            <Thead>
              <Tr>
                <Th
                  select={{
                    onSelect: (_event, isSelecting) => selectAllRows(isSelecting),
                    isSelected: areAllRowsSelected
                  }}
                  aria-label='Row select'
                />
                <Th>{columnNames.id}</Th>
                <Th>{columnNames.relative_path}</Th>
                <Th>{columnNames.title}</Th>
                <Th>{columnNames.description}</Th>
              </Tr>
            </Thead>
            <Tbody>
              {workItems.map((workItem, rowIndex) => (
                <Tr key={rowIndex}>
                  <Td
                    select={{
                      rowIndex,
                      onSelect: (_event, isSelecting) => onSelectRow(workItem, rowIndex, isSelecting),
                      isSelected: isRowSelected(workItem.index)
                    }}
                  />
                  <Td dataLabel={columnNames.id}>{workItem.id}</Td>
                  <Td dataLabel={columnNames.id}>{workItem.relative_path}</Td>
                  <Td dataLabel={columnNames.title}>{workItem.title}</Td>
                  <Td dataLabel={columnNames.description}>{workItem.description}</Td>
                </Tr>
              ))}
            </Tbody>
          </Table>
        ) : (
          ''
        )}
      </div>

      <ActionGroup>
        <Flex>
          <FlexItem>
            <Button
              id='btn-test-case-import-submit'
              isDisabled={selectedIndexes.length == 0}
              variant='primary'
              onClick={() => setStatusValue('submitted')}
            >
              Submit
            </Button>
          </FlexItem>
        </Flex>
      </ActionGroup>
    </React.Fragment>
  )
}
