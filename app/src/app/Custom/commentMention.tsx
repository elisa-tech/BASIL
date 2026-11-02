import React from 'react'

export const MENTION_USER_SCHEME = 'basil-user:'

export const formatMentionMarkdown = (username: string, userId: number): string => {
  return `[@${username}](${MENTION_USER_SCHEME}${userId})`
}

export const mentionLinkHref = (href: string | undefined): boolean => {
  return typeof href === 'string' && href.startsWith(MENTION_USER_SCHEME)
}

export const mentionUserIdFromHref = (href: string): number | null => {
  if (!href.startsWith(MENTION_USER_SCHEME)) {
    return null
  }
  const id = parseInt(href.slice(MENTION_USER_SCHEME.length), 10)
  return Number.isFinite(id) ? id : null
}

export const parseMappingTableName = (parentTable: string): { workItemType: string; parentType: string } | null => {
  const marker = '_mapping_'
  const idx = parentTable.indexOf(marker)
  if (idx < 0) {
    return null
  }
  const workItem = parentTable.slice(0, idx).replaceAll('_', '-')
  const parent = parentTable.slice(idx + marker.length).replaceAll('_', '-')
  return { workItemType: workItem, parentType: parent }
}
