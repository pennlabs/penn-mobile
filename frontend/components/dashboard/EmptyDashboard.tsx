import React from 'react'
import s from 'styled-components'
import Link from 'next/link'

import { maxWidth, PHONE } from '@/components/styles/sizes'
import { Group, Row } from '@/components/styles/Layout'
import { Subtitle, Text } from '@/components/styles/Text'
import { IconArrowRight } from '@/components/styles/Icons'
import { colors } from '@/components/styles/colors'
import { CREATE_POLL_ROUTE, CREATE_POST_ROUTE } from '@/utils/routes'
import { PageType } from '@/utils/types'

const EmptyDashboardImg = s.img`
  ${maxWidth(PHONE)} {
    display: none;
  }
`

const EmptyDashboard = ({ page }: { page: PageType }) => {
  return (
    <Row justifyContent="center" margin="5rem 0">
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
            <Link
              href={
                page === PageType.POST ? CREATE_POST_ROUTE : CREATE_POLL_ROUTE
              }
            >
              <a style={{ color: colors.MEDIUM_BLUE }}>
                {' '}
                Create a new {page.toLowerCase()}
              </a>
            </Link>
            <IconArrowRight />
          </Text>
        </Group>
      </Group>
    </Row>
  )
}

export default EmptyDashboard
