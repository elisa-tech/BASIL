import * as React from 'react'
import * as Constants from '../Constants/constants'
import empty_leaf from '@app/bgimages/empty_leaf.svg'
import half_leaf from '@app/bgimages/half_leaf.svg'
import full_leaf from '@app/bgimages/full_leaf.svg'
import { Icon } from '@patternfly/react-core'
import { Tooltip } from '@patternfly/react-core'

export interface LeavesProgressBarProps {
  progressId
  progressValue
}

const LeavesProgressBar: React.FunctionComponent<LeavesProgressBarProps> = ({
  progressValue = 0,
  progressId = 'progress-bar'
}: LeavesProgressBarProps) => {
  let limited_progress = Math.min(Math.max(0, progressValue), 100)
  limited_progress = Math.round(limited_progress * 1e1) / 1e1
  const icon_size = 'xl'
  let leaves = [empty_leaf, empty_leaf, empty_leaf, empty_leaf]

  if (limited_progress == 0) {
    leaves = [empty_leaf, empty_leaf, empty_leaf, empty_leaf]
  } else if (limited_progress > 0 && limited_progress <= 12) {
    leaves = [half_leaf, empty_leaf, empty_leaf, empty_leaf]
  } else if (limited_progress > 12 && limited_progress <= 25) {
    leaves = [full_leaf, empty_leaf, empty_leaf, empty_leaf]
  } else if (limited_progress > 25 && limited_progress <= 37) {
    leaves = [full_leaf, half_leaf, empty_leaf, empty_leaf]
  } else if (limited_progress > 37 && limited_progress <= 50) {
    leaves = [full_leaf, full_leaf, empty_leaf, empty_leaf]
  } else if (limited_progress > 50 && limited_progress <= 62) {
    leaves = [full_leaf, full_leaf, half_leaf, empty_leaf]
  } else if (limited_progress > 62 && limited_progress <= 75) {
    leaves = [full_leaf, full_leaf, full_leaf, empty_leaf]
  } else if (limited_progress > 75 && limited_progress < 100) {
    leaves = [full_leaf, full_leaf, full_leaf, half_leaf]
  } else if (limited_progress == 100) {
    leaves = [full_leaf, full_leaf, full_leaf, full_leaf]
  }

  return (
    <React.Fragment>
      <div aria-describedby={progressId + '-ref2'} id={progressId}>
        <Icon iconSize={icon_size}>
          <img alt='progress 0-25' src={leaves[0]} />
        </Icon>
        <Icon iconSize={icon_size}>
          <img alt='progress 25-50' src={leaves[1]} />
        </Icon>
        <Icon iconSize={icon_size}>
          <img alt='progress 50-75' src={leaves[2]} />
        </Icon>
        <Icon iconSize={icon_size}>
          <img alt='progress 75-100' src={leaves[3]} />
        </Icon>
      </div>
      <Tooltip
        id={progressId + '-ref2'}
        content={<div>Completion {Constants.percentageStringFormat(limited_progress)}%</div>}
        triggerRef={() => document.getElementById(progressId) as HTMLElement}
      />
    </React.Fragment>
  )
}

export { LeavesProgressBar }
