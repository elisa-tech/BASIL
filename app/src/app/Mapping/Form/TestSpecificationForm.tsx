import React from 'react'
import * as Constants from '../../Constants/constants'
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
import { useAuth } from '../../User/AuthProvider'

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
  const auth = useAuth()

  const [titleValue, setTitleValue] = React.useState(formData.title)
  const [validatedTitleValue, setValidatedTitleValue] = React.useState<Constants.validate>('error')

  const [preconditionsValue, setPreconditionsValue] = React.useState(formData.preconditions)

  const [testDescriptionValue, setTestDescriptionValue] = React.useState(formData.test_description)
  const [validatedTestDescriptionValue, setValidatedTestDescriptionValue] = React.useState<Constants.validate>('error')

  const [expectedBehaviorValue, setExpectedBehaviorValue] = React.useState(formData.expected_behavior)
  const [validatedExpectedBehaviorValue, setValidatedExpectedBehaviorValue] = React.useState<Constants.validate>('error')

  const [coverageValue, setCoverageValue] = React.useState(formData.coverage != '' ? formData.coverage : '0')
  const [validatedCoverageValue, setValidatedCoverageValue] = React.useState<Constants.validate>('error')

  const [testSpecificationStatusValue, setTestSpecificationStatusValue] = React.useState(formData.status)

  const [messageValue, setMessageValue] = React.useState(formMessage)

  const [statusValue, setStatusValue] = React.useState('waiting')

  // Form constants
  const INPUT_BASE_NAME = 'input-test-specification'
  const SELECT_BASE_NAME = 'select-test-specification'

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

  const handleTestSpecificationStatusChange = (_event, value: string) => {
    setTestSpecificationStatusValue(value)
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
      setMessageValue(Constants.UNVALID_REF_DOCUMENT_SECTION_MESSAGE)
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
      data[Constants._TS]['id'] = formData.id
      data[Constants._TS]['status'] = testSpecificationStatusValue
    }

    fetch(Constants.API_BASE_URL + '/mapping/' + parentType + '/test-specifications', {
      method: formVerb,
      headers: Constants.JSON_HEADER,
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

  // Form elements focus
  const focusInputTitle = () => {
    document.getElementById(INPUT_BASE_NAME + '-' + formAction + '-title-' + formData.id)?.focus()
  }

  const focusInputPreconditions = () => {
    document.getElementById(INPUT_BASE_NAME + '-' + formAction + '-preconditions-' + formData.id)?.focus()
  }

  const focusInputTestDescription = () => {
    document.getElementById(INPUT_BASE_NAME + '-' + formAction + '-test-description-' + formData.id)?.focus()
  }

  const focusInputExpectedBehavior = () => {
    document.getElementById(INPUT_BASE_NAME + '-' + formAction + '-expected-behavior-' + formData.id)?.focus()
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
      focusInputPreconditions()
    }
  }

  const handlePreconditionsKeyUp = (event) => {
    if (event.key === 'Enter' && event.shiftKey) {
      focusInputTestDescription()
    }
  }

  const handleTestDescriptionKeyUp = (event) => {
    if (event.key === 'Enter' && event.shiftKey) {
      focusInputExpectedBehavior()
    }
  }

  const handleExpectedBehaviorKeyUp = (event) => {
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
            value={testSpecificationStatusValue}
            id={`${SELECT_BASE_NAME}-${formAction}-status-${formData.id}`}
            onChange={handleTestSpecificationStatusChange}
            onKeyUp={handleStatusKeyUp}
            aria-label='Test Specification Status Input'
          >
            {Constants.status_options.map((option, index) => (
              <FormSelectOption isDisabled={option.disabled} key={index} value={option.value} label={option.label} />
            ))}
          </FormSelect>
        </FormGroup>
      ) : (
        ''
      )}

      <FormGroup label='Test Specification Title' isRequired fieldId={`${INPUT_BASE_NAME}-${formAction}-title-${formData.id}`}>
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
      <FormGroup label='Preconditions' fieldId={`${INPUT_BASE_NAME}-${formAction}-preconditions-${formData.id}`}>
        <TextArea
          isRequired
          resizeOrientation='vertical'
          aria-label='Test Specification preconditions field'
          id={`${INPUT_BASE_NAME}-${formAction}-preconditions-${formData.id}`}
          value={preconditionsValue || ''}
          onChange={(_ev, value) => handlePreconditionsValueChange(_ev, value)}
          onKeyUp={handlePreconditionsKeyUp}
        />
      </FormGroup>
      <FormGroup label='Test Description' isRequired fieldId={`${INPUT_BASE_NAME}-${formAction}-test-description-${formData.id}`}>
        <TextArea
          isRequired
          resizeOrientation='vertical'
          aria-label='Test Specification test description field'
          id={`${INPUT_BASE_NAME}-${formAction}-test-description-${formData.id}`}
          value={testDescriptionValue || ''}
          onChange={(_ev, value) => handleTestDescriptionValueChange(_ev, value)}
          onKeyUp={handleTestDescriptionKeyUp}
        />
        {validatedTestDescriptionValue !== 'success' && (
          <FormHelperText>
            <HelperText>
              <HelperTextItem variant='error'>{validatedTestDescriptionValue === 'error' ? 'This field is mandatory' : ''}</HelperTextItem>
            </HelperText>
          </FormHelperText>
        )}
      </FormGroup>
      <FormGroup label='Expected Behavior' isRequired fieldId={`${INPUT_BASE_NAME}-${formAction}-expected-behavior-${formData.id}`}>
        <TextArea
          isRequired
          resizeOrientation='vertical'
          aria-label='Test Specification expected behavior field'
          id={`${INPUT_BASE_NAME}-${formAction}-expected-behavior-${formData.id}`}
          value={expectedBehaviorValue || ''}
          onChange={(_ev, value) => handleExpectedBehaviorValueChange(_ev, value)}
          onKeyUp={handleExpectedBehaviorKeyUp}
        />
        {validatedExpectedBehaviorValue !== 'success' && (
          <FormHelperText>
            <HelperText>
              <HelperTextItem variant='error'>{validatedExpectedBehaviorValue === 'error' ? 'This field is mandatory' : ''}</HelperTextItem>
            </HelperText>
          </FormHelperText>
        )}
      </FormGroup>

      <Grid hasGutter md={3}>
        <FormGroup label='Unique Coverage:' isRequired fieldId={`${INPUT_BASE_NAME}-${formAction}-coverage-${formData.id}`}>
          <TextInput
            isRequired
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
              <Button id='btn-mapping-test-specification-submit' variant='primary' onClick={() => setStatusValue('submitted')}>
                Submit
              </Button>
            </FlexItem>
            <FlexItem>
              <Button id='btn-mapping-test-specification-reset' variant='secondary' onClick={resetForm}>
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
