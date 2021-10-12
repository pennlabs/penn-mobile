import React from 'react'
import s from 'styled-components'
import { colors } from '../../utils/colors'

interface iButtonProps {
  color: string
  hide?: boolean
}

export const Button = s.button<iButtonProps>`
  margin: 8px 8px 0px 0px;
  height: 2rem;
  line-height: 2rem;
  text-align: center;
  border: solid 0 #979797;
  background-color: ${(props) => props.color};
  color: #ffffff;
  border-radius: 5px;
  outline: none;
  padding: 0px 15px 0px 15px;
  display: ${(props) => (props.hide ? 'none' : 'flex')};
  cursor: pointer;
  font-family: inherit;
`
