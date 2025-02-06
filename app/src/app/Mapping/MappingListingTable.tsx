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
import ReactMarkdown from 'react-markdown'
import { DocumentMenuKebab } from './Menu/DocumentMenuKebab'
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
import FileIcon from '@patternfly/react-icons/dist/esm/icons/file-icon'
import TaskIcon from '@patternfly/react-icons/dist/esm/icons/task-icon'
import BalanceScaleIcon from '@patternfly/react-icons/dist/esm/icons/balance-scale-icon'
import MigrationIcon from '@patternfly/react-icons/dist/esm/icons/migration-icon'
import { useAuth } from '../User/AuthProvider'

export interface MappingListingTableProps {
  api
  mappingData
  unmappingData
  setDocModalInfo
  setTsModalInfo
  setTcModalInfo
  setSrModalInfo
  setJModalInfo
  srModalShowState
  //tsModalShowState
  //setTsModalShowState
  //tcModalShowState
  //setTcModalShowState
  //testRunModalShowState
  //setTestRunModalShowState
  //testResultModalShowState
  //setTestResultModalShowState
  //jModalShowState
  setCommentModalInfo
  setDeleteModalInfo
  setDetailsModalInfo
  setForkModalInfo
  setHistoryModalInfo
  setTestResultsModalInfo
  setTestRunModalInfo
  setUsageModalInfo
  mappingViewSelectValue
  showIndirectTestCases
  showIndirectTestSpecifications
}

const MappingListingTable: React.FunctionComponent<MappingListingTableProps> = ({
  api,
  mappingData = [],
  unmappingData = [],
  setDocModalInfo,
  setTsModalInfo,
  setTcModalInfo,
  setSrModalInfo,
  setJModalInfo,
  srModalShowState,
  //tsModalShowState,
  //setTsModalShowState,
  //tcModalShowState,
  //setTcModalShowState,
  //testRunModalShowState,
  //setTestRunModalShowState,
  //testResultModalShowState,
  //setTestResultModalShowState,
  //jModalShowState,
  setCommentModalInfo,
  setDeleteModalInfo,
  setDetailsModalInfo,
  setForkModalInfo,
  setHistoryModalInfo,
  setTestResultsModalInfo,
  setTestRunModalInfo,
  setUsageModalInfo,
  mappingViewSelectValue,
  showIndirectTestCases,
  showIndirectTestSpecifications
}: MappingListingTableProps) => {
  const auth = useAuth()

  const getWorkItemDescription = (_work_item_type) => {
    const work_item_types = [Constants._A, Constants._J, Constants._D, Constants._SR, Constants._TS, Constants._TC]
    const work_item_descriptions = [Constants._A, Constants._J, Constants._D, 'Software Requirement', 'Test Specification', 'Test Case']
    return work_item_descriptions[work_item_types.indexOf(_work_item_type)]
  }

  const columnNames = {
    specification: 'SPECIFICATION',
    work_items: 'WORK ITEMS'
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
    if (work_item_type == Constants._D) {
      return (
        <Flex>
          <FlexItem>
            <Icon iconSize='lg'>
              <FileIcon />
            </Icon>
          </FlexItem>
        </Flex>
      )
    } else if (work_item_type == Constants._J) {
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

  const getStatusLabel = (status) => {
    let label_color = 'orange'
    const status_lc = status.toString().toLowerCase()

    if (status_lc == 'new') {
      label_color = 'grey'
    } else if (status_lc == 'approved') {
      label_color = 'green'
    } else if (status_lc == 'rejected') {
      label_color = 'red'
    }

    return (
      <React.Fragment>
        <FlexItem>
          <Label
            color={
              // eslint-disable-next-line  @typescript-eslint/no-explicit-any
              label_color as any
            }
            name='label-status'
            isCompact
          >
            {status.toLowerCase()}
          </Label>
        </FlexItem>
      </React.Fragment>
    )
  }

  const isValidRemoteDocument = (_id) => {
    if (!auth.isLogged()) {
      return false
    }

    const valid_class = 'pf-m-green'
    const unvalid_class = 'pf-m-red'

    let url = Constants.API_BASE_URL + '/remote-documents?id=' + _id
    url += '&api-id=' + api.id
    url += '&user-id=' + auth.userId + '&token=' + auth.token

    fetch(url)
      .then((res) => res.json())
      .then((data) => {
        if ('valid' in data) {
          const label = document.getElementById('label-document-valid-' + _id)
          if (label) {
            if (label.classList.contains(valid_class)) {
              label.classList.remove(valid_class)
            }
            if (label.classList.contains(unvalid_class)) {
              label.classList.remove(unvalid_class)
            }
            if (data['valid']) {
              label.classList.add('pf-m-green')
              label.innerHTML = 'yes'
            } else {
              label.classList.add('pf-m-red')
              label.innerHTML = 'no'
            }
          }
        }
      })
      .catch((err) => {
        console.log(err.message)
        return false
      })
      return true
  }

  const getTestCases = (section, offset, test_cases, indirect, parent_type, parent_related_to_type) => {
    if (indirect == false) {
      if (mappingViewSelectValue != Constants._TCs) {
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
                {getStatusLabel(test_case[Constants._TC_]['status'])}
                <FlexItem>
                  <Label variant='outline' isCompact>
                    {coverageFormat(test_case['coverage'])}% Coverage
                  </Label>
                </FlexItem>
                <FlexItem align={{ default: 'alignRight' }}>
                  {indirect == false && auth.isLogged() ? (
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
                    setTestRunModalInfo={setTestRunModalInfo}
                    setTestResultsModalInfo={setTestResultsModalInfo}
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
                    <Text component={TextVariants.h5}>{Constants.getLimitedText(test_case[Constants._TC_]['title'], 0)}</Text>
                    <Text className='work-item-detail-text'>
                      <ReactMarkdown>{Constants.getLimitedText(test_case[Constants._TC_]['description'], 0)}</ReactMarkdown>
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
                {getStatusLabel(test_spec[Constants._TS_]['status'])}
                <FlexItem>
                  <Label variant='outline' isCompact>
                    {coverageFormat(test_spec['coverage'])}% Coverage
                  </Label>
                </FlexItem>
                {test_spec['gap'] != 0 ? (
                  <React.Fragment>
                    <FlexItem>
                      <Label color='red' name='label-test-specification-coverage' variant='outline' isCompact>
                        {coverageFormat(test_spec['gap'])}% Gap
                      </Label>
                    </FlexItem>
                  </React.Fragment>
                ) : (
                  ''
                )}
                <FlexItem align={{ default: 'alignRight' }}>
                  {indirect == false && auth.isLogged() ? (
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
                    <Text component={TextVariants.h5}>{Constants.getLimitedText(test_spec[Constants._TS_]['title'], 0)}</Text>
                    <Text component={TextVariants.h6}>Preconditions:</Text>
                    <Text className='work-item-detail-text'>
                      <ReactMarkdown>{Constants.getLimitedText(test_spec[Constants._TS_]['preconditions'], 0)}</ReactMarkdown>
                    </Text>
                    <Text component={TextVariants.h6}>Test Description:</Text>
                    <Text className='work-item-detail-text'>
                      <ReactMarkdown>{Constants.getLimitedText(test_spec[Constants._TS_]['test_description'], 0)}</ReactMarkdown>
                    </Text>
                    <Text component={TextVariants.h6}>Expected Behavior:</Text>
                    <Text className='work-item-detail-text'>
                      <ReactMarkdown>{Constants.getLimitedText(test_spec[Constants._TS_]['expected_behavior'], 0)}</ReactMarkdown>
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
                {getStatusLabel(mappedItem[Constants._SR_]['status'])}
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
                  {indirect == false && auth.isLogged() ? (
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
                    <Text component={TextVariants.h5}>{Constants.getLimitedText(mappedItem[Constants._SR_]['title'], 0)}</Text>
                    <Text className='work-item-detail-text'>
                      <ReactMarkdown>{Constants.getLimitedText(mappedItem[Constants._SR_]['description'], 0)}</ReactMarkdown>
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
                {getStatusLabel(mappedItem[Constants._J]['status'])}
                <Label variant='outline' isCompact>
                  {coverageFormat(mappedItem['coverage'])}% Coverage
                </Label>
                {auth.isLogged() ? (
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
                ) : (
                  ''
                )}
              </Flex>
              <Flex>
                <FlexItem>
                  <TextContent>
                    <Text className='work-item-detail-text'>
                      <ReactMarkdown>{Constants.getLimitedText(mappedItem[Constants._J]['description'], 0)}</ReactMarkdown>
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

  const getDocuments = (section, offset, mapping) => {
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
                <FlexItem>{getWorkItemIcon(Constants._D, false)}</FlexItem>
                <FlexItem>
                  <TextContent>
                    <Text component={TextVariants.h2}>Document</Text>
                  </TextContent>
                </FlexItem>
                <FlexItem>
                  <Text component={TextVariants.h6}>ver. {mappedItem['version']}</Text>
                </FlexItem>
                {getStatusLabel(mappedItem[Constants._D]['status'])}
                <Label variant='outline' isCompact>
                  {coverageFormat(mappedItem['coverage'])}% Coverage
                </Label>
                {auth.isLogged() ? (
                  <FlexItem align={{ default: 'alignRight' }}>
                    <Button
                      variant='plain'
                      icon={<OutlinedCommentsIcon />}
                      onClick={() => setCommentModalInfo(true, Constants._D, Constants._A, '', mapping, mIndex)}
                    ></Button>
                    <Badge key={3} screenReaderText='Comments'>
                      {mappedItem[Constants._D]['comment_count']}
                    </Badge>
                    <DocumentMenuKebab
                      setDocModalInfo={setDocModalInfo}
                      setDetailsModalInfo={setDetailsModalInfo}
                      setHistoryModalInfo={setHistoryModalInfo}
                      setUsageModalInfo={setUsageModalInfo}
                      setDeleteModalInfo={setDeleteModalInfo}
                      mappingList={mapping}
                      mappingIndex={mIndex}
                      mappingSection={section}
                      mappingOffset={offset}
                      api={api}
                    />
                  </FlexItem>
                ) : (
                  ''
                )}
              </Flex>
              <Flex>
                <FlexItem>
                  <TextContent>
                    <Text className='work-item-detail-text'>
                      <h3>{mappedItem[Constants._D]['title']}</h3>
                    </Text>
                  </TextContent>
                </FlexItem>
              </Flex>
              <Flex>
                <FlexItem>
                  <TextContent>
                    <Text className='work-item-detail-text'>
                      <ReactMarkdown>{Constants.getLimitedText(mappedItem[Constants._D]['description'], 0)}</ReactMarkdown>
                    </Text>
                  </TextContent>
                </FlexItem>
              </Flex>
              <Flex>
                <FlexItem>
                  <TextContent>
                    <Text className='work-item-detail-document-type'>&nbsp;</Text>
                  </TextContent>
                </FlexItem>
              </Flex>
              {mappedItem[Constants._D]['document_type'] == 'text' ? (
                <Flex>
                  <FlexItem>
                    <b>Valid: </b>{' '}
                    <Label id={`label-document-valid-${mappedItem[Constants._D]['id']}`} isCompact>
                      {isValidRemoteDocument(mappedItem[Constants._D]['id']) ? '' : ''}
                    </Label>
                  </FlexItem>
                </Flex>
              ) : (
                ''
              )}
              <Flex>
                <FlexItem>
                  <TextContent>
                    <Text className='work-item-detail-document-type'>
                      <b>Type:</b> {mappedItem[Constants._D]['document_type']}
                    </Text>
                  </TextContent>
                </FlexItem>
              </Flex>
              <Flex>
                <FlexItem>
                  <TextContent>
                    <Text className='work-item-detail-document-url'>
                      <b>Url:</b>{' '}
                      <a target='_blank' rel='noopener noreferrer' href={mappedItem[Constants._D]['url']}>
                        {mappedItem[Constants._D]['url']}
                      </a>
                    </Text>
                  </TextContent>
                </FlexItem>
              </Flex>
              <Flex>
                <FlexItem>
                  <TextContent>
                    <Text className='work-item-detail-spdx-relation'>
                      <b>SPDX Relation:</b> {mappedItem[Constants._D]['spdx_relation']}
                    </Text>
                  </TextContent>
                </FlexItem>
              </Flex>
              {mappedItem[Constants._D]['document_type'] == 'text' ? (
                <>
                  <Flex>
                    <FlexItem>
                      <TextContent>
                        <Text className='work-item-detail-document-offset'>
                          <b>Offset:</b> {Constants.getLimitedText(mappedItem[Constants._D]['offset'], 0)}
                        </Text>
                      </TextContent>
                    </FlexItem>
                  </Flex>
                  <Flex>
                    <FlexItem>
                      <TextContent>
                        <Text className='work-item-detail-document-section'>
                          <b>Section:</b>
                        </Text>
                      </TextContent>
                    </FlexItem>
                  </Flex>
                  <Flex>
                    <FlexItem>
                      <CodeBlock>
                        <CodeBlockCode>{Constants.getLimitedText(mappedItem[Constants._D]['section'], 0)}</CodeBlockCode>
                      </CodeBlock>
                    </FlexItem>
                  </Flex>
                </>
              ) : (
                ''
              )}
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
    } else if (Object.prototype.hasOwnProperty.call(snippet, 'document')) {
      work_item_type = Constants._D
      work_item_description = snippet[Constants._D]['title']
      work_item_id = snippet[Constants._D]['id']
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
                  setDocModalInfo={setDocModalInfo}
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
                  <Text component={TextVariants.h5}>
                    <ReactMarkdown>{Constants.getLimitedText(work_item_description, 0)}</ReactMarkdown>
                  </Text>
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
                    {api?.permissions?.indexOf('w') >= 0 ? (
                      <MappingSectionMenuKebab
                        api={api}
                        offset={snippet['offset']}
                        section={snippet['section']}
                        sectionIndex={snippetIndex}
                        setDocModalInfo={setDocModalInfo}
                        setTcModalInfo={setTcModalInfo}
                        setTsModalInfo={setTsModalInfo}
                        setSrModalInfo={setSrModalInfo}
                        setJModalInfo={setJModalInfo}
                      />
                    ) : (
                      ''
                    )}
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
              snippet[mappingViewSelectValue ? mappingViewSelectValue.replaceAll('-', '_') : Constants.DEFAULT_VIEW],
              false,
              Constants._A,
              ''
            )}
            {getTestSpecifications(
              snippet['section'],
              snippet['offset'],
              snippet[mappingViewSelectValue ? mappingViewSelectValue.replaceAll('-', '_') : Constants.DEFAULT_VIEW],
              false,
              Constants._A,
              ''
            )}
            {getTestCases(
              snippet['section'],
              snippet['offset'],
              snippet[mappingViewSelectValue ? mappingViewSelectValue.replaceAll('-', '_') : Constants.DEFAULT_VIEW],
              false,
              Constants._A,
              ''
            )}
            {getJustifications(snippet['section'], snippet['offset'], snippet[Constants._Js])}
            {getDocuments(snippet['section'], snippet['offset'], snippet[Constants._Ds])}
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
