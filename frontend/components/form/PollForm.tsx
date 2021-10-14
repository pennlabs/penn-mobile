import React from 'react'

import { Status } from '../../types'
import { Button } from '../styles/Buttons'
import { Subtitle } from '../styles/Text'
import { colors } from '../../utils/colors'
import { Group } from '../styles/Layout'
import StatusBar from './StatusBar'

const PollForm = () => {
  return (
    <>
      <Group horizontal justifyContent="space-between" margin="1.5rem 0">
        <Subtitle>Poll Details</Subtitle>
        {/* TODO: add functionality to these buttons... */}
        <Group horizontal alignItems="center">
          <Button color={colors.RED}>Delete</Button>
          <Button color={colors.GRAY}>Save</Button>
          <Button color={colors.GREEN}>Submit</Button>
        </Group>
      </Group>
      <StatusBar status={Status.APPROVED} />
    </>
  )
}

export default PollForm
