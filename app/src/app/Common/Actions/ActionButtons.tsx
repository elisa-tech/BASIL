import React from 'react'
import { DropdownItem, Spinner, Tooltip } from '@patternfly/react-core'
import * as Constants from '@app/Constants/constants'
import { useAuth } from '@app/User/AuthProvider'

type HttpHeaders = Record<string, string>

type ActionConfig = {
  url?: string
  method?: string
  headers?: string[] | HttpHeaders
  body?: unknown
}

type CustomAction = {
  name: string
  label?: string
  alt?: string
  type: 'http'
  config?: ActionConfig
}

type ActionsMap = Record<string, CustomAction[]>

export interface ActionButtonsProps {
  workItemType: string
  className?: string
}

const normalizeHeaders = (headers?: string[] | HttpHeaders): HttpHeaders => {
  if (!headers) return {}
  if (Array.isArray(headers)) {
    const out: HttpHeaders = {}
    headers.forEach((h) => {
      const idx = h.indexOf(':')
      if (idx > 0) {
        const k = h.slice(0, idx).trim()
        const v = h.slice(idx + 1).trim()
        if (k) out[k] = v
      }
    })
    return out
  }
  return headers
}

export const ActionButtons: React.FunctionComponent<ActionButtonsProps> = ({ workItemType, className }) => {
  const auth = useAuth()
  const [loading, setLoading] = React.useState(false)
  const [error, setError] = React.useState<string>('')
  const [actions, setActions] = React.useState<CustomAction[]>([])
  const [busyAction, setBusyAction] = React.useState<string>('')

  const loadActions = React.useCallback(() => {
    if (!auth?.isLogged?.() || !workItemType) {
      setActions([])
      return
    }
    setLoading(true)
    setError('')

    // Build GET URL with user and token, consistent with existing calls
    let url = Constants.API_BASE_URL + Constants.API_CUSTOM_ACTIONS_ENDPOINT
    url += '?user-id=' + auth.userId
    url += '&token=' + auth.token

    fetch(url, {
      method: 'GET',
      headers: Constants.JSON_HEADER
    })
      .then((res) => {
        if (!res.ok) {
          throw new Error(Constants.getResponseErrorMessage(res.status, res.statusText, 'Unable to load custom actions'))
        }
        return res.json()
      })
      .then((data: ActionsMap) => {
        const list = data && typeof data === 'object' && Array.isArray(data[workItemType]) ? data[workItemType] : []
        setActions(list)
      })
      .catch((err: Error) => {
        setError(err.message)
        setActions([])
      })
      .finally(() => setLoading(false))
  }, [auth, workItemType])

  React.useEffect(() => {
    loadActions()
  }, [loadActions])

  const runHttpAction = async (action: CustomAction) => {
    const cfg: ActionConfig = action?.config || {}
    const method = (cfg.method || 'GET').toUpperCase()
    const headers = { ...normalizeHeaders(cfg.headers) }
    let body: BodyInit | undefined = undefined

    // Best-effort JSON body support when provided
    if (cfg.body !== undefined && cfg.body !== null && method !== 'GET') {
      if (typeof cfg.body === 'string') {
        body = cfg.body
      } else {
        headers['Content-Type'] = headers['Content-Type'] || 'application/json'
        body = JSON.stringify(cfg.body)
      }
    }

    const url = cfg.url || ''
    if (!url) {
      window.alert('Invalid action configuration: missing URL')
      return
    }

    // For simple GET without body, open in new tab (friendlier UX for external web services)
    if (method === 'GET' && body === undefined) {
      window.open(url, '_blank', 'noopener,noreferrer')
      return
    }

    try {
      setBusyAction(action.name)
      const res = await fetch(url, { method, headers, body })
      if (!res.ok) {
        const text = await res.text()
        throw new Error(Constants.getResponseErrorMessage(res.status, res.statusText, text || 'Request failed'))
      }
      // Try to read a short response
      const contentType = res.headers.get('content-type') || ''
      if (contentType.includes('application/json')) {
        const json = await res.json()
        window.alert('Action executed successfully.\n\n' + JSON.stringify(json, null, 2))
      } else {
        const text = await res.text()
        window.alert('Action executed successfully.\n\n' + (text || '(no content)'))
      }
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e)
      window.alert('Action failed: ' + msg)
    } finally {
      setBusyAction('')
    }
  }

  if (!auth?.isLogged?.()) {
    return null
  }

  if (loading) {
    return (
      <DropdownItem
        key='custom-actions-loading'
        name='custom-actions-loading'
        id='btn-custom-actions-loading'
        isDisabled
        className={className}
      >
        <Spinner size='sm' /> Loading actions…
      </DropdownItem>
    )
  }

  if (error) {
    return (
      <DropdownItem
        key='custom-actions-error'
        name='custom-actions-error'
        id='btn-custom-actions-error'
        isDisabled
        className={className + ' danger-text'}
      >
        {error}
      </DropdownItem>
    )
  }

  if (!actions?.length) {
    return null
  }

  return (
    <>
      {actions
        .filter((a) => a && a.type === 'http')
        .map((act, idx) => {
          const label = act.label || act.name
          const isBusy = busyAction === act.name
          const content = (
            <>
              {isBusy ? <Spinner size='sm' /> : null}
              {isBusy ? ' ' : ''}
              {label}
            </>
          )
          const id =
            'btn-custom-action-' +
            String(act.name || idx)
              .toLowerCase()
              .replace(/[^a-z0-9]+/g, '-')
          const item = (
            <DropdownItem
              value={idx}
              id={id}
              name='btn-custom-action'
              key={act.name || idx}
              isDisabled={isBusy}
              onClick={() => runHttpAction(act)}
              className={className}
            >
              {act.alt ? (
                <Tooltip content={act.alt}>
                  <span>{content}</span>
                </Tooltip>
              ) : (
                content
              )}
            </DropdownItem>
          )
          return item
        })}
    </>
  )
}

export default ActionButtons
