import * as React from 'react'
import * as Constants from '../Constants/constants'
import { Table, Tbody, Td, Th, Thead, Tr } from '@patternfly/react-table'
import {
  Badge,
  Button,
  Card,
  CardBody,
  CodeBlock,
  CodeBlockCode,
  Divider,
  Flex,
  FlexItem,
  Icon,
  Label,
  PageSection,
  Text,
  TextContent,
  TextVariants
} from '@patternfly/react-core'
import { MappingSectionMenuKebab } from './Menu/MappingSectionMenuKebab'
import { SwRequirementMenuKebab } from './Menu/SwRequirementMenuKebab'
import { TestSpecificationMenuKebab } from './Menu/TestSpecificationMenuKebab'
import { TestCaseMenuKebab } from './Menu/TestCaseMenuKebab'
import { JustificationMenuKebab } from './Menu/JustificationMenuKebab'
import { UnmappedMenuKebab } from './Menu/UnmappedMenuKebab'
import { LeavesProgressBar } from '../Custom/LeavesProgressBar'
import OutlinedCommentsIcon from '@patternfly/react-icons/dist/esm/icons/outlined-comments-icon'
import CodeIcon from '@patternfly/react-icons/dist/esm/icons/code-icon'
import CatalogIcon from '@patternfly/react-icons/dist/esm/icons/catalog-icon'
import TaskIcon from '@patternfly/react-icons/dist/esm/icons/task-icon'
import BalanceScaleIcon from '@patternfly/react-icons/dist/esm/icons/balance-scale-icon'
import MigrationIcon from '@patternfly/react-icons/dist/esm/icons/migration-icon'
import { useAuth } from '@app/User/AuthProvider'

export interface MappingListingTableProps {
  api
  mappingData
  unmappingData
  setTsModalInfo
  setTcModalInfo
  setSrModalInfo
  setJModalInfo
  srModalShowState
  tsModalShowState
  setTsModalShowState
  tcModalShowState
  setTcModalShowState
  jModalShowState
  setCommentModalInfo
  setDeleteModalInfo
  setDetailsModalInfo
  setForkModalInfo
  setHistoryModalInfo
  setUsageModalInfo
  mappingViewSelectValue
  showIndirectTestCases
  showIndirectTestSpecifications
}

const MappingListingTable: React.FunctionComponent<MappingListingTableProps> = ({
  api,
  mappingData = [],
  unmappingData = [],
  setTsModalInfo,
  setTcModalInfo,
  setSrModalInfo,
  setJModalInfo,
  srModalShowState,
  tsModalShowState,
  setTsModalShowState,
  tcModalShowState,
  setTcModalShowState,
  jModalShowState,
  setCommentModalInfo,
  setDeleteModalInfo,
  setDetailsModalInfo,
  setForkModalInfo,
  setHistoryModalInfo,
  setUsageModalInfo,
  mappingViewSelectValue,
  showIndirectTestCases,
  showIndirectTestSpecifications
}: MappingListingTableProps) => {
  let auth = useAuth();

  const getWorkItemDescription = (_work_item_type) => {
    const work_item_types = [Constants._A, Constants._J, Constants._SR, Constants._TS, Constants._TC]
    const work_item_descriptions = [Constants._A, Constants._J, 'Software Requirement', 'Test Specification', 'Test Case']
    return work_item_descriptions[work_item_types.indexOf(_work_item_type)]
  }

  const columnNames = {
    specification: 'SPECIFICATION',
    work_items: 'WORK ITEMS'
  }

  const getLimitedText = (_text, _length) => {
    if (_text == undefined) {
      return ''
    }
    let tmp = _text.substr(0, _length)
    if (_text.length > _length) {
      tmp = tmp + '...'
    }
    return tmp
  }

  const coverageFormat = (x) => Number.parseFloat(x).toFixed(1)

  const getMappedSectionCodeBlockBackgroundColor = (snippet) => {
    const j_l = snippet[Constants._Js].length
    const sr_l = snippet[Constants._SRs_].length
    const ts_l = snippet[Constants._TSs_].length
    const tc_l = snippet[Constants._TCs_].length

    if (j_l > 0 && sr_l == 0 && ts_l == 0 && tc_l == 0) {
      return 'code-block-bg-gold'
    } else if (j_l == 0 && sr_l == 0 && ts_l == 0 && tc_l == 0) {
      return 'code-block-bg-gray'
    } else {
      return 'code-block-bg-green'
    }
  }

  const getWorkItemIcon = (work_item_type, indirect) => {
    if (work_item_type == Constants._J) {
      return (
        <Flex>
          <FlexItem>
            <Icon iconSize='lg'>
              <BalanceScaleIcon />
            </Icon>
          </FlexItem>
        </Flex>
      )
    } else if (work_item_type == Constants._SR) {
      return (
        <Flex>
          <FlexItem>
            <Icon iconSize='lg'>
              <CatalogIcon />
            </Icon>
          </FlexItem>
        </Flex>
      )
    } else if (work_item_type == Constants._TS) {
      if (indirect == 1) {
        return (
          <Flex>
            <FlexItem>
              <Icon iconSize='sm'>
                <MigrationIcon />
              </Icon>{' '}
              &nbsp;
              <Icon iconSize='lg'>
                <TaskIcon />
              </Icon>
            </FlexItem>
          </Flex>
        )
      } else {
        return (
          <Flex>
            <FlexItem>
              <Icon iconSize='lg'>
                <TaskIcon />
              </Icon>
            </FlexItem>
          </Flex>
        )
      }
    } else if (work_item_type == Constants._TC) {
      if (indirect == 1) {
        return (
          <Flex>
            <FlexItem>
              <Icon iconSize='sm'>
                <MigrationIcon />
              </Icon>{' '}
              &nbsp;
              <Icon iconSize='lg'>
                <CodeIcon />
              </Icon>
            </FlexItem>
          </Flex>
        )
      } else {
        return (
          <Flex>
            <FlexItem>
              <Icon iconSize='lg'>
                <CodeIcon />
              </Icon>
            </FlexItem>
          </Flex>
        )
      }
    } else {
      return ''
    }
  }

  const getTestCases = (section, offset, test_cases, indirect, parent_type, parent_related_to_type) => {
    if (indirect == false) {
      if (mappingViewSelectValue != 'test-cases') {
        return ''
      }
    } else {
      if (showIndirectTestCases == false) {
        return ''
      }
    }
    if (test_cases == undefined) {
      return ''
    }
    if (test_cases.length == 0) {
      return ''
    } else {
      return test_cases.map((test_case, cIndex) => (
        <React.Fragment key={cIndex}>
          <Card>
            {' '}
            <CardBody>
              <Flex>
                <FlexItem>{getWorkItemIcon(Constants._TC, indirect)}</FlexItem>
                <FlexItem>
                  <TextContent>
                    <Text component={TextVariants.h2}>Test Case {test_case[Constants._TC_]['id']}</Text>
                  </TextContent>
                </FlexItem>
                <FlexItem>
                  <Text component={TextVariants.h6}>ver. {test_case['version']}</Text>
                </FlexItem>
                <FlexItem>
                  <Label variant='outline' isCompact>
                    {coverageFormat(test_case['coverage'])}% Coverage
                  </Label>
                </FlexItem>
                <FlexItem align={{ default: 'alignRight' }}>
                  {indirect == false && auth.isGuest() == false ? (
                    <React.Fragment>
                      <Button
                        variant='plain'
                        icon={<OutlinedCommentsIcon />}
                        onClick={() => setCommentModalInfo(true, Constants._TC, Constants._A, '', test_cases, cIndex)}
                      ></Button>
                      <Badge key={3} screenReaderText='Comments'>
                        {test_case[Constants._TC_]['comment_count']}
                      </Badge>
                    </React.Fragment>
                  ) : (
                    ''
                  )}
                  <TestCaseMenuKebab
                    indirect={indirect}
                    setDetailsModalInfo={setDetailsModalInfo}
                    setHistoryModalInfo={setHistoryModalInfo}
                    setUsageModalInfo={setUsageModalInfo}
                    setTcModalInfo={setTcModalInfo}
                    setDeleteModalInfo={setDeleteModalInfo}
                    mappingParentType={parent_type}
                    mappingParentRelatedToType={parent_related_to_type}
                    mappingIndex={cIndex}
                    mappingList={test_cases}
                    mappingSection={section}
                    mappingOffset={offset}
                    api={api}
                    //setTcModalShowState={setTcModalShowState}
                    //mappingType={Constants._TC}
                    //tcModalShowState={tcModalShowState}
                  />
                </FlexItem>
              </Flex>
              <Flex>
                <FlexItem>
                  <TextContent>
                    <Text component={TextVariants.h5}>{getLimitedText(test_case[Constants._TC_]['title'], 100)}</Text>
                    <Text component={TextVariants.p} className='work-item-detail-text'>
                      {getLimitedText(test_case[Constants._TC_]['description'], 200)}
                    </Text>
                  </TextContent>
                </FlexItem>
              </Flex>
            </CardBody>
          </Card>
          <Divider />
        </React.Fragment>
      ))
    }
  }

  const getTestSpecifications = (section, offset, test_specs, indirect, parent_type, parent_related_to_type) => {
    if (indirect == false) {
      if (mappingViewSelectValue != Constants._TSs) {
        return ''
      }
    } else {
      if (showIndirectTestSpecifications == false) {
        return ''
      }
    }
    if (test_specs == undefined) {
      return ''
    }
    if (test_specs.length == 0) {
      return ''
    } else {
      return test_specs.map((test_spec, cIndex) => (
        <React.Fragment key={cIndex}>
          <Card>
            {' '}
            <CardBody>
              <Flex>
                <FlexItem>{getWorkItemIcon(Constants._TS, indirect)}</FlexItem>
                <FlexItem>
                  <TextContent>
                    <Text component={TextVariants.h2}>Test Specification {test_spec[Constants._TS_]['id']}</Text>
                  </TextContent>
                </FlexItem>
                <FlexItem>
                  <Text component={TextVariants.h6}>ver. {test_spec['version']}</Text>
                </FlexItem>
                <FlexItem>
                  <Label variant='outline' isCompact>
                    {coverageFormat(test_spec['coverage'])}% Coverage
                  </Label>
                </FlexItem>
                {test_spec['gap'] != 0 ? (
                  <React.Fragment>
                    <FlexItem>
                      <Label color='red' name='label-sw-requirement-coverage' variant='outline' isCompact>
                        {coverageFormat(test_spec['gap'])}% Gap
                      </Label>
                    </FlexItem>
                  </React.Fragment>
                ) : (
                  ''
                )}
                <FlexItem align={{ default: 'alignRight' }}>
                  {indirect == false && auth.isGuest() == false ? (
                    <React.Fragment>
                      <Button
                        variant='plain'
                        icon={<OutlinedCommentsIcon />}
                        onClick={() => setCommentModalInfo(true, 'test-specification', Constants._A, '', test_specs, cIndex)}
                      ></Button>
                      <Badge key={3} screenReaderText='Comments'>
                        {test_spec[Constants._TS_]['comment_count']}
                      </Badge>
                    </React.Fragment>
                  ) : (
                    ''
                  )}
                  <TestSpecificationMenuKebab
                    indirect={indirect}
                    setDetailsModalInfo={setDetailsModalInfo}
                    setHistoryModalInfo={setHistoryModalInfo}
                    setUsageModalInfo={setUsageModalInfo}
                    setTcModalInfo={setTcModalInfo}
                    setTsModalInfo={setTsModalInfo}
                    setDeleteModalInfo={setDeleteModalInfo}
                    mappingParentType={parent_type}
                    mappingParentRelatedToType={parent_related_to_type}
                    mappingIndex={cIndex}
                    mappingList={test_specs}
                    mappingSection={section}
                    mappingOffset={offset}
                    api={api}
                    //setTcModalShowState={setTcModalShowState}
                    //setTsModalShowState={setTsModalShowState}
                    //mappingType={'test-specification'}
                    //tsModalShowState={tsModalShowState}
                    //tcModalShowState={tcModalShowState}
                  />
                </FlexItem>
              </Flex>
              <Flex>
                <FlexItem>
                  <TextContent>
                    <Text component={TextVariants.h5}>{getLimitedText(test_spec[Constants._TS_]['title'], 100)}</Text>
                    <Text component={TextVariants.p} className='work-item-detail-text'>
                      {getLimitedText(test_spec[Constants._TS_]['test_description'], 200)}
                    </Text>
                  </TextContent>
                </FlexItem>
              </Flex>
            </CardBody>
            <CardBody>
              {getTestCases(section, offset, test_spec[Constants._TS_][Constants._TCs_], true, 'test-specification', parent_type)}
            </CardBody>
          </Card>
          <Divider />
        </React.Fragment>
      ))
    }
  }

  const getSwRequirements = (section, offset, mapping, indirect, parent_type, parent_related_to_type) => {
    if (mappingViewSelectValue != Constants._SRs) {
      return ''
    }
    if (mapping == undefined) {
      return ''
    }
    if (mapping.length == 0) {
      return ''
    } else {
      return mapping.map((mappedItem, mIndex) => (
        <React.Fragment key={mIndex}>
          <Card>
            <CardBody>
              <Flex>
                <FlexItem>{getWorkItemIcon(Constants._SR, false)}</FlexItem>
                <FlexItem>
                  <TextContent>
                    <Text component={TextVariants.h2}>Software Requirement {mappedItem[Constants._SR_]['id']}</Text>
                  </TextContent>
                </FlexItem>
                <FlexItem>
                  <Text component={TextVariants.h6}>ver. {mappedItem['version']}</Text>
                </FlexItem>
                <FlexItem>
                  <Label name='label-sw-requirement-coverage' variant='outline' isCompact>
                    {coverageFormat(mappedItem['coverage'])}% Coverage
                  </Label>
                </FlexItem>
                {mappedItem['gap'] != 0 ? (
                  <React.Fragment>
                    <FlexItem>
                      <Label color='red' name='label-sw-requirement-coverage' variant='outline' isCompact>
                        {coverageFormat(mappedItem['gap'])}% Gap
                      </Label>
                    </FlexItem>
                  </React.Fragment>
                ) : (
                  ''
                )}
                <FlexItem align={{ default: 'alignRight' }}>
                  {indirect == false && auth.isGuest() == false ? (
                    <React.Fragment>
                      <Button
                        variant='plain'
                        icon={<OutlinedCommentsIcon />}
                        onClick={() => setCommentModalInfo(true, Constants._SR, Constants._A, '', mapping, mIndex)}
                      ></Button>
                      <Badge key={3} screenReaderText='Comments'>
                        {mappedItem[Constants._SR_]['comment_count']}
                      </Badge>
                    </React.Fragment>
                  ) : (
                    ''
                  )}
                  <SwRequirementMenuKebab
                    setDetailsModalInfo={setDetailsModalInfo}
                    setHistoryModalInfo={setHistoryModalInfo}
                    setUsageModalInfo={setUsageModalInfo}
                    setSrModalInfo={setSrModalInfo}
                    setTsModalInfo={setTsModalInfo}
                    setTcModalInfo={setTcModalInfo}
                    setDeleteModalInfo={setDeleteModalInfo}
                    setForkModalInfo={setForkModalInfo}
                    api={api}
                    indirect={indirect}
                    mappingParentType={parent_type}
                    mappingParentRelatedToType={parent_related_to_type}
                    mappingList={mapping}
                    mappingIndex={mIndex}
                    mappingSection={section}
                    mappingOffset={offset}
                    //tsModalShowState={tsModalShowState}
                    //setTsModalShowState={setTsModalShowState}
                    //tcModalShowState={tcModalShowState}
                    //mappingType={Constants._SR}
                  />
                </FlexItem>
              </Flex>
              <Flex>
                <FlexItem>
                  <TextContent>
                    <Text component={TextVariants.h5}>{getLimitedText(mappedItem[Constants._SR_]['title'], 100)}</Text>
                    <Text component={TextVariants.p} className='work-item-detail-text'>
                      {getLimitedText(mappedItem[Constants._SR_]['description'], 200)}
                    </Text>
                  </TextContent>
                </FlexItem>
              </Flex>
            </CardBody>
            <CardBody>
              {getSwRequirements(section, offset, mappedItem[Constants._SRs_], true, Constants._SR, parent_type)}
              {getTestSpecifications(section, offset, mappedItem[Constants._TSs_], true, Constants._SR, parent_type)}
              {getTestCases(section, offset, mappedItem[Constants._TCs_], true, Constants._SR, parent_type)}
            </CardBody>
          </Card>
          <Divider />
        </React.Fragment>
      ))
    }
  }

  const getJustifications = (section, offset, mapping) => {
    if (mapping == undefined) {
      return ''
    }
    if (mapping.length == 0) {
      return ''
    } else {
      return mapping.map((mappedItem, mIndex) => (
        <React.Fragment key={mIndex}>
          <Card>
            <CardBody>
              <Flex>
                <FlexItem>{getWorkItemIcon(Constants._J, false)}</FlexItem>
                <FlexItem>
                  <TextContent>
                    <Text component={TextVariants.h2}>Justification</Text>
                  </TextContent>
                </FlexItem>
                <FlexItem>
                  <Text component={TextVariants.h6}>ver. {mappedItem['version']}</Text>
                </FlexItem>
                <Label variant='outline' isCompact>
                  {coverageFormat(mappedItem['coverage'])}% Coverage
                </Label>
                {auth.isGuest() == false ? (
                <FlexItem align={{ default: 'alignRight' }}>
                  <Button
                    variant='plain'
                    icon={<OutlinedCommentsIcon />}
                    onClick={() => setCommentModalInfo(true, Constants._J, Constants._A, '', mapping, mIndex)}
                  ></Button>
                  <Badge key={3} screenReaderText='Comments'>
                    {mappedItem[Constants._J]['comment_count']}
                  </Badge>
                  <JustificationMenuKebab
                    setJModalInfo={setJModalInfo}
                    setDetailsModalInfo={setDetailsModalInfo}
                    setHistoryModalInfo={setHistoryModalInfo}
                    setUsageModalInfo={setUsageModalInfo}
                    setDeleteModalInfo={setDeleteModalInfo}
                    mappingList={mapping}
                    mappingIndex={mIndex}
                    mappingSection={section}
                    mappingOffset={offset}
                    api={api}
                    //jModalShowState={jModalShowState}
                  />
                </FlexItem>
              ) : ('')}
              </Flex>
              <Flex>
                <FlexItem>
                  <TextContent>
                    <Text component={TextVariants.h5} className='work-item-detail-text'>
                      {getLimitedText(mappedItem[Constants._J]['description'], 100)}
                    </Text>
                  </TextContent>
                </FlexItem>
              </Flex>
            </CardBody>
          </Card>
          <Divider />
        </React.Fragment>
      ))
    }
  }

  const getUnmapped = (snippet) => {
    let work_item_id = ''
    let work_item_type = ''
    let work_item_description = ''

    if (Object.prototype.hasOwnProperty.call(snippet, 'justification')) {
      work_item_type = Constants._J
      work_item_description = snippet[Constants._J]['description']
      work_item_id = snippet[Constants._J]['id']
    } else if (Object.prototype.hasOwnProperty.call(snippet, 'sw_requirement')) {
      work_item_type = Constants._SR
      work_item_description = snippet[Constants._SR_]['title']
      work_item_id = snippet[Constants._SR_]['id']
    } else if (Object.prototype.hasOwnProperty.call(snippet, 'test_specification')) {
      work_item_type = 'test-specification'
      work_item_description = snippet[Constants._TS_]['title']
      work_item_id = snippet[Constants._TS_]['id']
    } else if (Object.prototype.hasOwnProperty.call(snippet, 'test_case')) {
      work_item_type = Constants._TC
      work_item_description = snippet[Constants._TC_]['title']
      work_item_id = snippet[Constants._TC_]['id']
    }

    return (
      <React.Fragment>
        <Card>
          <CardBody>
            <Flex>
              <FlexItem>{getWorkItemIcon(work_item_type, false)}</FlexItem>
              <FlexItem>
                <TextContent>
                  <Text component={TextVariants.h2}>
                    {getWorkItemDescription(work_item_type)} {work_item_id}
                  </Text>
                </TextContent>
              </FlexItem>
              <FlexItem>
                <Text component={TextVariants.h6}>ver. {snippet['version']}</Text>
              </FlexItem>
              <Label variant='outline' isCompact>
                {coverageFormat(snippet['coverage'])}% Coverage
              </Label>
              <FlexItem align={{ default: 'alignRight' }}>
                <UnmappedMenuKebab
                  api={api}
                  srModalShowState={srModalShowState}
                  setDeleteModalInfo={setDeleteModalInfo}
                  setTcModalInfo={setTcModalInfo}
                  setTsModalInfo={setTsModalInfo}
                  setSrModalInfo={setSrModalInfo}
                  setJModalInfo={setJModalInfo}
                  mappingType={work_item_type}
                  mappingParentType='api'
                  mappingIndex={0}
                  mappingList={[snippet]}
                  mappingSection={snippet['section']}
                  mappingOffset={snippet['offset']}
                  //jModalShowState={jModalShowState}
                  //tcModalShowState={tcModalShowState}
                  //tsModalShowState={tsModalShowState}
                />
              </FlexItem>
            </Flex>
            <Flex>
              <FlexItem>
                <TextContent>
                  <Text component={TextVariants.h5}>{getLimitedText(work_item_description, 100)}</Text>
                </TextContent>
              </FlexItem>
            </Flex>
          </CardBody>
        </Card>
        <Divider />
      </React.Fragment>
    )
  }

  const getMappingTable = () => {
    if (mappingData == undefined) {
      return ''
    }
    if (mappingData.length == 0) {
      return ''
    } else {
      return mappingData.map((snippet, snippetIndex) => (
        <Tr className='row-bottom-sep' key={snippetIndex}>
          <Td width={50} dataLabel={columnNames.specification}>
            <Card>
              <CardBody>
                <Flex>
                  <FlexItem align={{ default: 'alignLeft' }}>Coverage Total:</FlexItem>
                  <FlexItem align={{ default: 'alignLeft' }}>
                    <LeavesProgressBar progressValue={snippet['covered']} progressId={'mapping-section-coverage-' + snippetIndex} />
                  </FlexItem>
                  <FlexItem align={{ default: 'alignRight' }}>
                    { api?.permissions?.indexOf('w') >= 0 ? (
                    <MappingSectionMenuKebab
                      api={api}
                      offset={snippet['offset']}
                      section={snippet['section']}
                      sectionIndex={snippetIndex}
                      setTcModalInfo={setTcModalInfo}
                      setTsModalInfo={setTsModalInfo}
                      setSrModalInfo={setSrModalInfo}
                      setJModalInfo={setJModalInfo}/>
                  ) : ('') }
                  </FlexItem>
                </Flex>
              </CardBody>
            </Card>
            <Divider />
            <CodeBlock className={getMappedSectionCodeBlockBackgroundColor(snippet) + ' full-height'}>
              <CodeBlockCode>
                <div id={'snippet-' + snippetIndex} data-offset={snippet['offset']}>
                  {snippet['section']}
                </div>
              </CodeBlockCode>
            </CodeBlock>
          </Td>
          <Td width={50} dataLabel={columnNames.work_items}>
            {getSwRequirements(
              snippet['section'],
              snippet['offset'],
              snippet[mappingViewSelectValue.replaceAll('-', '_')],
              false,
              Constants._A,
              ''
            )}
            {getTestSpecifications(
              snippet['section'],
              snippet['offset'],
              snippet[mappingViewSelectValue.replaceAll('-', '_')],
              false,
              Constants._A,
              ''
            )}
            {getTestCases(
              snippet['section'],
              snippet['offset'],
              snippet[mappingViewSelectValue.replaceAll('-', '_')],
              false,
              Constants._A,
              ''
            )}
            {getJustifications(snippet['section'], snippet['offset'], snippet[Constants._Js])}
            {/*getSpecifications*/}
          </Td>
        </Tr>
      ))
    }
  }

  const getUnmappingTable = () => {
    if (unmappingData.length == 0) {
      return ''
    } else {
      return unmappingData.map((snippet, snippetIndex) => (
        <Tr key={snippetIndex}>
          <Td width={50} dataLabel={columnNames.specification}>
            <Card>
              <CardBody>
                <Flex>
                  <FlexItem align={{ default: 'alignLeft' }}>
                    Coverage Total:
                    <LeavesProgressBar progressValue={snippet['coverage']} progressId={'unmapping-section-coverage-' + snippetIndex} />
                  </FlexItem>
                </Flex>
              </CardBody>
            </Card>
            <Divider />
            <CodeBlock className='code-block-bg-red'>
              <CodeBlockCode>
                <div id={'snippet-' + snippetIndex} data-offset={snippet['offset']}>
                  {snippet['section']}
                </div>
              </CodeBlockCode>
            </CodeBlock>
          </Td>
          <Td width={50} dataLabel={columnNames.work_items}>
            {getUnmapped(snippet)}
          </Td>
        </Tr>
      ))
    }
  }

  return (
    <React.Fragment>
      <PageSection>
        <Table id='table-matching-sections'>
          <Thead>
            <Tr>
              <Th>{columnNames.specification}</Th>
              <Th>{columnNames.work_items}</Th>
            </Tr>
          </Thead>
          <Tbody key={1}>{getMappingTable()}</Tbody>
        </Table>
      </PageSection>

      <PageSection>
        <Table id='table-unmatching-sections'>
          <Thead>
            <Tr>
              <Th>{columnNames.specification}</Th>
              <Th>UNMATCHING {columnNames.work_items}</Th>
            </Tr>
          </Thead>
          <Tbody key={2}>{getUnmappingTable()}</Tbody>
        </Table>
      </PageSection>
    </React.Fragment>
  )
}

export { MappingListingTable }
