import React from 'react';
import {
  Button,
  CodeBlock,
  CodeBlockCode,
  FormGroup,
  FormHelperText,
  HelperText,
  HelperTextItem,
  TextArea,
  TextInput,
} from '@patternfly/react-core';
export interface SectionFormProps {
  api;
  modalOffset;
  modalSection;
  setModalOffset;
  setModalSection;
}

export const SectionForm: React.FunctionComponent<SectionFormProps> = ({
  api,
  modalOffset,
  modalSection,
  setModalOffset,
  setModalSection,
    }: SectionFormProps) => {

    type validate = 'success' | 'warning' | 'error' | 'default';

    const [sectionValue, setSectionValue] = React.useState(modalSection == undefined ? '' : modalSection);
    const [validatedSectionValue, setValidatedSectionValue] = React.useState<validate>('error');

    const [offsetValue, setOffsetValue] = React.useState(modalOffset == undefined ? 0 : modalOffset);
    const [validatedOffsetValue, setValidatedOffsetValue] = React.useState<validate>('error');

    React.useEffect(() => {
      if (sectionValue.trim() === '') {
          setValidatedSectionValue('error');
        } else {
          setValidatedSectionValue('success');
        }
    }, [sectionValue]);

    React.useEffect(() => {
        if (offsetValue === '') {
          setValidatedOffsetValue('default');
        } else if (/^\d+$/.test(offsetValue)) {
          if ((offsetValue >= 0) && (offsetValue <= api['raw_specification'].length)){
            setValidatedOffsetValue('success');
          } else {
            setValidatedOffsetValue('error');
          }
        } else {
          setValidatedOffsetValue('error');
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [offsetValue]);

    const handleSectionValueChange = () => {
      if (getSelection().toString() != ''){
        if (getSelection().anchorNode.parentNode.id == "input-raw-specification"){
          setModalSection(getSelection().toString());
          setModalOffset(Math.min(getSelection().baseOffset, getSelection().extentOffset));
          setSectionValue(getSelection().toString());
          setOffsetValue(Math.min(getSelection().baseOffset, getSelection().extentOffset));
        }
      }
    }

    const setSectionAsUnmatching = () => {
      const unmatching_section = '?????????';
      const unmatching_offset = 0;
      setSectionValue(unmatching_section);
      setModalSection(unmatching_section);
      setOffsetValue(unmatching_offset);
      setModalOffset(unmatching_offset);
    }

    return (
        <React.Fragment>
          <FormGroup label="Section" fieldId={`input-justification-section`}>
            <TextArea
              isDisabled
              resizeOrientation="vertical"
              aria-label="Section preview field"
              id={`input-justification-section`}
              name={`input-justification-section`}
              value={sectionValue || ''}
              onChange={(_ev, value) => handleSectionValueChange(_ev, value)}
            />
            {validatedSectionValue !== 'success' && (
              <FormHelperText>
                <HelperText>
                  <HelperTextItem variant={validatedSectionValue}>
                    {validatedSectionValue === 'error' ? 'This field is mandatory' : ''}
                  </HelperTextItem>
                </HelperText>
              </FormHelperText>
            )}
          </FormGroup>

          <FormGroup label="Offset" fieldId={`input-justification-offset`}>
            <TextInput
              isDisabled
              id={`input-justification-offset`}
              name={`input-justification-offset`}
              value={offsetValue}
              onChange={(_ev, value) => handleOffsetValueChange(_ev, value)}
            />
            {validatedOffsetValue !== 'success' && (
              <FormHelperText>
                <HelperText>
                  <HelperTextItem variant={validatedOffsetValue}>
                    {validatedOffsetValue === 'error' ? 'Must be an integer number' : ''}
                  </HelperTextItem>
                </HelperText>
              </FormHelperText>
            )}
          </FormGroup>

          <Button
            id="btn-section-set-unmatching"
            variant="link"
            onClick={setSectionAsUnmatching}>
            Set as unmatching
          </Button>

          <CodeBlock className="code-block-bg-green">
            <CodeBlockCode>
              <div onMouseUp={handleSectionValueChange} id={"input-raw-specification"} data-offset={offsetValue}>
              {api['raw_specification']}
              </div>
            </CodeBlockCode>
          </CodeBlock>

      </React.Fragment>
   );
};
