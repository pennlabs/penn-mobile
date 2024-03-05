import React, { useState, useCallback } from 'react'
import { GetServerSidePropsContext } from 'next'

import { AuthUserContext, withAuth } from '@/utils/auth'
import { doApiRequest } from '@/utils/fetch'
import { initialPoll, PollType, User } from '@/utils/types'
import { Col, Container, Row } from '@/components/styles/Layout'
import PollForm from '@/components/form/poll/PollForm'
import { PollsPhonePreview } from '@/components/form/Preview'
import { FilterType } from '@/components/form/Filters'
import FormHeader from '@/components/form/FormHeader'

interface iPollPageProps {
  createMode: boolean // true if creating a poll, false if editing an existing poll
  poll?: PollType
  prevOptionIds?: number[] // poll option ids
  filters: FilterType[]
}

const PollPage = ({
  user,
  createMode,
  poll,
  prevOptionIds,
  filters,
}: iPollPageProps & { user: User }) => {
  const [state, setState] = useState<PollType>(poll || initialPoll)
  const updateState = useCallback((newState) => {
    setState((currentState) => ({ ...currentState, ...newState }))
  }, [])

  return (
    <AuthUserContext.Provider value={{ user }}>
      <Container>
        <Row>
          <Col sm={12} md={12} lg={7} padding="0.5rem">
            <FormHeader
              createMode={createMode}
              state={state}
              prevOptionIds={prevOptionIds}
            />
            <PollForm
              state={state}
              updateState={updateState}
              filters={filters}
            />
          </Col>
          <Col sm={12} md={12} lg={5}>
            <PollsPhonePreview state={state} />
          </Col>
        </Row>
      </Container>
    </AuthUserContext.Provider>
  )
}

export const getServerSidePropsInner = async (
  context: GetServerSidePropsContext
): Promise<{
  props: iPollPageProps
}> => {
  const pid = context.params?.pollId
  const data = {
    headers: context.req ? { cookie: context.req.headers.cookie } : undefined,
  }

  const filtersRes = await doApiRequest('/api/portal/populations/', data)

  if (pid && +pid) {
    const res = await doApiRequest(`/api/portal/polls/${pid}/option_view`, data)
    const poll = await res.json()
    if (res.ok && poll.id) {
      const prevOptionIds = poll.options.map((opt: any) => opt.id)
      poll.target_populations = poll.target_populations.map(
        (pop: any) => pop.id
      )

      return {
        props: {
          poll,
          createMode: false,
          prevOptionIds,
          filters: await filtersRes.json(),
        },
      }
    }
  }

  return {
    props: {
      createMode: true,
      filters: await filtersRes.json(),
    },
  }
}

export const getServerSideProps = withAuth(getServerSidePropsInner)

export default PollPage
