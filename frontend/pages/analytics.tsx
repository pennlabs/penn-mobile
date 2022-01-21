import type { GetServerSidePropsContext } from 'next'
import { AuthUserContext, withAuth } from '@/utils/auth'
import { PollType, PostType, Status, User } from '@/utils/types'
import { Container } from '@/components/styles/Layout'
import { doApiRequest } from '@/utils/fetch'
import Analytics from '@/components/analytics/Analytics'
import { setStatuses } from '@/utils/utils'

interface IndexPageProps {
  user: User
  pollList: PollType[]
  postList: PostType[]
}

const AnalyticsPage = ({ user, pollList, postList }: IndexPageProps) => {
  return (
    <AuthUserContext.Provider value={{ user }}>
      <Container>
        <Analytics postList={postList} pollList={pollList} />
      </Container>
    </AuthUserContext.Provider>
  )
}

export const getServerSidePropsInner = async (
  context: GetServerSidePropsContext
): Promise<{
  props: { postList: PostType[]; pollList: PollType[] }
}> => {
  const data = {
    headers: context.req ? { cookie: context.req.headers.cookie } : undefined,
  }
  const postRes = await doApiRequest('/api/portal/posts/', data)
  const postList = await postRes.json()

  const pollRes = await doApiRequest('/api/portal/polls/', data)
  const pollList = await pollRes.json()

  return {
    props: {
      postList: setStatuses(postList).filter(
        (p) => p.status === Status.LIVE || p.status === Status.EXPIRED
      ),
      pollList: setStatuses(pollList).filter(
        (p) => p.status === Status.LIVE || p.status === Status.EXPIRED
      ),
    },
  }
}

export const getServerSideProps = withAuth(getServerSidePropsInner)

export default AnalyticsPage
