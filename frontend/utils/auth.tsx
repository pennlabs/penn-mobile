import { createContext } from 'react'
import {
  GetServerSidePropsContext,
  GetServerSidePropsResult,
  Redirect,
} from 'next'
import { doApiRequest } from '@/utils/fetch'
import { User } from '@/utils/types'

export interface AuthProps {
  user: User
}

export const AuthUserContext: React.Context<{ user?: User }> = createContext({})

type GetServerSidePropsResultDiscUnion<T> =
  | { tag: 'props'; props: T }
  | { tag: 'redirect'; redirect: Redirect }
  | { tag: 'notFound'; notFound: true }

function convertGetServerSidePropsResult<T>(
  r: GetServerSidePropsResult<T>
): GetServerSidePropsResultDiscUnion<T> {
  if (Object.prototype.hasOwnProperty.call(r, 'props')) {
    const casted = r as { props: T }
    return { tag: 'props', props: casted.props }
  } else if (Object.prototype.hasOwnProperty.call(r, 'redirect')) {
    const casted = r as { redirect: Redirect }
    return { tag: 'redirect', redirect: casted.redirect }
  } else if (Object.prototype.hasOwnProperty.call(r, 'notFound')) {
    return { tag: 'notFound', notFound: true }
  }

  throw new Error('NextJS typing information incorrect')
}

type GetServerSidePropsFunc<T> = (
  ctx: GetServerSidePropsContext
) => Promise<GetServerSidePropsResult<T>>

export function withAuth<T>(getServerSidePropsFunc: GetServerSidePropsFunc<T>) {
  return async (
    ctx: GetServerSidePropsContext
  ): Promise<GetServerSidePropsResult<T & AuthProps>> => {
    const headers = {
      credentials: 'include',
      headers: { cookie: ctx.req.headers.cookie },
    }

    const userReq = await doApiRequest('/api/portal/user/', headers)

    if (userReq.ok) {
      const userRes = await userReq.json()
      const user: User = {
        first_name: userRes.user.first_name,
        last_name: userRes.user.last_name,
        email: userRes.user.email,
      }
      const wrapped = await getServerSidePropsFunc(ctx)
      const casted = convertGetServerSidePropsResult(wrapped)

      if (casted.tag === 'props') {
        return {
          props: { ...casted.props, user },
        }
      } else if (casted.tag === 'notFound') {
        return { notFound: casted.notFound }
      } else {
        return { redirect: casted.redirect }
      }
    } else {
      // redirect to landing page if no user is logged in
      return {
        redirect: {
          destination: '/',
          permanent: false,
        },
      }
    }
  }
}
