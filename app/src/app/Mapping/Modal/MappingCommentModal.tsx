import React from 'react'
import ReactMarkdown from 'react-markdown'
import * as Constants from '../../Constants/constants'
import { Button, Modal, ModalVariant } from '@patternfly/react-core'
import { Text, TextContent, TextList, TextListItem } from '@patternfly/react-core'
import { Panel, PanelMain, PanelMainBody } from '@patternfly/react-core'
import { Table, Tbody, Td, Th, Thead, Tr } from '@patternfly/react-table'
import { CommentForm } from '../Form/CommentForm'

export interface MappingCommentModalProps {
  modalDescription
  modalTitle
  relationData
  workItemType
  parentType
  setModalShowState
  modalShowState: boolean
  loadMappingData
}

export const MappingCommentModal: React.FunctionComponent<MappingCommentModalProps> = ({
  modalDescription,
  modalTitle,
  relationData,
  workItemType,
  parentType,
  setModalShowState,
  modalShowState = false,
  loadMappingData
}: MappingCommentModalProps) => {
  const [isModalOpen, setIsModalOpen] = React.useState(false)
  // eslint-disable-next-line  @typescript-eslint/no-explicit-any
  const [comments, setComments] = React.useState<any[]>([])

  const handleModalToggle = () => {
    const new_state = !modalShowState
    setModalShowState(new_state)
    setIsModalOpen(new_state)
  }

  React.useEffect(() => {
    setIsModalOpen(modalShowState)
  }, [modalShowState])

  React.useEffect(() => {
    if (isModalOpen == false) {
      return
    }
    let parent_table = ''
    let parent_id = ''
    if (workItemType == Constants._J) {
      if (parentType == Constants._A) {
        parent_table = Constants._J + Constants._M_ + Constants._A
        parent_id = relationData.relation_id
      }
    } else if (workItemType == Constants._SR) {
      if (parentType == Constants._A) {
        parent_table = Constants._SR_ + Constants._M_ + Constants._A
        parent_id = relationData.relation_id
      }
    } else if (workItemType == Constants._TS) {
      if (parentType == Constants._A) {
        parent_table = Constants._TS_ + Constants._M_ + Constants._A
        parent_id = relationData.relation_id
      }
    } else if (workItemType == Constants._TC) {
      if (parentType == Constants._A) {
        parent_table = Constants._TC_ + Constants._M_ + Constants._A
        parent_id = relationData.relation_id
      }
    }

    if (parent_table != '' && parent_id != '') {
      loadComments(parent_table, parent_id)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isModalOpen])

  React.useEffect(() => {
    getComments()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [comments])

  const loadComments = (parent_table, parent_id) => {
    fetch(Constants.API_BASE_URL + '/comments?parent_table=' + parent_table + '&parent_id=' + parent_id)
      .then((res) => res.json())
      .then((data) => {
        setComments(data)
      })
      .catch((err) => {
        console.log(err.message)
      })
  }

  const getComments = () => {
    return comments.map((comment, index) => (
      <TextListItem key={index}>
        <em>
          <b>{comment['created_by']}</b>
        </em>
        <span className='date-text'> on {comment['created_at']}</span>
        <br />
        <Text>
          <ReactMarkdown>{comment['comment'].toString()}</ReactMarkdown>
        </Text>
      </TextListItem>
    ))
  }

  return (
    <React.Fragment>
      <Modal
        bodyAriaLabel='Scrollable modal content'
        tabIndex={0}
        variant={ModalVariant.large}
        title={modalTitle}
        description={modalDescription}
        isOpen={isModalOpen}
        onClose={handleModalToggle}
        actions={[
          <Button key='cancel' variant='link' onClick={handleModalToggle}>
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
                        <TextList>{getComments()}</TextList>
                      </TextContent>
                    </PanelMainBody>
                  </PanelMain>
                </Panel>
              </Td>
              <Td>
                <CommentForm
                  //api={api}
                  relationData={relationData}
                  workItemType={workItemType}
                  parentType={parentType}
                  //parentRelatedToType={parentRelatedToType}
                  //setModalShowState={setModalShowState}
                  //modalShowState={modalShowState}
                  handleModalToggle={handleModalToggle}
                  loadMappingData={loadMappingData}
                  //loadComments={loadComments}
                />
              </Td>
            </Tr>
          </Tbody>
        </Table>
      </Modal>
    </React.Fragment>
  )
}
