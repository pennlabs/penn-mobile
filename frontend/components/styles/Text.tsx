import s from 'styled-components'

interface ITextProps {
  size?: string
  bold?: boolean
  marginBottom?: string
}

export const Title = s.h1<ITextProps>`
  font-size: 2rem;
  font-weight: bold;
  margin-bottom: ${({ marginBottom }) => marginBottom || '0.5rem'};
  line-height: 1.25;
`

export const Subtitle = s.h2<ITextProps>`
  font-size: 1.75rem;
  font-weight: bold;
  margin-bottom: ${({ marginBottom }) => marginBottom || '0.5rem'};
  line-height: 1.25;
`

export const Text = s.p<ITextProps>`
  font-size: ${({ size }) => size || '0.75rem'};
  font-weight: ${({ bold }) => (bold ? 'bold' : 'normal')};
  margin-bottom: ${({ marginBottom }) => marginBottom || '0.5rem'};
  line-height: 1.25;
`
