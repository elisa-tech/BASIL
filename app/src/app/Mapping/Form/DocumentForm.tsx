import React from 'react'
import * as Constants from '../../Constants/constants'
import {
  ActionGroup,
  Button,
  CodeBlock,
  CodeBlockCode,
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

export interface DocumentFormProps {
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

export const DocumentForm: React.FunctionComponent<DocumentFormProps> = ({
  api,
  formAction = 'add',
  formData = Constants.docFormEmpty,
  formDefaultButtons = 1,
  formMessage = '',
  formVerb,
  handleModalToggle,
  loadMappingData,
  modalFormSubmitState = 'waiting',
  modalOffset,
  modalSection,
  parentData
}: DocumentFormProps) => {
  const auth = useAuth()
  const [descriptionValue, setDescriptionValue] = React.useState(formData.description)
  const [SPDXRelationValue, setSPDXRelationValue] = React.useState(formData.spdx_relation)
  const [documentContentValue, setDocumentContentValue] = React.useState('')
  const [titleValue, setTitleValue] = React.useState(formData.title)
  const [urlValue, setUrlValue] = React.useState(formData.url)
  const [offsetValue, setOffsetValue] = React.useState(formData.offset)
  const [sectionValue, setSectionValue] = React.useState(formData.section)
  const [validatedDescriptionValue, setValidatedDescriptionValue] = React.useState<Constants.validate>('error')
  const [validatedTitleValue, setValidatedTitleValue] = React.useState<Constants.validate>('error')
  const [validatedUrlValue, setValidatedUrlValue] = React.useState<Constants.validate>('error')
  const [coverageValue, setCoverageValue] = React.useState(formData.coverage)
  const [validatedCoverageValue, setValidatedCoverageValue] = React.useState<Constants.validate>('error')
  const [documentStatusValue, setDocumentStatusValue] = React.useState(formData.status)
  const [documentTypeValue, setDocumentTypeValue] = React.useState(formData.document_type)
  const [validatedOffsetValue, setValidatedOffsetValue] = React.useState<Constants.validate>('error')
  const [validatedSectionValue, setValidatedSectionValue] = React.useState<Constants.validate>('error')
  const [messageValue, setMessageValue] = React.useState(formMessage)
  const [statusValue, setStatusValue] = React.useState('waiting')

  const resetForm = () => {
    setDescriptionValue('')
    setTitleValue('')
    setUrlValue('')
    setSectionValue('')
    setOffsetValue(0)
    setSPDXRelationValue('')
    setCoverageValue('100')
    setDocumentContentValue('')
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
    if (urlValue == undefined) {
      setUrlValue('')
    } else {
      if (urlValue.trim() === '') {
        setValidatedUrlValue('error')
      } else {
        setValidatedUrlValue('success')
      }
    }
  }, [urlValue])

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

  React.useEffect(() => {
    if (sectionValue.trim() === '') {
      setValidatedSectionValue('error')
    } else {
      setValidatedSectionValue('success')
    }
  }, [sectionValue])

  React.useEffect(() => {
    if (offsetValue === '') {
      setValidatedOffsetValue('default')
    } else if (/^\d+$/.test(offsetValue)) {
      if (offsetValue >= 0 && offsetValue <= documentContentValue.length) {
        setValidatedOffsetValue('success')
      } else {
        setValidatedOffsetValue('error')
      }
    } else {
      setValidatedOffsetValue('error')
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [offsetValue])

  const handleDescriptionValueChange = (_event, value: string) => {
    setDescriptionValue(value)
  }

  const handleTitleValueChange = (_event, value: string) => {
    setTitleValue(value)
  }

  const handleUrlValueChange = (_event, value: string) => {
    setUrlValue(value)
  }

  const handleSPDXRelationValueChange = (_event, value: string) => {
    setSPDXRelationValue(value)
  }

  const handleSectionValueChange = () => {
    const currentSelection = getSelection()?.toString() as string | ''
    if (currentSelection != '') {
      // eslint-disable-next-line  @typescript-eslint/no-explicit-any
      if (((getSelection()?.anchorNode?.parentNode as any)?.id as string | '') == 'div-document-${formAction}-content-${formData.id}') {
        setSectionValue(currentSelection)
        // eslint-disable-next-line  @typescript-eslint/no-explicit-any
        setOffsetValue(Math.min((getSelection() as any)?.baseOffset, (getSelection() as any)?.extentOffset))
      }
    }
  }

  const handleCoverageValueChange = (_event, value: string) => {
    setCoverageValue(value)
  }

  const handleDocumentStatusChange = (_event, value: string) => {
    setDocumentStatusValue(value)
  }

  const handleDocumentTypeChange = (_event, value: string) => {
    setDocumentTypeValue(value)
  }

  const handleSubmit = () => {
    if (validatedDescriptionValue != 'success') {
      setMessageValue('Document Description is mandatory.')
      setStatusValue('waiting')
      return
    } else if (validatedTitleValue != 'success') {
      setMessageValue('Document Title is mandatory.')
      setStatusValue('waiting')
      return
    } else if (validatedUrlValue != 'success') {
      setMessageValue('Document Url is mandatory.')
      setStatusValue('waiting')
      return
    } else if (validatedCoverageValue != 'success') {
      setMessageValue('Document Coverage is mandatory and must be a integer value in the range 0-100.')
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
      document: {
        title: titleValue,
        description: descriptionValue,
        document_type: documentTypeValue,
        url: urlValue,
        spdx_relation: SPDXRelationValue,
        offset: offsetValue,
        section: sectionValue
      },
      section: modalSection,
      offset: modalOffset,
      coverage: coverageValue,
      'user-id': auth.userId,
      token: auth.token
    }

    if (formVerb == 'PUT' || formVerb == 'DELETE') {
      data['relation-id'] = parentData.relation_id
      data['document']['id'] = formData.id
    }

    if (formVerb == 'PUT') {
      data['document']['status'] = documentStatusValue
    }

    fetch(Constants.API_BASE_URL + '/mapping/api/documents', {
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

  const readRemoteTextFile = () => {
    if (documentTypeValue != 'text') {
      return
    }

    let url = Constants.API_BASE_URL + '/remote-documents?url=' + urlValue
    url += '&api-id=' + api.id

    if (auth.isLogged()) {
      url += '&user-id=' + auth.userId + '&token=' + auth.token
    } else {
      return
    }

    fetch(url)
      .then((res) => res.json())
      .then((data) => {
        setDocumentContentValue(data['content'])
      })
      .catch((err) => {
        console.log(err.message)
      })
  }

  const setSectionAsUnmatching = () => {
    const unmatching_section = '?????????'
    const unmatching_offset = 0
    setSectionValue(unmatching_section)
    setOffsetValue(unmatching_offset)
  }

  const setSectionAsFullDocument = () => {
    setSectionValue(documentContentValue)
    setOffsetValue(0)
  }

  return (
    <Form>
      {formAction == 'edit' ? (
        <FormGroup label='Status' isRequired fieldId={`input-document-${formAction}-status-${formData.id}`}>
          <FormSelect
            value={documentStatusValue}
            id={`input-document-${formAction}-status-${formData.id}`}
            onChange={handleDocumentStatusChange}
            aria-label='Document Status Input'
          >
            {Constants.status_options.map((option, index) => (
              <FormSelectOption isDisabled={option.disabled} key={index} value={option.value} label={option.label} />
            ))}
          </FormSelect>
        </FormGroup>
      ) : (
        ''
      )}
      <FormGroup label='Title' isRequired fieldId={`input-document-${formAction}-title-${formData.id}`}>
        <TextInput
          isRequired
          id={`input-document-${formAction}-title-${formData.id}`}
          name={`input-document-${formAction}-title-${formData.id}`}
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
      <FormGroup label='Description' isRequired fieldId={`input-document-${formAction}-description-${formData.id}`}>
        <TextArea
          isRequired
          resizeOrientation='vertical'
          aria-label='Document description field'
          id={`input-document-${formAction}-description-${formData.id}`}
          name={`input-document-${formAction}-description-${formData.id}`}
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
      <FormGroup label='Type' isRequired fieldId={`input-document-${formAction}-type-${formData.id}`}>
        <FormSelect
          value={documentTypeValue}
          id={`input-document-${formAction}-type-${formData.id}`}
          onChange={handleDocumentTypeChange}
          aria-label='Document Type Input'
        >
          {Constants.document_type.map((option, index) => (
            <FormSelectOption isDisabled={option.disabled} key={index} value={option.value} label={option.label} />
          ))}
        </FormSelect>
      </FormGroup>
      <FormGroup label='SPDX Relation' isRequired fieldId={`input-document-${formAction}-spdx-relation-${formData.id}`}>
        <FormSelect
          value={SPDXRelationValue}
          id={`input-document-${formAction}-spdx-relation-${formData.id}`}
          onChange={handleSPDXRelationValueChange}
          aria-label='SPDX Relation Input'
        >
          {Constants.spdx_relations.map((option, index) => (
            <FormSelectOption isDisabled={option.disabled} key={index} value={option.value} label={option.label} />
          ))}
        </FormSelect>
      </FormGroup>
      <FormGroup label='Url' isRequired fieldId={`input-document-${formAction}-url-${formData.id}`}>
        <TextInput
          isRequired
          id={`input-document-${formAction}-url-${formData.id}`}
          name={`input-document-${formAction}-url-${formData.id}`}
          value={urlValue || ''}
          onChange={(_ev, value) => handleUrlValueChange(_ev, value)}
          onBlur={readRemoteTextFile}
        />
        {validatedUrlValue !== 'success' && (
          <FormHelperText>
            <HelperText>
              <HelperTextItem variant='error'>{validatedUrlValue === 'error' ? 'This field is mandatory' : ''}</HelperTextItem>
            </HelperText>
          </FormHelperText>
        )}
      </FormGroup>
      {documentTypeValue == 'text' ? (
        <React.Fragment>
          <FormGroup
            label='Section (automatically populated based on your selection)'
            fieldId={`input-document-${formAction}-section-${formData.id}`}
          >
            <TextArea
              isDisabled
              resizeOrientation='vertical'
              aria-label='Section preview field'
              id={`input-document-section`}
              name={`input-document-section`}
              value={sectionValue || ''}
              onChange={handleSectionValueChange}
            />
            {validatedSectionValue !== 'success' && (
              <FormHelperText>
                <HelperText>
                  <HelperTextItem variant='error'>{validatedSectionValue === 'error' ? 'This field is mandatory' : ''}</HelperTextItem>
                </HelperText>
              </FormHelperText>
            )}
          </FormGroup>
          <FormGroup
            label='Offset (automatically populated based on your selection)'
            fieldId={`input-document-${formAction}-offset-${formData.id}`}
          >
            <TextInput
              isDisabled
              id={`input-document-${formAction}-offset-${formData.id}`}
              name={`input-document-${formAction}-offset-${formData.id}`}
              value={offsetValue}
              //onChange={(_ev, value) => handleOffsetValueChange(_ev, value)}
            />
            {validatedOffsetValue !== 'success' && (
              <FormHelperText>
                <HelperText>
                  <HelperTextItem variant='error'>{validatedOffsetValue === 'error' ? 'Must be an integer number' : ''}</HelperTextItem>
                </HelperText>
              </FormHelperText>
            )}
          </FormGroup>
          <FormGroup>
            Select a section of the document or
            <Button id={`btn-document-${formAction}-section-set-unmatching-${formData.id}`} variant='link' onClick={setSectionAsUnmatching}>
              Set as unmatching
            </Button>
            or
            <Button id={`btn-document-${formAction}-section-set-full-${formData.id}`} variant='link' onClick={setSectionAsFullDocument}>
              Set as Full Document
            </Button>
          </FormGroup>
          <CodeBlock className='code-block-bg-green'>
            <CodeBlockCode>
              <div onMouseUp={handleSectionValueChange} id={'div-document-${formAction}-content-${formData.id}'} data-offset={offsetValue}>
                {documentContentValue}
              </div>
            </CodeBlockCode>
          </CodeBlock>
        </React.Fragment>
      ) : (
        ''
      )}
      <FormGroup label='Unique Coverage:' isRequired fieldId={`input-document-${formAction}-coverage-${formData.id}`}>
        <TextInput
          isRequired
          id={`input-document-${formAction}-coverage-${formData.id}`}
          name={`input-document-${formAction}-coverage-${formData.id}`}
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
          <Button id='btn-mapping-document-submit' variant='primary' onClick={() => setStatusValue('submitted')}>
            Submit
          </Button>
          <Button id='btn-mapping-document-reset' variant='secondary' onClick={resetForm}>
            Reset
          </Button>
        </ActionGroup>
      ) : (
        <span></span>
      )}
    </Form>
  )
}
