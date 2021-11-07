import React from 'react'
import { colors } from '../../utils/colors'

import { Row, Col, Group } from '../styles/Layout'
import { Title, Text } from '../styles/Text'
import Wireframes from './Wireframes'

const LandingPage = () => (
  <>
    <Row style={{ backgroundColor: colors.WHITE }}>
      <Col sm={12} md={12} lg={5} fullHeight padding="0 0 0 3rem">
        <Group style={{ marginTop: '6rem' }}>
          <Title>
            Welcome <br /> to Portal.
          </Title>
          <Text>ah, there will be some text here...</Text>
        </Group>
      </Col>
      <Col sm={12} md={12} lg={7} style={{ overflow: 'hidden' }}>
        <Wireframes />
      </Col>
    </Row>
  </>
)

export default LandingPage
