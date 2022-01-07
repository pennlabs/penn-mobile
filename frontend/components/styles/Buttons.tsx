import s from 'styled-components'

import { colors } from '@/components/styles/colors'

interface iButtonProps {
  color: string
  hide?: boolean
  round?: boolean
}

export const Button = s.button<iButtonProps>`
  margin: 8px 8px 0px 0px;
  height: 2rem;
  line-height: 2rem;
  text-align: center;
  border: solid 0 #979797;
  background-color: ${(props) => props.color};
  color: #ffffff;
  border-radius: ${(props) => (props.round ? '100px' : '5px')};
  outline: none;
  padding: 0px 15px 0px 15px;
  display: ${(props) => (props.hide ? 'none' : 'flex')};
  cursor: pointer;
  font-family: inherit;
`

export const Toggle = s.div`
  display: inline-block;
  border-radius: 100px;
  background: ${colors.LIGHTER_GRAY};
  padding: 5px;
`

export const ToggleOption = s.button<{ active: boolean }>`
  border-width: 0;
  background-color: ${(props) =>
    props.active ? colors.MEDIUM_BLUE : colors.LIGHTER_GRAY};
  color: ${(props) => props.active && 'white'};
  border-radius: 100px;
  line-height: inherit;
  padding: 0.25rem 1rem;
  outline: none;

  &:hover {
    cursor: pointer;
    opacity: 0.7;
  }
`
