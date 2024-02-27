import React from 'react'
import * as Constants from '../../Constants/constants'
import {
  ActionGroup,
  Button,
  Form,
  FormGroup,
  FormHelperText,
  HelperText,
  HelperTextItem,
  Hint,
  HintBody,
  TextArea,
  TextInput
} from '@patternfly/react-core'
import { useAuth } from '@app/User/AuthProvider'

export interface TestSpecificationFormProps {
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

export const TestSpecificationForm: React.FunctionComponent<TestSpecificationFormProps> = ({
  api,
  formAction = 'add',
  formData = { id: 0, coverage: 0, title: '', preconditions: '', test_description: '', expected_behavior: '' },
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
}: TestSpecificationFormProps) => {
  let auth = useAuth()

  const [titleValue, setTitleValue] = React.useState(formData.title)
  const [validatedTitleValue, setValidatedTitleValue] = React.useState<Constants.validate>('error')

  const [preconditionsValue, setPreconditionsValue] = React.useState(formData.preconditions)

  const [testDescriptionValue, setTestDescriptionValue] = React.useState(formData.test_description)
  const [validatedTestDescriptionValue, setValidatedTestDescriptionValue] = React.useState<Constants.validate>('error')

  const [expectedBehaviorValue, setExpectedBehaviorValue] = React.useState(formData.expected_behavior)
  const [validatedExpectedBehaviorValue, setValidatedExpectedBehaviorValue] = React.useState<Constants.validate>('error')

  const [coverageValue, setCoverageValue] = React.useState(formData.coverage != '' ? formData.coverage : '0')
  const [validatedCoverageValue, setValidatedCoverageValue] = React.useState<Constants.validate>('error')

  const [messageValue, setMessageValue] = React.useState(formMessage)

  const [statusValue, setStatusValue] = React.useState('waiting')

  const resetForm = () => {
    setTitleValue('')
    setPreconditionsValue('')
    setTestDescriptionValue('')
    setExpectedBehaviorValue('')
    setCoverageValue('0')
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
    if (testDescriptionValue == undefined) {
      setTestDescriptionValue('')
    } else {
      if (testDescriptionValue.trim() === '') {
        setValidatedTestDescriptionValue('error')
      } else {
        setValidatedTestDescriptionValue('success')
      }
    }
  }, [testDescriptionValue])

  React.useEffect(() => {
    if (expectedBehaviorValue == undefined) {
      setExpectedBehaviorValue('')
    } else {
      if (expectedBehaviorValue.trim() === '') {
        setValidatedExpectedBehaviorValue('error')
      } else {
        setValidatedExpectedBehaviorValue('success')
      }
    }
  }, [expectedBehaviorValue])

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

  const handleTitleValueChange = (_event, value: string) => {
    setTitleValue(value)
  }

  const handlePreconditionsValueChange = (_event, value: string) => {
    setPreconditionsValue(value)
  }

  const handleTestDescriptionValueChange = (_event, value: string) => {
    setTestDescriptionValue(value)
  }

  const handleExpectedBehaviorValueChange = (_event, value: string) => {
    setExpectedBehaviorValue(value)
  }

  const handleCoverageValueChange = (_event, value: string) => {
    setCoverageValue(value)
  }

  const handleSubmit = () => {
    if (validatedTitleValue != 'success') {
      setMessageValue('Test Specification Title is mandatory.')
      setStatusValue('waiting')
      return
    } else if (validatedTestDescriptionValue != 'success') {
      setMessageValue('Test Specification Test Description is mandatory.')
      setStatusValue('waiting')
      return
    } else if (validatedExpectedBehaviorValue != 'success') {
      setMessageValue('Test Specification Expected Behavior is mandatory.')
      setStatusValue('waiting')
      return
    } else if (validatedCoverageValue != 'success') {
      setMessageValue('Test Specification Coverage of Parent Item is mandatory.')
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
      'test-specification': {
        title: titleValue,
        preconditions: preconditionsValue,
        'test-description': testDescriptionValue,
        'expected-behavior': expectedBehaviorValue
      },
      'sw-requirement': {},
      section: modalSection,
      offset: modalOffset,
      coverage: coverageValue,
      'user-id': auth.userId,
      token: auth.token
    }

    if (modalIndirect == true || formVerb == 'PUT') {
      data['relation-id'] = parentData.relation_id
      data['relation-to'] = parentRelatedToType
      if (parentType == Constants._SR) {
        data['sw-requirement']['id'] = parentData.sw_requirement.id
      }
    }

    if (formVerb == 'PUT') {
      data['test-specification']['id'] = formData.id
    }

    fetch(Constants.API_BASE_URL + '/mapping/' + parentType + '/test-specifications', {
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
      <FormGroup label='Test Specification Title' isRequired fieldId={`input-test-specification-${formAction}-title-${formData.id}`}>
        <TextInput
          isRequired
          id={`input-test-specification-${formAction}-title-${formData.id}`}
          name={`input-test-specification-${formAction}-title-${formData.id}`}
          value={titleValue || ''}
          onChange={(_ev, value) => handleTitleValueChange(_ev, value)}
        />
        {validatedTitleValue !== 'success' && (
          <FormHelperText>
            <HelperText>
              <HelperTextItem variant='error'>{validatedTitleValue === 'error' ? 'This field is mandatory' : ''}</HelperTextItem>
            </HelperText>
          </FormHelperText>
        )}
      </FormGroup>
      <FormGroup label='Preconditions' fieldId={`input-test-specification-${formAction}-preconditions-${formData.id}`}>
        <TextArea
          isRequired
          resizeOrientation='vertical'
          aria-label='Test Specification preconditions field'
          id={`input-test-specification-${formAction}-preconditions-${formData.id}`}
          name={`input-test-specification-${formAction}-preconditions-${formData.id}`}
          value={preconditionsValue || ''}
          onChange={(_ev, value) => handlePreconditionsValueChange(_ev, value)}
        />
      </FormGroup>
      <FormGroup label='Test Description' isRequired fieldId={`input-test-specification-test-description-${formData.id}`}>
        <TextArea
          isRequired
          resizeOrientation='vertical'
          aria-label='Test Specification test description field'
          id={`input-test-specification-${formAction}-test-description-${formData.id}`}
          name={`input-test-specification-${formAction}-test-description-${formData.id}`}
          value={testDescriptionValue || ''}
          onChange={(_ev, value) => handleTestDescriptionValueChange(_ev, value)}
        />
        {validatedTestDescriptionValue !== 'success' && (
          <FormHelperText>
            <HelperText>
              <HelperTextItem variant='error'>{validatedTestDescriptionValue === 'error' ? 'This field is mandatory' : ''}</HelperTextItem>
            </HelperText>
          </FormHelperText>
        )}
      </FormGroup>
      <FormGroup label='Expected Behavior' isRequired fieldId={`input-test-specification-${formAction}-expected-behavior-${formData.id}`}>
        <TextArea
          isRequired
          resizeOrientation='vertical'
          aria-label='Test Specification expected behavior field'
          id={`input-test-specification-${formAction}-expected-behavior-${formData.id}`}
          name={`input-test-specification-${formAction}-expected-behavior-${formData.id}`}
          value={expectedBehaviorValue || ''}
          onChange={(_ev, value) => handleExpectedBehaviorValueChange(_ev, value)}
        />
        {validatedExpectedBehaviorValue !== 'success' && (
          <FormHelperText>
            <HelperText>
              <HelperTextItem variant='error'>{validatedExpectedBehaviorValue === 'error' ? 'This field is mandatory' : ''}</HelperTextItem>
            </HelperText>
          </FormHelperText>
        )}
      </FormGroup>

      <FormGroup label='Unique Coverage:' isRequired fieldId={`input-test-specification-${formAction}-coverage-${formData.id}`}>
        <TextInput
          isRequired
          id={`input-test-specification-${formAction}-coverage-${formData.id}`}
          name={`input-test-specification-${formAction}-coverage-${formData.id}`}
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
        <Hint>
          <HintBody>{messageValue}</HintBody>
        </Hint>
      ) : (
        <span></span>
      )}

      {formDefaultButtons ? (
        <ActionGroup>
          <Button id='btn-mapping-test-specification-submit' variant='primary' onClick={() => setStatusValue('submitted')}>
            Submit
          </Button>
          <Button id='btn-mapping-test-specification-reset' variant='secondary' onClick={resetForm}>
            Reset
          </Button>
        </ActionGroup>
      ) : (
        <span></span>
      )}
    </Form>
  )
}
