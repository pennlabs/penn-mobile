import type { GetServerSidePropsContext } from 'next'
import { AuthUserContext, withAuth } from '@/utils/auth'
import { User } from '@/utils/types'
import { Container, Group } from '@/components/styles/Layout'
import { Heading3 } from '@/components/styles/Text'

interface IndexPageProps {
  user: User
}

const Settings = ({ user }: IndexPageProps) => {
  return (
    <AuthUserContext.Provider value={{ user }}>
      <Container>
        <Group padding="4rem">
          <Heading3 style={{ marginTop: 0 }}>Analytics</Heading3>
        </Group>
      </Container>
    </AuthUserContext.Provider>
  )
}

async function getServerSidePropsInner(_context: GetServerSidePropsContext) {
  return { props: {} }
}

export const getServerSideProps = withAuth(getServerSidePropsInner)

export default Settings
