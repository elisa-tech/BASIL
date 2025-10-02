import * as React from 'react'
import * as Constants from '@app/Constants/constants'
import moment from 'moment'
import { Text } from '@patternfly/react-core'

export interface AutoRefreshProps {
  loadRows
  showCountdown
}

const AutoRefresh: React.FunctionComponent<AutoRefreshProps> = ({ loadRows, showCountdown = false }: AutoRefreshProps) => {
  const [count, setCount] = React.useState(0)
  const [lastFetchDateTiime, setLastFetchDateTime] = React.useState<any>(moment())
  const [fetchDateDiff, setFetchDateDiff] = React.useState<any>()

  // Timers for automatic refresh
  const [time, setTime] = React.useState(0)
  const currentTimer = React.useRef<any>()

  React.useEffect(() => {
    clearInterval(currentTimer.current)
    startTimer()
  }, [])

  React.useEffect(() => {
    if (lastFetchDateTiime != undefined && lastFetchDateTiime != null) {
      setFetchDateDiff(moment().diff(lastFetchDateTiime, 'seconds'))
    }
    if (fetchDateDiff >= Constants.REFRESH_INTERVAL) {
      loadRows(true)
      setLastFetchDateTime(moment())
      setTime(0)
    }
  }, [time])

  const startTimer = () => {
    currentTimer.current = setInterval(() => {
      setTime((prev) => prev + 1)
    }, 1000)
  }

  const stopTimer = () => {
    clearInterval(currentTimer.current)
  }

  const resetTimer = () => {
    stopTimer()
    setTime(0)
  }

  return <React.Fragment>{showCountdown ? <Text component='small'>Updated {fetchDateDiff} seconds ago</Text> : ''}</React.Fragment>
}

export { AutoRefresh }
