import * as React from 'react';
import empty_leaf from '@app/bgimages/empty_leaf.svg';
import half_leaf from '@app/bgimages/half_leaf.svg';
import full_leaf from '@app/bgimages/full_leaf.svg';
import { Icon } from '@patternfly/react-core';
import { Tooltip } from '@patternfly/react-core';

export interface LeavesProgressBarProps {
  progressValue;
  progressId;
}

const LeavesProgressBar: React.FunctionComponent<LeavesProgressBarProps> = ({
    progressValue=0,
    progressId='progress-bar',
}: LeavesProgressBarProps) => {

  let limited_progress = Math.min(Math.max(0, progressValue), 100);
  limited_progress = Number.parseFloat(limited_progress).toFixed(1);
  let icon_size = "xl";
  let leaves = [empty_leaf, empty_leaf, empty_leaf, empty_leaf];

  if (limited_progress == 0){
    leaves = [empty_leaf, empty_leaf, empty_leaf, empty_leaf];
  } else if ((limited_progress > 0) && (limited_progress <= 12)) {
    leaves = [half_leaf, empty_leaf, empty_leaf, empty_leaf];
  } else if ((limited_progress > 12) && (limited_progress <= 25)) {
    leaves = [full_leaf, empty_leaf, empty_leaf, empty_leaf];
  } else if ((limited_progress > 25) && (limited_progress <= 37)) {
    leaves = [full_leaf, half_leaf, empty_leaf, empty_leaf];
  } else if ((limited_progress > 37) && (limited_progress <= 50)) {
    leaves = [full_leaf, full_leaf, empty_leaf, empty_leaf];
  } else if ((limited_progress > 50) && (limited_progress <= 62)) {
    leaves = [full_leaf, full_leaf, half_leaf, empty_leaf];
  } else if ((limited_progress > 62) && (limited_progress <= 75)) {
    leaves = [full_leaf, full_leaf, full_leaf, empty_leaf];
  } else if ((limited_progress > 75) && (limited_progress < 100)) {
    leaves = [full_leaf, full_leaf, full_leaf, half_leaf];
  } else if (limited_progress == 100) {
    leaves = [full_leaf, full_leaf, full_leaf, full_leaf];
  }

  return(
    <React.Fragment>
      <div aria-describedby={progressId + "-ref2"} id={progressId}>
        <Icon iconSize={icon_size}><img src={leaves[0]} /></Icon>
        <Icon iconSize={icon_size}><img src={leaves[1]} /></Icon>
        <Icon iconSize={icon_size}><img src={leaves[2]} /></Icon>
        <Icon iconSize={icon_size}><img src={leaves[3]} /></Icon>
      </div>
      <Tooltip
        id={progressId + "-ref2"}
        content={
          <div>
            Coverage {limited_progress}%
          </div>
        }
        triggerRef={() => document.getElementById(progressId)}
        />
    </React.Fragment>
  );
}

export { LeavesProgressBar };
