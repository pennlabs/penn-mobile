import React from 'react'
import s from 'styled-components'
import Link from 'next/link'

import Logo from '../header/Logo'
import { Text } from '../styles/Text'
import { Button } from '../styles/Buttons'
import { colors } from '../../utils/colors'
import { Group } from '../styles/Layout'

const NAV_HEIGHT = '4.25rem'

const NavStyle = s.nav`
  padding: 1rem 1.5rem 0rem 1.5rem;
  display: flex;
  width: 100%;
  min-height: ${NAV_HEIGHT};
  position: fixed;
  top: 0;
  left: 0;
  background: ${colors.WHITE};
  align-items: center;
  justify-content: space-between;
`

const NavSpace = s.div`
  width: 100%;
  height: ${NAV_HEIGHT};
`

const NavLink = ({ title }: { title: string }) => {
  return (
    <Link href={`/${title}`}>
      <a>
        <Text size={'1rem'} style={{ marginRight: '4rem' }}>
          {title}
        </Text>
      </a>
    </Link>
  )
}

const Nav = () => {
  return (
    <>
      <NavStyle>
        <Logo />
        <Group>
          <NavLink title="Home" />
          <NavLink title="About" />
          <NavLink title="Tutorial" />
          <NavLink title="Team" />
          <Button color={colors.MEDIUM_BLUE}>Login</Button>
        </Group>
      </NavStyle>
      {/* <NavSpace /> */}
    </>
  )
}

export default Nav
