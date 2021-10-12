import type { NextPage } from 'next'
import Header from '../components/header/Header'
import LandingPage from '../components/landing-page/LandingPage'

const Home: NextPage = () => {
  return (
    <>
      <Header />
      <LandingPage />
    </>
  )
}

export default Home
