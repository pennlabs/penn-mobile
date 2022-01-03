import s, { css } from 'styled-components'
import { colors } from './colors'

interface iBadgeProps {
  active?: boolean
}

export const Badge = s.button<iBadgeProps>(
  ({ active }) => css`
    border-radius: 100px;
    padding: 0 1rem;
    height: 1.75rem;
    background-color: ${active ? '#d2ebfc' : '#f2f2f2'};
    color: ${active ? '#209cee' : colors.DARK_GRAY};
    border: solid 1px ${active ? '#209cee' : '#e0e0e0'};
    cursor: pointer;
  `
)
