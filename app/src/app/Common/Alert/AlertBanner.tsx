import React from 'react'
import * as Constants from '../../Constants/constants'
import { Alert } from '@patternfly/react-core'
import { AutoRefresh } from '../AutoRefresh/AutoRefresh'

export const AlertBanner: React.FunctionComponent = () => {
  const [alert, setAlert] = React.useState<{ info: string[]; warning: string[]; danger: string[]; success: string[] } | null>(null)

  const loadAlertMessages = () => {
    fetch(Constants.API_BASE_URL + '/alert')
      .then((res) => res.json())
      .then((data) => setAlert(data))
  }

  React.useEffect(() => {
    loadAlertMessages()
  }, [])

  console.log('Warnings to render:', alert?.warning)

  return (
    <>
      <AutoRefresh loadRows={loadAlertMessages} showCountdown={false} />
      {(alert?.danger ?? []).map((alert_message, index) => (
        <Alert key={'danger-' + index} variant='danger' isInline title={alert_message} ouiaId='DangerAlert' />
      ))}

      {(alert?.info ?? []).map((alert_message, index) => (
        <Alert key={'info-' + index} variant='info' isInline title={alert_message} ouiaId='InfoAlert' />
      ))}

      {(alert?.success ?? []).map((alert_message, index) => (
        <Alert key={'success-' + index} variant='success' isInline title={alert_message} ouiaId='SuccessAlert' />
      ))}

      {(alert?.warning ?? []).map((alert_message, index) => (
        <Alert key={'warning-' + index} variant='warning' isInline title={alert_message} ouiaId='WarningAlert' />
      ))}
    </>
  )
}
