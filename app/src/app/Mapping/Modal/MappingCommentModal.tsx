import React from 'react';
import { Modal, ModalVariant, Form, FormGroup, Popover, Button, TextInput} from '@patternfly/react-core';
import { PageSection } from '@patternfly/react-core';
import { TextContent, Text, TextList, TextListItem, TextVariants } from '@patternfly/react-core';
import { Panel, PanelMain, PanelMainBody } from '@patternfly/react-core';
import { Table, Tbody, Td, Th, Thead, Tr } from '@patternfly/react-table';
import { CommentForm } from '../Form/CommentForm';
import { JustificationSearch } from '../Search/JustificationSearch';
import { MappingModalProps } from './MappingModalProps';

export interface MappingCommentModalProps {
  api;
  baseApiUrl;
  modalDescription;
  modalTitle;
  relationData;
  workItemType;
  parentType;
  parentRelatedToType;
  setModalShowState;
  modalShowState;
  loadMappingData;
}

export const MappingCommentModal: React.FunctionComponent<MappingCommentModalProps> = ({
  api,
  baseApiUrl,
  modalDescription,
  modalTitle,
  relationData,
  workItemType,
  parentType,
  parentRelatedToType,
  setModalShowState,
  modalShowState=false,
  loadMappingData,
  }: MappingCommentModalProps) => {
  const [isModalOpen, setIsModalOpen] = React.useState(false);
  const [comments, setComments] = React.useState([]);

  const _A = 'api';
  const _J = 'justification';
  const _M_ = '_mapping_';
  const _SR = 'sw-requirement';
  const _SR_ = 'sw_requirement';
  const _TS = 'test-specification';
  const _TS_ = 'test_specification';
  const _TC = 'test-case';
  const _TC_ = 'test_case';

  const handleModalToggle = (_event: KeyboardEvent | React.MouseEvent) => {
    let new_state = !modalShowState;
    setModalShowState(new_state);
    setIsModalOpen(new_state);
  };

  React.useEffect(() => {
    setIsModalOpen(modalShowState);
  }, [modalShowState]);

  React.useEffect(() => {
    if (isModalOpen == false){
      return;
    }
    let parent_table = '';
    let parent_id = '';
    if (workItemType == _J){
      if (parentType == _A){
        parent_table = _J + _M_ + _A;
        parent_id = relationData.relation_id;
      }
    } else if (workItemType == _SR) {
      if (parentType == _A){
        parent_table = _SR_ + _M_ + _A;
        parent_id = relationData.relation_id;
      }
    } else if (workItemType == _TS) {
      if (parentType == _A){
        parent_table = _TS_ + _M_ + _A;
        parent_id = relationData.relation_id;
      }
    } else if (workItemType == _TC) {
      if (parentType == _A){
        parent_table = _TC_ + _M_ + _A;
        parent_id = relationData.relation_id;
      }
    }

    if ((parent_table != '') && (parent_id != '')){
      loadComments(parent_table, parent_id);
    }
  }, [isModalOpen]);

  React.useEffect(() => {
    getComments();
  }, [comments]);


  const loadComments = (parent_table, parent_id) => {
    fetch(baseApiUrl + '/comments?parent_table=' +  parent_table + '&parent_id=' + parent_id)
      .then((res) => res.json())
      .then((data) => {
        setComments(data);
      })
      .catch((err) => {
        console.log(err.message);
      });
  }

  const getComments = () => {
    return comments.map((comment, index) => (
                <TextListItem>

                  <em><b>{comment.username}</b></em>< span class="date-text"> on {comment.created_at}</span>
                  <br />
                  {comment.comment}


                </TextListItem>
            ))
  }

  return (
    <React.Fragment>
      <Modal
        bodyAriaLabel="Scrollable modal content"
        tabIndex={0}
        variant={ModalVariant.large}
        title={modalTitle}
        description={modalDescription}
        isOpen={isModalOpen}
        onClose={handleModalToggle}
        actions={[
          <Button key="cancel" variant="link" onClick={handleModalToggle}>
            Cancel
          </Button>
        ]}
      >

          <Table>
            <Thead>
              <Tr>
                <Th>Comments</Th>
                <Th>Add new Comment</Th>
              </Tr>
            </Thead>
            <Tbody key={1}>
              <Tr>
                <Td>
                <Panel isScrollable>
                  <PanelMain tabIndex={0}>
                    <PanelMainBody>
                      <TextContent>
                        <TextList>
                          {getComments()}
                        </TextList>
                      </TextContent>
                    </PanelMainBody>
                  </PanelMain>
                </Panel>
                </Td>
                <Td>
                  <CommentForm
                    api={api}
                    baseApiUrl={baseApiUrl}
                    relationData={relationData}
                    workItemType={workItemType}
                    parentType={parentType}
                    parentRelatedToType={parentRelatedToType}
                    setModalShowState={setModalShowState}
                    modalShowState={modalShowState}
                    handleModalToggle={handleModalToggle}
                    loadMappingData={loadMappingData}
                    loadComments={loadComments} />
                </Td>
              </Tr>

            </Tbody>
          </Table>


      </Modal>
    </React.Fragment>
  );
};
