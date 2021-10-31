import React, { useState, useCallback } from 'react'
import { NextPageContext } from 'next'

import { withAuth } from '../../context/auth'
import { doApiRequest } from '../../utils/fetch'
import { PageType, PollType, Status } from '../../types'
import Nav from '../../components/header/Nav'
import { Col, Group, Row } from '../../components/styles/Layout'
import { Button, ToggleButton } from '../../components/styles/Buttons'
import { Subtitle } from '../../components/styles/Text'
import { colors } from '../../utils/colors'
import StatusBar from '../../components/form/StatusBar'
import PollForm from '../../components/form/poll/PollForm'
import Preview from '../../components/form/Preview'

interface iPollPageProps {
  // true if creating a new poll, false if editing an existing poll
  createMode: boolean
  poll: PollType
}

const PollPage = ({ poll, createMode }: iPollPageProps) => {
  const [state, setState] = useState<PollType>(poll)

  const updateState = useCallback((newState) => {
    setState((currentState) => ({ ...currentState, ...newState }))
  }, [])

  const onSubmit = () => {
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
        const options = Object.values(state.pollOptions)
        options.map((option) =>
          doApiRequest('/api/portal/options/', {
            method: 'POST',
            body: {
              poll: res.id,
              choice: option,
            },
          })
        )
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
              {!createMode && <Button color={colors.RED}>Delete</Button>}
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

// TODO: types
export const getServerSideProps = async (context: any) => {
  const { req, params } = context
  const { pid } = params

  const res = await doApiRequest(`/api/portal/polls/${pid}`, {
    method: 'GET',
    // TODO: auth?
    headers: req ? { cookie: req.headers.cookie } : undefined,
  })
  const poll = await res.json()

  // poll with pid exists, render poll to edit or delete
  if (poll.id) {
    // fetch poll options for poll
    const pollOptions = await doApiRequest(`/api/portal/options/${pid}`, {
      method: 'GET',
      headers: req ? { cookie: req.headers.cookie } : undefined,
    })
    poll.pollOptions = await pollOptions.json()

    return {
      props: { poll, createMode: false },
    }
  } else {
    // for any poll where pid does not exist, render poll create form
    const initPollState = {
      question: '',
      source: '',
      startDate: null,
      endDate: null,
      pollOptions: { 0: '', 1: '' },
      userComments: '',
      status: Status.DRAFT,
    }

    return {
      props: {
        poll: initPollState,
        createMode: true,
      },
    }
  }
}

export default PollPage
