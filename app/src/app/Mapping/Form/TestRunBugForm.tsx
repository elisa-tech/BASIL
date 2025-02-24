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
  const [bugsValue, setBugsValue] = React.useState(modalTestRun?.bugs || '')
  const [fixesValue, setFixesValue] = React.useState(modalTestRun?.fixes || '')
  const [notesValue, setNotesValue] = React.useState(modalTestRun?.notes || '')
  const [messageValue, setMessageValue] = React.useState('')

  const handleBugsValueChange = (value: string) => {
    setBugsValue(value)
  }

  const handleFixesValueChange = (value: string) => {
    setFixesValue(value)
  }

  const handleNotesValueChange = (value: string) => {
    setNotesValue(value)
  }

  React.useEffect(() => {
    setBugsValue(modalTestRun.bugs)
    setFixesValue(modalTestRun.fixes)
    setNotesValue(modalTestRun.notes)
  }, [modalTestRun])

  const handleSubmit = () => {
    if (api?.permissions.indexOf('w') < 0) {
      return
    }
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
      bugs: Constants._trim(bugsValue),
      fixes: Constants._trim(fixesValue),
      notes: Constants._trim(notesValue),
      'user-id': auth.userId,
      token: auth.token,
      mapped_to_type: mapping_to,
      mapped_to_id: mapping_id
    }

    fetch(Constants.API_BASE_URL + '/mapping/api/test-runs', {
      method: 'PUT',
      headers: Constants.JSON_HEADER,
      body: JSON.stringify(data)
    })
      .then((response) => {
        if (response.status !== 200) {
          setMessageValue(response.statusText)
        } else {
          setMessageValue('SAVED')
        }
      })
      .catch((err) => {
        setMessageValue(err.toString())
      })
  }

  return (
    <Form>
      <FormGroup label='Bugs' fieldId={`input-test-run-bugs`}>
        <TextInput
          isDisabled={api?.permissions.indexOf('w') < 0}
          aria-label='Test Run Bugs field'
          id={`input-test-run-bugs`}
          name={`input-test-run-bugs`}
          value={bugsValue || ''}
          onChange={(_ev, value) => handleBugsValueChange(value)}
        />
      </FormGroup>
      <FormGroup label='Fixes' fieldId={`input-test-run-fixes`}>
        <TextInput
          isDisabled={api?.permissions.indexOf('w') < 0}
          aria-label='Test Run Fixes'
          id={`input-test-run-fixes`}
          name={`input-test-run-fixes`}
          value={fixesValue || ''}
          onChange={(_ev, value) => handleFixesValueChange(value)}
        />
      </FormGroup>
      <FormGroup label='Notes' fieldId={`input-test-run-notes`}>
        <TextArea
          isDisabled={api?.permissions.indexOf('w') < 0}
          resizeOrientation='vertical'
          aria-label='Test Run Notes field'
          id={`input-test-run-notes`}
          name={`input-test-run-notes`}
          value={notesValue || ''}
          onChange={(_ev, value) => handleNotesValueChange(value)}
        />
      </FormGroup>

      {api?.permissions.indexOf('w') >= 0 ? (
        <ActionGroup>
          <Button id='btn-test-run-bug-submit' variant='primary' onClick={() => handleSubmit()}>
            Save
          </Button>
        </ActionGroup>
      ) : (
        ''
      )}

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
