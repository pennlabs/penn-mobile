import React from 'react'
import s from 'styled-components'

import { Col, Group } from '@/components/styles/Layout'
import { PostType, Status } from '@/utils/types'
import { colors } from '@/components/styles/colors'
import { Text, InlineText } from '@/components/styles/Text'
import { Icon } from '@/components/styles/Icons'

interface StatusColumnProps {
  status: Status
  posts: PostType[]
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

const getStatusProperties = (
  status: Status
): { label: string; color: string; icon: string } => {
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
        icon: 'video',
      }
    default:
      return {
        label: 'Unknown Status',
        color: 'colors.GRAY',
        icon: 'edit',
      }
  }
}

export const StatusColumn = ({ status, posts }: StatusColumnProps) => {
  const { label, color, icon } = getStatusProperties(status)

  return (
    <Col sm={12} md={4} lg={4}>
      <StatusColumnWrapper>
        <StatusHeader>
          <Text heading bold size="18px">
            {label}
          </Text>
        </StatusHeader>
        {posts.map((post) => (
          <PostCard post={post} label={label} color={color} icon={icon} />
        ))}
      </StatusColumnWrapper>
    </Col>
  )
}

interface PostCardProps {
  post: PostType
  label: string
  color: string
  icon: string
}

const PostCard = ({ post, label, color, icon }: PostCardProps) => (
  <DashboardCardWrapper>
    <DashboardCardHeader color={color}>
      <InlineText heading bold size="14px" color="inherit" centerY>
        {label}
      </InlineText>
      <Icon name={icon} />
    </DashboardCardHeader>
    <DashboardCardBody>
      <Group horizontal justifyContent="space-between">
        {/* <InlineText size="10px" bold>
          {post.club_code}
        </InlineText> */}
      </Group>
    </DashboardCardBody>
  </DashboardCardWrapper>
)

const DashboardCardWrapper = s.div`
  padding: 1rem;
`

const DashboardCardHeader = s.div<{ color: string }>`
  background-color: ${(props) => props.color};
  border-radius: 10px 10px 0 0;
  padding: 0.5rem;
  color: white;
  display: flex;
  justify-content: space-between;
  box-shadow: 0px 2px 10px rgba(0, 0, 0, 0.25);
`

const DashboardCardBody = s.div`
  background-color: ${colors.WHITE};
  padding: 0.5rem;
  border-radius: 0 0 10px 10px;
  box-shadow: 0px 2px 10px rgba(0, 0, 0, 0.25);
`
