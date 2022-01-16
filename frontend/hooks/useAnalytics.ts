import { useEffect, useState } from 'react'

import { doApiRequest } from '@/utils/fetch'

const useAnalytics = (id: number | undefined) => {
  const [data, setData] = useState({})
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
      setData({})
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
