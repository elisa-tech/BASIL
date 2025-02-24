import React from 'react'
import ReactMarkdown from 'react-markdown'
import * as Constants from '@app/Constants/constants'
import { Button, Modal, ModalVariant } from '@patternfly/react-core'
import { List, ListItem, Text, TextContent } from '@patternfly/react-core'
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
    const parent_table = Constants.getMappingTableName(workItemType, parentType)
    let parent_id = relationData.relation_id

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
      <ListItem key={index}>
        <em>
          <b>{comment['created_by']}</b>
        </em>
        <span className='date-text'> on {comment['created_at']}</span>
        <br />
        <Text>
          <ReactMarkdown>{comment['comment'].toString()}</ReactMarkdown>
        </Text>
      </ListItem>
    ))
  }

  return (
    <React.Fragment>
      <Modal
        width={Constants.MODAL_WIDTH}
        bodyAriaLabel='MappingCommentModal'
        aria-label='mapping comment modal'
        tabIndex={0}
        variant={ModalVariant.large}
        title={modalTitle}
        description={modalDescription}
        isOpen={isModalOpen}
        onClose={handleModalToggle}
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
                        <List isPlain isBordered>
                          {getComments()}
                        </List>
                      </TextContent>
                    </PanelMainBody>
                  </PanelMain>
                </Panel>
              </Td>
              <Td>
                <CommentForm
                  handleModalToggle={handleModalToggle}
                  loadComments={loadComments}
                  loadMappingData={loadMappingData}
                  parentType={parentType}
                  relationData={relationData}
                  workItemType={workItemType}
                />
              </Td>
            </Tr>
          </Tbody>
        </Table>
      </Modal>
    </React.Fragment>
  )
}
