import type { GetServerSidePropsContext } from 'next'

import Dashboard from '@/components/dashboard/Dashboard'
import { AuthUserContext, withAuth } from '@/utils/auth'
import { PollType, PostType, Status, User } from '@/utils/types'
import { doApiRequest } from '@/utils/fetch'

interface DashboardPageProps {
  user: User
  postList: PostType[]
  pollList: PollType[]
}

const DashboardPage = ({ user, postList, pollList }: DashboardPageProps) => {
  return (
    <AuthUserContext.Provider value={{ user }}>
      <Dashboard postList={postList} pollList={pollList} />
    </AuthUserContext.Provider>
  )
}

const setStatuses = (contentList: PostType[] | PollType[]) => {
  return contentList.map((p: any) => {
    if (new Date(p.expire_date) < new Date()) {
      p.status = Status.EXPIRED
      return p
    }
    if (p.status === Status.APPROVED && new Date(p.start_date) < new Date()) {
      p.status = Status.LIVE
    }
    return p
  })
}

export const getServerSidePropsInner = async (
  context: GetServerSidePropsContext
): Promise<{
  props: { postList: PostType[]; pollList: PollType[] }
}> => {
  const postRes = await doApiRequest('/api/portal/posts/', {
    headers: context.req ? { cookie: context.req.headers.cookie } : undefined,
  })
  const postList = await postRes.json()

  const pollRes = await doApiRequest('/api/portal/polls/', {
    headers: context.req ? { cookie: context.req.headers.cookie } : undefined,
  })
  const pollList = await pollRes.json()

  return {
    props: {
      postList: setStatuses(postList) as PostType[],
      pollList: setStatuses(pollList) as PollType[],
    },
  }
}

export const getServerSideProps = withAuth(getServerSidePropsInner)

export default DashboardPage
