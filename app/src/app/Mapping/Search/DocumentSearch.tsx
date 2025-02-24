import React from 'react'
import * as Constants from '@app/Constants/constants'
import {
  ActionGroup,
  Button,
  Flex,
  FlexItem,
  FormGroup,
  FormHelperText,
  Grid,
  HelperText,
  HelperTextItem,
  Hint,
  HintBody,
  TextInput
} from '@patternfly/react-core'
import { DataList, DataListCell, DataListItem, DataListItemCells, DataListItemRow, SearchInput } from '@patternfly/react-core'
import { useAuth } from '@app/User/AuthProvider'

export interface DocumentSearchProps {
  api
  formDefaultButtons: number
  formVerb: string
  formData
  formMessage: string
  handleModalToggle
  documents
  modalOffset
  modalSection
  modalShowState
  loadDocuments
  loadMappingData
}

export const DocumentSearch: React.FunctionComponent<DocumentSearchProps> = ({
  api,
  formDefaultButtons = 1,
  formVerb = 'POST',
  formData = { id: 0, description: '' },
  formMessage = '',
  handleModalToggle,
  documents,
  modalOffset,
  modalSection,
  modalShowState,
  loadDocuments,
  loadMappingData
}: DocumentSearchProps) => {
  const auth = useAuth()
  const [searchValue, setSearchValue] = React.useState<string>('')
  const [messageValue, setMessageValue] = React.useState(formMessage)
  const [statusValue, setStatusValue] = React.useState('waiting')
  const [selectedDataListItemId, setSelectedDataListItemId] = React.useState<string>('')
  const [initializedValue, setInitializedValue] = React.useState(false)
  const [coverageValue, setCoverageValue] = React.useState(formData?.coverage || 0)
  const [validatedCoverageValue, setValidatedCoverageValue] = React.useState<Constants.validate>('error')

  const resetForm = () => {
    setSelectedDataListItemId('')
    setCoverageValue('0')
    setSearchValue('')
  }

  const onChangeSearchValue = (value) => {
    setSearchValue(value)
  }

  const onSelectDataListItem = (_event: React.MouseEvent | React.KeyboardEvent, id: string) => {
    setSelectedDataListItemId(id)
  }

  const handleInputChange = (_event: React.FormEvent<HTMLInputElement>, id: string) => {
    setSelectedDataListItemId(id)
  }

  React.useEffect(() => {
    Constants.validateCoverage(coverageValue, setValidatedCoverageValue)
  }, [coverageValue])

  const handleCoverageValueChange = (_event, value: string) => {
    setCoverageValue(value)
  }

  React.useEffect(() => {
    if (statusValue == 'submitted') {
      handleSubmit()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [statusValue])

  React.useEffect(() => {
    if (modalShowState == true && initializedValue == false) {
      setInitializedValue(true)
      loadDocuments(searchValue)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const getDocumentsTable = (documents) => {
    return documents.map((curr_document, jIndex) => (
      <DataListItem
        key={curr_document.id}
        aria-labelledby={'clickable-action-item-' + curr_document.id}
        id={'list-existing-document-item-' + curr_document.id}
        data-id={curr_document.id}
      >
        <DataListItemRow>
          <DataListItemCells
            dataListCells={[
              <DataListCell key={jIndex}>
                <span id={'clickable-action-item-' + curr_document.id}>
                  {curr_document.id} - {curr_document.title} - {curr_document.document_type} - {curr_document.spdx_relation}
                </span>
              </DataListCell>
            ]}
          />
        </DataListItemRow>
      </DataListItem>
    ))
  }

  const handleSubmit = () => {
    if (selectedDataListItemId == '' || selectedDataListItemId == null) {
      setMessageValue('Please, select an item before submitting the form.')
      setStatusValue('waiting')
      return
    }
    if (validatedCoverageValue != 'success') {
      setMessageValue('Coverage of Parent Item is mandatory and must be a integer value in the range 0-100.')
      setStatusValue('waiting')
      return
    }
    if (modalSection.trim().length == 0) {
      setMessageValue(Constants.UNVALID_REF_DOCUMENT_SECTION_MESSAGE)
      setStatusValue('waiting')
      return
    }

    setMessageValue('')
    const document_id = document.getElementById(selectedDataListItemId)?.dataset?.id

    if (document_id == null) {
      setMessageValue('Bad selection.')
      return
    }

    const data = {
      'api-id': api.id,
      document: { id: document_id },
      section: modalSection,
      offset: modalOffset,
      coverage: coverageValue,
      'user-id': auth.userId,
      token: auth.token
    }

    if (formVerb == 'PUT' || formVerb == 'DELETE') {
      setMessageValue('Wrong actions.')
      setStatusValue('waiting')
      return
    }

    let status: number = 0
    let status_text: string = ''

    fetch(Constants.API_BASE_URL + '/mapping/api/documents', {
      method: formVerb,
      headers: Constants.JSON_HEADER,
      body: JSON.stringify(data)
    })
      .then((response) => {
        status = response.status
        status_text = response.statusText
        if (status !== 200) {
          setStatusValue('waiting')
          return response.text()
        } else {
          setStatusValue('waiting')
          setMessageValue('Database updated!')
          handleModalToggle()
          setMessageValue('')
          loadMappingData(Constants.force_reload)
          return {}
        }
      })
      .then((data) => {
        if (status != 200) {
          setMessageValue(Constants.getResponseErrorMessage(status, status_text, data))
        }
      })
      .catch((err) => {
        setStatusValue('waiting')
        setMessageValue(err.toString())
      })
  }

  // Keyboard events
  const handleSearchKeyPress = (event) => {
    if (event.key === 'Enter') {
      setSelectedDataListItemId('')
      loadDocuments(searchValue)
    }
  }

  const handleCoverageKeyPress = (event) => {
    if (event.key === 'Enter') {
      handleSubmit()
    }
  }

  return (
    <React.Fragment>
      <Flex>
        <FlexItem>
          <SearchInput
            placeholder='Search Identifier'
            value={searchValue}
            onChange={(_event, value) => onChangeSearchValue(value)}
            onKeyUp={handleSearchKeyPress}
            onClear={() => onChangeSearchValue('')}
            style={{ width: '400px' }}
          />
        </FlexItem>
        <FlexItem>
          <Button
            variant='primary'
            aria-label='Action'
            onClick={() => {
              loadDocuments(searchValue)
            }}
          >
            Search
          </Button>
        </FlexItem>
      </Flex>
      <br />
      <DataList
        isCompact
        id='list-existing-documents'
        aria-label='clickable data list example'
        selectedDataListItemId={selectedDataListItemId}
        onSelectDataListItem={onSelectDataListItem}
        onSelectableRowChange={handleInputChange}
      >
        {getDocumentsTable(documents)}
      </DataList>
      <br />
      <Grid hasGutter md={3}>
        <FormGroup label='Unique Coverage:' isRequired fieldId={`input-document-coverage-${formData?.id}`}>
          <TextInput
            isRequired
            id={`input-document-coverage-${formData?.id}`}
            value={coverageValue}
            onChange={(_ev, value) => handleCoverageValueChange(_ev, value)}
            onKeyUp={handleCoverageKeyPress}
          />
          {validatedCoverageValue !== 'success' && (
            <FormHelperText>
              <HelperText>
                <HelperTextItem variant='error'>
                  {validatedCoverageValue === 'error' ? 'Must be an integer number in the range 0-100' : ''}
                </HelperTextItem>
              </HelperText>
            </FormHelperText>
          )}
        </FormGroup>
      </Grid>
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

      {formDefaultButtons ? (
        <ActionGroup>
          <Flex>
            <FlexItem>
              <Button id='btn-mapping-existing-document-submit' variant='primary' onClick={() => setStatusValue('submitted')}>
                Submit
              </Button>
            </FlexItem>
            <FlexItem>
              <Button id='btn-mapping-existing-document-cancel' variant='secondary' onClick={resetForm}>
                Reset
              </Button>
            </FlexItem>
          </Flex>
        </ActionGroup>
      ) : (
        ''
      )}
    </React.Fragment>
  )
}
