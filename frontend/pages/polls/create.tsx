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
import { doApiRequest } from '../../utils/fetch'
import Preview from '../../components/form/Preview'

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
  const [id, setId] = useState('')
  console.log(state)

  // helper function to set state
  const updateState = useCallback((newState) => {
    setState((currentState) => ({ ...currentState, ...newState }))
  }, [])

  const onSubmit = () => {
    // TODO: refactor this shit
    doApiRequest('/api/portal/polls/', {
      method: 'POST',
      body: {
        question: state.question,
        source: state.source,
        start_date: state.startDate,
        expire_date: state.endDate,
        user_comments: state.userComments,
        // TODO: add target populations and multiselect
        target_populations: [],
        // multiselect: state.multiselect,
      },
    })
      .then((res) => res.json())
      .then((res) => {
        setId(res.id)
        doApiRequest('/api/portal/options', {
          method: 'POST',
          body: {
            poll_id: res.id,
            options: state.pollOptions,
          },
        })
      })
  }

  return (
    <>
      <Nav />
      <Row style={{ padding: '2.5rem 0 0 4rem' }}>
        <ToggleButton currPage={PageType.POLL} />
      </Row>
      <Row>
        <Col sm={12} md={12} lg={7} padding="0.5rem 4rem">
          <Group
            horizontal
            justifyContent="space-between"
            margin="0 0 1.5rem 0"
          >
            <Subtitle>Poll Details</Subtitle>
            {/* TODO: add functionality to these buttons... */}
            <Group horizontal alignItems="center">
              <Button color={colors.RED}>Delete</Button>
              <Button color={colors.GRAY}>Save</Button>
              <Button color={colors.GREEN} onClick={onSubmit}>
                Submit
              </Button>
            </Group>
          </Group>
          <StatusBar status={state.status} />
          <PollForm state={state} updateState={updateState} />
        </Col>
        <Col sm={12} md={12} lg={5}>
          <Preview state={state} />
        </Col>
      </Row>
    </>
  )
}

export default withAuth(CreatePoll)
