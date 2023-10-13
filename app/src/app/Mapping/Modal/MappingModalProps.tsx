import React from 'react';

export interface MappingModalProps {
  api;
  baseApiUrl: string;
  modalAction: string;
  modalVerb: string;
  modalObject: string;
  modalTitle: string;
  modalDescription: string;
  modalShowState: string;
  modalFormData;
  modalData;
  modalSection;
  modalIndirect;
  modalOffset;
  modalHistoryData;
  parentType;
  parentRelatedToType;
  loadMappingData;
  setModalShowState;
}
