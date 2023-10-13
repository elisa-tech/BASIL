import React from 'react';
import { Form, FormGroup, HelperText, HelperTextItem, FormHelperText, Button, TextInput, TextArea, ActionGroup, Hint, HintBody} from '@patternfly/react-core';

export interface JustificationFormProps {
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

export const JustificationForm: React.FunctionComponent<JustificationFormProps> = ({
    api,
    baseApiUrl,
    formAction="add",
    formData={'id': 0,
              'description': '',
              'coverage': 100},
    formDefaultButtons=1,
    formMessage='',
    formVerb,
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
    }: JustificationFormProps) => {

    type validate = 'success' | 'warning' | 'error' | 'default';

    const [descriptionValue, setDescriptionValue] = React.useState(formData.description);
    const [validatedDescriptionValue, setValidatedDescriptionValue] = React.useState<validate>('error');

    const [coverageValue, setCoverageValue] = React.useState(formData.coverage);
    const [validatedCoverageValue, setValidatedCoverageValue] = React.useState<validate>('error');

    const [messageValue, setMessageValue] = React.useState(formMessage);

    const [statusValue, setStatusValue] = React.useState('waiting');

    const _J = 'justification';

    const resetForm = () => {
        setDescriptionValue("");
        setCoverageValue("100");
    }

    React.useEffect(() => {
      if (descriptionValue == undefined) {
        setDescriptionValue("");
      } else {
        if (descriptionValue.trim() === '') {
          setValidatedDescriptionValue('error');
        } else {
            setValidatedDescriptionValue('success');
          }
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

    const handleDescriptionValueChange = (_event, value: string) => {
        setDescriptionValue(value);
    };

    const handleCoverageValueChange = (_event, value: string) => {
        setCoverageValue(value);
    };

    const handleSubmit = () => {
        if (validatedDescriptionValue != 'success'){
            setMessageValue('Justification Description is mandatory.');
            setStatusValue('waiting');
            return;
        } else if (validatedCoverageValue != 'success'){
            setMessageValue('Justification Coverage of Parent Item is mandatory and must be a integer value in the range 0-100.');
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
          'justification': {'description': descriptionValue},
          'section': modalSection,
          'offset': modalOffset,
          'coverage': coverageValue,
        }

        if ((formVerb == 'PUT') || (formVerb == 'DELETE')){
          data['relation-id'] = formData.relation_id;
          data['justification']['id'] = formData.id;
        }

        fetch(baseApiUrl + '/mapping/api/justifications', {
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
          <FormGroup label="Description" isRequired fieldId={`input-justification-description-${formData.id}`}>
            <TextArea
              isRequired
              resizeOrientation="vertical"
              aria-label="Justification description field"
              id={`input-justification-description-${formData.id}`}
              name={`input-justification-description-${formData.id}`}
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

          <FormGroup label="Unique Coverage:" isRequired fieldId={`input-justification-coverage-${formData.id}`}>
            <TextInput
              isRequired
              id={`input-justification-coverage-${formData.id}`}
              name={`input-justification-coverage-${formData.id}`}
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
                variant="primary"
                onClick={() => setStatusValue('submitted')}>
              Submit
              </Button>
              <Button
                variant="secondary"
                onClick={resetForm}>
                Reset
              </Button>
            </ActionGroup>
          ) : (<span></span>)}
        </Form>
   );
};
