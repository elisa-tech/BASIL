import * as React from 'react'
import * as XLSX from 'xlsx'
import * as Constants from '@app/Constants/constants'
import { ActionGroup, Button, FileUpload, Flex, FlexItem, Hint, HintBody } from '@patternfly/react-core'
import { Table, Tbody, Td, Th, Thead, Tr } from '@patternfly/react-table'
import { useAuth } from '@app/User/AuthProvider'

interface SwRequirement {
  id: string
  index: number
  title: string
  description: string
}

export interface SwRequirementImportProps {
  loadSwRequirements
}

export const SwRequirementImport: React.FunctionComponent<SwRequirementImportProps> = ({
  loadSwRequirements
}: SwRequirementImportProps) => {
  const auth = useAuth()
  const importUrl = Constants.API_BASE_URL + '/import/sw-requirements'
  const [messageValue, setMessageValue] = React.useState('')
  const [statusValue, setStatusValue] = React.useState('waiting')

  // Table
  const [workItems, setWorkItems] = React.useState<SwRequirement[]>([])

  const [selectedIndexes, setSelectedIndexes] = React.useState<number[]>([])
  const areAllRowsSelected = selectedIndexes.length === workItems.length
  const [shifting, setShifting] = React.useState(false)
  const [recentSelectedRowIndex, setRecentSelectedRowIndex] = React.useState<number | null>(null)
  const isRowSelected = (_index) => selectedIndexes.includes(_index)

  const setRowSelected = (row: SwRequirement, isSelecting = true) =>
    setSelectedIndexes((prevSelected) => {
      const otherSelectedRows = prevSelected.filter((r) => r !== row.index)
      return isSelecting ? [...otherSelectedRows, row.index] : otherSelectedRows
    })

  const onSelectRow = (row: SwRequirement, rowIndex: number, isSelecting: boolean) => {
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

  React.useEffect(() => {
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

  // File Upload
  const [fileContent, setFileContent] = React.useState<string>('')
  const [fileName, setFileName] = React.useState('')

  const readTextFile = (file: File) => {
    const reader = new FileReader()
    reader.onload = () => {
      if (typeof reader.result === 'string') {
        setFileContent(reader.result)
      }
    }
    reader.readAsText(file)
  }

  const readXlsxFile = (file: File) => {
    const reader = new FileReader()

    reader.onload = (event) => {
      const workbook = XLSX.read(event.target?.result, { type: 'binary' })
      const sheetName = workbook.SheetNames[0]
      const sheet = workbook.Sheets[sheetName]
      const sheetData = XLSX.utils.sheet_to_json(sheet)
      setFileContent(JSON.stringify(sheetData))
    }
    reader.readAsArrayBuffer(file)
  }

  const handleFileInputChange = (_, file: File) => {
    setSelectedIndexes([])
    setFileName(file.name)
    if (file.name.endsWith('xlsx')) {
      readXlsxFile(file)
    } else {
      readTextFile(file)
    }
  }

  const handleClear = () => {
    setFileName('')
    setFileContent('')
    setSelectedIndexes([])
    setMessageValue('Data erased')
  }

  const columnNames = {
    id: 'ID',
    title: 'Title',
    description: 'Description'
  }

  const resetForm = () => {
    setFileName('')
    setFileContent('')
    setWorkItems([])
    setSelectedIndexes([])
  }

  React.useEffect(() => {
    if (fileContent) {
      if (fileContent.length > 0) {
        getWorkItemsList()
      }
    }
  }, [fileContent])

  const getWorkItemsList = () => {
    const data = {
      file_name: fileName,
      file_content: fileContent
    }
    fetch(importUrl, {
      method: 'POST',
      headers: Constants.JSON_HEADER,
      body: JSON.stringify(data)
    })
      .then((res) => {
        if (!res.ok) {
          setMessageValue('Error loading data')
          setWorkItems([])
          return {}
        } else {
          return res.json()
        }
      })
      .then((data) => {
        const reqs: SwRequirement[] = []
        for (let i = 0; i < data['sw_requirements'].length; i++) {
          const req: SwRequirement = {
            id: data['sw_requirements'][i].id,
            index: i,
            title: data['sw_requirements'][i].title,
            description: data['sw_requirements'][i].description
          }
          reqs.push(req)
        }
        setWorkItems(reqs)
        if (reqs.length > 0) {
          setMessageValue('Data loaded')
        }
      })
      .catch((err) => {
        console.log(err.message)
        setMessageValue(err.message)
        setWorkItems([])
      })
  }

  React.useEffect(() => {
    if (statusValue == 'submitted') {
      handleSubmit()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [statusValue])

  const handleSubmit = () => {
    if (selectedIndexes.length == 0) {
      setMessageValue('Please, select at least one row.')
      return
    }

    const items: SwRequirement[] = []
    for (let i = 0; i < workItems.length; i++) {
      if (selectedIndexes.includes(workItems[i].index)) {
        items.push(workItems[i])
      }
    }

    setMessageValue('')

    const data = {
      file_content: fileContent,
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
          setMessageValue('Requirements imported!')
          loadSwRequirements('')
          resetForm()
        }
      })
      .catch((err) => {
        setStatusValue('waiting')
        setMessageValue(err.toString())
      })
  }

  return (
    <React.Fragment>
      <FileUpload
        id='sw-requirement-spdx-file-upload'
        hideDefaultPreview={true}
        value={fileContent}
        filename={fileName}
        filenamePlaceholder='Drag and drop a file or upload one'
        onFileInputChange={handleFileInputChange}
        onClearClick={handleClear}
        allowEditingUploadedText={false}
        browseButtonText='Upload'
      />
      <br />
      <div style={{ minHeight: '400px', overflowY: 'scroll' }}>
        {fileContent && (
          <Table aria-label='Selectable table'>
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
                  <Td dataLabel={columnNames.title}>{workItem.title}</Td>
                  <Td dataLabel={columnNames.description}>{workItem.description}</Td>
                </Tr>
              ))}
            </Tbody>
          </Table>
        )}
      </div>
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

      <ActionGroup>
        <Flex>
          <FlexItem>
            <Button id='btn-mapping-existing-sw-requirement-submit' variant='primary' onClick={() => setStatusValue('submitted')}>
              Submit
            </Button>
          </FlexItem>
          <FlexItem>
            <Button id='btn-mapping-existing-sw-requirement-cancel' variant='secondary' onClick={resetForm}>
              Reset
            </Button>
          </FlexItem>
        </Flex>
      </ActionGroup>
    </React.Fragment>
  )
}
