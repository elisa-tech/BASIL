import React from 'react';
import { Modal, ModalVariant, Form, FormGroup, Popover, Button, TextInput} from '@patternfly/react-core';
import { Tabs, Tab, TabTitleText, TabContent, TabContentBody } from '@patternfly/react-core';
import { JustificationForm } from '../Form/JustificationForm';
import { SectionForm } from '../Form/SectionForm';
import { JustificationSearch } from '../Search/JustificationSearch';
import { MappingModalProps } from './MappingModalProps';

export interface MappingJustificationModalProps {
  api;
  baseApiUrl: string;
  modalAction: string;
  modalVerb: string;
  modalObject: string;
  modalTitle: string;
  modalDescription: string;
  modalShowState: string;
  modalFormData;
  modalIndirect;
  modalOffset;
  setModalOffset;
  modalSection;
  setModalSection;
  parentData;
  parentType;
  parentRelatedToType;
  loadMappingData;
  setModalShowState;
}

export const MappingJustificationModal: React.FunctionComponent<MappingModalProps> = ({
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
  setModalOffset,
  modalSection,
  setModalSection,
  modalDescription = "",
  parentData,
  parentType='',
  parentRelatedToType='',
  loadMappingData,
  api,
  }: MappingModalProps) => {
  const [isModalOpen, setIsModalOpen] = React.useState(false);
  let [modalFormSubmitState, setModalFormSubmitState] = React.useState('waiting');

  const handleModalConfirm = () => {
    setModalFormSubmitState('submitted');
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
        aria-label="Add a New/Existing Justification"
        role="region"
      >
        <Tab
          eventKey={0}
          title={<TabTitleText>Justification Data</TabTitleText>}
          tabContentId="tabNewJustification"
          tabContentRef={newItemRef}
        />
        <Tab
          eventKey={1}
          title={<TabTitleText>Mapping Section</TabTitleText>}
          tabContentId="tabSection"
          tabContentRef={sectionItemsRef}
        />
        <Tab
          isDisabled={modalVerb == 'POST' ? false : true}
          eventKey={2}
          title={<TabTitleText>Existing</TabTitleText>}
          tabContentId="tabExistingJustification"
          tabContentRef={existingItemsRef}
        />
      </Tabs>
      <div>
        <TabContent eventKey={0} id="tabNewJustification" ref={newItemRef}>
          <TabContentBody hasPadding>
            <JustificationForm
              api={api}
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
        <TabContent eventKey={1} id="tabSection" ref={sectionItemsRef} hidden>
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
        <TabContent eventKey={2} id="tabExistingJustification" ref={existingItemsRef} hidden>
          <TabContentBody hasPadding>
            <JustificationSearch
              api={api}
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
      </div>

      </Modal>
    </React.Fragment>
  );
};
