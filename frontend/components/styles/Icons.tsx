import s from 'styled-components'

import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import {
  faCircle,
  faPlus,
  faTimes,
  faInfoCircle,
  faArrowCircleRight,
} from '@fortawesome/free-solid-svg-icons'
import { colors } from '@/components/styles/colors'
import Dashboard from '../../public/icons/dashboard.svg'
import Analytics from '../../public/icons/analytics.svg'
import Settings from '../../public/icons/settings.svg'

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
    margin="0 0 0 1.5rem"
    color={colors.GRAY}
    style={{ fontSize: '14px' }}
  >
    <FontAwesomeIcon
      icon={faInfoCircle}
      size="1x"
      style={{ marginRight: '1rem' }}
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

// TODO: include iconwrapper in this if not used for anything else?
export const getIcon = (icon: string) => {
  switch (icon) {
    case 'dashboard':
      return <IconDashboard />
    case 'analytics':
      return <IconAnalytics />
    case 'settings':
      return <IconSettings />
    default:
      return <IconDashboard />
  }
}

export const IconDashboard = () => (
  <IconWrapper margin="auto 1rem 1px 0">
    <Dashboard />
  </IconWrapper>
)

export const IconAnalytics = () => (
  <IconWrapper margin="auto 1rem 1px 0">
    <Analytics />
  </IconWrapper>
)

export const IconSettings = () => (
  <IconWrapper margin="auto 1rem 1px 0">
    <Settings />
  </IconWrapper>
)
