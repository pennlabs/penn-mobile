import s from 'styled-components'

import dynamic from 'next/dynamic'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import {
  faCircle,
  faTimes,
  faInfoCircle,
  faArrowCircleRight,
} from '@fortawesome/free-solid-svg-icons'
import { colors } from '@/components/styles/colors'
import Dashboard from '@/public/icons/dashboard.svg'
import Analytics from '@/public/icons/analytics.svg'
import Settings from '@/public/icons/settings.svg'

/**
 * renders icon svg from public/icons as a component
 * @param {string} name icon filename
 */
export const Icon = ({
  name,
  margin,
  color,
}: { name: string } & IIconProps) => {
  // icons to load statically to prevent flickering
  switch (name) {
    case 'dashboard':
      return (
        <IconWrapper margin={margin} color={color}>
          <Dashboard />
        </IconWrapper>
      )
    case 'analytics':
      return (
        <IconWrapper margin={margin} color={color}>
          <Analytics />
        </IconWrapper>
      )
    case 'settings':
      return (
        <IconWrapper margin={margin} color={color}>
          <Settings />
        </IconWrapper>
      )
  }

  const IconSvg = dynamic(() => import(`@/public/icons/${name}.svg`))

  return (
    <IconWrapper margin={margin} color={color}>
      <IconSvg />
    </IconWrapper>
  )
}

interface IIconProps {
  margin?: string
  color?: string
}

const IconWrapper = s.span<IIconProps>`
  margin: ${(props) => props.margin || '0'};
  color: ${(props) => props.color || colors.DARK_GRAY};
  stroke: ${(props) => props.color || colors.DARK_GRAY};
  display: inline-flex;
  vertical-align: middle;
`

export const IconCircle = ({ color }: { color?: string }) => (
  <IconWrapper color={color}>
    <FontAwesomeIcon icon={faCircle} size="lg" />
  </IconWrapper>
)

export const InfoSpan = ({ infoText }: { infoText: string }) => (
  <IconWrapper
    margin="0 0 0 1rem"
    color={colors.GRAY}
    style={{ fontSize: '0.75rem' }}
  >
    <FontAwesomeIcon
      icon={faInfoCircle}
      size="1x"
      style={{ marginRight: '0.5rem' }}
    />
    {infoText || ''}
  </IconWrapper>
)

const TimesWrapper = s.span`
  position: absolute;
  right: 0.75rem;
  bottom: 0.5rem;
  line-height: 2rem;
  border-left: 1px solid ${colors.LIGHT_GRAY};
  cursor: pointer;
  color: ${colors.GRAY}
`

export const IconTimes = () => (
  <TimesWrapper>
    <FontAwesomeIcon
      icon={faTimes}
      size="lg"
      style={{ marginLeft: '0.75rem' }}
    />
  </TimesWrapper>
)

export const IconArrowRight = () => (
  <IconWrapper color={colors.MEDIUM_BLUE} margin="0 0.5rem">
    <FontAwesomeIcon icon={faArrowCircleRight} size="1x" />
  </IconWrapper>
)
