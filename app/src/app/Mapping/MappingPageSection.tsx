import * as React from 'react'
import * as Constants from '../Constants/constants'
import { Button, Card, CardBody, Flex, FlexItem, PageSection, Title } from '@patternfly/react-core'
import { MappingListingTable } from './MappingListingTable'
import { MappingSwRequirementModal } from './Modal/MappingSwRequirementModal'
import { MappingTestSpecificationModal } from './Modal/MappingTestSpecificationModal'
import { MappingTestCaseModal } from './Modal/MappingTestCaseModal'
import { MappingJustificationModal } from './Modal/MappingJustificationModal'
import { MappingDeleteModal } from './Modal/MappingDeleteModal'
import { MappingDetailsModal } from './Modal/MappingDetailsModal'
import { MappingDocumentModal } from './Modal/MappingDocumentModal'
import { MappingForkModal } from './Modal/MappingForkModal'
import { MappingHistoryModal } from './Modal/MappingHistoryModal'
import { MappingUsageModal } from './Modal/MappingUsageModal'
import { MappingCommentModal } from './Modal/MappingCommentModal'
import { TestResultModal } from './Modal/TestResultModal'
import { TestRunModal } from './Modal/TestRunModal'
import { Switch } from '@patternfly/react-core'
import { MappingViewSelect } from './MappingViewSelect'
import { LeavesProgressBar } from '../Custom/LeavesProgressBar'

export interface MappingPageSectionProps {
  mappingData
  unmappingData
  loadMappingData
  mappingViewSelectValue
  setMappingViewSelectValue
  setMappingViewSelectValueOld
  totalCoverage
  api
}

const MappingPageSection: React.FunctionComponent<MappingPageSectionProps> = ({
  mappingData = [],
  unmappingData = [],
  loadMappingData,
  mappingViewSelectValue,
  setMappingViewSelectValue,
  setMappingViewSelectValueOld,
  totalCoverage,
  api
}: MappingPageSectionProps) => {
  const [modalAction, setModalAction] = React.useState('')
  const [modalVerb, setModalVerb] = React.useState('')
  // eslint-disable-next-line  @typescript-eslint/no-explicit-any
  const [modalFormData, setModalFormData] = React.useState<any>('')
  const [modalTitle, setModalTitle] = React.useState('')
  const [modalIndirect, setModalIndirect] = React.useState<boolean>(false)
  const [modalDescription, setModalDescription] = React.useState('')
  const [modalParentData, setModalParentData] = React.useState({})
  const [modalParentType, setModalParentType] = React.useState('')
  const [modalParentRelatedToType, setModalParentRelatedToType] = React.useState('')

  const [modalSection, setModalSection] = React.useState('')
  const [modalOffset, setModalOffset] = React.useState('')

  const [srModalShowState, setSrModalShowState] = React.useState<boolean>(false)
  const [tsModalShowState, setTsModalShowState] = React.useState<boolean>(false)
  const [tcModalShowState, setTcModalShowState] = React.useState<boolean>(false)
  const [jModalShowState, setJModalShowState] = React.useState<boolean>(false)
  const [docModalShowState, setDocModalShowState] = React.useState<boolean>(false)
  const [historyModalShowState, setHistoryModalShowState] = React.useState<boolean>(false)
  const [deleteModalShowState, setDeleteModalShowState] = React.useState<boolean>(false)
  const [detailsModalShowState, setDetailsModalShowState] = React.useState<boolean>(false)
  const [forkModalShowState, setForkModalShowState] = React.useState<boolean>(false)
  const [usageModalShowState, setUsageModalShowState] = React.useState<boolean>(false)
  const [commentModalShowState, setCommentModalShowState] = React.useState<boolean>(false)
  const [testResultModalShowState, setTestResultModalShowState] = React.useState<boolean>(false)
  const [testRunModalShowState, setTestRunModalShowState] = React.useState<boolean>(false)

  const [currentMappingHistory, setCurrentMappingHistory] = React.useState()
  const [currentMappingDetails, setCurrentMappingDetails] = React.useState()
  const [currentMappingUsage, setCurrentMappingUsage] = React.useState()

  const [modalRelationData, setModalRelationData] = React.useState({})
  const [modalWorkItemType, setModalWorkItemType] = React.useState('')

  const [showIndirectTestSpecificationsOld, setShowIndirectTestSpecificationsOld] = React.useState<boolean>(true)
  const [showIndirectTestSpecifications, setShowIndirectTestSpecifications] = React.useState<boolean>(true)
  const [showIndirectTestCasesOld, setShowIndirectTestCasesOld] = React.useState<boolean>(true)
  const [showIndirectTestCases, setShowIndirectTestCases] = React.useState<boolean>(true)

  const getWorkItemDescription = (_work_item_type) => {
    const work_item_types = [Constants._A, Constants._D, Constants._J, Constants._SR, Constants._TS, Constants._TC]
    const work_item_descriptions = ['Api', 'Document', 'Justification', 'Software Requirement', 'Test Specification', 'Test Case']
    return work_item_descriptions[work_item_types.indexOf(_work_item_type)]
  }

  const getSwRequirementData = (_list, _index) => {
    const sr = {
      id: _list[_index][Constants._SR_]['id'],
      coverage: _list[_index]['coverage'],
      title: _list[_index][Constants._SR_]['title'],
      description: _list[_index][Constants._SR_]['description']
    }
    return sr
  }

  const getTestCaseData = (_list, _index) => {
    let tc = {}
    tc = _list[_index][Constants._TC_]
    tc['coverage'] = _list[_index]['coverage']
    return tc
  }

  const getTestSpecificationData = (_list, _index) => {
    let ts = {}
    ts = _list[_index][Constants._TS_]
    ts['coverage'] = _list[_index]['coverage']
    return ts
  }

  const getJustificationData = (_list, _index) => {
    let js = {}
    js = _list[_index][Constants._J]
    js['coverage'] = _list[_index]['coverage']
    return js
  }

  const getDocumentData = (_list, _index) => {
    let doc = {}
    doc = _list[_index][Constants._D]
    doc['coverage'] = _list[_index]['coverage']
    return doc
  }

  const setSrModalInfo = (show, indirect, action, api, section, offset, parent_type, parent_list, parent_index, parent_related_to_type) => {
    setModalTitle(getWorkItemDescription(Constants._SR))
    setModalDescription('Work item data and mapping information (section, offset, coverage).')
    setSrModalShowState(show)
    setModalAction(action)
    if (action == 'add') {
      setModalVerb('POST')
      setModalFormData(Constants.srFormEmpty)
    } else if (action == 'edit') {
      setModalVerb('PUT')
      setModalFormData(getSwRequirementData(parent_list, parent_index))
    }
    setModalParentData(parent_list[parent_index])
    setModalSection(section)
    setModalOffset(offset)
    setModalIndirect(indirect)
    setModalParentType(parent_type)
    setModalParentRelatedToType(parent_related_to_type)
  }

  const setTsModalInfo = (show, indirect, action, api, section, offset, parent_type, parent_list, parent_index, parent_related_to_type) => {
    setModalTitle(getWorkItemDescription(Constants._TS))
    setModalDescription('Work item data and mapping information (section, offset, coverage).')
    setModalAction(action)
    if (action == 'add') {
      setModalVerb('POST')
      setModalFormData(Constants.tsFormEmpty)
    } else if (action == 'edit') {
      setModalVerb('PUT')
      setModalFormData(getTestSpecificationData(parent_list, parent_index))
    }
    setModalParentData(parent_list[parent_index])
    setModalSection(section)
    setModalOffset(offset)
    setModalIndirect(indirect)
    setModalParentType(parent_type)
    setModalParentRelatedToType(parent_related_to_type)
    setTsModalShowState(show)
  }

  const setTcModalInfo = (show, indirect, action, api, section, offset, parent_type, parent_list, parent_index, parent_related_to_type) => {
    setModalTitle(getWorkItemDescription(Constants._TC))
    setModalDescription('Work item data and mapping information (section, offset, coverage).')
    setTcModalShowState(show)
    setModalAction(action)
    if (action == 'add') {
      setModalVerb('POST')
      setModalFormData(Constants.tcFormEmpty)
    } else if (action == 'edit') {
      setModalVerb('PUT')
      setModalFormData(getTestCaseData(parent_list, parent_index))
    }
    setModalParentData(parent_list[parent_index])
    setModalSection(section)
    setModalOffset(offset)
    setModalIndirect(indirect)
    setModalParentType(parent_type)
    setModalParentRelatedToType(parent_related_to_type)
  }

  const setJModalInfo = (show, action, api, section, offset, parent_list, parent_index) => {
    setJModalShowState(show)
    setModalAction(action)

    if (action == 'add') {
      setModalVerb('POST')
      setModalFormData(Constants.jFormEmpty)
    } else if (action == 'edit') {
      setModalVerb('PUT')
      setModalFormData(getJustificationData(parent_list, parent_index))
    }

    setModalTitle(getWorkItemDescription(Constants._J))
    setModalDescription('Work item data and mapping information (section, offset, coverage).')
    setModalSection(section)
    setModalOffset(offset)
    setModalIndirect(false)
    setModalParentData(parent_list[parent_index])
    setModalParentType(Constants._A)
    setModalParentRelatedToType('')
  }

  const setDocModalInfo = (show, action, api, section, offset, parent_list, parent_index) => {
    setDocModalShowState(show)
    setModalAction(action)

    if (action == 'add') {
      setModalVerb('POST')
      setModalFormData(Constants.docFormEmpty)
    } else if (action == 'edit') {
      setModalVerb('PUT')
      setModalFormData(getDocumentData(parent_list, parent_index))
    }

    setModalTitle(getWorkItemDescription(Constants._D))
    setModalDescription('Work item data and mapping information (section, offset, coverage).')
    setModalSection(section)
    setModalOffset(offset)
    setModalIndirect(false)
    setModalParentData(parent_list[parent_index])
    setModalParentType(Constants._A)
    setModalParentRelatedToType('')
  }

  const setDeleteModalInfo = (show, work_item_type, parent_type, parent_related_to_type, list, index) => {
    setModalTitle('Delete selected ' + getWorkItemDescription(work_item_type))
    setModalDescription('Do you want to continue?')
    setModalRelationData(list[index])
    setDeleteModalShowState(show)
    setModalWorkItemType(work_item_type)
    setModalParentType(parent_type)
    setModalParentRelatedToType(parent_related_to_type)
  }

  const setTestRunModalInfo = (show, api, work_item, parent_type) => {
    setModalRelationData(work_item)
    setTestRunModalShowState(show)
    setModalParentType(parent_type)
  }

  const setTestResultModalInfo = (show, api, work_item, parent_type) => {
    setModalRelationData(work_item)
    setTestResultModalShowState(show)
    setModalParentType(parent_type)
  }

  const setForkModalInfo = (show, work_item_type, parent_type, parent_related_to_type, list, index) => {
    setModalTitle('Fork selected ' + getWorkItemDescription(work_item_type))
    setModalDescription('Do you want to continue?')
    setModalRelationData(list[index])
    setForkModalShowState(show)
    setModalWorkItemType(work_item_type)
    setModalParentType(parent_type)
    setModalParentRelatedToType(parent_related_to_type)
  }

  const setCommentModalInfo = (show, work_item_type, parent_type, parent_related_to_type, list, index) => {
    let wi_field = 'title'
    let wi_title = ''
    let wi_type = ''

    if (work_item_type == Constants._J) {
      wi_field = 'description'
    }

    if (work_item_type == Constants._SR) {
      wi_type = Constants._SR_
    } else if (work_item_type == Constants._TS) {
      wi_type = Constants._TS_
    } else if (work_item_type == Constants._TC) {
      wi_type = Constants._TC_
    } else if (work_item_type == Constants._J) {
      wi_type = Constants._J
    } else if (work_item_type == Constants._D) {
      wi_type = Constants._D
    }

    wi_title = list[index][wi_type][wi_field].substr(0, 100)
    if (list[index][wi_type][wi_field].length > 99) {
      wi_title = wi_title + '...'
    }

    setModalTitle('Comment a ' + getWorkItemDescription(work_item_type))
    setModalDescription(wi_title)
    setCommentModalShowState(show)
    setModalWorkItemType(work_item_type)
    setModalParentType(parent_type)
    setModalParentRelatedToType(parent_related_to_type)
    setModalRelationData(list[index])
  }

  const setHistoryModalInfo = (show, work_item_type, mapped_to_type, relation_id) => {
    const url =
      Constants.API_BASE_URL +
      '/mapping/history?work_item_type=' +
      work_item_type +
      '&mapped_to_type=' +
      mapped_to_type +
      '&relation_id=' +
      relation_id
    fetch(url)
      .then((res) => res.json())
      .then((data) => {
        setCurrentMappingHistory(data)
        setHistoryModalShowState(show)
      })
      .catch((err) => {
        console.log(err.message)
      })
  }

  const setDetailsModalInfo = (show, work_item_type, work_item_id) => {
    const url = Constants.API_BASE_URL + '/' + work_item_type + 's?field1=id&filter1=' + work_item_id
    fetch(url)
      .then((res) => res.json())
      .then((data) => {
        setModalTitle(getWorkItemDescription(work_item_type) + ' details')
        setModalDescription('')
        setCurrentMappingDetails(data)
        setDetailsModalShowState(show)
      })
      .catch((err) => {
        console.log(err.message)
      })
  }

  const setUsageModalInfo = (show, work_item_type, work_item_id) => {
    const url = Constants.API_BASE_URL + '/mapping/usage?work_item_type=' + work_item_type + '&id=' + work_item_id
    fetch(url)
      .then((res) => res.json())
      .then((data) => {
        setCurrentMappingUsage(data)
        setUsageModalShowState(show)
        setModalTitle(getWorkItemDescription(work_item_type) + ' usage')
        setModalDescription('')
      })
      .catch((err) => {
        console.log(err.message)
      })
  }

  const toggleIndirectTestSpecifications = () => {
    setShowIndirectTestSpecificationsOld(showIndirectTestSpecifications)
    setShowIndirectTestSpecifications(!showIndirectTestSpecifications)
  }
  const toggleIndirectTestCases = () => {
    setShowIndirectTestCasesOld(showIndirectTestCases)
    setShowIndirectTestCases(!showIndirectTestCases)
  }

  React.useEffect(() => {
    if (showIndirectTestSpecifications != showIndirectTestSpecificationsOld || showIndirectTestCases != showIndirectTestCasesOld) {
      loadMappingData(false)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [showIndirectTestSpecifications, showIndirectTestCases])

  return (
    <React.Fragment>
      <PageSection isFilled>
        <Card>
          <CardBody>
            <Flex>
              <Flex>
                <FlexItem>
                  <Title headingLevel='h1'>Mapping</Title>
                </FlexItem>
                <FlexItem>
                  <LeavesProgressBar progressValue={totalCoverage} progressId='api-mapping-coverage' />
                </FlexItem>
              </Flex>
              {api?.permissions?.indexOf('w') >= 0 ? (
                <Flex align={{ default: 'alignRight' }}>
                  <FlexItem>
                    <Button
                      variant='secondary'
                      id='btn-mapping-new-sw-requirement'
                      isDisabled={api?.raw_specification == null}
                      onClick={() => setSrModalInfo(true, false, 'add', api, '', 0, Constants._A, [], -1, '')}
                    >
                      Map Software Req.
                    </Button>
                  </FlexItem>
                  <FlexItem>
                    <Button
                      variant='secondary'
                      id='btn-mapping-new-test-specification'
                      isDisabled={api?.raw_specification == null}
                      onClick={() => setTsModalInfo(true, false, 'add', api, '', 0, Constants._A, [], -1, '')}
                    >
                      Map Test Specification
                    </Button>
                  </FlexItem>
                  <FlexItem>
                    <Button
                      variant='secondary'
                      id='btn-mapping-new-test-case'
                      isDisabled={api?.raw_specification == null}
                      onClick={() => setTcModalInfo(true, false, 'add', api, '', 0, Constants._A, [], -1, '')}
                    >
                      Map Test Case
                    </Button>
                  </FlexItem>
                  <FlexItem>
                    <Button
                      variant='secondary'
                      id='btn-mapping-new-justification'
                      isDisabled={api?.raw_specification == null}
                      onClick={() => setJModalInfo(true, 'add', api, '', 0, [], -1)}
                    >
                      Map Justification
                    </Button>
                  </FlexItem>
                  <FlexItem>
                    <Button
                      variant='secondary'
                      id='btn-mapping-new-document'
                      isDisabled={api?.raw_specification == null}
                      onClick={() => setDocModalInfo(true, 'add', api, '', 0, [], -1)}
                    >
                      Map Document
                    </Button>
                  </FlexItem>
                </Flex>
              ) : (
                ''
              )}
            </Flex>
          </CardBody>
        </Card>
        <Card>
          <CardBody>
            <Flex>
              <FlexItem>
                <MappingViewSelect
                  mappingViewSelectValue={mappingViewSelectValue}
                  setMappingViewSelectValue={setMappingViewSelectValue}
                  setMappingViewSelectValueOld={setMappingViewSelectValueOld}
                />
              </FlexItem>
              <FlexItem align={{ default: 'alignRight' }}>
                <Switch
                  id='switch-indirect-test-specifications'
                  label='Indirect Test Specification'
                  labelOff='Indirect Test Specification Hidden'
                  isChecked={showIndirectTestSpecifications}
                  onChange={toggleIndirectTestSpecifications}
                  ouiaId='BasicSwitch'
                />
              </FlexItem>
              <FlexItem>
                <Switch
                  id='switch-indirect-test-cases'
                  label='Indirect Test Case'
                  labelOff='Indirect Test Case Hidden'
                  isChecked={showIndirectTestCases}
                  onChange={toggleIndirectTestCases}
                  ouiaId='BasicSwitch'
                />
              </FlexItem>
            </Flex>
          </CardBody>
        </Card>
      </PageSection>

      <MappingListingTable
        mappingData={mappingData}
        unmappingData={unmappingData}
        api={api}
        srModalShowState={srModalShowState}
        //setSrModalShowState={setSrModalShowState}
        //tsModalShowState={tsModalShowState}
        //setTsModalShowState={setTsModalShowState}
        //tcModalShowState={tcModalShowState}
        //setTcModalShowState={setTcModalShowState}
        //jModalShowState={jModalShowState}
        //testResultModalShowState={testResultModalShowState}
        //setTestResultModalShowState={setTestResultModalShowState}
        //testRunModalShowState={testRunModalShowState}
        //setTestRunModalShowState={setTestRunModalShowState}
        //setJModalShowState={setJModalShowState}
        setDocModalInfo={setDocModalInfo}
        setTsModalInfo={setTsModalInfo}
        setTcModalInfo={setTcModalInfo}
        setSrModalInfo={setSrModalInfo}
        setJModalInfo={setJModalInfo}
        setCommentModalInfo={setCommentModalInfo}
        setDeleteModalInfo={setDeleteModalInfo}
        setTestRunModalInfo={setTestRunModalInfo}
        setTestResultModalInfo={setTestResultModalInfo}
        setDetailsModalInfo={setDetailsModalInfo}
        setForkModalInfo={setForkModalInfo}
        setHistoryModalInfo={setHistoryModalInfo}
        setUsageModalInfo={setUsageModalInfo}
        mappingViewSelectValue={mappingViewSelectValue}
        showIndirectTestCases={showIndirectTestCases}
        showIndirectTestSpecifications={showIndirectTestSpecifications}
      />
      <MappingSwRequirementModal
        api={api}
        modalAction={modalAction}
        modalDescription={modalDescription}
        modalFormData={modalFormData}
        modalIndirect={modalIndirect}
        modalOffset={modalOffset}
        setModalOffset={setModalOffset}
        modalSection={modalSection}
        setModalSection={setModalSection}
        modalShowState={srModalShowState}
        modalTitle={modalTitle}
        modalVerb={modalVerb}
        loadMappingData={loadMappingData}
        parentData={modalParentData}
        parentRelatedToType={modalParentRelatedToType}
        parentType={modalParentType}
        setModalShowState={setSrModalShowState}
      />
      <MappingTestSpecificationModal
        api={api}
        modalAction={modalAction}
        modalDescription={modalDescription}
        modalFormData={modalFormData}
        modalIndirect={modalIndirect}
        modalOffset={modalOffset}
        setModalOffset={setModalOffset}
        modalSection={modalSection}
        setModalSection={setModalSection}
        modalShowState={tsModalShowState}
        modalTitle={modalTitle}
        modalVerb={modalVerb}
        loadMappingData={loadMappingData}
        parentData={modalParentData}
        parentType={modalParentType}
        parentRelatedToType={modalParentRelatedToType}
        setModalShowState={setTsModalShowState}
      />
      <MappingTestCaseModal
        api={api}
        modalAction={modalAction}
        modalDescription={modalDescription}
        modalFormData={modalFormData}
        modalIndirect={modalIndirect}
        modalOffset={modalOffset}
        setModalOffset={setModalOffset}
        modalSection={modalSection}
        setModalSection={setModalSection}
        modalShowState={tcModalShowState}
        modalTitle={modalTitle}
        modalVerb={modalVerb}
        loadMappingData={loadMappingData}
        parentData={modalParentData}
        parentType={modalParentType}
        parentRelatedToType={modalParentRelatedToType}
        setModalShowState={setTcModalShowState}
      />
      <MappingJustificationModal
        api={api}
        modalAction={modalAction}
        modalDescription={modalDescription}
        modalFormData={modalFormData}
        modalIndirect={modalIndirect}
        modalOffset={modalOffset}
        setModalOffset={setModalOffset}
        modalSection={modalSection}
        setModalSection={setModalSection}
        modalShowState={jModalShowState}
        modalTitle={modalTitle}
        modalVerb={modalVerb}
        loadMappingData={loadMappingData}
        parentData={modalParentData}
        parentType={modalParentType}
        setModalShowState={setJModalShowState}
        modalData={{}}
        modalHistoryData={currentMappingHistory}
        parentRelatedToType={modalParentRelatedToType}
      />
      <MappingDetailsModal
        modalDescription={modalDescription}
        modalTitle={modalTitle}
        modalData={currentMappingDetails}
        setModalShowState={setDetailsModalShowState}
        modalShowState={detailsModalShowState}
      />
      <MappingDocumentModal
        api={api}
        modalAction={modalAction}
        modalDescription={modalDescription}
        modalFormData={modalFormData}
        modalIndirect={modalIndirect}
        modalOffset={modalOffset}
        setModalOffset={setModalOffset}
        modalSection={modalSection}
        setModalSection={setModalSection}
        modalShowState={docModalShowState}
        modalTitle={modalTitle}
        modalVerb={modalVerb}
        loadMappingData={loadMappingData}
        parentData={modalParentData}
        parentType={modalParentType}
        setModalShowState={setDocModalShowState}
        modalData={{}}
        modalHistoryData={currentMappingHistory}
        parentRelatedToType={modalParentRelatedToType}
      />
      <MappingHistoryModal
        modalDescription={modalDescription}
        modalTitle={modalTitle}
        modalData={currentMappingHistory}
        setModalShowState={setHistoryModalShowState}
        modalShowState={historyModalShowState}
      />
      <MappingUsageModal
        modalDescription={modalDescription}
        modalTitle={modalTitle}
        modalData={currentMappingUsage}
        setModalShowState={setUsageModalShowState}
        modalShowState={usageModalShowState}
      />
      <MappingCommentModal
        //api={api}
        modalDescription={modalDescription}
        modalTitle={modalTitle}
        relationData={modalRelationData}
        workItemType={modalWorkItemType}
        parentType={modalParentType}
        //parentRelatedToType={modalParentRelatedToType}
        setModalShowState={setCommentModalShowState}
        modalShowState={commentModalShowState}
        loadMappingData={loadMappingData}
      />
      <MappingDeleteModal
        api={api}
        modalTitle={modalTitle}
        modalDescription={modalDescription}
        setModalShowState={setDeleteModalShowState}
        modalShowState={deleteModalShowState}
        workItemType={modalWorkItemType}
        parentType={modalParentType}
        //parentRelatedToType={modalParentRelatedToType}
        relationData={modalRelationData}
        loadMappingData={loadMappingData}
      />
      <MappingForkModal
        api={api}
        modalTitle={modalTitle}
        modalDescription={modalDescription}
        setModalShowState={setForkModalShowState}
        modalShowState={forkModalShowState}
        workItemType={modalWorkItemType}
        parentType={modalParentType}
        //parentRelatedToType={modalParentRelatedToType}
        relationData={modalRelationData}
        loadMappingData={loadMappingData}
      />
      <TestResultModal
        api={api}
        setModalShowState={setTestResultModalShowState}
        modalShowState={testResultModalShowState}
        modalRelationData={modalRelationData}
        parentType={modalParentType}
      />
      <TestRunModal
        api={api}
        setModalShowState={setTestRunModalShowState}
        modalShowState={testRunModalShowState}
        modalRelationData={modalRelationData}
        parentType={modalParentType}
      />
    </React.Fragment>
  )
}

export { MappingPageSection }
