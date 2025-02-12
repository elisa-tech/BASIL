import * as React from 'react'
import * as Constants from '@app/Constants/constants'
import { Button, Modal, ModalVariant, Tab, TabContent, TabContentBody, TabTitleText, Tabs } from '@patternfly/react-core'
import { DocumentForm } from '../Form/DocumentForm'
import { SectionForm } from '../Form/SectionForm'
import { DocumentSearch } from '../Search/DocumentSearch'
import { MappingModalProps } from './MappingModalProps'

export const MappingDocumentModal: React.FunctionComponent<MappingModalProps> = ({
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

  const loadDocuments = (searchValue) => {
    let url = Constants.API_BASE_URL + '/' + Constants._Ds
    if (searchValue != undefined) {
      url = url + '?search=' + searchValue
    }
    fetch(url)
      .then((res) => res.json())
      .then((data) => {
        setDocuments(data)
      })
      .catch((err) => {
        console.log(err.message)
      })
  }

  const [activeTabKey, setActiveTabKey] = React.useState<string | number>(0)
  const [documents, setDocuments] = React.useState([])
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
        width={Constants.MODAL_WIDTH}
        bodyAriaLabel='MappingDocumentModal'
        aria-label='mapping document modal'
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
        <Tabs activeKey={activeTabKey} onSelect={handleTabClick} aria-label='Add a New/Existing Document' role='region'>
          <Tab
            eventKey={0}
            id='tab-btn-document-data'
            title={<TabTitleText>Document Data</TabTitleText>}
            tabContentId='tabNewDocument'
            tabContentRef={newItemRef}
          />
          <Tab
            eventKey={1}
            id='tab-btn-document-mapping-section'
            title={<TabTitleText>Mapping Section</TabTitleText>}
            tabContentId='tabSection'
            tabContentRef={sectionItemsRef}
          />
          <Tab
            isDisabled={modalVerb == 'POST' ? false : true}
            eventKey={2}
            id='tab-btn-document-existing'
            title={<TabTitleText>Existing</TabTitleText>}
            tabContentId='tabExistingDocument'
            tabContentRef={existingItemsRef}
          />
        </Tabs>
        <div>
          <TabContent eventKey={0} id='tabContentDocumentForm' ref={newItemRef} hidden={0 !== activeTabKey}>
            <TabContentBody hasPadding>
              <DocumentForm
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
          <TabContent eventKey={1} id='tabContentDocumentSection' ref={sectionItemsRef} hidden={1 !== activeTabKey}>
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
          <TabContent eventKey={2} id='tabContentDocumentExisting' ref={existingItemsRef} hidden={2 !== activeTabKey}>
            <TabContentBody hasPadding>
              <DocumentSearch
                api={api}
                formVerb={modalVerb}
                //parentData={parentData}
                //parentType={parentType}
                //parentRelatedToType={parentRelatedToType}
                documents={documents}
                handleModalToggle={handleModalToggle}
                loadMappingData={loadMappingData}
                loadDocuments={loadDocuments}
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
