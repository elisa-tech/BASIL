import React from 'react';
import { Dropdown, DropdownItem, DropdownList, Divider, MenuToggle, MenuToggleElement } from '@patternfly/react-core';
import EllipsisVIcon from '@patternfly/react-icons/dist/esm/icons/ellipsis-v-icon';

export interface TestSpecificationMenuKebabProps {
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

export const TestSpecificationMenuKebab: React.FunctionComponent<TestSpecificationMenuKebabProps> = ({
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
}: TestSpecificationMenuKebabProps) => {
  const [isOpen, setIsOpen] = React.useState(false);

  const onToggleClick = () => {
    setIsOpen(!isOpen);
  };

  const onSelect = (_event: React.MouseEvent<Element, MouseEvent> | undefined, value: string | number | undefined) => {
    setIsOpen(false);
  };

  const getTestSpecification = () => {
    if (indirect == true){
      return mappingList[mappingIndex]['test_specification'];
    } else {
      return mappingList[mappingIndex];
    }
  }

  const _TS = 'test-specification';
  const _A = 'api';

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
          key="assign-test-case"
          className="success-text"
          onClick={() => (setTcModalInfo(true,
                                         true,
                                         'add',
                                         api,
                                         mappingSection,
                                         mappingOffset,
                                         _TS,
                                         mappingList,
                                         mappingIndex,
                                         mappingParentType))}>
          Assign Test Case
        </DropdownItem>
        <DropdownItem
          value={1}
          key="delete"
          className="danger-text"
          onClick={() => (setDeleteModalInfo(true,
                                             _TS,
                                             mappingParentType,
                                             mappingParentRelatedToType,
                                             mappingList,
                                             mappingIndex))}>
          Delete
        </DropdownItem>
        <DropdownItem
          value={2}
          key="edit"
          onClick={() => (setTsModalInfo(true,
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
          value={3}
          key="fork"
          isDisabled>
          Fork
        </DropdownItem>
        <DropdownItem
          value={4}
          key="history"
          onClick={() => (setHistoryModalInfo(true,
                                              _TS,
                                              mappingParentType,
                                              mappingList[mappingIndex].relation_id))}>
          History
        </DropdownItem>
        <DropdownItem
          value={5}
          key="show-details"
          onClick={() => (setDetailsModalInfo(true,
                                              _TS,
                                              getTestSpecification()['id']))}>
          Show Details
        </DropdownItem>
        <DropdownItem
          value={6}
          key="usage"
          onClick={() => (setUsageModalInfo(true,
                                            _TS,
                                            getTestSpecification()['id']))}>
          Usage
        </DropdownItem>
      </DropdownList>
    </Dropdown>
  );
};
