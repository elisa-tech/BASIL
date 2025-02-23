import React from 'react'
import * as Constants from '@app/Constants/constants'
import {
  ActionGroup,
  Button,
  Flex,
  FlexItem,
  Form,
  FormGroup,
  FormHelperText,
  HelperText,
  HelperTextItem,
  Hint,
  HintBody,
  TextArea
} from '@patternfly/react-core'
import { useAuth } from '@app/User/AuthProvider'

export interface CommentFormProps {
  relationData
  workItemType
  parentType
  handleModalToggle
  loadComments
  loadMappingData
}

export const CommentForm: React.FunctionComponent<CommentFormProps> = ({
  relationData,
  workItemType,
  parentType,
  handleModalToggle,
  loadComments,
  loadMappingData
}: CommentFormProps) => {
  const auth = useAuth()
  const [commentValue, setCommentValue] = React.useState('')
  const [validatedCommentValue, setValidatedCommentValue] = React.useState<Constants.validate>('error')

  const [messageValue, setMessageValue] = React.useState('')
  const [statusValue, setStatusValue] = React.useState('waiting')

  const resetForm = () => {
    setCommentValue('')
  }

  React.useEffect(() => {
    if (commentValue.trim() === '') {
      setValidatedCommentValue('error')
    } else {
      setValidatedCommentValue('success')
    }
  }, [commentValue])

  React.useEffect(() => {
    if (statusValue == 'submitted') {
      handleSubmit()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [statusValue])

  const handleCommentValueChange = (_event, value: string) => {
    setCommentValue(value)
  }

  const handleSubmit = () => {
    let parent_table = Constants.getMappingTableName(workItemType, parentType)
    const parent_id = relationData.relation_id

    if (validatedCommentValue != 'success') {
      setMessageValue('Comment is mandatory.')
      setStatusValue('waiting')
      return
    }

    if (parent_table == '' || parent_id == '') {
      setMessageValue('Wrong Data')
      setStatusValue('waiting')
      return
    }

    setMessageValue('')

    const data = {
      parent_table: parent_table,
      parent_id: parent_id,
      comment: commentValue,
      'user-id': auth.userId,
      token: auth.token
    }

    fetch(Constants.API_BASE_URL + '/comments', {
      method: 'POST',
      headers: Constants.JSON_HEADER,
      body: JSON.stringify(data)
    })
      .then((response) => {
        if (response.status !== 200) {
          setMessageValue(response.statusText)
          setStatusValue('waiting')
        } else {
          loadComments(parent_table, parent_id)
          loadMappingData(Constants.force_reload)
          setMessageValue('Comment saved')
          setStatusValue('waiting')
          setCommentValue('')
          focusInputComment()
        }
      })
      .catch((err) => {
        setMessageValue(err.toString())
        setStatusValue('waiting')
      })
  }

  // Form elements focus
  const focusInputComment = () => {
    document.getElementById('input-comment-comment')?.focus()
  }

  // Keyboard events
  const handleCommentKeyUp = (event) => {
    if (event.key === 'Enter' && event.shiftKey) {
      handleSubmit()
    }
  }

  return (
    <Form
      onSubmit={(event) => {
        event.preventDefault()
      }}
    >
      <FormGroup label='Comment' isRequired fieldId={`input-comment-comment`}>
        <TextArea
          isRequired
          resizeOrientation='vertical'
          aria-label='Comment comment field'
          id={`input-comment-comment`}
          value={commentValue || ''}
          onChange={(_ev, value) => handleCommentValueChange(_ev, value)}
          onKeyUp={handleCommentKeyUp}
        />
        {validatedCommentValue !== 'success' && (
          <FormHelperText>
            <HelperText>
              <HelperTextItem variant='error'>{validatedCommentValue === 'error' ? 'This field is mandatory' : ''}</HelperTextItem>
            </HelperText>
          </FormHelperText>
        )}
      </FormGroup>

      {messageValue ? (
        <>
          <Hint>
            <HintBody>{messageValue}</HintBody>
          </Hint>
          <br />
        </>
      ) : (
        ''
      )}

      <ActionGroup>
        <Flex>
          <FlexItem>
            <Button variant='primary' onClick={() => setStatusValue('submitted')}>
              Submit
            </Button>
          </FlexItem>
          <FlexItem>
            <Button variant='secondary' onClick={resetForm}>
              Reset
            </Button>
          </FlexItem>
        </Flex>
      </ActionGroup>
    </Form>
  )
}
