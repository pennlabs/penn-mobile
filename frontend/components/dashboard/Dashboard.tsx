import React, { useState } from 'react'
import _ from 'lodash'

import { Container, Row } from '@/components/styles/Layout'
import { PageType, PollType, PostType, Status } from '@/utils/types'
import EmptyDashboard from '@/components/dashboard/EmptyDashboard'
import { DashboardHeader } from '@/components/dashboard/DashboardHeader'
import { DashboardStatusColumn } from '@/components/dashboard/DashboardColumn'
import { Heading3 } from '@/components/styles/Text'

interface DashboardProps {
  postList: PostType[]
  pollList: PollType[]
}

const Dashboard = ({ postList, pollList }: DashboardProps) => {
  const [activeOption, setActiveOption] = useState<PageType>(PageType.POLL)

  const DashboardContent = ({ page }: { page: PageType }) => {
    const activeList: (PollType | PostType)[] =
      page === PageType.POST ? postList : pollList

    if (activeList.length === 0) {
      return <EmptyDashboard page={page} />
    }
    return (
      <>
        <Row>
          <DashboardStatusColumn
            status={Status.DRAFT}
            cardList={activeList.filter((p) => p.status === Status.DRAFT)}
          />
          <DashboardStatusColumn
            status={Status.REVISION}
            cardList={activeList.filter((p) => p.status === Status.REVISION)}
          />
          <DashboardStatusColumn
            status={Status.APPROVED}
            cardList={activeList.filter(
              (p) => p.status === Status.APPROVED || p.status === Status.LIVE
            )}
          />
        </Row>
        <Heading3>Past {`${_.startCase(_.toLower(activeOption))}s`}</Heading3>
        <Row>
          <DashboardStatusColumn
            status={Status.EXPIRED}
            cardList={activeList.filter((p) => p.status === Status.EXPIRED)}
          />
        </Row>
      </>
    )
  }

  return (
    <>
      <Container>
        <DashboardHeader
          activeOption={activeOption}
          setActiveOption={setActiveOption}
        />
        <DashboardContent page={activeOption} />
      </Container>
    </>
  )
}

export default Dashboard
