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

    const res = await doApiRequest('/api/users/me/', headers)
    if (res.ok || ctx.req.url === '/') {
      const user = await res.json()
      const wrapped = await getServerSidePropsFunc(ctx)
      const casted = convertGetServerSidePropsResult(wrapped)

      if (casted.tag === 'props') {
        return {
          // pass null user if in landing page route `/` and user is not logged in
          props: { ...casted.props, user: res.ok ? user : null },
        }
      } else if (casted.tag === 'notFound') {
        return { notFound: casted.notFound }
      } else {
        return { redirect: casted.redirect }
      }
    } else {
      return {
        redirect: {
          destination: '/',
          permanent: false,
        },
      }
    }
  }
}
