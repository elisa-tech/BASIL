import React from 'react'
import * as Constants from '../../Constants/constants'
import {
  Button,
  CodeBlock,
  CodeBlockCode,
  FormGroup,
  FormHelperText,
  HelperText,
  HelperTextItem,
  TextArea,
  TextInput
} from '@patternfly/react-core'
export interface SectionFormProps {
  api
  modalOffset
  modalSection
  setModalOffset
  setModalSection
}

export const SectionForm: React.FunctionComponent<SectionFormProps> = ({
  api,
  modalOffset,
  modalSection,
  setModalOffset,
  setModalSection
}: SectionFormProps) => {
  const [sectionValue, setSectionValue] = React.useState(modalSection == undefined ? '' : modalSection)
  const [validatedSectionValue, setValidatedSectionValue] = React.useState<Constants.validate>('error')

  const [offsetValue, setOffsetValue] = React.useState(modalOffset == undefined ? 0 : modalOffset)
  const [validatedOffsetValue, setValidatedOffsetValue] = React.useState<Constants.validate>('error')

  React.useEffect(() => {
    if (sectionValue.trim() === '') {
      setValidatedSectionValue('error')
    } else {
      setValidatedSectionValue('success')
    }
  }, [sectionValue])

  React.useEffect(() => {
    if (offsetValue === '') {
      setValidatedOffsetValue('default')
    } else if (/^\d+$/.test(offsetValue)) {
      if (offsetValue >= 0 && offsetValue <= api['raw_specification'].length) {
        setValidatedOffsetValue('success')
      } else {
        setValidatedOffsetValue('error')
      }
    } else {
      setValidatedOffsetValue('error')
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [offsetValue])

  const handleSectionValueChange = () => {
    const currentSelection = getSelection()?.toString() as string | ''
    if (currentSelection != '') {
      // eslint-disable-next-line  @typescript-eslint/no-explicit-any
      if (((getSelection()?.anchorNode?.parentNode as any)?.id as string | '') == 'input-raw-specification') {
        const currentOffset = Constants.getSelectionOffset()
        if (currentOffset > -1) {
          setModalSection(currentSelection)
          setSectionValue(currentSelection)
          setModalOffset(currentOffset)
          setOffsetValue(currentOffset)
        }
      }
    }
  }

  const setSectionAsUnmatching = () => {
    const unmatching_section = '?????????'
    const unmatching_offset = 0
    setSectionValue(unmatching_section)
    setModalSection(unmatching_section)
    setOffsetValue(unmatching_offset)
    setModalOffset(unmatching_offset)
  }

  const setSectionAsFullDocument = () => {
    setSectionValue(api['raw_specification'])
    setModalSection(api['raw_specification'])
    setOffsetValue(0)
    setModalOffset(0)
  }

  return (
    <React.Fragment>
      <FormGroup label='Section' fieldId={`input-mapping-section`}>
        <TextArea
          isDisabled
          resizeOrientation='vertical'
          aria-label='Section preview field'
          id={`input-mapping-section`}
          rows={8}
          value={sectionValue}
          onChange={() => handleSectionValueChange()}
        />
        {validatedSectionValue !== 'success' && (
          <FormHelperText>
            <HelperText>
              <HelperTextItem variant='error'>{validatedSectionValue === 'error' ? 'This field is mandatory' : ''}</HelperTextItem>
            </HelperText>
          </FormHelperText>
        )}
      </FormGroup>
      <FormGroup label='Offset' fieldId={`input-mapping-offset`}>
        <TextInput isDisabled id={`input-mapping-offset`} value={offsetValue} />
        {validatedOffsetValue !== 'success' && (
          <FormHelperText>
            <HelperText>
              <HelperTextItem variant='error'>{validatedOffsetValue === 'error' ? 'Must be an integer number' : ''}</HelperTextItem>
            </HelperText>
          </FormHelperText>
        )}
      </FormGroup>
      <Button id='btn-section-set-unmatching' variant='link' onClick={() => setSectionAsUnmatching()}>
        Set as unmatching
      </Button>
      |
      <Button id='btn-section-set-full-document' variant='link' onClick={() => setSectionAsFullDocument()}>
        Set as Full Document
      </Button>
      <CodeBlock className='code-block-bg-green code-fixed-height'>
        <CodeBlockCode>
          <div onMouseUp={() => handleSectionValueChange()} id={'input-raw-specification'} data-offset={offsetValue}>
            {api['raw_specification']}
          </div>
        </CodeBlockCode>
      </CodeBlock>
    </React.Fragment>
  )
}
