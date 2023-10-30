import React from 'react';
import { Dropdown, DropdownItem, DropdownList, Divider, MenuToggle, MenuToggleElement } from '@patternfly/react-core';
import EllipsisVIcon from '@patternfly/react-icons/dist/esm/icons/ellipsis-v-icon';

//NOTE: Unampped sections are only direct mapping
//      so we don't need indirect and mappedParedntRelatedToType

export interface UnmappedMenuKebabProps {
  setModalInfo;
  srModalShowState;
  tcModalShowState;
  tsModalShowState;
  jModalShowState;
  setDeleteModalInfo;
  setTcModalInfo;
  setTsModalInfo;
  setSrModalInfo;
  setJModalInfo;
  api;
  mappingType;
  mappingParentType;
  mappingIndex;
  mappingList;
  mappingSection;
  mappingOffset;
}

export const UnmappedMenuKebab: React.FunctionComponent<UnmappedMenuKebabProps> = ({
  setModalInfo,
  tsModalShowState,
  tcModalShowState,
  setTcModalShowState,
  jModalShowState,
  setDeleteModalInfo,
  setTcModalInfo,
  setTsModalInfo,
  setSrModalInfo,
  setJModalInfo,
  api,
  mappingType,
  mappingParentType,
  mappingIndex,
  mappingList,
  mappingSection,
  mappingOffset,
}: UnmappedMenuKebabProps) => {
  const [isOpen, setIsOpen] = React.useState(false);

  const onToggleClick = () => {
    setIsOpen(!isOpen);
  };

  const onSelect = (_event: React.MouseEvent<Element, MouseEvent> | undefined, value: string | number | undefined) => {
    setIsOpen(false);
  };

  const _J = 'justification';
  const _SR = 'sw-requirement';
  const _TS = 'test-specification';
  const _TC = 'test-case';

  const handleDelete = () => {
    setDeleteModalInfo(true,
                       mappingType,
                       mappingParentType,
                       '',
                       mappingList,
                       mappingIndex);
  }

  const handleEdit = () => {
    let list_item = {};
    let list = [];
    if (mappingType == _J) {
      list_item = mappingList[mappingIndex]['justification'];
      list_item['coverage'] = mappingList[mappingIndex]['coverage'];
      list_item['relation_id'] = mappingList[mappingIndex]['relation_id'];
      list = [list_item];
      setJModalInfo(true,
                    'edit',
                    api,
                    mappingSection,
                    mappingOffset,
                    list,
                    mappingIndex);
    } else if (mappingType == _SR) {
      list_item = mappingList[mappingIndex]['sw_requirement'];
      list_item['coverage'] = mappingList[mappingIndex]['coverage'];
      list_item['relation_id'] = mappingList[mappingIndex]['relation_id'];
      list = [list_item];
      setSrModalInfo(true,
                     false,
                     'edit',
                      api,
                      mappingSection,
                      mappingOffset,
                      mappingParentType,
                      list,
                      mappingIndex,
                      '');
    } else if (mappingType == _TS){
      list_item = mappingList[mappingIndex]['test_specification'];
      list_item['coverage'] = mappingList[mappingIndex]['coverage'];
      list_item['relation_id'] = mappingList[mappingIndex]['relation_id'];
      list = [list_item];
      setTsModalInfo(true,
                     false,
                     'edit',
                     api,
                     mappingSection,
                     mappingOffset,
                     mappingParentType,
                     list,
                     mappingIndex,
                     '');
    } else if (mappingType == _TC){
      list_item = mappingList[mappingIndex]['test_case'];
      list_item['coverage'] = mappingList[mappingIndex]['coverage'];
      list_item['relation_id'] = mappingList[mappingIndex]['relation_id'];
      list = [list_item];
      setTcModalInfo(true,
                     false,
                     'edit',
                     api,
                     mappingSection,
                     mappingOffset,
                     mappingParentType,
                     [mappingList[mappingIndex]['test_case']],
                     mappingIndex,
                     '');
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
          aria-label="unmapped section menu"
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
          value={2}
          key="delete"
          className="danger-text"
          id={"btn-menu-unmapped-delete-" + mappingList[mappingIndex].relation_id}
          onClick={handleDelete}>
          Delete
        </DropdownItem>
        <DropdownItem
          value={0}
          key="edit"
          id={"btn-menu-unmapped-edit-" + mappingList[mappingIndex].relation_id}
          onClick={handleEdit}>
          Edit
        </DropdownItem>
      </DropdownList>
    </Dropdown>
  );
};
