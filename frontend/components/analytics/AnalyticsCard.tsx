import React, { useState } from 'react'
import s from 'styled-components'
import moment from 'moment'

import { colors } from '@/components/styles/colors'
import { isPost, PollType, PostType, Status } from '@/utils/types'
import { Row, Group } from '@/components/styles/Layout'
import { Text, InlineText } from '../styles/Text'
import useAnalytics from '@/hooks/useAnalytics'

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
          width: `${Math.round((number * 100) / total)}%`,
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
          {`${Math.round((number * 100) / total)}%`}
        </div>
        <div
          style={{ textAlign: 'right', fontSize: '0.875rem', color: '#A0AEC0' }}
        >
          {total ? `${number} people` : '10 people'}
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
  const { data, optionData, isLoading, error } = useAnalytics(content.id)
  let total = 0
  optionData?.options?.forEach((x) => {
    total += x.vote_count
  })
  // TODO: add loading state?
  return (
    <AnalyticsBodyWrapper>
      {error}
      {data.poll_statistics.length > 0 && !isLoading && (
        <>
          <Text>Poll Options</Text>
          {data.poll_statistics.map((opt: any, idx: number) => (
            <PollResult
              key={opt.option}
              title={opt.option}
              number={optionData.options[idx].vote_count}
              total={total}
              margin={true}
            />
          ))}
        </>
      )}
    </AnalyticsBodyWrapper>
    // <div
    //   style={{
    //     display: 'flex',
    //     alignItems: 'center',
    //     justifyContent: 'center',
    //     height: '100vh',
    //     width: 'auto',
    //     backgroundColor: '#CBD5E0', // Replace with your desired color
    //   }}
    // >
    //   <div
    //     style={{
    //       padding: '1.5rem',
    //       width: '90%',
    //       backgroundColor: '#F0F4F8', // Replace with your desired color
    //       borderRadius: '0.375rem',
    //       marginBottom: '1.25rem',
    //     }}
    //   >
    //     <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
    //       <div style={{ display: 'flex', flexDirection: 'column' }}>
    //         <p>Jan 19, 2022</p>
    //         <p style={{ fontSize: '0.875rem', color: '#A0AEC0' }}>12:00AM</p>
    //       </div>
    //       <div
    //         style={{
    //           display: 'flex',
    //           backgroundColor: '#E2E8F0', // Replace with your desired color
    //           borderRadius: '0.25rem',
    //           padding: '0.5rem',
    //           gap: '0.5rem',
    //         }}
    //       >
    //         <img
    //           src="https://picsum.photos/90/45"
    //           alt=""
    //           style={{ width: '3.125rem', height: '1.5625rem' }}
    //         />
    //         <div style={{ display: 'flex', flexDirection: 'column' }}>
    //           <p style={{ fontWeight: 'bold', fontSize: '1.125rem', letterSpacing: '0.025em' }}>
    //             Applications for Spring 2020 are open!
    //           </p>
    //           <p style={{ fontSize: '0.875rem', color: '#A0AEC0' }}>Expires Jan 25, 2022 at 12:00AM</p>
    //         </div>
    //       </div>
    //     </div>
    //     <div style={{ display: 'flex', gap: '2.5rem' }}>
    //       {/* Second Row */}
    //       <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
    //         {/* You may replace "ViewsComp" with actual content */}
    //         <div style={{ /* ViewsComp Styles */ }}></div>
    //         <div style={{ /* ViewsComp Styles */ }}></div>
    //       </div>
    //       <div style={{ display: 'flex', flexDirection: 'column', gap: '0.625rem', width: '100%' }}>
    //         <div
    //           style={{
    //             border: '2px solid #CBD5E0', // Replace with your desired color
    //             height: '100%',
    //             borderRadius: '0.375rem',
    //             padding: '0.75rem',
    //             gap: '0.9375rem',
    //           }}
    //         >
    //           <div style={{ fontSize: '1.5rem', fontWeight: 'bold', marginBottom: '0.5rem' }}>
    //             Poll Results
    //           </div>
    //           {/* Replace "PollResult" with actual content */}
    //           <PollResult title="Penn Mobile" percentage={20} />
    //           <PollResult
    //             title="Penn Mobile"
    //             percentage={30}
    //           />
    //           <PollResult title="Penn Mobile" percentage={50} />
    //           <PollResult title="Penn Mobile" percentage={10} />
    //         </div>
    //       </div>
    //     </div>
    //   </div>
    // </div>
  )
}

export default AnalyticsCard
