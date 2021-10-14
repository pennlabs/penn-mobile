import React, { useState } from 'react'

import Nav from '../../components/header/Nav'
import { Row, Col } from '../../components/styles/Layout'
import { withAuth } from '../../context/auth'
import PollForm from '../../components/form/PollForm'
import { ToggleButton } from '../../components/styles/Buttons'
import { PageType } from '../../types'

// TODO: maybe move this to /polls instead?
const CreatePoll = () => {
  const [state, setState] = useState({
    question: '',
  })

  return (
    <>
      <Nav />
      <Row>
        <Col sm={12} md={12} lg={6} padding="4rem">
          <ToggleButton currPage={PageType.POLL} />
          <PollForm />
        </Col>
        <Col sm={12} md={12} lg={6}>
          preview
        </Col>
      </Row>
    </>
  )
}

export default withAuth(CreatePoll)
