import React, { useContext } from 'react'
import Link from 'next/link'

import { Group, Row } from '@/components/styles/Layout'
import { Subtitle, InlineText } from '@/components/styles/Text'
import { colors } from '@/components/styles/colors'
import { PageType } from '@/utils/types'
import { Button, Toggle, ToggleOption } from '@/components/styles/Buttons'
import { CREATE_POLL_ROUTE, CREATE_POST_ROUTE } from '@/utils/routes'
import { IconPlus } from '@/components/styles/Icons'
import { AuthUserContext } from '@/utils/auth'

export const DashboardHeader = ({
  activeOption,
  setActiveOption,
}: {
  activeOption: PageType
  setActiveOption: React.Dispatch<React.SetStateAction<PageType>>
}) => {
  const { user } = useContext(AuthUserContext)

  const DashboardToggle = () => (
    <Toggle>
      <ToggleOption
        active={activeOption === PageType.POST}
        onClick={() => setActiveOption(PageType.POST)}
      >
        <InlineText heading color="inherit">
          Posts
        </InlineText>
      </ToggleOption>
      <ToggleOption
        active={activeOption === PageType.POLL}
        onClick={() => setActiveOption(PageType.POLL)}
      >
        <InlineText heading color="inherit">
          Polls
        </InlineText>
      </ToggleOption>
    </Toggle>
  )

  return (
    <Row justifyContent="space-between">
      <Subtitle>{user?.clubs[0].name}</Subtitle>
      <Group horizontal alignItems="center">
        <DashboardToggle />
        <Link
          href={
            activeOption === PageType.POST
              ? CREATE_POST_ROUTE
              : CREATE_POLL_ROUTE
          }
        >
          <a>
            <Button color={colors.GREEN} round style={{ margin: '0 0 0 1rem' }}>
              Create <IconPlus margin="0 0 0 0.5rem" />
            </Button>
          </a>
        </Link>
      </Group>
    </Row>
  )
}
