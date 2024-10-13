import React from 'react'
import s from 'styled-components'

import { colors } from '@/components/styles/colors'
import { PageType } from '@/utils/types'
import { InlineText } from '@/components/styles/Text'

interface iButtonProps {
  color?: string
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

export const ButtonIcon = s.button<iButtonProps>`
  text-align: center;
  background-color: white;
  border: none;
  outline: none;
  padding: 2px;
  cursor: pointer;
  font-family: inherit;
`

export const Toggle = s.div`
  display: inline-block;
  border-radius: 100px;
  background: ${colors.LIGHTER_GRAY};
  padding: 6px;
  height: 2.5rem;
`

export const ToggleOption = React.forwardRef<
  HTMLButtonElement,
  { active: boolean } & React.ButtonHTMLAttributes<HTMLButtonElement>
>(({ active, className, ...props }, ref) => (
  <button
    ref={ref}
    type="button"
    className={`
      border-0
      ${active ? 'bg-blue-500 text-white' : 'bg-neutral-100 text-gray-700'}
      rounded-full
      py-1 px-4
      outline-none
      hover:cursor-pointer
      hover:opacity-80
      transition-opacity
      ${className || ''}
    `}
    {...props}
  />
))

ToggleOption.displayName = 'ToggleOption'

export const PostPollToggle = ({
  activeOption,
  setActiveOption,
}: {
  activeOption: PageType
  setActiveOption: React.Dispatch<React.SetStateAction<PageType>>
}) => (
  <div className="flex items-center rounded-full bg-neutral-100 p-1.5 h-10 align-middle border shadow-sm shadow-neutral-50">
    <ToggleOption
      active={activeOption === PageType.POST}
      onClick={() => setActiveOption(PageType.POST)}
    >
      <InlineText heading color="inherit">
        Posts
      </InlineText>
    </ToggleOption>
    <ToggleOption
      active={activeOption === PageType.POLL}
      onClick={() => setActiveOption(PageType.POLL)}
    >
      <InlineText heading color="inherit">
        Polls
      </InlineText>
    </ToggleOption>
  </div>
)
