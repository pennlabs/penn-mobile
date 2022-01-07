import React, { useState, useCallback } from 'react'
import { GetServerSidePropsContext } from 'next'
import { useRouter } from 'next/router'

import { AuthUserContext, withAuth } from '@/utils/auth'
import { doApiRequest } from '@/utils/fetch'
import { PageType, PostType, Status, User } from '@/utils/types'
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
  const [state, setState] = useState<PostType>(
    post || {
      title: '',
      subtitle: '',
      source: '', // TODO: replace with club_code
      post_url: '',
      image_url:
        'https://www.akc.org/wp-content/uploads/2017/11/Pembroke-Welsh-Corgi-standing-outdoors-in-the-fall.jpg',
      start_date: null,
      expire_date: null,
      club_comment: '',
      status: Status.DRAFT,
      target_populations: [],
    }
  )

  const router = useRouter()

  const updateState = useCallback((newState) => {
    setState((currentState) => ({ ...currentState, ...newState }))
  }, [])

  const onSubmit = () => {
    doApiRequest('/api/portal/posts/', {
      method: 'POST',
      body: state,
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
      body: state,
    })
  }

  return (
    <AuthUserContext.Provider value={{ user }}>
      <Container>
        <Row>
          <Col sm={12} md={12} lg={7} padding="0.5rem">
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
