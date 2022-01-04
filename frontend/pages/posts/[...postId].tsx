import React, { useState, useCallback } from 'react'
import { GetServerSidePropsContext } from 'next'
import { useRouter } from 'next/router'

import { AuthUserContext, withAuth } from '@/utils/auth'
import { doApiRequest } from '@/utils/fetch'
import { PageType, PostType, Status, User } from '@/utils/types'
import { Col, Container, Group, Row } from '@/components/styles/Layout'
import { Button, ToggleButton } from '@/components/styles/Buttons'
import { Subtitle } from '@/components/styles/Text'
import { colors } from '@/components/styles/colors'
import StatusBar from '@/components/form/StatusBar'
import PostForm from '@/components/form/post/PostForm'
import { PostPhonePreview } from '@/components/form/Preview'
import { convertCamelCase, convertSnakeCase } from '@/utils/utils'
import { DASHBOARD_ROUTE } from '@/utils/routes'

interface iPostPageProps {
  user: User
  createMode: boolean // true if creating a post, false if editing an existing post
  post?: PostType
}

const PostPage = ({ user, createMode, post }: iPostPageProps) => {
  const [state, setState] = useState<PostType>(
    post || {
      title: '',
      subtitle: '',
      source: '',
      postUrl: '',
      imageUrl:
        'https://www.akc.org/wp-content/uploads/2017/11/Pembroke-Welsh-Corgi-standing-outdoors-in-the-fall.jpg',
      startDate: null,
      expireDate: null,
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
    doApiRequest('/api/portal/posts/', {
      method: 'POST',
      body: convertCamelCase(state),
    }).then(() => router.push(DASHBOARD_ROUTE)) // redirect to dashboard after submitting
  }

  const onDelete = () => {
    doApiRequest(`/api/portal/posts/${state.id}`, {
      method: 'DELETE',
    })
    router.push(DASHBOARD_ROUTE)
  }

  const onSave = () => {
    doApiRequest(`/api/portal/posts/${state.id}/`, {
      method: 'PATCH',
      body: convertCamelCase(state),
    })
  }

  return (
    <AuthUserContext.Provider value={{ user }}>
      <Container>
        <Row style={{ padding: '2.5rem 0 0 4rem' }}>
          <ToggleButton currPage={PageType.POST} />
        </Row>
        <Row>
          <Col sm={12} md={12} lg={7} padding="0.5rem 4rem">
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
            <PostForm state={state} updateState={updateState} />
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
  props: { post?: PostType; createMode: boolean }
}> => {
  const pid = context.params?.postId

  if (pid && +pid) {
    const res = await doApiRequest(`/api/portal/posts/${pid}`, {
      method: 'GET',
      headers: context.req ? { cookie: context.req.headers.cookie } : undefined,
    })
    const post = await res.json()
    if (res.ok && post.id) {
      post.status = post.approved ? Status.APPROVED : Status.PENDING

      return {
        props: {
          post: convertSnakeCase(post) as unknown as PostType,
          createMode: false,
        },
      }
    }
  }

  return {
    props: {
      createMode: true,
    },
  }
}

export const getServerSideProps = withAuth(getServerSidePropsInner)

export default PostPage
