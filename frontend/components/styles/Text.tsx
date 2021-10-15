import s from 'styled-components'
import { colors } from '../../utils/colors'

interface ITextProps {
  size?: string
  bold?: boolean
  color?: string
  marginBottom?: string
}

export const Title = s.h1<ITextProps>`
  font-size: 6rem;
  font-weight: normal;
  margin-bottom: ${({ marginBottom }) => marginBottom || '0.5rem'};
  line-height: 1.25;
`

export const Subtitle = s.h2<ITextProps>`
  font-size: 1.75rem;
  font-weight: bold;
  margin-bottom: ${({ marginBottom }) => marginBottom || '0.5rem'};
  line-height: 1.25;
`

export const Heading3 = s.h3<ITextProps>`
  font-size: 1.5rem;
  font-weight: bold;
  margin-bottom: ${({ marginBottom }) => marginBottom || '0.5rem'};
  line-height: 1.25;
`

export const Text = s.p<ITextProps>`
  font-size: ${({ size }) => size || '1rem'};
  font-weight: ${({ bold }) => (bold ? 'bold' : 'normal')};
  margin-bottom: ${({ marginBottom }) => marginBottom || '0.5rem'};
  line-height: 1.25;
  overflow-wrap: break-word;
  color: ${({ color }) => color || '#4a4a4a'};
`
