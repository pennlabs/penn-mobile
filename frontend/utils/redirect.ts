import Router from 'next/router'
import { NextPageContext } from 'next'

export default function nextRedirect(
  { req, res }: NextPageContext,
  condition: (url: string) => boolean,
  redirectUrl: string
) {
  // if redirect is called server side
  if (req && res) {
    // if request doesn't have an associated URL or the condition
    // on the url applies, we redirect
    if (!req.url || condition(req.url)) {
      res.writeHead(302, { Location: redirectUrl })
      res.end()
    }
  } else if (condition(window.location.pathname)) {
    Router.replace(redirectUrl)
  }
}
