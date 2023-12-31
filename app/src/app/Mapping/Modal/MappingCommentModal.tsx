import React from 'react';
import { Button, Modal, ModalVariant } from '@patternfly/react-core';
import { TextContent, TextList, TextListItem } from '@patternfly/react-core';
import { Panel, PanelMain, PanelMainBody } from '@patternfly/react-core';
import { Table, Tbody, Td, Th, Thead, Tr } from '@patternfly/react-table';
import { CommentForm } from '../Form/CommentForm';

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

  const handleModalToggle = () => {
    const new_state = !modalShowState;
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
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isModalOpen]);

  React.useEffect(() => {
    getComments();
    // eslint-disable-next-line react-hooks/exhaustive-deps
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
                <TextListItem key={index}>

                  <em><b>{comment.username}</b></em><span className="date-text"> on {comment.created_at}</span>
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
