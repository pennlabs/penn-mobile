import React from 'react'
import Head from 'next/head'
import Nav from '../landing-page/Nav'

const Header = () => {
  return (
    <>
      <Head>
        <title>Penn Mobile Portal</title>
        <meta
          name="description"
          content="A web-based portal for organizations to reach Penn Mobile users."
        />
        <link rel="icon" href="/favicon.ico" />
      </Head>
    </>
  )
}

export default Header
