import React from 'react'
import { Form, FormGroup, FormHelperText, HelperText, HelperTextItem, TextArea, TextInput } from '@patternfly/react-core'

export interface TestRunFormProps {
  titleValue
  noteValue
  validatedTitleValue
  handleTitleValueChange
  handleNoteValueChange
}

export const TestRunForm: React.FunctionComponent<TestRunFormProps> = ({
  titleValue,
  noteValue,
  validatedTitleValue,
  handleTitleValueChange,
  handleNoteValueChange
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
      <FormGroup label='Note' fieldId={`input-test-run-add-note`}>
        <TextArea
          resizeOrientation='vertical'
          aria-label='Test Run Note field'
          id={`input-test-run-add-note`}
          name={`input-test-run-add-note`}
          value={noteValue || ''}
          onChange={(_ev, value) => handleNoteValueChange(value)}
        />
      </FormGroup>
    </Form>
  )
}
