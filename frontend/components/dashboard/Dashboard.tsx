import React, { useState } from 'react'

import { Container, Row } from '@/components/styles/Layout'
import { PageType, PollType, PostType, Status } from '@/utils/types'
import EmptyDashboard from '@/components/dashboard/EmptyDashboard'
import { DashboardHeader } from '@/components/dashboard/DashboardHeader'
import { StatusColumn } from '@/components/dashboard/StatusColumn'

interface DashboardProps {
  postList: PostType[]
  pollList: PollType[]
}

const Dashboard = ({ postList, pollList }: DashboardProps) => {
  const [activeOption, setActiveOption] = useState<PageType>(PageType.POST)

  return (
    <>
      <Container>
        <DashboardHeader
          activeOption={activeOption}
          setActiveOption={setActiveOption}
        />
        {activeOption === PageType.POST && postList.length === 0 ? (
          <EmptyDashboard contentType="post" />
        ) : (
          <Row>
            <StatusColumn status={Status.DRAFT} posts={postList} />
            <StatusColumn status={Status.REVISION} posts={postList} />
            <StatusColumn status={Status.APPROVED} posts={postList} />
          </Row>
        )}
      </Container>
    </>
  )
}

export default Dashboard
