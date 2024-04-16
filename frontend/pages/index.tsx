import { GetServerSidePropsContext, GetServerSidePropsResult } from 'next'

import Header from '@/components/header/Header'
import LandingPage from '@/components/landing-page/LandingPage'
import { doApiRequest } from '@/utils/fetch'
import { DASHBOARD_ROUTE } from '@/utils/routes'

const Home = () => {
  return (
    <>
      <Header />
      <LandingPage />
    </>
  )
}

// check if user is logged in and redirect to dashboard if so
export const getServerSideProps = async (
  context: GetServerSidePropsContext
): Promise<GetServerSidePropsResult<{}>> => {
  const res = await doApiRequest('/api/portal/user', {
    credentials: 'include',
    headers: { cookie: context.req.headers.cookie },
  })

  if (
    res.status === 403 &&
    (await res.json()).detail ===
      'Authentication credentials were not provided.'
  ) {
    return { props: {} } // homepage if user not logged in
  }

  // otherwise redirect to dashboard
  const destination = res.ok
    ? DASHBOARD_ROUTE
    : `/api/user/clear-cookies/?next=${DASHBOARD_ROUTE}`

  return { redirect: { destination, permanent: false } }
}

export default Home
