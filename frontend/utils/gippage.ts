import { NextPageContext, NextPage } from 'next'

export type GIPPage<P> = NextPage<P> & {
  getInitialProps: (ctx: NextPageContext) => P | Promise<P>
}
