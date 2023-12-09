import React from 'react';
import {
  Button,
  Modal,
  ModalVariant,
  Tab,
  TabContent,
  TabContentBody,
  TabTitleText,
  Tabs
} from '@patternfly/react-core';
import { SectionForm } from '../Form/SectionForm';
import { TestCaseForm } from '../Form/TestCaseForm';
import { TestCaseSearch } from '../Search/TestCaseSearch';

export interface MappingTestCaseModalProps {
  api;
  baseApiUrl: string;
  modalAction: string;
  modalVerb: string;
  modalTitle: string;
  modalDescription: string;
  modalShowState: string;
  modalFormData;
  modalSection;
  modalIndirect;
  modalOffset;
  parentData;
  parentType;
  parentRelatedToType;
  loadMappingData;
  setModalShowState;
  setModalOffset;
  setModalSection;
}

export const MappingTestCaseModal: React.FunctionComponent<MappingTestCaseModalProps> = ({
  baseApiUrl,
  modalShowState = false,
  setModalShowState,
  modalAction = "",
  modalVerb = "",
  modalTitle = "",
  modalFormData,
  modalIndirect,
  modalOffset,
  modalSection,
  parentData,
  parentType,
  parentRelatedToType,
  loadMappingData,
  modalDescription = "",
  api,
  setModalOffset,
  setModalSection,
  }: MappingTestCaseModalProps) => {

  const [isModalOpen, setIsModalOpen] = React.useState(false);
  const [testCases, setTestCases] = React.useState([]);

  const handleModalToggle = () => {
    const new_state = !modalShowState;
    setModalShowState(new_state);
    setIsModalOpen(new_state);
  };

  React.useEffect(() => {
    setIsModalOpen(modalShowState);
  }, [modalShowState]);

  const loadTestCases = (searchValue) => {
    const url = baseApiUrl + '/test-cases';
    if (searchValue != undefined){
      url = url + '?search=' + searchValue;
    }
    fetch(url)
      .then((res) => res.json())
      .then((data) => {
          setTestCases(data);
      })
      .catch((err) => {
        console.log(err.message);
      });
  }

  const [activeTabKey, setActiveTabKey] = React.useState<string | number>(0);
  // Toggle currently active tab
  const handleTabClick = (
  event: React.MouseEvent | React.KeyboardEvent | MouseEvent,
  tabIndex: string | number
  ) => {
  setActiveTabKey(tabIndex);
  };

  const newItemRef = React.createRef<HTMLElement>();
  const sectionItemsRef = React.createRef<HTMLElement>();
  const existingItemsRef = React.createRef<HTMLElement>();

  return (
    <React.Fragment>
      <Modal
        bodyAriaLabel="Scrollable modal content"
        tabIndex={0}
        variant={ModalVariant.large}
        title={modalTitle}
        description={modalDescription}
        isOpen={isModalOpen}
        onClose={handleModalToggle}
        actions={[
          <Button key="cancel" variant="link" onClick={handleModalToggle}>
            Cancel
          </Button>
        ]}
      >

      <Tabs
        activeKey={activeTabKey}
        onSelect={handleTabClick}
        aria-label="Add a New/Existing Test Specification"
        role="region"
      >
        <Tab
          eventKey={0}
          id="tab-btn-test-case-data"
          title={<TabTitleText>Test Case Data</TabTitleText>}
          tabContentId="tabNewTestCase"
          tabContentRef={newItemRef}
        />
        <Tab
          eventKey={1}
          id="tab-btn-test-case-mapping-section"
          isDisabled={modalIndirect}
          title={<TabTitleText>Mapping Section</TabTitleText>}
          tabContentId="tabSection"
          tabContentRef={sectionItemsRef}
        />
        <Tab
          eventKey={2}
          id="tab-btn-test-case-existing"
          isDisabled={modalVerb == 'POST' ? false : true}
          title={<TabTitleText>Existing</TabTitleText>}
          tabContentId="tabExistingTestCase"
          tabContentRef={existingItemsRef}
        />
      </Tabs>
      <div>
        <TabContent eventKey={0} id="tabContentTestCaseForm" ref={newItemRef}>
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
              baseApiUrl={baseApiUrl}
              modalIndirect={modalIndirect}
              modalOffset={modalOffset}
              modalSection={modalSection}
            />
          </TabContentBody>
        </TabContent>
        <TabContent eventKey={1} id="tabContentTestCaseSection" ref={sectionItemsRef} hidden>
          <TabContentBody hasPadding>
            <SectionForm
              api={api}
              formVerb={modalVerb}
              handleModalToggle={handleModalToggle}
              baseApiUrl={baseApiUrl}
              modalIndirect={modalIndirect}
              modalOffset={modalOffset}
              modalSection={modalSection}
              setModalOffset={setModalOffset}
              setModalSection={setModalSection}
            />
          </TabContentBody>
        </TabContent>
        <TabContent eventKey={2} id="tabContentTestCaseExisting" ref={existingItemsRef} hidden>
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
              baseApiUrl={baseApiUrl}
              modalIndirect={modalIndirect}
              modalOffset={modalOffset}
              modalSection={modalSection}
            />
          </TabContentBody>
        </TabContent>
      </div>

      </Modal>
    </React.Fragment>
  );
};
