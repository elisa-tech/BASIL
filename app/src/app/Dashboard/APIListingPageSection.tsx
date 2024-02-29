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

export interface APIListingPageSectionProps {
  currentLibrary: string
  setCurrentLibrary
  loadLibraries
  loadApi
  apis
  totalCoverage
  searchValue: string
}

const APIListingPageSection: React.FunctionComponent<APIListingPageSectionProps> = ({
  currentLibrary,
  setCurrentLibrary,
  loadLibraries,
  loadApi,
  apis,
  totalCoverage,
  searchValue
}: APIListingPageSectionProps) => {
  let auth = useAuth()
  const rows = []
  const [page, setPage] = React.useState(1)
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
  const [perPage, setPerPage] = React.useState(10)
  const [SPDXContent, setSPDXContent] = React.useState('')

  const [modalDeleteShowState, setModalDeleteShowState] = React.useState(false)
  const [modalManageUserPermissionsApiData, setModalManageUserPermissionsApiData] = React.useState(null)
  const [modalManageUserPermissionsShowState, setModalManageUserPermissionsShowState] = React.useState(false)
  /* eslint-disable @typescript-eslint/no-unused-vars */
  const [paginatedRows, setPaginatedRows] = React.useState(rows.slice(0, 10))
  const handleSetPage = (_evt, newPage, perPage, startIdx, endIdx) => {
    setPaginatedRows(rows.slice(startIdx, endIdx))
    setPage(newPage)
  }
  const handlePerPageSelect = (_evt, newPerPage, newPage, startIdx, endIdx) => {
    setPaginatedRows(rows.slice(startIdx, endIdx))
    setPage(newPage)
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
      itemCount={rows.length}
      page={page}
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
                  Covered {totalCoverage}%
                </Label>
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
            //currentLibrary={currentLibrary}
            //searchValue={searchValue}
            setModalInfo={setModalInfo}
            setModalCheckSpecInfo={setModalCheckSpecInfo}
            setModalDeleteInfo={setModalDeleteInfo}
            setModalManageUserPermissionsInfo={setModalManageUserPermissionsInfo}
            apis={apis}
          />
        </CardBody>
      </Card>
      <APIModal
        modalAction={modalAction}
        modalVerb={modalVerb}
        //modalObject={modalObject}
        modalTitle={modalTitle}
        modalDescription={modalDescription}
        modalFormData={modalFormData}
        modalShowState={modalShowState}
        setModalShowState={setModalShowState}
        setCurrentLibrary={setCurrentLibrary}
        loadLibraries={loadLibraries}
        loadApi={loadApi}
      />
      <APIDeleteModal
        modalShowState={modalDeleteShowState}
        setModalShowState={setModalDeleteShowState}
        api={modalObject}
        modalTitle={modalTitle}
        modalDescription={modalDescription}
        //loadLibraries={loadLibraries}
        //loadApi={loadApi}
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
    </PageSection>
  )
}

export { APIListingPageSection }
