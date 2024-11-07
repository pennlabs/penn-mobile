import React from 'react'
import s from 'styled-components'

import { IconCircle } from '@/components/styles/Icons'
import { Group, Row } from '@/components/styles/Layout'
import { colors } from '@/components/styles/colors'
import { Text } from '@/components/styles/Text'
import { Status } from '@/utils/types'

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
  const orderedStatus = Object.values(Status)

  // colors line & circle blue if active, gray if not. dependent on Status enum order.
  const StatusGroup = ({ compareStatus }: { compareStatus: Status }) => {
    const statusColor =
      orderedStatus.indexOf(status) >= orderedStatus.indexOf(compareStatus)
        ? colors.MEDIUM_BLUE
        : colors.LIGHT_GRAY
    return (
      <>
        <StatusBarLine color={statusColor} width={25} />
        <IconCircle color={statusColor} />
      </>
    )
  }

  return (
    <>
      <Group horizontal className="flex items-center mx-2">
        <IconCircle color={colors.MEDIUM_BLUE} />
        <StatusGroup compareStatus={Status.REVISION} />
        <StatusGroup compareStatus={Status.APPROVED} />
        <StatusGroup compareStatus={Status.LIVE} />
        <StatusGroup compareStatus={Status.EXPIRED} />
      </Group>
      <Row style={{ textAlign: 'center' }} justifyContent="space-between">
        <Text heading>Draft</Text>
        <Text heading>
          Under <br /> Review
        </Text>
        <Text heading>Approved</Text>
        <Text heading>Live</Text>
        <Text heading>Expired</Text>
      </Row>
    </>
  )
}

export default StatusBar
