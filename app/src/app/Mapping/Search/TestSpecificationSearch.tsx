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

export interface TestSpecificationSearchProps {
  api
  formDefaultButtons: number
  formVerb: string
  formData
  formMessage: string
  parentData
  parentType: string
  parentRelatedToType
  handleModalToggle
  modalIndirect
  modalOffset
  modalSection
  modalShowState
  loadMappingData
  loadTestSpecifications
  testSpecifications
}

export const TestSpecificationSearch: React.FunctionComponent<TestSpecificationSearchProps> = ({
  api,
  formDefaultButtons = 1,
  formVerb = 'POST',
  formData = { id: 0, title: '', preconditions: '', test_description: '', expected_behavior: '' },
  formMessage = '',
  parentData,
  parentType = '',
  parentRelatedToType,
  handleModalToggle,
  modalIndirect,
  modalOffset,
  modalSection,
  modalShowState,
  loadMappingData,
  loadTestSpecifications,
  testSpecifications
}: TestSpecificationSearchProps) => {
  const auth = useAuth()
  const [searchValue, setSearchValue] = React.useState<string>('')
  const [messageValue, setMessageValue] = React.useState(formMessage)
  const [statusValue, setStatusValue] = React.useState('waiting')
  const [selectedDataListItemId, setSelectedDataListItemId] = React.useState('')
  const [initializedValue, setInitializedValue] = React.useState(false)
  const [coverageValue, setCoverageValue] = React.useState(formData.coverage || 0)
  const [validatedCoverageValue, setValidatedCoverageValue] = React.useState('error')

  const resetForm = () => {
    setSelectedDataListItemId('')
    setCoverageValue(0)
    setSearchValue('')
  }

  React.useEffect(() => {
    Constants.validateCoverage(coverageValue, setValidatedCoverageValue)
  }, [coverageValue])

  const handleCoverageValueChange = (_event, value: string) => {
    setCoverageValue(value)
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

  const getTestSpecificationsTable = (test_specifications) => {
    return test_specifications.map((test_specification, tsIndex) => (
      <DataListItem
        key={test_specification.id}
        aria-labelledby={'clickable-action-item-' + test_specification.id}
        id={'list-existing-test-specification-item-' + test_specification.id}
        data-id={test_specification.id}
      >
        <DataListItemRow>
          <DataListItemCells
            dataListCells={[
              <DataListCell key={tsIndex}>
                <span id={'clickable-action-item-' + test_specification.id}>
                  {test_specification.id} - {test_specification.title}
                </span>
              </DataListCell>
            ]}
          />
        </DataListItemRow>
      </DataListItem>
    ))
  }

  React.useEffect(() => {
    if (modalShowState == true && initializedValue == false) {
      setInitializedValue(true)
      loadTestSpecifications(searchValue)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  React.useEffect(() => {
    if (statusValue == 'submitted') {
      handleSubmit()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [statusValue])

  const handleSubmit = () => {
    if (selectedDataListItemId == '' || selectedDataListItemId == '' || selectedDataListItemId == null) {
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
    const test_specification_id = document.getElementById(selectedDataListItemId)?.dataset?.id

    if (test_specification_id == null) {
      setMessageValue('Bad selection.')
      return
    }

    const data = {
      'api-id': api.id,
      'test-specification': { id: test_specification_id },
      'sw-requirement': {},
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

    if (modalIndirect == true) {
      data['relation-id'] = parentData.relation_id
      data['relation-to'] = parentRelatedToType
      data['sw-requirement']['id'] = parentData.sw_requirement.id
    }

    let status: number = 0
    let status_text: string = ''

    fetch(Constants.API_BASE_URL + '/mapping/' + parentType + '/test-specifications', {
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
        console.log(err.message)
      })
  }

  // Keyboard events
  const handleSearchKeyPress = (event) => {
    if (event.key === 'Enter') {
      setSelectedDataListItemId('')
      loadTestSpecifications(searchValue)
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
            onClear={() => onChangeSearchValue('')}
            onKeyUp={handleSearchKeyPress}
            style={{ width: '400px' }}
          />
        </FlexItem>
        <FlexItem>
          <Button
            variant='primary'
            aria-label='Action'
            onClick={() => {
              loadTestSpecifications(searchValue)
            }}
          >
            Search
          </Button>
        </FlexItem>
      </Flex>
      <br />
      <DataList
        isCompact
        id='list-existing-test-specifications'
        aria-label='clickable data list example'
        selectedDataListItemId={selectedDataListItemId}
        onSelectDataListItem={onSelectDataListItem}
        onSelectableRowChange={handleInputChange}
      >
        {getTestSpecificationsTable(testSpecifications)}
      </DataList>
      <br />
      <Grid hasGutter md={4}>
        <FormGroup label={Constants.FORM_COMPLETION_LABEL} isRequired fieldId={`input-test-specification-coverage-existing`}>
          <TextInput
            isRequired
            id={`input-test-specification-coverage-existing`}
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
              <Button id='btn-mapping-existing-test-specification-submit' variant='primary' onClick={() => setStatusValue('submitted')}>
                Submit
              </Button>
            </FlexItem>
            <FlexItem>
              <Button id='btn-mapping-existing-test-specification-cancel' variant='secondary' onClick={resetForm}>
                Reset
              </Button>
            </FlexItem>
          </Flex>
        </ActionGroup>
      ) : (
        <span></span>
      )}
    </React.Fragment>
  )
}
