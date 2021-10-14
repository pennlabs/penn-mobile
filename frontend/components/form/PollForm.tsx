import React, { useState } from 'react'

import { Poll } from '../../types'
import { Button } from '../styles/Buttons'
import { Heading3, Text } from '../styles/Text'
import { colors } from '../../utils/colors'
import { Card } from '../styles/Card'
import { FormField } from '../styles/Form'
import { updateStateType } from '../../pages/polls/create'
import { InfoSpan, IconPlus, IconTimes } from '../styles/Icons'
import { Group } from '../styles/Layout'

interface PollFormProps {
  state: Poll
  updateState: updateStateType
}

const MAX_NUM_OPTIONS = 6

const PollForm = ({ state, updateState }: PollFormProps) => {
  const [numOptions, setNumOptions] = useState(2)

  const updatePollOptions = (newOption: Object) => {
    updateState({
      ...state,
      pollOptions: { ...state.pollOptions, ...newOption },
    })
  }

  const addPollOption = () => {
    if (Object.keys(state.pollOptions).length < MAX_NUM_OPTIONS) {
      updatePollOptions({
        [numOptions]: '',
      })
      setNumOptions(numOptions + 1)
    }
  }

  const removePollOption = (pollIndex: number) => {
    const oldOptions = state.pollOptions
    delete oldOptions[pollIndex]
    updatePollOptions(oldOptions)
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
        {Object.entries(state.pollOptions).map(([key, value]) => (
          <Group horizontal style={{ position: 'relative' }} key={key}>
            <FormField
              name={key}
              value={value}
              placeholder="e.g. poll option"
              updateState={updatePollOptions}
            />
            {Number(key) >= 2 && (
              <div onClick={() => removePollOption(Number(key))} role="button">
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

      <Heading3>Dates</Heading3>
      {/* <Card></Card> */}

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
