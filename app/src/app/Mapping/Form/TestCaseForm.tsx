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

  const [userFiles, setUserFiles] = React.useState([])

  const [titleValue, setTitleValue] = React.useState(formData.title)
  const [validatedTitleValue, setValidatedTitleValue] = React.useState<Constants.validate>('error')

  const [descriptionValue, setDescriptionValue] = React.useState(formData.description)
  const [validatedDescriptionValue, setValidatedDescriptionValue] = React.useState<Constants.validate>('error')

  const [implementationSource, setImplementationSource] = React.useState('url')
  const [implementationFilePath, setImplementationFilePath] = React.useState('')
  const [validatedImplementationFilePath, setValidatedImplementationFilePath] = React.useState<Constants.validate>('error')
  const [repositoryValue, setRepositoryValue] = React.useState(formData.repository)
  const [validatedRepositoryValue, setValidatedRepositoryValue] = React.useState<Constants.validate>('error')
  const [relativePathValue, setRelativePathValue] = React.useState(formData.relative_path)
  const [validatedRelativePathValue, setValidatedRelativePathValue] = React.useState<Constants.validate>('error')

  const [coverageValue, setCoverageValue] = React.useState(formData.coverage != '' ? formData.coverage : '0')
  const [validatedCoverageValue, setValidatedCoverageValue] = React.useState<Constants.validate>('error')

  const [testCaseStatusValue, setTestCaseStatusValue] = React.useState(formData.status)

  const [messageValue, setMessageValue] = React.useState(formMessage)

  const [statusValue, setStatusValue] = React.useState('waiting')

  // Form constants
  const INPUT_BASE_NAME = 'input-test-case'
  const SELECT_BASE_NAME = 'select-test-case'

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
    if (implementationFilePath.trim() == '') {
      setValidatedImplementationFilePath('error')
    } else {
      setValidatedImplementationFilePath('success')
    }
  }, [implementationFilePath])

  React.useEffect(() => {
    if (implementationSource == 'user-files') {
      if (userFiles.length == 0) {
        Constants.loadUserFiles(auth, setUserFiles)
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [implementationSource])

  React.useEffect(() => {
    if (relativePathValue.trim() === '') {
      setValidatedRelativePathValue('error')
    } else {
      setValidatedRelativePathValue('success')
    }
  }, [relativePathValue])

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
  const handleImplementationFilePathChange = (_event, value: string) => {
    setImplementationFilePath(value)
  }

  const handleSubmit = () => {
    if (validatedTitleValue != 'success') {
      setMessageValue('Test Case Title is mandatory.')
      setStatusValue('waiting')
      return
    }
    if (validatedDescriptionValue != 'success') {
      setMessageValue('Test Case Description is mandatory.')
      setStatusValue('waiting')
      return
    }
    if (implementationSource == 'url') {
      if (validatedRepositoryValue != 'success') {
        setMessageValue('Test Case Repository is mandatory.')
        setStatusValue('waiting')
        return
      } else if (validatedRelativePathValue != 'success') {
        setMessageValue('Test Case Relative Path is mandatory.')
        setStatusValue('waiting')
        return
      }
    }
    if (implementationSource == 'user-files') {
      if (validatedImplementationFilePath != 'success') {
        setMessageValue('Test Case user file is mandatory.')
        setStatusValue('waiting')
        return
      }
    }
    if (validatedCoverageValue != 'success') {
      setMessageValue('Test Case Coverage of Parent Item is mandatory and must be an integer in the range 0-100.')
      setStatusValue('waiting')
      return
    }
    if (modalSection.trim().length == 0) {
      setMessageValue(Constants.UNVALID_REF_DOCUMENT_SECTION_MESSAGE)
      setStatusValue('waiting')
      return
    }

    setMessageValue('')

    const tc_repository: string = implementationSource == 'url' ? repositoryValue : implementationFilePath.split('/api/')[0]
    const tc_relative_path: string = implementationSource == 'url' ? relativePathValue : implementationFilePath.slice(tc_repository.length)

    const data = {
      'api-id': api.id,
      'test-case': {
        title: titleValue,
        description: descriptionValue,
        repository: tc_repository,
        'relative-path': tc_relative_path
      },
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

    let status: number = 0
    let status_text: string = ''

    fetch(Constants.API_BASE_URL + '/mapping/' + parentType + '/test-cases', {
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
      })
  }

  // Form elements focus
  const focusInputTitle = () => {
    document.getElementById(INPUT_BASE_NAME + '-' + formAction + '-title-' + formData.id)?.focus()
  }

  const focusInputDescription = () => {
    document.getElementById(INPUT_BASE_NAME + '-' + formAction + '-description-' + formData.id)?.focus()
  }

  const focusInputRepository = () => {
    document.getElementById(INPUT_BASE_NAME + '-' + formAction + '-repository-' + formData.id)?.focus()
  }

  const focusInputRelativePath = () => {
    document.getElementById(INPUT_BASE_NAME + '-' + formAction + '-relative-path-' + formData.id)?.focus()
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
      focusInputRepository()
    }
  }

  const handleRepositoryKeyUp = (event) => {
    if (event.key === 'Enter') {
      focusInputRelativePath()
    }
  }

  const handleRelativePathKeyUp = (event) => {
    if (event.key === 'Enter') {
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
            value={testCaseStatusValue}
            id={`${SELECT_BASE_NAME}-${formAction}-status-${formData.id}`}
            onChange={handleTestCaseStatusChange}
            onKeyUp={handleStatusKeyUp}
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

      <FormGroup label='Test Case Title' isRequired fieldId={`${INPUT_BASE_NAME}-${formAction}-title-${formData.id}`}>
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
          aria-label='Test Case description field'
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
      <FormGroup
        label={implementationSource == 'url' ? 'Repository' : 'User file'}
        isRequired
        fieldId={`${INPUT_BASE_NAME}-${formAction}-repository-${formData.id}`}
        labelIcon={
          implementationSource == 'url' ? (
            <Button variant='link' onClick={() => setImplementationSource('user-files')}>
              From user files
            </Button>
          ) : (
            <Button variant='link' onClick={() => setImplementationSource('url')}>
              From url
            </Button>
          )
        }
      >
        {implementationSource == 'url' ? (
          <>
            <TextInput
              isRequired
              id={`${INPUT_BASE_NAME}-${formAction}-repository-${formData.id}`}
              value={repositoryValue || ''}
              onChange={(_ev, value) => handleRepositoryValueChange(_ev, value)}
              onKeyUp={handleRepositoryKeyUp}
            />
            {validatedRepositoryValue !== 'success' && (
              <FormHelperText>
                <HelperText>
                  <HelperTextItem variant='error'>{validatedRepositoryValue === 'error' ? 'This field is mandatory' : ''}</HelperTextItem>
                </HelperText>
              </FormHelperText>
            )}
          </>
        ) : (
          <>
            <FormSelect
              value={implementationFilePath}
              id={`${SELECT_BASE_NAME}-${formAction}-file-${formData.id}`}
              onChange={handleImplementationFilePathChange}
              onKeyUp={handleRepositoryKeyUp}
              aria-label='Test Case from user file'
            >
              <FormSelectOption key={0} value={''} label={'Select a file from the list'} />
              {userFiles.map((userFile, index) => (
                <FormSelectOption key={index + 1} value={userFile['filepath']} label={userFile['filename']} />
              ))}
            </FormSelect>
            {validatedImplementationFilePath !== 'success' && (
              <FormHelperText>
                <HelperText>
                  <HelperTextItem variant='error'>
                    {validatedImplementationFilePath === 'error' ? 'This field is mandatory' : ''}
                  </HelperTextItem>
                </HelperText>
              </FormHelperText>
            )}
          </>
        )}
      </FormGroup>
      {implementationSource == 'url' ? (
        <FormGroup label='Relative Path' isRequired fieldId={`${INPUT_BASE_NAME}-${formAction}-relative-path-${formData.id}`}>
          <TextInput
            isRequired
            id={`${INPUT_BASE_NAME}-${formAction}-relative-path-${formData.id}`}
            value={relativePathValue || ''}
            onChange={(_ev, value) => handleRelativePathValueChange(_ev, value)}
            onKeyUp={handleRelativePathKeyUp}
          />
          {validatedRelativePathValue !== 'success' && (
            <FormHelperText>
              <HelperText>
                <HelperTextItem variant='error'>{validatedRelativePathValue === 'error' ? 'This field is mandatory' : ''}</HelperTextItem>
              </HelperText>
            </FormHelperText>
          )}
        </FormGroup>
      ) : (
        ''
      )}
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
              <Button id='btn-mapping-test-case-submit' variant='primary' onClick={() => setStatusValue('submitted')}>
                Submit
              </Button>
            </FlexItem>
            <FlexItem>
              <Button id='btn-mapping-test-case-reset' variant='secondary' onClick={resetForm}>
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
