import { PostType, PollType, Status } from '@/utils/types'

// sets live and expired statuses. returns an array of posts/polls sorted by start date
// with live posts first
export const setStatuses = (contentList: PostType[] | PollType[]) => {
  const contentWithStatus = contentList.map((p: any) => {
    if (new Date(p.expire_date) < new Date()) {
      p.status = Status.EXPIRED
      return p
    }
    if (p.status === Status.APPROVED && new Date(p.start_date) < new Date()) {
      p.status = Status.LIVE
    }
    return p
  })

  const sortedByDate = contentWithStatus.sort((a, b) => {
    if (new Date(a.start_date) < new Date(b.start_date)) {
      return 1
    } else if (new Date(a.start_date) > new Date(b.start_date)) {
      return -1
    }
    return 0
  })

  return sortedByDate.sort((a, _) => (a.status === Status.LIVE ? -1 : 1))
}
