import React from 'react';
import { Dropdown, DropdownItem, DropdownList, Divider, MenuToggle, MenuToggleElement } from '@patternfly/react-core';
import EllipsisVIcon from '@patternfly/react-icons/dist/esm/icons/ellipsis-v-icon';

export interface JustificationMenuKebabProps {
  jModalShowState;
  setJModalInfo;
  setHistoryModalInfo;
  setDetailsModalInfo;
  setUsageModalInfo;
  setDeleteModalInfo;
  api;
  mappingType;
  mappingParentType;
  mappingParentRelatedToType;
  mappingIndex;
  mappingList;
  mappingSection;
  mappingOffset;
}

export const JustificationMenuKebab: React.FunctionComponent<JustificationMenuKebabProps> = ({
  jModalShowState,
  setJModalInfo,
  setHistoryModalInfo,
  setDetailsModalInfo,
  setUsageModalInfo,
  setDeleteModalInfo,
  api,
  mappingType,
  mappingParentType,
  mappingParentRelatedToType,
  mappingIndex,
  mappingList,
  mappingSection,
  mappingOffset,
}: JustificationMenuKebabProps) => {
  const [isOpen, setIsOpen] = React.useState(false);

  const onToggleClick = () => {
    setIsOpen(!isOpen);
  };

  const onSelect = (_event: React.MouseEvent<Element, MouseEvent> | undefined, value: string | number | undefined) => {
    setIsOpen(false);
  };

  const _A = 'api';
  const _J = 'justification';

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
                                             _J,
                                             'api',
                                             '',
                                             mappingList,
                                             mappingIndex))}>
          Delete
        </DropdownItem>
        <DropdownItem
          value={1}
          key="edit"
          onClick={() => (setJModalInfo(true,
                                        'edit',
                                        api,
                                        mappingSection,
                                        mappingOffset,
                                        mappingList,
                                        mappingIndex))}>
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
                                              _J,
                                              _A,
                                              mappingList[mappingIndex].relation_id))}>
          History
        </DropdownItem>
        <DropdownItem
          value={4}
          key="show-details"
          onClick={() => (setDetailsModalInfo(true,
                                              _J,
                                              mappingList[mappingIndex]['id']))}>
          Show Details
        </DropdownItem>
        <DropdownItem
          value={5}
          key="usage"
          onClick={() => (setUsageModalInfo(true,
                                            _J,
                                            mappingList[mappingIndex]['id']))}>
          Usage
        </DropdownItem>

      </DropdownList>
    </Dropdown>
  );
};
