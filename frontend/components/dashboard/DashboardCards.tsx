import React, { ReactNode } from 'react'
import Link from 'next/link'
import s from 'styled-components'

import { colors } from '@/components/styles/colors'
import { InlineText, Text } from '@/components/styles/Text'
import { Icon } from '@/components/styles/Icons'
import { Group } from '@/components/styles/Layout'
import {
  getStatusProperties,
  StatusProps,
} from '@/components/dashboard/DashboardColumn'
import { PollType, PostType } from '@/utils/types'

const DashboardCardWrapper = ({
  href,
  children,
}: {
  href: string
  children: ReactNode
}) => (
  <Link href={href}>
    <a>
      <div style={{ padding: '1rem' }}>{children}</div>
    </a>
  </Link>
)

const DashboardCardHeaderWrapper = s.div<{ color: string }>`
  background-color: ${(props) => props.color};
  border-radius: 10px 10px 0 0;
  padding: 0.5rem;
  color: white;
  display: flex;
  justify-content: space-between;
  box-shadow: 0px 2px 10px rgba(0, 0, 0, 0.25);
  line-height: 2rem;
`

const DashboardCardBody = s.div`
  background-color: ${colors.WHITE};
  border-radius: 0 0 10px 10px;
  box-shadow: 0px 2px 10px rgba(0, 0, 0, 0.25);
`

const DashboardCardHeader = ({ statusProps }: { statusProps: StatusProps }) => (
  <DashboardCardHeaderWrapper color={statusProps.color}>
    <InlineText heading bold size="14px" color="inherit" centerY>
      {statusProps.label}
    </InlineText>
    <Icon name={statusProps.icon} />
  </DashboardCardHeaderWrapper>
)

export const PostCard = ({ post }: { post: PostType }) => {
  return (
    <DashboardCardWrapper href={`/posts/${post.id}`}>
      <DashboardCardHeader statusProps={getStatusProperties(post.status)} />
      <DashboardCardBody>
        <div
          style={{
            backgroundSize: 'cover',
            backgroundPosition: 'center',
            backgroundRepeat: 'no-repeat',
            height: 175,
            backgroundImage: `url("${post.image_url}")`,
          }}
        />
        <div style={{ padding: '0.5rem' }}>
          <Group horizontal justifyContent="space-between">
            <InlineText size="10px" bold>
              {post.club_code}
            </InlineText>
            <InlineText size="10px" bold>
              {post.start_date &&
                new Date(post.start_date).toLocaleDateString()}
            </InlineText>
          </Group>
          <Text size="16px" bold>
            {post.title}
          </Text>
        </div>
      </DashboardCardBody>
    </DashboardCardWrapper>
  )
}

export const PollCard = ({ poll }: { poll: PollType }) => {
  return (
    <DashboardCardWrapper href={`/polls/${poll.id}`}>
      <DashboardCardHeader statusProps={getStatusProperties(poll.status)} />
      <DashboardCardBody>
        <div style={{ padding: '0.5rem' }}>
          <Group horizontal justifyContent="space-between">
            <InlineText size="10px" bold>
              {poll.club_code}
            </InlineText>
            <InlineText size="10px" bold>
              {poll.start_date &&
                new Date(poll.start_date).toLocaleDateString()}
            </InlineText>
          </Group>
          <Text size="16px" bold>
            {poll.question}
          </Text>
        </div>
      </DashboardCardBody>
    </DashboardCardWrapper>
  )
}
