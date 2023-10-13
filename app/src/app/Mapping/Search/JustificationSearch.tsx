import React from 'react';
import { Form, FormGroup, HelperText, HelperTextItem, FormHelperText, Button, TextInput, ActionGroup, Hint, HintBody} from '@patternfly/react-core';
import {
  DataList,
  DataListItem,
  DataListCell,
  DataListItemRow,
  DataListItemCells,
  DataListAction,
  SearchInput,
} from '@patternfly/react-core';

export interface JustificationSearchProps {
  api;
  baseApiUrl: str;
  formDefaultButtons: int;
  formVerb: str;
  formAction: str;
  formData;
  formMessage: string;
  parentType: string;
  modalFormSubmitState: string;
  setModalFormSubmitState;
  handleModalToggle;
  modalOffset;
  modalSection;
  loadMappingData;
}

export const JustificationSearch: React.FunctionComponent<JustificationSearchProps> = ({
    api,
    baseApiUrl,
    formDefaultButtons= 1,
    formVerb='POST',
    formAction='add',
    formData = {'id': 0,
                'description': ''},
    formMessage = "",
    parentType,
    modalFormSubmitState = "waiting",
    setModalFormSubmitState,
    handleModalToggle,
    modalOffset,
    modalSection,
    loadMappingData,
    }: JustificationSearchProps) => {

    const [searchValue, setSearchValue] = React.useState(formData.title);
    const [messageValue, setMessageValue] = React.useState(formMessage);
    const [statusValue, setStatusValue] = React.useState('waiting');
    const [justifications, setJustifications] = React.useState([]);
    const [selectedDataListItemId, setSelectedDataListItemId] = React.useState(-1);

    const [coverageValue, setCoverageValue] = React.useState(formData.coverage);
    const [validatedCoverageValue, setValidatedCoverageValue] = React.useState<validate>('error');

    const resetForm = () => {
        setSelectedDataListItemId(-1);
        setCoverageValue("0");
        setSearchValue("");
    }

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

    React.useEffect(() => {
        loadJustifications(searchValue);
    }, [searchValue]);

    const handleCoverageValueChange = (_event, value: string) => {
        setCoverageValue(value);
    };

    React.useEffect(() => {
        if (statusValue == 'submitted'){
          handleSubmit();
        }
    }, [statusValue]);

    const loadJustifications = (searchValue) => {
      let url = baseApiUrl + '/justifications';
      if (searchValue != undefined){
        url = url + '?search=' + searchValue;
      }
      fetch(url)
        .then((res) => res.json())
        .then((data) => {
            setJustifications(data);
        })
        .catch((err) => {
          console.log(err.message);
        });
    }

    const getJustificationsTable = (justifications) => {
      return justifications.map((justification, jIndex) => (
        <DataListItem key={justification.id} aria-labelledby={"clickable-action-item-" + justification.id} id={justification.id}>
          <DataListItemRow>
            <DataListItemCells
              dataListCells={[
                <DataListCell key="primary content">
                  <span id={"clickable-action-item-" + justification.id}>{justification.description}</span>
                </DataListCell>,
              ]}
            />
            <DataListAction
              aria-labelledby={"clickable-action-item-" + justification.id + " clickable-action-action-" + justification.id}
              id={"clickable-action-action-" + justification.id}
              aria-label="Actions"
              isPlainButtonAction
            >
            </DataListAction>
          </DataListItemRow>
        </DataListItem>
      ))
    }

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

        let data = {
          'api-id': api.id,
          'justification': {'id': selectedDataListItemId},
          'section': modalSection,
          'offset': modalOffset,
          'coverage': coverageValue,
        }

        if ((formVerb == 'PUT') || (formVerb == 'DELETE')){
          setMessageValue('Wrong actions.');
          setStatusValue('waiting');
          return;
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
          {getJustificationsTable(justifications)}
        </DataList>
        <br />
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
