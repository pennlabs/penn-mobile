import React from 'react'

import { PollType, updateStateType } from '@/utils/types'
import { Group } from '@/components/styles/Layout'
import { FormField } from '@/components/styles/Form'
import { IconTimes } from '@/components/styles/Icons'
import { Button } from '@/components/styles/Buttons'
import { colors } from '@/components/styles/colors'

export const MAX_NUM_OPTIONS = 6

interface iPollOptionsProps {
  state: PollType
  updateState: updateStateType
}

const PollOptions = ({ state, updateState }: iPollOptionsProps) => {
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
        Add Option +
      </Button>
    </>
  )
}

export default PollOptions
