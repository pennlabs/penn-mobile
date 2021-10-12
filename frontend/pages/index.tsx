import { useContext } from 'react'
import type { NextPage } from 'next'
import Header from '../components/header/Header'
import LandingPage from '../components/landing-page/LandingPage'
import { AuthUserContext, withAuth } from '../context/auth'

const Home: NextPage = () => {
  const { user } = useContext(AuthUserContext)

  return (
    <>
      <Header />
      <LandingPage />
    </>
  )
}

export default withAuth(Home)
