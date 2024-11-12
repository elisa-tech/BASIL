import React from 'react'
import { Form, FormGroup, FormHelperText, HelperText, HelperTextItem, TextArea, TextInput } from '@patternfly/react-core'

export interface TestRunFormProps {
  titleValue
  notesValue
  validatedTitleValue
  handleTitleValueChange
  handleNotesValueChange
}

export const TestRunForm: React.FunctionComponent<TestRunFormProps> = ({
  titleValue,
  notesValue,
  validatedTitleValue,
  handleTitleValueChange,
  handleNotesValueChange
}: TestRunFormProps) => {
  return (
    <Form>
      <FormGroup label='Test Run Title' isRequired fieldId={`input-test-run-add-title`}>
        <TextInput
          isRequired
          id={`input-test-run-add-title`}
          name={`input-test-run-add-title`}
          value={titleValue || ''}
          onChange={(_ev, value) => handleTitleValueChange(value)}
        />
        {validatedTitleValue !== 'success' && (
          <FormHelperText>
            <HelperText>
              <HelperTextItem variant='error'>{validatedTitleValue === 'error' ? 'This field is mandatory' : ''}</HelperTextItem>
            </HelperText>
          </FormHelperText>
        )}
      </FormGroup>
      <FormGroup label='Notes' fieldId={`input-test-run-add-notes`}>
        <TextArea
          resizeOrientation='vertical'
          aria-label='Test Run Notes field'
          id={`input-test-run-add-notes`}
          name={`input-test-run-add-notes`}
          value={notesValue || ''}
          onChange={(_ev, value) => handleNotesValueChange(value)}
        />
      </FormGroup>
    </Form>
  )
}
