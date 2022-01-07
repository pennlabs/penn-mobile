import s from 'styled-components'

import dynamic from 'next/dynamic'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import {
  faCircle,
  faPlus,
  faTimes,
  faInfoCircle,
  faArrowCircleRight,
} from '@fortawesome/free-solid-svg-icons'
import { colors } from '@/components/styles/colors'

/**
 * renders icon svg from public/icons as a component
 * @param {string} name icon filename
 */
export const Icon = ({ name, margin }: { name: string; margin?: string }) => {
  const IconSvg = dynamic(() => import(`@/public/icons/${name}.svg`))

  return (
    <IconWrapper margin={margin}>
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
  color: ${(props) => props.color || colors.MEDIUM_BLUE};
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
    style={{
      fontSize: '0.75rem',
      lineHeight: '1.25rem',
      verticalAlign: 'middle',
    }}
  >
    <FontAwesomeIcon
      icon={faInfoCircle}
      size="1x"
      style={{ marginRight: '0.5rem' }}
    />
    {infoText || ''}
  </IconWrapper>
)

export const IconPlus = ({ margin }: { margin: string }) => (
  <IconWrapper color={colors.WHITE} margin={margin}>
    <FontAwesomeIcon icon={faPlus} size="sm" />
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
