import React from 'react';
import {
  Button,
  Hint,
  HintBody,
  Modal,
  ModalVariant
} from '@patternfly/react-core';

export interface MappingDeleteModalProps{
  api;
  baseApiUrl;
  modalShowState;
  setModalShowState;
  modalTitle;
  modalDescription;
  workItemType;
  parentType;
  parentRelatedToType;
  relationData;
  loadMappingData;
}

export const MappingDeleteModal: React.FunctionComponent<MappingDeleteModalProps> = ({
  api,
  baseApiUrl,
  modalShowState = false,
  setModalShowState,
  modalTitle = "",
  modalDescription = "",
  workItemType,
  parentType,
  parentRelatedToType,
  relationData,
  loadMappingData,
  }: MappingDeleteModalProps) => {
  const [isModalOpen, setIsModalOpen] = React.useState(false);
  const [messageValue, setMessageValue] = React.useState('');

  const handleModalToggle = (_event: KeyboardEvent | React.MouseEvent) => {
    let new_state = !modalShowState;
    setModalShowState(new_state);
    setIsModalOpen(new_state);
  };

  React.useEffect(() => {
    setIsModalOpen(modalShowState);
    if (modalShowState == false){
      setMessageValue("");
    }
  }, [modalShowState]);

  const deleteMapping = () => {
    let data = {'api-id': api.id,
                'relation-id': relationData.relation_id};
    fetch(baseApiUrl + '/mapping/' + parentType + '/' + workItemType + 's', {
      method: 'DELETE',
      headers: {
        Accept: 'application/json',
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    })
      .then((response) => {
        if (response.status !== 200) {
          setMessageValue(response.statusText);
        } else {
          loadMappingData();
          handleModalToggle();
        }
      })
      .catch((err) => {
        setMessageValue(err.toString());
      });
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
          <Button
            id="btn-mapping-delete-confirm"
            variant="primary"
            onClick={deleteMapping}>
            Confirm
          </Button>,
          <Button
            id="btn-mapping-delete-cancel"
            key="cancel"
            variant="link"
            onClick={handleModalToggle}>
            Cancel
          </Button>
        ]}
      >

      { messageValue ? (
      <Hint>
        <HintBody>
          {messageValue}
        </HintBody>
      </Hint>
      ) : (<span></span>)}

      </Modal>
    </React.Fragment>
  );
};
