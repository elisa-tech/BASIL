import React from 'react'
import * as Constants from '@app/Constants/constants'
import {
  ActionGroup,
  Button,
  Form,
  FormGroup,
  FormHelperText,
  FormSelect,
  FormSelectOption,
  Flex,
  FlexItem,
  Grid,
  HelperText,
  HelperTextItem,
  Hint,
  HintBody,
  TextArea,
  TextInput
} from '@patternfly/react-core'
import { useAuth } from '@app/User/AuthProvider'

export interface SwRequirementFormProps {
  api
  formAction: string
  formData
  formDefaultButtons: number
  formMessage: string
  formVerb: string
  handleModalToggle
  loadMappingData
  modalFormSubmitState: string
  modalIndirect
  modalOffset
  modalSection
  parentData
  parentRelatedToType
  parentType
}

export const SwRequirementForm: React.FunctionComponent<SwRequirementFormProps> = ({
  api,
  formAction = 'add',
  formData = { id: 0, coverage: '0', title: '', description: '' },
  formDefaultButtons = 1,
  formMessage = '',
  formVerb = 'POST',
  handleModalToggle,
  loadMappingData,
  modalFormSubmitState = 'waiting',
  modalIndirect,
  modalOffset,
  modalSection,
  parentData,
  parentRelatedToType,
  parentType
}: SwRequirementFormProps) => {
  const auth = useAuth()

  const [titleValue, setTitleValue] = React.useState(formData.title)
  const [validatedTitleValue, setValidatedTitleValue] = React.useState<Constants.validate>('error')

  const [descriptionValue, setDescriptionValue] = React.useState(formData.description)
  const [validatedDescriptionValue, setValidatedDescriptionValue] = React.useState<Constants.validate>('error')

  const [coverageValue, setCoverageValue] = React.useState(formData.coverage != '' ? formData.coverage : '0')
  const [validatedCoverageValue, setValidatedCoverageValue] = React.useState<Constants.validate>('error')

  const [swRequirementStatusValue, setSwRequirementStatusValue] = React.useState(formData.status)

  const [reasoningValue, setReasoningValue] = React.useState<string | undefined>()

  const [messageValue, setMessageValue] = React.useState(formMessage)
  const [statusValue, setStatusValue] = React.useState('waiting')

  const [isAIAvailable, setIsAIAvailable] = React.useState(false)
  const [isAskAIMetadataButtonEnabled, setIsAskAIMetadataButtonEnabled] = React.useState(true)
  const [askAIMetadataButtonText, setAskAIMetadataButtonText] = React.useState<string>('Ask AI for suggestion')

  // Form constants
  const INPUT_BASE_NAME = 'input-sw-requirement'
  const SELECT_BASE_NAME = 'select-sw-requirement'

  React.useEffect(() => {
    Constants.checkEndpoint(Constants.API_BASE_URL + Constants.API_AI_HEALTH_CHECK_ENDPOINT, setIsAIAvailable)
  }, [Constants.API_AI_HEALTH_CHECK_ENDPOINT])

  const resetForm = () => {
    setTitleValue('')
    setDescriptionValue('')
    setCoverageValue('0')
    setMessageValue('')
  }

  React.useEffect(() => {
    if (titleValue == undefined) {
      setTitleValue('')
    } else {
      if (titleValue.trim() === '') {
        setValidatedTitleValue('error')
      } else {
        setValidatedTitleValue('success')
      }
    }
  }, [titleValue])

  React.useEffect(() => {
    if (descriptionValue == undefined) {
      setDescriptionValue('')
    } else {
      if (descriptionValue.trim() === '') {
        setValidatedDescriptionValue('error')
      } else {
        setValidatedDescriptionValue('success')
      }
    }
  }, [descriptionValue])

  React.useEffect(() => {
    Constants.validateCoverage(coverageValue, setValidatedCoverageValue)
  }, [coverageValue])

  React.useEffect(() => {
    if (statusValue == 'submitted') {
      handleSubmit()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [statusValue])

  React.useEffect(() => {
    if (modalFormSubmitState == 'submitted') {
      handleSubmit()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [modalFormSubmitState])

  const handleTitleValueChange = (_event, value: string) => {
    setTitleValue(value)
  }

  const handleDescriptionValueChange = (_event, value: string) => {
    setDescriptionValue(value)
  }

  const handleCoverageValueChange = (_event, value: string) => {
    setCoverageValue(value)
  }

  const handleSwRequirementStatusChange = (_event, value: string) => {
    setSwRequirementStatusValue(value)
  }

  const handleSubmit = () => {
    if (validatedTitleValue != 'success') {
      setMessageValue('Sw Requirement Title is mandatory.')
      setStatusValue('waiting')
      focusInputTitle()
      return
    } else if (validatedDescriptionValue != 'success') {
      setMessageValue('Sw Requirement Description is mandatory.')
      setStatusValue('waiting')
      focusInputDescription()
      return
    } else if (validatedCoverageValue != 'success') {
      setMessageValue('Sw Requirement Coverage of Parent Item is mandatory and must be a integer value in the range 0-100.')
      setStatusValue('waiting')
      focusInputCoverage()
      return
    } else if (modalSection.trim().length == 0) {
      setMessageValue(Constants.UNVALID_REF_DOCUMENT_SECTION_MESSAGE)
      setStatusValue('waiting')
      return
    }

    setMessageValue('')

    const data = {
      'api-id': api.id,
      'sw-requirement': { title: titleValue, description: descriptionValue },
      section: modalSection,
      offset: modalOffset,
      coverage: coverageValue,
      'user-id': auth.userId,
      token: auth.token
    }

    if (modalIndirect == true) {
      data['relation-id'] = parentData.relation_id
      data['relation-to'] = parentRelatedToType
      data['parent-sw-requirement'] = { id: parentData[Constants._SR_]['id'] }
    } else {
      if (formVerb == 'PUT' || formVerb == 'DELETE') {
        data[Constants._SR]['id'] = formData.id
        data['relation-id'] = parentData.relation_id
      }
    }

    if (formVerb == 'PUT') {
      data[Constants._SR]['status'] = swRequirementStatusValue
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
        setMessageValue(err.toString())
        setStatusValue('waiting')
      })
  }

  // Form elements focus
  const focusInputTitle = () => {
    document.getElementById(INPUT_BASE_NAME + '-' + formAction + '-title-' + formData.id)?.focus()
  }

  const focusInputDescription = () => {
    document.getElementById(INPUT_BASE_NAME + '-' + formAction + '-description-' + formData.id)?.focus()
  }

  const focusInputCoverage = () => {
    document.getElementById(INPUT_BASE_NAME + '-' + formAction + '-coverage-' + formData.id)?.focus()
  }

  // Keyboard events
  const handleStatusKeyUp = (event) => {
    if (event.key === 'Enter') {
      focusInputTitle()
    }
  }

  const handleTitleKeyUp = (event) => {
    if (event.key === 'Enter') {
      focusInputDescription()
    }
  }

  const handleDescriptionKeyUp = (event) => {
    if (event.key === 'Enter' && event.shiftKey) {
      focusInputCoverage()
    }
  }

  const handleCoverageKeyUp = (event) => {
    if (event.key === 'Enter') {
      handleSubmit()
    }
  }

  const handleAskAIMetadataClick = () => {
    if (!isAskAIMetadataButtonEnabled) return
    resetForm()
    setIsAskAIMetadataButtonEnabled(false)
    setAskAIMetadataButtonText('Elaborating ...')
    askAiForMetadataSuggestion()
  }

  const askAiForMetadataSuggestion = () => {
    let spec = ''

    if (modalIndirect == true || formVerb == 'PUT') {
      if (parentType == Constants._SR) {
        spec = parentData.sw_requirement.description
      } else {
        spec = parentData.section
      }
    } else {
      spec = modalSection
    }

    let status
    let status_text

    const data = {
      'api-id': api.id,
      spec: spec,
      'user-id': auth.userId,
      token: auth.token
    }

    fetch(Constants.API_BASE_URL + Constants.API_AI_SUGGEST_SW_REQ_METADATA_ENDPOINT, {
      method: 'POST',
      headers: Constants.JSON_HEADER,
      body: JSON.stringify(data)
    })
      .then((response) => {
        status = response.status
        status_text = response.statusText
        if (status !== 200) {
          setStatusValue('Unable to get suggestions for this specification.')
          return {}
        } else {
          setStatusValue('waiting')
          setMessageValue('')
          return response.json()
        }
      })
      .then((data) => {
        if (status != 200) {
          setMessageValue(Constants.getResponseErrorMessage(status, status_text, data))
        } else {
          if ('title' in data && typeof data.title === 'string') {
            setTitleValue(data.title)
          }

          if ('description' in data && typeof data.description === 'string') {
            setDescriptionValue(data.description)
          }

          if ('completeness' in data) {
            setCoverageValue(data.completeness)
          }

          if ('reasoning' in data && typeof data.reasoning === 'string') {
            setReasoningValue(data.reasoning)
            setMessageValue('AI reasoning: ' + data.reasoning)
          }
        }
      })
      .catch((err) => {
        setMessageValue(err.toString())
        setStatusValue('waiting')
      })
      .finally(() => {
        setAskAIMetadataButtonText('Ask AI for suggestion')
        setIsAskAIMetadataButtonEnabled(true)
      })
  }

  return (
    <Form
      onSubmit={(event) => {
        event.preventDefault()
      }}
    >
      {formAction == 'edit' ? (
        <FormGroup label='Status' isRequired fieldId={`${SELECT_BASE_NAME}-${formAction}-status-${formData.id}`}>
          <FormSelect
            value={swRequirementStatusValue}
            id={`${SELECT_BASE_NAME}-${formAction}-status-${formData.id}`}
            onChange={handleSwRequirementStatusChange}
            onKeyUp={handleStatusKeyUp}
            aria-label='Sw Requirement Status Input'
          >
            {Constants.status_options.map((option, index) => (
              <FormSelectOption isDisabled={option.disabled} key={index} value={option.value} label={option.label} />
            ))}
          </FormSelect>
        </FormGroup>
      ) : (
        ''
      )}

      <FormGroup label='Sw Requirement Title' isRequired fieldId={`${INPUT_BASE_NAME}-${formAction}-title-${formData.id}`}>
        <TextInput
          isRequired
          id={`${INPUT_BASE_NAME}-${formAction}-title-${formData.id}`}
          value={titleValue || ''}
          onChange={(_ev, value) => handleTitleValueChange(_ev, value)}
          onKeyUp={handleTitleKeyUp}
        />
        {validatedTitleValue !== 'success' && (
          <FormHelperText>
            <HelperText>
              <HelperTextItem variant='error'>{validatedTitleValue === 'error' ? 'This field is mandatory' : ''}</HelperTextItem>
            </HelperText>
          </FormHelperText>
        )}
      </FormGroup>
      <FormGroup label='Description' isRequired fieldId={`${INPUT_BASE_NAME}-${formAction}-description-${formData.id}`}>
        <TextArea
          isRequired
          resizeOrientation='vertical'
          aria-label='Sw Requirement description field'
          id={`${INPUT_BASE_NAME}-${formAction}-description-${formData.id}`}
          value={descriptionValue || ''}
          onChange={(_ev, value) => handleDescriptionValueChange(_ev, value)}
          onKeyUp={handleDescriptionKeyUp}
        />
        {validatedDescriptionValue !== 'success' && (
          <FormHelperText>
            <HelperText>
              <HelperTextItem variant='error'>{validatedDescriptionValue === 'error' ? 'This field is mandatory' : ''}</HelperTextItem>
            </HelperText>
          </FormHelperText>
        )}
      </FormGroup>
      <Grid hasGutter md={3}>
        <FormGroup label='Unique Coverage:' fieldId={`${INPUT_BASE_NAME}-${formAction}-coverage-${formData.id}`}>
          <TextInput
            id={`${INPUT_BASE_NAME}-${formAction}-coverage-${formData.id}`}
            value={coverageValue || ''}
            onChange={(_ev, value) => handleCoverageValueChange(_ev, value)}
            onKeyUp={handleCoverageKeyUp}
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
              <Button id='btn-mapping-sw-requirement-submit' variant='primary' onClick={() => setStatusValue('submitted')}>
                Submit
              </Button>
            </FlexItem>
            <FlexItem>
              <Button id='btn-mapping-sw-requirement-reset' variant='secondary' onClick={resetForm}>
                Reset
              </Button>
            </FlexItem>
            {isAIAvailable ? (
              <FlexItem>
                <Button
                  id='btn-mapping-test-specification-ai-suggestion'
                  variant='secondary'
                  disabled={!isAskAIMetadataButtonEnabled}
                  onClick={() => handleAskAIMetadataClick()}
                >
                  {askAIMetadataButtonText}
                </Button>
              </FlexItem>
            ) : (
              ''
            )}
          </Flex>
        </ActionGroup>
      ) : (
        <span></span>
      )}
    </Form>
  )
}
