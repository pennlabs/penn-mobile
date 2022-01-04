import React from 'react'
import s from 'styled-components'
import Link from 'next/link'

import Logo from '@/components/header/Logo'
import { Button } from '@/components/styles/Buttons'
import { colors } from '@/components/styles/colors'
import { Group } from '@/components/styles/Layout'
import { NAV_HEIGHT } from '@/components/styles/sizes'
import { DASHBOARD_ROUTE } from '@/utils/routes'

const NavStyle = s.nav`
  padding: 1rem 1.5rem 0rem 1.5rem;
  display: flex;
  width: 100%;
  max-height: ${NAV_HEIGHT};
  position: fixed;
  top: 0;
  left: 0;
  background: rgba(255, 255, 255, 0.9);
  align-items: center;
  justify-content: space-between;
  z-index: 100;
`

const NavSpace = s.div`
  width: 100%;
  height: ${NAV_HEIGHT};
`

const LandingPageNav = () => {
  return (
    <>
      <NavStyle>
        <Logo />
        <Group horizontal margin="0 0 0.5rem 0">
          <Link href={`/api/accounts/login/?next=${DASHBOARD_ROUTE}`}>
            <a>
              <Button color={colors.MEDIUM_BLUE}>Login</Button>
            </a>
          </Link>
        </Group>
      </NavStyle>
      <NavSpace />
    </>
  )
}

export default LandingPageNav
