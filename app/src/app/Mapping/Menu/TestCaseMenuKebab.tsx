import React from 'react';
import { Dropdown, DropdownItem, DropdownList, Divider, MenuToggle, MenuToggleElement } from '@patternfly/react-core';
import EllipsisVIcon from '@patternfly/react-icons/dist/esm/icons/ellipsis-v-icon';

export interface TestCaseMenuKebabProps {
  indirect;
  tsModalShowState;
  tcModalShowState;
  setHistoryModalInfo;
  setDetailsModalInfo;
  setUsageModalInfo;
  setTcModalInfo;
  setTsModalInfo;
  setTcModalShowState;
  setTsModalShowState;
  setDeleteModalInfo;
  mappingType;
  mappingParentType;
  mappingParentRelatedToType;
  mappingIndex;
  mappingList;
  api;
  mappingSection;
  mappingOffset;
}

export const TestCaseMenuKebab: React.FunctionComponent<TestCaseMenuKebabProps> = ({
  indirect,
  tsModalShowState,
  tcModalShowState,
  setHistoryModalInfo,
  setDetailsModalInfo,
  setUsageModalInfo,
  setTcModalInfo,
  setTsModalInfo,
  setTcModalShowState,
  setTsModalShowState,
  setDeleteModalInfo,
  mappingType,
  mappingParentType,
  mappingParentRelatedToType,
  mappingIndex,
  mappingList,
  api,
  mappingSection,
  mappingOffset,
}: TestCaseMenuKebabProps) => {
  const [isOpen, setIsOpen] = React.useState(false);

  const onToggleClick = () => {
    setIsOpen(!isOpen);
  };

  const onSelect = (_event: React.MouseEvent<Element, MouseEvent> | undefined, value: string | number | undefined) => {
    setIsOpen(false);
  };

  const _A = 'api';
  const _TC = 'test-case';

  const getTestCase = () => {
    if (indirect == true){
      return mappingList[mappingIndex]['test_case'];
    } else {
      return mappingList[mappingIndex];
    }
  }

  return (
    <Dropdown
      isOpen={isOpen}
      onSelect={onSelect}
      onOpenChange={(isOpen: boolean) => setIsOpen(isOpen)}
      toggle={(toggleRef: React.Ref<MenuToggleElement>) => (
        <MenuToggle
          ref={toggleRef}
          aria-label="kebab dropdown toggle"
          variant="plain"
          onClick={onToggleClick}
          isExpanded={isOpen}
        >
          <EllipsisVIcon />
        </MenuToggle>
      )}
      shouldFocusToggleOnSelect
    >

      <DropdownList>

        <DropdownItem
          value={0}
          key="delete"
          className="danger-text"
          onClick={() => (setDeleteModalInfo(true,
                                             _TC,
                                             mappingParentType,
                                             mappingParentRelatedToType,
                                             mappingList,
                                             mappingIndex))}>
          Delete
        </DropdownItem>
        <DropdownItem
          value={1}
          key="edit"
          onClick={() => (setTcModalInfo(true,
                                         indirect,
                                         'edit',
                                         api,
                                         mappingSection,
                                         mappingOffset,
                                         mappingParentType,
                                         mappingList,
                                         mappingIndex,
                                         mappingParentRelatedToType))}>
          Edit
        </DropdownItem>
        <DropdownItem
          value={2}
          key="fork"
          isDisabled>
          Fork
        </DropdownItem>
        <DropdownItem
          value={3}
          key="history"
          onClick={() => (setHistoryModalInfo(true,
                                              _TC,
                                              mappingParentType,
                                              mappingList[mappingIndex].relation_id))}>
          History
        </DropdownItem>
        <DropdownItem
          value={4}
          key="show-details"
          onClick={() => (setDetailsModalInfo(true,
                                              _TC,
                                              getTestCase()['id']))}>
          Show Details
        </DropdownItem>
        <DropdownItem
          value={5}
          key="usage"
          onClick={() => (setUsageModalInfo(true,
                                            _TC,
                                            getTestCase()['id']))}>
          Usage
        </DropdownItem>

      </DropdownList>
    </Dropdown>
  );
};
