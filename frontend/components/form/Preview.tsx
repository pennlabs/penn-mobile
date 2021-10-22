import React from 'react'

import s from 'styled-components'
import { Poll } from '../../types'
import { colors } from '../../utils/colors'
import { Group } from '../styles/Layout'
import { Text } from '../styles/Text'

const PhoneCard = s.div`
  border-radius: 10px;
  box-shadow: 0 0 8px 3px #d9d9d9;
  padding: 0.5rem 1rem;
  background-color: ${colors.WHITE};
  margin: 0.5rem;
  font-family: -apple-system, BlinkMacSystemFont;
`

const PhonePollOption = s.div<{ width: number }>`
  background-color: #e3e3e3;
  border-radius: 10px;
  width: ${(props) => `${props.width}%`};
  height: 3rem;
  line-height: 2rem;
  position: relative;
`

const Preview = ({ state }: { state: Poll }) => {
  return (
    <div
      className="phone-preview"
      style={{
        textAlign: 'center',
        transformOrigin: 'top center',
        transform: 'scale(0.9)',
      }}
    >
      <div className="marvel-device iphone-x">
        <div className="notch" style={{ marginTop: -1 }}>
          <div className="camera" />
          <div className="speaker" />
        </div>
        <div className="top-bar" />
        <div className="sleep" />
        <div className="bottom-bar" />
        <div className="volume" />
        <div className="overflow">
          <div className="shadow shadow--tr" />
          <div className="shadow shadow--tl" />
          <div className="shadow shadow--br" />
          <div className="shadow shadow--bl" />
        </div>
        <div className="inner-shadow" />
        <div
          className="screen"
          style={{
            textAlign: 'left',
            userSelect: 'none',
            pointerEvents: 'none',
          }}
        >
          <img
            src="/phone_header.png"
            style={{ width: '100%' }}
            alt="Phone Header"
          />
          <PhoneCard>
            <Text size="12px" color={colors.LIGHT_GRAY}>
              POLL FROM{' '}
              <span style={{ fontWeight: 'bold' }}>
                {state.source.toUpperCase()}
              </span>
            </Text>
            <Text size="1rem" bold>
              {state.question}
            </Text>
            {Object.entries(state.pollOptions).map(([key, value]) => (
              <Group
                horizontal
                justifyContent="space-between"
                style={{ marginBottom: '0.5rem' }}
                key={key}
              >
                <PhonePollOption
                  key={key}
                  width={100 / Object.entries(state.pollOptions).length}
                />
                <Text
                  bold
                  color={colors.DARK_GRAY}
                  style={{ position: 'absolute', marginLeft: '0.5rem' }}
                >
                  {value || 'Example Poll Option'}
                </Text>
                <Text size="1rem" bold color={colors.LIGHT_GRAY}>{`${Math.floor(
                  100 / Object.entries(state.pollOptions).length
                )}%`}</Text>
              </Group>
            ))}
          </PhoneCard>
        </div>
      </div>
    </div>
  )
}

export default Preview
