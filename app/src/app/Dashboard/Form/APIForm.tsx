import React from 'react'
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
  HelperText,
  HelperTextItem,
  Hint,
  HintBody,
  Radio,
  Text,
  TextInput
} from '@patternfly/react-core'
import * as Constants from '../../Constants/constants'
import { useAuth } from '../../User/AuthProvider'

export interface APIFormProps {
  formDefaultButtons?: number
  formVerb: string
  formAction: string
  formData
  formMessage?: string
  modalFormSubmitState?: string
  setModalFormSubmitState?
}

export const APIForm: React.FunctionComponent<APIFormProps> = ({
  formDefaultButtons = 1,
  formVerb = 'POST',
  formAction = 'add',
  formData = {
    id: 0,
    api: '',
    library: '',
    library_version: '',
    raw_specification_url: '',
    category: '',
    default_view: '',
    tags: '',
    implementation_file_from_row: '',
    implementation_file_to_row: '',
    implementation_file: '',
    'user-id': '',
    token: ''
  },
  formMessage = '',
  modalFormSubmitState = 'waiting',
  setModalFormSubmitState
}: APIFormProps) => {
  const auth = useAuth()
  const [referenceSource, setReferenceSource] = React.useState<string>('url')
  const [referenceFileName, setReferenceFileName] = React.useState<string>('')
  const [referenceUrl, setReferenceUrl] = React.useState(formData.raw_specification_url)
  const [validatedReferenceValue, setValidatedReferenceValue] = React.useState<Constants.validate>('error')

  const [implementationSource, setImplementationSource] = React.useState<string>('url')
  const [implementationFileName, setImplementationFileName] = React.useState<string>('')
  const [implementationUrl, setImplementationUrl] = React.useState(formData.implementation_file)

  const [userFiles, setUserFiles] = React.useState([])

  const [apiValue, setApiValue] = React.useState(formData.api)
  const [validatedApiValue, setValidatedApiValue] = React.useState<Constants.validate>('error')

  const [libraryValue, setLibraryValue] = React.useState(formData.library)
  const [validatedLibraryValue, setValidatedLibraryValue] = React.useState<Constants.validate>('error')

  const [libraryVersionValue, setLibraryVersionValue] = React.useState(formAction == 'fork' ? '' : formData.library_version)
  const [validatedLibraryVersionValue, setValidatedLibraryVersionValue] = React.useState<Constants.validate>('error')

  const [categoryValue, setCategoryValue] = React.useState(formData.category)
  const [defaultViewValue, setDefaultViewValue] = React.useState(formData.default_view)

  const [tagsValue, setTagsValue] = React.useState(formData.tags)

  const [implementationFileFromRowValue, setImplementationFileFromRowValue] = React.useState(formData.implementation_file_from_row)
  const [validatedImplementationFileFromRowValue, setValidatedImplementationFileFromRowValue] = React.useState<Constants.validate>('error')

  const [implementationFileToRowValue, setImplementationFileToRowValue] = React.useState(formData.implementation_file_to_row)
  const [validatedImplementationFileToRowValue, setValidatedImplementationFileToRowValue] = React.useState<Constants.validate>('error')

  const [messageValue, setMessageValue] = React.useState(formMessage)

  const [statusValue, setStatusValue] = React.useState('waiting')

  const handleDefaultViewChange = () => {
    const radio_dv_rs = document.getElementById('radio-default-view-raw-specification') as HTMLInputElement
    const radio_dv_sr = document.getElementById('radio-default-view-sw-requirements') as HTMLInputElement
    const radio_dv_tc = document.getElementById('radio-default-view-test-cases') as HTMLInputElement
    const radio_dv_ts = document.getElementById('radio-default-view-test-specifications') as HTMLInputElement

    if (radio_dv_rs != null && radio_dv_sr != null && radio_dv_tc != null && radio_dv_ts != null) {
      if (radio_dv_rs.checked) {
        setDefaultViewValue(Constants._RS)
      } else if (radio_dv_sr.checked) {
        setDefaultViewValue(Constants._SRs)
      } else if (radio_dv_tc.checked) {
        setDefaultViewValue(Constants._TCs)
      } else if (radio_dv_ts.checked) {
        setDefaultViewValue(Constants._TSs)
      }
    }
  }

  React.useEffect(() => {
    if (apiValue.trim() === '') {
      setValidatedApiValue('error')
    } else {
      setValidatedApiValue('success')
    }
  }, [apiValue])

  React.useEffect(() => {
    if (libraryValue.trim() === '') {
      setValidatedLibraryValue('error')
    } else {
      setValidatedLibraryValue('success')
    }
  }, [libraryValue])

  React.useEffect(() => {
    if (libraryVersionValue.trim() === '') {
      setValidatedLibraryVersionValue('error')
    } else {
      setValidatedLibraryVersionValue('success')
    }
  }, [libraryVersionValue])

  React.useEffect(() => {
    if (referenceSource == 'url') {
      if (referenceUrl.trim() === '') {
        setValidatedReferenceValue('error')
      } else {
        setValidatedReferenceValue('success')
      }
    } else {
      if (referenceFileName.trim() === '') {
        setValidatedReferenceValue('error')
      } else {
        setValidatedReferenceValue('success')
      }
    }
  }, [referenceUrl, referenceFileName])

  React.useEffect(() => {
    if (implementationFileFromRowValue === '') {
      setValidatedImplementationFileFromRowValue('default')
    } else if (/^\d+$/.test(implementationFileFromRowValue)) {
      setValidatedImplementationFileFromRowValue('success')
    } else {
      setValidatedImplementationFileFromRowValue('error')
    }
  }, [implementationFileFromRowValue])

  React.useEffect(() => {
    if (implementationFileToRowValue === '') {
      setValidatedImplementationFileToRowValue('default')
    } else if (/^\d+$/.test(implementationFileToRowValue)) {
      setValidatedImplementationFileToRowValue('success')
    } else {
      setValidatedImplementationFileToRowValue('error')
    }
  }, [implementationFileToRowValue])

  React.useEffect(() => {
    if (referenceSource == 'user-files' || implementationSource == 'user-files') {
      if (userFiles.length == 0) {
        Constants.loadUserFiles(auth, setUserFiles)
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [referenceSource, implementationSource])

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

  const handleApiValueChange = (_event, value: string) => {
    setApiValue(value)
  }

  const handleLibraryValueChange = (_event, value: string) => {
    setLibraryValue(value)
  }

  const handleLibraryVersionValueChange = (_event, value: string) => {
    setLibraryVersionValue(value)
  }

  const handleReferenceUrlChange = (_event, value: string) => {
    setReferenceUrl(value)
  }

  const handleImplementationUrlChange = (_event, value: string) => {
    setImplementationUrl(value)
  }

  const handleImplementationFileFromRowValueChange = (_event, value: string) => {
    setImplementationFileFromRowValue(value)
  }

  const handleImplementationFileToRowValueChange = (_event, value: string) => {
    setImplementationFileToRowValue(value)
  }

  const handleCategoryValueChange = (_event, value: string) => {
    setCategoryValue(value)
  }

  const handleTagsValueChange = (_event, value: string) => {
    setTagsValue(value)
  }

  const handleReferenceFileNameChange = (_event, value: string) => {
    setReferenceFileName(value)
  }

  const handleImplementationFileNameChange = (_event, value: string) => {
    setImplementationFileName(value)
  }

  const resetForm = () => {
    setReferenceSource('url')
    setImplementationSource('url')
    setApiValue(formData.api)
    setLibraryValue(formData.library)
    setLibraryVersionValue(formAction == 'fork' ? '' : formData.library_version)
    setReferenceUrl(formData.raw_specification_url)
    setCategoryValue(formData.category)
    setDefaultViewValue(formData.default_view)
    setTagsValue(formData.tags)
    setImplementationUrl(formData.implementation_file)
    setImplementationFileFromRowValue(formData.implementation_file_from_row)
    setImplementationFileToRowValue(formData.implementation_file_to_row)
  }

  const handleSubmit = () => {
    if (!auth.isLogged()) {
      setMessageValue('Session expired, please login.')
      return
    }

    if (formVerb == 'POST') {
      {
        /*Only post handled in modal window*/
      }
      if (setModalFormSubmitState != null) {
        setModalFormSubmitState('waiting')
      }
    }

    if (validatedApiValue != 'success') {
      setMessageValue('Software Component Name is mandatory.')
      return
    } else if (validatedLibraryValue != 'success') {
      setMessageValue('Software Component Library is mandatory.')
      return
    } else if (validatedLibraryVersionValue != 'success') {
      setMessageValue('Software Component Library Version is mandatory.')
      return
    } else if (validatedReferenceValue != 'success') {
      setMessageValue('Software Component Specification Url/Path is mandatory.')
      return
    } else if (validatedImplementationFileFromRowValue == 'error') {
      setMessageValue('Wrong value for Implementation File From Row.')
      return
    } else if (validatedImplementationFileToRowValue == 'error') {
      setMessageValue('Wrong value for Implementation File To Row.')
      return
    }

    setMessageValue('')
    const data = {
      action: formAction,
      'api-id': formData.id,
      api: apiValue,
      library: libraryValue,
      'library-version': libraryVersionValue,
      category: categoryValue,
      tags: tagsValue,
      'implementation-file': implementationSource == 'url' ? implementationUrl : implementationFileName,
      'implementation-file-from-row': implementationFileFromRowValue,
      'implementation-file-to-row': implementationFileToRowValue,
      'raw-specification-url': referenceSource == 'url' ? referenceUrl : referenceFileName,
      'user-id': auth.userId,
      token: auth.token
    }

    if (formAction == 'edit') {
      data['default-view'] = defaultViewValue
    }

    fetch(Constants.API_BASE_URL + '/apis', {
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
          if (setModalFormSubmitState != null) {
            setModalFormSubmitState('waiting')
          }
        } else {
          setMessageValue('Database updated!')
          window.location.href = '/?currentLibrary=' + libraryValue
        }
      })
      .catch((err) => {
        setMessageValue(err.toString())
        if (setModalFormSubmitState) {
          setModalFormSubmitState('waiting')
        }
        console.log(err.message)
      })
  }

  return (
    <Form>
      <FormGroup label='Software Component Name' isRequired fieldId={`input-api-${formAction}-api-${formData.id}`}>
        <TextInput
          isRequired
          id={`input-api-${formAction}-api-${formData.id}`}
          name={`input-api-${formAction}-api-${formData.id}`}
          value={apiValue || ''}
          onChange={(_ev, value) => handleApiValueChange(_ev, value)}
        />
        {validatedApiValue !== 'success' && (
          <FormHelperText>
            <HelperText>
              <HelperTextItem variant='error'>{validatedApiValue === 'error' ? 'This field is mandatory' : ''}</HelperTextItem>
            </HelperText>
          </FormHelperText>
        )}
      </FormGroup>
      <FormGroup label='Library' isRequired fieldId={`input-api-${formAction}-library-${formData.id}`}>
        <TextInput
          isRequired
          id={`input-api-${formAction}-library-${formData.id}`}
          name={`input-api-${formAction}-library-${formData.id}`}
          value={libraryValue || ''}
          onChange={(_ev, value) => handleLibraryValueChange(_ev, value)}
        />
        {validatedLibraryValue !== 'success' && (
          <FormHelperText>
            <HelperText>
              <HelperTextItem variant='error'>{validatedLibraryValue === 'error' ? 'This field is mandatory' : ''}</HelperTextItem>
            </HelperText>
          </FormHelperText>
        )}
      </FormGroup>
      <FormGroup label='Library Version' isRequired fieldId={`input-api-${formAction}-library-version-${formData.id}`}>
        <TextInput
          isRequired
          id={`input-api-${formAction}-library-version-${formData.id}`}
          name={`input-api-${formAction}-library-version-${formData.id}`}
          value={libraryVersionValue || ''}
          onChange={(_ev, value) => handleLibraryVersionValueChange(_ev, value)}
        />
        {validatedLibraryVersionValue !== 'success' && (
          <FormHelperText>
            <HelperText>
              <HelperTextItem variant='error'>{validatedLibraryVersionValue === 'error' ? 'This field is mandatory' : ''}</HelperTextItem>
            </HelperText>
          </FormHelperText>
        )}
      </FormGroup>
      <FormGroup
        label='Specification Url/Path (plain text format):'
        isRequired
        fieldId={`input-api-${formAction}-raw-specification-url-${formData.id}`}
        labelIcon={
          referenceSource == 'url' ? (
            <Button variant='link' onClick={() => setReferenceSource('user-files')}>
              From user files
            </Button>
          ) : (
            <Button variant='link' onClick={() => setReferenceSource('url')}>
              From url
            </Button>
          )
        }
      >
        {referenceSource == 'url' ? (
          <TextInput
            isRequired
            id={`input-api-${formAction}-raw-specification-url-${formData.id}`}
            name={`input-api-${formAction}-raw-specification-url-${formData.id}`}
            value={referenceUrl || ''}
            onChange={(_ev, value) => handleReferenceUrlChange(_ev, value)}
          />
        ) : (
          <FormSelect
            value={referenceFileName}
            id={`select-api-${formAction}-raw-specification-path-${formData.id}`}
            onChange={handleReferenceFileNameChange}
            aria-label='Software specification from user file'
          >
            <FormSelectOption key={0} value={''} label={'Select a file from the list'} />
            {userFiles.map((userFile, index) => (
              <FormSelectOption key={index + 1} value={userFile['filepath']} label={userFile['filename']} />
            ))}
          </FormSelect>
        )}
        {validatedReferenceValue !== 'success' && (
          <FormHelperText>
            <HelperText>
              <HelperTextItem variant='error'>{validatedReferenceValue === 'error' ? 'This field is mandatory' : ''}</HelperTextItem>
            </HelperText>
          </FormHelperText>
        )}
      </FormGroup>
      <FormGroup label='Category:' fieldId={`input-api-${formAction}-category-${formData.id}`}>
        <TextInput
          isRequired
          id={`input-api-${formAction}-category-${formData.id}`}
          name={`input-api-${formAction}-category-${formData.id}`}
          value={categoryValue || ''}
          onChange={(_ev, value) => handleCategoryValueChange(_ev, value)}
        />
      </FormGroup>
      <FormGroup
        label='Implementation file Url/Path:'
        fieldId={`input-api-${formAction}-implementation-file-${formData.id}`}
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
          <TextInput
            isRequired
            id={`input-api-${formAction}-implementation-file-${formData.id}`}
            name={`input-api-${formAction}-implementation-file-${formData.id}`}
            value={implementationUrl || ''}
            onChange={(_ev, value) => handleImplementationUrlChange(_ev, value)}
          />
        ) : (
          <FormSelect
            value={implementationFileName}
            id={`select-api-${formAction}-implementation-file-path-${formData.id}`}
            onChange={handleImplementationFileNameChange}
            aria-label='Implementation from user file'
          >
            <FormSelectOption key={0} value={''} label={'Select a file from the list'} />
            {userFiles.map((userFile, index) => (
              <FormSelectOption key={index + 1} value={userFile['filepath']} label={userFile['filename']} />
            ))}
          </FormSelect>
        )}
      </FormGroup>
      <FormGroup
        label='Implementation file from row number:'
        fieldId={`input-api-${formAction}-implementation-file-from-row-${formData.id}`}
      >
        <TextInput
          id={`input-api-${formAction}-implementation-file-from-row-${formData.id}`}
          name={`input-api-${formAction}-implementation-file-from-row-${formData.id}`}
          value={implementationFileFromRowValue || ''}
          onChange={(_ev, value) => handleImplementationFileFromRowValueChange(_ev, value)}
        />
        {validatedImplementationFileFromRowValue !== 'success' && (
          <FormHelperText>
            <HelperText>
              <HelperTextItem variant='error'>
                {validatedImplementationFileFromRowValue === 'error' ? 'Must be a number' : ''}
              </HelperTextItem>
            </HelperText>
          </FormHelperText>
        )}
      </FormGroup>
      <FormGroup label='Implementation file to row number:' fieldId={`input-api-${formAction}-implementation-file-to-row-${formData.id}`}>
        <TextInput
          id={`input-api-${formAction}-implementation-file-to-row-${formData.id}`}
          name={`input-api-${formAction}-implementation-file-to-row-${formData.id}`}
          value={implementationFileToRowValue || ''}
          onChange={(_ev, value) => handleImplementationFileToRowValueChange(_ev, value)}
        />
        {validatedImplementationFileToRowValue !== 'success' && (
          <FormHelperText>
            <HelperText>
              <HelperTextItem variant='error'>{validatedImplementationFileToRowValue === 'error' ? 'Must be a number' : ''}</HelperTextItem>
            </HelperText>
          </FormHelperText>
        )}
      </FormGroup>
      <FormGroup label='Tags:' fieldId={`input-api-${formAction}-tags-${formData.id}`}>
        <TextInput
          id={`input-api-${formAction}-tags-${formData.id}`}
          name={`input-api-${formAction}-tags-${formData.id}`}
          value={tagsValue || ''}
          onChange={(_ev, value) => handleTagsValueChange(_ev, value)}
        />
      </FormGroup>

      {formAction == 'edit' ? (
        <FormGroup>
          <Flex>
            <FlexItem>
              <Text>Default View:</Text>
            </FlexItem>
            <FlexItem>
              <Radio
                isChecked={defaultViewValue == Constants._RS}
                name='radio-default-view'
                onChange={handleDefaultViewChange}
                label='Raw Specification'
                id='radio-default-view-raw-specification'
              ></Radio>
              <Radio
                isChecked={defaultViewValue == Constants._SRs || defaultViewValue == '' || defaultViewValue == null}
                name='radio-default-view'
                onChange={handleDefaultViewChange}
                label='Sw Requirements'
                id='radio-default-view-sw-requirements'
              ></Radio>
              <Radio
                isChecked={defaultViewValue == Constants._TCs}
                name='radio-default-view'
                onChange={handleDefaultViewChange}
                label='Test Cases'
                id='radio-default-view-test-cases'
              ></Radio>
              <Radio
                isChecked={defaultViewValue == Constants._TSs}
                name='radio-default-view'
                onChange={handleDefaultViewChange}
                label='Test Specifications'
                id='radio-default-view-test-specifications'
              ></Radio>
            </FlexItem>
          </Flex>
        </FormGroup>
      ) : (
        ''
      )}

      {messageValue ? (
        <Hint>
          <HintBody>{messageValue}</HintBody>
        </Hint>
      ) : (
        <span></span>
      )}

      {formDefaultButtons ? (
        <ActionGroup>
          <Button id='btn-api-form-submit' variant='primary' onClick={() => setStatusValue('submitted')}>
            Submit
          </Button>
          <Button id='btn-api-form-reset' variant='secondary' onClick={() => resetForm()}>
            Reset
          </Button>
        </ActionGroup>
      ) : (
        <span></span>
      )}
    </Form>
  )
}
