import React, { useContext } from 'react'
import s from 'styled-components'
import Link from 'next/link'

import { AuthUserContext } from '@/utils/auth'
import { User } from '@/utils/types'
import { NAV_WIDTH } from '@/components/styles/sizes'
import { colors } from '@/components/styles/colors'
import { InlineText, Text } from '@/components/styles/Text'
import { Icon } from '@/components/styles/Icons'
import { Group } from '@/components/styles/Layout'
import {
  ANALYTICS_ROUTE,
  DASHBOARD_ROUTE,
  SETTINGS_ROUTE,
} from '@/utils/routes'

const PROFILE_HEIGHT = '24vh'
const PROFILE_PIC_SIZE = '4rem'

const ProfileWrapper = s.div`
  height: ${PROFILE_HEIGHT};
  background-color: ${colors.NAV_PROFILE_BACKGROUND};
  text-align: center;
  display: flex;
  justify-content: center;
  align-items: center;
`

const ProfilePicWrapper = s.div`
  border-radius: 50%;
  background-color: ${colors.LIGHT_GRAY};
  width: ${PROFILE_PIC_SIZE};
  height: ${PROFILE_PIC_SIZE};
  margin: 0 auto;
`

const Profile = ({ user }: { user: User }) => {
  return (
    <ProfileWrapper>
      <Group center>
        <ProfilePicWrapper>
          <InlineText bold heading style={{ lineHeight: PROFILE_PIC_SIZE }}>
            {user.first_name[0].toUpperCase()}
            {user.last_name[0].toUpperCase()}
          </InlineText>
        </ProfilePicWrapper>
        <Text bold heading>
          {user.clubs[0]?.name}
        </Text>
      </Group>
    </ProfileWrapper>
  )
}

const NavItemWrapper = s.div`
  display: flex;
  cursor: pointer;
  opacity: 0.8;

  &:hover {
    opacity: 1;
  }
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
  return (
    <Link href={link}>
      <NavItemWrapper>
        <Icon name={icon} margin="auto 1rem 1px 0" />
        <Text heading>{title}</Text>
      </NavItemWrapper>
    </Link>
  )
}

const NavWrapper = s.div`
  width: ${NAV_WIDTH};
  background-color: ${colors.NAV_BACKGROUND};
  text-align: center;
  min-height: 99vh;
  position: fixed;
`

export const Nav = () => {
  const { user } = useContext(AuthUserContext)

  return (
    <NavWrapper>
      {user && <Profile user={user} />}
      <Group center>
        <NavItem icon="dashboard" title="Dashboard" link={DASHBOARD_ROUTE} />
        <NavItem icon="analytics" title="Analytics" link={ANALYTICS_ROUTE} />
        <NavItem icon="settings" title="Settings" link={SETTINGS_ROUTE} />
      </Group>
    </NavWrapper>
  )
}
