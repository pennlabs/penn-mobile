import React, { ReactNode } from 'react'
import s from 'styled-components'

import { Col } from '@/components/styles/Layout'
import { PollType, PostType, Status } from '@/utils/types'
import { colors } from '@/components/styles/colors'
import { Text } from '@/components/styles/Text'
import { PollCard, PostCard } from '@/components/dashboard/DashboardCards'

export interface StatusProps {
  color: string
  label: string
  icon: string
}

const StatusColumnWrapper = s.div`
  background-color: ${colors.NAV_BACKGROUND};
  border-radius: 10px;
  margin: 2rem 0.5rem 0 0.5rem;
`

const StatusHeader = s.div`
  background-color: ${colors.WHITE};
  border-radius: 10px 10px 0 0;
  border: 1px solid #EBE8E8;
  padding: 0.25rem 1rem;
`

export const PostStatusColumn = ({
  status,
  cardList,
}: {
  status: Status
  cardList: PostType[]
}) => {
  return (
    <StatusColumn label={getStatusProperties(status).label}>
      {cardList.map((content) => (
        <PostCard post={content} />
      ))}
    </StatusColumn>
  )
}

export const PollStatusColumn = ({
  status,
  cardList,
}: {
  status: Status
  cardList: PollType[]
}) => {
  return (
    <StatusColumn label={getStatusProperties(status).label}>
      {cardList.map((content) => (
        <PollCard poll={content} />
      ))}
    </StatusColumn>
  )
}

const StatusColumn = ({
  label,
  children,
}: {
  label: string
  children: ReactNode
}) => (
  <Col sm={12} md={4} lg={4}>
    <StatusColumnWrapper>
      <StatusHeader>
        <Text heading bold size="18px">
          {label}
        </Text>
      </StatusHeader>
      {children}
    </StatusColumnWrapper>
  </Col>
)

export const getStatusProperties = (status: Status): StatusProps => {
  switch (status) {
    case Status.DRAFT:
      return {
        label: 'Awaiting Review',
        color: colors.YELLOW,
        icon: 'edit',
      }
    case Status.REVISION:
      return {
        label: 'Revision',
        color: colors.ORANGE,
        icon: 'tool',
      }
    case Status.APPROVED:
      return {
        label: 'Approved',
        color: colors.IMAGE_BLUE,
        icon: 'check-circle',
      }
    case Status.LIVE:
      return {
        label: 'Live',
        color: colors.GREEN,
        icon: 'live',
      }
    case Status.EXPIRED:
      return {
        label: 'Expired',
        color: colors.GRAY,
        icon: 'check-circle', // TODO: expired icon?
      }
    default:
      return {
        label: 'Unknown Status',
        color: colors.GRAY,
        icon: 'edit',
      }
  }
}
