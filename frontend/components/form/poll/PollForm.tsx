import React from 'react'

import { PollType, updateStateType } from '@/utils/types'
import { Button } from '@/components/styles/Buttons'
import { Heading3, Text } from '@/components/styles/Text'
import { colors } from '@/components/styles/colors'
import { Card } from '@/components/styles/Card'
import { FormField } from '@/components/styles/Form'
import { IconPlus, IconTimes } from '@/components/styles/Icons'
import { Group } from '@/components/styles/Layout'
import { DatesCard, NotesCard } from '@/components/form/SharedCards'
import ClubSelect from '@/components/form/ClubSelect'
import FiltersCard, { FilterType } from '@/components/form/Filters'

interface PollFormProps {
  state: PollType
  updateState: updateStateType
  filters: FilterType[]
}

const MAX_NUM_OPTIONS = 6

const PollForm = ({ state, updateState, filters }: PollFormProps) => {
  const updatePollOptions = (newOption: any) => {
    let modified = false
    const key = Number(Object.keys(newOption)[0])
    const newOptions = state.options.map((option) => {
      if (option.id === key) {
        modified = true
        return { id: option.id, choice: newOption[key] }
      }
      return option
    })

    if (!modified) {
      newOptions.push({ id: key, choice: newOption[key] })
    }

    updateState({
      ...state,
      options: newOptions,
    })
  }

  const addPollOption = () => {
    const maxId = Math.max(...state.options.map((opt) => opt.id), 0)

    if (state.options.length < MAX_NUM_OPTIONS) {
      updatePollOptions({
        [maxId + 1]: '',
      })
    }
  }

  const removePollOption = (pollIndex: number) => {
    updateState({
      ...state,
      options: state.options.filter((_, index) => {
        return index !== pollIndex
      }),
    })
  }

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
        {state.options.map((obj, i) => (
          <Group
            horizontal
            style={{ position: 'relative' }}
            key={`group-${obj.id}`}
          >
            <FormField
              name={obj.id.toString()}
              value={obj.choice}
              placeholder="e.g. poll option"
              updateState={updatePollOptions}
              paddingRight={i >= 2}
            />
            {i >= 2 && (
              <div
                onClick={() => removePollOption(i)}
                role="button"
                key={`remove-${obj.id}`}
              >
                <IconTimes />
              </div>
            )}
          </Group>
        ))}
        <Button onClick={addPollOption} color={colors.MEDIUM_BLUE}>
          <IconPlus margin="0 0.5rem 0 0" />
          Add Option
        </Button>
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
