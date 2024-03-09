import React from 'react'
import * as Constants from '../../Constants/constants'
import { ActionGroup, Button, Form, FormGroup, Hint, HintBody, TextArea, TextInput } from '@patternfly/react-core'
import { useAuth } from '../../User/AuthProvider'

export interface TestRunBugFormProps {
  api
  modalTestRun
  modalRelationData
  parentType
}

export const TestRunBugForm: React.FunctionComponent<TestRunBugFormProps> = ({
  api,
  modalTestRun,
  modalRelationData,
  parentType
}: TestRunBugFormProps) => {
  const auth = useAuth()
  const [bugsValue, setBugsValue] = React.useState(modalTestRun.bugs)
  const [noteValue, setNoteValue] = React.useState(modalTestRun.note)
  const [messageValue, setMessageValue] = React.useState('')

  const handleBugsValueChange = (value: string) => {
    setBugsValue(value)
  }

  const handleNoteValueChange = (value: string) => {
    setNoteValue(value)
  }

  React.useEffect(() => {
    setBugsValue(modalTestRun.bugs)
    setNoteValue(modalTestRun.note)
  }, [modalTestRun])

  const handleSubmit = () => {
    if (modalTestRun.id == null) {
      setMessageValue('Select a Test Run')
      return
    }

    const mapping_to = Constants._TC_ + Constants._M_ + parentType.replaceAll('-', '_')
    const mapping_id = modalRelationData['relation_id']
    setMessageValue('')

    const data = {
      'api-id': api.id,
      id: modalTestRun.id,
      bugs: bugsValue.trim(),
      note: noteValue.trim(),
      'user-id': auth.userId,
      token: auth.token,
      mapped_to_type: mapping_to,
      mapped_to_id: mapping_id
    }

    fetch(Constants.API_BASE_URL + '/mapping/api/test-runs', {
      method: 'PUT',
      headers: {
        Accept: 'application/json',
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(data)
    })
      .then((response) => {
        if (response.status !== 200) {
          setMessageValue(response.statusText)
        } else {
          setMessageValue('')
        }
      })
      .catch((err) => {
        setMessageValue(err.toString())
      })
  }

  return (
    <Form>
      <FormGroup label='Bug' isRequired fieldId={`input-test-run-bug-bugs`}>
        <TextInput
          isRequired
          aria-label='Test Run Bug Bug field'
          id={`input-test-run-bug-bugs`}
          name={`input-test-run-bug-bugs`}
          value={bugsValue || ''}
          onChange={(_ev, value) => handleBugsValueChange(value)}
        />
      </FormGroup>
      <FormGroup label='Note' fieldId={`input-test-run-bug-note`}>
        <TextArea
          resizeOrientation='vertical'
          aria-label='Test Run Bug Note field'
          id={`input-test-run-bug-note`}
          name={`input-test-run-bug-note`}
          value={noteValue || ''}
          onChange={(_ev, value) => handleNoteValueChange(value)}
        />
      </FormGroup>
      <ActionGroup>
        <Button id='btn-test-run-bug-submit' variant='primary' onClick={() => handleSubmit()}>
          Save
        </Button>
      </ActionGroup>

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
    </Form>
  )
}
