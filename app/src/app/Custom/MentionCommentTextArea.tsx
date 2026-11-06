import React from 'react'
import * as Constants from '@app/Constants/constants'
import { formatMentionMarkdown } from '@app/Custom/commentMention'
import { CommentMarkdown } from '@app/Custom/CommentMarkdown'
import { Button, Text, TextArea, TextVariants } from '@patternfly/react-core'
import { useAuth } from '@app/User/AuthProvider'

export interface MentionableUser {
  id: number
  username: string
}

export interface MentionCommentTextAreaProps {
  apiId: number
  id: string
  value: string
  onChange: (value: string) => void
  onKeyUp?: (event: React.KeyboardEvent<HTMLTextAreaElement>) => void
  rows?: number
}

export const MentionCommentTextArea: React.FunctionComponent<MentionCommentTextAreaProps> = ({
  apiId,
  id,
  value,
  onChange,
  onKeyUp,
  rows = 5
}) => {
  const auth = useAuth()
  const [mentionMenuOpen, setMentionMenuOpen] = React.useState(false)
  const [mentionCandidates, setMentionCandidates] = React.useState<MentionableUser[]>([])
  const [mentionQuery, setMentionQuery] = React.useState('')
  const [mentionStartIndex, setMentionStartIndex] = React.useState<number | null>(null)
  const [activeMentionIndex, setActiveMentionIndex] = React.useState(0)
  const textareaRef = React.useRef<HTMLTextAreaElement | null>(null)

  const fetchMentionableUsers = (search: string) => {
    let url = Constants.API_BASE_URL + Constants.API_COMMENTS_MENTIONABLE_USERS_ENDPOINT
    url += '?api-id=' + apiId
    url += '&search=' + encodeURIComponent(search)
    if (auth.isLogged()) {
      url += '&user-id=' + auth.userId + '&token=' + auth.token
    }
    fetch(url)
      .then((res) => res.json())
      .then((data) => {
        const currentUserId = Number(auth.userId)
        const others = (Array.isArray(data) ? data : []).filter((candidate) => candidate.id !== currentUserId)
        setMentionCandidates(others)
        setActiveMentionIndex(0)
        if (others.length === 0) {
          setMentionMenuOpen(false)
        }
      })
      .catch(() => {
        setMentionCandidates([])
      })
  }

  const closeMentionMenu = () => {
    setMentionMenuOpen(false)
    setMentionQuery('')
    setMentionStartIndex(null)
    setMentionCandidates([])
  }

  const detectMentionAtCursor = (text: string, cursorPos: number) => {
    const before = text.slice(0, cursorPos)
    const at = before.lastIndexOf('@')
    if (at < 0) {
      closeMentionMenu()
      return
    }
    if (at > 0 && !/\s/.test(before[at - 1])) {
      closeMentionMenu()
      return
    }
    const query = before.slice(at + 1)
    if (query.includes(' ') || query.includes('\n')) {
      closeMentionMenu()
      return
    }
    setMentionStartIndex(at)
    setMentionQuery(query)
    setMentionMenuOpen(true)
    fetchMentionableUsers(query)
  }

  const insertMention = (user: MentionableUser) => {
    if (mentionStartIndex === null) {
      return
    }
    const el = textareaRef.current
    const cursorPos = el?.selectionStart ?? value.length
    const before = value.slice(0, mentionStartIndex)
    const after = value.slice(cursorPos)
    const token = formatMentionMarkdown(user.username, user.id)
    const next = before + token + ' ' + after
    onChange(next)
    closeMentionMenu()
    window.setTimeout(() => {
      const pos = (before + token + ' ').length
      el?.focus()
      el?.setSelectionRange(pos, pos)
    }, 0)
  }

  const handleChange = (_ev, newValue: string) => {
    onChange(newValue)
    const el = textareaRef.current
    const cursorPos = el?.selectionStart ?? newValue.length
    detectMentionAtCursor(newValue, cursorPos)
  }

  const handleKeyDown = (event: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (!mentionMenuOpen || mentionCandidates.length === 0) {
      return
    }
    if (event.key === 'ArrowDown') {
      event.preventDefault()
      setActiveMentionIndex((i) => (i + 1) % mentionCandidates.length)
    } else if (event.key === 'ArrowUp') {
      event.preventDefault()
      setActiveMentionIndex((i) => (i - 1 + mentionCandidates.length) % mentionCandidates.length)
    } else if (event.key === 'Enter' || event.key === 'Tab') {
      event.preventDefault()
      insertMention(mentionCandidates[activeMentionIndex])
    } else if (event.key === 'Escape') {
      event.preventDefault()
      closeMentionMenu()
    }
  }

  return (
    <div style={{ position: 'relative' }}>
      <TextArea
        ref={textareaRef}
        isRequired
        rows={rows}
        resizeOrientation='vertical'
        aria-label='Comment field'
        id={id}
        value={value || ''}
        onChange={handleChange}
        onKeyUp={onKeyUp}
        onKeyDown={handleKeyDown}
        onClick={() => {
          const el = textareaRef.current
          if (el) {
            detectMentionAtCursor(value, el.selectionStart ?? value.length)
          }
        }}
      />
      {mentionMenuOpen && mentionCandidates.length > 0 ? (
        <div
          style={{
            position: 'absolute',
            zIndex: 10,
            left: 0,
            top: '100%',
            minWidth: '14rem',
            marginTop: '0.25rem'
          }}
        >
          <div
            style={{
              background: 'var(--pf-v5-global--BackgroundColor--100)',
              border: '1px solid var(--pf-v5-global--BorderColor--100)',
              boxShadow: 'var(--pf-v5-global--BoxShadow--md)'
            }}
          >
            {mentionCandidates.map((user, index) => (
              <Button
                key={'mention-user-' + user.id}
                variant={index === activeMentionIndex ? 'primary' : 'plain'}
                onClick={() => insertMention(user)}
                style={{ display: 'block', width: '100%', textAlign: 'left' }}
              >
                @{user.username}
              </Button>
            ))}
          </div>
        </div>
      ) : (
        ''
      )}
      {value.trim() ? (
        <div
          style={{
            marginTop: '0.75rem',
            padding: '0.75rem',
            border: '1px solid var(--pf-v5-global--BorderColor--100)',
            borderRadius: '3px',
            background: 'var(--pf-v5-global--BackgroundColor--100)'
          }}
        >
          <Text component={TextVariants.small} style={{ marginBottom: '0.35rem', color: 'var(--pf-v5-global--Color--200)' }}>
            Preview
          </Text>
          <CommentMarkdown>{value}</CommentMarkdown>
        </div>
      ) : (
        ''
      )}
    </div>
  )
}
