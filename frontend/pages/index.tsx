import type { GetServerSidePropsContext } from 'next'

import Header from '../components/header/Header'
import LandingPage from '../components/landing-page/LandingPage'
import Dashboard from '../components/dashboard/Dashboard'
import { AuthUserContext, withAuth } from '../context/auth'
import { User } from '../types'

interface IndexPageProps {
  user: User
}

const Home = ({ user }: IndexPageProps) => {
  return (
    <AuthUserContext.Provider value={{ user }}>
      <Header />
      {user ? <Dashboard /> : <LandingPage />}
    </AuthUserContext.Provider>
  )
}

async function getServerSidePropsInner(_context: GetServerSidePropsContext) {
  return { props: {} }
}

export const getServerSideProps = withAuth(getServerSidePropsInner)

export default Home
