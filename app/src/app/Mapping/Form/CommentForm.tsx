import React from 'react'
import * as Constants from '../../Constants/constants'
import {
  ActionGroup,
  Button,
  Form,
  FormGroup,
  FormHelperText,
  HelperText,
  HelperTextItem,
  Hint,
  HintBody,
  TextArea
} from '@patternfly/react-core'
import { useAuth } from '../../User/AuthProvider'

export interface CommentFormProps {
  relationData
  workItemType
  parentType
  handleModalToggle
  loadMappingData
}

export const CommentForm: React.FunctionComponent<CommentFormProps> = ({
  relationData,
  workItemType,
  parentType,
  handleModalToggle,
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
    let parent_table = ''
    let parent_id = ''

    if (validatedCommentValue != 'success') {
      setMessageValue('Comment is mandatory.')
      setStatusValue('waiting')
      return
    }

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
      headers: {
        Accept: 'application/json',
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(data)
    })
      .then((response) => {
        if (response.status !== 200) {
          setMessageValue(response.statusText)
          setStatusValue('waiting')
        } else {
          loadMappingData(Constants.force_reload)
          handleModalToggle()
          setMessageValue('')
          setStatusValue('waiting')
        }
      })
      .catch((err) => {
        setMessageValue(err.toString())
        setStatusValue('waiting')
      })
  }

  return (
    <Form>
      <FormGroup label='Comment' isRequired fieldId={`input-comment-comment`}>
        <TextArea
          isRequired
          resizeOrientation='vertical'
          aria-label='Comment comment field'
          id={`input-comment-comment`}
          name={`input-comment-comment`}
          value={commentValue || ''}
          onChange={(_ev, value) => handleCommentValueChange(_ev, value)}
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
        <Button variant='primary' onClick={() => setStatusValue('submitted')}>
          Submit
        </Button>
        <Button variant='secondary' onClick={resetForm}>
          Reset
        </Button>
      </ActionGroup>
    </Form>
  )
}
