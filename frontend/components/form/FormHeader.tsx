import React, { useState } from 'react'
import { useRouter } from 'next/router'

import { isPost, PageType, PollType, PostType } from '@/utils/types'
import StatusBar from '@/components/form/StatusBar'
import { CreateContentToggle } from '@/components/form/SharedCards'
import { Group } from '@/components/styles/Layout'
import { Subtitle } from '@/components/styles/Text'
import { Button } from '@/components/styles/Buttons'
import { colors } from '@/components/styles/colors'
import { doApiRequest } from '@/utils/fetch'
import { useLocalStorage } from '@/hooks/useLocalStorage'
import { DASHBOARD_ROUTE } from '@/utils/routes'
import { ErrorMessage } from '@/components/styles/StatusMessage'

interface iFormHeaderProps {
  createMode: boolean
  state: PollType | PostType
  prevOptionIds?: number[]
}

const FormHeader = ({ createMode, state, prevOptionIds }: iFormHeaderProps) => {
  const router = useRouter()
  const activeOption = isPost(state) ? PageType.POST : PageType.POLL
  const route = `${activeOption.toLowerCase()}s` // e.g. 'polls'

  // success message to display on dashboard if successfully created/deleted/updated
  const [, setSuccess] = useLocalStorage<string | null>('success', null)
  const [error, setError] = useState<string | null>(null)

  const onSubmit = async () => {
    if (
      !isPost(state) &&
      (state.options[0]?.choice === '' || state.options[1]?.choice === '')
    ) {
      setError('Polls must have at least 2 options')
      return
    }

    const form_data = new FormData()
    if (isPost(state)) {
      Object.entries(state).forEach(([key, value]) => {
        if (key !== 'image_url') {
          if (key === 'start_date' || key === 'expire_date') {
            const val = value.toISOString()
            form_data.append(key, val)
          } else if (key !== 'target_populations') {
            form_data.append(key, value)
          }
        } else {
          form_data.append(key, value)
        }
      })
    }

    // const data = {
    //   title: 'adf',
    //   subtitle: 'asdf',
    //   club_code: 'pennlabs',
    //   post_url: 'https://google.com/',
    //   start_date: new Date('September 17, 2023 03:24:00'),
    //   expire_date: new Date('October 17, 2023 03:24:00'),
    //   club_comment: 'af',
    //   status: 'DRAFT',
    //   target_populations: '',
    // }

    const res = await doApiRequest(`/api/portal/${route}/`, {
      method: 'POST',
      body: isPost(state) ? form_data : state,
      // headers: {
      //   'Content-Type': isPost(state)
      //     ? 'multipart/form-data'
      //     : 'application/json',
      // },
    })

    if (res.ok) {
      // post each poll option if creating a poll
      if (!isPost(state)) {
        const pollRes = await res.json()
        state.options.map((option) =>
          doApiRequest('/api/portal/options/', {
            method: 'POST',
            body: {
              poll: pollRes.id,
              choice: option.choice,
            },
          })
        )
      }

      // redirect to dashboard after submitting with success message
      setSuccess(`${activeOption} successfully submitted!`)
      router.push(DASHBOARD_ROUTE)
      return
    }

    const errorMsg = await res.json()
    setError(`Error submitting ${route}: ${JSON.stringify(errorMsg)}`)
  }

  const onDelete = async () => {
    const res = await doApiRequest(`/api/portal/${route}/${state.id}`, {
      method: 'DELETE',
    })
    if (res.ok) {
      setSuccess(`${activeOption} successfully deleted!`)
      router.push(DASHBOARD_ROUTE)
      return
    }

    const errorMsg = await res.json()
    setError(`Error deleting ${route}: ${JSON.stringify(errorMsg)}`)
  }

  const onSave = async () => {
    const res = await doApiRequest(`/api/portal/${route}/${state.id}/`, {
      method: 'PATCH',
      body: state,
    })

    if (res.ok) {
      if (!isPost(state)) {
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

      setSuccess(`${activeOption} successfully updated!`)
      router.push(DASHBOARD_ROUTE)
      return
    }

    const errorMsg = await res.json()
    setError(`Error updating ${route}: ${JSON.stringify(errorMsg)}`)
  }

  return (
    <>
      {error && <ErrorMessage msg={error} />}
      <CreateContentToggle activeOption={activeOption} />
      <Group horizontal justifyContent="space-between" margin="0 0 2rem 0">
        <Subtitle>{activeOption} Details</Subtitle>
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
    </>
  )
}

export default FormHeader
