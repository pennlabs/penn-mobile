import s from 'styled-components'
import Link from 'next/link'

import { colors } from '../../utils/colors'
import { PageType } from '../../types'

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
  page: PageType
  active?: boolean
}

const ToggleButtonStyle = s.button<iToggleButtonProps>`
  border-width: 0;
  background-color: ${(props) =>
    props.active ? colors.MEDIUM_BLUE : colors.LIGHT_GRAY};
  color: white;
  border-radius: ${(props) =>
    props.page === PageType.POST ? '12px 0px 0px 12px' : '0px 12px 12px 0px'};
  height: 28px;
  width: 115px;
  outline: none;
  cursor: pointer;
`

// TODO: change links here if i change create route. also refactor this perhaps?
export const ToggleButton = ({ currPage }: { currPage: PageType }) =>
  currPage === PageType.POST ? (
    <>
      <ToggleButtonStyle page={currPage} active>
        New Post
      </ToggleButtonStyle>
      <Link href="/polls/create">
        <a>
          <ToggleButtonStyle page={PageType.POLL}>New Poll</ToggleButtonStyle>
        </a>
      </Link>
    </>
  ) : (
    <>
      <Link href="/post/create">
        <a>
          <ToggleButtonStyle page={PageType.POST}>New Post</ToggleButtonStyle>
        </a>
      </Link>
      <ToggleButtonStyle page={currPage} active>
        New Poll
      </ToggleButtonStyle>
    </>
  )
