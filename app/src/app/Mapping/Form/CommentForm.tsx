import React from 'react';
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
  TextArea,
  TextInput,
} from '@patternfly/react-core';

export interface CommentFormProps {
  baseApiUrl: str;
  relationData;
  workItemType;
  parentType;
  handleModalToggle;
  loadMappingData;
}

export const CommentForm: React.FunctionComponent<CommentFormProps> = ({
  baseApiUrl,
  relationData,
  workItemType,
  parentType,
  handleModalToggle,
  loadMappingData,
    }: CommentFormProps) => {

    type validate = 'success' | 'warning' | 'error' | 'default';

    const [usernameValue, setUsernameValue] = React.useState('');
    const [validatedUsernameValue, setValidatedUsernameValue] = React.useState<validate>('error');

    const [commentValue, setCommentValue] = React.useState('');
    const [validatedCommentValue, setValidatedCommentValue] = React.useState<validate>('error');

    const [messageValue, setMessageValue] = React.useState();
    const [statusValue, setStatusValue] = React.useState('waiting');

    const _A = 'api';
    const _J = 'justification';
    const _M_ = '_mapping_';
    const _SR = 'sw-requirement';
    const _SR_ = 'sw_requirement';
    const _TS = 'test-specification';
    const _TS_ = 'test_specification';
    const _TC = 'test-case';
    const _TC_ = 'test_case';

    const resetForm = () => {
        setCommentValue("");
        setUsernameValue("");
    }

    React.useEffect(() => {
      if (usernameValue.trim() === '') {
          setValidatedUsernameValue('error');
        } else {
          setValidatedUsernameValue('success');
        }
    }, [usernameValue]);

    React.useEffect(() => {
      if (commentValue.trim() === '') {
          setValidatedCommentValue('error');
        } else {
          setValidatedCommentValue('success');
        }
    }, [commentValue]);


    React.useEffect(() => {
        if (statusValue == 'submitted'){
          handleSubmit();
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [statusValue]);

    const handleCommentValueChange = (_event, value: string) => {
        setCommentValue(value);
    };

    const handleUsernameValueChange = (_event, value: string) => {
        setUsernameValue(value);
    };

    const handleSubmit = () => {
        let parent_table = '';
        let parent_id = '';

        if (validatedCommentValue != 'success'){
            setMessageValue('Comment is mandatory.');
            setStatusValue('waiting');
            return;
        } else if (validatedUsernameValue != 'success'){
            setMessageValue('Username is mandatory.');
            setStatusValue('waiting');
            return;
        }

        if (workItemType == _J){
          if (parentType == _A){
            parent_table = _J + _M_ + _A;
            parent_id = relationData.relation_id;
          }
        }  else if (workItemType == _SR) {
          if (parentType == _A){
            parent_table = _SR_ + _M_ + _A;
            parent_id = relationData.relation_id;
          }
        } else if (workItemType == _TS) {
          if (parentType == _A){
            parent_table = _TS_ + _M_ + _A;
            parent_id = relationData.relation_id;
          }
        } else if (workItemType == _TC) {
          if (parentType == _A){
            parent_table = _TC_ + _M_ + _A;
            parent_id = relationData.relation_id;
          }
        }

        if ((parent_table == '') || (parent_id == '')){
          setMessageValue('Wrong Data');
          setStatusValue('waiting');
          return;
        }

        setMessageValue('');

        const data = {
          'parent_table': parent_table,
          'parent_id': parent_id,
          'comment': commentValue,
          'username': usernameValue,
        }

        fetch(baseApiUrl + '/comments', {
          method: 'POST',
          headers: {
            Accept: 'application/json',
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(data),
        })
          .then((response) => {
            if (response.status !== 200) {
              setMessageValue(response.statusText);
              setStatusValue('waiting');
            } else {
              loadMappingData();
              handleModalToggle();
              setMessageValue('');
              setStatusValue('waiting');
            }
          })
          .catch((err) => {
            setMessageValue(err.toString());
            setStatusValue('waiting');
          });
      };

    return (
        <Form>
          <FormGroup label="Username:" isRequired fieldId={`input-comment-username`}>
            <TextInput
              isRequired
              id={`input-comment-username`}
              name={`input-comment-username`}
              value={usernameValue || ''}
              onChange={(_ev, value) => handleUsernameValueChange(_ev, value)}
            />
            {validatedUsernameValue !== 'success' && (
              <FormHelperText>
                <HelperText>
                  <HelperTextItem variant={validatedUsernameValue}>
                    {validatedUsernameValue === 'error' ? 'This field is mandatory' : ''}
                  </HelperTextItem>
                </HelperText>
              </FormHelperText>
            )}
          </FormGroup>

          <FormGroup label="Comment" isRequired fieldId={`input-comment-comment`}>
            <TextArea
              isRequired
              resizeOrientation="vertical"
              aria-label="Comment comment field"
              id={`input-comment-comment`}
              name={`input-comment-comment`}
              value={commentValue || ''}
              onChange={(_ev, value) => handleCommentValueChange(_ev, value)}
            />
            {validatedCommentValue !== 'success' && (
              <FormHelperText>
                <HelperText>
                  <HelperTextItem variant={validatedCommentValue}>
                    {validatedCommentValue === 'error' ? 'This field is mandatory' : ''}
                  </HelperTextItem>
                </HelperText>
              </FormHelperText>
            )}
          </FormGroup>

          { messageValue ? (
          <Hint>
            <HintBody>
              {messageValue}
            </HintBody>
          </Hint>
          ) : (<span></span>)}

          <ActionGroup>
            <Button
              variant="primary"
              onClick={() => setStatusValue('submitted')}>
            Submit
            </Button>
            <Button
              variant="secondary"
              onClick={resetForm}>
              Reset
            </Button>
          </ActionGroup>

        </Form>
   );
};
