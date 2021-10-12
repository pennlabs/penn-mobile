import React from 'react'
import s from 'styled-components'
import Link from 'next/link'

import { Text } from '../styles/Text'
import { HOME_ROUTE } from '../../utils/routes'

const LogoStyle = s.div`
  display: inline-block;
`

const LOGO_SIZE = '35px'
const LogoImageStyle = s.img`
  height: ${LOGO_SIZE};
  width: ${LOGO_SIZE};
  margin-right: 1rem;
`

const Logo = () => {
  return (
    <LogoStyle>
      <Link href={HOME_ROUTE}>
        <a style={{ height: LOGO_SIZE }}>
          <LogoImageStyle
            src="/penn-mobile.svg"
            alt="Penn Mobile Logo"
            width={LOGO_SIZE}
            height={LOGO_SIZE}
          ></LogoImageStyle>
        </a>
      </Link>
      <Link href={HOME_ROUTE}>
        <a>
          <Text
            size={'1.5rem'}
            style={{
              display: 'inline-block',
              transform: 'translateY(-0.5rem)',
            }}
          >
            Penn Mobile Portal
          </Text>
        </a>
      </Link>
    </LogoStyle>
  )
}

export default Logo
