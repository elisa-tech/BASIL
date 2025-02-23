import * as React from 'react'
import * as Constants from '@app/Constants/constants'
import { Button, Modal, ModalVariant, Tab, TabContent, TabContentBody, TabTitleText, Tabs } from '@patternfly/react-core'
import { SectionForm } from '../Form/SectionForm'
import { TestSpecificationForm } from '../Form/TestSpecificationForm'
import { TestSpecificationSearch } from '../Search/TestSpecificationSearch'

export interface MappingTestSpecificationModalProps {
  api
  modalAction: string
  modalVerb: string
  modalTitle: string
  modalDescription: string
  modalShowState: boolean
  modalFormData
  modalIndirect
  modalOffset
  modalSection
  setModalShowState
  loadMappingData
  parentData
  parentType
  parentRelatedToType
  setModalOffset
  setModalSection
}

export const MappingTestSpecificationModal: React.FunctionComponent<MappingTestSpecificationModalProps> = ({
  modalShowState = false,
  setModalShowState,
  modalAction = '',
  modalVerb = '',
  modalTitle = '',
  modalFormData,
  modalIndirect,
  modalOffset,
  modalSection,
  modalDescription = '',
  api,
  loadMappingData,
  parentData,
  parentType,
  parentRelatedToType,
  setModalOffset,
  setModalSection
}: MappingTestSpecificationModalProps) => {
  const [isModalOpen, setIsModalOpen] = React.useState(false)
  const [testSpecifications, setTestSpecifications] = React.useState([])

  const handleModalToggle = () => {
    const new_state = !modalShowState
    setModalShowState(new_state)
    setIsModalOpen(new_state)
  }

  React.useEffect(() => {
    if (modalShowState == true) {
      loadTestSpecifications('')
      setActiveTabKey(0)
    }
    setIsModalOpen(modalShowState)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [modalShowState])

  const loadTestSpecifications = (searchValue) => {
    const url = Constants.API_BASE_URL + '/test-specifications?search=' + searchValue
    fetch(url)
      .then((res) => res.json())
      .then((data) => {
        setTestSpecifications(data)
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
        width={Constants.MODAL_WIDTH}
        bodyAriaLabel='MappingTestSpecificationModal'
        aria-label='mapping test specification modal'
        tabIndex={0}
        variant={ModalVariant.large}
        title={modalTitle}
        description={modalDescription}
        isOpen={isModalOpen}
        onClose={handleModalToggle}
      >
        <Tabs activeKey={activeTabKey} onSelect={handleTabClick} aria-label='Add a New/Existing Test Specification' role='region'>
          <Tab
            eventKey={0}
            id='tab-btn-test-specification-data'
            title={<TabTitleText>Test Specification Data</TabTitleText>}
            tabContentId='tabNewTestSpecification'
            tabContentRef={newItemRef}
          />
          <Tab
            eventKey={1}
            id='tab-btn-test-specification-mapping-section'
            isDisabled={modalIndirect}
            title={<TabTitleText>Mapping Section</TabTitleText>}
            tabContentId='tabSection'
            tabContentRef={sectionItemsRef}
          />
          <Tab
            eventKey={2}
            id='tab-btn-test-specification-existing'
            isDisabled={modalVerb == 'POST' ? false : true}
            title={<TabTitleText>Existing</TabTitleText>}
            tabContentId='tabExistingTestSpecification'
            tabContentRef={existingItemsRef}
          />
        </Tabs>
        <div>
          <TabContent eventKey={0} id='tabContentTestSpecificationForm' ref={newItemRef} hidden={0 !== activeTabKey}>
            <TabContentBody hasPadding>
              <TestSpecificationForm
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
          <TabContent eventKey={1} id='tabContentTestSpecificationSection' ref={sectionItemsRef} hidden={1 !== activeTabKey}>
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
          <TabContent eventKey={2} id='tabContentTestSpecificationExisting' ref={existingItemsRef} hidden={2 !== activeTabKey}>
            <TabContentBody hasPadding>
              <TestSpecificationSearch
                api={api}
                parentData={parentData}
                formVerb={modalVerb}
                parentType={parentType}
                parentRelatedToType={parentRelatedToType}
                handleModalToggle={handleModalToggle}
                loadMappingData={loadMappingData}
                loadTestSpecifications={loadTestSpecifications}
                testSpecifications={testSpecifications}
                modalIndirect={modalIndirect}
                modalOffset={modalOffset}
                modalSection={modalSection}
                modalShowState={modalShowState}
                formDefaultButtons={1}
                formData={modalFormData}
                formMessage={''}
              />
            </TabContentBody>
          </TabContent>
        </div>
      </Modal>
    </React.Fragment>
  )
}
