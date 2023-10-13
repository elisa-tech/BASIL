import * as React from 'react';
import { Flex, FlexItem, PageGroup, PageSection, PageSectionVariants, SearchInput, Tab, Tabs, TabTitleText } from '@patternfly/react-core';
import { APIListingPageSection } from './APIListingPageSection';
import { APIListingTable } from './APIListingTable';

const Dashboard: React.FunctionComponent = () => {
  const [activeTabKey, setActiveTabKey] = React.useState(0);
  const [searchValue, setSearchValue] = React.useState('');
  const [apis, setApis] = React.useState([]);
  const [totalCoverage, setTotalCoverage] = React.useState(0);
  /* eslint-disable @typescript-eslint/no-unused-vars */
  const [libraries, setLibraries] = React.useState([]);
  const [currentLibrary, setCurrentLibrary] = React.useState('');
  const API_BASE_URL = 'http://localhost:5000';
  const search = window.location.search;
  const params = new URLSearchParams(search);
  const qsCurrentLibrary = params.get('currentLibrary');

  const onChangeSearchValue = (value: string) => {
    setSearchValue(value);
  };

  const libraryTabClick = (lib) => {
     setCurrentLibrary(lib);
   }

  const loadLibraries = (current) => {
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

  const loadApi = () => {
    if (currentLibrary.trim().length == 0){
      return;
    }

    let base_url = API_BASE_URL + '/apis?field1=library&filter1=';
    let url = "";
    if (searchValue.trim().length > 0){
      url = base_url + currentLibrary + "&search=" + searchValue.trim();
    } else {
      url = base_url + currentLibrary;
    }

    fetch(url)
      .then((res) => res.json())
      .then((data) => {
        setApis(data);
      })
      .catch((err) => {
        console.log(err.message);
      });
  }

  React.useEffect(() => {
    setActiveTabKey(libraries.indexOf(currentLibrary));
  }, [currentLibrary]);

  React.useEffect(() => {
    let tc = 0;
    for (let i = 0; i<apis.length; i++){
      tc = tc + (apis[i].coverage  / apis.length);
    }
    setTotalCoverage(tc);
  }, [apis]);

  React.useEffect(() => {
    loadLibraries('');
  }, []);

  React.useEffect(() => {
    loadApi();
  }, [currentLibrary, searchValue]);

  React.useEffect(() => {
    if (libraries.length > 0){
      if (currentLibrary == ""){
        if(qsCurrentLibrary != undefined){
          if (qsCurrentLibrary.length > 0){
            if (libraries.indexOf(qsCurrentLibrary)>0){
              setCurrentLibrary(qsCurrentLibrary);
            }
          } else {
            setCurrentLibrary(libraries[0]);
          }
        } else {
          setCurrentLibrary(libraries[0]);
        }
      } else {
        setActiveTabKey(libraries.indexOf(currentLibrary));
      }
    }
  }, [libraries]);


  return (
    <React.Fragment>
      <PageGroup stickyOnBreakpoint={{ default: 'top' }} hasShadowBottom>
        <PageSection variant={PageSectionVariants.light} >
          <Flex>
            <FlexItem align={{ default: 'alignRight' }}>
              <SearchInput
                placeholder="Search Identifier"
                value={searchValue}
                onChange={(_event, value) => onChangeSearchValue(value)}
                onClear={() => onChangeSearchValue('')}
                style={{width:'400px'}}
              />
            </FlexItem>
          </Flex>
        </PageSection>
        <PageSection type="tabs" variant={PageSectionVariants.light} isWidthLimited>
          <Tabs activeKey={activeTabKey} usePageInsets id="open-tabs-example-tabs-list">
            {/*}<Tab eventKey={0} title={<TabTitleText>glibc</TabTitleText>} tabContentId="glibc" />
            <Tab eventKey={1} title={<TabTitleText>libcurl</TabTitleText>} tabContentId="libcurl" />
            <Tab eventKey={2} title={<TabTitleText>libcrypt</TabTitleText>} tabContentId="libcrypt" />
            <Tab eventKey={3} title={<TabTitleText>something</TabTitleText>} tabContentId="something" />
            <Tab eventKey={4} title={<TabTitleText>somethingelse</TabTitleText>} tabContentId="somethingelse" />*/}
            {libraries.map((library, index) => (
              <Tab eventKey={index} onClick={() => {libraryTabClick(library)}} title={<TabTitleText>{library}</TabTitleText>}></Tab>
            ))}
          </Tabs>
        </PageSection>
      </PageGroup>
      <APIListingPageSection
        currentLibrary={currentLibrary}
        setCurrentLibrary={setCurrentLibrary}
        loadLibraries={loadLibraries}
        loadApi={loadApi}
        apis={apis}
        searchValue={searchValue}
        totalCoverage={totalCoverage}
        baseApiUrl={API_BASE_URL}/>
    </React.Fragment>
  )
}

export { Dashboard };
