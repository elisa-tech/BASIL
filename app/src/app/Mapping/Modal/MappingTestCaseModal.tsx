import * as React from 'react'
import * as Constants from '../../Constants/constants'
import { Button, Modal, ModalVariant, Tab, TabContent, TabContentBody, TabTitleText, Tabs } from '@patternfly/react-core'
import { SectionForm } from '../Form/SectionForm'
import { TestCaseForm } from '../Form/TestCaseForm'
import { TestCaseSearch } from '../Search/TestCaseSearch'

export interface MappingTestCaseModalProps {
  api
  modalAction: string
  modalVerb: string
  modalTitle: string
  modalDescription: string
  modalShowState: boolean
  modalFormData
  modalSection
  modalIndirect
  modalOffset
  parentData
  parentType
  parentRelatedToType
  loadMappingData
  setModalShowState
  setModalOffset
  setModalSection
}

export const MappingTestCaseModal: React.FunctionComponent<MappingTestCaseModalProps> = ({
  modalShowState = false,
  setModalShowState,
  modalAction = '',
  modalVerb = '',
  modalTitle = '',
  modalFormData,
  modalIndirect,
  modalOffset,
  modalSection,
  parentData,
  parentType,
  parentRelatedToType,
  loadMappingData,
  modalDescription = '',
  api,
  setModalOffset,
  setModalSection
}: MappingTestCaseModalProps) => {
  const [isModalOpen, setIsModalOpen] = React.useState(false)
  const [testCases, setTestCases] = React.useState([])

  const testCaseSearchFormDataDefault = { id: 0, title: '', description: '', repository: '', relative_path: '' }

  const handleModalToggle = () => {
    const new_state = !modalShowState
    setModalShowState(new_state)
    setIsModalOpen(new_state)
  }

  React.useEffect(() => {
    setIsModalOpen(modalShowState)
  }, [modalShowState])

  const loadTestCases = (searchValue) => {
    let url = Constants.API_BASE_URL + '/test-cases'
    if (searchValue != undefined) {
      url = url + '?search=' + searchValue
    }
    fetch(url)
      .then((res) => res.json())
      .then((data) => {
        setTestCases(data)
      })
      .catch((err) => {
        console.log(err.message)
      })
  }

  const [activeTabKey, setActiveTabKey] = React.useState<string | number>(0)
  // Toggle currently active tab
  const handleTabClick = (event: React.MouseEvent | React.KeyboardEvent | MouseEvent, tabIndex: string | number) => {
    setActiveTabKey(tabIndex)
  }

  const newItemRef = React.createRef<HTMLElement>()
  const sectionItemsRef = React.createRef<HTMLElement>()
  const existingItemsRef = React.createRef<HTMLElement>()

  return (
    <React.Fragment>
      <Modal
        bodyAriaLabel='MappingTestCaseModal'
        aria-label='mapping test case modal'
        tabIndex={0}
        variant={ModalVariant.large}
        title={modalTitle}
        description={modalDescription}
        isOpen={isModalOpen}
        onClose={handleModalToggle}
        actions={[
          <Button key='cancel' variant='link' onClick={handleModalToggle}>
            Cancel
          </Button>
        ]}
      >
        <Tabs activeKey={activeTabKey} onSelect={handleTabClick} aria-label='Add a New/Existing Test Specification' role='region'>
          <Tab
            eventKey={0}
            id='tab-btn-test-case-data'
            title={<TabTitleText>Test Case Data</TabTitleText>}
            tabContentId='tabNewTestCase'
            tabContentRef={newItemRef}
          />
          <Tab
            eventKey={1}
            id='tab-btn-test-case-mapping-section'
            isDisabled={modalIndirect}
            title={<TabTitleText>Mapping Section</TabTitleText>}
            tabContentId='tabSection'
            tabContentRef={sectionItemsRef}
          />
          <Tab
            eventKey={2}
            id='tab-btn-test-case-existing'
            isDisabled={modalVerb == 'POST' ? false : true}
            title={<TabTitleText>Existing</TabTitleText>}
            tabContentId='tabExistingTestCase'
            tabContentRef={existingItemsRef}
          />
        </Tabs>
        <div>
          <TabContent eventKey={0} id='tabContentTestCaseForm' ref={newItemRef} hidden={0 !== activeTabKey}>
            <TabContentBody hasPadding>
              <TestCaseForm
                api={api}
                formAction={modalAction}
                formData={modalFormData}
                formVerb={modalVerb}
                parentData={parentData}
                parentType={parentType}
                parentRelatedToType={parentRelatedToType}
                handleModalToggle={handleModalToggle}
                loadMappingData={loadMappingData}
                modalIndirect={modalIndirect}
                modalOffset={modalOffset}
                modalSection={modalSection}
                formDefaultButtons={1}
                formMessage={''}
                modalFormSubmitState={'waiting'}
              />
            </TabContentBody>
          </TabContent>
          <TabContent eventKey={1} id='tabContentTestCaseSection' ref={sectionItemsRef} hidden={1 !== activeTabKey}>
            <TabContentBody hasPadding>
              <SectionForm
                api={api}
                //formVerb={modalVerb}
                //handleModalToggle={handleModalToggle}
                //modalIndirect={modalIndirect}
                modalOffset={modalOffset}
                modalSection={modalSection}
                setModalOffset={setModalOffset}
                setModalSection={setModalSection}
              />
            </TabContentBody>
          </TabContent>
          <TabContent eventKey={2} id='tabContentTestCaseExisting' ref={existingItemsRef} hidden={2 !== activeTabKey}>
            <TabContentBody hasPadding>
              <TestCaseSearch
                api={api}
                formVerb={modalVerb}
                parentData={parentData}
                parentType={parentType}
                parentRelatedToType={parentRelatedToType}
                handleModalToggle={handleModalToggle}
                loadMappingData={loadMappingData}
                loadTestCases={loadTestCases}
                testCases={testCases}
                modalIndirect={modalIndirect}
                modalOffset={modalOffset}
                modalSection={modalSection}
                modalShowState={modalShowState}
                formMessage={''}
                formDefaultButtons={1}
                formData={testCaseSearchFormDataDefault}
              />
            </TabContentBody>
          </TabContent>
        </div>
      </Modal>
    </React.Fragment>
  )
}
