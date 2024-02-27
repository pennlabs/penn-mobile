import React, { useState, useCallback } from 'react'
import { GetServerSidePropsContext } from 'next'

import { AuthUserContext, withAuth } from '@/utils/auth'
import { doApiRequest } from '@/utils/fetch'
import { initialPost, PostType, User } from '@/utils/types'
import { Col, Container, Row } from '@/components/styles/Layout'
import PostForm from '@/components/form/post/PostForm'
import { PostPhonePreview } from '@/components/form/Preview'
import { FilterType } from '@/components/form/Filters'
import FormHeader from '@/components/form/FormHeader'

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
    post
      ? {
          ...post,
          start_date: new Date(post.start_date!), // deserialize date strings since they have to be sent as strings
          expire_date: new Date(post.expire_date!),
        }
      : initialPost
  )

  const updateState = useCallback((newState) => {
    setState((currentState) => ({ ...currentState, ...newState }))
  }, [])

  return (
    <AuthUserContext.Provider value={{ user }}>
      <Container>
        <Row>
          <Col sm={12} md={12} lg={7} padding="0.5rem">
            <FormHeader createMode={createMode} state={state} />
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
