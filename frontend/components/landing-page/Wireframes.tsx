import React from 'react'
import s from 'styled-components'

const IPhoneImg = s.img`
  position: absolute;
  left: -10%;
  bottom: 0%;
  z-index: 1;
  width: 420px;
`

const Wireframes = () => (
  <div style={{ position: 'relative', top: '-10%' }}>
    <img
      style={{ zIndex: 3, width: '1150px' }}
      src="/web-mockup4x.png"
      alt="web-mockup"
    />
    <IPhoneImg src="/phone-mockup4x.png" alt="phone-mockup" />
  </div>
)

export default Wireframes
