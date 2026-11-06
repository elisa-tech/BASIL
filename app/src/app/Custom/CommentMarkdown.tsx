import React from 'react'
import ReactMarkdown, { defaultUrlTransform } from 'react-markdown'
import { mentionLinkHref } from '@app/Custom/commentMention'

const mentionStyle: React.CSSProperties = {
  color: 'var(--pf-v5-global--link--Color)',
  fontWeight: 600,
  textDecoration: 'underline',
  cursor: 'text'
}

const commentUrlTransform = (url: string): string => {
  if (mentionLinkHref(url)) {
    return url
  }
  return defaultUrlTransform(url)
}

export const CommentMarkdown: React.FunctionComponent<{ children: string }> = ({ children }) => {
  return (
    <ReactMarkdown
      urlTransform={commentUrlTransform}
      components={{
        a: ({ href, children: linkChildren }) => {
          if (mentionLinkHref(href)) {
            return <span style={mentionStyle}>{linkChildren}</span>
          }
          return <a href={href}>{linkChildren}</a>
        }
      }}
    >
      {children}
    </ReactMarkdown>
  )
}
