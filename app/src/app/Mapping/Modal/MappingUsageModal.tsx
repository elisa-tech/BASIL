import React from 'react';
import {
  Button,
  Modal,
  ModalVariant,
  TextContent,
  TextList,
  TextListItem,
} from '@patternfly/react-core';

import { MappingModalProps } from './MappingModalProps';

export const MappingUsageModal: React.FunctionComponent<MappingModalProps> = ({
  modalShowState = false,
  setModalShowState,
  modalTitle = "",
  modalDescription = "",
  modalData,
  }: MappingModalProps) => {

  const [isModalOpen, setIsModalOpen] = React.useState(false);

  React.useEffect(() => {
    setIsModalOpen(modalShowState);
  }, [modalShowState]);


  const handleModalToggle = () => {
    const new_state = !modalShowState;
    setModalShowState(new_state);
    setIsModalOpen(new_state);
  };

  const getApiUsage = () => {
    if (modalData == undefined){
      return "";
    }
    if (modalData['api'] == undefined){
      return "";
    }
    if (modalData['api'].length == 0){
      return "";
    } else {
      return modalData['api'].map((api, apiIndex) => (
        <React.Fragment key={apiIndex}>
          <TextContent>
          <TextList>
            <TextListItem><em><b>{api.api}</b></em> from library {api.library} ver. {api.library_version}</TextListItem>
          </TextList>
          </TextContent>
        </React.Fragment>
      ));
    }
  }

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
            Close
          </Button>
        ]}>

       {getApiUsage()}

      </Modal>
    </React.Fragment>
  );
};
