import * as React from 'react';
import { ExpandableRowContent, Table, Tbody, Td, Th, Thead, Tr } from '@patternfly/react-table';
import { ActionGroup, Button, Flex, FlexItem, PageSection } from '@patternfly/react-core';
import { PageSection, Divider } from '@patternfly/react-core';
import { TextContent, Text, TextVariants } from '@patternfly/react-core';
import { Badge, Label, Card, CardBody } from '@patternfly/react-core';
import { Icon } from '@patternfly/react-core';
import LongArrowAltDownIcon from '@patternfly/react-icons/dist/esm/icons/long-arrow-alt-down-icon';
import {CodeBlock, CodeBlockCode} from '@patternfly/react-core';
import { MappingSectionMenuKebab } from './Menu/MappingSectionMenuKebab';
import { SwRequirementMenuKebab } from './Menu/SwRequirementMenuKebab';
import { TestSpecificationMenuKebab } from './Menu/TestSpecificationMenuKebab';
import { TestCaseMenuKebab } from './Menu/TestCaseMenuKebab';
import { JustificationMenuKebab } from './Menu/JustificationMenuKebab';
import { UnmappedMenuKebab } from './Menu/UnmappedMenuKebab';
import { LeavesProgressBar } from '../Custom/LeavesProgressBar';
import OutlinedCommentsIcon from '@patternfly/react-icons/dist/esm/icons/outlined-comments-icon';
import CodeIcon from '@patternfly/react-icons/dist/esm/icons/code-icon';
import CatalogIcon from '@patternfly/react-icons/dist/esm/icons/catalog-icon';
import TaskIcon from '@patternfly/react-icons/dist/esm/icons/task-icon';
import BalanceScaleIcon from '@patternfly/react-icons/dist/esm/icons/balance-scale-icon';
import MigrationIcon from '@patternfly/react-icons/dist/esm/icons/migration-icon';

interface APIHistoryData {
  versionNumber: number;
  id?: string;
  description?: string;
  notes?: string;
}

interface APIDetailsData {
  url?: string;
  library?: string;
  branch?: string;
  fileMatchCriteria: string;
}

interface DataObject {
  id: string;
  api: string;
  coverage: 0 | 25 | 50 | 75 | 100;
  history: APIHistoryData[];
  details: APIDetailsData;
}

export interface MappingListingTableProps {
  api;
  apiSwRequirement;
  baseApiUrl:string;
  mappingData;
  unmappingData;
  setTsModalInfo;
  setTcModalInfo;
  setSrModalInfo;
  setJModalInfo;
  srModalShowState;
  setSrModalShowState;
  tsModalShowState;
  setTsModalShowState;
  tcModalShowState;
  setTcModalShowState;
  jModalShowState;
  setJModalShowState;
  setCommentModalInfo;
  setDeleteModalInfo;
  setDetailsModalInfo;
  setForkModalInfo;
  setHistoryModalInfo;
  setUsageModalInfo;
  mappingViewSelectValue;
  showIndirectTestCases;
  showIndirectTestSpecifications;
}

const MappingListingTable: React.FunctionComponent<MappingListingTableProps> = ({
  api,
  apiSwRequirement,
  setApiSwRequirement,
  baseApiUrl,
  mappingData=[],
  unmappingData=[],
  setTsModalInfo,
  setTcModalInfo,
  setSrModalInfo,
  setJModalInfo,
  srModalShowState,
  setSrModalShowState,
  tsModalShowState,
  setTsModalShowState,
  tcModalShowState,
  setTcModalShowState,
  jModalShowState,
  setJModalShowState,
  setCommentModalInfo,
  setDeleteModalInfo,
  setDetailsModalInfo,
  setForkModalInfo,
  setHistoryModalInfo,
  setUsageModalInfo,
  mappingViewSelectValue,
  showIndirectTestCases,
  showIndirectTestSpecifications,
}: MappingListingTableProps) => {

  const [expandedRepoNames, setExpandedRepoNames] = React.useState<string[]>([]);
  const setRepoExpanded = (repo: DataObject, isExpanding = true) =>
    setExpandedRepoNames(prevExpanded => {
      const otherExpandedRepoNames = prevExpanded.filter(r => r !== repo.id);
      return isExpanding ? [...otherExpandedRepoNames, repo.id] : otherExpandedRepoNames;
    });
  const isRepoExpanded = (repo: DataObject) => expandedRepoNames.includes(repo.id);
  const [currentApiID, setCurrentApiID] = React.useState(0);
  const [currentApiHistory, setCurrentApiHistory] = React.useState([]);
  const [snippets, setSnippets] = React.useState([]);

  const _A = 'api';
  const _SR = 'sw-requirement';
  const _SR_ = 'sw_requirement';
  const _TS = 'test-specification';
  const _TS_ = 'test_specification';
  const _TC = 'test-case';
  const _TC_ = 'test_case';
  const _J = 'justification';

  const getWorkItemDescription = (_work_item_type) => {
      const work_item_types = [_A, _J, _SR, _TS, _TC];
      const work_item_descriptions = ['Api',
                                      'Justification',
                                      'Software Requirement',
                                      'Test Specification',
                                      'Test Case'];
      return work_item_descriptions[work_item_types.indexOf(_work_item_type)];
  }

  React.useEffect(() => {
    let url = baseApiUrl + '/apis/history?api-id=' + currentApiID;
    fetch(url)
      .then((res) => res.json())
      .then((data) => {
        setCurrentApiHistory(data);
      })
      .catch((err) => {
        console.log(err.message);
      });
  }, [currentApiID]);

  const columnNames = {
    specification: 'SPECIFICATION',
    work_items: 'WORK ITEMS',
  };


  const getHistory = () => {
    if (currentApiHistory.length == 0){
      return "";
    } else {
      return currentApiHistory.map((version, versionIndex) => (
        <React.Fragment key={versionIndex}>
          <Text component={TextVariants.h3}>Version {version.version} - {version.created_at}</Text>
          <TextList>
            {Object.keys(version.object).map((key, index) => (
                <TextListItem key={index}><em>{key}: </em>{version.object[key]}</TextListItem>
            ))}
          </TextList>
        </React.Fragment>
      ));
    }
  }

  const getLimitedText = (_text, _length) => {
    if (_text == undefined){
      return "";
    }
    let tmp = _text.substr(0, _length);
    if (_text.length > _length) {
      tmp = tmp + "...";
    }
    return tmp;
  }

  const coverageFormat = (x) => Number.parseFloat(x).toFixed(1);

  const getMappedSectionCodeBlockBackgroundColor = (snippet) => {
    let j_l = snippet['justifications'].length;
    let sr_l = snippet['sw_requirements'].length;
    let ts_l = snippet['test_specifications'].length;
    let tc_l = snippet['test_cases'].length;

    if ((j_l>0) && (sr_l == 0) && (ts_l == 0) && (tc_l == 0)){
      return "code-block-bg-gold";
    } else {
      return "code-block-bg-green";
    }
  }

  const getWorkItemIcon = (work_item_type, indirect) => {
    if (work_item_type == _J) {
      return <Flex><FlexItem><Icon iconSize='lg'><BalanceScaleIcon /></Icon></FlexItem></Flex>
    } else if (work_item_type == _SR) {
      return <Flex><FlexItem><Icon iconSize='lg'><CatalogIcon /></Icon></FlexItem></Flex>
    } else if (work_item_type == _TS) {
      if (indirect == 1) {
        return (<Flex><FlexItem><Icon iconSize='sm'><MigrationIcon /></Icon> &nbsp;
                <Icon iconSize='lg'><TaskIcon /></Icon></FlexItem></Flex>)
      } else {
        return <Flex><FlexItem><Icon  iconSize='lg'><TaskIcon /></Icon></FlexItem></Flex>
      }
    } else if (work_item_type == _TC) {
      if (indirect == 1) {
        return (<Flex><FlexItem><Icon iconSize='sm'><MigrationIcon /></Icon> &nbsp;
               <Icon iconSize='lg'><CodeIcon /></Icon></FlexItem></Flex>)
      } else {
        return <Flex><FlexItem><Icon iconSize='lg'><CodeIcon /></Icon></FlexItem></Flex>
      }
    }
  }

  const getTestCases = (section, offset, test_cases, indirect, parent_type, parent_related_to_type) => {
    if (indirect == false){
      if (mappingViewSelectValue != 'test-cases'){
        return "";
      }
    } else {
      if (showIndirectTestCases == false){
        return "";
      }
    }
    if (test_cases == undefined){
      return "";
    }
    if (test_cases.length == 0) {
      return "";
    } else {
      return test_cases.map((test_case, cIndex) => (
          <React.Fragment>
            <Card pl="10">
              <CardBody>
                <Flex>
                  <FlexItem>
                    {getWorkItemIcon('test-case', indirect)}
                  </FlexItem>
                  <FlexItem>
                    <TextContent>
                      <Text component={TextVariants.h2}>Test Case {indirect == true ? test_case['test_case']['id'] : test_case['id']}</Text>
                    </TextContent>
                  </FlexItem>
                  <FlexItem>
                    <Text component={TextVariants.h6}>ver. {test_case['version']}</Text>
                  </FlexItem>
                  {indirect == true ? (
                    <Label variant="outline" isCompact>
                      {coverageFormat(test_case['coverage'])}% Coverage
                    </Label>
                  ) : ('')}
                  <FlexItem align={{ default: 'alignRight' }}>
                    {indirect == false ? (
                      <React.Fragment>
                      <Button
                        variant="plain"
                        icon={<OutlinedCommentsIcon  />}
                        onClick={() => setCommentModalInfo(true, 'test-case', 'api', '', test_cases, cIndex)}>
                      </Button>
                      <Badge key={3} screenReaderText="Comments">
                        {test_case['comment_count']}
                      </Badge>
                      </React.Fragment>
                    ) : ('')}
                    <TestCaseMenuKebab
                      indirect={indirect}
                      setDetailsModalInfo={setDetailsModalInfo}
                      setHistoryModalInfo={setHistoryModalInfo}
                      setUsageModalInfo={setUsageModalInfo}
                      tcModalShowState={tcModalShowState}
                      setTcModalInfo={setTcModalInfo}
                      setTcModalShowState={setTcModalShowState}
                      setDeleteModalInfo={setDeleteModalInfo}
                      mappingType={'test-case'}
                      mappingParentType={parent_type}
                      mappingParentRelatedToType={parent_related_to_type}
                      mappingIndex={cIndex}
                      mappingList={test_cases}
                      mappingSection={section}
                      mappingOffset={offset}
                      api={api}
                      />
                  </FlexItem>
                </Flex>
                <Flex>
                  <FlexItem>
                    <TextContent>
                      <Text component={TextVariants.h5}>{indirect == true ? getLimitedText(test_case['test_case']['title'], 100) : getLimitedText(test_case['title'], 100)}</Text>
                      <Text component={TextVariants.p}>{indirect == true ? getLimitedText(test_case['test_case']['description'], 200) : getLimitedText(test_case['description'], 200)}</Text>
                    </TextContent>
                  </FlexItem>
                </Flex>
              </CardBody>
            </Card>
            <Divider />
          </React.Fragment>
      ));
    }
  }

  const getTestSpecifications = (section, offset, test_specs, indirect, parent_type, parent_related_to_type) => {
    if (indirect == false){
      if (mappingViewSelectValue != 'test-specifications'){
        return "";
      }
    } else {
      if (showIndirectTestSpecifications == false){
        return "";
      }
    }
    if (test_specs == undefined){
      return "";
    }
    if (test_specs.length == 0) {
      return "";
    } else {
      return test_specs.map((test_spec, cIndex) => (
          <React.Fragment>
            <Card pl="10">
              <CardBody>
                <Flex>
                  <FlexItem>
                    {getWorkItemIcon('test-specification', indirect)}
                  </FlexItem>
                  <FlexItem>
                    <TextContent>
                      <Text component={TextVariants.h2}>Test Specification {indirect == true ? test_spec['test_specification']['id'] : test_spec['id']}</Text>
                    </TextContent>
                  </FlexItem>
                  <FlexItem>
                    <Text component={TextVariants.h6}>ver. {test_spec['version']}</Text>
                  </FlexItem>
                  {indirect == true ? (
                    <Label variant="outline" isCompact>
                      {coverageFormat(test_spec['coverage'])}% Coverage
                    </Label>
                  ) : ('')}
                  <FlexItem align={{ default: 'alignRight' }}>
                    {indirect == false ? (
                      <React.Fragment>
                      <Button
                        variant="plain"
                        icon={<OutlinedCommentsIcon  />}
                        onClick={() => setCommentModalInfo(true, 'test-specification', 'api', '', test_specs, cIndex)}>
                      </Button>
                      <Badge key={3} screenReaderText="Comments">
                        {test_spec['comment_count']}
                      </Badge>
                      </React.Fragment>
                    ) : ('')}
                    <TestSpecificationMenuKebab
                      indirect={indirect}
                      setDetailsModalInfo={setDetailsModalInfo}
                      setHistoryModalInfo={setHistoryModalInfo}
                      setUsageModalInfo={setUsageModalInfo}
                      tsModalShowState={tsModalShowState}
                      tcModalShowState={tcModalShowState}
                      setTcModalInfo={setTcModalInfo}
                      setTsModalInfo={setTsModalInfo}
                      setTcModalShowState={setTcModalShowState}
                      setTsModalShowState={setTsModalShowState}
                      setDeleteModalInfo={setDeleteModalInfo}
                      mappingType={'test-specification'}
                      mappingParentType={parent_type}
                      mappingParentRelatedToType={parent_related_to_type}
                      mappingIndex={cIndex}
                      mappingList={test_specs}
                      mappingSection={section}
                      mappingOffset={offset}
                      api={api}
                      />
                  </FlexItem>
                </Flex>
                <Flex>
                  <FlexItem>
                    <TextContent>
                      <Text component={TextVariants.h5}>{indirect == true ? getLimitedText(test_spec['test_specification']['title'], 100) : getLimitedText(test_spec['title'], 100)}</Text>
                      <Text component={TextVariants.p}>{indirect == true ? getLimitedText(test_spec['test_specification']['test_description'], 200) : getLimitedText(test_spec['test_description'], 200)}</Text>
                    </TextContent>
                  </FlexItem>
                </Flex>
                </CardBody>
              <CardBody>
                {indirect == true ? getTestCases(section,
                                                 offset,
                                                 test_spec['test_specification']['test_cases'],
                                                 true,
                                                 'test-specification',
                                                 parent_type)
                                  : getTestCases(section,
                                                 offset,
                                                 test_spec['test_cases'],
                                                 true,
                                                 'test-specification',
                                                 parent_type)}
              </CardBody>
            </Card>
            <Divider />
          </React.Fragment>
      ));
    }
  }

  const getSwRequirements = (section, offset, mapping) => {
    if(mappingViewSelectValue != 'sw-requirements'){
      return "";
    }
    if (mapping == undefined){
      return ""
    }
    if (mapping.length == 0) {
      return "";
    } else {
      return mapping.map((mappedItem, mIndex) => (
          <React.Fragment>
            <Card>
              <CardBody>
                <Flex>
                  <FlexItem>
                    {getWorkItemIcon('sw-requirement', false)}
                  </FlexItem>
                  <FlexItem>
                    <TextContent>
                      <Text component={TextVariants.h2}>Software Requirement</Text>
                    </TextContent>
                  </FlexItem>
                  <FlexItem>
                    <Text component={TextVariants.h6}>ver. {mappedItem['version']}</Text>
                  </FlexItem>
                  <Label variant="outline" isCompact>
                    {coverageFormat(mappedItem['coverage'])}% Coverage
                  </Label>
                  <FlexItem align={{ default: 'alignRight' }}>
                    <Button
                      variant="plain"
                      icon={<OutlinedCommentsIcon  />}
                      onClick={() => setCommentModalInfo(true, 'sw-requirement', 'api', '', mapping, mIndex)}>
                    </Button>
                    <Badge key={3} screenReaderText="Comments">
                      {mappedItem['comment_count']}
                    </Badge>
                    <SwRequirementMenuKebab
                      setDetailsModalInfo={setDetailsModalInfo}
                      setHistoryModalInfo={setHistoryModalInfo}
                      setUsageModalInfo={setUsageModalInfo}
                      tsModalShowState={tsModalShowState}
                      setTsModalShowState={setTsModalShowState}
                      tcModalShowState={tcModalShowState}
                      setSrModalInfo={setSrModalInfo}
                      setTsModalInfo={setTsModalInfo}
                      setTcModalInfo={setTcModalInfo}
                      setDeleteModalInfo={setDeleteModalInfo}
                      setForkModalInfo={setForkModalInfo}
                      api={api}
                      mappingType={'sw-requirement'}
                      mappingParentType={'api'}
                      mappingParentRelatedToType={''}
                      mappingList={mapping}
                      mappingIndex={mIndex}
                      mappingSection={section}
                      mappingOffset={offset}
                    />
                  </FlexItem>
                </Flex>
                <Flex>
                  <FlexItem>
                    <TextContent>
                      <Text component={TextVariants.h5}>{getLimitedText(mappedItem['title'], 100)}</Text>
                      <Text component={TextVariants.p}>{getLimitedText(mappedItem['description'], 200)}</Text>
                    </TextContent>
                  </FlexItem>
                </Flex>
              </CardBody>
              <CardBody>
                {getTestSpecifications(section, offset, mappedItem['test_specifications'], true, 'sw-requirement', 'api')}
                {getTestCases(section, offset, mappedItem['test_cases'], true, 'sw-requirement', 'api')}
              </CardBody>
            </Card>
            <Divider />
          </React.Fragment>
      ));
    }
  }

  const getJustifications = (section, offset, mapping) => {
    if (mapping == undefined) {
      return "";
    }
    if (mapping.length == 0) {
      return "";
    } else {
      return mapping.map((mappedItem, mIndex) => (
          <React.Fragment>
            <Card>
              <CardBody>
                <Flex>
                  <FlexItem>
                    {getWorkItemIcon('justification', false)}
                  </FlexItem>
                  <FlexItem>
                    <TextContent>
                      <Text component={TextVariants.h2}>Justification</Text>
                    </TextContent>
                  </FlexItem>
                  <FlexItem>
                    <Text component={TextVariants.h6}>ver. {mappedItem['version']}</Text>
                  </FlexItem>
                  <Label variant="outline" isCompact>
                    {coverageFormat(mappedItem['coverage'])}% Coverage
                  </Label>
                  <FlexItem align={{ default: 'alignRight' }}>
                    <Button
                      variant="plain"
                      icon={<OutlinedCommentsIcon  />}
                      onClick={() => setCommentModalInfo(true, 'justification', 'api', '', mapping, mIndex)}>
                    </Button>
                    <Badge key={3} screenReaderText="Comments">
                      {mappedItem['comment_count']}
                    </Badge>
                    <JustificationMenuKebab
                      jModalShowState={jModalShowState}
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
                    />
                  </FlexItem>
                </Flex>
                <Flex>
                  <FlexItem>
                    <TextContent>
                      <Text component={TextVariants.h5}>{getLimitedText(mappedItem['description'], 100)}</Text>
                    </TextContent>
                  </FlexItem>
                </Flex>
              </CardBody>
            </Card>
            <Divider />
          </React.Fragment>
      ));
    }
  }

  const getUnmapped = (snippet) => {
    let work_item_id = '';
    let work_item_type = '';
    let work_item_description = '';
    let menu = '';

    if (snippet.hasOwnProperty('justification')){
      work_item_type = 'justification';
      work_item_description = snippet['justification']['description'];
      work_item_id = snippet['justification']['id'];
    } else if (snippet.hasOwnProperty('sw_requirement')){
      work_item_type = 'sw-requirement';
      work_item_description = snippet['sw_requirement']['title'];
      work_item_id = snippet['sw_requirement']['id'];
    } else if (snippet.hasOwnProperty('test_specification')){
      work_item_type = 'test-specification';
      work_item_description = snippet['test_specification']['title'];
      work_item_id = snippet['test_specification']['id'];
    } else if (snippet.hasOwnProperty('test_case')){
      work_item_type = 'test-case';
      work_item_description = snippet['test_case']['title'];
      work_item_id = snippet['test_case']['id'];
    }

    return (<React.Fragment>
            <Card>
              <CardBody>
                <Flex>
                  <FlexItem>
                    {getWorkItemIcon(work_item_type, false)}
                  </FlexItem>
                  <FlexItem>
                    <TextContent>
                      <Text component={TextVariants.h2}>{getWorkItemDescription(work_item_type)} {work_item_id}</Text>
                    </TextContent>
                  </FlexItem>
                  <FlexItem>
                    <Text component={TextVariants.h6}>ver. {snippet['version']}</Text>
                  </FlexItem>
                  <Label variant="outline" isCompact>
                    {coverageFormat(snippet['coverage'])}% Coverage
                  </Label>
                  <FlexItem align={{ default: 'alignRight' }}>
                    <UnmappedMenuKebab
                      api={api}
                      jModalShowState={jModalShowState}
                      srModalShowState={srModalShowState}
                      tcModalShowState={tcModalShowState}
                      tsModalShowState={tsModalShowState}
                      setDeleteModalInfo={setDeleteModalInfo}
                      setTcModalInfo={setTcModalInfo}
                      setTsModalInfo={setTsModalInfo}
                      setSrModalInfo={setSrModalInfo}
                      setJModalInfo={setJModalInfo}
                      mappingType={work_item_type}
                      mappingParentType="api"
                      mappingIndex={0}
                      mappingList={[snippet]}
                      mappingSection={snippet['section']}
                      mappingOffset={snippet['offset']}
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
      );
  }

  const getMappingTable = () => {
    if (mappingData == undefined){
      return "";
    }
    if (mappingData.length == 0) {
      return "";
    } else {
      return mappingData.map((snippet, snippetIndex) => (
          <Tr className="row-bottom-sep">
            <Td width={50} dataLabel={columnNames.specification}>
            <Card>
              <CardBody>
                <Flex>
                  <FlexItem align={{ default: 'alignLeft' }}>
                      Coverage Total:
                  </FlexItem>
                  <FlexItem align={{ default: 'alignLeft' }}>
                    <LeavesProgressBar
                      progressValue={snippet['coverage']}
                      progressId={"mapping-section-coverage-" + snippetIndex}
                      />
                  </FlexItem>
                  <FlexItem align={{ default: 'alignRight' }}>
                    <MappingSectionMenuKebab
                      offset={snippet['offset']}
                      section={snippet['section']}
                      sectionIndex={snippetIndex}
                      isMatchingSection={true}
                      setTcModalInfo={setTcModalInfo}
                      setTsModalInfo={setTsModalInfo}
                      setSrModalInfo={setSrModalInfo}
                      setJModalInfo={setJModalInfo} />
                  </FlexItem>
                </Flex>
                </CardBody>
                </Card>
                <Divider />
              <CodeBlock className={getMappedSectionCodeBlockBackgroundColor(snippet) + " full-height"}>
                <CodeBlockCode>
                  <div id={"snippet-" + snippetIndex} data-offset={snippet['offset']}>
                  {snippet['section']}
                  </div>
                </CodeBlockCode>
              </CodeBlock>
            </Td>
            <Td width={50} dataLabel={columnNames.work_items}>
              {getSwRequirements(snippet['section'], snippet['offset'], snippet[mappingViewSelectValue.replaceAll("-", "_")])}
              {getTestSpecifications(snippet['section'], snippet['offset'], snippet[mappingViewSelectValue.replaceAll("-", "_")], false, 'api')}
              {getTestCases(snippet['section'], snippet['offset'], snippet[mappingViewSelectValue.replaceAll("-", "_")], false, 'api')}
              {getJustifications(snippet['section'], snippet['offset'], snippet['justifications'])}
              {/*getSpecifications*/}
            </Td>
          </Tr>
      ));
    }
  }

  const getUnmappingTable = () => {
    if (unmappingData.length == 0) {
      return "";
    } else {
      return unmappingData.map((snippet, snippetIndex) => (
          <Tr>
            <Td width={50} dataLabel={columnNames.specification}>
            <Card>
              <CardBody>
                <Flex>
                  <FlexItem align={{ default: 'alignLeft' }}>
                    Coverage Total:
                    <LeavesProgressBar
                      progressValue={snippet['coverage']}
                      progressId={"unmapping-section-coverage-" + snippetIndex}
                      />
                  </FlexItem>
                </Flex>
                </CardBody>
                </Card>
                <Divider />
              <CodeBlock className="code-block-bg-red">
                <CodeBlockCode>
                  <div id={"snippet-" + snippetIndex} data-offset={snippet['offset']}>
                  {snippet['section']}
                  </div>
                </CodeBlockCode>
              </CodeBlock>
            </Td>
            <Td width={50} dataLabel={columnNames.work_items}>
              {getUnmapped(snippet)}
            </Td>
          </Tr>
      ));
    }
  }


  const dataHistory =
    {
      history: [{
        version: 1,
        object: {'prova': 'valore1'},
        mapping: {}
      }]
    }

  return (
    <React.Fragment>
      <PageSection>
        <Table>
          <Thead>
            <Tr>
              <Th>{columnNames.specification}</Th>
              <Th>{columnNames.work_items}</Th>
            </Tr>
          </Thead>
          <Tbody key={1}>
            {getMappingTable()}
          </Tbody>
        </Table>
      </PageSection>

      <PageSection>
        <Table>
          <Thead>
            <Tr>
              <Th>{columnNames.specification}</Th>
              <Th>UNMATCHING {columnNames.work_items}</Th>
            </Tr>
          </Thead>
          <Tbody key={2}>
            {getUnmappingTable()}
          </Tbody>
        </Table>
      </PageSection>
    </React.Fragment>
  )
}

export { MappingListingTable };
