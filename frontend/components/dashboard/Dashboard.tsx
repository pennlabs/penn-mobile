import React from 'react'
import s from 'styled-components'
import Link from 'next/link'

import { maxWidth, PHONE } from '@/components/styles/sizes'
import { Container, Group, Row } from '@/components/styles/Layout'
import { Subtitle, Text } from '@/components/styles/Text'
import { IconArrowRight } from '@/components/styles/Icons'
import { colors } from '@/components/styles/colors'

const Dashboard = () => (
  <>
    <Container>
      <EmptyDashboard />
    </Container>
  </>
)

const EmptyDashboardImg = s.img`
  ${maxWidth(PHONE)} {
    display: none;
  }
`

const EmptyDashboard = () => {
  return (
    <Row
      justifyContent="center"
      style={{
        alignItems: 'center',
        height: '99vh',
      }}
    >
      <Group horizontal>
        <EmptyDashboardImg src="/desk-graphic.svg" alt="desk svg" />
        <Group margin="0 2rem" style={{ maxWidth: '24rem' }}>
          <Subtitle>Oh, hello there.</Subtitle>
          <Text>
            Looks like you&apos;re new here.
            <br />
            <br />
            Penn Mobile Portal allows organizations to connect and engage with
            students on the Penn Mobile app. Make posts for recruiting, events,
            or campaigns and watch in real time as users see and interact with
            your content.
          </Text>
          <Text>
            Ready to get started?
            <Link href="/posts/create">
              <a style={{ color: colors.MEDIUM_BLUE }}> Create a new post</a>
            </Link>
            <IconArrowRight />
          </Text>
        </Group>
      </Group>
    </Row>
  )
}

export default Dashboard
