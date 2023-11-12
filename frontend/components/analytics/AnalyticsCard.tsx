import React, { useState } from 'react'
import s from 'styled-components'
import moment from 'moment'

import {
  faArrowCircleLeft,
  faArrowCircleRight,
} from '@fortawesome/free-solid-svg-icons'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { colors } from '@/components/styles/colors'
import { isPost, PollType, PostType, Status } from '@/utils/types'
import { Row, Group } from '@/components/styles/Layout'
import { Text, InlineText, Heading4, FlexCentered } from '../styles/Text'
import useAnalytics from '@/hooks/useAnalytics'
// import ViewsComponent from './ViewsComponent'
import SimplePieChart from './PieChartComponent'
import VotesBreakdownComponent from './VotesBreakdownComponent'
import { ButtonIcon } from '@/components/styles/Buttons'
import { PieChartToggle } from './PieChartToggle'

interface iAnalyticsCardWrapperProps {
  live: boolean
}

const AnalyticsCardWrapper = s.div<iAnalyticsCardWrapperProps>`
  border-radius: 10px;
  margin: 12px 0px;
  box-shadow: 0 0 8px 3px #d9d9d9;
  padding: 24px 24px 24px 24px;
  background-color: ${colors.WHITE};
  border-left: ${(props) =>
    props.live ? 'solid #3FAA6D 12px' : 'solid #999999 12px'};
  width: 99%;
`

const PrettyBorderWrapper = s.div`
  border: 2px solid #cbd5e0;
  border-radius: 0.375rem;
  padding: 1.5rem;
  width: 100%;
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
  const [isExpanded, setIsExpanded] = useState(false)

  const AnalyticsCardHeader = () => (
    <>
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
    </>
  )

  return (
    <Row>
      <AnalyticsCardWrapper live={content.status === Status.LIVE}>
        <div
          onClick={() => setIsExpanded(!isExpanded)}
          role="button"
          style={{ cursor: 'pointer' }}
        >
          <AnalyticsCardHeader />
        </div>
        {isExpanded && <AnalyticsCardContent content={content} />}
      </AnalyticsCardWrapper>
    </Row>
  )
}

const AnalyticsBodyWrapper = s.div`
  margin: 2rem 0 0 0;
`
const PollResult = ({
  title,
  number,
  total,
  margin = true,
}: {
  title: string
  number: number
  total: number
  margin: boolean
}) => {
  return (
    <div style={{ display: 'flex' }}>
      <div
        style={{
          backgroundColor: colors.LIGHTER_GRAY, // Replace with your desired color
          height: '3rem',
          borderRadius: '0.375rem',
          display: 'flex',
          alignItems: 'center',
          paddingLeft: '1rem',
          whiteSpace: 'nowrap',
          width: `${total === 0 ? 0 : Math.round((number * 100) / total)}%`,
          marginBottom: margin ? '5px' : '0px',
        }}
      >
        {title}
      </div>
      <div style={{ width: '100%' }}>
        <div
          style={{
            textAlign: 'right',
            color: colors.DARK_GRAY,
            fontWeight: 'bold',
          }}
        >
          {`${total === 0 ? 0 : Math.round((number * 100) / total)}%`}
        </div>
        <div
          style={{ textAlign: 'right', fontSize: '0.875rem', color: '#A0AEC0' }}
        >
          {total ? `${number} people` : '0 people'}
        </div>
      </div>
    </div>
  )
}

const AnalyticsCardContent = ({
  content,
}: {
  content: PostType | PollType
}) => {
  const [slide, setSlide] = useState(true)
  const [pieChartOption, setPieChartOption] = useState('school')
  const { data, optionData, isLoading, error } = useAnalytics(content.id)
  let total = 0
  optionData?.options?.forEach((x) => {
    total += x.vote_count
  })
  const targetPopulationsData = data?.poll_statistics || []
  const schoolVotes = {}
  const yearVotes = {}

  targetPopulationsData.forEach((item) => {
    if (item.breakdown && item.breakdown.SCHOOL) {
      const schools = item.breakdown.SCHOOL
      Object.keys(schools).forEach((school) => {
        if (schoolVotes[school]) {
          schoolVotes[school] += schools[school]
        } else {
          schoolVotes[school] = schools[school]
        }
      })
    }
    if (item.breakdown && item.breakdown.YEAR) {
      const years = item.breakdown.YEAR
      Object.keys(year).forEach((year) => {
        if (yearVotes[year]) {
          yearVotes[year] += years[year]
        } else {
          yearVotes[year] = years[year]
        }
      })
    }
  })

  let totalVoteCount = 0
  data?.poll_statistics?.map((opt: any, idx: number) => {
    totalVoteCount += optionData.options[idx]?.vote_count || 0
  })

  // TODO: add loading state?
  return (
    <AnalyticsBodyWrapper>
      {error}
      {'title' in content && (
        <div
          style={{
            display: 'flex',
            justifyContent: 'center',
            fontSize: '1rem',
            fontWeight: '500',
          }}
        >
          Coming Soon!
        </div>
      )}
      {'question' in content && data.poll_statistics.length > 0 && !isLoading && (
        <div style={{ display: 'flex' }}>
          <PrettyBorderWrapper>
            <FlexCentered>
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  height: '100%',
                  paddingRight: 10,
                }}
              >
                <ButtonIcon onClick={() => setSlide(!slide)}>
                  <FontAwesomeIcon icon={faArrowCircleLeft} size="lg" />
                </ButtonIcon>
              </div>
              <div style={{ width: '90%' }}>
                {slide ? (
                  <div>
                    <Heading4 marginBottom="1rem">Poll Results</Heading4>
                    {data.poll_statistics.map((opt: any, idx: number) => {
                      return (
                        <PollResult
                          key={opt.option}
                          title={opt.option}
                          number={optionData.options[idx].vote_count || 0}
                          total={total}
                          margin={true}
                        />
                      )
                    })}
                  </div>
                ) : (
                  <div
                    style={{ display: 'flex', justifyContent: 'space-between' }}
                  >
                    <div>
                      <Heading4 marginBottom="1rem">Votes Breakdown</Heading4>
                      <PieChartToggle
                        activeOption={pieChartOption}
                        setActiveOption={setPieChartOption}
                      />
                      <div style={{ height: 20 }} />
                      <VotesBreakdownComponent
                        schoolData={schoolVotes}
                        yearData={yearVotes}
                        mode={pieChartOption}
                      />
                    </div>
                    <SimplePieChart
                      schoolData={schoolVotes}
                      yearData={yearVotes}
                      mode={pieChartOption}
                      uniqueVotes={totalVoteCount}
                    />
                  </div>
                )}
              </div>
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  height: '100%',
                  paddingLeft: 10,
                }}
              >
                <ButtonIcon onClick={() => setSlide(!slide)}>
                  <FontAwesomeIcon icon={faArrowCircleRight} size="lg" />
                </ButtonIcon>
              </div>
            </FlexCentered>
          </PrettyBorderWrapper>
        </div>
      )}
    </AnalyticsBodyWrapper>
  )
}

export default AnalyticsCard
