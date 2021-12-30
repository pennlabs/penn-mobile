import s from 'styled-components'

interface ITextProps {
  size?: string
  bold?: boolean
  color?: string
  marginBottom?: string
  heading?: boolean // Work Sans
}

export const Title = s.h1<ITextProps>`
  font-size: 6rem;
  font-weight: normal;
  margin-bottom: ${({ marginBottom }) => marginBottom || '0.5rem'};
  line-height: 1.25;
  font-family: 'Work Sans', sans-serif;
`

export const Subtitle = s.h2<ITextProps>`
  font-size: 1.75rem;
  font-weight: ${({ bold }) => (bold === false ? '350' : '500')};
  margin-bottom: ${({ marginBottom }) => marginBottom || '0.5rem'};
  line-height: 1.25;
  font-family: 'Work Sans', sans-serif;
`

export const Heading3 = s.h3<ITextProps>`
  font-size: 1.5rem;
  font-weight: ${({ bold }) => (bold === false ? '350' : '500')};
  margin-bottom: ${({ marginBottom }) => marginBottom || '0.5rem'};
  line-height: 1.25;
  font-family: 'Work Sans', sans-serif;
`

export const Text = s.p<ITextProps>`
  font-size: ${({ size }) => size || '1rem'};
  font-weight: ${({ bold }) => (bold ? '500' : '350')};
  margin-bottom: ${({ marginBottom }) => marginBottom || '0.5rem'};
  line-height: 1.25;
  overflow-wrap: break-word;
  color: ${({ color }) => color || '#4a4a4a'};
  font-family: ${({ heading }) => (heading ? 'Work Sans' : 'Inter')};
`

export const InlineText = s.span<ITextProps>`
  font-size: ${({ size }) => size || '1rem'};
  font-weight: ${({ bold }) => (bold ? '500' : '350')};
  margin-bottom: ${({ marginBottom }) => marginBottom || '0.5rem'};
  line-height: 1.25;
  overflow-wrap: break-word;
  color: ${({ color }) => color || '#4a4a4a'};
  font-family: ${({ heading }) => (heading ? 'Work Sans' : 'Inter')};
`
