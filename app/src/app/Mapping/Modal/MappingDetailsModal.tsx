import React from 'react';
import {
  Button,
  Modal,
  ModalVariant,
  Text,
  TextContent,
  TextList,
  TextListItem,
  TextVariants,
} from '@patternfly/react-core';
import { MappingModalProps } from './MappingModalProps';

export const MappingDetailsModal: React.FunctionComponent<MappingModalProps> = ({
  modalShowState = false,
  setModalShowState,
  modalTitle = "",
  modalDescription = "",
  modalData,
  }: MappingModalProps) => {
  const [isModalOpen, setIsModalOpen] = React.useState(false);

  const handleModalToggle = (_event: KeyboardEvent | React.MouseEvent) => {
    let new_state = !modalShowState;
    setModalShowState(new_state);
    setIsModalOpen(new_state);
  };

  React.useEffect(() => {
    setIsModalOpen(modalShowState);
  }, [modalShowState]);

  const getDetails = () => {
    if (modalData == undefined){
      return "";
    }
    if (modalData.length == 0){
      return "";
    } else {
      return modalData.map((version, versionIndex) => (
        <React.Fragment key={versionIndex}>
          <TextContent>
          <TextList>
            {Object.keys(version).map((key, index) => (
                <TextListItem><em><b>{key}</b>: </em>{version[key]}</TextListItem>
            ))}
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
            Cancel
          </Button>
        ]}
      >

      {getDetails()}

      </Modal>
    </React.Fragment>
  );
};
