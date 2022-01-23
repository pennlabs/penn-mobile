import React, { useState, useCallback } from 'react'
import { GetServerSidePropsContext } from 'next'
import { useRouter } from 'next/router'

import { AuthUserContext, withAuth } from '@/utils/auth'
import { doApiRequest } from '@/utils/fetch'
import { initialPost, PageType, PostType, User } from '@/utils/types'
import { Col, Container, Group, Row } from '@/components/styles/Layout'
import { Button } from '@/components/styles/Buttons'
import { Subtitle } from '@/components/styles/Text'
import { colors } from '@/components/styles/colors'
import StatusBar from '@/components/form/StatusBar'
import PostForm from '@/components/form/post/PostForm'
import { PostPhonePreview } from '@/components/form/Preview'
import { DASHBOARD_ROUTE } from '@/utils/routes'
import { CreateContentToggle } from '@/components/form/SharedCards'
import { FilterType } from '@/components/form/Filters'
import { useLocalStorage } from '@/hooks/useLocalStorage'
import { ErrorMessage } from '@/components/styles/StatusMessage'

interface iPostPageProps {
  createMode: boolean // true if creating a post, false if editing an existing post
  post?: PostType
  filters: FilterType[]
}

const PostPage = ({
  user,
  createMode,
  post,
  filters,
}: iPostPageProps & { user: User }) => {
  const [state, setState] = useState<PostType>(post || initialPost)
  // success message to display on dashboard if successfully created a post
  const [, setSuccess] = useLocalStorage<string | null>('success', null)
  const [error, setError] = useState<string | null>(null)

  const router = useRouter()

  const updateState = useCallback((newState) => {
    setState((currentState) => ({ ...currentState, ...newState }))
  }, [])

  const onSubmit = async () => {
    const res = await doApiRequest('/api/portal/posts/', {
      method: 'POST',
      body: state,
    })
    if (res.ok) {
      // redirect to dashboard after submitting with success message
      setSuccess('Post successfully submitted!')
      router.push(DASHBOARD_ROUTE)
    } else {
      const errorMsg = await res.json()
      setError(`Error submitting post: ${JSON.stringify(errorMsg)}`)
    }
  }

  const onDelete = async () => {
    const res = await doApiRequest(`/api/portal/posts/${state.id}`, {
      method: 'DELETE',
    })
    if (res.ok) {
      setSuccess('Post successfully deleted!')
      router.push(DASHBOARD_ROUTE)
    } else {
      const errorMsg = await res.json()
      setError(`Error deleting post: ${JSON.stringify(errorMsg)}`)
    }
  }

  const onSave = async () => {
    const res = await doApiRequest(`/api/portal/posts/${state.id}/`, {
      method: 'PATCH',
      body: state,
    })
    if (res.ok) {
      setSuccess('Post successfully updated!')
      router.push(DASHBOARD_ROUTE)
    } else {
      const errorMsg = await res.json()
      setError(`Error updating post: ${JSON.stringify(errorMsg)}`)
    }
  }

  return (
    <AuthUserContext.Provider value={{ user }}>
      <Container>
        <Row>
          <Col sm={12} md={12} lg={7} padding="0.5rem">
            {error && <ErrorMessage msg={error} />}
            <CreateContentToggle activeOption={PageType.POST} />
            <Group
              horizontal
              justifyContent="space-between"
              margin="0 0 2rem 0"
            >
              <Subtitle>Post Details</Subtitle>
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
            <PostForm
              state={state}
              updateState={updateState}
              filters={filters}
            />
          </Col>
          <Col sm={12} md={12} lg={5}>
            <PostPhonePreview state={state} />
          </Col>
        </Row>
      </Container>
    </AuthUserContext.Provider>
  )
}

export const getServerSidePropsInner = async (
  context: GetServerSidePropsContext
): Promise<{
  props: iPostPageProps
}> => {
  const pid = context.params?.postId
  const data = {
    headers: context.req ? { cookie: context.req.headers.cookie } : undefined,
  }

  const filtersRes = await doApiRequest('/api/portal/populations/', data)

  if (pid && +pid) {
    const res = await doApiRequest(`/api/portal/posts/${pid}`, data)
    const post = await res.json()
    if (res.ok && post.id) {
      return {
        props: {
          post,
          createMode: false,
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

export default PostPage
