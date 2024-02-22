import React from 'react'
import * as Constants from '../../Constants/constants'
import { Dropdown, DropdownItem, DropdownList, MenuToggle, MenuToggleElement } from '@patternfly/react-core'
import EllipsisVIcon from '@patternfly/react-icons/dist/esm/icons/ellipsis-v-icon'

export interface JustificationMenuKebabProps {
  setJModalInfo
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

export const JustificationMenuKebab: React.FunctionComponent<JustificationMenuKebabProps> = ({
  setJModalInfo,
  setHistoryModalInfo,
  setDetailsModalInfo,
  setUsageModalInfo,
  setDeleteModalInfo,
  api,
  mappingIndex,
  mappingList,
  mappingSection,
  mappingOffset
}: JustificationMenuKebabProps) => {
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

        { api?.permissions.indexOf('w') >= 0 ? (
        <React.Fragment>
        <DropdownItem
          value={0}
          id={'btn-menu-justification-delete-' + mappingList[mappingIndex].relation_id}
          key='delete'
          className='danger-text'
          onClick={() => setDeleteModalInfo(true, Constants._J, 'api', '', mappingList, mappingIndex)}
        >
          Delete
        </DropdownItem>
        <DropdownItem
          value={1}
          id={'btn-menu-justification-edit-' + mappingList[mappingIndex].relation_id}
          key='edit'
          onClick={() => setJModalInfo(true, 'edit', api, mappingSection, mappingOffset, mappingList, mappingIndex)}
        >
          Edit
        </DropdownItem>
        <DropdownItem value={2} key='fork' isDisabled>
          Fork
        </DropdownItem>
        </React.Fragment>
        ) : ('') }

        <DropdownItem
          value={3}
          id={'btn-menu-justification-history-' + mappingList[mappingIndex].relation_id}
          key='history'
          onClick={() => setHistoryModalInfo(true, Constants._J, Constants._A, mappingList[mappingIndex].relation_id)}
        >
          History
        </DropdownItem>
        <DropdownItem
          value={4}
          id={'btn-menu-justification-details-' + mappingList[mappingIndex].relation_id}
          key='show-details'
          onClick={() => setDetailsModalInfo(true, Constants._J, mappingList[mappingIndex]['id'])}
        >
          Show Details
        </DropdownItem>
        <DropdownItem
          value={5}
          id={'btn-menu-justification-usage-' + mappingList[mappingIndex].relation_id}
          key='usage'
          onClick={() => setUsageModalInfo(true, Constants._J, mappingList[mappingIndex]['id'])}
        >
          Usage
        </DropdownItem>
      </DropdownList>
    </Dropdown>
  )
}
