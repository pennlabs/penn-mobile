import React from 'react'
import s from 'styled-components'
import Link from 'next/link'

import { maxWidth, PHONE } from '@/components/styles/sizes'
import { Group, Row } from '@/components/styles/Layout'
import { Heading3 } from '@/components/styles/Text'
import { colors } from '@/components/styles/colors'
import { Button } from '@/components/styles/Buttons'

const EmptyClubDashboardImg = s.img`
  ${maxWidth(PHONE)} {
    display: none;
  }
`

/**
 * if the user has no clubs, show empty club page and redirect to PennClubs
 */
const EmptyClubDashboard = () => {
  return (
    <Row justifyContent="center" margin="5rem 0">
      <Group
        center
        padding="0 20%"
        justifyContent="center"
        alignItems="center"
        style={{ textAlign: 'center' }}
      >
        <EmptyClubDashboardImg src="/empty-clubs.svg" alt="desk svg" />
        <Heading3>
          Looks like you&apos;re not in any clubs.
          <br />
          Check your club membership on Penn Clubs.
        </Heading3>
        <Button
          color={colors.MEDIUM_BLUE}
          style={{ display: 'block', margin: '0 auto' }}
        >
          <Link href="https://pennclubs.com/">
            <a target="_blank" style={{ color: colors.WHITE }}>
              Go to Penn Clubs
            </a>
          </Link>
        </Button>
      </Group>
    </Row>
  )
}

export default EmptyClubDashboard
