import React, { ReactNode } from 'react'

import s, { css } from 'styled-components'
import { PollType, PostType } from '@/utils/types'
import { colors } from '@/components/styles/colors'
import { Group } from '@/components/styles/Layout'
import { Text } from '@/components/styles/Text'
import { DESKTOP, minWidth } from '@/components/styles/sizes'

interface IPhoneCard {
  borderRadius?: string
  padding?: string
}

const PhoneCard = s.div<IPhoneCard>(
  (props) => css`
    border-radius: ${props.borderRadius || '0'};
    box-shadow: 0 0 8px 3px #d9d9d9;
    padding: ${props.padding || '0'};
    background-color: ${colors.WHITE};
    margin: 1rem;

    ${!props.padding &&
    `p {
      margin-top: 0 !important;
    }`}
  `
)

const PhonePollOption = s.div<{ width: number }>`
  background-color: #e3e3e3;
  border-radius: 10px;
  width: ${(props) => `${props.width}%`};
  height: 3rem;
  line-height: 2rem;
  position: relative;
`

const PhoneWrapper = s.div`
  ${minWidth(DESKTOP)} {
    position: fixed;
  }
`

const PhonePreview = ({ children }: { children: ReactNode }) => {
  return (
    <PhoneWrapper>
      <div
        className="phone-preview"
        style={{
          textAlign: 'center',
          transformOrigin: 'top center',
          transform: 'scale(0.85)',
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
          <div className="screen" style={{ textAlign: 'left' }}>
            <img
              src="/phone_header.png"
              style={{ width: '100%' }}
              alt="Phone Header"
            />
            {children}
          </div>
        </div>
      </div>
    </PhoneWrapper>
  )
}

export const PostPhonePreview = ({ state }: { state: PostType }) => (
  <PhonePreview>
    <PhoneCard borderRadius="15px">
      <div
        className="img-wrapper"
        style={{
          backgroundColor: '#eee',
          borderRadius: '15px 15px 0 0',
          overflow: 'hidden',
        }}
      >
        <div
          style={{
            backgroundSize: 'cover',
            backgroundPosition: 'center',
            backgroundRepeat: 'no-repeat',
            height: 175,
            backgroundImage: `url("${state.image_url}")`,
          }}
        />
      </div>
      <div style={{ padding: '0.5rem' }}>
        <Text size="12px" color={colors.LIGHT_GRAY} bold>
          {state.club_code.toUpperCase()}
        </Text>
        <Text bold>{state.title}</Text>
        <Text size="12px" color={colors.LIGHT_GRAY} bold>
          {state.subtitle}
        </Text>
      </div>
    </PhoneCard>
  </PhonePreview>
)

export const PollsPhonePreview = ({ state }: { state: PollType }) => (
  <PhonePreview>
    <PhoneCard borderRadius="10px" padding="0.5rem 1rem">
      <Text size="12px" color={colors.LIGHT_GRAY}>
        POLL FROM{' '}
        <span style={{ fontWeight: 'bold' }}>
          {state.club_code.toUpperCase()}
        </span>
      </Text>
      <Text size="1rem" bold>
        {state.question}
      </Text>
      {state.options.map((option, index) => (
        <Group
          horizontal
          justifyContent="space-between"
          style={{ marginBottom: '0.5rem' }}
          key={`preview-group-${option.id}`}
        >
          <PhonePollOption
            key={`preview-opt-${option.id}`}
            width={100 / state.options.length}
          />
          <Text
            bold
            color={colors.DARK_GRAY}
            style={{ position: 'absolute', marginLeft: '0.5rem' }}
          >
            {option.choice || `poll option #${index + 1}`}
          </Text>
          <Text size="1rem" bold color={colors.LIGHT_GRAY}>{`${Math.floor(
            100 / state.options.length
          )}%`}</Text>
        </Group>
      ))}
    </PhoneCard>
  </PhonePreview>
)
