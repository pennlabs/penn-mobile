import React from 'react'
import s from 'styled-components'
import Link from 'next/link'

import { Text } from '../styles/Text'
import { HOME_ROUTE } from '../../utils/routes'
import { maxWidth, TABLET } from '../styles/sizes'

const LogoStyle = s.div`
  display: inline-block;
`

const LOGO_SIZE = '35px'
const LogoImageStyle = s.img`
  height: ${LOGO_SIZE};
  width: ${LOGO_SIZE};
  margin-right: 1rem;
`

const LogoTextWrapper = s.div`
  display: inline-block;
  transform: translateY(-0.5rem);
  ${maxWidth(TABLET)} {
    display: none;
  }
`

const Logo = () => (
  <LogoStyle>
    <Link href={HOME_ROUTE}>
      <a style={{ height: LOGO_SIZE }}>
        <LogoImageStyle src="/penn-mobile.svg" alt="Penn Mobile Logo" />
        <LogoTextWrapper>
          <Text size="1.5rem" heading>
            Portal
          </Text>
        </LogoTextWrapper>
      </a>
    </Link>
  </LogoStyle>
)

export default Logo
