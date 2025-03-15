import React from 'react'
import * as Constants from '../../Constants/constants'
import { Dropdown, DropdownItem, DropdownList, MenuToggle, MenuToggleElement } from '@patternfly/react-core'
import EllipsisVIcon from '@patternfly/react-icons/dist/esm/icons/ellipsis-v-icon'

//NOTE: Unampped sections are only direct mapping
//      so we don't need indirect and mappedParedntRelatedToType

export interface UnmappedMenuKebabProps {
  srModalShowState
  setDeleteModalInfo
  setDocModalInfo
  setTcModalInfo
  setTsModalInfo
  setSrModalInfo
  setJModalInfo
  api
  mappingType
  mappingParentType
  mappingIndex
  mappingList
  mappingSection
  mappingOffset
}

export const UnmappedMenuKebab: React.FunctionComponent<UnmappedMenuKebabProps> = ({
  setDeleteModalInfo,
  setDocModalInfo,
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
  mappingOffset
}: UnmappedMenuKebabProps) => {
  const [isOpen, setIsOpen] = React.useState(false)

  const onToggleClick = () => {
    setIsOpen(!isOpen)
  }

  const onSelect = () => {
    setIsOpen(false)
  }

  const handleDelete = () => {
    setDeleteModalInfo(true, mappingType, mappingParentType, '', mappingList, mappingIndex)
  }

  const handleEdit = () => {
    //let list_item = {};
    //let list = []
    if (mappingType == Constants._J) {
      //list_item = mappingList[mappingIndex];
      //list_item['coverage'] = mappingList[mappingIndex]['coverage'];
      //list_item['relation_id'] = mappingList[mappingIndex]['relation_id'];
      //list = list_item;
      //list = mappingList[mappingIndex]
      setJModalInfo(true, 'edit', api, mappingSection, mappingOffset, mappingList, mappingIndex)
    } else if (mappingType == Constants._D) {
      //list_item = mappingList[mappingIndex];
      //list_item['coverage'] = mappingList[mappingIndex]['coverage'];
      //list_item['relation_id'] = mappingList[mappingIndex]['relation_id'];
      //list = [list_item];
      //list = mappingList[mappingIndex]
      setDocModalInfo(true, 'edit', api, mappingSection, mappingOffset, mappingList, mappingIndex)
    } else if (mappingType == Constants._SR) {
      //list_item = mappingList[mappingIndex];
      //list_item['coverage'] = mappingList[mappingIndex]['coverage'];
      //list_item['relation_id'] = mappingList[mappingIndex]['relation_id'];
      //list = [list_item];
      //list = mappingList[mappingIndex]
      setSrModalInfo(true, false, 'edit', api, mappingSection, mappingOffset, mappingParentType, mappingList, mappingIndex, '')
    } else if (mappingType == Constants._TS) {
      //list_item = mappingList[mappingIndex];
      //list_item['coverage'] = mappingList[mappingIndex]['coverage'];
      //list_item['relation_id'] = mappingList[mappingIndex]['relation_id'];
      //list = [list_item];
      //list = mappingList[mappingIndex]
      setTsModalInfo(true, false, 'edit', api, mappingSection, mappingOffset, mappingParentType, mappingList, mappingIndex, '')
    } else if (mappingType == Constants._TC) {
      //list_item = mappingList[mappingIndex];
      //list_item['coverage'] = mappingList[mappingIndex]['coverage'];
      //list_item['relation_id'] = mappingList[mappingIndex]['relation_id'];
      //list = [list_item];
      //list = mappingList[mappingIndex]
      setTcModalInfo(true, false, 'edit', api, mappingSection, mappingOffset, mappingParentType, mappingList, mappingIndex, '')
    }
  }

  return (
    <Dropdown
      popperProps={{ position: 'right' }}
      isOpen={isOpen}
      onSelect={onSelect}
      onOpenChange={(isOpen: boolean) => setIsOpen(isOpen)}
      toggle={(toggleRef: React.Ref<MenuToggleElement>) => (
        <MenuToggle ref={toggleRef} aria-label='unmapped section menu' variant='plain' onClick={onToggleClick} isExpanded={isOpen}>
          <EllipsisVIcon />
        </MenuToggle>
      )}
      shouldFocusToggleOnSelect
    >
      <DropdownList>
        {api?.permissions.indexOf('w') >= 0 && api.raw_specification != null ? (
          <React.Fragment>
            <DropdownItem
              value={2}
              key='delete'
              className='danger-text'
              id={'btn-menu-unmapped-delete-' + mappingList[mappingIndex].relation_id}
              onClick={handleDelete}
            >
              Delete
            </DropdownItem>
            <DropdownItem value={0} key='edit' id={'btn-menu-unmapped-edit-' + mappingList[mappingIndex].relation_id} onClick={handleEdit}>
              Edit
            </DropdownItem>
          </React.Fragment>
        ) : (
          ''
        )}
      </DropdownList>
    </Dropdown>
  )
}
