import * as React from 'react'
import * as Constants from '../../Constants/constants'
import {
  ActionGroup,
  Button,
  Flex,
  FlexItem,
  FormGroup,
  FormHelperText,
  HelperText,
  HelperTextItem,
  Hint,
  HintBody,
  TextInput
} from '@patternfly/react-core'
import { DataList, DataListCell, DataListItem, DataListItemCells, DataListItemRow, SearchInput } from '@patternfly/react-core'
import { useAuth } from '../../User/AuthProvider'

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
  const [searchValue, setSearchValue] = React.useState(formData?.title || '')
  const [messageValue, setMessageValue] = React.useState(formMessage)
  const [statusValue, setStatusValue] = React.useState('waiting')
  const [selectedDataListItemId, setSelectedDataListItemId] = React.useState('')
  const [initializedValue, setInitializedValue] = React.useState(false)
  const [coverageValue, setCoverageValue] = React.useState(formData?.coverage || 0)
  const [validatedCoverageValue, setValidatedCoverageValue] = React.useState<Constants.validate>('error')

  const resetForm = () => {
    setSelectedDataListItemId('')
    setCoverageValue('0')
    setSearchValue('')
  }

  React.useEffect(() => {
    if (coverageValue === '') {
      setValidatedCoverageValue('default')
    } else if (/^\d+$/.test(coverageValue)) {
      if (coverageValue >= 0 && coverageValue <= 100) {
        setValidatedCoverageValue('success')
      } else {
        setValidatedCoverageValue('error')
      }
    } else {
      setValidatedCoverageValue('error')
    }
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
    } else if (validatedCoverageValue != 'success') {
      setMessageValue('Coverage of Parent Item is mandatory and must be a integer value in the range 0-100.')
      setStatusValue('waiting')
      return
    } else if (modalSection.trim().length == 0) {
      setMessageValue('Section of the software component specification is mandatory.')
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

    fetch(Constants.API_BASE_URL + '/mapping/' + parentType + '/sw-requirements', {
      method: formVerb,
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
          setMessageValue('Database updated!')
          handleModalToggle()
          setMessageValue('')
          loadMappingData(Constants.force_reload)
        }
      })
      .catch((err) => {
        setStatusValue('waiting')
        setMessageValue(err.toString())
      })
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
      <FormGroup label='Unique Coverage:' isRequired fieldId={`input-sw-requirement-coverage-${formData?.id}`}>
        <TextInput
          isRequired
          id={`input-sw-requirement-coverage-${formData?.id}`}
          name={`input-sw-requirement-coverage-${formData?.id}`}
          value={coverageValue || ''}
          onChange={(_ev, value) => handleCoverageValueChange(_ev, value)}
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
          <Button id='btn-mapping-existing-sw-requirement-submit' variant='primary' onClick={() => setStatusValue('submitted')}>
            Submit
          </Button>
          <Button id='btn-mapping-existing-sw-requirement-cancel' variant='secondary' onClick={resetForm}>
            Reset
          </Button>
        </ActionGroup>
      ) : (
        <span></span>
      )}
    </React.Fragment>
  )
}
