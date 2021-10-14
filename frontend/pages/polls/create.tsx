import React, { useState, useCallback } from 'react'

import Nav from '../../components/header/Nav'
import { Row, Col, Group } from '../../components/styles/Layout'
import { withAuth } from '../../context/auth'
import PollForm from '../../components/form/PollForm'
import { Button, ToggleButton } from '../../components/styles/Buttons'
import { Poll, PageType, Status } from '../../types'
import { Subtitle } from '../../components/styles/Text'
import { colors } from '../../utils/colors'
import StatusBar from '../../components/form/StatusBar'

export type updateStateType = (newState: Object) => void

// TODO: maybe move this to /polls instead?
const CreatePoll = () => {
  const [state, setState] = useState<Poll>({
    question: '',
    source: '',
    startDate: null,
    endDate: null,
    pollOptions: { 0: '', 1: '' },
    userComments: '',
    status: Status.DRAFT,
  })
  console.log(state)

  // helper function to set state
  const updateState = useCallback((newState) => {
    setState((currentState) => ({ ...currentState, ...newState }))
  }, [])

  return (
    <>
      <Nav />
      <Row>
        <Col sm={12} md={12} lg={7} padding="4rem">
          <ToggleButton currPage={PageType.POLL} />
          <Group horizontal justifyContent="space-between" margin="1.5rem 0">
            <Subtitle>Poll Details</Subtitle>
            {/* TODO: add functionality to these buttons... */}
            <Group horizontal alignItems="center">
              <Button color={colors.RED}>Delete</Button>
              <Button color={colors.GRAY}>Save</Button>
              <Button color={colors.GREEN}>Submit</Button>
            </Group>
          </Group>
          <StatusBar status={state.status} />
          <PollForm state={state} updateState={updateState} />
        </Col>
        <Col sm={12} md={12} lg={5}>
          preview
        </Col>
      </Row>
    </>
  )
}

export default withAuth(CreatePoll)
