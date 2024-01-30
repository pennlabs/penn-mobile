import { useEffect, useState } from 'react'

import { doApiRequest } from '@/utils/fetch'

interface OptionStatsType {
  breakdown: { [key: string]: { [key: string]: number } }
  option: string
}

interface TimeSeriesDataType {
  date: string
  votes: number
}

interface AnalyticsDataType {
  poll_statistics: OptionStatsType[]
  time_series: TimeSeriesDataType[]
}

interface OptionDataType {
  club_code: string
  club_comment: string | null
  created_date: string
  expire_date: string
  id: number
  multiselect: boolean
  options: {
    id: number
    poll: number
    choice: string
    vote_count: number
  }[]
  question: string
  start_date: string
  status: string
  target_populations: {
    id: number
    kind: string
    population: string
  }[]
}

const optionTypeInitData = {
  club_code: '',
  club_comment: '',
  created_date: '',
  expire_date: '',
  id: 0,
  multiselect: false,
  options: [
    {
      id: 0,
      poll: 0,
      choice: '',
      vote_count: 0,
    },
  ],
  question: '',
  start_date: '',
  status: '',
  target_populations: [
    {
      id: 0,
      kind: '',
      population: '',
    },
  ],
}

const initData = {
  poll_statistics: [],
  time_series: [],
}

const useAnalytics = (id: number | undefined) => {
  const [data, setData] = useState<AnalyticsDataType>(initData)
  const [optionData, setOptionData] =
    useState<OptionDataType>(optionTypeInitData)
  const [isLoading, setIsLoading] = useState<boolean>(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    setIsLoading(true)
    doApiRequest(`/api/portal/vote-statistics/${id}`)
      .then((res) => res.json())
      .then((res) => {
        setData(res)
        doApiRequest(`/api/portal/polls/${id}/option_view/`)
          .then((optionRes) => optionRes.json())
          .then((optionRes) => {
            setOptionData(optionRes)
            setIsLoading(false)
          })
          .catch((err) => setError(err))
      })
      .catch((err) => setError(err))

    // clean up after component unmounts
    return () => {
      setData(initData)
      setError(null)
    }
  }, [id])

  return {
    data,
    optionData,
    isLoading,
    error,
  }
}

export default useAnalytics
