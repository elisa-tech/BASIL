import * as React from 'react'
import * as Constants from '../Constants/constants'
import { Flex, FlexItem, PageGroup, PageSection, PageSectionVariants } from '@patternfly/react-core'
import { MappingBreadCrumb } from './MappingBreadCrumb'
import { MappingPageSection } from './MappingPageSection'
import { useParams } from 'react-router-dom'
import { useAuth } from '../User/AuthProvider'
import { AlertBanner } from '@app/Common/Alert/AlertBanner'

const Mapping: React.FunctionComponent = () => {
  const auth = useAuth()
  const [mappingViewSelectValue, setMappingViewSelectValue] = React.useState('')
  const [mappingViewSelectValueOld, setMappingViewSelectValueOld] = React.useState('')
  const [num, setNum] = React.useState(0)
  const [apiData, setApiData] = React.useState(null)
  const [mappingData, setMappingData] = React.useState([])
  const [unmappingData, setUnmappingData] = React.useState([])
  const [totalCoverage, setTotalCoverage] = React.useState(-1)
  const { api_id } = useParams<{ api_id: string }>()

  //view
  //const search = window.location.search
  //const params = new URLSearchParams(search)
  //const queryView = params.get('view')

  const loadMappingData = (force_reload) => {
    if (!Constants.isValidId(api_id)) {
      return
    }

    if (force_reload == false || force_reload == undefined) {
      if (num > 0) {
        return
      }
    }
    let url
    url = Constants.API_BASE_URL + '/mapping/api/' + mappingViewSelectValue
    url += '?api-id=' + api_id

    if (auth.isLogged()) {
      url += '&user-id=' + auth.userId + '&token=' + auth.token
    }

    setNum(num + 1)

    fetch(url)
      .then((res) => res.json())
      .then((data) => {
        setMappingData(data['mapped'])
        setUnmappingData(data['unmapped'])
      })
      .catch((err) => {
        console.log(err.message)
      })
  }

  React.useEffect(() => {
    const loadApiData = () => {
      let url = Constants.API_BASE_URL + '/api-specifications?api-id=' + api_id

      if (auth.isLogged()) {
        url += '&user-id=' + auth.userId + '&token=' + auth.token
      }

      fetch(url)
        .then((res) => res.json())
        .then((data) => {
          setApiData(data)
          setMappingViewSelectValueOld(mappingViewSelectValue)
          if (data.default_view != '' && data.default_view != 'null' && data.default_view != undefined) {
            setMappingViewSelectValue(data.default_view)
          } else {
            setMappingViewSelectValue(Constants.DEFAULT_VIEW)
          }
        })
        .catch((err) => {
          console.log(err.message)
        })
    }

    loadApiData()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  React.useEffect(() => {
    if (mappingViewSelectValue != mappingViewSelectValueOld) {
      loadMappingData(Constants.force_reload)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [mappingViewSelectValue])

  React.useEffect(() => {
    if (mappingData == null) {
      return
    }
    if (mappingData.length == 0) {
      return
    }
    let total_len = 0
    let wa = 0
    for (let i = 0; i < mappingData['length']; i++) {
      total_len = total_len + mappingData[i]['section']['length']
    }
    if (total_len == 0) {
      return
    }
    for (let i = 0; i < mappingData['length']; i++) {
      wa = wa + (mappingData[i]['section']['length'] / total_len) * (mappingData[i]['covered'] / 100.0)
    }
    const tc = Math.round(wa * 100 * 1e1) / 1e1
    updateLastCoverage(tc)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [mappingData])

  const updateLastCoverage = (new_coverage) => {
    if (apiData == null) {
      return
    }
    if (new_coverage == apiData['last_coverage']) {
      return
    }
    const data = { 'api-id': api_id, 'last-coverage': new_coverage }

    if (auth.isLogged()) {
      data['user-id'] = auth.userId
      data['token'] = auth.token
    }

    setTotalCoverage(new_coverage)

    fetch(Constants.API_BASE_URL + '/mapping/api/last-coverage', {
      method: 'PUT',
      headers: Constants.JSON_HEADER,
      body: JSON.stringify(data)
    })
      .then((response) => {
        if (response.status !== 200) {
          console.log(response.statusText)
        }
      })
      .catch((err) => {
        console.log(err.toString())
      })
  }

  return (
    <React.Fragment>
      <PageGroup stickyOnBreakpoint={{ default: 'top' }} hasShadowBottom>
        <AlertBanner />
        <PageSection variant={PageSectionVariants.light}>
          <Flex>
            <FlexItem align={{ default: 'alignLeft' }}>
              <MappingBreadCrumb api={apiData} />
            </FlexItem>
            <FlexItem align={{ default: 'alignRight' }}></FlexItem>
          </Flex>
        </PageSection>
        <MappingPageSection
          mappingData={mappingData}
          unmappingData={unmappingData}
          loadMappingData={loadMappingData}
          mappingViewSelectValue={mappingViewSelectValue}
          setMappingViewSelectValue={setMappingViewSelectValue}
          setMappingViewSelectValueOld={setMappingViewSelectValueOld}
          totalCoverage={totalCoverage}
          api={apiData}
        />
      </PageGroup>
    </React.Fragment>
  )
}

export { Mapping }
