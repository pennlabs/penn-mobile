import type { GetServerSidePropsContext } from 'next'

import Header from '@/components/header/Header'
import LandingPage from '@/components/landing-page/LandingPage'
import Dashboard from '@/components/dashboard/Dashboard'
import { AuthUserContext, withAuth } from '@/utils/auth'
import { User } from '@/utils/types'

interface IndexPageProps {
  user: User
}

const Home = ({ user }: IndexPageProps) => {
  return (
    <AuthUserContext.Provider value={{ user }}>
      <Header />
      <Dashboard />
    </AuthUserContext.Provider>
  )
}

async function getServerSidePropsInner(_context: GetServerSidePropsContext) {
  return { props: {} }
}

export const getServerSideProps = withAuth(getServerSidePropsInner)

export default Home
