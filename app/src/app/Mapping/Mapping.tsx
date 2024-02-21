import * as React from 'react'
import * as Constants from '../Constants/constants'
import { Flex, FlexItem, PageGroup, PageSection, PageSectionVariants } from '@patternfly/react-core'
import { MappingBreadCrumb } from './MappingBreadCrumb'
import { MappingPageSection } from './MappingPageSection'
import { useParams } from 'react-router-dom'

const Mapping: React.FunctionComponent = () => {
  const [mappingViewSelectValue, setMappingViewSelectValue] = React.useState('sw-requirements')
  const [num, setNum] = React.useState(0)
  const [apiData, setApiData] = React.useState(null)
  const [mappingData, setMappingData] = React.useState([])
  const [unmappingData, setUnmappingData] = React.useState([])
  const [totalCoverage, setTotalCoverage] = React.useState(0)
  const { api_id } = useParams<{ api_id: string }>()

  const loadApiData = () => {
    const url = Constants.API_BASE_URL + '/api-specifications?api-id=' + api_id

    fetch(url)
      .then((res) => res.json())
      .then((data) => {
        setApiData(data)
      })
      .catch((err) => {
        console.log(err.message)
      })
  }

  const loadMappingData = (force_reload) => {
    if (force_reload == false || force_reload == undefined) {
      if (num > 0) {
        return
      }
    }

    const url = Constants.API_BASE_URL + '/mapping/api/' + mappingViewSelectValue + '?api-id=' + api_id
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
    if (num == 0) {
      loadApiData()
      loadMappingData(false)
    }
    setNum(num + 1)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  React.useEffect(() => {
    loadMappingData(true)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [mappingViewSelectValue])

  React.useEffect(() => {
    let total_len = 0
    let wa = 0
    for (let i = 0; i < mappingData['length']; i++) {
      total_len = total_len + mappingData[i]['section']['length']
    }
    for (let i = 0; i < mappingData['length']; i++) {
      wa = wa + (mappingData[i]['section']['length'] / total_len) * (mappingData[i]['covered'] / 100.0)
    }
    const tc = Math.round(wa * 100 * 1e1) / 1e1
    setTotalCoverage(tc)
  }, [mappingData])

  return (
    <React.Fragment>
      <PageGroup stickyOnBreakpoint={{ default: 'top' }} hasShadowBottom>
        <PageSection variant={PageSectionVariants.light}>
          <Flex>
            <FlexItem align={{ default: 'alignLeft' }}>
              <MappingBreadCrumb api={apiData} />
            </FlexItem>
            <FlexItem align={{ default: 'alignRight' }}></FlexItem>
          </Flex>
        </PageSection>
        <PageSection type='tabs' variant={PageSectionVariants.light} isWidthLimited>
          <MappingPageSection
            mappingData={mappingData}
            unmappingData={unmappingData}
            loadMappingData={loadMappingData}
            mappingViewSelectValue={mappingViewSelectValue}
            setMappingViewSelectValue={setMappingViewSelectValue}
            totalCoverage={totalCoverage}
            api={apiData}
          />
        </PageSection>
      </PageGroup>
    </React.Fragment>
  )
}

export { Mapping }
