import { useEffect, useState } from 'react'

import { doApiRequest } from '@/utils/fetch'

interface OptionStatsType {
  breakdown: { [key: string]: number }
  option: string
}

interface AnalyticsDataType {
  poll_statistics: OptionStatsType[]
  time_series: number[]
}

const initData = {
  poll_statistics: [],
  time_series: [],
}

const useAnalytics = (id: number | undefined) => {
  const [data, setData] = useState<AnalyticsDataType>(initData)
  const [isLoading, setIsLoading] = useState<boolean>(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    setIsLoading(true)
    doApiRequest(`/api/portal/vote-statistics/${id}`)
      .then((res) => res.json())
      .then((res) => setData(res))
      .catch((err) => setError(err))
    setIsLoading(false)

    // clean up after component unmounts
    return () => {
      setData(initData)
      setError(null)
    }
  }, [id])

  return {
    data,
    isLoading,
    error,
  }
}

export default useAnalytics
