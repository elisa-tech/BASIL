import * as React from 'react'
import * as Constants from '../Constants/constants'
import {
  Button,
  Card,
  CardBody,
  Flex,
  FlexItem,
  Label,
  PageSection,
  Pagination,
  Title,
  Toolbar,
  ToolbarContent,
  ToolbarItem
} from '@patternfly/react-core'
import { APIListingTable } from './APIListingTable'
import { APIModal } from './Modal/APIModal'
import { APICheckSpecModal } from './Modal/APICheckSpecModal'
import { APIDeleteModal } from './Modal/APIDeleteModal'
import { APIExportSPDXModal } from './Modal/APIExportSPDXModal'
import { APIManageUserPermissionsModal } from './Modal/APIManageUserPermissionsModal'
import { useAuth } from '../User/AuthProvider'
import { ModalNotification } from '@app/Common/Modal/ModalNotification'

export interface APIListingPageSectionProps {
  currentLibrary: string
  apis
  totalCoverage
  currentPage
  setCurrentPage
  apiCount
  perPage
  setPerPage
}

const APIListingPageSection: React.FunctionComponent<APIListingPageSectionProps> = ({
  currentLibrary,
  apis,
  totalCoverage,
  currentPage,
  setCurrentPage,
  apiCount,
  perPage,
  setPerPage
}: APIListingPageSectionProps) => {
  const auth = useAuth()
  const rows = []
  const [modalShowState, setModalShowState] = React.useState(false)

  const [modalCheckSpecShowState, setModalCheckSpecShowState] = React.useState(false)
  const [modalSPDXExportShowState, setModalSPDXExportShowState] = React.useState(false)
  const [modalCheckSpecApiData, setModalCheckSpecApiData] = React.useState(null)
  const [modalObject, setModalObject] = React.useState('')
  const [modalAction, setModalAction] = React.useState('')
  const [modalVerb, setModalVerb] = React.useState('')
  const [modalFormData, setModalFormData] = React.useState('')
  const [modalTitle, setModalTitle] = React.useState('')
  const [modalDescription, setModalDescription] = React.useState('')
  const [SPDXContent, setSPDXContent] = React.useState('')

  const [modalNotificationShowState, setModalNotificationShowState] = React.useState(false)
  const [modalNotificationTitle, setModalNotificationTitle] = React.useState('')
  const [modalNotificationMessage, setModalNotificationMessage] = React.useState('')

  const [modalDeleteShowState, setModalDeleteShowState] = React.useState(false)
  const [modalManageUserPermissionsApiData, setModalManageUserPermissionsApiData] = React.useState(null)
  const [modalManageUserPermissionsShowState, setModalManageUserPermissionsShowState] = React.useState(false)
  /* eslint-disable @typescript-eslint/no-unused-vars */
  const [paginatedRows, setPaginatedRows] = React.useState(rows.slice(0, 10))
  const handleSetPage = (_evt, newPage, perPage, startIdx, endIdx) => {
    setCurrentPage(newPage)
  }
  const handlePerPageSelect = (_evt, newPerPage, newPage, startIdx, endIdx) => {
    setCurrentPage(Math.max(1, Math.ceil(startIdx / newPerPage)))
    setPerPage(newPerPage)
  }

  const setModalInfo = (_modalData, _modalShowState, _modalObject, _modalVerb, _modalAction, _modalTitle, _modalDescription) => {
    setModalFormData(_modalData)
    setModalShowState(_modalShowState)
    setModalObject(_modalObject)
    setModalVerb(_modalVerb)
    setModalAction(_modalAction)
    setModalTitle(_modalTitle)
    setModalDescription(_modalDescription)
  }

  const setModalDeleteInfo = (_modalObject, _modalShowState, _modalTitle, _modalDescription) => {
    setModalDeleteShowState(_modalShowState)
    setModalObject(_modalObject)
    setModalTitle(_modalTitle)
    setModalDescription(_modalDescription)
  }

  const setModalCheckSpecInfo = (_api, _modalShowState) => {
    setModalCheckSpecShowState(_modalShowState)
    setModalCheckSpecApiData(_api)
  }

  const setModalManageUserPermissionsInfo = (_api, _modalShowState) => {
    setModalManageUserPermissionsShowState(_modalShowState)
    setModalManageUserPermissionsApiData(_api)
  }

  const setModalNotificationInfo = (_title, _message, _modalShowState) => {
    setModalNotificationTitle(_title)
    setModalNotificationMessage(_message)
    setModalNotificationShowState(_modalShowState)
  }

  const exportSPDX = () => {
    fetch(Constants.API_BASE_URL + '/spdx/libraries?library=' + currentLibrary)
      .then((res) => res.json())
      .then((data) => {
        setSPDXContent(JSON.stringify(data, null, 2))
        setModalSPDXExportShowState(true)
      })
      .catch((err) => {
        console.log(err.message)
      })
  }

  const renderPagination = (variant, isCompact) => (
    <Pagination
      isCompact={isCompact}
      itemCount={apiCount}
      page={currentPage}
      perPage={perPage}
      onSetPage={handleSetPage}
      onPerPageSelect={handlePerPageSelect}
      variant={variant}
      titles={{
        paginationAriaLabel: `${variant} pagination`
      }}
    />
  )

  const tableToolbar = (
    <Toolbar usePageInsets id='compact-toolbar'>
      <ToolbarContent>
        <ToolbarItem variant='pagination'>{renderPagination('top', true)}</ToolbarItem>
      </ToolbarContent>
    </Toolbar>
  )

  const emptyFormData = {
    id: 0,
    api: '',
    library: '',
    library_version: '',
    raw_specification_url: '',
    category: '',
    tags: '',
    implementation_file_from_row: '',
    implementation_file_to_row: '',
    implementation_file: ''
  }
  return (
    <PageSection isFilled>
      <Card>
        <CardBody>
          <Flex>
            <Flex>
              <FlexItem>
                <Title headingLevel='h1'>API Listing for {currentLibrary}</Title>
              </FlexItem>
              <FlexItem>
                <Label color='green' isCompact>
                  Covered {Constants.percentageStringFormat(totalCoverage)}%
                </Label>
                {''}
              </FlexItem>
            </Flex>
            <Flex align={{ default: 'alignRight' }}>
              <FlexItem>
                {!auth.isGuest() ? (
                  <Button
                    id='btn-add-sw-component'
                    variant='primary'
                    onClick={() =>
                      setModalInfo(emptyFormData, true, 'api', 'POST', 'add', 'Software Component', 'Add a new software component')
                    }
                  >
                    Add Software Component
                  </Button>
                ) : (
                  ''
                )}
              </FlexItem>
              <FlexItem>
                <Button id='btn-export-sw-components-to-spdx' variant='secondary' onClick={() => exportSPDX()}>
                  Export to SPDX
                </Button>
              </FlexItem>
              <FlexItem>
                <Button variant='secondary' isDisabled>
                  Baseline
                </Button>
              </FlexItem>
            </Flex>
          </Flex>
          {tableToolbar}
          <APIListingTable
            setModalInfo={setModalInfo}
            setModalCheckSpecInfo={setModalCheckSpecInfo}
            setModalDeleteInfo={setModalDeleteInfo}
            setModalManageUserPermissionsInfo={setModalManageUserPermissionsInfo}
            setModalNotificationInfo={setModalNotificationInfo}
            apis={apis}
          />
        </CardBody>
      </Card>
      <APIModal
        modalAction={modalAction}
        modalVerb={modalVerb}
        modalTitle={modalTitle}
        modalDescription={modalDescription}
        modalFormData={modalFormData}
        modalShowState={modalShowState}
        setModalShowState={setModalShowState}
        //setCurrentLibrary={setCurrentLibrary}
        //loadLibraries={loadLibraries}
      />
      <APIDeleteModal
        modalShowState={modalDeleteShowState}
        setModalShowState={setModalDeleteShowState}
        api={modalObject}
        modalTitle={modalTitle}
        modalDescription={modalDescription}
      />
      <APICheckSpecModal
        api={modalCheckSpecApiData}
        modalShowState={modalCheckSpecShowState}
        setModalShowState={setModalCheckSpecShowState}
      />
      <APIExportSPDXModal
        SPDXContent={SPDXContent}
        setSPDXContent={setSPDXContent}
        modalShowState={modalSPDXExportShowState}
        setModalShowState={setModalSPDXExportShowState}
      />
      <APIManageUserPermissionsModal
        api={modalManageUserPermissionsApiData}
        modalShowState={modalManageUserPermissionsShowState}
        setModalShowState={setModalManageUserPermissionsShowState}
      />
      <ModalNotification
        modalMessage={modalNotificationMessage}
        modalTitle={modalNotificationTitle}
        modalShowState={modalNotificationShowState}
        setModalShowState={setModalNotificationShowState}
      />
    </PageSection>
  )
}

export { APIListingPageSection }
