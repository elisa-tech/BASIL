import React from 'react';
import { Dropdown, DropdownItem, DropdownList, Divider, MenuToggle, MenuToggleElement } from '@patternfly/react-core';
import EllipsisVIcon from '@patternfly/react-icons/dist/esm/icons/ellipsis-v-icon';

export interface ApiMenuKebabProps {
  setModalInfo;
  setModalCheckSpecInfo;
  setModalDeleteInfo;
  apiData;
}

export const ApiMenuKebab: React.FunctionComponent<ApiMenuKebabProps> = ({
  setModalInfo,
  setModalCheckSpecInfo,
  setModalDeleteInfo,
  apiData,
}: ApiMenuKebabProps) => {
  const [isOpen, setIsOpen] = React.useState(false);

  const onToggleClick = () => {
    setIsOpen(!isOpen);
  };

  const onSelect = (_event: React.MouseEvent<Element, MouseEvent> | undefined, value: string | number | undefined) => {
    setIsOpen(false);
  };

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
          id={"btn-menu-api-check-spec-" + apiData.id}
          key="action check different spec"
          onClick={() => setModalCheckSpecInfo(apiData, true)}
        >
          Check Spec
        </DropdownItem>
        <DropdownItem
          value={1}
          id={"btn-menu-api-delete-" + apiData.id}
          className="danger-text"
          key="action delete"
          onClick={() => setModalDeleteInfo(apiData,
                                            true,
                                            'Delete ' + apiData.api + ' and all related work items and mapping information?',
                                            'Do you want to delete selected api and all related work items and mapping information?')}>
          Delete
        </DropdownItem>
        <DropdownItem
          value={2}
          id={"btn-menu-api-new-version-" + apiData.id}
          key="action new version"
          onClick={() => setModalInfo(apiData,
                                      true,
                                      'api',
                                      'POST',
                                      'fork',
                                      'Create a new Version of "' + apiData.api + '" from "' + apiData.library + '"',
                                      'Information are prepopulated with the current version')}
          >
          New Version
        </DropdownItem>

      </DropdownList>
    </Dropdown>
  );
};
