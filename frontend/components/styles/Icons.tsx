import s from 'styled-components'

import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faCircle } from '@fortawesome/free-solid-svg-icons'
import { colors } from '../../utils/colors'

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
