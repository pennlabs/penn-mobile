import React, { useContext } from 'react'
import s from 'styled-components'
import Link from 'next/link'

import { AuthUserContext } from '@/utils/auth'
import { User } from '@/utils/types'
import { colors } from '@/components/styles/colors'
import { Text } from '@/components/styles/Text'
import { getIcon } from '@/components/styles/Icons'
import { Group } from './Layout'

const NAV_WIDTH = '14%'
const PROFILE_HEIGHT = '18vh'

const Profile = ({ user }: { user: User }) => {
  const ProfileStyle = s.div`
    position: fixed;
    height: ${PROFILE_HEIGHT};
    width: ${NAV_WIDTH};
    background-color: ${colors.NAV_PROFILE_BACKGROUND};
    text-align: center;
    display: flex;
    justify-content: center;
    align-items: center;
  `

  // TODO: replace this with user's org and add user img
  return (
    <ProfileStyle>
      <Text bold heading>
        {user.username}
      </Text>
    </ProfileStyle>
  )
}

const NavItemsStyle = s.div`
  width: ${NAV_WIDTH};
  margin-top: calc(${PROFILE_HEIGHT} + 1rem);
  position: fixed;
`

const NavItem = ({
  icon,
  title,
  link,
}: {
  icon: string
  title: string
  link: string
}) => {
  const NavItemStyle = s.div`
    display: flex;
    cursor: pointer;
  `

  return (
    <Link href={link}>
      <NavItemStyle>
        {getIcon(icon)}
        <Text heading>{title}</Text>
      </NavItemStyle>
    </Link>
  )
}

const NavStyle = s.div`
  width: ${NAV_WIDTH};
  background-color: ${colors.NAV_BACKGROUND};
  text-align: center;
  min-height: 99vh;
`

export const Nav = () => {
  const { user } = useContext(AuthUserContext)

  return (
    <NavStyle>
      {user && <Profile user={user} />}
      <NavItemsStyle>
        <Group center>
          <NavItem icon="dashboard" title="Dashboard" link="/" />
          <NavItem icon="analytics" title="Analytics" link="/analytics" />
          <NavItem icon="settings" title="Settings" link="/settings" />
        </Group>
      </NavItemsStyle>
    </NavStyle>
  )
}
