import React from 'react'
import Link from 'next/link'
import { Group, Row } from '../styles/Layout'
import { Subtitle, Text } from '../styles/Text'
import { IconArrowRight } from '../styles/Icons'
import { colors } from '../../utils/colors'

const Dashboard = () => (
  <Row
    justifyContent="center"
    style={{
      alignItems: 'center',
      height: '80vh',
    }}
  >
    <Group horizontal margin="auto">
      <img src="/desk-graphic.svg" alt="desk svg" />
      <Group margin="0 2rem" style={{ maxWidth: '24rem' }}>
        <Subtitle>Oh, hello there.</Subtitle>
        <Text>
          Looks like you&apos;re new here.
          <br />
          <br />
          Penn Mobile Portal allows organizations to connect and engage with
          students on the Penn Mobile app. Make posts for recruiting, events, or
          campaigns and watch in real time as users see and interact with your
          content.
        </Text>
        <Text>
          Ready to get started? {/* TODO: change this post/create */}
          <Link href="/polls/create">
            <a style={{ color: colors.MEDIUM_BLUE }}>Create a new post</a>
          </Link>
          <IconArrowRight />
        </Text>
      </Group>
    </Group>
  </Row>
)

export default Dashboard
