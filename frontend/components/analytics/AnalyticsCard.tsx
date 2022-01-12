import React from 'react'
import s from 'styled-components'
import moment from 'moment'

import { colors } from '@/components/styles/colors'
import { isPost, PollType, PostType, Status } from '@/utils/types'
import { Row, Group } from '@/components/styles/Layout'
import { Text, InlineText } from '../styles/Text'

interface iAnalyticsCardWrapperProps {
  live: boolean
}

const AnalyticsCardWrapper = s.div<iAnalyticsCardWrapperProps>`
  border-radius: 10px;
  margin: 12px 0px;
  box-shadow: 0 0 8px 3px #d9d9d9;
  padding: 24px 24px 24px 24px;
  background-color: ${colors.WHITE};
  cursor: pointer;
  border-left: ${(props) =>
    props.live ? 'solid #3FAA6D 12px' : 'solid #999999 12px'};
  width: 99%;
  align-items: center;
  display: flex;
`

// returns Month Day, Year string from Date Object (ex: Jan 01, 2020)
const formatDate = (date: Date | null) => {
  return date ? moment(date).format('MMM Do, YYYY') : 'invalid date'
}

// returns time from Date object (ex: 1:00 PM)
const formatTime = (date: Date | null) => {
  return date ? moment(date).format('h:mmA') : 'invalid date'
}

const AnalyticsCard = ({ content }: { content: PostType | PollType }) => {
  return (
    <Row>
      <AnalyticsCardWrapper live={content.status === Status.LIVE}>
        <Group style={{ width: '16%' }}>
          <Text size="14px" noMarginTop>
            {formatDate(content.start_date)}
          </Text>
          <InlineText size="10px" bold color={colors.DARK_GRAY}>
            {formatTime(content.start_date)}
          </InlineText>
        </Group>
        {isPost(content) && (
          <img
            src={content.image_url}
            alt="post"
            width={125}
            height={60}
            style={{ marginRight: '1rem' }}
          />
        )}
        <Group>
          <Text bold noMarginTop>
            {isPost(content) ? content.title : content.question}
          </Text>
          <InlineText size="10px" bold color={colors.DARK_GRAY}>
            Expires {formatDate(content.expire_date)}
          </InlineText>
        </Group>
      </AnalyticsCardWrapper>
    </Row>
  )
}

export default AnalyticsCard
