import useSWR from 'swr'
import { Club } from '@/utils/types'

const useClubs = (): {
  clubs: Club[]
  clubsLoading: boolean
  clubsError: Object
} => {
  const { data, error } = useSWR('/api/portal/clubs')

  return { clubs: data?.clubs, clubsLoading: !data, clubsError: error }
}

export default useClubs
