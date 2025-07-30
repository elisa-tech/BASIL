import React from 'react'
import * as Constants from '@app/Constants/constants'
import { Modal, ModalVariant } from '@patternfly/react-core'
import { Panel, PanelMain, PanelMainBody } from '@patternfly/react-core'
import { Table, Tbody, Td, Th, Thead, Tr } from '@patternfly/react-table'
import { CommentForm } from '../Form/CommentForm'
import { useAuth } from '../../User/AuthProvider'
import CommentCard from '@app/Custom/CommentCard'

export interface MappingCommentModalProps {
  api
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
  api,
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
  const [commentToEdit, setCommentToEdit] = React.useState<any>({})
  const [messageValue, setMessageValue] = React.useState<string>('')

  const auth = useAuth()

  const handleModalToggle = () => {
    const new_state = !modalShowState
    setModalShowState(new_state)
    setIsModalOpen(new_state)
    if (!new_state) {
      setMessageValue('')
    }
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
    let url = Constants.API_BASE_URL + '/comments'
    url += '?parent_table=' + parent_table
    url += '&parent_id=' + parent_id
    url += '&api-id=' + api.id

    if (auth.isLogged()) {
      url += '&user-id=' + auth.userId
      url += '&token=' + auth.token
    }

    fetch(url)
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
      <CommentCard
        key={'comment-card-' + comment.id}
        api={api}
        comment={comment}
        setCommentToEdit={setCommentToEdit}
        loadComments={loadComments}
        editEnabled={comment.created_by_id == auth.userId}
        parentType={parentType}
        relationData={relationData}
        workItemType={workItemType}
        setMessageValue={setMessageValue}
      />
    ))
  }

  return (
    <React.Fragment>
      <Modal
        width='90%'
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
              <Td width={50}>
                <Panel isScrollable>
                  <PanelMain tabIndex={0}>
                    <PanelMainBody>{getComments()}</PanelMainBody>
                  </PanelMain>
                </Panel>
              </Td>
              <Td width={50}>
                <CommentForm
                  api={api}
                  commentToEdit={commentToEdit}
                  setCommentToEdit={setCommentToEdit}
                  handleModalToggle={handleModalToggle}
                  loadComments={loadComments}
                  loadMappingData={loadMappingData}
                  parentType={parentType}
                  relationData={relationData}
                  workItemType={workItemType}
                  messageValue={messageValue}
                  setMessageValue={setMessageValue}
                />
              </Td>
            </Tr>
          </Tbody>
        </Table>
      </Modal>
    </React.Fragment>
  )
}
