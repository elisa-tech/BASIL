import * as React from 'react'
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

export interface SwRequirementSearchProps {
  api
  formDefaultButtons: number
  formVerb: string
  formData
  formMessage: string
  handleModalToggle
  modalIndirect
  modalOffset
  modalSection
  modalShowState
  loadMappingData
  loadSwRequirements
  parentData
  parentType
  parentRelatedToType
  swRequirements
}

export const SwRequirementSearch: React.FunctionComponent<SwRequirementSearchProps> = ({
  api,
  formDefaultButtons = 1,
  formVerb = 'POST',
  formData = { id: 0, title: '', description: '' },
  formMessage = '',
  handleModalToggle,
  modalIndirect,
  modalOffset,
  modalSection,
  modalShowState,
  loadMappingData,
  loadSwRequirements,
  parentData,
  parentType,
  parentRelatedToType,
  swRequirements
}: SwRequirementSearchProps) => {
  const auth = useAuth()
  const [searchValue, setSearchValue] = React.useState<string>('')
  const [messageValue, setMessageValue] = React.useState(formMessage)
  const [statusValue, setStatusValue] = React.useState('waiting')
  const [selectedDataListItemId, setSelectedDataListItemId] = React.useState('')
  const [initializedValue, setInitializedValue] = React.useState(false)
  const [coverageValue, setCoverageValue] = React.useState(formData?.coverage || 0)
  const [validatedCoverageValue, setValidatedCoverageValue] = React.useState<Constants.validate>('error')

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

  React.useEffect(() => {
    if (statusValue == 'submitted') {
      handleSubmit()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [statusValue])

  React.useEffect(() => {
    if (modalShowState == true && initializedValue == false) {
      setInitializedValue(true)
      loadSwRequirements(searchValue)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const getSwRequirementsTable = (sw_requirements) => {
    return sw_requirements.map((sw_requirement, srIndex) => (
      <DataListItem
        key={sw_requirement.id}
        aria-labelledby={'clickable-action-item-' + sw_requirement.id}
        id={'list-existing-sw-requirement-item-' + sw_requirement.id}
        data-id={sw_requirement.id}
      >
        <DataListItemRow>
          <DataListItemCells
            dataListCells={[
              <DataListCell key={srIndex}>
                <span id={'clickable-action-item-' + sw_requirement.id}>
                  {sw_requirement.id} - {sw_requirement.title}
                </span>
              </DataListCell>
            ]}
          />
        </DataListItemRow>
      </DataListItem>
    ))
  }

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

    const sw_requirement_id = document.getElementById(selectedDataListItemId)?.dataset?.id

    if (sw_requirement_id == null) {
      setMessageValue('Bad selection.')
      return
    }

    const data = {
      'sw-requirement': { id: sw_requirement_id },
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
      data['parent-sw-requirement'] = { id: parentData[Constants._SR_]['id'] }
    } else {
      data['api-id'] = api.id
    }

    let status: number = 0
    let status_text: string = ''

    fetch(Constants.API_BASE_URL + '/mapping/' + parentType + '/sw-requirements', {
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
      loadSwRequirements(searchValue)
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
            id={`input-search-sw-requirement-existing`}
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
              loadSwRequirements(searchValue)
            }}
          >
            Search
          </Button>
        </FlexItem>
      </Flex>
      <br />
      <DataList
        isCompact
        id='list-existing-sw-requirements'
        aria-label='clickable data list example'
        selectedDataListItemId={selectedDataListItemId}
        onSelectDataListItem={onSelectDataListItem}
        onSelectableRowChange={handleInputChange}
      >
        {getSwRequirementsTable(swRequirements)}
      </DataList>
      <br />
      <Grid hasGutter md={3}>
        <FormGroup label='Unique Coverage:' isRequired fieldId={`input-sw-requirement-coverage-existing`}>
          <TextInput
            isRequired
            id={`input-sw-requirement-coverage-existing`}
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
      ) : (
        <span></span>
      )}
    </React.Fragment>
  )
}
