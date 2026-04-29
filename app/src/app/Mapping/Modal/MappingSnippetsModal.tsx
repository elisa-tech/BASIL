import React from 'react'
import * as Constants from '@app/Constants/constants'
import {
  Button,
  Card,
  CardBody,
  CodeBlock,
  CodeBlockCode,
  Divider,
  Flex,
  FlexItem,
  FormGroup,
  Hint,
  HintBody,
  Label,
  Modal,
  ModalVariant,
  Text,
  TextContent,
  TextVariants,
  Title
} from '@patternfly/react-core'
import TrashIcon from '@patternfly/react-icons/dist/esm/icons/trash-icon'
import PlusCircleIcon from '@patternfly/react-icons/dist/esm/icons/plus-circle-icon'
import { useAuth } from '../../User/AuthProvider'

export interface MappingSnippetsModalProps {
  api
  modalShowState: boolean
  setModalShowState
  workItemGroup
  workItemType
  loadMappingData
}

export const MappingSnippetsModal: React.FunctionComponent<MappingSnippetsModalProps> = ({
  api,
  modalShowState = false,
  setModalShowState,
  workItemGroup,
  workItemType,
  loadMappingData
}: MappingSnippetsModalProps) => {
  const auth = useAuth()
  const [isModalOpen, setIsModalOpen] = React.useState(false)
  const [messageValue, setMessageValue] = React.useState('')
  const [addingSnippet, setAddingSnippet] = React.useState(false)
  const [newSection, setNewSection] = React.useState('')
  const [newOffset, setNewOffset] = React.useState(0)

  const handleModalToggle = () => {
    const new_state = !modalShowState
    setModalShowState(new_state)
    setIsModalOpen(new_state)
  }

  React.useEffect(() => {
    setIsModalOpen(modalShowState)
    if (modalShowState === false) {
      setMessageValue('')
      setAddingSnippet(false)
      setNewSection('')
      setNewOffset(0)
    }
  }, [modalShowState])

  if (!workItemGroup || !workItemType) {
    return null
  }

  const snippets = workItemGroup.snippets || []

  const getWorkItemLabel = () => {
    const typeLabels = {
      [Constants._SR]: 'Software Requirement',
      [Constants._TS]: 'Test Specification',
      [Constants._TC]: 'Test Case',
      [Constants._J]: 'Justification',
      [Constants._D]: 'Document'
    }
    const wiKey = workItemType.replace('-', '_')
    const wi = workItemGroup[wiKey]
    const label = typeLabels[workItemType] || workItemType
    return wi ? `${label} ${wi.id}` : label
  }

  const getWorkItemTypeKebab = () => {
    return workItemType.replace('_', '-')
  }

  const deleteSnippetMapping = (snippet) => {
    setMessageValue('')
    const data = {
      'api-id': api.id,
      'relation-id': snippet.relation_id,
      'user-id': auth.userId,
      token: auth.token
    }

    fetch(Constants.API_BASE_URL + Constants.buildMappingDeletePath(Constants._A, getWorkItemTypeKebab()), {
      method: 'DELETE',
      headers: Constants.JSON_HEADER,
      body: JSON.stringify(data)
    })
      .then((response) => {
        if (!Constants.isHttpSuccessStatus(response.status)) {
          setMessageValue('Error deleting snippet mapping: ' + response.statusText)
        } else {
          loadMappingData(Constants.force_reload)
          handleModalToggle()
        }
      })
      .catch((err) => {
        setMessageValue(err.toString())
      })
  }

  const handleSelectionFromSpec = () => {
    const currentSelection = getSelection()?.toString() || ''
    if (currentSelection !== '') {
      const anchorParentId = (getSelection()?.anchorNode?.parentNode as any)?.id || ''
      if (anchorParentId === 'snippets-modal-raw-specification') {
        const currentOffset = Constants.getSelectionOffset()
        if (currentOffset > -1) {
          setNewSection(currentSelection)
          setNewOffset(currentOffset)
        }
      }
    }
  }

  const addSnippetMapping = () => {
    if (newSection.trim().length === 0) {
      setMessageValue('Please select a section from the reference document.')
      return
    }

    setMessageValue('')
    const wiKey = workItemType.replace('-', '_')
    const wi = workItemGroup[wiKey]
    if (!wi) {
      setMessageValue('Work item data not found.')
      return
    }

    const parentType = Constants._A
    const wiTypeKebab = getWorkItemTypeKebab()
    const pluralSegment = wiTypeKebab + 's'

    const data: any = {
      'api-id': api.id,
      section: newSection,
      offset: newOffset,
      coverage: 100,
      'user-id': auth.userId,
      token: auth.token
    }

    data[wiTypeKebab] = { id: wi.id }

    fetch(Constants.API_BASE_URL + Constants.buildMappingParentWorkItemsPath(parentType, pluralSegment), {
      method: 'POST',
      headers: Constants.JSON_HEADER,
      body: JSON.stringify(data)
    })
      .then((response) => {
        if (!Constants.isHttpSuccessStatus(response.status)) {
          response
            .json()
            .then((body) => setMessageValue(body?.message || response.statusText))
            .catch(() => setMessageValue(response.statusText))
        } else {
          setAddingSnippet(false)
          setNewSection('')
          setNewOffset(0)
          loadMappingData(Constants.force_reload)
          handleModalToggle()
        }
      })
      .catch((err) => {
        setMessageValue(err.toString())
      })
  }

  return (
    <Modal
      width={Constants.MODAL_WIDTH}
      bodyAriaLabel='MappingSnippetsModal'
      aria-label='mapping snippets modal'
      tabIndex={0}
      variant={ModalVariant.large}
      title={'Manage Snippets - ' + getWorkItemLabel()}
      description='View, add, or remove reference document snippets mapped to this work item.'
      isOpen={isModalOpen}
      onClose={handleModalToggle}
      actions={[
        <Button key='close' variant='primary' onClick={handleModalToggle}>
          Close
        </Button>
      ]}
    >
      {messageValue && (
        <Hint>
          <HintBody>{messageValue}</HintBody>
        </Hint>
      )}

      <Title headingLevel='h4' style={{ marginTop: '16px', marginBottom: '8px' }}>
        Current Snippets ({snippets.length})
      </Title>

      {snippets.length === 0 && (
        <TextContent>
          <Text component={TextVariants.p}>No snippets mapped to this work item.</Text>
        </TextContent>
      )}

      {snippets.map((snippet, idx) => (
        <Card key={idx} style={{ marginBottom: '8px' }}>
          <CardBody>
            <Flex>
              <FlexItem flex={{ default: 'flex_1' }}>
                <Flex direction={{ default: 'column' }}>
                  <FlexItem>
                    <Label isCompact color={snippet.match ? 'green' : 'red'}>
                      {snippet.match ? 'Matching' : 'Unmatching'}
                    </Label>
                    &nbsp;
                    <Label isCompact>Offset: {snippet.offset}</Label>
                    &nbsp;
                    <Label isCompact>Coverage: {snippet.coverage}%</Label>
                  </FlexItem>
                  <FlexItem>
                    <CodeBlock>
                      <CodeBlockCode className='pf-v5-u-text-wrap' style={{ maxHeight: '100px', overflow: 'auto', whiteSpace: 'pre-wrap' }}>
                        {Constants.getLimitedText(snippet.section, 300)}
                      </CodeBlockCode>
                    </CodeBlock>
                  </FlexItem>
                </Flex>
              </FlexItem>
              <FlexItem alignSelf={{ default: 'alignSelfCenter' }}>
                <Button
                  variant='danger'
                  icon={<TrashIcon />}
                  onClick={() => deleteSnippetMapping(snippet)}
                  isDisabled={!auth.isLogged() || !Constants.hasWritePermission(api)}
                >
                  Remove
                </Button>
              </FlexItem>
            </Flex>
          </CardBody>
        </Card>
      ))}

      <Divider style={{ marginTop: '16px', marginBottom: '16px' }} />

      {!addingSnippet ? (
        <Button
          variant='link'
          icon={<PlusCircleIcon />}
          onClick={() => setAddingSnippet(true)}
          isDisabled={!auth.isLogged() || !Constants.hasWritePermission(api) || !api?.raw_specification}
        >
          Add New Snippet
        </Button>
      ) : (
        <Card>
          <CardBody>
            <Title headingLevel='h4' style={{ marginBottom: '8px' }}>
              Select a section from the reference document
            </Title>
            <FormGroup label='Selected Section'>
              <CodeBlock>
                <CodeBlockCode className='pf-v5-u-text-wrap' style={{ maxHeight: '80px', overflow: 'auto', whiteSpace: 'pre-wrap' }}>
                  {newSection || '(highlight text in the document below to select)'}
                </CodeBlockCode>
              </CodeBlock>
            </FormGroup>
            <FormGroup label='Offset'>
              <Text>{newOffset}</Text>
            </FormGroup>
            <FormGroup label='Reference Document'>
              <CodeBlock className='code-block-bg-green code-fixed-height'>
                <CodeBlockCode>
                  <div onMouseUp={handleSelectionFromSpec} id='snippets-modal-raw-specification' data-offset={newOffset}>
                    {api?.raw_specification || ''}
                  </div>
                </CodeBlockCode>
              </CodeBlock>
            </FormGroup>
            <Flex style={{ marginTop: '8px' }}>
              <FlexItem>
                <Button variant='primary' onClick={addSnippetMapping} isDisabled={newSection.trim().length === 0}>
                  Add Snippet
                </Button>
              </FlexItem>
              <FlexItem>
                <Button
                  variant='link'
                  onClick={() => {
                    setAddingSnippet(false)
                    setNewSection('')
                    setNewOffset(0)
                  }}
                >
                  Cancel
                </Button>
              </FlexItem>
            </Flex>
          </CardBody>
        </Card>
      )}
    </Modal>
  )
}
