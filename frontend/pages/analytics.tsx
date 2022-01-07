import type { GetServerSidePropsContext } from 'next'
import { AuthUserContext, withAuth } from '@/utils/auth'
import { User } from '@/utils/types'
import { Container } from '@/components/styles/Layout'
import { Heading3 } from '@/components/styles/Text'

interface IndexPageProps {
  user: User
}

const Settings = ({ user }: IndexPageProps) => {
  return (
    <AuthUserContext.Provider value={{ user }}>
      <Container>
        <Heading3>Analytics</Heading3>
      </Container>
    </AuthUserContext.Provider>
  )
}

async function getServerSidePropsInner(_context: GetServerSidePropsContext) {
  return { props: {} }
}

export const getServerSideProps = withAuth(getServerSidePropsInner)

export default Settings
