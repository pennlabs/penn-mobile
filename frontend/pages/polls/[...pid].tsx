import React, { useState, useCallback } from 'react'
import { GetServerSidePropsContext } from 'next'
import { useRouter } from 'next/router'

import { AuthUserContext, withAuth } from '../../context/auth'
import { doApiRequest } from '../../utils/fetch'
import { PageType, PollType, Status, User } from '../../types'
import Nav from '../../components/header/Nav'
import { Col, Group, Row } from '../../components/styles/Layout'
import { Button, ToggleButton } from '../../components/styles/Buttons'
import { Subtitle } from '../../components/styles/Text'
import { colors } from '../../utils/colors'
import StatusBar from '../../components/form/StatusBar'
import PollForm from '../../components/form/poll/PollForm'
import Preview from '../../components/form/Preview'
import { convertCamelCase, convertSnakeCase } from '../../utils/utils'

interface iPollPageProps {
  user: User
  createMode: boolean // true if creating a poll, false if editing an existing poll
  poll?: PollType
}

const PollPage = ({ user, createMode, poll }: iPollPageProps) => {
  const [state, setState] = useState<PollType>(
    poll || {
      question: '',
      source: '',
      startDate: null,
      expireDate: null,
      options: [
        { id: 0, choice: '' },
        { id: 1, choice: '' },
      ],
      userComments: '',
      status: Status.DRAFT,
      targetPopulations: [],
    }
  )

  const router = useRouter()

  const updateState = useCallback((newState) => {
    setState((currentState) => ({ ...currentState, ...newState }))
  }, [])

  const onSubmit = () => {
    doApiRequest('/api/portal/polls/', {
      method: 'POST',
      body: convertCamelCase(state),
    })
      .then((res) => res.json())
      .then((res) => {
        Object.values(state.options).map((option) =>
          doApiRequest('/api/portal/options/', {
            method: 'POST',
            body: {
              poll: res.id,
              choice: option,
            },
          })
        )

        router.push('/') // redirect to dashboard after submitting
      })
  }

  const onDelete = () => {
    doApiRequest(`/api/portal/polls/${state.id}`, {
      method: 'DELETE',
    })
    router.push('/')
  }

  const onSave = () => {
    doApiRequest(`/api/portal/polls/${state.id}/`, {
      method: 'PATCH',
      body: convertCamelCase(state),
    })
      .then((res) => res.json())
      .then((res) => {
        state.options.map((option) =>
          doApiRequest(`/api/portal/options/${state.id}/`, {
            method: 'PATCH',
            body: {
              poll: res.id,
              choice: option.choice,
            },
          })
        )
      })
  }

  return (
    <AuthUserContext.Provider value={{ user }}>
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
            <Group horizontal alignItems="center">
              {!createMode && (
                <>
                  <Button color={colors.RED} onClick={onDelete}>
                    Delete
                  </Button>
                  <Button color={colors.GRAY} onClick={onSave}>
                    Save
                  </Button>
                </>
              )}
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
    </AuthUserContext.Provider>
  )
}

export const getServerSidePropsInner = async (
  context: GetServerSidePropsContext
): Promise<{ props: { poll?: PollType; createMode: boolean } }> => {
  const pid = context.params?.pid

  if (pid && +pid) {
    const res = await doApiRequest(`/api/portal/polls/${pid}/edit_view`, {
      method: 'GET',
      headers: context.req ? { cookie: context.req.headers.cookie } : undefined,
    })
    const poll = await res.json()
    if (res.ok && poll.id) {
      // const pollOptionsObj: PollType['options'] = {}
      // poll.options.forEach((option: any, index: number) => {
      //   pollOptionsObj[index] = option.choice
      // })
      // poll.options = pollOptionsObj
      poll.status = poll.approved ? Status.APPROVED : Status.PENDING

      return {
        props: { poll: convertSnakeCase(poll), createMode: false },
      }
    }
  }

  // for any poll where pid does not exist, render create poll form with
  // empty initial state
  return {
    props: {
      createMode: true,
    },
  }
}

export const getServerSideProps = withAuth(getServerSidePropsInner)

export default PollPage
