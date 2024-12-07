import * as React from 'react'
import * as Constants from '../../Constants/constants'
import { Button, Modal, ModalVariant, Tab, TabContent, TabContentBody, TabTitleText, Tabs } from '@patternfly/react-core'
import { JustificationForm } from '../Form/JustificationForm'
import { SectionForm } from '../Form/SectionForm'
import { JustificationSearch } from '../Search/JustificationSearch'
import { MappingModalProps } from './MappingModalProps'

export const MappingJustificationModal: React.FunctionComponent<MappingModalProps> = ({
  modalShowState = false,
  setModalShowState,
  modalAction = '',
  modalVerb = '',
  modalTitle = '',
  modalFormData,
  modalOffset,
  setModalOffset,
  modalSection,
  setModalSection,
  modalDescription = '',
  parentData,
  loadMappingData,
  api
}: MappingModalProps) => {
  const [isModalOpen, setIsModalOpen] = React.useState(false)

  const handleModalToggle = () => {
    const new_state = !modalShowState
    setModalShowState(new_state)
    setIsModalOpen(new_state)
  }

  React.useEffect(() => {
    setIsModalOpen(modalShowState)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [modalShowState])

  const loadJustifications = (searchValue) => {
    let url = Constants.API_BASE_URL + '/justifications'
    if (searchValue != undefined) {
      url = url + '?search=' + searchValue
    }
    fetch(url)
      .then((res) => res.json())
      .then((data) => {
        setJustifications(data)
      })
      .catch((err) => {
        console.log(err.message)
      })
  }

  const [activeTabKey, setActiveTabKey] = React.useState<string | number>(0)
  const [justifications, setJustifications] = React.useState([])
  // Toggle currently active tab
  const handleTabClick = (event: React.MouseEvent | React.KeyboardEvent | MouseEvent, tabIndex: string | number) => {
    setActiveTabKey(tabIndex)
  }

  const newItemRef = React.createRef<HTMLElement>()
  const sectionItemsRef = React.createRef<HTMLElement>()
  const existingItemsRef = React.createRef<HTMLElement>()

  return (
    <React.Fragment>
      <Modal
        bodyAriaLabel='MappingJustificationModal'
        aria-label='mapping justification modal'
        tabIndex={0}
        variant={ModalVariant.large}
        title={modalTitle}
        description={modalDescription}
        isOpen={isModalOpen}
        onClose={handleModalToggle}
        actions={[
          <Button key='cancel' variant='link' onClick={handleModalToggle}>
            Cancel
          </Button>
        ]}
      >
        <Tabs activeKey={activeTabKey} onSelect={handleTabClick} aria-label='Add a New/Existing Justification' role='region'>
          <Tab
            eventKey={0}
            id='tab-btn-justification-data'
            title={<TabTitleText>Justification Data</TabTitleText>}
            tabContentId='tabNewJustification'
            tabContentRef={newItemRef}
          />
          <Tab
            eventKey={1}
            id='tab-btn-justification-mapping-section'
            title={<TabTitleText>Mapping Section</TabTitleText>}
            tabContentId='tabSection'
            tabContentRef={sectionItemsRef}
          />
          <Tab
            isDisabled={modalVerb == 'POST' ? false : true}
            eventKey={2}
            id='tab-btn-justification-existing'
            title={<TabTitleText>Existing</TabTitleText>}
            tabContentId='tabExistingJustification'
            tabContentRef={existingItemsRef}
          />
        </Tabs>
        <div>
          <TabContent eventKey={0} id='tabContentJustificationForm' ref={newItemRef} hidden={0 !== activeTabKey}>
            <TabContentBody hasPadding>
              <JustificationForm
                api={api}
                formAction={modalAction}
                formData={modalFormData}
                formVerb={modalVerb}
                parentData={parentData}
                handleModalToggle={handleModalToggle}
                loadMappingData={loadMappingData}
                modalOffset={modalOffset}
                modalSection={modalSection}
                formDefaultButtons={1}
                formMessage={''}
                modalFormSubmitState={'waiting'}
                //modalIndirect={modalIndirect}
                //parentType={parentType}
                //parentRelatedToType={parentRelatedToType}
              />
            </TabContentBody>
          </TabContent>
          <TabContent eventKey={1} id='tabContentJustificationSection' ref={sectionItemsRef} hidden={1 !== activeTabKey}>
            <TabContentBody hasPadding>
              <SectionForm
                api={api}
                //formVerb={modalVerb}
                //handleModalToggle={handleModalToggle}
                //modalIndirect={modalIndirect}
                modalOffset={modalOffset}
                modalSection={modalSection}
                setModalOffset={setModalOffset}
                setModalSection={setModalSection}
              />
            </TabContentBody>
          </TabContent>
          <TabContent eventKey={2} id='tabContentJustificationExisting' ref={existingItemsRef} hidden={2 !== activeTabKey}>
            <TabContentBody hasPadding>
              <JustificationSearch
                api={api}
                formVerb={modalVerb}
                //parentData={parentData}
                //parentType={parentType}
                //parentRelatedToType={parentRelatedToType}
                justifications={justifications}
                handleModalToggle={handleModalToggle}
                loadMappingData={loadMappingData}
                loadJustifications={loadJustifications}
                //modalIndirect={modalIndirect}
                modalOffset={modalOffset}
                modalSection={modalSection}
                modalShowState={modalShowState}
                formDefaultButtons={1}
                formData={null}
                formMessage={''}
              />
            </TabContentBody>
          </TabContent>
        </div>
      </Modal>
    </React.Fragment>
  )
}
