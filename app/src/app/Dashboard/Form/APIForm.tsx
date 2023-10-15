import React from 'react';
import { Form, FormGroup, HelperText, HelperTextItem, FormHelperText, Button, TextInput, ActionGroup, Hint, HintBody} from '@patternfly/react-core';

export interface APIFormProps {
  baseApiUrl: str;
  formDefaultButtons: int;
  formVerb: str;
  formAction: str;
  formData;
  formMessage: string;
  modalFormSubmitState: string;
  setModalFormSubmitState;
  setCurrentLibrary;
  loadLibraries;
  loadApi;
  handleModalToggle;
}

export const APIForm: React.FunctionComponent<APIFormProps> = ({
    baseApiUrl,
    formDefaultButtons= 1,
    formVerb='POST',
    formAction='add',
    formData = {'id': 0,
                'api': '',
                'library': '',
                'library_version': '',
                'raw_specification_url': '',
                'category': '',
                'tags': '',
                'implementation_file_from_row': '',
                'implementation_file_to_row': '',
                'implementation_file': '',},
    formMessage = "",
    modalFormSubmitState = "waiting",
    setModalFormSubmitState,
    setCurrentLibrary,
    loadLibraries,
    loadApi,
    handleModalToggle,
    }: APIFormProps) => {

    type validate = 'success' | 'warning' | 'error' | 'default';

    const [apiValue, setApiValue] = React.useState(formData.api);
    const [validatedApiValue, setValidatedApiValue] = React.useState<validate>('error');

    const [libraryValue, setLibraryValue] = React.useState(formData.library);
    const [validatedLibraryValue, setValidatedLibraryValue] = React.useState<validate>('error');

    const [libraryVersionValue, setLibraryVersionValue] = React.useState(formAction == 'fork' ? '' : formData.library_version);
    const [validatedLibraryVersionValue, setValidatedLibraryVersionValue] = React.useState<validate>('error');

    const [rawSpecificationUrlValue, setRawSpecificationUrlValue] = React.useState(formData.raw_specification_url);
    const [validatedRawSpecificationUrlValue, setValidatedRawSpecificationUrlValue] = React.useState<validate>('error');

    const [categoryValue, setCategoryValue] = React.useState(formData.category);

    const [tagsValue, setTagsValue] = React.useState(formData.tags);

    const [implementationFileValue, setImplementationFileValue] = React.useState(formData.implementation_file);

    const [implementationFileFromRowValue, setImplementationFileFromRowValue] = React.useState(formData.implementation_file_from_row);
    const [validatedImplementationFileFromRowValue, setValidatedImplementationFileFromRowValue] = React.useState<validate>('error');

    const [implementationFileToRowValue, setImplementationFileToRowValue] = React.useState(formData.implementation_file_to_row);
    const [validatedImplementationFileToRowValue, setValidatedImplementationFileToRowValue] = React.useState<validate>('error');

    const [messageValue, setMessageValue] = React.useState(formMessage);

    const [statusValue, setStatusValue] = React.useState('waiting');

    React.useEffect(() => {
      if (apiValue.trim() === '') {
          setValidatedApiValue('error');
        } else {
          setValidatedApiValue('success');
        }
    }, [apiValue]);

    React.useEffect(() => {
      if (libraryValue.trim() === '') {
          setValidatedLibraryValue('error');
        } else {
          setValidatedLibraryValue('success');
        }
    }, [libraryValue]);

   React.useEffect(() => {
      if (libraryVersionValue.trim() === '') {
          setValidatedLibraryVersionValue('error');
        } else {
          setValidatedLibraryVersionValue('success');
        }
    }, [libraryVersionValue]);

    React.useEffect(() => {
       if (rawSpecificationUrlValue.trim() === '') {
          setValidatedRawSpecificationUrlValue('error');
        } else {
          setValidatedRawSpecificationUrlValue('success');
        }
    }, [rawSpecificationUrlValue]);

    React.useEffect(() => {
        if (implementationFileFromRowValue === '') {
          setValidatedImplementationFileFromRowValue('default');
        } else if (/^\d+$/.test(implementationFileFromRowValue)) {
          setValidatedImplementationFileFromRowValue('success');
        } else {
          setValidatedImplementationFileFromRowValue('error');
        }
    }, [implementationFileFromRowValue]);

    React.useEffect(() => {
        if (implementationFileToRowValue === '') {
          setValidatedImplementationFileToRowValue('default');
        } else if (/^\d+$/.test(implementationFileToRowValue)) {
          setValidatedImplementationFileToRowValue('success');
        } else {
          setValidatedImplementationFileToRowValue('error');
        }
    }, [implementationFileToRowValue]);

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

    const handleApiValueChange = (_event, value: string) => {
        setApiValue(value);
    };

    const handleLibraryValueChange = (_event, value: string) => {
        setLibraryValue(value);
    };

    const handleLibraryVersionValueChange = (_event, value: string) => {
        setLibraryVersionValue(value);
    };

    const handleRawSpecificationUrlValueChange = (_event, value: string) => {
        setRawSpecificationUrlValue(value);
    };

    const handleImplementationFileValueChange = (_event, value: string) => {
        setImplementationFileValue(value);
    };

    const handleImplementationFileFromRowValueChange = (_event, value: string) => {
        setImplementationFileFromRowValue(value);
    };

    const handleImplementationFileToRowValueChange = (_event, value: int) => {
        setImplementationFileToRowValue(value);
    };

    const handleCategoryValueChange = (_event, value: string) => {
        setCategoryValue(value);
    };

    const handleTagsValueChange = (_event, value: string) => {
        setTagsValue(value);
    };

    const handleSubmit = () => {
        if (formVerb=='POST'){
          {/*Only post handled in modal window*/}
          setModalFormSubmitState('waiting');
        }

        if (validatedApiValue != 'success'){
            setMessageValue('Software Component Name is mandatory.'); return;
        } else if (validatedLibraryValue != 'success'){
            setMessageValue('Software Component Library is mandatory.'); return;
        } else if (validatedLibraryVersionValue != 'success'){
            setMessageValue('Software Component Library Version is mandatory.'); return;
        } else if (validatedRawSpecificationUrlValue != 'success'){
            setMessageValue('Software Component Specification Url/Path is mandatory.'); return;
        } else if (validatedImplementationFileFromRowValue == 'error'){
            setMessageValue('Wrong value for Implementation File From Row.'); return;
        } else if (validatedImplementationFileToRowValue == 'error'){
            setMessageValue('Wrong value for Implementation File To Row.'); return;
        }

        setMessageValue('');
        let data = {
          'action': formAction,
          'api-id': formData.id,
          'api': apiValue,
          'library': libraryValue,
          'library-version': libraryVersionValue,
          'category': categoryValue,
          'tags': tagsValue,
          'implementation-file': implementationFileValue,
          'implementation-file-from-row': implementationFileFromRowValue,
          'implementation-file-to-row': implementationFileToRowValue,
          'raw-specification-url': rawSpecificationUrlValue,
        }

        fetch(baseApiUrl + '/apis', {
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
            } else {
              setMessageValue('Database updated!');
              if (formVerb=='POST'){
                window.location = "/?currentLibrary=" + libraryValue;
              }
            }
          })
          .catch((err) => {
            setMessageValue(err.toString());
            console.log(err.message);
          });
      };

    return (
        <Form>
          <FormGroup label="Software Component Name" isRequired fieldId={`input-api-api-${formData.id}`}>
            <TextInput
              isRequired
              id={`input-api-api-${formData.id}`}
              name={`input-api-api-${formData.id}`}
              value={apiValue || ''}
              onChange={(_ev, value) => handleApiValueChange(_ev, value)}
            />
            {validatedApiValue !== 'success' && (
              <FormHelperText>
                <HelperText>
                  <HelperTextItem variant={validatedApiValue}>
                    {validatedApiValue === 'error' ? 'This field is mandatory' : ''}
                  </HelperTextItem>
                </HelperText>
              </FormHelperText>
            )}
          </FormGroup>
          <FormGroup label="Library" isRequired fieldId={`input-api-library-${formData.id}`}>
            <TextInput
              isRequired
              id={`input-api-library-${formData.id}`}
              name={`input-api-library-${formData.id}`}
              value={libraryValue || ''}
              onChange={(_ev, value) => handleLibraryValueChange(_ev, value)}
            />
            {validatedLibraryValue !== 'success' && (
              <FormHelperText>
                <HelperText>
                  <HelperTextItem variant={validatedLibraryValue}>
                    {validatedLibraryValue === 'error' ? 'This field is mandatory' : ''}
                  </HelperTextItem>
                </HelperText>
              </FormHelperText>
            )}
          </FormGroup>
          <FormGroup label="Library Version" isRequired fieldId={`input-api-library-version-${formData.id}`}>
            <TextInput
              isRequired
              id={`input-api-library-version-${formData.id}`}
              name={`input-api-library-version-${formData.id}`}
              value={libraryVersionValue || ''}
              onChange={(_ev, value) => handleLibraryVersionValueChange(_ev, value)}
            />
            {validatedLibraryVersionValue !== 'success' && (
              <FormHelperText>
                <HelperText>
                  <HelperTextItem variant={validatedLibraryVersionValue}>
                    {validatedLibraryVersionValue === 'error' ? 'This field is mandatory' : ''}
                  </HelperTextItem>
                </HelperText>
              </FormHelperText>
            )}
          </FormGroup>
          <FormGroup label="Specification Url/Path (plain text format):" isRequired fieldId={`input-api-raw-specification-url-${formData.id}`}>
            <TextInput
              isRequired
              id={`input-api-raw-specification-url-${formData.id}`}
              name={`input-api-raw-specification-url-${formData.id}`}
              value={rawSpecificationUrlValue || ''}
              onChange={(_ev, value) => handleRawSpecificationUrlValueChange(_ev, value)}
            />
            {validatedRawSpecificationUrlValue !== 'success' && (
              <FormHelperText>
                <HelperText>
                  <HelperTextItem variant={validatedRawSpecificationUrlValue}>
                    {validatedRawSpecificationUrlValue === 'error' ? 'This field is mandatory' : ''}
                  </HelperTextItem>
                </HelperText>
              </FormHelperText>
            )}
          </FormGroup>
          <FormGroup label="Category:" fieldId={`input-api-category-${formData.id}`}>
            <TextInput
              isRequired
              id={`input-api-category-${formData.id}`}
              name={`input-api-category-${formData.id}`}
              value={categoryValue || ''}
              onChange={(_ev, value) => handleCategoryValueChange(_ev, value)}
            />
          </FormGroup>
          <FormGroup label="Implementation file Url/Path:" fieldId={`input-api-implementation-file-${formData.id}`}>
            <TextInput
              isRequired
              id={`input-api-implementation-file-${formData.id}`}
              name={`input-api-implementation-file-${formData.id}`}
              value={implementationFileValue || ''}
              onChange={(_ev, value) => handleImplementationFileValueChange(_ev, value)}
            />
          </FormGroup>
          <FormGroup label="Implementation file from row number:" fieldId={`input-api-implementation-file-from-row-${formData.id}`}>
            <TextInput
              id={`input-api-implementation-file-from-row-${formData.id}`}
              name={`input-api-implementation-file-from-row-${formData.id}`}
              value={implementationFileFromRowValue || ''}
              onChange={(_ev, value) => handleImplementationFileFromRowValueChange(_ev, value)}
            />
            {validatedImplementationFileFromRowValue !== 'success' && (
              <FormHelperText>
                <HelperText>
                  <HelperTextItem variant={validatedImplementationFileFromRowValue}>
                    {validatedImplementationFileFromRowValue === 'error' ? 'Must be a number' : ''}
                  </HelperTextItem>
                </HelperText>
              </FormHelperText>
            )}
          </FormGroup>
          <FormGroup label="Implementation file to row number:" fieldId={`input-api-implementation-file-to-row-${formData.id}`}>
            <TextInput
              id={`input-api-implementation-file-to-row-${formData.id}`}
              name={`input-api-implementation-file-to-row-${formData.id}`}
              value={implementationFileToRowValue || ''}
              onChange={(_ev, value) => handleImplementationFileToRowValueChange(_ev, value)}
            />
            {validatedImplementationFileToRowValue !== 'success' && (
              <FormHelperText>
                <HelperText>
                  <HelperTextItem variant={validatedImplementationFileToRowValue}>
                    {validatedImplementationFileToRowValue === 'error' ? 'Must be a number' : ''}
                  </HelperTextItem>
                </HelperText>
              </FormHelperText>
            )}
          </FormGroup>
          <FormGroup label="Tags:" fieldId={`input-api-tags-${formData.id}`}>
            <TextInput
              id={`input-api-tags-${formData.id}`}
              name={`input-api-tags-${formData.id}`}
              value={tagsValue || ''}
              onChange={(_ev, value) => handleTagsValueChange(_ev, value)}
            />
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
              <Button variant="link">Reset</Button>
            </ActionGroup>
          ) : (<span></span>)}
        </Form>
   );
};
