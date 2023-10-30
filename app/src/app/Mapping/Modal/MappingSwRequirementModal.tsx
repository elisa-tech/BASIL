import React from 'react';
import { Modal, ModalVariant, Form, FormGroup, Popover, Button, TextInput} from '@patternfly/react-core';
import { Tabs, Tab, TabTitleText, TabContent, TabContentBody } from '@patternfly/react-core';
import { SectionForm } from '../Form/SectionForm';
import { SwRequirementForm } from '../Form/SwRequirementForm';
import { SwRequirementSearch } from '../Search/SwRequirementSearch';

export interface MappingSwRequirementModalProps {
  api;
  baseApiUrl: string;
  modalAction: string;
  modalVerb: string;
  modalObject: string;
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

export const MappingSwRequirementModal: React.FunctionComponent<MappingSwRequirementModalProps> = ({
  baseApiUrl,
  modalShowState = false,
  setModalShowState,
  setCurrentLibrary,
  modalObject = "",
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
  }: MappingSwRequirementModalProps) => {
  const [isModalOpen, setIsModalOpen] = React.useState(false);
  let [modalFormSubmitState, setModalFormSubmitState] = React.useState('waiting');

  const handleModalConfirm = () => {
    setModalFormSubmitState('submitted');
    {/*}handleModalToggle();*/}
  }


  const handleModalToggle = (_event: KeyboardEvent | React.MouseEvent) => {
    let new_state = !modalShowState;
    setModalShowState(new_state);
    setIsModalOpen(new_state);
  };

  React.useEffect(() => {
    setIsModalOpen(modalShowState);
  }, [modalShowState]);


  const [activeTabKey, setActiveTabKey] = React.useState<string | number>(0);
  // Toggle currently active tab
  const handleTabClick = (
  event: React.MouseEvent<any> | React.KeyboardEvent | MouseEvent,
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
          id="tab-btn-sw-requirement-data"
          eventKey={0}
          title={<TabTitleText>Sw Requirement Data</TabTitleText>}
          tabContentId="tabNewTestCase"
          tabContentRef={newItemRef}
        />
        <Tab
          id="tab-btn-sw-requirement-mapping-section"
          eventKey={1}
          title={<TabTitleText>Mapping Section</TabTitleText>}
          tabContentId="tabSection"
          tabContentRef={sectionItemsRef}
        />
        <Tab
          id="tab-btn-sw-requirement-existing"
          eventKey={2}
          isDisabled={modalVerb == 'POST' ? false : true}
          title={<TabTitleText>Existing</TabTitleText>}
          tabContentId="tabExistingTestCase"
          tabContentRef={existingItemsRef}
        />
      </Tabs>
      <div>
        <TabContent eventKey={0} id="tabContentSwRequirementForm" ref={newItemRef}>
          <TabContentBody hasPadding>
            <SwRequirementForm
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
        <TabContent eventKey={1} id="tabContentSwRequirementSection" ref={sectionItemsRef} hidden>
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
        <TabContent eventKey={2} id="tabContentSwRequirementExisting" ref={existingItemsRef} hidden>
          <TabContentBody hasPadding>
            <SwRequirementSearch
              api={api}
              parentData={parentData}
              parentType={parentType}
              formVerb={modalVerb}
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
      </div>

      </Modal>
    </React.Fragment>
  );
};
