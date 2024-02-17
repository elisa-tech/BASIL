import * as React from 'react';
import { Breadcrumb, BreadcrumbItem } from '@patternfly/react-core';

export interface BreadCrumbProps {
  api;
}

export const MappingBreadCrumb: React.FunctionComponent<BreadCrumbProps> = ({
  api,
}: BreadCrumbProps) => {
  if (api != null){
    return (
      <React.Fragment>
        <Breadcrumb ouiaId="BasicBreadcrumb">
          <BreadcrumbItem to={"?currentLibrary=" + api['library']}>{api['library']}</BreadcrumbItem>
          <BreadcrumbItem to="#" isActive>
            {api['library_version']}
          </BreadcrumbItem>
          <BreadcrumbItem to="#" isActive>
            {api['api']}
          </BreadcrumbItem>
        </Breadcrumb>
      </React.Fragment>
  )} else {
    return (
      <React.Fragment>
      </React.Fragment>
    )
  }
}
