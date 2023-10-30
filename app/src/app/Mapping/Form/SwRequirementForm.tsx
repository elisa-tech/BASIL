import React from 'react';
import { Form, FormGroup, HelperText, HelperTextItem, FormHelperText, Button, TextInput, TextArea, ActionGroup, Hint, HintBody} from '@patternfly/react-core';

export interface SwRequirementFormProps {
  api;
  baseApiUrl: str;
  formAction: str;
  formData;
  formDefaultButtons: int;
  formMessage: string;
  formVerb: str;
  handleModalToggle;
  loadMappingData;
  modalFormSubmitState: string;
  modalIndirect;
  modalOffset;
  modalSection;
  parentData;
  parentRelatedToType;
  parentType;
  setModalFormSubmitState;
}

export const SwRequirementForm: React.FunctionComponent<SwRequirementFormProps> = ({
    api,
    baseApiUrl,
    formAction="add",
    formData={'id': 0,
              'coverage': '0',
              'title': '',
              'description': '',},
    formDefaultButtons=1,
    formMessage='',
    formVerb='POST',
    handleModalToggle,
    loadMappingData,
    modalFormSubmitState="waiting",
    modalIndirect,
    modalOffset,
    modalSection,
    parentData,
    parentRelatedToType,
    parentType,
    setModalFormSubmitState,
    }: SwRequirementFormProps) => {

    type validate = 'success' | 'warning' | 'error' | 'default';

    const [titleValue, setTitleValue] = React.useState(formData.title);
    const [validatedTitleValue, setValidatedTitleValue] = React.useState<validate>('error');

    const [descriptionValue, setDescriptionValue] = React.useState(formData.description);
    const [validatedDescriptionValue, setValidatedDescriptionValue] = React.useState<validate>('error');

    const [coverageValue, setCoverageValue] = React.useState(formData.coverage != '' ? formData.coverage : '0');
    const [validatedCoverageValue, setValidatedCoverageValue] = React.useState<validate>('error');

    const [messageValue, setMessageValue] = React.useState(formMessage);

    const [statusValue, setStatusValue] = React.useState('waiting');

    const _SR = 'sw-requirement';


    const resetForm = () => {
        setTitleValue("");
        setDescriptionValue("");
        setCoverageValue("0");
    }

    React.useEffect(() => {
      if (titleValue == undefined) {
        setTitleValue("");
      } else {
        if (titleValue.trim() === '') {
          setValidatedTitleValue('error');
        } else {
          setValidatedTitleValue('success');
        }
      }
    }, [titleValue]);

    React.useEffect(() => {
      if (descriptionValue.trim() === '') {
          setValidatedDescriptionValue('error');
        } else {
          setValidatedDescriptionValue('success');
        }
    }, [descriptionValue]);

    React.useEffect(() => {
        if (coverageValue === '') {
          setValidatedCoverageValue('error');
        } else if (/^\d+$/.test(coverageValue)) {
          if ((coverageValue >= 0) && (coverageValue <= 100)){
            setValidatedCoverageValue('success');
          } else {
            setValidatedCoverageValue('error');
          }
        } else {
          setValidatedCoverageValue('error');
        }
    }, [coverageValue]);

    React.useEffect(() => {
        if (statusValue == 'submitted'){
          handleSubmit();
        }
    }, [statusValue]);

    React.useEffect(() => {
        if (modalFormSubmitState == 'submitted'){
          handleSubmit();
        }
    }, [modalFormSubmitState]);

    const handleTitleValueChange = (_event, value: string) => {
        setTitleValue(value);
    };

    const handleDescriptionValueChange = (_event, value: string) => {
        setDescriptionValue(value);
    };

    const handleCoverageValueChange = (_event, value: string) => {
        setCoverageValue(value);
    };


    const handleSubmit = () => {

        if (validatedTitleValue != 'success'){
            setMessageValue('Sw Requirement Title is mandatory.');
            setStatusValue('waiting');
            return;
        } else if (validatedDescriptionValue != 'success'){
            setMessageValue('Sw Requirement Description is mandatory.');
            setStatusValue('waiting');
            return;
        } else if (validatedCoverageValue != 'success'){
            setMessageValue('Sw Requirement Coverage of Parent Item is mandatory and must be a integer value in the range 0-100.');
            setStatusValue('waiting');
            return;
        } else if (modalSection.trim().length==0){
            setMessageValue('Section of the software component specification is mandatory.');
            setStatusValue('waiting');
            return;
        }

        setMessageValue('');

        let data = {
          'api-id': api.id,
          'sw-requirement': {'title': titleValue,
                             'description': descriptionValue},
          'section': modalSection,
          'offset': modalOffset,
          'coverage': coverageValue,
        }

        if ((formVerb == 'PUT') || (formVerb == 'DELETE')){
          data['relation-id'] = formData.relation_id;
          data['sw-requirement']['id'] = formData.id;
        }

        fetch(baseApiUrl + '/mapping/api/sw-requirements', {
          method: formVerb,
          headers: {
            Accept: 'application/json',
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(data),
        })
          .then((response) => {
            if (response.status !== 200) {
              setMessageValue(response.statusText);
              setStatusValue('waiting');
            } else {
              handleModalToggle();
              setMessageValue('');
              setStatusValue('waiting');
              loadMappingData();
            }
          })
          .catch((err) => {
            setMessageValue(err.toString());
            setStatusValue('waiting');
          });
      };

    return (
        <Form>
          <FormGroup label="Sw Requirement Title" isRequired fieldId={`input-sw-requirement-${formAction}-title-${formData.id}`}>
            <TextInput
              isRequired
              id={`input-sw-requirement-${formAction}-title-${formData.id}`}
              name={`input-sw-requirement-${formAction}-title-${formData.id}`}
              value={titleValue || ''}
              onChange={(_ev, value) => handleTitleValueChange(_ev, value)}
            />
            {validatedTitleValue !== 'success' && (
              <FormHelperText>
                <HelperText>
                  <HelperTextItem variant={validatedTitleValue}>
                    {validatedTitleValue === 'error' ? 'This field is mandatory' : ''}
                  </HelperTextItem>
                </HelperText>
              </FormHelperText>
            )}
          </FormGroup>
          <FormGroup label="Description" isRequired fieldId={`input-sw-requirement-${formAction}-description-${formData.id}`}>
            <TextArea
              isRequired
              resizeOrientation="vertical"
              aria-label="Sw Requirement description field"
              id={`input-sw-requirement-${formAction}-description-${formData.id}`}
              name={`input-sw-requirement-${formAction}-description-${formData.id}`}
              value={descriptionValue || ''}
              onChange={(_ev, value) => handleDescriptionValueChange(_ev, value)}
            />
            {validatedDescriptionValue !== 'success' && (
              <FormHelperText>
                <HelperText>
                  <HelperTextItem variant={validatedDescriptionValue}>
                    {validatedDescriptionValue === 'error' ? 'This field is mandatory' : ''}
                  </HelperTextItem>
                </HelperText>
              </FormHelperText>
            )}
          </FormGroup>
          <FormGroup label="Unique Coverage:" fieldId={`input-sw-requirement-${formAction}-coverage-${formData.id}`}>
            <TextInput
              id={`input-sw-requirement-${formAction}-coverage-${formData.id}`}
              name={`input-sw-requirement-${formAction}-coverage-${formData.id}`}
              value={coverageValue || ''}
              onChange={(_ev, value) => handleCoverageValueChange(_ev, value)}
            />
            {validatedCoverageValue !== 'success' && (
              <FormHelperText>
                <HelperText>
                  <HelperTextItem variant={validatedCoverageValue}>
                    {validatedCoverageValue === 'error' ? 'Must be an integer number in the range 0-100' : ''}
                  </HelperTextItem>
                </HelperText>
              </FormHelperText>
            )}
          </FormGroup>

          { messageValue ? (
          <Hint>
            <HintBody>
              {messageValue}
            </HintBody>
          </Hint>
          ) : (<span></span>)}

          {formDefaultButtons ? (
            <ActionGroup>
              <Button
                id="btn-mapping-sw-requirement-submit"
                variant="primary"
                onClick={() => setStatusValue('submitted')}>
              Submit
              </Button>
              <Button
                id="btn-mapping-sw-requirement-reset"
                variant="secondary"
                onClick={resetForm}>
                Reset
              </Button>
            </ActionGroup>
          ) : (<span></span>)}
        </Form>
   );
};
