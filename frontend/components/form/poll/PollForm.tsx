import React from 'react'

import { PollType, updateStateType } from '@/utils/types'
import { Heading3, Text } from '@/components/styles/Text'
import { Card } from '@/components/styles/Card'
import { FormField } from '@/components/styles/Form'
import { DatesCard, NotesCard } from '@/components/form/SharedCards'
import ClubSelect from '@/components/form/ClubSelect'
import FiltersCard, { FilterType } from '@/components/form/Filters'
import PollOptions from './PollOptions'

interface PollFormProps {
  state: PollType
  updateState: updateStateType
  filters: FilterType[]
}

const PollForm = ({ state, updateState, filters }: PollFormProps) => {
  return (
    <>
      <Heading3>Content</Heading3>
      <Card>
        <FormField
          label="Question"
          name="question"
          value={state.question}
          placeholder={"e.g. What do you think about Penn's COVID response?"}
          updateState={updateState}
        />

        <Text bold>Club</Text>
        <ClubSelect updateState={updateState} clubCode={state.club_code} />

        <Text bold>Poll Options</Text>
        <PollOptions state={state} updateState={updateState} />
      </Card>

      <DatesCard updateState={updateState} state={state} />

      <FiltersCard
        updateState={updateState}
        targetPopulations={state.target_populations}
        filters={filters}
      />

      <NotesCard updateState={updateState} state={state} />
    </>
  )
}

export default PollForm
