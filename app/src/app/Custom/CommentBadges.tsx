import * as React from 'react'
import { Badge, Divider, Flex } from '@patternfly/react-core'

export interface CommentBadgesProps {
  /** Optional comment icon / button shown on the same row as the badges */
  leading?: React.ReactNode
  comment_count: number
  todo_count: number
}

const commentBadgeStyle: React.CSSProperties = {
  backgroundColor: 'var(--pf-v5-global--palette--blue-100)',
  color: 'var(--pf-v5-global--palette--blue-700)'
}

const todoBadgeStyle: React.CSSProperties = {
  backgroundColor: 'var(--pf-v5-global--palette--orange-200)',
  color: 'var(--pf-v5-global--palette--orange-700)'
}

const CommentBadges = ({ leading, comment_count, todo_count }: CommentBadgesProps) => (
  <Flex alignItems={{ default: 'alignItemsCenter' }} spaceItems={{ default: 'spaceItemsMd' }} flexWrap={{ default: 'nowrap' }}>
    {leading}
    <Badge screenReaderText='Comments' style={commentBadgeStyle}>
      Comments: {comment_count}
    </Badge>
    {todo_count >= 1 && (
      <React.Fragment>
        <Divider orientation={{ default: 'vertical' }} />
        <Badge screenReaderText='TODO' style={todoBadgeStyle}>
          TODO: {todo_count}
        </Badge>
      </React.Fragment>
    )}
  </Flex>
)

export default CommentBadges
