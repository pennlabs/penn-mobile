import React, { useState } from 'react'

import { PageType, PollType, PostType } from '@/utils/types'
import { PostPollToggle } from '@/components/styles/Buttons'
import { Row } from '@/components/styles/Layout'
import { Subtitle } from '@/components/styles/Text'
import EmptyDashboard from '@/components/dashboard/EmptyDashboard'
import AnalyticsCard from '@/components/analytics/AnalyticsCard'

interface AnalyticsProps {
  postList: PostType[]
  pollList: PollType[]
}

const Analytics = ({ postList, pollList }: AnalyticsProps) => {
  const [activeOption, setActiveOption] = useState<PageType>(PageType.POLL)

  const AnalyticsContent = ({ page }: { page: PageType }) => {
    const activeList: (PollType | PostType)[] =
      page === PageType.POST ? postList : pollList

    if (activeList.length === 0) {
      // TODO: empty analytics page?
      return <EmptyDashboard page={page} />
    }
    return (
      <>
        {activeList.map((p) => (
          <AnalyticsCard key={p.id} content={p} />
        ))}
      </>
    )
  }

  return (
    <>
      <Row justifyContent="space-between" alignItems="center">
        <Subtitle>All {`${activeOption}s`} </Subtitle>
        <PostPollToggle
          activeOption={activeOption}
          setActiveOption={setActiveOption}
        />
      </Row>
      <Row>
        <AnalyticsContent page={activeOption} />
      </Row>
    </>
  )
}

export default Analytics
