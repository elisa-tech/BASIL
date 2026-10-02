import * as React from 'react'
import { Label, Tooltip } from '@patternfly/react-core'
import { UserAvatarIcon } from '@app/User/Avatar/UserAvatarIcon'

export interface CreatedByLabelProps {
  username?: string | null
}

// Who created a work item: the username, with the avatar of the user as icon.
// A compact label like the status and completion ones next to it, so that
// they line up.
const CreatedByLabel: React.FunctionComponent<CreatedByLabelProps> = ({ username }: CreatedByLabelProps) => {
  if (!username) {
    return null
  }
  return (
    <Tooltip content={`Created by ${username}`}>
      <Label
        className='created-by-label'
        variant='outline'
        isCompact
        icon={<UserAvatarIcon username={username} style={{ width: '14px', height: '14px' }} />}
      >
        {username}
      </Label>
    </Tooltip>
  )
}

export { CreatedByLabel }
