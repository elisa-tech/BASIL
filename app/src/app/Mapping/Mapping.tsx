import * as React from 'react';
import { Flex, FlexItem, PageGroup, PageSection, PageSectionVariants, SearchInput, Tab, Tabs, TabTitleText } from '@patternfly/react-core';
import { MappingBreadCrumb } from './MappingBreadCrumb';
import { MappingPageSection } from './MappingPageSection';
import {
  BrowserRouter as Router,
  Switch,
  Route,
  Link,
  useParams
} from "react-router-dom";

const Mapping: React.FunctionComponent = (api_id, setNotificationCount) => {
  const API_BASE_URL = 'http://localhost:5000';

  const [mappingViewSelectValue, setMappingViewSelectValue] = React.useState('sw-requirements');
  const [num, setNum] = React.useState(0);
  const [apiData, setApiData] = React.useState(null);
  const [mappingData, setMappingData] = React.useState([]);
  const [unmappingData, setUnmappingData] = React.useState([]);
  const [totalCoverage, setTotalCoverage] = React.useState(0);

  let { api_id } = useParams();

  const loadMapping = (current) => {
    fetch(API_BASE_URL + '/libraries')
      .then((res) => res.json())
      .then((data) => {
        setLibraries(data);
      })
      .catch((err) => {
        console.log(err.message);
      });
      setCurrentLibrary(current);
  }

  const loadApiData = () => {
    let url = API_BASE_URL + '/api-specifications?api-id=' + api_id;

    fetch(url)
      .then((res) => res.json())
      .then((data) => {
        setApiData(data);
      })
      .catch((err) => {
        console.log(err.message);
      });
  }

  const loadMappingData = () => {
    let url = API_BASE_URL + '/mapping/api/' + mappingViewSelectValue + '?api-id=' + api_id;
    fetch(url)
      .then((res) => res.json())
      .then((data) => {
          setMappingData(data['mapped']);
          setUnmappingData(data['unmapped']);
      })
      .catch((err) => {
        console.log(err.message);
      });
  }

  React.useEffect(() => {
    if (num == 0){
      loadApiData();
      loadMappingData();
    }
    setNum(num + 1);
  }, []);

  React.useEffect(() => {
    loadMappingData();
  }, [mappingViewSelectValue]);

  React.useEffect(() => {
    let total_len = 0;
    let wa = 0;
    for (let i = 0; i<mappingData.length; i++){
      total_len = total_len + mappingData[i]['section'].length;
    }
    for (let i = 0; i<mappingData.length; i++){
      wa = wa + (mappingData[i]['section'].length / total_len) * (mappingData[i]['coverage'] / 100.0);
    }
    let tc = Number.parseFloat(wa*100).toFixed(1);
    setTotalCoverage(tc);
  }, [mappingData]);

  return (
    <React.Fragment>
      <PageGroup stickyOnBreakpoint={{ default: 'top' }} hasShadowBottom>
        <PageSection variant={PageSectionVariants.light} >
          <Flex>
            <FlexItem align={{ default: 'alignLeft' }}>
             <MappingBreadCrumb
               api={apiData} />
            </FlexItem>
            <FlexItem align={{ default: 'alignRight' }}>

            </FlexItem>
          </Flex>
        </PageSection>
        <PageSection type="tabs" variant={PageSectionVariants.light} isWidthLimited>
          <MappingPageSection
            baseApiUrl={API_BASE_URL}
            mappingData={mappingData}
            unmappingData={unmappingData}
            loadMappingData={loadMappingData}
            mappingViewSelectValue={mappingViewSelectValue}
            setMappingViewSelectValue={setMappingViewSelectValue}
            totalCoverage={totalCoverage}
            api={apiData}/>
        </PageSection>
      </PageGroup>
    </React.Fragment>
  )
}

export { Mapping };
