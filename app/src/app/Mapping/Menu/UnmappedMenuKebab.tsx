import React from 'react'
import { useAuth } from '@app/User/AuthProvider'
import * as Constants from '@app/Constants/constants'
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
  setModalNotificationInfo
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
  mappingOffset,
  setModalNotificationInfo
}: UnmappedMenuKebabProps) => {
  const [isOpen, setIsOpen] = React.useState(false)
  const auth = useAuth()

  const onToggleClick = () => {
    setIsOpen(!isOpen)
  }

  const onSelect = () => {
    setIsOpen(false)
  }

  const handleDelete = () => {
    setDeleteModalInfo(true, mappingType, mappingParentType, '', mappingList, mappingIndex)
  }

  const handleAutoFix = () => {
    // Mapping endpoint based on mappingType
    const mappingEndpoint = Constants.API_BASE_URL + '/mapping/api/' + mappingType.toLowerCase().replace('_', '-') + 's'

    const data = {
      'api-id': api.id,
      'relation-id': mappingList[mappingIndex].relation_id,
      section: mappingSection,
      coverage: mappingList[mappingIndex]['coverage'],
      offset: mappingList[mappingIndex]['auto-fix-offset'],
      'user-id': auth.userId,
      token: auth.token
    }

    if (mappingType == Constants._J) {
      data['justification'] = mappingList[mappingIndex][Constants._J]
      data['justification'] = Constants.normalizeKeys(data['justification'])
    } else if (mappingType == Constants._D) {
      data['document'] = mappingList[mappingIndex][Constants._D]
      data['document'] = Constants.normalizeKeys(data['document'])
    } else if (mappingType == Constants._SR) {
      data['sw-requirement'] = mappingList[mappingIndex][Constants._SR_]
      data['sw-requirement'] = Constants.normalizeKeys(data['sw-requirement'])
    } else if (mappingType == Constants._TS) {
      data['test-specification'] = mappingList[mappingIndex][Constants._TS_]
      data['test-specification'] = Constants.normalizeKeys(data['test-specification'])
    } else if (mappingType == Constants._TC) {
      data['test-case'] = mappingList[mappingIndex][Constants._TC_]
      data['test-case'] = Constants.normalizeKeys(data['test-case'])
    }

    fetch(mappingEndpoint, {
      method: 'PUT',
      headers: Constants.JSON_HEADER,
      body: JSON.stringify(data)
    })
      .then((response) => {
        if (response.status !== 200) {
          console.log(response.status)
          // show modal notification error
          setModalNotificationInfo('Error', response.statusText + ' - ' + response.status, true)
        } else {
          location.reload()
        }
      })
      .catch((err) => {
        console.log(err)
        // show modal notification error
        setModalNotificationInfo('Error', err.message, true)
      })
      .finally(() => {
        setIsOpen(false)
      })
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
      setDocModalInfo(true, false, 'edit', api, mappingSection, mappingOffset, mappingParentType, mappingList, mappingIndex, '')
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
            {mappingList[mappingIndex]['auto-fix-offset'] != -1 && (
              <DropdownItem
                value={0}
                key='auto-fix'
                className='danger-text'
                id={'btn-menu-unmapped-auto-fix-' + mappingList[mappingIndex].relation_id}
                onClick={handleAutoFix}
              >
                Auto Fix
              </DropdownItem>
            )}
            <DropdownItem
              value={1}
              key='delete'
              className='danger-text'
              id={'btn-menu-unmapped-delete-' + mappingList[mappingIndex].relation_id}
              onClick={handleDelete}
            >
              Delete
            </DropdownItem>
            <DropdownItem value={2} key='edit' id={'btn-menu-unmapped-edit-' + mappingList[mappingIndex].relation_id} onClick={handleEdit}>
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
