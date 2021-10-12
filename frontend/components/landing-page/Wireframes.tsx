import React from 'react'
import s from 'styled-components'

const IPhoneImg = s.img`
  position: absolute;
  left: 20%;
  bottom: -30%;
  z-index: 1;
`

const Wireframes = () => (
  <div style={{ position: 'relative' }}>
    <img
      style={{ zIndex: 3 }}
      src="/browser-wireframe.svg"
      alt="browser wireframe"
    />
    <IPhoneImg src="/iphone-wireframe.svg" alt="iphone wireframe" />
  </div>
)

export default Wireframes
