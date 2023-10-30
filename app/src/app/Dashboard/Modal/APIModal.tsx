import React from 'react';
import { Modal, ModalVariant, Form, FormGroup, Popover, Button, TextInput} from '@patternfly/react-core';
import { APIForm } from '../Form/APIForm';

export interface APIModalProps {
  baseApiUrl: string;
  modalAction: string;
  modalVerb: string;
  modalObject: string;
  modalTitle: string;
  modalDescription: string;
  modalShowState: string;
  modalFormData;
  setCurrentLibrary;
  loadLibraries;
  loadApi;
  setModalShowState;
}

export const APIModal: React.FunctionComponent<APIModalProps> = ({
  baseApiUrl,
  modalShowState = false,
  setModalShowState,
  setCurrentLibrary,
  loadLibraries,
  loadApi,
  modalObject = "",
  modalAction = "",
  modalVerb = "",
  modalTitle = "",
  modalFormData,
  modalDescription = "",
  }: APIModalProps) => {
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
            id="btn-modal-api-confirm"
            key="confirm"
            variant="primary"
            onClick={() => handleModalConfirm()}>
            Confirm
          </Button>,
          <Button
            id="btn-modal-api-reset"
            key="cancel"
            variant="link"
            onClick={handleModalToggle}>
            Cancel
          </Button>
        ]}
      >
        <APIForm
          baseApiUrl={baseApiUrl}
          formAction={modalAction}
          formVerb={modalVerb}
          formDefaultButtons={0}
          formData={modalFormData}
          modalFormSubmitState={modalFormSubmitState}
          setModalFormSubmitState={setModalFormSubmitState}
          setCurrentLibrary={setCurrentLibrary}
          loadLibraries={loadLibraries}
          loadApi={loadApi}
          handleModalToggle={handleModalToggle}
          />
      </Modal>
    </React.Fragment>
  );
};
