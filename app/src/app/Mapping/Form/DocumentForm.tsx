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
  modalIndirect
  modalOffset
  modalSection
  parentData
  parentRelatedToType
  parentType
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
  modalIndirect,
  modalOffset,
  modalSection,
  parentData,
  parentRelatedToType,
  parentType
}: DocumentFormProps) => {
  const auth = useAuth()
  const [userFiles, setUserFiles] = React.useState([])
  const [documentSource, setDocumentSource] = React.useState('url')
  const [documentFileNameValue, setDocumentFileNameValue] = React.useState('')
  const [documentUrlValue, setDocumentUrlValue] = React.useState(formData.url)
  const [validatedDocumentSourceValue, setValidatedvalidatedDocumentSourceValue] = React.useState<Constants.validate>('error')
  const [descriptionValue, setDescriptionValue] = React.useState(formData.description)
  const [SPDXRelationValue, setSPDXRelationValue] = React.useState(formData.spdx_relation)
  const [validatedSPDXRelationValue, setValidatedSPDXRelationValue] = React.useState<Constants.validate>('error')
  const [documentContentValue, setDocumentContentValue] = React.useState('')
  const [titleValue, setTitleValue] = React.useState(formData.title)
  const [offsetValue, setOffsetValue] = React.useState(formData.offset)
  const [sectionValue, setSectionValue] = React.useState(formData.section)
  const [validatedDescriptionValue, setValidatedDescriptionValue] = React.useState<Constants.validate>('error')
  const [validatedTitleValue, setValidatedTitleValue] = React.useState<Constants.validate>('error')
  const [coverageValue, setCoverageValue] = React.useState(formData.coverage)
  const [validatedCoverageValue, setValidatedCoverageValue] = React.useState<Constants.validate>('error')
  const [documentStatusValue, setDocumentStatusValue] = React.useState(formData.status)
  const [documentTypeValue, setDocumentTypeValue] = React.useState(formData.document_type)
  const [validatedOffsetValue, setValidatedOffsetValue] = React.useState<Constants.validate>('error')
  const [validatedSectionValue, setValidatedSectionValue] = React.useState<Constants.validate>('error')
  const [messageValue, setMessageValue] = React.useState(formMessage)
  const [statusValue, setStatusValue] = React.useState('waiting')

  const resetForm = () => {
    setDocumentSource('url')
    setDescriptionValue('')
    setTitleValue('')
    setDocumentUrlValue('')
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
    if (SPDXRelationValue.trim() === '') {
      setValidatedSPDXRelationValue('error')
    } else {
      setValidatedSPDXRelationValue('success')
    }
  }, [SPDXRelationValue])

  React.useEffect(() => {
    if (validatedDocumentSourceValue == 'success') {
      readFileContent()
    }
  }, [documentTypeValue])

  React.useEffect(() => {
    if (documentSource == 'url') {
      if (documentUrlValue == undefined) {
        setDocumentUrlValue('')
      } else {
        if (documentUrlValue.trim() === '') {
          setValidatedvalidatedDocumentSourceValue('error')
        } else {
          setValidatedvalidatedDocumentSourceValue('success')
          readFileContent()
        }
      }
    } else {
      if (documentFileNameValue.trim() === '') {
        setValidatedvalidatedDocumentSourceValue('error')
      } else {
        setValidatedvalidatedDocumentSourceValue('success')
        readFileContent()
      }
    }
  }, [documentUrlValue, documentFileNameValue])

  React.useEffect(() => {
    if (documentSource == 'user-files') {
      if (userFiles.length == 0) {
        Constants.loadUserFiles(auth, setUserFiles)
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [documentSource])

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

  React.useEffect(() => {
    if (sectionValue == undefined || sectionValue == null) {
      setValidatedSectionValue('error')
    } else {
      if (sectionValue.trim() === '') {
        setValidatedSectionValue('error')
      } else {
        setValidatedSectionValue('success')
      }
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
    setDocumentUrlValue(value)
  }

  const handleSPDXRelationValueChange = (_event, value: string) => {
    setSPDXRelationValue(value)
  }

  const handleSectionValueChange = () => {
    const currentSelection = getSelection()?.toString() as string | ''
    if (currentSelection != '') {
      // eslint-disable-next-line  @typescript-eslint/no-explicit-any
      if (((getSelection()?.anchorNode?.parentNode as any)?.id as string | '') == 'div-document-${formAction}-content-${formData.id}') {
        const currentOffset = Constants.getSelectionOffset()
        if (currentOffset > -1) {
          setSectionValue(currentSelection)
          setOffsetValue(currentOffset)
        }
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

  const handleDocumentFileNameChange = (_event, value: string) => {
    setDocumentFileNameValue(value)
  }

  const handleSubmit = () => {
    if (validatedTitleValue != 'success') {
      setMessageValue('Document Title is mandatory.')
      setStatusValue('waiting')
      return
    }
    if (validatedDescriptionValue != 'success') {
      setMessageValue('Document Description is mandatory.')
      setStatusValue('waiting')
      return
    }
    if (validatedSPDXRelationValue != 'success') {
      setMessageValue('Relationship is mandatory.')
      setStatusValue('waiting')
      return
    }
    if (validatedDocumentSourceValue != 'success') {
      setMessageValue('Document url or filename is mandatory.')
      setStatusValue('waiting')
      return
    }
    if (documentTypeValue == 'text') {
      if (validatedSectionValue != 'success') {
        setMessageValue('Section of the document is mandatory.')
        setStatusValue('waiting')
        return
      }
    }
    if (validatedCoverageValue != 'success') {
      setMessageValue('Document Coverage is mandatory and must be a integer value in the range 0-100.')
      setStatusValue('waiting')
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
      document: {
        title: titleValue,
        description: descriptionValue,
        'document-type': documentTypeValue,
        url: documentSource == 'url' ? documentUrlValue : documentFileNameValue,
        'spdx-relation': SPDXRelationValue,
        offset: offsetValue,
        section: sectionValue
      },
      section: modalSection,
      offset: modalOffset,
      coverage: coverageValue,
      'user-id': auth.userId,
      token: auth.token
    }

    if (modalIndirect == true) {
      data['relation-id'] = parentData.relation_id
      data['relation-to'] = parentRelatedToType
      data['parent-document'] = { id: parentData[Constants._D]['id'] }
    } else {
      if (formVerb == 'PUT' || formVerb == 'DELETE') {
        data[Constants._D]['id'] = formData.id
        data['relation-id'] = parentData.relation_id
      }
    }

    if (formVerb == 'PUT') {
      data[Constants._D]['status'] = documentStatusValue
    }

    let status: number = 0
    let status_text: string = ''

    fetch(Constants.API_BASE_URL + '/mapping/' + parentType + '/documents', {
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

  const readFileContent = () => {
    // In case of text file read the content
    // to let the user able to select the snippet
    if (documentTypeValue != 'text') {
      return
    }

    if (documentSource == 'url') {
      readRemoteTextFile()
    } else {
      Constants.loadFileContent(auth, documentFileNameValue, setMessageValue, setDocumentContentValue)
    }
  }

  const readRemoteTextFile = () => {
    let url = Constants.API_BASE_URL + '/remote-documents?url=' + documentUrlValue
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
    <Form
      onSubmit={(event) => {
        event.preventDefault()
      }}
    >
      {formAction == 'edit' ? (
        <FormGroup label='Status' isRequired fieldId={`input-document-${formAction}-status-${formData.id}`}>
          <FormSelect
            value={documentStatusValue}
            id={`input-document-${formAction}-status-${formData.id}`}
            onChange={(event, value) => handleDocumentStatusChange(event, value)}
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
          value={titleValue}
          maxLength={200}
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
          value={descriptionValue}
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
      <FormGroup label='Type' isRequired fieldId={`select-document-${formAction}-type-${formData.id}`}>
        <FormSelect
          value={documentTypeValue}
          id={`select-document-${formAction}-type-${formData.id}`}
          onChange={(event, value) => handleDocumentTypeChange(event, value)}
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
          id={`select-document-${formAction}-spdx-relation-${formData.id}`}
          onChange={(event, value) => handleSPDXRelationValueChange(event, value)}
          aria-label='SPDX Relation Input'
        >
          {Constants.spdx_relations.map((option, index) => (
            <FormSelectOption isDisabled={option.disabled} key={index} value={option.value} label={option.label} />
          ))}
        </FormSelect>
      </FormGroup>
      <FormGroup
        label='Url'
        isRequired
        fieldId={`input-document-${formAction}-url-${formData.id}`}
        labelIcon={
          documentSource == 'url' ? (
            <Button variant='link' onClick={() => setDocumentSource('user-files')}>
              From user files
            </Button>
          ) : (
            <Button variant='link' onClick={() => setDocumentSource('url')}>
              From url
            </Button>
          )
        }
      >
        {documentSource == 'url' ? (
          <TextInput
            isRequired
            id={`input-document-${formAction}-url-${formData.id}`}
            value={documentUrlValue}
            onChange={(_ev, value) => handleUrlValueChange(_ev, value)}
            onBlur={() => readFileContent()}
          />
        ) : (
          <FormSelect
            value={documentFileNameValue}
            id={`select-document-${formAction}-file-${formData.id}`}
            onChange={(event, value) => handleDocumentFileNameChange(event, value)}
            aria-label='Document from user file'
          >
            <FormSelectOption key={0} value={''} label={'Select a file from the list'} />
            {userFiles.map((userFile, index) => (
              <FormSelectOption key={index + 1} value={userFile['filepath']} label={userFile['filename']} />
            ))}
          </FormSelect>
        )}
        {validatedDocumentSourceValue !== 'success' && (
          <FormHelperText>
            <HelperText>
              <HelperTextItem variant='error'>{validatedDocumentSourceValue === 'error' ? 'This field is mandatory' : ''}</HelperTextItem>
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
              rows={10}
              resizeOrientation='vertical'
              aria-label='Section preview field'
              id={`input-document-${formAction}-section-${formData.id}`}
              value={sectionValue}
              onChange={(event, value) => handleSectionValueChange()}
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
            <Button
              id={`btn-document-${formAction}-section-set-unmatching-${formData.id}`}
              variant='link'
              onClick={() => setSectionAsUnmatching()}
            >
              Set as unmatching
            </Button>
            or
            <Button
              id={`btn-document-${formAction}-section-set-full-${formData.id}`}
              variant='link'
              onClick={() => setSectionAsFullDocument()}
            >
              Set as Full Document
            </Button>
            -
            <Button id={`btn-document-${formAction}-load-file-content-${formData.id}`} variant='link' onClick={() => readFileContent()}>
              Load file content
            </Button>
          </FormGroup>
          <CodeBlock className='code-block-bg-green'>
            <CodeBlockCode>
              <div
                onMouseUp={() => handleSectionValueChange()}
                id={'div-document-${formAction}-content-${formData.id}'}
                data-offset={offsetValue}
              >
                {documentContentValue}
              </div>
            </CodeBlockCode>
          </CodeBlock>
        </React.Fragment>
      ) : (
        ''
      )}
      <FormGroup label={Constants.FORM_COMPLETION_LABEL} isRequired fieldId={`input-document-${formAction}-coverage-${formData.id}`}>
        <TextInput
          isRequired
          id={`input-document-${formAction}-coverage-${formData.id}`}
          value={coverageValue}
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
