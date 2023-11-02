import React from 'react';
import { ActionGroup, Button, FormGroup, FormHelperText, HelperText, HelperTextItem, Hint, HintBody, TextInput} from '@patternfly/react-core';
import {
  DataList,
  DataListAction,
  DataListCell,
  DataListItem,
  DataListItemCells,
  DataListItemRow,
  SearchInput,
} from '@patternfly/react-core';

export interface TestSpecificationSearchProps {
  api;
  baseApiUrl: str;
  formDefaultButtons: int;
  formVerb: str;
  formData;
  formMessage: string;
  parentData;
  parentType: string;
  handleModalToggle;
  modalOffset;
  modalSection;
  modalIndirect;
  loadMappingData;
}

export const TestSpecificationSearch: React.FunctionComponent<TestSpecificationSearchProps> = ({
    api,
    baseApiUrl,
    formDefaultButtons= 1,
    formVerb='POST',
    formData = {'id': 0,
                'title': '',
                'preconditions': '',
                'test_description': '',
                'expected_behavior': ''},
    formMessage = "",
    parentData,
    parentType = "",
    handleModalToggle,
    modalOffset,
    modalSection,
    modalIndirect,
    loadMappingData,
    }: TestSpecificationSearchProps) => {

    const [searchValue, setSearchValue] = React.useState(formData.title);
    const [messageValue, setMessageValue] = React.useState(formMessage);
    const [statusValue, setStatusValue] = React.useState('waiting');
    const [testSpecifications, setTestSpecifications] = React.useState([]);
    const [selectedDataListItemId, setSelectedDataListItemId] = React.useState('');

    const [coverageValue, setCoverageValue] = React.useState(formData.coverage);
    const [validatedCoverageValue, setValidatedCoverageValue] = React.useState<validate>('error');

    const resetForm = () => {
        setSelectedDataListItemId(-1);
        setCoverageValue("0");
        setSearchValue("");
    }

    React.useEffect(() => {
        if (coverageValue === '') {
          setValidatedCoverageValue('default');
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

    const handleCoverageValueChange = (_event, value: string) => {
        setCoverageValue(value);
    };

    const onChangeSearchValue = (value) => {
      setSearchValue(value);
    }

    const onSelectDataListItem = (_event: React.MouseEvent | React.KeyboardEvent, id: string) => {
      setSelectedDataListItemId(id);
    };

    const handleInputChange = (_event: React.FormEvent<HTMLInputElement>, id: string) => {
      setSelectedDataListItemId(id);
    };

    React.useEffect(() => {
        loadTestSpecifications(searchValue);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [searchValue]);

    const loadTestSpecifications = (searchValue) => {
      const url = baseApiUrl + '/test-specifications?search=' + searchValue;
      fetch(url)
        .then((res) => res.json())
        .then((data) => {
            setTestSpecifications(data);
        })
        .catch((err) => {
          console.log(err.message);
        });
    }

    const getTestSpecificationsTable = (test_specifications) => {
      return test_specifications.map((test_specification, tsIndex) => (
        <DataListItem key={test_specification.id} aria-labelledby={"clickable-action-item-" + test_specification.id} id={test_specification.id}>
          <DataListItemRow>
            <DataListItemCells
              dataListCells={[
                <DataListCell key={tsIndex}>
                  <span id={"clickable-action-item-" + test_specification.id}>{test_specification.title}</span>
                </DataListCell>,
              ]}
            />
            <DataListAction
              aria-labelledby={"clickable-action-item-" + test_specification.id + " clickable-action-action-" + test_specification.id}
              id={"clickable-action-action-" + test_specification.id}
              aria-label="Actions"
              isPlainButtonAction
            >
            </DataListAction>
          </DataListItemRow>
        </DataListItem>
      ))
    }

    React.useEffect(() => {
        if (statusValue == 'submitted'){
          handleSubmit();
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [statusValue]);

    const handleSubmit = () => {
        if ((selectedDataListItemId == -1) || (selectedDataListItemId == '') || (selectedDataListItemId == undefined)){
            setMessageValue('Please, select an item before submitting the form.');
            setStatusValue('waiting');
            return;
        } else if (validatedCoverageValue != 'success'){
            setMessageValue('Coverage of Parent Item is mandatory and must be a integer value in the range 0-100.');
            setStatusValue('waiting');
            return;
        } else if (modalSection.trim().length==0){
            setMessageValue('Section of the software component specification is mandatory.');
            setStatusValue('waiting');
            return;
        }

        setMessageValue('');

        const data = {
          'api-id': api.id,
          'test-specification': {'id': selectedDataListItemId},
          'sw-requirement': {},
          'section': modalSection,
          'offset': modalOffset,
          'coverage': coverageValue,
        }

        if ((formVerb == 'PUT') || (formVerb == 'DELETE')){
          setMessageValue('Wrong actions.');
          setStatusValue('waiting');
          return;
        }

        if (modalIndirect == true){
          console.log("parentData: " + JSON.stringify(parentData));
          data['relation-id'] = parentData.relation_id;
          data['sw-requirement']['id'] = parentData.id;
        }

        fetch(baseApiUrl + '/mapping/' + parentType + '/test-specifications', {
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
              setStatusValue('waiting');
              setMessageValue('Database updated!');
              handleModalToggle();
              setMessageValue('');
              loadMappingData();
            }
          })
          .catch((err) => {
            setStatusValue('waiting');
            setMessageValue(err.toString());
            console.log(err.message);
          });
      };

    return (
        <React.Fragment>
        <SearchInput
          placeholder="Search Identifier"
          value={searchValue}
          onChange={(_event, value) => onChangeSearchValue(value)}
          onClear={() => onChangeSearchValue('')}
          style={{width:'400px'}}
        />
        <br />
        <DataList
          isCompact
          aria-label="clickable data list example"
          selectedDataListItemId={selectedDataListItemId}
          onSelectDataListItem={onSelectDataListItem}
          onSelectableRowChange={handleInputChange}
        >
          {getTestSpecificationsTable(testSpecifications)}
        </DataList>
        <br />
        <FormGroup label="Unique Coverage:" isRequired fieldId={`input-test-specification-coverage-${formData.id}`}>
          <TextInput
            isRequired
            id={`input-test-specification-coverage-${formData.id}`}
            name={`input-test-specification-coverage-${formData.id}`}
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

        <br />

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

        </React.Fragment>
   );
};
