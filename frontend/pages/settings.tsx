import type { GetServerSidePropsContext } from 'next'
import Link from 'next/link'

import { LANDING_PAGE_ROUTE } from '@/utils/routes'
import { AuthUserContext, withAuth } from '@/utils/auth'
import { User } from '@/utils/types'
import { colors } from '@/components/styles/colors'
import { Button } from '@/components/styles/Buttons'
import { Container } from '@/components/styles/Layout'
import { Heading3 } from '@/components/styles/Text'

interface IndexPageProps {
  user: User
}

const Settings = ({ user }: IndexPageProps) => {
  return (
    <AuthUserContext.Provider value={{ user }}>
      <Container>
        <Heading3>Settings</Heading3>
        <Link href={`/api/accounts/logout/?next=${LANDING_PAGE_ROUTE}`}>
          <a>
            <Button color={colors.MEDIUM_BLUE}>Logout</Button>
          </a>
        </Link>
      </Container>
    </AuthUserContext.Provider>
  )
}

async function getServerSidePropsInner(_context: GetServerSidePropsContext) {
  return { props: {} }
}

export const getServerSideProps = withAuth(getServerSidePropsInner)

export default Settings
