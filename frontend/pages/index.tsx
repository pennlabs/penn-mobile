import Header from '@/components/header/Header'
import LandingPage from '@/components/landing-page/LandingPage'

/**
 * displays landing page at route `/` -- no auth required
 */
const Home = () => {
  return (
    <>
      <Header />
      <LandingPage />
    </>
  )
}

export default Home
