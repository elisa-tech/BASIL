import * as React from 'react'
import { Label, Tooltip, Spinner } from '@patternfly/react-core'
import * as Constants from '@app/Constants/constants'

export interface CompletionLabelProps {
  mappedItem
}

const CompletionLabel: React.FunctionComponent<CompletionLabelProps> = ({ mappedItem }: CompletionLabelProps) => {
  return (
    <Tooltip
      content={
        <>
          Completion is referring to the parent work item
          <br />
          Work item completion (relative to parent): {Constants.percentageStringFormat(mappedItem['coverage'])}%
          <br />
          Work item gap (due to nested work items): {Constants.percentageStringFormat(mappedItem['gap'])}%
          <br />
          Overall completion: {Constants.percentageStringFormat(mappedItem['coverage'] - mappedItem['gap'])}%
        </>
      }
    >
      <Label color='red' name='label-document-coverage' variant='outline' isCompact>
        {Constants.percentageStringFormat(mappedItem['coverage'] - mappedItem['gap'])}% Completion
      </Label>
    </Tooltip>
  )
}

export { CompletionLabel }
