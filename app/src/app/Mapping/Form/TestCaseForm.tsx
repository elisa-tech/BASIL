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

export interface TestCaseFormProps {
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

export const TestCaseForm: React.FunctionComponent<TestCaseFormProps> = ({
  api,
  formAction = 'add',
  formData = { id: 0, coverage: 0, title: '', description: '', repository: '', relative_path: '' },
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
}: TestCaseFormProps) => {
  const auth = useAuth()

  const [titleValue, setTitleValue] = React.useState(formData.title)
  const [validatedTitleValue, setValidatedTitleValue] = React.useState<Constants.validate>('error')

  const [descriptionValue, setDescriptionValue] = React.useState(formData.description)
  const [validatedDescriptionValue, setValidatedDescriptionValue] = React.useState<Constants.validate>('error')

  const [repositoryValue, setRepositoryValue] = React.useState(formData.repository)
  const [validatedRepositoryValue, setValidatedRepositoryValue] = React.useState<Constants.validate>('error')

  const [relativePathValue, setRelativePathValue] = React.useState(formData.relative_path)
  const [validatedRelativePathValue, setValidatedRelativePathValue] = React.useState<Constants.validate>('error')

  const [coverageValue, setCoverageValue] = React.useState(formData.coverage != '' ? formData.coverage : '0')
  const [validatedCoverageValue, setValidatedCoverageValue] = React.useState<Constants.validate>('error')

  const [testCaseStatusValue, setTestCaseStatusValue] = React.useState(formData.status)

  const [messageValue, setMessageValue] = React.useState(formMessage)

  const [statusValue, setStatusValue] = React.useState('waiting')

  const resetForm = () => {
    setTitleValue('')
    setDescriptionValue('')
    setRepositoryValue('')
    setRelativePathValue('')
    setCoverageValue('0')
  }

  React.useEffect(() => {
    if (titleValue.trim() === '') {
      setValidatedTitleValue('error')
    } else {
      setValidatedTitleValue('success')
    }
  }, [titleValue])

  React.useEffect(() => {
    if (descriptionValue.trim() === '') {
      setValidatedDescriptionValue('error')
    } else {
      setValidatedDescriptionValue('success')
    }
  }, [descriptionValue])

  React.useEffect(() => {
    if (repositoryValue.trim() === '') {
      setValidatedRepositoryValue('error')
    } else {
      setValidatedRepositoryValue('success')
    }
  }, [repositoryValue])

  React.useEffect(() => {
    if (relativePathValue.trim() === '') {
      setValidatedRelativePathValue('error')
    } else {
      setValidatedRelativePathValue('success')
    }
  }, [relativePathValue])

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

  const handleRepositoryValueChange = (_event, value: string) => {
    setRepositoryValue(value)
  }

  const handleDescriptionValueChange = (_event, value: string) => {
    setDescriptionValue(value)
  }

  const handleRelativePathValueChange = (_event, value: string) => {
    setRelativePathValue(value)
  }

  const handleCoverageValueChange = (_event, value: string) => {
    setCoverageValue(value)
  }

  const handleTestCaseStatusChange = (_event, value: string) => {
    setTestCaseStatusValue(value)
  }

  const handleSubmit = () => {
    if (validatedTitleValue != 'success') {
      setMessageValue('Test Case Title is mandatory.')
      setStatusValue('waiting')
      return
    } else if (validatedDescriptionValue != 'success') {
      setMessageValue('Test Case Description is mandatory.')
      setStatusValue('waiting')
      return
    } else if (validatedRepositoryValue != 'success') {
      setMessageValue('Test Case Repository is mandatory.')
      setStatusValue('waiting')
      return
    } else if (validatedRelativePathValue != 'success') {
      setMessageValue('Test Case Relative Path is mandatory.')
      setStatusValue('waiting')
      return
    } else if (validatedCoverageValue != 'success') {
      setMessageValue('Test Case Coverage of Parent Item is mandatory and must be an integer in the range 0-100.')
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
      'test-case': { title: titleValue, description: descriptionValue, repository: repositoryValue, 'relative-path': relativePathValue },
      section: modalSection,
      offset: modalOffset,
      coverage: coverageValue,
      'user-id': auth.userId,
      token: auth.token
    }

    if (modalIndirect == true || formVerb == 'PUT') {
      data['relation-id'] = parentData.relation_id
      data['relation-to'] = parentRelatedToType
      if (parentType == Constants._TS) {
        if (parentRelatedToType == Constants._A) {
          data[parentType] = { id: parentData[Constants._TS_]['id'] }
        } else if (parentRelatedToType == Constants._SR) {
          data[parentType] = { id: parentData[Constants._TS_]['id'] }
        }
      } else if (parentType == Constants._SR) {
        data[parentType] = { id: parentData[Constants._SR_]['id'] }
      }
    }

    if (formVerb == 'PUT') {
      data[Constants._TC]['status'] = testCaseStatusValue
    }

    fetch(Constants.API_BASE_URL + '/mapping/' + parentType + '/test-cases', {
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
      })
  }

  return (
    <Form>
      {formAction == 'edit' ? (
        <FormGroup label='Status' isRequired fieldId={`input-test-case-${formAction}-status-${formData.id}`}>
          <FormSelect
            value={testCaseStatusValue}
            id={`input-test-case-${formAction}-status-${formData.id}`}
            onChange={handleTestCaseStatusChange}
            aria-label='Test Case Status Input'
          >
            {Constants.status_options.map((option, index) => (
              <FormSelectOption isDisabled={option.disabled} key={index} value={option.value} label={option.label} />
            ))}
          </FormSelect>
        </FormGroup>
      ) : (
        ''
      )}

      <FormGroup label='Test Case Title' isRequired fieldId={`input-test-case-${formAction}-title-${formData.id}`}>
        <TextInput
          isRequired
          id={`input-test-case-${formAction}-title-${formData.id}`}
          name={`input-test-case-${formAction}-title-${formData.id}`}
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
      <FormGroup label='Description' isRequired fieldId={`input-test-case-${formAction}-description-${formData.id}`}>
        <TextArea
          isRequired
          resizeOrientation='vertical'
          aria-label='Test Case description field'
          id={`input-test-case-${formAction}-description-${formData.id}`}
          name={`input-test-case-${formAction}-description-${formData.id}`}
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
      <FormGroup label='Repository' isRequired fieldId={`input-test-case-${formAction}-repository-${formData.id}`}>
        <TextInput
          isRequired
          id={`input-test-case-${formAction}-repository-${formData.id}`}
          name={`input-test-case-${formAction}-repository-${formData.id}`}
          value={repositoryValue || ''}
          onChange={(_ev, value) => handleRepositoryValueChange(_ev, value)}
        />
        {validatedRepositoryValue !== 'success' && (
          <FormHelperText>
            <HelperText>
              <HelperTextItem variant='error'>{validatedRepositoryValue === 'error' ? 'This field is mandatory' : ''}</HelperTextItem>
            </HelperText>
          </FormHelperText>
        )}
      </FormGroup>
      <FormGroup label='Relative Path' isRequired fieldId={`input-test-case-${formAction}-relative-path-${formData.id}`}>
        <TextInput
          isRequired
          id={`input-test-case-${formAction}-relative-path-${formData.id}`}
          name={`input-test-case-${formAction}-relative-path-${formData.id}`}
          value={relativePathValue || ''}
          onChange={(_ev, value) => handleRelativePathValueChange(_ev, value)}
        />
        {validatedRelativePathValue !== 'success' && (
          <FormHelperText>
            <HelperText>
              <HelperTextItem variant='error'>{validatedRelativePathValue === 'error' ? 'This field is mandatory' : ''}</HelperTextItem>
            </HelperText>
          </FormHelperText>
        )}
      </FormGroup>

      <FormGroup label='Unique Coverage:' isRequired fieldId={`input-test-case-${formAction}-coverage-${formData.id}`}>
        <TextInput
          isRequired
          id={`input-test-case-${formAction}-coverage-${formData.id}`}
          name={`input-test-case-${formAction}-coverage-${formData.id}`}
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
          <Button id='btn-mapping-test-case-submit' variant='primary' onClick={() => setStatusValue('submitted')}>
            Submit
          </Button>
          <Button id='btn-mapping-test-case-reset' variant='secondary' onClick={resetForm}>
            Reset
          </Button>
        </ActionGroup>
      ) : (
        <span></span>
      )}
    </Form>
  )
}
