import React from 'react'
import { Row, Col, Group } from '@/components/styles/Layout'
import { Heading3, Title } from '@/components/styles/Text'
import {
  DesktopWireframes,
  MobileWireframes,
} from '@/components/landing-page/Wireframes'
import LandingPageNav from '@/components/landing-page/LandingPageNav'

const LandingPage = () => (
  <>
    <LandingPageNav />
    <Row>
      <Col sm={12} md={8} lg={5}>
        <Group margin="15vh 0 0 5vw">
          <Title>
            Welcome <br /> to Portal.
          </Title>
          <Heading3 bold={false}>
            Poll/advertise to 8,000 undergraduates in real time on the
            University of Pennsylvania&apos;s official student app.
          </Heading3>
        </Group>
      </Col>
      <Col sm={12} md={12} lg={7}>
        <DesktopWireframes />
        <MobileWireframes />
      </Col>
    </Row>
  </>
)

export default LandingPage
