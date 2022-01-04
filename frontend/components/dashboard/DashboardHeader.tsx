import React from 'react'
import Link from 'next/link'

import { Group, Row } from '@/components/styles/Layout'
import { Heading3, InlineText } from '@/components/styles/Text'
import { colors } from '@/components/styles/colors'
import { PageType, PollType, PostType } from '@/utils/types'
import { Button, Toggle, ToggleOption } from '@/components/styles/Buttons'
import { CREATE_POLL_ROUTE, CREATE_POST_ROUTE } from '@/utils/routes'

export const DashboardHeader = ({
  activeOption,
  setActiveOption,
}: {
  activeOption: PageType
  setActiveOption: React.Dispatch<React.SetStateAction<PageType>>
}) => {
  const DashboardToggle = () => (
    <Toggle>
      <ToggleOption
        active={activeOption == PageType.POST}
        onClick={() => setActiveOption(PageType.POST)}
      >
        <InlineText heading color="inherit">
          Posts
        </InlineText>
      </ToggleOption>
      <ToggleOption
        active={activeOption == PageType.POLL}
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
      <Heading3>Penn Labs</Heading3>
      <Group horizontal alignItems="center">
        <DashboardToggle />
        <Link
          href={
            activeOption == PageType.POST
              ? CREATE_POST_ROUTE
              : CREATE_POLL_ROUTE
          }
        >
          <a>
            <Button color={colors.GREEN} round style={{ margin: '0 0 0 1rem' }}>
              Create
            </Button>
          </a>
        </Link>
      </Group>
    </Row>
  )
}
