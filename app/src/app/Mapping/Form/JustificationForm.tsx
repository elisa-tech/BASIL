import React from 'react'
import * as Constants from '../../Constants/constants'
import {
  ActionGroup,
  Button,
  Form,
  FormGroup,
  FormHelperText,
  FormSelect,
  FormSelectOption,
  HelperText,
  HelperTextItem,
  Hint,
  HintBody,
  TextArea,
  TextInput
} from '@patternfly/react-core'
import { useAuth } from '../../User/AuthProvider'

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

  const [coverageValue, setCoverageValue] = React.useState(formData.coverage)
  const [validatedCoverageValue, setValidatedCoverageValue] = React.useState<Constants.validate>('error')
  const [justificationStatusValue, setJustificationStatusValue] = React.useState(formData.status)

  const [messageValue, setMessageValue] = React.useState(formMessage)

  const [statusValue, setStatusValue] = React.useState('waiting')

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
    if (coverageValue === '') {
      setValidatedCoverageValue('error')
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
      return
    } else if (validatedCoverageValue != 'success') {
      setMessageValue('Justification Coverage of Parent Item is mandatory and must be a integer value in the range 0-100.')
      setStatusValue('waiting')
      return
    } else if (modalSection.trim().length == 0) {
      setMessageValue('Section of the software component specification is mandatory.')
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

    fetch(Constants.API_BASE_URL + '/mapping/api/justifications', {
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
          handleModalToggle()
          setMessageValue('')
          setStatusValue('waiting')
          loadMappingData(Constants.force_reload)
        }
      })
      .catch((err) => {
        setMessageValue(err.toString())
        setStatusValue('waiting')
      })
  }

  return (
    <Form>
      {formAction == 'edit' ? (
        <FormGroup label='Status' isRequired fieldId={`input-justification-${formAction}-status-${formData.id}`}>
          <FormSelect
            value={justificationStatusValue}
            id={`input-justification-${formAction}-status-${formData.id}`}
            onChange={handleJustificationStatusChange}
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

      <FormGroup label='Description' isRequired fieldId={`input-justification-${formAction}-description-${formData.id}`}>
        <TextArea
          isRequired
          resizeOrientation='vertical'
          aria-label='Justification description field'
          id={`input-justification-${formAction}-description-${formData.id}`}
          name={`input-justification-${formAction}-description-${formData.id}`}
          value={descriptionValue || ''}
          onChange={(_ev, value) => handleDescriptionValueChange(_ev, value)}
        />
        {validatedDescriptionValue !== 'success' && (
          <FormHelperText>
            <HelperText>
              <HelperTextItem variant='error'>{validatedDescriptionValue === 'error' ? 'This field is mandatory' : ''}</HelperTextItem>
            </HelperText>
          </FormHelperText>
        )}
      </FormGroup>

      <FormGroup label='Unique Coverage:' isRequired fieldId={`input-justification-${formAction}-coverage-${formData.id}`}>
        <TextInput
          isRequired
          id={`input-justification-${formAction}-coverage-${formData.id}`}
          name={`input-justification-${formAction}-coverage-${formData.id}`}
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
          <Button id='btn-mapping-justification-submit' variant='primary' onClick={() => setStatusValue('submitted')}>
            Submit
          </Button>
          <Button id='btn-mapping-justification-reset' variant='secondary' onClick={resetForm}>
            Reset
          </Button>
        </ActionGroup>
      ) : (
        <span></span>
      )}
    </Form>
  )
}
