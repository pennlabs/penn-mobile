import React, { useState } from 'react'
import _ from 'lodash'

import { Container, Row } from '@/components/styles/Layout'
import { PageType, PollType, PostType, Status } from '@/utils/types'
import EmptyDashboard from '@/components/dashboard/EmptyDashboard'
import { DashboardHeader } from '@/components/dashboard/DashboardHeader'
import {
  PostStatusColumn,
  PollStatusColumn,
} from '@/components/dashboard/DashboardColumn'
import { Heading3 } from '@/components/styles/Text'

interface DashboardProps {
  postList: PostType[]
  pollList: PollType[]
}

const Dashboard = ({ postList, pollList }: DashboardProps) => {
  const [activeOption, setActiveOption] = useState<PageType>(PageType.POLL)

  const DashboardContent = ({ page }: { page: PageType }) => {
    const activeList = page === PageType.POST ? postList : pollList
    if (activeList.length === 0) {
      return <EmptyDashboard page={page} />
    }
    return page === PageType.POST ? (
      <Row>
        <PostStatusColumn status={Status.DRAFT} cardList={postList} />
        <PostStatusColumn status={Status.REVISION} cardList={postList} />
        <PostStatusColumn status={Status.APPROVED} cardList={postList} />
      </Row>
    ) : (
      <Row>
        <PollStatusColumn
          status={Status.DRAFT}
          cardList={pollList.filter((p) => p.status === Status.DRAFT)}
        />
        <PollStatusColumn
          status={Status.REVISION}
          cardList={pollList.filter((p) => p.status === Status.REVISION)}
        />
        <PollStatusColumn
          status={Status.APPROVED}
          cardList={pollList.filter(
            (p) => p.status === Status.APPROVED || p.status === Status.LIVE
          )}
        />
      </Row>
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

        <Heading3>Past {`${_.startCase(_.toLower(activeOption))}s`}</Heading3>
        <Row>
          {activeOption === PageType.POST ? (
            <PostStatusColumn status={Status.EXPIRED} cardList={postList} />
          ) : (
            <PollStatusColumn
              status={Status.EXPIRED}
              cardList={pollList.filter((p) => p.status === Status.EXPIRED)}
            />
          )}
        </Row>
      </Container>
    </>
  )
}

export default Dashboard
