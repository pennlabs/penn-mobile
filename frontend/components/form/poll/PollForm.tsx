import React from 'react'

import { PollType, updateStateType } from '../../../types'
import { Button } from '../../styles/Buttons'
import { Heading3, Text } from '../../styles/Text'
import { colors } from '../../../utils/colors'
import { Card } from '../../styles/Card'
import { FormField } from '../../styles/Form'
import { InfoSpan, IconPlus, IconTimes } from '../../styles/Icons'
import { Group } from '../../styles/Layout'
import DatePickerForm from '../DatePicker'

interface PollFormProps {
  state: PollType
  updateState: updateStateType
}

const MAX_NUM_OPTIONS = 6

const PollForm = ({ state, updateState }: PollFormProps) => {
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
        <FormField
          label="Organization"
          name="source"
          value={state.source}
          placeholder="e.g. Daily Pennsylvanian"
          updateState={updateState}
        />
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

      <Heading3>Visibility</Heading3>
      <Card>
        <Text bold>Dates</Text>
        <DatePickerForm
          updateState={updateState}
          startDate={state.startDate}
          expireDate={state.expireDate}
        />
      </Card>

      <Heading3>
        Notes
        <InfoSpan infoText="Portal administrators will see this message during the review process." />
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
}

export default PollForm
