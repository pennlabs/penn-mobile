import type { GetServerSidePropsContext } from 'next'

import Dashboard from '@/components/dashboard/Dashboard'
import { AuthUserContext, withAuth } from '@/utils/auth'
import { PollType, PostType, User } from '@/utils/types'
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

export const getServerSidePropsInner = async (
  context: GetServerSidePropsContext
): Promise<{
  props: { postList: PostType[]; pollList: PollType[] }
}> => {
  const postRes = await doApiRequest(`/api/portal/posts/`, {
    method: 'GET',
    headers: context.req ? { cookie: context.req.headers.cookie } : undefined,
  })
  const postList = await postRes.json()

  const pollRes = await doApiRequest(`/api/portal/polls/`, {
    method: 'GET',
    headers: context.req ? { cookie: context.req.headers.cookie } : undefined,
  })
  const pollList = await pollRes.json()

  return {
    props: {
      postList: postList,
      pollList: pollList,
    },
  }
}

export const getServerSideProps = withAuth(getServerSidePropsInner)

export default DashboardPage
