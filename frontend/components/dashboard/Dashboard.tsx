import React, { useEffect, useState } from 'react'

import { useLocalStorage } from '@/hooks/useLocalStorage'
import { Row } from '@/components/styles/Layout'
import { PageType, PollType, PostType, Status } from '@/utils/types'
import EmptyDashboard from '@/components/dashboard/EmptyDashboard'
import EmptyClubDashboard from '@/components/dashboard/EmptyClubs'
import { DashboardHeader } from '@/components/dashboard/DashboardHeader'
import { DashboardStatusColumn } from '@/components/dashboard/DashboardColumn'
import { Heading3 } from '@/components/styles/Text'
import { SuccessMessage } from '@/components/styles/StatusMessage'
import { DashboardProps } from '@/pages/dashboard'
import useClubs from '@/hooks/useClubs'

const Dashboard = ({ postList, pollList }: DashboardProps) => {
  const [activeOption, setActiveOption] = useState<PageType>(PageType.POST)
  const [success, setSuccess] = useLocalStorage<string | null>('success', null)
  const [successMsg, setSuccessMsg] = useState<string | null>(success)

  // clear success message from local storage
  useEffect(() => {
    if (success) {
      setSuccessMsg(success)
      setSuccess(null)
    }
  }, [success, setSuccess])

  const { clubs, clubsLoading } = useClubs()

  if (!clubsLoading && clubs.length === 0) {
    return <EmptyClubDashboard />
  }

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
        <Heading3>Past {`${activeOption}s`}</Heading3>
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
      {successMsg && <SuccessMessage msg={successMsg} />}
      <DashboardHeader
        activeOption={activeOption}
        setActiveOption={setActiveOption}
      />
      <DashboardContent page={activeOption} />
    </>
  )
}

export default Dashboard
