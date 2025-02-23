import * as React from 'react'
import * as Constants from '../Constants/constants'
import {
  Button,
  Flex,
  FlexItem,
  PageGroup,
  PageSection,
  PageSectionVariants,
  SearchInput,
  Tab,
  TabTitleText,
  Tabs
} from '@patternfly/react-core'
import { APIListingPageSection } from './APIListingPageSection'
import { useAuth } from '../User/AuthProvider'

const Dashboard: React.FunctionComponent = () => {
  const auth = useAuth()
  const [activeTabKey, setActiveTabKey] = React.useState(0)
  const [searchValue, setSearchValue] = React.useState('')
  const [apis, setApis] = React.useState([])
  const [totalCoverage, setTotalCoverage] = React.useState(0)
  /* eslint-disable @typescript-eslint/no-unused-vars */
  const [libraries, setLibraries] = React.useState<string[]>([])
  const [currentLibrary, setCurrentLibrary] = React.useState('')
  const search = window.location.search
  const params = new URLSearchParams(search)
  const qsCurrentLibrary = params.get('currentLibrary')

  // Pagination
  const [currentPage, setCurrentPage] = React.useState(1)
  const [pageCount, setPageCount] = React.useState(0)
  const [apiCount, setApiCount] = React.useState(0)
  const [perPage, setPerPage] = React.useState(Constants.DEFAULT_PER_PAGE)

  const onChangeSearchValue = (value: string) => {
    setSearchValue(value)
  }

  const libraryTabClick = (lib) => {
    setCurrentPage(1)
    setPageCount(0)
    setApiCount(0)
    setCurrentLibrary(lib)
  }

  const loadLibraries = (current) => {
    fetch(Constants.API_BASE_URL + '/libraries')
      .then((res) => res.json())
      .then((data) => {
        setLibraries(data)
      })
      .catch((err) => {
        console.log(err.message)
      })
    setCurrentLibrary(current)
  }

  const loadApi = () => {
    if (currentLibrary == undefined) {
      return
    }
    if (currentLibrary.trim().length == 0) {
      return
    }

    const base_url = Constants.API_BASE_URL + '/apis?field1=library&filter1='
    let url = ''
    if (searchValue.trim().length > 0) {
      url = base_url + currentLibrary + '&search=' + searchValue.trim()
    } else {
      url = base_url + currentLibrary
    }

    if (auth.isLogged()) {
      url += '&user-id=' + auth.userId + '&token=' + auth.token
    }

    url += '&page=' + currentPage + '&per_page=' + perPage

    fetch(url)
      .then((res) => res.json())
      .then((data) => {
        setApis(data['apis'])
        setPageCount(data['page_count'])
        setApiCount(data['count'])
      })
      .catch((err) => {
        console.log(err.message)
      })
  }

  React.useEffect(() => {
    setActiveTabKey(libraries.indexOf(currentLibrary))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentLibrary])

  React.useEffect(() => {
    let tc = 0
    for (let i = 0; i < apis.length; i++) {
      tc = tc + apis[i]['covered'] / apis.length
    }
    setTotalCoverage(tc)
  }, [apis])

  React.useEffect(() => {
    loadLibraries('')
  }, [])

  React.useEffect(() => {
    loadApi()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentLibrary])

  React.useEffect(() => {
    loadApi()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentPage])

  React.useEffect(() => {
    loadApi()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [perPage])

  React.useEffect(() => {
    if (libraries.length > 0) {
      if (currentLibrary == '') {
        if (qsCurrentLibrary != undefined) {
          if (qsCurrentLibrary.length > 0) {
            if (libraries.indexOf(qsCurrentLibrary) >= 0) {
              setCurrentLibrary(qsCurrentLibrary)
            }
          } else {
            setCurrentLibrary(libraries[0])
          }
        } else {
          setCurrentLibrary(libraries[0])
        }
      } else {
        setActiveTabKey(libraries.indexOf(currentLibrary))
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [libraries])

  // Keyboard events
  const handleSearchKeyPress = (event) => {
    if (event.key === 'Enter') {
      loadApi()
    }
  }

  return (
    <React.Fragment>
      <PageGroup stickyOnBreakpoint={{ default: 'top' }} hasShadowBottom>
        <PageSection variant={PageSectionVariants.light}>
          <Flex>
            <FlexItem align={{ default: 'alignRight' }}>
              <SearchInput
                id='input-api-list-search'
                placeholder='Search Identifier'
                value={searchValue}
                onChange={(_event, value) => onChangeSearchValue(value)}
                onClear={() => onChangeSearchValue('')}
                onKeyUp={handleSearchKeyPress}
                style={{ width: '400px' }}
              />
            </FlexItem>
            <FlexItem>
              <Button
                variant='primary'
                aria-label='Action'
                onClick={() => {
                  loadApi()
                }}
              >
                Search
              </Button>
            </FlexItem>
          </Flex>
        </PageSection>
        <PageSection type='tabs' variant={PageSectionVariants.light} isWidthLimited>
          <Tabs activeKey={activeTabKey} usePageInsets id='open-tabs-example-tabs-list'>
            {libraries.map((library, index) => (
              <Tab
                key={index}
                eventKey={index}
                onClick={() => {
                  libraryTabClick(library)
                }}
                title={<TabTitleText>{library}</TabTitleText>}
              ></Tab>
            ))}
          </Tabs>
        </PageSection>
      </PageGroup>
      <APIListingPageSection
        currentLibrary={currentLibrary}
        apis={apis}
        totalCoverage={totalCoverage}
        currentPage={currentPage}
        setCurrentPage={setCurrentPage}
        apiCount={apiCount}
        perPage={perPage}
        setPerPage={setPerPage}
      />
    </React.Fragment>
  )
}

export { Dashboard }
