import * as React from 'react'
import * as Constants from '../Constants/constants'
import {
  Badge,
  Button,
  Card,
  CardBody,
  Divider,
  Flex,
  FlexItem,
  Icon,
  Label,
  Text,
  TextContent,
  TextVariants,
  Tooltip
} from '@patternfly/react-core'
import ReactMarkdown from 'react-markdown'
import { SwRequirementMenuKebab } from './Menu/SwRequirementMenuKebab'
import { TestSpecificationMenuKebab } from './Menu/TestSpecificationMenuKebab'
import { TestCaseMenuKebab } from './Menu/TestCaseMenuKebab'
import { JustificationMenuKebab } from './Menu/JustificationMenuKebab'
import { DocumentMenuKebab } from './Menu/DocumentMenuKebab'
import { LeavesProgressBar } from '../Custom/LeavesProgressBar'
import { CompletionLabel } from '@app/Common/Label/CompletionLabel'
import CommentBadges from '../Custom/CommentBadges'
import OutlinedCommentsIcon from '@patternfly/react-icons/dist/esm/icons/outlined-comments-icon'
import CodeIcon from '@patternfly/react-icons/dist/esm/icons/code-icon'
import CatalogIcon from '@patternfly/react-icons/dist/esm/icons/catalog-icon'
import FileIcon from '@patternfly/react-icons/dist/esm/icons/file-icon'
import TaskIcon from '@patternfly/react-icons/dist/esm/icons/task-icon'
import BalanceScaleIcon from '@patternfly/react-icons/dist/esm/icons/balance-scale-icon'
import MigrationIcon from '@patternfly/react-icons/dist/esm/icons/migration-icon'
import TimesIcon from '@patternfly/react-icons/dist/esm/icons/times-icon'
import ListIcon from '@patternfly/react-icons/dist/esm/icons/list-icon'
import { useAuth } from '../User/AuthProvider'

export interface MappingDynamicViewTableProps {
  api
  dynamicViewData
  setDocModalInfo
  setTsModalInfo
  setTcModalInfo
  setSrModalInfo
  setJModalInfo
  setCommentModalInfo
  setDeleteModalInfo
  setDetailsModalInfo
  setForkModalInfo
  setHistoryModalInfo
  setImplementationModalInfo
  setTestResultsModalInfo
  setTestRunModalInfo
  setUsageModalInfo
  setModalNotificationInfo
  setSnippetsModalInfo
  showIndirectTestCases
  showIndirectTestSpecifications
}

const MappingDynamicViewTable: React.FunctionComponent<MappingDynamicViewTableProps> = ({
  api,
  dynamicViewData,
  setDocModalInfo,
  setTsModalInfo,
  setTcModalInfo,
  setSrModalInfo,
  setJModalInfo,
  setCommentModalInfo,
  setDeleteModalInfo,
  setDetailsModalInfo,
  setForkModalInfo,
  setHistoryModalInfo,
  setImplementationModalInfo,
  setTestResultsModalInfo,
  setTestRunModalInfo,
  setUsageModalInfo,
  setModalNotificationInfo,
  setSnippetsModalInfo,
  showIndirectTestCases,
  showIndirectTestSpecifications
}: MappingDynamicViewTableProps) => {
  const auth = useAuth()
  const [selectedWorkItem, setSelectedWorkItem] = React.useState<any>(null)
  const [selectedWorkItemType, setSelectedWorkItemType] = React.useState('')
  const workItemsPanelRef = React.useRef<HTMLDivElement>(null)
  const specPanelRef = React.useRef<HTMLDivElement>(null)
  const panelsRef = React.useRef<HTMLDivElement>(null)
  const specContentPreRef = React.useRef<HTMLPreElement>(null)
  const [contextMenu, setContextMenu] = React.useState<{
    x: number
    y: number
    items: { group: any; type: string; label: string; icon: React.ReactNode }[]
  } | null>(null)

  React.useEffect(() => {
    const panels = panelsRef.current
    if (!panels) return

    const scrollParent = document.getElementById('primary-app-container') as HTMLElement
    if (!scrollParent) return

    let maxScroll = 0

    const computeMax = () => {
      const panelsRect = panels.getBoundingClientRect()
      const scrollParentRect = scrollParent.getBoundingClientRect()
      maxScroll = panelsRect.top - scrollParentRect.top + scrollParent.scrollTop
    }

    const rafId = requestAnimationFrame(() => {
      computeMax()
    })

    const handleScroll = () => {
      if (maxScroll <= 0) computeMax()
      if (maxScroll > 0 && scrollParent.scrollTop > maxScroll) {
        scrollParent.scrollTop = maxScroll
      }
    }

    const handleWheel = (e: WheelEvent) => {
      if (maxScroll <= 0) computeMax()
      if (maxScroll > 0 && e.deltaY > 0 && scrollParent.scrollTop >= maxScroll) {
        e.preventDefault()
      }
    }

    scrollParent.addEventListener('scroll', handleScroll)
    scrollParent.addEventListener('wheel', handleWheel, { passive: false })
    return () => {
      cancelAnimationFrame(rafId)
      scrollParent.removeEventListener('scroll', handleScroll)
      scrollParent.removeEventListener('wheel', handleWheel)
    }
  }, [dynamicViewData])

  React.useEffect(() => {
    if (!contextMenu) return
    const dismiss = () => setContextMenu(null)
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') dismiss()
    }
    document.addEventListener('click', dismiss)
    document.addEventListener('keydown', handleKeyDown)
    const specPanel = specPanelRef.current
    const workPanel = workItemsPanelRef.current
    if (specPanel) specPanel.addEventListener('scroll', dismiss)
    if (workPanel) workPanel.addEventListener('scroll', dismiss)
    return () => {
      document.removeEventListener('click', dismiss)
      document.removeEventListener('keydown', handleKeyDown)
      if (specPanel) specPanel.removeEventListener('scroll', dismiss)
      if (workPanel) workPanel.removeEventListener('scroll', dismiss)
    }
  }, [contextMenu])

  if (!dynamicViewData) {
    return null
  }

  const specification = dynamicViewData['specification'] || ''
  const srGroups = dynamicViewData[Constants._SRs_] || []
  const tsGroups = dynamicViewData[Constants._TSs_] || []
  const tcGroups = dynamicViewData[Constants._TCs_] || []
  const jGroups = dynamicViewData[Constants._Js] || []
  const docGroups = dynamicViewData[Constants._Ds] || []

  const columnNames = {
    specification: 'REFERENCE DOCUMENT',
    work_items: 'WORK ITEMS'
  }

  const getWorkItemIcon = (work_item_type, indirect) => {
    const iconMap = {
      [Constants._D]: <FileIcon />,
      [Constants._J]: <BalanceScaleIcon />,
      [Constants._SR]: <CatalogIcon />,
      [Constants._TS]: <TaskIcon />,
      [Constants._TC]: <CodeIcon />
    }
    const icon = iconMap[work_item_type]
    if (!icon) return ''
    if (indirect && (work_item_type === Constants._TS || work_item_type === Constants._TC)) {
      return (
        <Flex>
          <FlexItem>
            <Icon iconSize='sm'>
              <MigrationIcon />
            </Icon>{' '}
            &nbsp;
            <Icon iconSize='lg'>{icon}</Icon>
          </FlexItem>
        </Flex>
      )
    }
    return (
      <Flex>
        <FlexItem>
          <Icon iconSize='lg'>{icon}</Icon>
        </FlexItem>
      </Flex>
    )
  }

  const getStatusLabel = (status) => {
    let label_color = 'orange'
    const status_lc = status.toString().toLowerCase()
    if (status_lc === 'new') label_color = 'grey'
    else if (status_lc === 'approved') label_color = 'green'
    else if (status_lc === 'rejected') label_color = 'red'
    return (
      <Label color={label_color as any} name='label-status' isCompact>
        {status.toLowerCase()}
      </Label>
    )
  }

  const handleWorkItemClick = (_e: React.MouseEvent, workItemGroup, workItemType) => {
    if (selectedWorkItem && selectedWorkItemType === workItemType && selectedWorkItem === workItemGroup) {
      setSelectedWorkItem(null)
      setSelectedWorkItemType('')
    } else {
      setSelectedWorkItem(workItemGroup)
      setSelectedWorkItemType(workItemType)
      requestAnimationFrame(() => {
        if (workItemsPanelRef.current) {
          workItemsPanelRef.current.scrollTo({ top: 0, behavior: 'smooth' })
        }
        if (specPanelRef.current) {
          specPanelRef.current.scrollTo({ top: 0, behavior: 'smooth' })
        }
        const scrollParent = document.getElementById('primary-app-container')
        if (scrollParent) {
          scrollParent.scrollTo({ top: 0, behavior: 'smooth' })
        }
      })
    }
  }

  const clearSelection = () => {
    setSelectedWorkItem(null)
    setSelectedWorkItemType('')
  }

  const getContextMenuWorkItemLabel = (group, type) => {
    const keyMap = {
      [Constants._SR]: Constants._SR_,
      [Constants._TS]: Constants._TS_,
      [Constants._TC]: Constants._TC_,
      [Constants._J]: Constants._J,
      [Constants._D]: Constants._D
    }
    const typeLabels = {
      [Constants._SR]: 'SW Requirement',
      [Constants._TS]: 'Test Specification',
      [Constants._TC]: 'Test Case',
      [Constants._J]: 'Justification',
      [Constants._D]: 'Document'
    }
    const wi = group[keyMap[type]]
    const typeLabel = typeLabels[type] || type
    if (!wi) return typeLabel
    const title = wi.title || wi.description || ''
    const titleStr = title ? ` - ${Constants.getLimitedText(title, 40)}` : ''
    return `${typeLabel} ${wi.id}${titleStr}`
  }

  const getContextMenuWorkItemIcon = (work_item_type) => {
    const iconMap = {
      [Constants._D]: <FileIcon />,
      [Constants._J]: <BalanceScaleIcon />,
      [Constants._SR]: <CatalogIcon />,
      [Constants._TS]: <TaskIcon />,
      [Constants._TC]: <CodeIcon />
    }
    return iconMap[work_item_type] || null
  }

  const handleSpecContextMenu = (e: React.MouseEvent<HTMLPreElement>) => {
    const selection = window.getSelection()
    if (!selection || selection.isCollapsed) return

    const preEl = specContentPreRef.current
    if (!preEl) return
    if (!preEl.contains(selection.anchorNode) || !preEl.contains(selection.focusNode)) return

    const selRange = selection.getRangeAt(0)

    const startRange = document.createRange()
    startRange.selectNodeContents(preEl)
    startRange.setEnd(selRange.startContainer, selRange.startOffset)
    const selStartInPre = startRange.toString().length

    const endRange = document.createRange()
    endRange.selectNodeContents(preEl)
    endRange.setEnd(selRange.endContainer, selRange.endOffset)
    const selEndInPre = endRange.toString().length

    const baseOffset = parseInt(preEl.getAttribute('data-spec-base-offset') || '0', 10)
    const specSelStart = baseOffset + selStartInPre
    const specSelEnd = baseOffset + selEndInPre

    if (specSelStart >= specSelEnd) return

    const allGroupsByType: { groups: any[]; type: string }[] = [
      { groups: srGroups, type: Constants._SR },
      { groups: tsGroups, type: Constants._TS },
      { groups: tcGroups, type: Constants._TC },
      { groups: jGroups, type: Constants._J },
      { groups: docGroups, type: Constants._D }
    ]

    const matchingItems: { group: any; type: string; label: string; icon: React.ReactNode }[] = []
    const seen = new Set<string>()

    for (const { groups, type } of allGroupsByType) {
      for (const group of groups) {
        if (!group.snippets) continue
        for (const s of group.snippets) {
          if (!s.match || s.offset == null || !s.section) continue
          const snippetStart = s.offset
          const snippetEnd = s.offset + s.section.length
          if (snippetStart < specSelEnd && specSelStart < snippetEnd) {
            const wiKey = {
              [Constants._SR]: Constants._SR_,
              [Constants._TS]: Constants._TS_,
              [Constants._TC]: Constants._TC_,
              [Constants._J]: Constants._J,
              [Constants._D]: Constants._D
            }[type]
            const wi = wiKey ? group[wiKey] : null
            const key = `${type}-${wi?.id}`
            if (!seen.has(key)) {
              seen.add(key)
              matchingItems.push({
                group,
                type,
                label: getContextMenuWorkItemLabel(group, type),
                icon: getContextMenuWorkItemIcon(type)
              })
            }
            break
          }
        }
      }
    }

    if (matchingItems.length === 0) return

    matchingItems.sort((a, b) => {
      if (a.type !== b.type) return a.type.localeCompare(b.type)
      return a.label.localeCompare(b.label)
    })

    e.preventDefault()
    setContextMenu({ x: e.clientX, y: e.clientY, items: matchingItems })
  }

  const getAllMappedSnippets = () => {
    const allGroups = [...srGroups, ...tsGroups, ...tcGroups, ...jGroups, ...docGroups]
    const rawSnippets: { offset: number; end: number }[] = []
    for (const group of allGroups) {
      if (!group.snippets) continue
      for (const s of group.snippets) {
        if (s.match && s.offset != null && s.section) {
          rawSnippets.push({ offset: s.offset, end: s.offset + s.section.length })
        }
      }
    }
    if (rawSnippets.length === 0) return []
    rawSnippets.sort((a, b) => a.offset - b.offset)
    const merged: { offset: number; end: number }[] = [rawSnippets[0]]
    for (let i = 1; i < rawSnippets.length; i++) {
      const prev = merged[merged.length - 1]
      if (rawSnippets[i].offset <= prev.end) {
        prev.end = Math.max(prev.end, rawSnippets[i].end)
      } else {
        merged.push(rawSnippets[i])
      }
    }
    return merged
  }

  const renderSpecificationContent = () => {
    if (!selectedWorkItem || !selectedWorkItem.snippets) {
      const mergedSnippets = getAllMappedSnippets()
      if (mergedSnippets.length === 0) {
        return (
          <pre
            ref={specContentPreRef}
            data-spec-base-offset='0'
            onContextMenu={handleSpecContextMenu}
            style={{
              whiteSpace: 'pre-wrap',
              wordBreak: 'break-word',
              fontFamily: 'var(--pf-v5-global--FontFamily--monospace, monospace)',
              fontSize: 'var(--pf-v5-global--FontSize--sm, 0.875rem)',
              padding: '16px',
              margin: 0,
              backgroundColor: '#f6f8fa',
              color: '#57606a'
            }}
          >
            {specification}
          </pre>
        )
      }

      const segments: { text: string; type: 'covered' | 'uncovered' }[] = []
      let cursor = 0
      for (const snip of mergedSnippets) {
        if (snip.offset > cursor) {
          segments.push({ text: specification.substring(cursor, snip.offset), type: 'uncovered' })
        }
        segments.push({ text: specification.substring(snip.offset, snip.end), type: 'covered' })
        cursor = snip.end
      }
      if (cursor < specification.length) {
        segments.push({ text: specification.substring(cursor), type: 'uncovered' })
      }

      return (
        <pre
          ref={specContentPreRef}
          data-spec-base-offset='0'
          onContextMenu={handleSpecContextMenu}
          style={{
            whiteSpace: 'pre-wrap',
            wordBreak: 'break-word',
            fontFamily: 'var(--pf-v5-global--FontFamily--monospace, monospace)',
            fontSize: 'var(--pf-v5-global--FontSize--sm, 0.875rem)',
            padding: '16px',
            margin: 0,
            backgroundColor: '#f6f8fa'
          }}
        >
          {segments.map((seg, idx) => (
            <span
              key={idx}
              style={
                seg.type === 'covered'
                  ? {
                      backgroundColor: '#dbeafe',
                      color: '#1e40af',
                      borderLeft: '3px solid #3b82f6',
                      paddingLeft: '4px'
                    }
                  : { color: '#57606a' }
              }
            >
              {seg.text}
            </span>
          ))}
        </pre>
      )
    }

    const matchingSnippets = selectedWorkItem.snippets
      .filter((s) => s.match && s.offset != null && s.section)
      .sort((a, b) => a.offset - b.offset)

    const selectedRanges: { offset: number; end: number }[] = []
    for (const s of matchingSnippets) {
      selectedRanges.push({ offset: s.offset, end: s.offset + s.section.length })
    }
    if (selectedRanges.length > 1) {
      selectedRanges.sort((a, b) => a.offset - b.offset)
      const merged: { offset: number; end: number }[] = [selectedRanges[0]]
      for (let i = 1; i < selectedRanges.length; i++) {
        const prev = merged[merged.length - 1]
        if (selectedRanges[i].offset <= prev.end) {
          prev.end = Math.max(prev.end, selectedRanges[i].end)
        } else {
          merged.push(selectedRanges[i])
        }
      }
      selectedRanges.length = 0
      selectedRanges.push(...merged)
    }

    if (selectedRanges.length === 0) {
      return (
        <pre
          ref={specContentPreRef}
          data-spec-base-offset='0'
          onContextMenu={handleSpecContextMenu}
          style={{
            whiteSpace: 'pre-wrap',
            wordBreak: 'break-word',
            fontFamily: 'var(--pf-v5-global--FontFamily--monospace, monospace)',
            fontSize: 'var(--pf-v5-global--FontSize--sm, 0.875rem)',
            padding: '16px',
            margin: 0,
            backgroundColor: '#f6f8fa',
            color: '#57606a'
          }}
        >
          {specification}
        </pre>
      )
    }

    const firstStart = selectedRanges[0].offset
    const lastEnd = selectedRanges[selectedRanges.length - 1].end

    const segments: { text: string; type: 'covered' | 'uncovered' }[] = []
    let cursor = firstStart
    for (const range of selectedRanges) {
      if (range.offset > cursor) {
        segments.push({ text: specification.substring(cursor, range.offset), type: 'uncovered' })
      }
      segments.push({ text: specification.substring(range.offset, range.end), type: 'covered' })
      cursor = range.end
    }

    return (
      <React.Fragment>
        <Flex style={{ marginBottom: '8px' }}>
          <FlexItem>
            <Button variant='link' onClick={clearSelection} icon={<TimesIcon />}>
              Show full document
            </Button>
          </FlexItem>
        </Flex>
        <pre
          ref={specContentPreRef}
          data-spec-base-offset={String(firstStart)}
          onContextMenu={handleSpecContextMenu}
          style={{
            whiteSpace: 'pre-wrap',
            wordBreak: 'break-word',
            fontFamily: 'var(--pf-v5-global--FontFamily--monospace, monospace)',
            fontSize: 'var(--pf-v5-global--FontSize--sm, 0.875rem)',
            padding: '16px',
            margin: 0,
            backgroundColor: '#f6f8fa'
          }}
        >
          {segments.map((seg, idx) => (
            <span
              key={idx}
              style={
                seg.type === 'covered'
                  ? {
                      backgroundColor: '#dbeafe',
                      color: '#1e40af',
                      borderLeft: '3px solid #3b82f6',
                      paddingLeft: '4px'
                    }
                  : { color: '#57606a' }
              }
            >
              {seg.text}
            </span>
          ))}
        </pre>
      </React.Fragment>
    )
  }

  const buildFakeMappingListEntry = (workItemGroup, workItemType, snippet) => {
    const entry: any = {
      relation_id: snippet.relation_id,
      section: snippet.section,
      offset: snippet.offset,
      coverage: snippet.coverage,
      covered: snippet.covered || snippet.coverage,
      gap: snippet.coverage - (snippet.covered || snippet.coverage),
      created_by: workItemGroup.created_by || '',
      version: workItemGroup.version || '1.0',
      __tablename__: snippet.__tablename__,
      direct: true
    }

    const wiKey = workItemType.replace('-', '_')
    entry[wiKey] = workItemGroup[wiKey]

    if (workItemType === Constants._SR) {
      entry[Constants._SRs_] = snippet[Constants._SRs_] || []
      entry[Constants._TSs_] = snippet[Constants._TSs_] || []
      entry[Constants._TCs_] = snippet[Constants._TCs_] || []
    }
    if (workItemType === Constants._D) {
      entry[Constants._Ds] = snippet[Constants._Ds] || []
    }

    return entry
  }

  const snippetBadgeStyle: React.CSSProperties = {
    backgroundColor: 'var(--pf-v5-global--palette--purple-100, #e8daef)',
    color: 'var(--pf-v5-global--palette--purple-700, #6c3483)'
  }

  const getSnippetsBadge = (workItemGroup) => {
    const count = workItemGroup.snippets ? workItemGroup.snippets.length : 0
    return (
      <Tooltip content={`${count} snippet${count !== 1 ? 's' : ''} mapped`}>
        <Badge screenReaderText='Snippets' style={snippetBadgeStyle}>
          <ListIcon /> Snippets: {count}
        </Badge>
      </Tooltip>
    )
  }

  const renderManageSnippetsButton = (workItemGroup, workItemType) => {
    if (!auth.isLogged() || !Constants.hasWritePermission(api)) return null
    return (
      <Button
        variant='link'
        size='sm'
        icon={<ListIcon />}
        onClick={(e) => {
          e.stopPropagation()
          setSnippetsModalInfo(true, workItemGroup, workItemType)
        }}
      >
        Manage Snippets
      </Button>
    )
  }

  const indentStyle = { paddingLeft: '24px', borderLeft: '2px solid var(--pf-v5-global--palette--black-300, #d2d2d2)' }

  const renderNestedTestCases = (testCases, section, offset, parentType, parentRelatedToType, parentGroup, parentGroupType) => {
    if (!showIndirectTestCases) return null
    if (!testCases || testCases.length === 0) return null
    return testCases.map((tc, idx) => {
      const tcData = tc[Constants._TC_]
      if (!tcData) return null
      return (
        <React.Fragment key={`nested-tc-${tcData.id}-${idx}`}>
          <Card isSelectable onClick={(e) => handleWorkItemClick(e, parentGroup, parentGroupType)} style={{ cursor: 'pointer' }}>
            <CardBody>
              <div style={indentStyle}>
                <Flex direction={{ default: 'column' }}>
                  <Flex>
                    <FlexItem>{getWorkItemIcon(Constants._TC, true)}</FlexItem>
                    <FlexItem>
                      <TextContent>
                        <Text component={TextVariants.h2}>Test Case {tcData.id}</Text>
                      </TextContent>
                    </FlexItem>
                    <FlexItem>
                      <TestCaseMenuKebab
                        indirect={true}
                        setCommentModalInfo={setCommentModalInfo}
                        setDetailsModalInfo={setDetailsModalInfo}
                        setForkModalInfo={setForkModalInfo}
                        setHistoryModalInfo={setHistoryModalInfo}
                        setImplementationModalInfo={setImplementationModalInfo}
                        setUsageModalInfo={setUsageModalInfo}
                        setTcModalInfo={setTcModalInfo}
                        setDeleteModalInfo={setDeleteModalInfo}
                        setTestRunModalInfo={setTestRunModalInfo}
                        setTestResultsModalInfo={setTestResultsModalInfo}
                        mappingParentType={parentType}
                        mappingParentRelatedToType={parentRelatedToType}
                        mappingIndex={idx}
                        mappingList={testCases}
                        mappingSection={section}
                        mappingOffset={offset}
                        api={api}
                      />
                    </FlexItem>
                  </Flex>
                  <Flex>
                    {tc.version && (
                      <FlexItem>
                        <Text component={TextVariants.h6}>ver. {tc.version}</Text>
                      </FlexItem>
                    )}
                    <FlexItem>{getStatusLabel(tcData.status)}</FlexItem>
                    <FlexItem>
                      <CompletionLabel mappedItem={tc} />
                    </FlexItem>
                  </Flex>
                  <Flex>
                    <FlexItem>
                      <TextContent>
                        <Text component={TextVariants.h5}>{Constants.getLimitedText(tcData.title, 0)}</Text>
                        <Text className='work-item-detail-text'>
                          <ReactMarkdown>{Constants.getLimitedText(tcData.description, 0)}</ReactMarkdown>
                        </Text>
                      </TextContent>
                    </FlexItem>
                  </Flex>
                </Flex>
              </div>
            </CardBody>
          </Card>
          <Divider />
        </React.Fragment>
      )
    })
  }

  const renderNestedTestSpecifications = (testSpecs, section, offset, parentType, parentRelatedToType, parentGroup, parentGroupType) => {
    if (!showIndirectTestSpecifications) return null
    if (!testSpecs || testSpecs.length === 0) return null
    return testSpecs.map((ts, idx) => {
      const tsData = ts[Constants._TS_]
      if (!tsData) return null
      return (
        <React.Fragment key={`nested-ts-${tsData.id}-${idx}`}>
          <Card isSelectable onClick={(e) => handleWorkItemClick(e, parentGroup, parentGroupType)} style={{ cursor: 'pointer' }}>
            <CardBody>
              <div style={indentStyle}>
                <Flex direction={{ default: 'column' }}>
                  <Flex>
                    <FlexItem>{getWorkItemIcon(Constants._TS, true)}</FlexItem>
                    <FlexItem>
                      <TextContent>
                        <Text component={TextVariants.h2}>Test Specification {tsData.id}</Text>
                      </TextContent>
                    </FlexItem>
                    <FlexItem>
                      <TestSpecificationMenuKebab
                        indirect={true}
                        setCommentModalInfo={setCommentModalInfo}
                        setDetailsModalInfo={setDetailsModalInfo}
                        setForkModalInfo={setForkModalInfo}
                        setHistoryModalInfo={setHistoryModalInfo}
                        setUsageModalInfo={setUsageModalInfo}
                        setTcModalInfo={setTcModalInfo}
                        setTsModalInfo={setTsModalInfo}
                        setDeleteModalInfo={setDeleteModalInfo}
                        mappingParentType={parentType}
                        mappingParentRelatedToType={parentRelatedToType}
                        mappingIndex={idx}
                        mappingList={testSpecs}
                        mappingSection={section}
                        mappingOffset={offset}
                        api={api}
                      />
                    </FlexItem>
                  </Flex>
                  <Flex>
                    {ts.version && (
                      <FlexItem>
                        <Text component={TextVariants.h6}>ver. {ts.version}</Text>
                      </FlexItem>
                    )}
                    <FlexItem>{getStatusLabel(tsData.status)}</FlexItem>
                    <FlexItem>
                      <CompletionLabel mappedItem={ts} />
                    </FlexItem>
                  </Flex>
                  <Flex>
                    <FlexItem>
                      <TextContent>
                        <Text component={TextVariants.h5}>{Constants.getLimitedText(tsData.title, 0)}</Text>
                        <Text component={TextVariants.h6}>Preconditions:</Text>
                        <Text className='work-item-detail-text'>
                          <ReactMarkdown>{Constants.getLimitedText(tsData.preconditions, 0)}</ReactMarkdown>
                        </Text>
                        <Text component={TextVariants.h6}>Test Description:</Text>
                        <Text className='work-item-detail-text'>
                          <ReactMarkdown>{Constants.getLimitedText(tsData.test_description, 0)}</ReactMarkdown>
                        </Text>
                        <Text component={TextVariants.h6}>Expected Behavior:</Text>
                        <Text className='work-item-detail-text'>
                          <ReactMarkdown>{Constants.getLimitedText(tsData.expected_behavior, 0)}</ReactMarkdown>
                        </Text>
                      </TextContent>
                    </FlexItem>
                  </Flex>
                </Flex>
              </div>
            </CardBody>
            {tsData[Constants._TCs_] && tsData[Constants._TCs_].length > 0 && (
              <CardBody>
                <div style={indentStyle}>
                  {renderNestedTestCases(
                    tsData[Constants._TCs_],
                    section,
                    offset,
                    'test-specification',
                    parentType,
                    parentGroup,
                    parentGroupType
                  )}
                </div>
              </CardBody>
            )}
          </Card>
          <Divider />
        </React.Fragment>
      )
    })
  }

  const renderNestedSwRequirements = (swReqs, section, offset, parentType, parentRelatedToType, parentGroup, parentGroupType) => {
    if (!swReqs || swReqs.length === 0) return null
    return swReqs.map((srItem, idx) => {
      const srData = srItem[Constants._SR_]
      if (!srData) return null
      return (
        <React.Fragment key={`nested-sr-${srData.id}-${idx}`}>
          <Card isSelectable onClick={(e) => handleWorkItemClick(e, parentGroup, parentGroupType)} style={{ cursor: 'pointer' }}>
            <CardBody>
              <div style={indentStyle}>
                <Flex direction={{ default: 'column' }}>
                  <Flex>
                    <FlexItem>{getWorkItemIcon(Constants._SR, false)}</FlexItem>
                    <FlexItem>
                      <TextContent>
                        <Text component={TextVariants.h2}>Software Requirement {srData.id}</Text>
                      </TextContent>
                    </FlexItem>
                    <FlexItem>
                      <SwRequirementMenuKebab
                        setCommentModalInfo={setCommentModalInfo}
                        setDetailsModalInfo={setDetailsModalInfo}
                        setHistoryModalInfo={setHistoryModalInfo}
                        setUsageModalInfo={setUsageModalInfo}
                        setSrModalInfo={setSrModalInfo}
                        setTsModalInfo={setTsModalInfo}
                        setTcModalInfo={setTcModalInfo}
                        setDeleteModalInfo={setDeleteModalInfo}
                        setForkModalInfo={setForkModalInfo}
                        api={api}
                        indirect={true}
                        mappingParentType={parentType}
                        mappingParentRelatedToType={parentRelatedToType}
                        mappingList={swReqs}
                        mappingIndex={idx}
                        mappingSection={section}
                        mappingOffset={offset}
                      />
                    </FlexItem>
                  </Flex>
                  <Flex>
                    {srItem.version && (
                      <FlexItem>
                        <Text component={TextVariants.h6}>ver. {srItem.version}</Text>
                      </FlexItem>
                    )}
                    <FlexItem>{getStatusLabel(srData.status)}</FlexItem>
                    <FlexItem>
                      <CompletionLabel mappedItem={srItem} />
                    </FlexItem>
                  </Flex>
                  <Flex>
                    <FlexItem>
                      <TextContent>
                        <Text component={TextVariants.h5}>{Constants.getLimitedText(srData.title, 0)}</Text>
                        <Text className='work-item-detail-text'>
                          <ReactMarkdown>{Constants.getLimitedText(srData.description, 0)}</ReactMarkdown>
                        </Text>
                      </TextContent>
                    </FlexItem>
                  </Flex>
                </Flex>
              </div>
            </CardBody>
          </Card>
          <Divider />
        </React.Fragment>
      )
    })
  }

  const renderNestedDocuments = (docs, section, offset, parentType, parentRelatedToType, parentGroup, parentGroupType) => {
    if (!docs || docs.length === 0) return null
    return docs.map((docItem, idx) => {
      const docData = docItem[Constants._D]
      if (!docData) return null
      return (
        <React.Fragment key={`nested-doc-${docData.id}-${idx}`}>
          <Card isSelectable onClick={(e) => handleWorkItemClick(e, parentGroup, parentGroupType)} style={{ cursor: 'pointer' }}>
            <CardBody>
              <div style={indentStyle}>
                <Flex direction={{ default: 'column' }}>
                  <Flex>
                    <FlexItem>{getWorkItemIcon(Constants._D, false)}</FlexItem>
                    <FlexItem>
                      <TextContent>
                        <Text component={TextVariants.h2}>Document {docData.id}</Text>
                      </TextContent>
                    </FlexItem>
                    <FlexItem>
                      <DocumentMenuKebab
                        indirect={true}
                        setCommentModalInfo={setCommentModalInfo}
                        setDocModalInfo={setDocModalInfo}
                        setDetailsModalInfo={setDetailsModalInfo}
                        setHistoryModalInfo={setHistoryModalInfo}
                        setUsageModalInfo={setUsageModalInfo}
                        setDeleteModalInfo={setDeleteModalInfo}
                        setForkModalInfo={setForkModalInfo}
                        mappingParentType={parentType}
                        mappingParentRelatedToType={parentRelatedToType}
                        mappingList={docs}
                        mappingIndex={idx}
                        mappingSection={section}
                        mappingOffset={offset}
                        api={api}
                      />
                    </FlexItem>
                  </Flex>
                  <Flex>
                    {docItem.version && (
                      <FlexItem>
                        <Text component={TextVariants.h6}>ver. {docItem.version}</Text>
                      </FlexItem>
                    )}
                    <FlexItem>{getStatusLabel(docData.status)}</FlexItem>
                    <FlexItem>
                      <CompletionLabel mappedItem={docItem} />
                    </FlexItem>
                  </Flex>
                  <Flex>
                    <FlexItem>
                      <TextContent>
                        <Text component={TextVariants.h5}>{docData.title}</Text>
                        <Text className='work-item-detail-text'>
                          <ReactMarkdown>{Constants.getLimitedText(docData.description, 0)}</ReactMarkdown>
                        </Text>
                      </TextContent>
                    </FlexItem>
                  </Flex>
                </Flex>
              </div>
            </CardBody>
          </Card>
          <Divider />
        </React.Fragment>
      )
    })
  }

  const renderSwRequirementCard = (srGroup, index) => {
    const sr = srGroup[Constants._SR_]
    if (!sr) return null
    const isSelected = selectedWorkItem === srGroup && selectedWorkItemType === Constants._SR
    const firstSnippet = srGroup.snippets && srGroup.snippets.length > 0 ? srGroup.snippets[0] : null
    const fakeMappingList = firstSnippet ? [buildFakeMappingListEntry(srGroup, Constants._SR, firstSnippet)] : []

    return (
      <React.Fragment key={`sr-${sr.id}-${index}`}>
        <Card
          isSelectable
          isSelected={isSelected}
          onClick={(e) => handleWorkItemClick(e, srGroup, Constants._SR)}
          style={{ cursor: 'pointer' }}
        >
          <CardBody>
            <Flex direction={{ default: 'column' }}>
              <Flex>
                <FlexItem>{getWorkItemIcon(Constants._SR, false)}</FlexItem>
                <FlexItem>
                  <TextContent>
                    <Text component={TextVariants.h2}>Software Requirement {sr.id}</Text>
                  </TextContent>
                </FlexItem>
                {firstSnippet && (
                  <FlexItem>
                    <SwRequirementMenuKebab
                      setCommentModalInfo={setCommentModalInfo}
                      setDetailsModalInfo={setDetailsModalInfo}
                      setHistoryModalInfo={setHistoryModalInfo}
                      setUsageModalInfo={setUsageModalInfo}
                      setSrModalInfo={setSrModalInfo}
                      setTsModalInfo={setTsModalInfo}
                      setTcModalInfo={setTcModalInfo}
                      setDeleteModalInfo={setDeleteModalInfo}
                      setForkModalInfo={setForkModalInfo}
                      api={api}
                      indirect={false}
                      mappingParentType={Constants._A}
                      mappingParentRelatedToType=''
                      mappingList={fakeMappingList}
                      mappingIndex={0}
                      mappingSection={firstSnippet.section}
                      mappingOffset={firstSnippet.offset}
                    />
                  </FlexItem>
                )}
              </Flex>
              <Flex>
                {srGroup.version && (
                  <FlexItem>
                    <Text component={TextVariants.h6}>ver. {srGroup.version}</Text>
                  </FlexItem>
                )}
                <FlexItem>{getStatusLabel(sr.status)}</FlexItem>
                {firstSnippet && (
                  <FlexItem>
                    <CompletionLabel mappedItem={fakeMappingList[0]} />
                  </FlexItem>
                )}
                <FlexItem>{getSnippetsBadge(srGroup)}</FlexItem>
                {auth.isLogged() && (
                  <FlexItem>
                    <CommentBadges
                      leading={
                        <Tooltip content='Click to read and add comments and todos'>
                          <Button
                            variant='plain'
                            icon={<OutlinedCommentsIcon />}
                            onClick={(e) => {
                              e.stopPropagation()
                              if (firstSnippet) {
                                setCommentModalInfo(true, Constants._SR, Constants._A, '', fakeMappingList, 0)
                              }
                            }}
                          />
                        </Tooltip>
                      }
                      comment_count={sr.comment_count}
                      todo_count={sr.todo_count}
                    />
                  </FlexItem>
                )}
              </Flex>
              <Flex>
                <FlexItem>
                  <TextContent>
                    <Text component={TextVariants.h5}>{Constants.getLimitedText(sr.title, 0)}</Text>
                    <Text className='work-item-detail-text'>
                      <ReactMarkdown>{Constants.getLimitedText(sr.description, 0)}</ReactMarkdown>
                    </Text>
                  </TextContent>
                </FlexItem>
              </Flex>
              <Flex>
                <FlexItem>{renderManageSnippetsButton(srGroup, Constants._SR)}</FlexItem>
              </Flex>
            </Flex>
          </CardBody>
          {firstSnippet &&
            (firstSnippet[Constants._SRs_]?.length > 0 ||
              firstSnippet[Constants._TSs_]?.length > 0 ||
              firstSnippet[Constants._TCs_]?.length > 0) && (
              <CardBody>
                {renderNestedSwRequirements(
                  firstSnippet[Constants._SRs_],
                  firstSnippet.section,
                  firstSnippet.offset,
                  Constants._SR,
                  '',
                  srGroup,
                  Constants._SR
                )}
                {renderNestedTestSpecifications(
                  firstSnippet[Constants._TSs_],
                  firstSnippet.section,
                  firstSnippet.offset,
                  Constants._SR,
                  '',
                  srGroup,
                  Constants._SR
                )}
                {renderNestedTestCases(
                  firstSnippet[Constants._TCs_],
                  firstSnippet.section,
                  firstSnippet.offset,
                  Constants._SR,
                  '',
                  srGroup,
                  Constants._SR
                )}
              </CardBody>
            )}
        </Card>
        <Divider />
      </React.Fragment>
    )
  }

  const renderTestSpecificationCard = (tsGroup, index) => {
    const ts = tsGroup[Constants._TS_]
    if (!ts) return null
    const isSelected = selectedWorkItem === tsGroup && selectedWorkItemType === Constants._TS
    const firstSnippet = tsGroup.snippets && tsGroup.snippets.length > 0 ? tsGroup.snippets[0] : null
    const fakeMappingList = firstSnippet ? [buildFakeMappingListEntry(tsGroup, Constants._TS, firstSnippet)] : []

    return (
      <React.Fragment key={`ts-${ts.id}-${index}`}>
        <Card
          isSelectable
          isSelected={isSelected}
          onClick={(e) => handleWorkItemClick(e, tsGroup, Constants._TS)}
          style={{ cursor: 'pointer' }}
        >
          <CardBody>
            <Flex direction={{ default: 'column' }}>
              <Flex>
                <FlexItem>{getWorkItemIcon(Constants._TS, false)}</FlexItem>
                <FlexItem>
                  <TextContent>
                    <Text component={TextVariants.h2}>Test Specification {ts.id}</Text>
                  </TextContent>
                </FlexItem>
                {firstSnippet && (
                  <FlexItem>
                    <TestSpecificationMenuKebab
                      indirect={false}
                      setCommentModalInfo={setCommentModalInfo}
                      setDetailsModalInfo={setDetailsModalInfo}
                      setForkModalInfo={setForkModalInfo}
                      setHistoryModalInfo={setHistoryModalInfo}
                      setUsageModalInfo={setUsageModalInfo}
                      setTcModalInfo={setTcModalInfo}
                      setTsModalInfo={setTsModalInfo}
                      setDeleteModalInfo={setDeleteModalInfo}
                      mappingParentType={Constants._A}
                      mappingParentRelatedToType=''
                      mappingIndex={0}
                      mappingList={fakeMappingList}
                      mappingSection={firstSnippet.section}
                      mappingOffset={firstSnippet.offset}
                      api={api}
                    />
                  </FlexItem>
                )}
              </Flex>
              <Flex>
                {tsGroup.version && (
                  <FlexItem>
                    <Text component={TextVariants.h6}>ver. {tsGroup.version}</Text>
                  </FlexItem>
                )}
                <FlexItem>{getStatusLabel(ts.status)}</FlexItem>
                {firstSnippet && (
                  <FlexItem>
                    <CompletionLabel mappedItem={fakeMappingList[0]} />
                  </FlexItem>
                )}
                <FlexItem>{getSnippetsBadge(tsGroup)}</FlexItem>
                {auth.isLogged() && (
                  <FlexItem>
                    <CommentBadges
                      leading={
                        <Tooltip content='Click to read and add comments and todos'>
                          <Button
                            variant='plain'
                            icon={<OutlinedCommentsIcon />}
                            onClick={(e) => {
                              e.stopPropagation()
                              if (firstSnippet) {
                                setCommentModalInfo(true, 'test-specification', Constants._A, '', fakeMappingList, 0)
                              }
                            }}
                          />
                        </Tooltip>
                      }
                      comment_count={ts.comment_count}
                      todo_count={ts.todo_count}
                    />
                  </FlexItem>
                )}
              </Flex>
              <Flex>
                <FlexItem>
                  <TextContent>
                    <Text component={TextVariants.h5}>{Constants.getLimitedText(ts.title, 0)}</Text>
                    <Text component={TextVariants.h6}>Preconditions:</Text>
                    <Text className='work-item-detail-text'>
                      <ReactMarkdown>{Constants.getLimitedText(ts.preconditions, 0)}</ReactMarkdown>
                    </Text>
                    <Text component={TextVariants.h6}>Test Description:</Text>
                    <Text className='work-item-detail-text'>
                      <ReactMarkdown>{Constants.getLimitedText(ts.test_description, 0)}</ReactMarkdown>
                    </Text>
                    <Text component={TextVariants.h6}>Expected Behavior:</Text>
                    <Text className='work-item-detail-text'>
                      <ReactMarkdown>{Constants.getLimitedText(ts.expected_behavior, 0)}</ReactMarkdown>
                    </Text>
                  </TextContent>
                </FlexItem>
              </Flex>
              <Flex>
                <FlexItem>{renderManageSnippetsButton(tsGroup, Constants._TS)}</FlexItem>
              </Flex>
            </Flex>
          </CardBody>
        </Card>
        <Divider />
      </React.Fragment>
    )
  }

  const renderTestCaseCard = (tcGroup, index) => {
    const tc = tcGroup[Constants._TC_]
    if (!tc) return null
    const isSelected = selectedWorkItem === tcGroup && selectedWorkItemType === Constants._TC
    const firstSnippet = tcGroup.snippets && tcGroup.snippets.length > 0 ? tcGroup.snippets[0] : null
    const fakeMappingList = firstSnippet ? [buildFakeMappingListEntry(tcGroup, Constants._TC, firstSnippet)] : []

    return (
      <React.Fragment key={`tc-${tc.id}-${index}`}>
        <Card
          isSelectable
          isSelected={isSelected}
          onClick={(e) => handleWorkItemClick(e, tcGroup, Constants._TC)}
          style={{ cursor: 'pointer' }}
        >
          <CardBody>
            <Flex direction={{ default: 'column' }}>
              <Flex>
                <FlexItem>{getWorkItemIcon(Constants._TC, false)}</FlexItem>
                <FlexItem>
                  <TextContent>
                    <Text component={TextVariants.h2}>Test Case {tc.id}</Text>
                  </TextContent>
                </FlexItem>
                {firstSnippet && (
                  <FlexItem>
                    <TestCaseMenuKebab
                      indirect={false}
                      setCommentModalInfo={setCommentModalInfo}
                      setDetailsModalInfo={setDetailsModalInfo}
                      setForkModalInfo={setForkModalInfo}
                      setHistoryModalInfo={setHistoryModalInfo}
                      setImplementationModalInfo={setImplementationModalInfo}
                      setUsageModalInfo={setUsageModalInfo}
                      setTcModalInfo={setTcModalInfo}
                      setDeleteModalInfo={setDeleteModalInfo}
                      setTestRunModalInfo={setTestRunModalInfo}
                      setTestResultsModalInfo={setTestResultsModalInfo}
                      mappingParentType={Constants._A}
                      mappingParentRelatedToType=''
                      mappingIndex={0}
                      mappingList={fakeMappingList}
                      mappingSection={firstSnippet.section}
                      mappingOffset={firstSnippet.offset}
                      api={api}
                    />
                  </FlexItem>
                )}
              </Flex>
              <Flex>
                {tcGroup.version && (
                  <FlexItem>
                    <Text component={TextVariants.h6}>ver. {tcGroup.version}</Text>
                  </FlexItem>
                )}
                <FlexItem>{getStatusLabel(tc.status)}</FlexItem>
                {firstSnippet && (
                  <FlexItem>
                    <CompletionLabel mappedItem={fakeMappingList[0]} />
                  </FlexItem>
                )}
                <FlexItem>{getSnippetsBadge(tcGroup)}</FlexItem>
                {auth.isLogged() && (
                  <FlexItem>
                    <CommentBadges
                      leading={
                        <Tooltip content='Click to read and add comments and todos'>
                          <Button
                            variant='plain'
                            icon={<OutlinedCommentsIcon />}
                            onClick={(e) => {
                              e.stopPropagation()
                              if (firstSnippet) {
                                setCommentModalInfo(true, Constants._TC, Constants._A, '', fakeMappingList, 0)
                              }
                            }}
                          />
                        </Tooltip>
                      }
                      comment_count={tc.comment_count}
                      todo_count={tc.todo_count}
                    />
                  </FlexItem>
                )}
              </Flex>
              <Flex>
                <FlexItem>
                  <TextContent>
                    <Text component={TextVariants.h5}>{Constants.getLimitedText(tc.title, 0)}</Text>
                    <Text className='work-item-detail-text'>
                      <ReactMarkdown>{Constants.getLimitedText(tc.description, 0)}</ReactMarkdown>
                    </Text>
                  </TextContent>
                </FlexItem>
              </Flex>
              <Flex>
                <FlexItem>{renderManageSnippetsButton(tcGroup, Constants._TC)}</FlexItem>
              </Flex>
            </Flex>
          </CardBody>
        </Card>
        <Divider />
      </React.Fragment>
    )
  }

  const renderJustificationCard = (jGroup, index) => {
    const j = jGroup[Constants._J]
    if (!j) return null
    const isSelected = selectedWorkItem === jGroup && selectedWorkItemType === Constants._J
    const firstSnippet = jGroup.snippets && jGroup.snippets.length > 0 ? jGroup.snippets[0] : null
    const fakeMappingList = firstSnippet ? [buildFakeMappingListEntry(jGroup, Constants._J, firstSnippet)] : []

    return (
      <React.Fragment key={`j-${j.id}-${index}`}>
        <Card
          isSelectable
          isSelected={isSelected}
          onClick={(e) => handleWorkItemClick(e, jGroup, Constants._J)}
          style={{ cursor: 'pointer' }}
        >
          <CardBody>
            <Flex direction={{ default: 'column' }}>
              <Flex>
                <FlexItem>{getWorkItemIcon(Constants._J, false)}</FlexItem>
                <FlexItem>
                  <TextContent>
                    <Text component={TextVariants.h2}>Justification {j.id}</Text>
                  </TextContent>
                </FlexItem>
                {firstSnippet && (
                  <FlexItem>
                    <JustificationMenuKebab
                      setCommentModalInfo={setCommentModalInfo}
                      setJModalInfo={setJModalInfo}
                      setForkModalInfo={setForkModalInfo}
                      setDetailsModalInfo={setDetailsModalInfo}
                      setHistoryModalInfo={setHistoryModalInfo}
                      setUsageModalInfo={setUsageModalInfo}
                      setDeleteModalInfo={setDeleteModalInfo}
                      mappingList={fakeMappingList}
                      mappingIndex={0}
                      mappingSection={firstSnippet.section}
                      mappingOffset={firstSnippet.offset}
                      api={api}
                    />
                  </FlexItem>
                )}
              </Flex>
              <Flex>
                {jGroup.version && (
                  <FlexItem>
                    <Text component={TextVariants.h6}>ver. {jGroup.version}</Text>
                  </FlexItem>
                )}
                <FlexItem>{getStatusLabel(j.status)}</FlexItem>
                {firstSnippet && (
                  <FlexItem>
                    <CompletionLabel mappedItem={fakeMappingList[0]} />
                  </FlexItem>
                )}
                <FlexItem>{getSnippetsBadge(jGroup)}</FlexItem>
                {auth.isLogged() && (
                  <FlexItem>
                    <CommentBadges
                      leading={
                        <Tooltip content='Click to read and add comments and todos'>
                          <Button
                            variant='plain'
                            icon={<OutlinedCommentsIcon />}
                            onClick={(e) => {
                              e.stopPropagation()
                              if (firstSnippet) {
                                setCommentModalInfo(true, Constants._J, Constants._A, '', fakeMappingList, 0)
                              }
                            }}
                          />
                        </Tooltip>
                      }
                      comment_count={j.comment_count}
                      todo_count={j.todo_count}
                    />
                  </FlexItem>
                )}
              </Flex>
              <Flex>
                <FlexItem>
                  <TextContent>
                    <Text className='work-item-detail-text'>
                      <ReactMarkdown>{Constants.getLimitedText(j.description, 0)}</ReactMarkdown>
                    </Text>
                  </TextContent>
                </FlexItem>
              </Flex>
              <Flex>
                <FlexItem>{renderManageSnippetsButton(jGroup, Constants._J)}</FlexItem>
              </Flex>
            </Flex>
          </CardBody>
        </Card>
        <Divider />
      </React.Fragment>
    )
  }

  const renderDocumentCard = (docGroup, index) => {
    const doc = docGroup[Constants._D]
    if (!doc) return null
    const isSelected = selectedWorkItem === docGroup && selectedWorkItemType === Constants._D
    const firstSnippet = docGroup.snippets && docGroup.snippets.length > 0 ? docGroup.snippets[0] : null
    const fakeMappingList = firstSnippet ? [buildFakeMappingListEntry(docGroup, Constants._D, firstSnippet)] : []

    return (
      <React.Fragment key={`doc-${doc.id}-${index}`}>
        <Card
          isSelectable
          isSelected={isSelected}
          onClick={(e) => handleWorkItemClick(e, docGroup, Constants._D)}
          style={{ cursor: 'pointer' }}
        >
          <CardBody>
            <Flex direction={{ default: 'column' }}>
              <Flex>
                <FlexItem>{getWorkItemIcon(Constants._D, false)}</FlexItem>
                <FlexItem>
                  <TextContent>
                    <Text component={TextVariants.h2}>Document {doc.id}</Text>
                  </TextContent>
                </FlexItem>
                {firstSnippet && (
                  <FlexItem>
                    <DocumentMenuKebab
                      indirect={false}
                      setCommentModalInfo={setCommentModalInfo}
                      setDocModalInfo={setDocModalInfo}
                      setDetailsModalInfo={setDetailsModalInfo}
                      setHistoryModalInfo={setHistoryModalInfo}
                      setUsageModalInfo={setUsageModalInfo}
                      setDeleteModalInfo={setDeleteModalInfo}
                      setForkModalInfo={setForkModalInfo}
                      mappingParentType={Constants._A}
                      mappingParentRelatedToType=''
                      mappingList={fakeMappingList}
                      mappingIndex={0}
                      mappingSection={firstSnippet.section}
                      mappingOffset={firstSnippet.offset}
                      api={api}
                    />
                  </FlexItem>
                )}
              </Flex>
              <Flex>
                {docGroup.version && (
                  <FlexItem>
                    <Text component={TextVariants.h6}>ver. {docGroup.version}</Text>
                  </FlexItem>
                )}
                <FlexItem>{getStatusLabel(doc.status)}</FlexItem>
                {firstSnippet && (
                  <FlexItem>
                    <CompletionLabel mappedItem={fakeMappingList[0]} />
                  </FlexItem>
                )}
                <FlexItem>{getSnippetsBadge(docGroup)}</FlexItem>
                {auth.isLogged() && (
                  <FlexItem>
                    <CommentBadges
                      leading={
                        <Tooltip content='Click to read and add comments and todos'>
                          <Button
                            variant='plain'
                            icon={<OutlinedCommentsIcon />}
                            onClick={(e) => {
                              e.stopPropagation()
                              if (firstSnippet) {
                                setCommentModalInfo(true, Constants._D, Constants._A, '', fakeMappingList, 0)
                              }
                            }}
                          />
                        </Tooltip>
                      }
                      comment_count={doc.comment_count}
                      todo_count={doc.todo_count}
                    />
                  </FlexItem>
                )}
              </Flex>
              <Flex>
                <FlexItem>
                  <TextContent>
                    <Text component={TextVariants.h5}>{doc.title}</Text>
                    <Text className='work-item-detail-text'>
                      <ReactMarkdown>{Constants.getLimitedText(doc.description, 0)}</ReactMarkdown>
                    </Text>
                  </TextContent>
                </FlexItem>
              </Flex>
              <Flex>
                <FlexItem>{renderManageSnippetsButton(docGroup, Constants._D)}</FlexItem>
              </Flex>
            </Flex>
          </CardBody>
          {firstSnippet && firstSnippet[Constants._Ds]?.length > 0 && (
            <CardBody>
              {renderNestedDocuments(
                firstSnippet[Constants._Ds],
                firstSnippet.section,
                firstSnippet.offset,
                Constants._D,
                '',
                docGroup,
                Constants._D
              )}
            </CardBody>
          )}
        </Card>
        <Divider />
      </React.Fragment>
    )
  }

  const hasWorkItems = srGroups.length > 0 || tsGroups.length > 0 || tcGroups.length > 0 || jGroups.length > 0 || docGroups.length > 0

  const renderSelectedCard = () => {
    if (!selectedWorkItem) return null
    if (selectedWorkItemType === Constants._SR) return renderSwRequirementCard(selectedWorkItem, 0)
    if (selectedWorkItemType === Constants._TS) return renderTestSpecificationCard(selectedWorkItem, 0)
    if (selectedWorkItemType === Constants._TC) return renderTestCaseCard(selectedWorkItem, 0)
    if (selectedWorkItemType === Constants._J) return renderJustificationCard(selectedWorkItem, 0)
    if (selectedWorkItemType === Constants._D) return renderDocumentCard(selectedWorkItem, 0)
    return null
  }

  const renderWorkItemsGrouped = (excludeSelected: boolean) => {
    const filterGroup = (groups) => {
      if (!excludeSelected || !selectedWorkItem) return groups
      return groups.filter((g) => g !== selectedWorkItem)
    }

    return (
      <React.Fragment>
        {srGroups.length > 0 && filterGroup(srGroups).length > 0 && (
          <React.Fragment>
            <TextContent>
              <Text component={TextVariants.h3}>Software Requirements</Text>
            </TextContent>
            <Divider />
            {filterGroup(srGroups).map((srGroup, idx) => renderSwRequirementCard(srGroup, idx))}
          </React.Fragment>
        )}

        {tsGroups.length > 0 && filterGroup(tsGroups).length > 0 && (
          <React.Fragment>
            <TextContent>
              <Text component={TextVariants.h3}>Test Specifications</Text>
            </TextContent>
            <Divider />
            {filterGroup(tsGroups).map((tsGroup, idx) => renderTestSpecificationCard(tsGroup, idx))}
          </React.Fragment>
        )}

        {tcGroups.length > 0 && filterGroup(tcGroups).length > 0 && (
          <React.Fragment>
            <TextContent>
              <Text component={TextVariants.h3}>Test Cases</Text>
            </TextContent>
            <Divider />
            {filterGroup(tcGroups).map((tcGroup, idx) => renderTestCaseCard(tcGroup, idx))}
          </React.Fragment>
        )}

        {jGroups.length > 0 && filterGroup(jGroups).length > 0 && (
          <React.Fragment>
            <TextContent>
              <Text component={TextVariants.h3}>Justifications</Text>
            </TextContent>
            <Divider />
            {filterGroup(jGroups).map((jGroup, idx) => renderJustificationCard(jGroup, idx))}
          </React.Fragment>
        )}

        {docGroups.length > 0 && filterGroup(docGroups).length > 0 && (
          <React.Fragment>
            <TextContent>
              <Text component={TextVariants.h3}>Documents</Text>
            </TextContent>
            <Divider />
            {filterGroup(docGroups).map((docGroup, idx) => renderDocumentCard(docGroup, idx))}
          </React.Fragment>
        )}
      </React.Fragment>
    )
  }

  return (
    <div
      ref={panelsRef}
      id='table-dynamic-view'
      style={{
        display: 'flex',
        height: '100vh',
        borderTop: '1px solid var(--pf-v5-global--BorderColor--100, #d2d2d2)'
      }}
    >
      <div
        ref={specPanelRef}
        style={{
          flex: 1,
          overflowY: 'auto',
          borderRight: '1px solid var(--pf-v5-global--BorderColor--100, #d2d2d2)'
        }}
      >
        <div
          style={{
            position: 'sticky',
            top: 0,
            zIndex: 1,
            backgroundColor: 'var(--pf-v5-global--BackgroundColor--100, #fff)',
            padding: '8px 16px',
            fontWeight: 700,
            fontSize: 'var(--pf-v5-global--FontSize--sm, 0.875rem)',
            borderBottom: '1px solid var(--pf-v5-global--BorderColor--100, #d2d2d2)'
          }}
        >
          {columnNames.specification}
        </div>
        <div style={{ padding: '16px' }}>{renderSpecificationContent()}</div>
      </div>
      <div
        ref={workItemsPanelRef}
        style={{
          flex: 1,
          overflowY: 'auto'
        }}
      >
        <div
          style={{
            position: 'sticky',
            top: 0,
            zIndex: 1,
            backgroundColor: 'var(--pf-v5-global--BackgroundColor--100, #fff)',
            padding: '8px 16px',
            fontWeight: 700,
            fontSize: 'var(--pf-v5-global--FontSize--sm, 0.875rem)',
            borderBottom: '1px solid var(--pf-v5-global--BorderColor--100, #d2d2d2)'
          }}
        >
          {columnNames.work_items}
        </div>
        <div style={{ padding: '16px' }}>
          {!hasWorkItems && (
            <TextContent>
              <Text component={TextVariants.p}>No work items mapped to this specification.</Text>
            </TextContent>
          )}

          {selectedWorkItem && (
            <React.Fragment>
              {renderSelectedCard()}
              <Divider style={{ borderBottomWidth: '3px', margin: '16px 0' }} />
            </React.Fragment>
          )}

          {renderWorkItemsGrouped(!!selectedWorkItem)}
        </div>
      </div>
      {contextMenu && (
        <div
          style={{
            position: 'fixed',
            top: contextMenu.y,
            left: contextMenu.x,
            zIndex: 9999,
            backgroundColor: '#fff',
            border: '1px solid var(--pf-v5-global--BorderColor--100, #d2d2d2)',
            borderRadius: '6px',
            boxShadow: '0 4px 16px rgba(0, 0, 0, 0.12)',
            maxHeight: '320px',
            overflowY: 'auto',
            minWidth: '240px',
            maxWidth: '400px'
          }}
          onClick={(e) => e.stopPropagation()}
        >
          <div
            style={{
              padding: '6px 12px',
              fontWeight: 600,
              fontSize: '0.75rem',
              color: 'var(--pf-v5-global--Color--200, #6a6e73)',
              textTransform: 'uppercase',
              letterSpacing: '0.5px',
              borderBottom: '1px solid var(--pf-v5-global--BorderColor--100, #d2d2d2)'
            }}
          >
            Mapped Work Items
          </div>
          {contextMenu.items.map((item, idx) => (
            <div
              key={idx}
              role='menuitem'
              tabIndex={0}
              style={{
                padding: '8px 12px',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                fontSize: 'var(--pf-v5-global--FontSize--sm, 0.875rem)',
                borderBottom: idx < contextMenu.items.length - 1 ? '1px solid var(--pf-v5-global--BorderColor--100, #d2d2d2)' : 'none'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.backgroundColor = 'var(--pf-v5-global--BackgroundColor--200, #f0f0f0)'
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.backgroundColor = '#fff'
              }}
              onClick={(e) => {
                e.stopPropagation()
                handleWorkItemClick(e as any, item.group, item.type)
                setContextMenu(null)
              }}
            >
              <Icon iconSize='sm'>{item.icon}</Icon>
              <span>{item.label}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export { MappingDynamicViewTable }
