import React from 'react'
import * as Constants from '@app/Constants/constants'
import {
  ActionGroup,
  Button,
  Flex,
  FlexItem,
  Form,
  FormGroup,
  FormHelperText,
  FormSelect,
  FormSelectOption,
  Grid,
  HelperText,
  HelperTextItem,
  Hint,
  HintBody,
  TextArea,
  TextInput
} from '@patternfly/react-core'
import { useAuth } from '@app/User/AuthProvider'

export interface JustificationFormProps {
  api
  formAction: string
  formData
  formDefaultButtons: number
  formMessage: string
  formVerb: string
  handleModalToggle
  loadMappingData
  modalFormSubmitState: string
  modalOffset
  modalSection
  parentData
}

export const JustificationForm: React.FunctionComponent<JustificationFormProps> = ({
  api,
  formAction = 'add',
  formData = { id: 0, description: '', coverage: 100 },
  formDefaultButtons = 1,
  formMessage = '',
  formVerb,
  handleModalToggle,
  loadMappingData,
  modalFormSubmitState = 'waiting',
  modalOffset,
  modalSection,
  parentData
}: JustificationFormProps) => {
  const auth = useAuth()
  const [descriptionValue, setDescriptionValue] = React.useState(formData.description)
  const [validatedDescriptionValue, setValidatedDescriptionValue] = React.useState<Constants.validate>('error')

  const [coverageValue, setCoverageValue] = React.useState(formData.coverage != '' ? formData.coverage : '100')
  const [validatedCoverageValue, setValidatedCoverageValue] = React.useState<Constants.validate>('error')
  const [justificationStatusValue, setJustificationStatusValue] = React.useState(formData.status)

  const [messageValue, setMessageValue] = React.useState(formMessage)

  const [statusValue, setStatusValue] = React.useState('waiting')

  // Form constants
  const INPUT_BASE_NAME = 'input-justification'
  const SELECT_BASE_NAME = 'select-justification'

  const resetForm = () => {
    setDescriptionValue('')
    setCoverageValue('100')
  }

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

  const handleDescriptionValueChange = (_event, value: string) => {
    setDescriptionValue(value)
  }

  const handleCoverageValueChange = (_event, value: string) => {
    setCoverageValue(value)
  }

  const handleJustificationStatusChange = (_event, value: string) => {
    setJustificationStatusValue(value)
  }

  const handleSubmit = () => {
    if (validatedDescriptionValue != 'success') {
      setMessageValue('Justification Description is mandatory.')
      setStatusValue('waiting')
      focusInputDescription()
      return
    }
    if (validatedCoverageValue != 'success') {
      setMessageValue('Justification Coverage of Parent Item is mandatory and must be a integer value in the range 0-100.')
      setStatusValue('waiting')
      focusInputCoverage()
      return
    }
    if (modalSection.trim().length == 0) {
      setMessageValue(Constants.UNVALID_REF_DOCUMENT_SECTION_MESSAGE)
      setStatusValue('waiting')
      return
    }

    setMessageValue('')

    const data = {
      'api-id': api.id,
      justification: { description: descriptionValue },
      section: modalSection,
      offset: modalOffset,
      coverage: coverageValue,
      'user-id': auth.userId,
      token: auth.token
    }

    if (formVerb == 'PUT' || formVerb == 'DELETE') {
      data['relation-id'] = parentData.relation_id
      data['justification']['id'] = formData.id
    }

    if (formVerb == 'PUT') {
      data['justification']['status'] = justificationStatusValue
    }

    let status: number = 0
    let status_text: string = ''

    fetch(Constants.API_BASE_URL + '/mapping/api/justifications', {
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
          handleModalToggle()
          setMessageValue('')
          setStatusValue('waiting')
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
  const focusInputDescription = () => {
    document.getElementById(INPUT_BASE_NAME + '-' + formAction + '-description-' + formData.id)?.focus()
  }

  const focusInputCoverage = () => {
    document.getElementById(INPUT_BASE_NAME + '-' + formAction + '-coverage-' + formData.id)?.focus()
  }

  // Keyboard events
  const handleStatusKeyUp = (event) => {
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

  return (
    <Form
      onSubmit={(event) => {
        event.preventDefault()
      }}
    >
      {formAction == 'edit' ? (
        <FormGroup label='Status' isRequired fieldId={`${SELECT_BASE_NAME}-${formAction}-status-${formData.id}`}>
          <FormSelect
            value={justificationStatusValue}
            id={`${SELECT_BASE_NAME}-${formAction}-status-${formData.id}`}
            onChange={handleJustificationStatusChange}
            onKeyUp={handleStatusKeyUp}
            aria-label='Justification Status Input'
          >
            {Constants.status_options.map((option, index) => (
              <FormSelectOption isDisabled={option.disabled} key={index} value={option.value} label={option.label} />
            ))}
          </FormSelect>
        </FormGroup>
      ) : (
        ''
      )}

      <FormGroup label='Description' isRequired fieldId={`${INPUT_BASE_NAME}-${formAction}-description-${formData.id}`}>
        <TextArea
          isRequired
          resizeOrientation='vertical'
          aria-label='Justification description field'
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

      <Grid hasGutter md={4}>
        <FormGroup label={Constants.FORM_COMPLETION_LABEL} isRequired fieldId={`${INPUT_BASE_NAME}-${formAction}-coverage-${formData.id}`}>
          <TextInput
            isRequired
            id={`${INPUT_BASE_NAME}-${formAction}-coverage-${formData.id}`}
            value={coverageValue}
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
              <Button id='btn-mapping-justification-submit' variant='primary' onClick={() => setStatusValue('submitted')}>
                Submit
              </Button>
            </FlexItem>
            <FlexItem>
              <Button id='btn-mapping-justification-reset' variant='secondary' onClick={resetForm}>
                Reset
              </Button>
            </FlexItem>
          </Flex>
        </ActionGroup>
      ) : (
        <span></span>
      )}
    </Form>
  )
}
