import * as React from 'react'
import * as Constants from '../../Constants/constants'
import { DropEvent, FileUpload } from '@patternfly/react-core'
import { ActionGroup, Button, Hint, HintBody } from '@patternfly/react-core'
import { Table, Tbody, Td, Th, Thead, Tr } from '@patternfly/react-table'
import { useAuth } from '../../User/AuthProvider'

interface SwRequirement {
  id: string
  title: string
  description: string
}

export const SwRequirementImport: React.FunctionComponent = () => {
  const auth = useAuth()
  const importUrl = Constants.API_BASE_URL + '/import/sw-requirements'
  const [messageValue, setMessageValue] = React.useState('')
  const [statusValue, setStatusValue] = React.useState('waiting')

  // Table
  const [SwRequirements, setSwRequirements] = React.useState<SwRequirement[]>([])

  const [selectedRowsIds, setSelectedRowsIds] = React.useState<string[]>([])
  const areAllRowsSelected = selectedRowsIds.length === SwRequirements.length
  const [shifting, setShifting] = React.useState(false)
  const [recentSelectedRowIndex, setRecentSelectedRowIndex] = React.useState<number | null>(null)
  const isRowSelected = (id) => selectedRowsIds.includes(id)

  const setRowSelected = (row: SwRequirement, isSelecting = true) =>
    setSelectedRowsIds((prevSelected) => {
      const otherSelectedRowsIds = prevSelected.filter((r) => r !== row.id)
      return isSelecting ? [...otherSelectedRowsIds, row.id] : otherSelectedRowsIds
    })

  const onSelectRow = (row: SwRequirement, rowIndex: number, isSelecting: boolean) => {
    // If the user is shift + selecting the checkboxes, then all intermediate checkboxes should be selected
    if (shifting && recentSelectedRowIndex !== null) {
      const numberSelected = rowIndex - recentSelectedRowIndex
      const intermediateIndexes =
        numberSelected > 0
          ? Array.from(new Array(numberSelected + 1), (_x, i) => i + recentSelectedRowIndex)
          : Array.from(new Array(Math.abs(numberSelected) + 1), (_x, i) => i + rowIndex)
      intermediateIndexes.forEach((index) => setRowSelected(SwRequirements[index], isSelecting))
    } else {
      setRowSelected(row, isSelecting)
    }
    setRecentSelectedRowIndex(rowIndex)
    setMessageValue('')
  }

  const selectAllRows = (isSelecting = true) => setSelectedRowsIds(isSelecting ? SwRequirements.map((r) => r.id) : [])

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
  const [fileContent, setFileContent] = React.useState('')
  const [fileName, setFileName] = React.useState('')
  const [isLoading, setIsLoading] = React.useState(false)

  const handleFileInputChange = (_, file: File) => {
    setFileName(file.name)
  }

  const handleTextChange = (_event: React.ChangeEvent<HTMLTextAreaElement>, value: string) => {
    setFileContent(value)
  }

  const handleDataChange = (_event: DropEvent, value: string) => {
    setFileContent(value)
  }

  const handleClear = () => {
    setFileName('')
    setFileContent('')
    setMessageValue('Data erased')
  }

  const handleFileReadStarted = () => {
    setIsLoading(true)
  }

  const handleFileReadFinished = () => {
    setIsLoading(false)
  }

  const columnNames = {
    id: 'ID',
    title: 'Title',
    description: 'Description'
  }

  const resetForm = () => {
    setFileName('')
    setFileContent('')
    setSwRequirements([])
    setSelectedRowsIds([])
  }

  React.useEffect(() => {
    console.log(fileContent)
    if (fileContent?.length > 0) {
      getSwRequirementsList()
    }
  }, [fileContent])

  const getSwRequirementsList = () => {
    const data = { file_content: fileContent }
    fetch(importUrl, {
      method: 'POST',
      headers: {
        Accept: 'application/json',
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(data)
    })
      .then((res) => {
        if (!res.ok) {
          setMessageValue('Error loading data')
          setSwRequirements([])
          return {}
        } else {
          return res.json()
        }
      })
      .then((data) => {
        const reqs: SwRequirement[] = []
        for (let i = 0; i < data.length; i++) {
          const req: SwRequirement = {
            id: data[i].id,
            title: data[i].title,
            description: data[i].description
          }
          reqs.push(req)
        }
        setSwRequirements(reqs)
        if (setSwRequirements.length > 0) {
          setMessageValue('Data loaded')
        }
      })
      .catch((err) => {
        console.log(err.message)
        setMessageValue(err.message)
        setSwRequirements([])
      })
  }

  React.useEffect(() => {
    if (statusValue == 'submitted') {
      handleSubmit()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [statusValue])

  const handleSubmit = () => {
    if (selectedRowsIds.length == 0) {
      setMessageValue('Please, select at least one row.')
      return
    }

    setMessageValue('')

    const data = {
      file_content: fileContent,
      filter_ids: selectedRowsIds.join(','),
      'user-id': auth.userId,
      token: auth.token
    }

    fetch(importUrl, {
      method: 'PUT',
      headers: {
        Accept: 'application/json',
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(data)
    })
      .then((response) => {
        if (response.status !== 200) {
          setMessageValue(response.statusText)
          setStatusValue('waiting')
        } else {
          setStatusValue('waiting')
          setMessageValue('Requirements imported!')
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
        type='text'
        hideDefaultPreview={true}
        value={fileContent}
        filename={fileName}
        filenamePlaceholder='Drag and drop a file or upload one'
        onFileInputChange={handleFileInputChange}
        onDataChange={handleDataChange}
        onTextChange={handleTextChange}
        onReadStarted={handleFileReadStarted}
        onReadFinished={handleFileReadFinished}
        onClearClick={handleClear}
        isLoading={isLoading}
        allowEditingUploadedText={false}
        browseButtonText='Upload'
      />
      <br />
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
            {SwRequirements.map((sw_requirement, rowIndex) => (
              <Tr key={rowIndex}>
                <Td
                  select={{
                    rowIndex,
                    onSelect: (_event, isSelecting) => onSelectRow(sw_requirement, rowIndex, isSelecting),
                    isSelected: isRowSelected(sw_requirement.id)
                  }}
                />
                <Td dataLabel={columnNames.id}>{sw_requirement.id}</Td>
                <Td dataLabel={columnNames.title}>{sw_requirement.title}</Td>
                <Td dataLabel={columnNames.description}>{sw_requirement.description}</Td>
              </Tr>
            ))}
          </Tbody>
        </Table>
      )}
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
        <Button id='btn-mapping-existing-sw-requirement-submit' variant='primary' onClick={() => setStatusValue('submitted')}>
          Submit
        </Button>
        <Button id='btn-mapping-existing-sw-requirement-cancel' variant='secondary' onClick={resetForm}>
          Reset
        </Button>
      </ActionGroup>
    </React.Fragment>
  )
}
