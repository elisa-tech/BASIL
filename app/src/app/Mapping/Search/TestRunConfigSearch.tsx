import React from 'react'
import {
  Button,
  DataList,
  DataListCell,
  DataListItem,
  DataListItemCells,
  DataListItemRow,
  Flex,
  FlexItem,
  SearchInput
} from '@patternfly/react-core'

export interface TestRunConfigSearchProps {
  handleSelectExistingTestConfig
  modalShowState
  loadTestRunConfigs
  testRunConfigs
  setInfoLabel
  setActiveTabKey
}

export const TestRunConfigSearch: React.FunctionComponent<TestRunConfigSearchProps> = ({
  handleSelectExistingTestConfig,
  loadTestRunConfigs,
  modalShowState,
  testRunConfigs,
  setInfoLabel,
  setActiveTabKey
}: TestRunConfigSearchProps) => {
  const [searchValue, setSearchValue] = React.useState('')
  const [selectedDataListItemId, setSelectedDataListItemId] = React.useState('')
  const [initializedValue, setInitializedValue] = React.useState(false)

  const onChangeSearchValue = (value) => {
    setSearchValue(value)
  }

  const onSelectDataListItem = (_event: React.MouseEvent | React.KeyboardEvent, id: string) => {
    if (document.getElementById(id) != null) {
      setSelectedDataListItemId(id)
      const tmpConfig = testRunConfigs[document.getElementById(id)?.dataset.index as string | number]
      handleSelectExistingTestConfig(tmpConfig)
      setInfoLabel('existing')
      setActiveTabKey(1)
      setSelectedDataListItemId('')
    }
  }

  const handleInputChange = (_event: React.FormEvent<HTMLInputElement>, id: string) => {
    setSelectedDataListItemId(id)
  }

  React.useEffect(() => {
    if (modalShowState == true && initializedValue == false) {
      setInitializedValue(true)
      loadTestRunConfigs(searchValue)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const getTestRunConfigTable = (test_run_configs) => {
    if (test_run_configs == null) {
      return
    }
    return test_run_configs.map((test_run_config, tcIndex) => (
      <DataListItem
        key={test_run_config.id}
        aria-labelledby={'clickable-action-item-' + test_run_config.id}
        id={'list-existing-test-run-config-item-' + test_run_config.id}
        data-id={test_run_config.id}
        data-index={tcIndex}
      >
        <DataListItemRow>
          <DataListItemCells
            dataListCells={[
              <DataListCell key={tcIndex}>
                <span id={'clickable-action-item-' + test_run_config.id}>
                  {test_run_config.id} - {test_run_config.title}
                </span>
              </DataListCell>
            ]}
          />
        </DataListItemRow>
      </DataListItem>
    ))
  }

  return (
    <React.Fragment>
      <Flex>
        <FlexItem>
          <SearchInput
            placeholder='Search Identifier'
            value={searchValue}
            onChange={(_event, value) => onChangeSearchValue(value)}
            onClear={() => onChangeSearchValue('')}
            style={{ width: '400px' }}
          />
        </FlexItem>
        <FlexItem>
          <Button
            variant='primary'
            aria-label='Action'
            onClick={() => {
              loadTestRunConfigs(searchValue)
            }}
          >
            Search
          </Button>
        </FlexItem>
      </Flex>
      <br />
      <DataList
        isCompact
        id='list-existing-test-cases'
        aria-label='clickable data list example'
        selectedDataListItemId={selectedDataListItemId}
        onSelectDataListItem={onSelectDataListItem}
        onSelectableRowChange={handleInputChange}
      >
        {getTestRunConfigTable(testRunConfigs)}
      </DataList>
      <br />
    </React.Fragment>
  )
}
