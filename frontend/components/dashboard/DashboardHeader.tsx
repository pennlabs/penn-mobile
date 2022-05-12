import React from 'react'
import Link from 'next/link'
import Skeleton from 'react-loading-skeleton'
import 'react-loading-skeleton/dist/skeleton.css'

import { Group, Row } from '@/components/styles/Layout'
import { Subtitle } from '@/components/styles/Text'
import { colors } from '@/components/styles/colors'
import { PageType } from '@/utils/types'
import { Button, PostPollToggle } from '@/components/styles/Buttons'
import { CREATE_POLL_ROUTE, CREATE_POST_ROUTE } from '@/utils/routes'
import useClubs from '@/hooks/useClubs'

export const DashboardHeader = ({
  activeOption,
  setActiveOption,
}: {
  activeOption: PageType
  setActiveOption: React.Dispatch<React.SetStateAction<PageType>>
}) => {
  const { clubs, clubsLoading } = useClubs()

  return (
    <Row justifyContent="space-between">
      <Subtitle>
        {clubsLoading ? (
          <Skeleton width={250} style={{ flexGrow: 1 }} />
        ) : (
          // TODO: add club select
          clubs[0]?.name
        )}
      </Subtitle>
      <Group horizontal alignItems="center">
        <PostPollToggle
          activeOption={activeOption}
          setActiveOption={setActiveOption}
        />
        <Link
          href={
            activeOption === PageType.POST
              ? CREATE_POST_ROUTE
              : CREATE_POLL_ROUTE
          }
        >
          <a>
            <Button color={colors.GREEN} round style={{ margin: '0 0 0 1rem' }}>
              Create +
            </Button>
          </a>
        </Link>
      </Group>
    </Row>
  )
}
