import React from 'react'
import s from 'styled-components'
import { IconCircle } from '../styles/Icons'

import { Group, Row } from '../styles/Layout'
import { colors } from '../../utils/colors'
import { Text } from '../styles/Text'
import { Status } from '../../types'

interface iStatusBarLineProps {
  color: string
  width: number
}

const StatusBarLine = s.hr<iStatusBarLineProps>`
  background-color: ${(props) => props.color};
  width: ${(props) => `${props.width}%`};
  height: 6px;
  display: inline-block;
  box-sizing: border-box;
`

interface iStatusBarProps {
  status: Status
}

const StatusBar = ({ status }: iStatusBarProps) => {
  // colors line & circle blue if active, gray if not. dependent on Status enum order.
  const StatusGroup = ({ compareStatus }: { compareStatus: Status }) => (
    <>
      <StatusBarLine
        color={status >= compareStatus ? colors.MEDIUM_BLUE : colors.LIGHT_GRAY}
        width={25}
      />
      <IconCircle
        color={status >= compareStatus ? colors.MEDIUM_BLUE : colors.LIGHT_GRAY}
      />
    </>
  )

  return (
    <>
      <Group horizontal style={{ margin: '0 0.5rem' }}>
        <IconCircle color={colors.MEDIUM_BLUE} />
        <StatusGroup compareStatus={Status.PENDING} />
        <StatusGroup compareStatus={Status.APPROVED} />
        <StatusGroup compareStatus={Status.LIVE} />
        <StatusGroup compareStatus={Status.EXPIRED} />
      </Group>
      <Row style={{ textAlign: 'center' }} justifyContent="space-between">
        <Text>Draft</Text>
        <Text>
          Under <br /> Review
        </Text>
        <Text>Approved</Text>
        <Text>Live</Text>
        <Text>Expired</Text>
      </Row>
    </>
  )
}

export default StatusBar
