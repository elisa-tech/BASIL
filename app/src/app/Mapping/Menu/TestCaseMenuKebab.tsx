import React from 'react'
import * as Constants from '../../Constants/constants'
import { Dropdown, DropdownItem, DropdownList, MenuToggle, MenuToggleElement } from '@patternfly/react-core'
import EllipsisVIcon from '@patternfly/react-icons/dist/esm/icons/ellipsis-v-icon'

export interface TestCaseMenuKebabProps {
  indirect
  setHistoryModalInfo
  setDetailsModalInfo
  setUsageModalInfo
  setTcModalInfo
  setDeleteModalInfo
  mappingParentType
  mappingParentRelatedToType
  mappingIndex
  mappingList
  api
  mappingSection
  mappingOffset
}

export const TestCaseMenuKebab: React.FunctionComponent<TestCaseMenuKebabProps> = ({
  indirect,
  setHistoryModalInfo,
  setDetailsModalInfo,
  setUsageModalInfo,
  setTcModalInfo,
  setDeleteModalInfo,
  mappingParentType,
  mappingParentRelatedToType,
  mappingIndex,
  mappingList,
  api,
  mappingSection,
  mappingOffset
}: TestCaseMenuKebabProps) => {
  const [isOpen, setIsOpen] = React.useState(false)

  const onToggleClick = () => {
    setIsOpen(!isOpen)
  }

  const onSelect = () => {
    setIsOpen(false)
  }

  const getTestCase = () => {
    if (indirect == true) {
      return mappingList[mappingIndex][Constants._TC_]
    } else {
      return mappingList[mappingIndex]
    }
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
              id={'btn-menu-test-case-delete-' + mappingList[mappingIndex].relation_id}
              key='delete'
              className='danger-text'
              onClick={() =>
                setDeleteModalInfo(true, Constants._TC, mappingParentType, mappingParentRelatedToType, mappingList, mappingIndex)
              }
            >
              Delete
            </DropdownItem>
            <DropdownItem
              value={1}
              id={'btn-menu-test-case-edit-' + mappingList[mappingIndex].relation_id}
              key='edit'
              onClick={() =>
                setTcModalInfo(
                  true,
                  indirect,
                  'edit',
                  api,
                  mappingSection,
                  mappingOffset,
                  mappingParentType,
                  mappingList,
                  mappingIndex,
                  mappingParentRelatedToType
                )
              }
            >
              Edit
            </DropdownItem>
            <DropdownItem value={2} key='fork' isDisabled>
              Fork
            </DropdownItem>
          </React.Fragment>
        ) : (
          ''
        )}

        <DropdownItem
          value={3}
          key='history'
          onClick={() => setHistoryModalInfo(true, Constants._TC, mappingParentType, mappingList[mappingIndex].relation_id)}
        >
          History
        </DropdownItem>
        <DropdownItem value={4} key='show-details' onClick={() => setDetailsModalInfo(true, Constants._TC, getTestCase()['id'])}>
          Show Details
        </DropdownItem>
        <DropdownItem value={5} key='usage' onClick={() => setUsageModalInfo(true, Constants._TC, getTestCase()['id'])}>
          Usage
        </DropdownItem>
      </DropdownList>
    </Dropdown>
  )
}
