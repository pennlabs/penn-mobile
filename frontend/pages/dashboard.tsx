import type { GetServerSidePropsContext } from 'next'

import Dashboard from '@/components/dashboard/Dashboard'
import { AuthUserContext, withAuth } from '@/utils/auth'
import { PollType, PostType, User } from '@/utils/types'
import { doApiRequest } from '@/utils/fetch'
import { Container } from '@/components/styles/Layout'
import { setStatuses } from '@/utils/utils'

export interface DashboardProps {
  postList: PostType[]
  pollList: PollType[]
}

const DashboardPage = ({
  user,
  postList,
  pollList,
}: { user: User } & DashboardProps) => {
  return (
    <AuthUserContext.Provider value={{ user }}>
      <Container>
        <Dashboard postList={postList} pollList={pollList} />
      </Container>
    </AuthUserContext.Provider>
  )
}

export const getServerSidePropsInner = async (
  context: GetServerSidePropsContext
): Promise<{ props: DashboardProps }> => {
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
