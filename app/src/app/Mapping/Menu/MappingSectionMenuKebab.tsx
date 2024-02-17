import React from 'react';
import {
  Dropdown,
  DropdownItem,
  DropdownList,
  MenuToggle,
  MenuToggleElement } from '@patternfly/react-core';
import EllipsisVIcon from '@patternfly/react-icons/dist/esm/icons/ellipsis-v-icon';

export interface MappingSectionMenuKebabProps {
  setTcModalInfo;
  setTsModalInfo;
  setSrModalInfo;
  setJModalInfo;
  api;
  offset;
  section;
  sectionIndex;
}

export const MappingSectionMenuKebab: React.FunctionComponent<MappingSectionMenuKebabProps> = ({
  setTcModalInfo,
  setTsModalInfo,
  setSrModalInfo,
  setJModalInfo,
  api,
  offset,
  section,
  sectionIndex,
}: MappingSectionMenuKebabProps) => {
  const [isOpen, setIsOpen] = React.useState(false);

  const onToggleClick = () => {
    setIsOpen(!isOpen);
  };

  const onSelect = () => {
    setIsOpen(false);
  };

  const getSection = () => {
    let currentSelection = getSelection()?.toString() as string | '';
    if (currentSelection != ''){
      if (((getSelection()?.anchorNode?.parentNode as any)?.id as string | '') == "snippet-" + sectionIndex){
        return currentSelection;
      } else {
        return section;
      }
    } else {
      return section;
    }
  }

  const getOffset = () => {
    let currentSelection = getSelection()?.toString() as string | '';
    if (currentSelection != ''){
      if (((getSelection()?.anchorNode?.parentNode as any)?.id as string | '') == "snippet-" + sectionIndex){
        return offset + Math.min((getSelection() as any)?.baseOffset, (getSelection() as any)?.extentOffset);
      } else {
        return offset;
      }
    } else {
      return offset;
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
          id={"btn-mapping-section-justification-" + sectionIndex}
          name="btn-mapping-section-justification"
          key="assign justification"
          onClick={() => (setJModalInfo(true,
                                        'add',
                                        api,
                                        getSection(),
                                        getOffset(),
                                        [],
                                        -1))}>
          Assign Justification
        </DropdownItem>
        <DropdownItem
          value={1}
          id={"btn-mapping-section-sw-requirement-" + sectionIndex}
          name="btn-mapping-section-sw-requirement"
          key="assign sw requirement"
          onClick={() => (setSrModalInfo(true,
                                         false,
                                         'add',
                                         api,
                                         getSection(),
                                         getOffset(),
                                         'api',
                                         [],
                                         -1,
                                         ''))}>
          Assign Sw Requirement
        </DropdownItem>
        <DropdownItem
          value={2}
          id={"btn-mapping-section-test-case-" + sectionIndex}
          name="btn-mapping-section-test-case"
          key="assign test case"
          onClick={() => (setTcModalInfo(true,
                                         false,
                                         'add',
                                         api,
                                         getSection(),
                                         getOffset(),
                                         'api',
                                         [],
                                         -1,
                                         ''))}>
          Assign Test Case
        </DropdownItem>
        <DropdownItem
          value={3}
          id={"btn-mapping-section-test-specification-" + sectionIndex}
          name="btn-mapping-section-test-specification"
          key="assign test specification"
          onClick={() => (setTsModalInfo(true,
                                         false,
                                         'add',
                                         api,
                                         getSection(),
                                         getOffset(),
                                         'api',
                                         [],
                                         -1,
                                         ''))}>
          Assign Test Specification
        </DropdownItem>


      </DropdownList>
    </Dropdown>
  );
};
