import Router from 'next/router'
import { NextPageContext } from 'next'

export default function nextRedirect(
  { req, res }: NextPageContext,
  redirectUrl: string,
  condition?: (url: string) => boolean
) {
  // if redirect is called server side
  if (req && res) {
    // if request doesn't have an associated URL or the condition
    // on the url applies, we redirect
    if (!req.url || (condition && condition(req.url))) {
      res.writeHead(302, { Location: redirectUrl })
      res.end()
    }
  } else if (condition && condition(window.location.pathname)) {
    Router.replace('redirectUrl')
  }
}
