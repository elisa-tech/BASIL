import React from 'react'
import { Badge, Card, CardHeader, CardBody, Text, TextVariants, Button, Flex, Tooltip, CardFooter } from '@patternfly/react-core'
import * as Constants from '@app/Constants/constants'
import { PencilAltIcon, TrashIcon } from '@patternfly/react-icons'
import ReactMarkdown from 'react-markdown'
import { useAuth } from '@app/User/AuthProvider'

const CommentCard = ({
  api,
  parentType,
  relationData,
  workItemType,
  loadComments,
  comment,
  editEnabled,
  setCommentToEdit,
  setMessageValue
}) => {
  const [deleteEnabled, setDeleteEnabled] = React.useState(false)
  const currentUserStyle = {
    color: 'var(--pf-v5-global--info-color--100)'
  }

  const postedStyle = {
    fontSize: '0.75rem',
    marginRight: '1rem'
  }

  const modifiedStyle = {
    fontSize: '0.75rem',
    color: 'var(--pf-v5-global--info-color--200)',
    fontWeight: 600
  }

  const auth = useAuth()

  const handleDelete = () => {
    if (deleteEnabled) {
      let parent_table = Constants.getMappingTableName(workItemType, parentType)
      const parent_id = relationData.relation_id

      if (parent_table == '' || parent_id == '') {
        setMessageValue('Wrong Data')
        return
      }

      const data = {
        'api-id': api.id,
        parent_table: parent_table,
        parent_id: parent_id,
        comment_id: comment.id,
        'user-id': auth.userId,
        token: auth.token
      }

      fetch(Constants.API_BASE_URL + Constants.API_COMMENTS_ENDPOINT, {
        method: 'DELETE',
        headers: Constants.JSON_HEADER,
        body: JSON.stringify(data)
      })
        .then((response) => {
          if (!Constants.isHttpSuccessStatus(response.status)) {
            setMessageValue(response.statusText)
          } else {
            loadComments(parent_table, parent_id)
            setMessageValue('Comment deleted')
          }
        })
        .catch((err) => {
          setMessageValue(err.toString())
        })
    } else {
      setDeleteEnabled(true)
    }
  }

  const handleTodoChange = (done: boolean) => {
    let parent_table = Constants.getMappingTableName(workItemType, parentType)
    const parent_id = relationData.relation_id

    const data = {
      'api-id': api.id,
      parent_table: parent_table,
      parent_id: parent_id,
      comment: comment.comment,
      todo: comment.todo,
      comment_id: comment.id,
      done: done ? 'true' : 'false',
      'user-id': auth.userId,
      token: auth.token
    }

    fetch(Constants.API_BASE_URL + Constants.API_COMMENTS_ENDPOINT, {
      method: 'PUT',
      headers: Constants.JSON_HEADER,
      body: JSON.stringify(data)
    })
      .then((response) => {
        if (!Constants.isHttpSuccessStatus(response.status)) {
          setMessageValue(response.statusText)
        } else {
          loadComments(parent_table, parent_id)
          setMessageValue('Todo marked as done')
        }
      })
      .catch((err) => {
        setMessageValue(err.toString())
      })
  }

  return (
    <Card isCompact isFlat>
      <CardHeader>
        <Flex justifyContent={{ default: 'justifyContentSpaceBetween' }} alignItems={{ default: 'alignItemsFlexStart' }}>
          <Flex direction={{ default: 'column' }}>
            <Text style={comment.created_by_id == auth.userId ? currentUserStyle : {}} component={TextVariants.h5}>
              {comment.created_by}
            </Text>
            <Flex>
              <Text component={TextVariants.small} style={postedStyle}>
                Posted on: {new Date(comment.created_at).toLocaleString()}
              </Text>
              {comment.created_at != comment.updated_at && (
                <Text component={TextVariants.small} style={modifiedStyle}>
                  Modified on: {new Date(comment.updated_at).toLocaleString()}
                </Text>
              )}
            </Flex>
          </Flex>
          {editEnabled ? (
            <Flex spaceItems={{ default: 'spaceItemsMd' }}>
              <Tooltip content='Edit comment'>
                <Button variant='plain' onClick={() => setCommentToEdit(comment)} aria-label='Edit comment'>
                  <PencilAltIcon />
                </Button>
              </Tooltip>
              <Tooltip content='Delete comment'>
                <Button variant='plain' aria-label='Delete comment' onClick={() => handleDelete()}>
                  <TrashIcon />
                  {deleteEnabled ? <Text component={TextVariants.p}>Confirm</Text> : ''}
                </Button>
              </Tooltip>
            </Flex>
          ) : (
            ''
          )}
        </Flex>
      </CardHeader>
      <CardBody>
        <ReactMarkdown>{comment.comment}</ReactMarkdown>
      </CardBody>
      <CardFooter>
        <Flex fullWidth={{ default: 'fullWidth' }} justifyContent={{ default: 'justifyContentFlexEnd' }}>
          {comment.todo && (
            <Flex spaceItems={{ default: 'spaceItemsSm' }} alignItems={{ default: 'alignItemsCenter' }}>
              {!comment.done ? (
                <React.Fragment>
                  <Badge
                    screenReaderText='TODO'
                    style={{
                      backgroundColor: 'var(--pf-v5-global--palette--orange-200)',
                      color: 'var(--pf-v5-global--palette--orange-700)'
                    }}
                  >
                    TODO
                  </Badge>
                  <Button variant='link' onClick={() => handleTodoChange(true)}>
                    Mark as done
                  </Button>
                </React.Fragment>
              ) : (
                <React.Fragment>
                  <Badge
                    screenReaderText='Done'
                    style={{
                      backgroundColor: 'var(--pf-v5-global--palette--green-100)',
                      color: 'var(--pf-v5-global--palette--green-700)',
                      whiteSpace: 'normal',
                      textAlign: 'left'
                    }}
                  >
                    Done by {comment.done_by} on {new Date(comment.done_at).toLocaleString()}
                  </Badge>
                  <Button variant='link' onClick={() => handleTodoChange(false)}>
                    Mark as not done
                  </Button>
                </React.Fragment>
              )}
            </Flex>
          )}
        </Flex>
      </CardFooter>
    </Card>
  )
}

export default CommentCard
