import s from 'styled-components'
import Link from 'next/link'

import { colors } from '@/components/styles/colors'
import { PageType } from '@/utils/types'
import { CREATE_POLL_ROUTE, CREATE_POST_ROUTE } from '@/utils/routes'

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

interface iToggleButtonProps {
  link?: boolean
  activeOption?: PageType
}

const ToggleContainer = s.div`
  display: inline-block;
  border-radius: 100px;
  background: ${colors.LIGHTER_GRAY};
  padding: 5px;
`

const ToggleOptionStyle = s.button<{ active: boolean }>`
  border-width: 0;
  background-color: ${(props) =>
    props.active ? colors.MEDIUM_BLUE : colors.LIGHTER_GRAY};
  color: ${(props) => props.active && 'white'};
  border-radius: 100px;
  height: 28px;
  padding: 0 1rem;
  outline: none;
  cursor: pointer;
`

export const ToggleButton = ({ link, activeOption }: iToggleButtonProps) => {
  const ToggleOption = ({
    label,
    active,
    route,
  }: {
    label: string
    active: boolean
    route: string
  }) =>
    link ? (
      <ToggleOptionStyle active={active}>
        <Link href={route}>
          <a>{label}</a>
        </Link>
      </ToggleOptionStyle>
    ) : (
      <ToggleOptionStyle active={active}>{label}</ToggleOptionStyle>
    )

  return (
    <ToggleContainer>
      <ToggleOption
        active={activeOption == PageType.POST}
        label="Post"
        route={CREATE_POST_ROUTE}
      />
      <ToggleOption
        active={activeOption === PageType.POLL}
        label="Poll"
        route={CREATE_POLL_ROUTE}
      />
    </ToggleContainer>
  )
}
