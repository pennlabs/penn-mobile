import React from 'react'

import Link from 'next/link'

import { Heading3, InlineText } from '@/components/styles/Text'
import { Card } from '@/components/styles/Card'
import DatePickerForm from '@/components/styles/DatePicker'
import { ContentType, PageType, updateStateType } from '@/utils/types'
import { InfoSpan } from '@/components/styles/Icons'
import { Group } from '@/components/styles/Layout'
import { Badge } from '@/components/styles/Badge'
import { FormField } from '@/components/styles/Form'
import { Toggle, ToggleOption } from '../styles/Buttons'
import { CREATE_POLL_ROUTE, CREATE_POST_ROUTE } from '@/utils/routes'

export const CreateContentToggle = ({
  activeOption,
}: {
  activeOption: PageType
}) => (
  <Toggle>
    <Link href={CREATE_POST_ROUTE}>
      <a>
        <ToggleOption active={activeOption == PageType.POST}>
          <InlineText heading color="inherit">
            Post
          </InlineText>
        </ToggleOption>
      </a>
    </Link>
    <Link href={CREATE_POLL_ROUTE}>
      <a>
        <ToggleOption active={activeOption == PageType.POLL}>
          <InlineText heading color="inherit">
            Poll
          </InlineText>
        </ToggleOption>
      </a>
    </Link>
  </Toggle>
)

export const FiltersCard = ({
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

export const DatesCard = ({
  updateState,
  state,
}: {
  updateState: updateStateType
  state: ContentType
}) => (
  <>
    <Heading3>Dates</Heading3>
    <Card>
      <DatePickerForm
        updateState={updateState}
        startDate={state.startDate}
        expireDate={state.expireDate}
      />
    </Card>
  </>
)

export const NotesCard = ({
  state,
  updateState,
}: {
  state: ContentType
  updateState: updateStateType
}) => (
  <>
    <Heading3>
      Notes
      <InfoSpan infoText="Portal admin will see this message during the review process." />
    </Heading3>
    <Card>
      <FormField
        name="userComments"
        value={state.userComments}
        placeholder="Enter any comments here."
        updateState={updateState}
        textArea={true}
      />
    </Card>
  </>
)
