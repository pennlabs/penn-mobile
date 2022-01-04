import React from 'react'
import s from 'styled-components'

import { Col } from '@/components/styles/Layout'
import { Status } from '@/utils/types'
import { colors } from '@/components/styles/colors'
import { Text, InlineText } from '@/components/styles/Text'

interface StatusColumnProps {
  status: Status
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
): { label: string; color: string } => {
  switch (status) {
    case Status.PENDING:
      return {
        label: 'Awaiting Review',
        color: colors.YELLOW,
      }
    case Status.REVISION:
      return {
        label: 'Revision',
        color: colors.ORANGE,
      }
    case Status.APPROVED:
      return {
        label: 'Approved',
        color: colors.IMAGE_BLUE,
      }
    case Status.LIVE:
      return {
        label: 'Live',
        color: colors.GREEN,
      }
    default:
      return {
        label: 'Unknown Status',
        color: 'colors.GRAY',
      }
  }
}

export const StatusColumn = ({ status }: StatusColumnProps) => {
  const { label, color } = getStatusProperties(status)

  return (
    <Col sm={12} md={4} lg={4}>
      <StatusColumnWrapper>
        <StatusHeader>
          <Text heading bold size="18px">
            {label}
          </Text>
        </StatusHeader>
        <div style={{ padding: '1rem' }}>
          <PostCardWrapper color={color}>
            <InlineText heading bold size="14px" color="inherit">
              {label}
            </InlineText>
          </PostCardWrapper>
        </div>
      </StatusColumnWrapper>
    </Col>
  )
}

const PostCardWrapper = s.div<{ color: string }>`
  background-color: ${(props) => props.color};
  border-radius: 10px 10px 0 0;
  padding: 0.5rem;
  color: white;
`
