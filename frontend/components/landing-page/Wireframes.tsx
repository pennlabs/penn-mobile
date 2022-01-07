import React from 'react'
import s from 'styled-components'
import {
  DESKTOP,
  maxWidth,
  minWidth,
  NAV_HEIGHT,
} from '@/components/styles/sizes'

const DesktopWireframesStyle = s.div`
  position: absolute;
  right: 0;
  top: calc(-${NAV_HEIGHT} + 1rem);
  z-index: 2;
  ${maxWidth(DESKTOP)} {
    display: none;
  }
`

const MobileWireframesStyle = s.div`
  width: 100%;
  height: auto;
  margin-bottom: 0;
  ${minWidth(DESKTOP)} {
    display: none;
  }
`

export const DesktopWireframes = () => (
  <DesktopWireframesStyle>
    <img src="/landing-page.svg" alt="web-mockup" />
  </DesktopWireframesStyle>
)

export const MobileWireframes = () => (
  <MobileWireframesStyle>
    <img style={{ float: 'right' }} src="/landing-page.svg" alt="web-mockup" />
  </MobileWireframesStyle>
)
