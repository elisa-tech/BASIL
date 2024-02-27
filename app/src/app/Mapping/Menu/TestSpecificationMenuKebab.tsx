import React from 'react'
import * as Constants from '../../Constants/constants'
import { Dropdown, DropdownItem, DropdownList, MenuToggle, MenuToggleElement } from '@patternfly/react-core'
import EllipsisVIcon from '@patternfly/react-icons/dist/esm/icons/ellipsis-v-icon'

export interface TestSpecificationMenuKebabProps {
  indirect
  setHistoryModalInfo
  setDetailsModalInfo
  setUsageModalInfo
  setTcModalInfo
  setTsModalInfo
  setDeleteModalInfo
  mappingParentType
  mappingParentRelatedToType
  mappingIndex
  mappingList
  api
  mappingSection
  mappingOffset
}

export const TestSpecificationMenuKebab: React.FunctionComponent<TestSpecificationMenuKebabProps> = ({
  indirect,
  setHistoryModalInfo,
  setDetailsModalInfo,
  setUsageModalInfo,
  setTcModalInfo,
  setTsModalInfo,
  setDeleteModalInfo,
  mappingParentType,
  mappingParentRelatedToType,
  mappingIndex,
  mappingList,
  api,
  mappingSection,
  mappingOffset
}: TestSpecificationMenuKebabProps) => {
  const [isOpen, setIsOpen] = React.useState(false)

  const onToggleClick = () => {
    setIsOpen(!isOpen)
  }

  const onSelect = () => {
    setIsOpen(false)
  }

  const getTestSpecification = () => {
    if (indirect == true) {
      return mappingList[mappingIndex][Constants._TS_]
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
              id={'btn-menu-test-specification-assign-test-case-' + mappingList[mappingIndex].relation_id}
              key='assign-test-case'
              className='success-text'
              onClick={() =>
                setTcModalInfo(
                  true,
                  true,
                  'add',
                  api,
                  mappingSection,
                  mappingOffset,
                  Constants._TS,
                  mappingList,
                  mappingIndex,
                  mappingParentType
                )
              }
            >
              Assign Test Case
            </DropdownItem>
            <DropdownItem
              value={1}
              id={'btn-menu-test-specification-delete-' + mappingList[mappingIndex].relation_id}
              key='delete'
              className='danger-text'
              onClick={() =>
                setDeleteModalInfo(true, Constants._TS, mappingParentType, mappingParentRelatedToType, mappingList, mappingIndex)
              }
            >
              Delete
            </DropdownItem>
            <DropdownItem
              value={2}
              id={'btn-menu-test-specification-edit-' + mappingList[mappingIndex].relation_id}
              key='edit'
              onClick={() =>
                setTsModalInfo(
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
            <DropdownItem value={3} key='fork' isDisabled>
              Fork
            </DropdownItem>
          </React.Fragment>
        ) : (
          ''
        )}

        <DropdownItem
          value={4}
          key='history'
          onClick={() => setHistoryModalInfo(true, Constants._TS, mappingParentType, mappingList[mappingIndex].relation_id)}
        >
          History
        </DropdownItem>
        <DropdownItem value={5} key='show-details' onClick={() => setDetailsModalInfo(true, Constants._TS, getTestSpecification()['id'])}>
          Show Details
        </DropdownItem>
        <DropdownItem value={6} key='usage' onClick={() => setUsageModalInfo(true, Constants._TS, getTestSpecification()['id'])}>
          Usage
        </DropdownItem>
      </DropdownList>
    </Dropdown>
  )
}
