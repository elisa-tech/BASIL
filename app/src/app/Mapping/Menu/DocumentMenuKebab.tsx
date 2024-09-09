import React from 'react'
import * as Constants from '../../Constants/constants'
import { Dropdown, DropdownItem, DropdownList, MenuToggle, MenuToggleElement } from '@patternfly/react-core'
import EllipsisVIcon from '@patternfly/react-icons/dist/esm/icons/ellipsis-v-icon'

export interface DocumentMenuKebabProps {
  setDocModalInfo
  setHistoryModalInfo
  setDetailsModalInfo
  setUsageModalInfo
  setDeleteModalInfo
  api
  mappingIndex
  mappingList
  mappingSection
  mappingOffset
}

export const DocumentMenuKebab: React.FunctionComponent<DocumentMenuKebabProps> = ({
  setDocModalInfo,
  setHistoryModalInfo,
  setDetailsModalInfo,
  setUsageModalInfo,
  setDeleteModalInfo,
  api,
  mappingIndex,
  mappingList,
  mappingSection,
  mappingOffset
}: DocumentMenuKebabProps) => {
  const [isOpen, setIsOpen] = React.useState(false)

  const onToggleClick = () => {
    setIsOpen(!isOpen)
  }

  const onSelect = () => {
    setIsOpen(false)
  }

  return (
    <Dropdown
      isOpen={isOpen}
      onSelect={onSelect}
      onOpenChange={(isOpen: boolean) => setIsOpen(isOpen)}
      toggle={(toggleRef: React.Ref<MenuToggleElement>) => (
        <MenuToggle ref={toggleRef} aria-label='kebab dropdown toggle' variant='plain' onClick={onToggleClick} isExpanded={isOpen}>
          <EllipsisVIcon />
        </MenuToggle>
      )}
      shouldFocusToggleOnSelect
    >
      <DropdownList>
        {api?.permissions.indexOf('w') >= 0 ? (
          <React.Fragment>
            <DropdownItem
              value={0}
              id={'btn-menu-document-delete-' + mappingList[mappingIndex].relation_id}
              key='delete'
              className='danger-text'
              onClick={() => setDeleteModalInfo(true, Constants._D, 'api', '', mappingList, mappingIndex)}
            >
              Delete
            </DropdownItem>
            <DropdownItem
              value={1}
              id={'btn-menu-document-edit-' + mappingList[mappingIndex].relation_id}
              key='edit'
              onClick={() => setDocModalInfo(true, 'edit', api, mappingSection, mappingOffset, mappingList, mappingIndex)}
            >
              Edit
            </DropdownItem>
          </React.Fragment>
        ) : (
          ''
        )}

        <DropdownItem
          value={3}
          id={'btn-menu-document-history-' + mappingList[mappingIndex].relation_id}
          key='history'
          onClick={() => setHistoryModalInfo(true, Constants._D, Constants._A, mappingList[mappingIndex].relation_id)}
        >
          History
        </DropdownItem>
        <DropdownItem
          value={4}
          id={'btn-menu-document-details-' + mappingList[mappingIndex].relation_id}
          key='show-details'
          onClick={() => setDetailsModalInfo(true, Constants._D, mappingList[mappingIndex][Constants._D]['id'])}
        >
          Show Details
        </DropdownItem>
        <DropdownItem
          value={5}
          id={'btn-menu-document-usage-' + mappingList[mappingIndex].relation_id}
          key='usage'
          onClick={() => setUsageModalInfo(true, Constants._D, mappingList[mappingIndex][Constants._D]['id'])}
        >
          Usage
        </DropdownItem>
      </DropdownList>
    </Dropdown>
  )
}
