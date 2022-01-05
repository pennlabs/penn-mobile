import React from 'react'

import { Heading3, InlineText } from '@/components/styles/Text'
import { Card } from '@/components/styles/Card'
import { ContentType, updateStateType } from '@/utils/types'
import { InfoSpan } from '@/components/styles/Icons'
import { Group } from '@/components/styles/Layout'
import { Badge } from '@/components/styles/Badge'

const FiltersCard = ({
  state,
  updateState,
}: {
  state: ContentType
  updateState: updateStateType
}) => (
  <>
    <Heading3>
      Filters
      <InfoSpan infoText="If no filters are applied, the post will be shared with all Penn Mobile users." />
    </Heading3>
    <Card>
      <Group horizontal justifyContent="space-between">
        <InlineText
          bold
          heading
          style={{ lineHeight: '1.75rem', width: '5.5rem' }}
        >
          Class Year
        </InlineText>
        <Badge>2021</Badge>
        <Badge>2022</Badge>
        <Badge>2023</Badge>
        <Badge>2024</Badge>
      </Group>
      <Group horizontal justifyContent="space-between">
        <InlineText
          bold
          heading
          style={{ lineHeight: '1.75rem', width: '5.5rem' }}
        >
          School
        </InlineText>
        <Badge>College</Badge>
        <Badge>Wharton</Badge>
        <Badge>SEAS</Badge>
        <Badge>Nursing</Badge>
      </Group>
    </Card>
  </>
)

export default FiltersCard
