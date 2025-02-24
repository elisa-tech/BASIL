import React from 'react'
import {
  Button,
  DescriptionList,
  DescriptionListDescription,
  DescriptionListGroup,
  DescriptionListTerm,
  Form,
  FormGroup,
  FormHelperText,
  HelperText,
  HelperTextItem,
  Hint,
  HintBody,
  Modal,
  ModalVariant,
  TextInput
} from '@patternfly/react-core'
import * as Constants from '@app/Constants/constants'

export interface checkSpecResultsProps {
  checkResultData
}

export const CheckSpecResults: React.FunctionComponent<checkSpecResultsProps> = ({ checkResultData = null }: checkSpecResultsProps) => {
  const [showSwRequirementsOk, setShowSwRequirementsOk] = React.useState(false)
  const [showSwRequirementsKo, setShowSwRequirementsKo] = React.useState(false)
  const [showSwRequirementsWarning, setShowSwRequirementsWarning] = React.useState(false)
  const [showTestSpecificationsOk, setShowTestSpecificationsOk] = React.useState(false)
  const [showTestSpecificationsKo, setShowTestSpecificationsKo] = React.useState(false)
  const [showTestSpecificationsWarning, setShowTestSpecificationsWarning] = React.useState(false)
  const [showTestCasesOk, setShowTestCasesOk] = React.useState(false)
  const [showTestCasesKo, setShowTestCasesKo] = React.useState(false)
  const [showTestCasesWarning, setShowTestCasesWarning] = React.useState(false)
  const [showJustificationsOk, setShowJustificationsOk] = React.useState(false)
  const [showJustificationsKo, setShowJustificationsKo] = React.useState(false)
  const [showJustificationsWarning, setShowJustificationsWarning] = React.useState(false)
  const [showDocumentsOk, setShowDocumentsOk] = React.useState(false)
  const [showDocumentsKo, setShowDocumentsKo] = React.useState(false)
  const [showDocumentsWarning, setShowDocumentsWarning] = React.useState(false)

  React.useEffect(() => {
    setShowSwRequirementsOk(false)
    setShowSwRequirementsKo(false)
    setShowSwRequirementsWarning(false)
    setShowTestSpecificationsOk(false)
    setShowTestSpecificationsKo(false)
    setShowTestSpecificationsWarning(false)
    setShowTestCasesOk(false)
    setShowTestCasesKo(false)
    setShowTestCasesWarning(false)
    setShowJustificationsOk(false)
    setShowJustificationsKo(false)
    setShowJustificationsWarning(false)
    setShowDocumentsOk(false)
    setShowDocumentsKo(false)
    setShowDocumentsWarning(false)

    if (checkResultData['sw-requirements']['ok'].length > 0) {
      setShowSwRequirementsOk(true)
    }
    if (checkResultData['sw-requirements']['ko'].length > 0) {
      setShowSwRequirementsKo(true)
    }
    if (checkResultData['sw-requirements']['warning'].length > 0) {
      setShowSwRequirementsWarning(true)
    }

    if (checkResultData['test-specifications']['ok'].length > 0) {
      setShowTestSpecificationsOk(true)
    }
    if (checkResultData['test-specifications']['ko'].length > 0) {
      setShowTestSpecificationsKo(true)
    }
    if (checkResultData['test-specifications']['warning'].length > 0) {
      setShowTestSpecificationsWarning(true)
    }

    if (checkResultData['test-cases']['ok'].length > 0) {
      setShowTestCasesOk(true)
    }
    if (checkResultData['test-cases']['ko'].length > 0) {
      setShowTestCasesKo(true)
    }
    if (checkResultData['test-cases']['warning'].length > 0) {
      setShowTestCasesWarning(true)
    }

    if (checkResultData['justifications']['ok'].length > 0) {
      setShowJustificationsOk(true)
    }
    if (checkResultData['justifications']['ko'].length > 0) {
      setShowJustificationsKo(true)
    }
    if (checkResultData['justifications']['warning'].length > 0) {
      setShowJustificationsWarning(true)
    }

    if (checkResultData['documents']['ok'].length > 0) {
      setShowDocumentsOk(true)
    }
    if (checkResultData['documents']['ko'].length > 0) {
      setShowDocumentsKo(true)
    }
    if (checkResultData['documents']['warning'].length > 0) {
      setShowDocumentsWarning(true)
    }
  }, [checkResultData])

  return (
    <React.Fragment>
      <DescriptionList>
        <DescriptionListGroup>
          <DescriptionListTerm>SW Requirements</DescriptionListTerm>
          {showSwRequirementsOk ? <DescriptionListTerm> * OK</DescriptionListTerm> : <span></span>}
          {checkResultData['sw-requirements']['ok'].map((item, index) => (
            <DescriptionListDescription key={index}>
              {item.id} - {item.title}
            </DescriptionListDescription>
          ))}
          {showSwRequirementsKo ? <DescriptionListTerm> * KO</DescriptionListTerm> : <span></span>}
          {checkResultData['sw-requirements']['ko'].map((item, index) => (
            <DescriptionListDescription key={index}>
              {item.id} - {item.title}
            </DescriptionListDescription>
          ))}
          {showSwRequirementsWarning ? <DescriptionListTerm> * WARNING</DescriptionListTerm> : <span></span>}
          {checkResultData['sw-requirements']['warning'].map((item, index) => (
            <DescriptionListDescription key={index}>
              {item.id} - {item.title}
            </DescriptionListDescription>
          ))}
        </DescriptionListGroup>

        <DescriptionListGroup>
          <DescriptionListTerm>Test Specifications</DescriptionListTerm>
          {showTestSpecificationsOk ? <DescriptionListTerm> * OK</DescriptionListTerm> : <span></span>}
          {checkResultData['test-specifications']['ok'].map((item, index) => (
            <DescriptionListDescription key={index}>
              {item.id} - {item.title}
            </DescriptionListDescription>
          ))}
          {showTestSpecificationsKo ? <DescriptionListTerm> * KO</DescriptionListTerm> : <span></span>}
          {checkResultData['test-specifications']['ko'].map((item, index) => (
            <DescriptionListDescription key={index}>
              {item.id} - {item.title}
            </DescriptionListDescription>
          ))}
          {showTestSpecificationsWarning ? <DescriptionListTerm> * WARNING</DescriptionListTerm> : <span></span>}
          {checkResultData['test-specifications']['warning'].map((item, index) => (
            <DescriptionListDescription key={index}>
              {item.id} - {item.title}
            </DescriptionListDescription>
          ))}
        </DescriptionListGroup>

        <DescriptionListGroup>
          <DescriptionListTerm>Test Cases</DescriptionListTerm>
          {showTestCasesOk ? <DescriptionListTerm> * OK</DescriptionListTerm> : <span></span>}
          {checkResultData['test-cases']['ok'].map((item, index) => (
            <DescriptionListDescription key={index}>
              {item.id} - {item.title}
            </DescriptionListDescription>
          ))}
          {showTestCasesKo ? <DescriptionListTerm> * KO</DescriptionListTerm> : <span></span>}
          {checkResultData['test-cases']['ko'].map((item, index) => (
            <DescriptionListDescription key={index}>
              {item.id} - {item.title}
            </DescriptionListDescription>
          ))}
          {showTestCasesWarning ? <DescriptionListTerm> * WARNING</DescriptionListTerm> : <span></span>}
          {checkResultData['test-cases']['warning'].map((item, index) => (
            <DescriptionListDescription key={index}>
              {item.id} - {item.title}
            </DescriptionListDescription>
          ))}
        </DescriptionListGroup>

        <DescriptionListGroup>
          <DescriptionListTerm>Other Justifications</DescriptionListTerm>
          {showJustificationsOk ? <DescriptionListTerm> * OK</DescriptionListTerm> : <span></span>}
          {checkResultData['justifications']['ok'].map((item, index) => (
            <DescriptionListDescription key={index}>
              {item.id} - {item.title}
            </DescriptionListDescription>
          ))}
          {showJustificationsKo ? <DescriptionListTerm> * KO</DescriptionListTerm> : <span></span>}
          {checkResultData['justifications']['ko'].map((item, index) => (
            <DescriptionListDescription key={index}>
              {item.id} - {item.title}
            </DescriptionListDescription>
          ))}
          {showJustificationsWarning ? <DescriptionListTerm> * WARNING</DescriptionListTerm> : <span></span>}
          {checkResultData['justifications']['warning'].map((item, index) => (
            <DescriptionListDescription key={index}>
              {item.id} - {item.title}
            </DescriptionListDescription>
          ))}
        </DescriptionListGroup>

        <DescriptionListGroup>
          <DescriptionListTerm>Documents</DescriptionListTerm>
          {showDocumentsOk ? <DescriptionListTerm> * OK</DescriptionListTerm> : <span></span>}
          {checkResultData['documents']['ok'].map((item, index) => (
            <DescriptionListDescription key={index}>
              {item.id} - {item.title}
            </DescriptionListDescription>
          ))}
          {showDocumentsKo ? <DescriptionListTerm> * KO</DescriptionListTerm> : <span></span>}
          {checkResultData['documents']['ko'].map((item, index) => (
            <DescriptionListDescription key={index}>
              {item.id} - {item.title}
            </DescriptionListDescription>
          ))}
          {showDocumentsWarning ? <DescriptionListTerm> * WARNING</DescriptionListTerm> : <span></span>}
          {checkResultData['documents']['warning'].map((item, index) => (
            <DescriptionListDescription key={index}>
              {item.id} - {item.title}
            </DescriptionListDescription>
          ))}
        </DescriptionListGroup>
      </DescriptionList>
    </React.Fragment>
  )
}

export interface APICheckSpecModalProps {
  modalShowState
  setModalShowState
  api
}

export const APICheckSpecModal: React.FunctionComponent<APICheckSpecModalProps> = ({
  modalShowState = false,
  setModalShowState,
  api = null
}: APICheckSpecModalProps) => {
  type validate = 'success' | 'warning' | 'error' | 'default'

  const [isModalOpen, setIsModalOpen] = React.useState(false)
  const [messageValue, setMessageValue] = React.useState('')
  const [checkResult, setCheckResult] = React.useState(null)

  const [rawSpecificationUrlValue, setRawSpecificationUrlValue] = React.useState(api != null ? api.raw_specification_url : '')
  const [validatedRawSpecificationUrlValue, setValidatedRawSpecificationUrlValue] = React.useState<validate>('error')

  React.useEffect(() => {
    if (rawSpecificationUrlValue.trim() === '') {
      setValidatedRawSpecificationUrlValue('error')
    } else {
      setValidatedRawSpecificationUrlValue('success')
    }
  }, [rawSpecificationUrlValue])

  React.useEffect(() => {
    if (api != null) {
      setRawSpecificationUrlValue(api.raw_specification_url)
    }
  }, [api])

  const handleModalConfirm = () => {
    let sr_count = 0
    let ts_count = 0
    let tc_count = 0
    let j_count = 0
    let doc_count = 0
    let analysis_message = ''
    if (validatedRawSpecificationUrlValue == 'error') {
      setMessageValue('Raw Specification Url is mandatory')
      return
    } else {
      setMessageValue('')
      fetch(Constants.API_BASE_URL + '/apis/check-specification?id=' + api.id + '&url=' + rawSpecificationUrlValue, {
        method: 'GET',
        headers: Constants.JSON_HEADER
      })
        .then((response) => response.json())
        .then((response) => {
          if (Object.keys(response).includes(Constants._SRs)) {
            setCheckResult(response)
            sr_count =
              response[Constants._SRs]['ok'].length + response[Constants._SRs]['ko'].length + response[Constants._SRs]['warning'].length
            ts_count =
              response[Constants._TSs]['ok'].length + response[Constants._TSs]['ko'].length + response[Constants._TSs]['warning'].length
            tc_count =
              response[Constants._TCs]['ok'].length + response[Constants._TCs]['ko'].length + response[Constants._TCs]['warning'].length
            j_count =
              response[Constants._Js]['ok'].length + response[Constants._Js]['ko'].length + response[Constants._Js]['warning'].length
            doc_count =
              response[Constants._Ds]['ok'].length + response[Constants._Ds]['ko'].length + response[Constants._Ds]['warning'].length
            const tot_count = sr_count + ts_count + tc_count + j_count + doc_count
            analysis_message = 'Analyzed ' + tot_count + ' work items'
            analysis_message += ' - Software Requirements: ' + sr_count
            analysis_message += ' - Test Specifications: ' + ts_count
            analysis_message += ' - Test Cases: ' + tc_count
            analysis_message += ' - Justifications: ' + j_count
            analysis_message += ' - Documents: ' + doc_count
            if (api.raw_specification_url === rawSpecificationUrlValue) {
              analysis_message += ' - NOTE: you are analyzing the current version of the reference document.'
            }
            setMessageValue(analysis_message)
          } else {
            setMessageValue('Error in the server response.')
          }
        })
        .catch((err) => {
          setMessageValue(err.toString())
        })
    }
  }

  const handleFixWarnings = () => {
    setMessageValue('')
    fetch(Constants.API_BASE_URL + '/apis/fix-specification-warnings?id=' + api.id, {
      method: 'GET',
      headers: Constants.JSON_HEADER
    })
      .then((response) => {
        if (response.status !== 200) {
          setMessageValue(response.statusText)
        } else {
          handleModalConfirm()
        }
      })
      .catch((err) => {
        setMessageValue(err.toString())
        console.log(err.message)
      })
  }

  const handleRawSpecificationUrlValueChange = (_event, value: string) => {
    setRawSpecificationUrlValue(value)
  }

  const handleModalToggle = () => {
    const new_state = !modalShowState
    if (new_state == false) {
      setCheckResult(null)
    }
    setModalShowState(new_state)
    setIsModalOpen(new_state)
  }

  React.useEffect(() => {
    setIsModalOpen(modalShowState)
  }, [modalShowState])

  return (
    <React.Fragment>
      <Modal
        width={Constants.MODAL_WIDTH}
        bodyAriaLabel='APICheckSpecModal'
        aria-label='api check spec modal'
        tabIndex={0}
        variant={ModalVariant.large}
        title='Check Work Item Mapping against a Software Component Specification'
        description={api != null ? 'Current api ' + api.api + ' from ' + api.library + ' ' + api.library_version : ''}
        isOpen={isModalOpen}
        onClose={handleModalToggle}
        actions={[
          <Button key='confirm' variant='primary' onClick={() => handleModalConfirm()}>
            Confirm
          </Button>,
          <Button key='cancel' variant='link' onClick={handleModalToggle}>
            Cancel
          </Button>,
          <Button
            key='fix warnings'
            variant='primary'
            isDisabled={api != null ? rawSpecificationUrlValue != api.raw_specification_url : true}
            onClick={() => handleFixWarnings()}
          >
            Fix Warnings
          </Button>
        ]}
      >
        <Form>
          <FormGroup label='Software Component Specification Url' isRequired fieldId={`input-api-check-spec-raw-specification-url`}>
            <TextInput
              isRequired
              id={`input-api-check-spec-raw-specification-url`}
              name={`input-api-check-spec-raw-specification-url`}
              value={api != null ? rawSpecificationUrlValue : ''}
              onChange={(_ev, value) => handleRawSpecificationUrlValueChange(_ev, value)}
            />
            {validatedRawSpecificationUrlValue !== 'success' && (
              <FormHelperText>
                <HelperText>
                  <HelperTextItem variant={validatedRawSpecificationUrlValue}>
                    {validatedRawSpecificationUrlValue === 'error' ? 'This field is mandatory' : ''}
                  </HelperTextItem>
                </HelperText>
              </FormHelperText>
            )}
          </FormGroup>
        </Form>

        {messageValue ? (
          <Hint>
            <HintBody>{messageValue}</HintBody>
          </Hint>
        ) : (
          <span></span>
        )}

        {checkResult ? <CheckSpecResults checkResultData={checkResult} /> : <span></span>}
      </Modal>
    </React.Fragment>
  )
}
