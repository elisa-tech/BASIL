import * as React from 'react';
import { Button, Card, CardBody, Flex, FlexItem, Label, PageSection, Pagination, Title, Toolbar, ToolbarContent, ToolbarItem } from '@patternfly/react-core';
import { MappingListingTable} from './MappingListingTable';
import { MappingSwRequirementModal } from './Modal/MappingSwRequirementModal';
import { MappingTestSpecificationModal } from './Modal/MappingTestSpecificationModal';
import { MappingTestCaseModal } from './Modal/MappingTestCaseModal';
import { MappingJustificationModal } from './Modal/MappingJustificationModal';
import { MappingDeleteModal } from './Modal/MappingDeleteModal';
import { MappingDetailsModal } from './Modal/MappingDetailsModal';
import { MappingForkModal } from './Modal/MappingForkModal';
import { MappingHistoryModal } from './Modal/MappingHistoryModal';
import { MappingUsageModal } from './Modal/MappingUsageModal';
import { MappingCommentModal } from './Modal/MappingCommentModal';
import { Switch } from '@patternfly/react-core';
import { MappingViewSelect } from './MappingViewSelect';
import { LeavesProgressBar } from '../Custom/LeavesProgressBar';

export interface MappingPageSectionProps {
  baseApiUrl: string;
  mappingData;
  unmappingData;
  loadMappingData;
  mappingViewSelectValue;
  setMappingViewSelectValue;
  totalCoverage;
  api;
}

const MappingPageSection: React.FunctionComponent<MappingPageSectionProps> = ({
  baseApiUrl,
  mappingData=[],
  unmappingData=[],
  loadMappingData,
  mappingViewSelectValue,
  setMappingViewSelectValue,
  totalCoverage,
  api,
  }: MappingPageSectionProps) => {
  const rows = [];
  const [modalShowState, setModalShowState] = React.useState<boolean>(false);
  const [modalCheckSpecShowState, setModalCheckSpecShowState] = React.useState<boolean>(false);
  const [modalSPDXExportShowState, setModalSPDXExportShowState] = React.useState<boolean>(false);
  const [modalCheckSpecApiData, setModalCheckSpecApiData] = React.useState(null);
  const [modalObject, setModalObject] = React.useState('');
  const [modalAction, setModalAction] = React.useState('');
  const [modalVerb, setModalVerb] = React.useState('');
  const [modalFormData, setModalFormData] = React.useState('');
  const [modalTitle, setModalTitle] = React.useState('');
  const [modalIndirect, setModalIndirect] = React.useState<boolean>(false);
  const [modalDescription, setModalDescription] = React.useState('');
  const [modalParentData, setModalParentData] = React.useState({});
  const [modalParentType, setModalParentType] = React.useState('');
  const [modalParentRelatedToType, setModalParentRelatedToType] = React.useState('');

  const [modalSection, setModalSection] = React.useState('');
  const [modalOffset, setModalOffset] = React.useState('');
  const [apiSwRequirement, setApiSwRequirement] = React.useState(null);

  const [srModalShowState, setSrModalShowState] = React.useState<boolean>(false);
  const [tsModalShowState, setTsModalShowState] = React.useState<boolean>(false);
  const [tcModalShowState, setTcModalShowState] = React.useState<boolean>(false);
  const [jModalShowState, setJModalShowState] = React.useState<boolean>(false);
  const [historyModalShowState, setHistoryModalShowState] = React.useState<boolean>(false);
  const [deleteModalShowState, setDeleteModalShowState] = React.useState<boolean>(false);
  const [detailsModalShowState, setDetailsModalShowState] = React.useState<boolean>(false);
  const [forkModalShowState, setForkModalShowState] = React.useState<boolean>(false);
  const [usageModalShowState, setUsageModalShowState] = React.useState<boolean>(false);
  const [commentModalShowState, setCommentModalShowState] = React.useState<boolean>(false);
  const [currentMappingHistory, setCurrentMappingHistory] = React.useState();
  const [currentMappingDetails, setCurrentMappingDetails] = React.useState();
  const [currentMappingUsage, setCurrentMappingUsage] = React.useState();

  const [modalRelationData, setModalRelationData] = React.useState({});
  const [modalWorkItemType, setModalWorkItemType] = React.useState('');

  const [showIndirectTestSpecifications, setShowIndirectTestSpecifications] = React.useState<boolean>(true);
  const [showIndirectTestCases, setShowIndirectTestCases] = React.useState<boolean>(true);

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

  const tcFormEmpty = {'coverage': 0,
                       'title': '',
                       'description': '',
                       'repository': '',
                       'relative_path': ''}
  const tsFormEmpty = {'coverage': 0,
                       'title': '',
                       'preconditions': '',
                       'test_description': '',
                       'expected_behavior': ''}
  const srFormEmpty = {'coverage': 0,
                       'title': '',
                       'description': ''}
  const jFormEmpty = {'description': '',
                      'coverage': 100}

  const getTestCaseData = (_list, _index, _parent_type) => {
    let tc = {};
    if (_parent_type != _A){
      tc = _list[_index][_TC_];
      tc['coverage'] = _list[_index]['coverage'];
    } else {
      tc = _list[_index];
    }
    return tc;
  }

  const getTestSpecificationData = (_list, _index, _parent_type) => {
    let ts = {};
    if (_parent_type != _A){
      ts = _list[_index][_TS_];
      ts['coverage'] = _list[_index]['coverage'];
    } else {
      ts = _list[_index];
    }
    return ts;
  }

  const setSrModalInfo = (show, indirect, action, api,
                          section, offset,
                          parent_type, parent_list, parent_index,
                          parent_related_to_type) => {
    setModalTitle(getWorkItemDescription(_SR));
    setModalDescription("Work item data and mapping information (section, offset, coverage).");
    setSrModalShowState(show);
    setModalAction(action);
    if (action == 'add') {
      setModalVerb('POST');
      setModalFormData(srFormEmpty);
    } else if (action == 'edit') {
      setModalVerb('PUT');
      setModalFormData(parent_list[parent_index]);
    }
    setModalParentData(parent_list[parent_index]);
    setModalSection(section);
    setModalOffset(offset);
    setModalIndirect(indirect);
    setModalParentType(parent_type);
    setModalParentRelatedToType(parent_related_to_type);
  }

  const setTsModalInfo = (show, indirect, action, api,
                          section, offset,
                          parent_type, parent_list, parent_index,
                          parent_related_to_type) => {

    setModalTitle(getWorkItemDescription(_TS));
    setModalDescription("Work item data and mapping information (section, offset, coverage).");
    setModalAction(action);
    if (action == 'add') {
      setModalVerb('POST');
      setModalFormData(tsFormEmpty);
    } else if (action == 'edit') {
      setModalVerb('PUT');
      setModalFormData(getTestSpecificationData(parent_list, parent_index, parent_type));
    }
    setModalParentData(parent_list[parent_index]);
    setModalSection(section);
    setModalOffset(offset);
    setModalIndirect(indirect);
    setModalParentType(parent_type);
    setModalParentRelatedToType(parent_related_to_type);
    setTsModalShowState(show);
  }

  const setTcModalInfo = (show, indirect, action, api,
                          section, offset,
                          parent_type, parent_list, parent_index,
                          parent_related_to_type) => {

    setModalTitle(getWorkItemDescription(_TC));
    setModalDescription("Work item data and mapping information (section, offset, coverage).");
    setTcModalShowState(show);
    setModalAction(action);
    if (action == 'add') {
      setModalVerb('POST');
      setModalFormData(tcFormEmpty);
    } else if (action == 'edit') {
      setModalVerb('PUT');
      setModalFormData(getTestCaseData(parent_list, parent_index, parent_type));
    }
    setModalParentData(parent_list[parent_index]);
    setModalSection(section);
    setModalOffset(offset);
    setModalIndirect(indirect);
    setModalParentType(parent_type);
    setModalParentRelatedToType(parent_related_to_type);
  }


  const setJModalInfo = (show, action, api,
                          section, offset, parent_list, parent_index) => {
    setJModalShowState(show);
    setModalAction(action);
    if (action == 'add') {
      setModalVerb('POST');
      setModalFormData(jFormEmpty);
    } else if (action == 'edit') {
      setModalVerb('PUT');
      setModalFormData(parent_list[parent_index]);
    }

    setModalTitle(getWorkItemDescription(_J));
    setModalDescription("Work item data and mapping information (section, offset, coverage).");
    setModalSection(section);
    setModalOffset(offset);
    setModalIndirect(false);
    setModalParentType('api');
    setModalParentRelatedToType('');
  }

  const setDeleteModalInfo = (show, work_item_type, parent_type, parent_related_to_type, list, index) => {
    setModalTitle("Delete selected " + getWorkItemDescription(work_item_type));
    setModalDescription("Do you want to continue?");
    setModalRelationData(list[index]);
    setDeleteModalShowState(show);
    setModalWorkItemType(work_item_type);
    setModalParentType(parent_type);
    setModalParentRelatedToType(parent_related_to_type);
  }

  const setForkModalInfo = (show, work_item_type, parent_type, parent_related_to_type, list, index) => {
    setModalTitle("Fork selected " + getWorkItemDescription(work_item_type));
    setModalDescription("Do you want to continue?");
    setModalRelationData(list[index]);
    setForkModalShowState(show);
    setModalWorkItemType(work_item_type);
    setModalParentType(parent_type);
    setModalParentRelatedToType(parent_related_to_type);
  }

  const setCommentModalInfo = (show, work_item_type, parent_type, parent_related_to_type, list, index) => {
    let wi_field = 'title';
    if (work_item_type == _J){
      wi_field = 'description';
    }
    let wi_title = list[index][wi_field].substr(0, 100);
    if (list[index][wi_field].length > 99){
      wi_title = wi_title + "...";
    }
    setModalTitle("Comment a " + getWorkItemDescription(work_item_type));
    setModalDescription(wi_title);
    setCommentModalShowState(show);
    setModalWorkItemType(work_item_type);
    setModalParentType(parent_type);
    setModalParentRelatedToType(parent_related_to_type);
    setModalRelationData(list[index]);
  }

  const setHistoryModalInfo = (show, work_item_type, mapped_to_type, relation_id) => {
    let url = baseApiUrl + "/mapping/history?work_item_type=" + work_item_type + "&mapped_to_type=" + mapped_to_type + "&relation_id=" + relation_id;
    fetch(url)
      .then((res) => res.json())
      .then((data) => {
        setCurrentMappingHistory(data);
        setHistoryModalShowState(show);
      })
      .catch((err) => {
        console.log(err.message);
      });
  }

  const setDetailsModalInfo = (show, work_item_type, work_item_id) => {
    let url = baseApiUrl + "/" + work_item_type + "s?field1=id&filter1=" + work_item_id;
    fetch(url)
      .then((res) => res.json())
      .then((data) => {
        setModalTitle(getWorkItemDescription(work_item_type) + " details");
        setModalDescription("");
        setCurrentMappingDetails(data);
        setDetailsModalShowState(show);
      })
      .catch((err) => {
        console.log(err.message);
    });
  }

  const setUsageModalInfo = (show, work_item_type, work_item_id) => {
    let url = baseApiUrl + "/mapping/usage?work_item_type=" + work_item_type + "&id=" + work_item_id;
    fetch(url)
      .then((res) => res.json())
      .then((data) => {
        setCurrentMappingUsage(data);
        setUsageModalShowState(show);
        setModalTitle(getWorkItemDescription(work_item_type) + " usage");
        setModalDescription("");
      })
      .catch((err) => {
        console.log(err.message);
    });
  }

  const toggleIndirectTestSpecifications = (_event: React.FormEvent<HTMLInputElement>, checked: boolean) => {
    setShowIndirectTestSpecifications(!showIndirectTestSpecifications);
  };
  const toggleIndirectTestCases = (_event: React.FormEvent<HTMLInputElement>, checked: boolean) => {
    setShowIndirectTestCases(!showIndirectTestCases);
  };

  React.useEffect(() => {
    loadMappingData();
  }, [showIndirectTestSpecifications, showIndirectTestCases]);

  return (
    <React.Fragment>
    <PageSection isFilled>
      <Card>
        <CardBody>
          <Flex>
            <Flex>
              <FlexItem>
                <Title headingLevel="h1">Mapping</Title>
              </FlexItem>
              <FlexItem>
                <LeavesProgressBar progressValue={totalCoverage} progressId="api-mapping-coverage" />
              </FlexItem>
            </Flex>
            <Flex align={{ default: 'alignRight' }}>
              <FlexItem>
                <Button
                  variant="secondary"
                  onClick={() => (setSrModalInfo(true,
                                                 false,
                                                 'add',
                                                 api,
                                                 '',
                                                 0,
                                                 'api',
                                                 [],
                                                 -1,
                                                 ''))}
                  >Map Software Req.
                </Button>
              </FlexItem>
              <FlexItem>
                <Button
                  variant="secondary"
                  onClick={() => (setTsModalInfo(true,
                                                 false,
                                                 'add',
                                                 api,
                                                 '',
                                                 0,
                                                 'api',
                                                 [],
                                                 -1,
                                                 ''))}
                >Map Test Specification
                </Button>
              </FlexItem>
              <FlexItem>
                <Button
                  variant="secondary"
                  onClick={() => (setTcModalInfo(true,
                                                 false,
                                                 'add',
                                                 api,
                                                 '',
                                                 0,
                                                 'api',
                                                 [],
                                                 -1,
                                                 ''))}
                >Map Test Case
                </Button>
              </FlexItem>
              <FlexItem>
                <Button
                  variant="secondary"
                  onClick={() => setJModalInfo(true,
                                               'add',
                                               api,
                                               '',
                                               0)}
                >Map Justification
                </Button>
              </FlexItem>
            </Flex>
          </Flex>
        </CardBody>
      </Card>
      <Card>
        <CardBody>
        <Flex>
          <FlexItem>
            <MappingViewSelect
              mappingViewSelectValue={mappingViewSelectValue}
              setMappingViewSelectValue={setMappingViewSelectValue}
            />
          </FlexItem>
          <FlexItem align={{ default: 'alignRight' }}>
            <Switch
              id="switch-indirect-test-specifications"
              label="Indirect Test Specification"
              labelOff="Indirect Test Specification Hidden"
              isChecked={showIndirectTestSpecifications}
              onChange={toggleIndirectTestSpecifications}
              ouiaId="BasicSwitch"
            />
          </FlexItem>
          <FlexItem>
          <Switch
            id="switch-indirect-test-cases"
            label="Indirect Test Case"
            labelOff="Indirect Test Case Hidden"
            isChecked={showIndirectTestCases}
            onChange={toggleIndirectTestCases}
            ouiaId="BasicSwitch"
          />
          </FlexItem>
        </Flex>
        </CardBody>
        </Card>
    </PageSection>

    <MappingListingTable
      baseApiUrl={baseApiUrl}
      mappingData={mappingData}
      unmappingData={unmappingData}
      api={api}
      apiSwRequirement={apiSwRequirement}
      srModalShowState={srModalShowState}
      setSrModalShowState={setSrModalShowState}
      tsModalShowState={tsModalShowState}
      setTsModalShowState={setTsModalShowState}
      tcModalShowState={tcModalShowState}
      setTcModalShowState={setTcModalShowState}
      jModalShowState={jModalShowState}
      setJModalShowState={setJModalShowState}
      setTsModalInfo={setTsModalInfo}
      setTcModalInfo={setTcModalInfo}
      setSrModalInfo={setSrModalInfo}
      setJModalInfo={setJModalInfo}
      setCommentModalInfo={setCommentModalInfo}
      setDeleteModalInfo={setDeleteModalInfo}
      setDetailsModalInfo={setDetailsModalInfo}
      setForkModalInfo={setForkModalInfo}
      setHistoryModalInfo={setHistoryModalInfo}
      setUsageModalInfo={setUsageModalInfo}
      mappingViewSelectValue={mappingViewSelectValue}
      showIndirectTestCases={showIndirectTestCases}
      showIndirectTestSpecifications={showIndirectTestSpecifications}
      />
    <MappingSwRequirementModal
      api={api}
      baseApiUrl={baseApiUrl}
      modalAction={modalAction}
      modalDescription={modalDescription}
      modalFormData={modalFormData}
      modalIndirect={modalIndirect}
      modalObject={modalObject}
      modalOffset={modalOffset}
      setModalOffset={setModalOffset}
      modalSection={modalSection}
      setModalSection={setModalSection}
      modalShowState={srModalShowState}
      modalTitle={modalTitle}
      modalVerb={modalVerb}
      loadMappingData={loadMappingData}
      parentData={modalParentData}
      parentType={modalParentType}
      setModalShowState={setSrModalShowState} />
    <MappingTestSpecificationModal
      api={api}
      baseApiUrl={baseApiUrl}
      modalAction={modalAction}
      modalDescription={modalDescription}
      modalFormData={modalFormData}
      modalIndirect={modalIndirect}
      modalObject={modalObject}
      modalOffset={modalOffset}
      setModalOffset={setModalOffset}
      modalSection={modalSection}
      setModalSection={setModalSection}
      modalShowState={tsModalShowState}
      modalTitle={modalTitle}
      modalVerb={modalVerb}
      loadMappingData={loadMappingData}
      parentData={modalParentData}
      parentType={modalParentType}
      parentRelatedToType={modalParentRelatedToType}
      setModalShowState={setTsModalShowState} />
    <MappingTestCaseModal
      api={api}
      baseApiUrl={baseApiUrl}
      modalAction={modalAction}
      modalDescription={modalDescription}
      modalFormData={modalFormData}
      modalIndirect={modalIndirect}
      modalObject={modalObject}
      modalOffset={modalOffset}
      setModalOffset={setModalOffset}
      modalSection={modalSection}
      setModalSection={setModalSection}
      modalShowState={tcModalShowState}
      modalTitle={modalTitle}
      modalVerb={modalVerb}
      loadMappingData={loadMappingData}
      parentData={modalParentData}
      parentType={modalParentType}
      parentRelatedToType={modalParentRelatedToType}
      setModalShowState={setTcModalShowState} />
    <MappingJustificationModal
      api={api}
      baseApiUrl={baseApiUrl}
      modalAction={modalAction}
      modalDescription={modalDescription}
      modalFormData={modalFormData}
      modalIndirect={modalIndirect}
      modalObject={modalObject}
      modalOffset={modalOffset}
      setModalOffset={setModalOffset}
      modalSection={modalSection}
      setModalSection={setModalSection}
      modalShowState={jModalShowState}
      modalTitle={modalTitle}
      modalVerb={modalVerb}
      loadMappingData={loadMappingData}
      parentData={modalParentData}
      parentType={modalParentType}
      setModalShowState={setJModalShowState}/>
    <MappingDetailsModal
      modalDescription={modalDescription}
      modalTitle={modalTitle}
      modalData={currentMappingDetails}
      setModalShowState={setDetailsModalShowState}
      modalShowState={detailsModalShowState}/>
    <MappingHistoryModal
      modalDescription={modalDescription}
      modalTitle={modalTitle}
      modalData={currentMappingHistory}
      setModalShowState={setHistoryModalShowState}
      modalShowState={historyModalShowState}/>
    <MappingUsageModal
      modalDescription={modalDescription}
      modalTitle={modalTitle}
      modalData={currentMappingUsage}
      setModalShowState={setUsageModalShowState}
      modalShowState={usageModalShowState}
      />
    <MappingCommentModal
      api={api}
      baseApiUrl={baseApiUrl}
      modalDescription={modalDescription}
      modalTitle={modalTitle}
      relationData={modalRelationData}
      workItemType={modalWorkItemType}
      parentType={modalParentType}
      parentRelatedToType={modalParentRelatedToType}
      setModalShowState={setCommentModalShowState}
      modalShowState={commentModalShowState}
      loadMappingData={loadMappingData}
      />
    <MappingDeleteModal
      api={api}
      baseApiUrl={baseApiUrl}
      modalTitle={modalTitle}
      modalDescription={modalDescription}
      setModalShowState={setDeleteModalShowState}
      modalShowState={deleteModalShowState}
      workItemType={modalWorkItemType}
      parentType={modalParentType}
      parentRelatedToType={modalParentRelatedToType}
      relationData={modalRelationData}
      loadMappingData={loadMappingData}/>
    <MappingForkModal
      api={api}
      baseApiUrl={baseApiUrl}
      modalTitle={modalTitle}
      modalDescription={modalDescription}
      setModalShowState={setForkModalShowState}
      modalShowState={forkModalShowState}
      workItemType={modalWorkItemType}
      parentType={modalParentType}
      parentRelatedToType={modalParentRelatedToType}
      relationData={modalRelationData}
      loadMappingData={loadMappingData}/>
    </React.Fragment>
  )
}

export { MappingPageSection };
