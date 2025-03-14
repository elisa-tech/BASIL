import React from 'react'
import * as Constants from '../../Constants/constants'
import { Dropdown, DropdownItem, DropdownList, MenuToggle, MenuToggleElement, preventedEvents } from '@patternfly/react-core'
import EllipsisVIcon from '@patternfly/react-icons/dist/esm/icons/ellipsis-v-icon'
import { constant } from 'cypress/types/lodash'

export interface MappingSectionMenuKebabProps {
  setDocModalInfo
  setTcModalInfo
  setTsModalInfo
  setSrModalInfo
  setJModalInfo
  api
  offset
  section
  sectionIndex
}

export const MappingSectionMenuKebab: React.FunctionComponent<MappingSectionMenuKebabProps> = ({
  setDocModalInfo,
  setTcModalInfo,
  setTsModalInfo,
  setSrModalInfo,
  setJModalInfo,
  api,
  offset,
  section,
  sectionIndex
}: MappingSectionMenuKebabProps) => {
  const [isOpen, setIsOpen] = React.useState(false)
  const [snippetOffset, setSnippetOffset] = React.useState(-1)
  const [snippetSection, setSnippetSection] = React.useState('')

  React.useEffect(() => {
    // on load calculate the offset and section based on user selection
    // inside the current snippet
    if (isOpen) {
      if (snippetOffset == -1) {
        setSnippetOffset(getOffset())
        setSnippetSection(getSection())
      }
    } else {
      setSnippetOffset(-1)
    }
  }, [isOpen])

  const onToggleClick = () => {
    setIsOpen(!isOpen)
  }

  const onSelect = () => {
    setIsOpen(false)
  }

  const getSection = () => {
    const currentSelection = getSelection()?.toString() as string | ''
    if (currentSelection != '') {
      // eslint-disable-next-line  @typescript-eslint/no-explicit-any
      if (((getSelection()?.anchorNode?.parentNode as any)?.id as string | '') == 'snippet-' + sectionIndex) {
        return currentSelection
      } else {
        return section
      }
    } else {
      return section
    }
  }

  const getOffset = () => {
    const currentSelection = getSelection()?.toString() as string | ''
    if (currentSelection != '') {
      // eslint-disable-next-line  @typescript-eslint/no-explicit-any
      if (((getSelection()?.anchorNode?.parentNode as any)?.id as string | '') == 'snippet-' + sectionIndex) {
        return offset + Constants.getSelectionOffset()
      } else {
        return offset
      }
    } else {
      return offset
    }
  }

  return api?.raw_specification != null ? (
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
        <DropdownItem
          value={0}
          id={'btn-mapping-section-document-' + sectionIndex}
          name='btn-mapping-section-document'
          key='assign document'
          onClick={(event) => {
            event.preventDefault
            setDocModalInfo(true, 'add', api, snippetSection, snippetOffset, [], -1)
          }}
        >
          Assign Document
        </DropdownItem>
        <DropdownItem
          value={0}
          id={'btn-mapping-section-justification-' + sectionIndex}
          name='btn-mapping-section-justification'
          key='assign justification'
          onClick={() => setJModalInfo(true, 'add', api, snippetSection, snippetOffset, [], -1)}
        >
          Assign Justification
        </DropdownItem>
        <DropdownItem
          value={1}
          id={'btn-mapping-section-sw-requirement-' + sectionIndex}
          name='btn-mapping-section-sw-requirement'
          key='assign sw requirement'
          onClick={() => setSrModalInfo(true, false, 'add', api, snippetSection, snippetOffset, 'api', [], -1, '')}
        >
          Assign Sw Requirement
        </DropdownItem>
        <DropdownItem
          value={2}
          id={'btn-mapping-section-test-case-' + sectionIndex}
          name='btn-mapping-section-test-case'
          key='assign test case'
          onClick={() => setTcModalInfo(true, false, 'add', api, snippetSection, snippetOffset, 'api', [], -1, '')}
        >
          Assign Test Case
        </DropdownItem>
        <DropdownItem
          value={3}
          id={'btn-mapping-section-test-specification-' + sectionIndex}
          name='btn-mapping-section-test-specification'
          key='assign test specification'
          onClick={() => setTsModalInfo(true, false, 'add', api, snippetSection, snippetOffset, 'api', [], -1, '')}
        >
          Assign Test Specification
        </DropdownItem>
      </DropdownList>
    </Dropdown>
  ) : (
    ''
  )
}
