import React from 'react'

import Link from 'next/link'

import { Heading3, InlineText } from '@/components/styles/Text'
import { Card } from '@/components/styles/Card'
import DatePickerForm from '@/components/styles/DatePicker'
import { ContentType, PageType, updateStateType } from '@/utils/types'
import { InfoSpan } from '@/components/styles/Icons'
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
        <ToggleOption active={activeOption === PageType.POST}>
          <InlineText heading color="inherit">
            Post
          </InlineText>
        </ToggleOption>
      </a>
    </Link>
    <Link href={CREATE_POLL_ROUTE}>
      <a>
        <ToggleOption active={activeOption === PageType.POLL}>
          <InlineText heading color="inherit">
            Poll
          </InlineText>
        </ToggleOption>
      </a>
    </Link>
  </Toggle>
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
        startDate={state.start_date}
        expireDate={state.expire_date}
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
        name="club_comment"
        value={state.club_comment}
        placeholder="Enter any comments here."
        updateState={updateState}
        textArea={true}
      />
    </Card>
  </>
)
