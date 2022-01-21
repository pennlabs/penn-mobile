import React from 'react'
import Image from 'next/image'
import s from 'styled-components'
import {
  DESKTOP,
  maxWidth,
  minWidth,
  NAV_HEIGHT,
} from '@/components/styles/sizes'
import LandingPageImg from '@/public/landing-page.jpg'

const DesktopWireframesStyle = s.div`
  position: absolute;
  right: 0;
  top: calc(-${NAV_HEIGHT} + 1rem);
  z-index: 2;
  width: 50vw;
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
    <Image
      src={LandingPageImg}
      alt="web-mockup"
      placeholder="blur"
      layout="responsive"
      objectFit="contain"
    />
  </DesktopWireframesStyle>
)

export const MobileWireframes = () => (
  <MobileWireframesStyle>
    <img style={{ float: 'right' }} src="/landing-page.svg" alt="web-mockup" />
  </MobileWireframesStyle>
)
