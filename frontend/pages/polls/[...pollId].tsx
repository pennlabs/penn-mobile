import React, { useState, useCallback } from 'react'
import { GetServerSidePropsContext } from 'next'
import { useRouter } from 'next/router'

import { AuthUserContext, withAuth } from '@/utils/auth'
import { doApiRequest } from '@/utils/fetch'
import { DASHBOARD_ROUTE } from '@/utils/routes'
import { initialPoll, PageType, PollType, User } from '@/utils/types'
import { Col, Container, Group, Row } from '@/components/styles/Layout'
import { Button } from '@/components/styles/Buttons'
import { Subtitle } from '@/components/styles/Text'
import { colors } from '@/components/styles/colors'
import StatusBar from '@/components/form/StatusBar'
import PollForm from '@/components/form/poll/PollForm'
import { PollsPhonePreview } from '@/components/form/Preview'
import { CreateContentToggle } from '@/components/form/SharedCards'
import { FilterType } from '@/components/form/Filters'

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

  const router = useRouter()

  const updateState = useCallback((newState) => {
    setState((currentState) => ({ ...currentState, ...newState }))
  }, [])

  const onSubmit = () => {
    doApiRequest('/api/portal/polls/', {
      method: 'POST',
      body: state,
    })
      .then((res) => res.json())
      .then((res) => {
        state.options.map((option) =>
          doApiRequest('/api/portal/options/', {
            method: 'POST',
            body: {
              poll: res.id,
              choice: option.choice,
            },
          })
        )

        router.push(DASHBOARD_ROUTE) // redirect to dashboard after submitting
      })
  }

  const onDelete = () => {
    doApiRequest(`/api/portal/polls/${state.id}`, {
      method: 'DELETE',
    })
    router.push(DASHBOARD_ROUTE)
  }

  const onSave = () => {
    // update poll fields
    doApiRequest(`/api/portal/polls/${state.id}/`, {
      method: 'PATCH',
      body: state,
    })

    const currOptionIds = state.options.map((option) => {
      // post new poll option
      if (!prevOptionIds?.includes(option.id)) {
        doApiRequest('/api/portal/options/', {
          method: 'POST',
          body: {
            poll: state.id,
            choice: option.choice,
          },
        })
      } else {
        // update existing poll option
        doApiRequest(`/api/portal/options/${option.id}/`, {
          method: 'PATCH',
          body: {
            poll: state.id,
            choice: option.choice,
          },
        })
      }
      return option.id
    })

    prevOptionIds?.forEach((optionId) => {
      if (!currOptionIds.includes(optionId)) {
        // delete existing poll option
        doApiRequest(`/api/portal/options/${optionId}/`, {
          method: 'DELETE',
        })
      }
    })
  }

  return (
    <AuthUserContext.Provider value={{ user }}>
      <Container>
        <Row>
          <Col sm={12} md={12} lg={7} padding="0.5rem">
            <CreateContentToggle activeOption={PageType.POLL} />
            <Group
              horizontal
              justifyContent="space-between"
              margin="0 0 2rem 0"
            >
              <Subtitle>Poll Details</Subtitle>
              <Group horizontal alignItems="center">
                {createMode ? (
                  <Button color={colors.GREEN} onClick={onSubmit}>
                    Submit
                  </Button>
                ) : (
                  <>
                    <Button color={colors.RED} onClick={onDelete}>
                      Delete
                    </Button>
                    <Button color={colors.GRAY} onClick={onSave}>
                      Save
                    </Button>
                  </>
                )}
              </Group>
            </Group>
            <StatusBar status={state.status} />
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
