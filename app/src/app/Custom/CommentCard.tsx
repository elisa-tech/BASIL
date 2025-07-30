import React from 'react'
import { Card, CardHeader, CardBody, Text, TextVariants, Button, Flex, Tooltip } from '@patternfly/react-core'
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

      fetch(Constants.API_BASE_URL + '/comments', {
        method: 'DELETE',
        headers: Constants.JSON_HEADER,
        body: JSON.stringify(data)
      })
        .then((response) => {
          if (response.status !== 200) {
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
    </Card>
  )
}

export default CommentCard
