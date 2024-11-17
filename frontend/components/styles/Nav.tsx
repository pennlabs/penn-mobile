import React, { useContext } from 'react'
import Image from 'next/image'
import Link from 'next/link'
import { useRouter } from 'next/router'

import { AuthUserContext } from '@/utils/auth'
import { User } from '@/utils/types'
import {
  ANALYTICS_ROUTE,
  DASHBOARD_ROUTE,
  SETTINGS_ROUTE,
} from '@/utils/routes'

const iconSrcMap: { [key: string]: string } = {
  dashboard: '/icons/dashboard.svg',
  analytics: '/icons/analytics.svg',
  settings: '/icons/settings.svg',
}

const Profile = ({ user }: { user: User }) => {
  return (
    <div className="flex items-center gap-2 font-work-sans">
      <div className="p-2 w-10 h-10 bg-lighterGray flex items-center justify-center rounded-full">
        {user.first_name[0].toUpperCase()}
        {user.last_name[0].toUpperCase()}
      </div>
      <div>
        {user.first_name} {user.last_name}
      </div>
    </div>
  )
}

const NavItem = ({
  icon,
  title,
  link,
}: {
  icon: string
  title: string
  link: string
}) => {
  const router = useRouter()
  const isActive = router.pathname === link

  return (
    <Link href={link}>
      <div
        className={`flex gap-2 cursor-pointer items-center py-2 px-4 rounded-full border ${
          isActive
            ? 'bg-neutral-50 shadow-sm shadow-neutral-100 border-lighterGray'
            : 'border-transparent'
        }`}
      >
        <img
          src={iconSrcMap[icon] || '/icons/dashboard.svg'}
          alt={`${icon} icon`}
          width={18}
          height={18}
          className={isActive ? 'text-blue-500' : 'text-gray-500'}
        />
        <span
          className={`text-base font-work-sans ${
            isActive ? 'text-blue-500' : 'text-neutral-500'
          }`}
        >
          {title}
        </span>
      </div>
    </Link>
  )
}

export const Nav = () => {
  const { user } = useContext(AuthUserContext)

  return (
    <div className="w-[12rem] bg-white flex flex-col justify-between items-center min-h-screen fixed py-4">
      <div className="flex flex-initial flex-col gap-6 justify-center items-center">
        <h1 className="flex justify-center items-center gap-4">
          <Image
            src="/penn-mobile.svg"
            alt="Penn Mobile"
            width={26}
            height={26}
          />
          <span className="inline text-2xl font-medium">Portal</span>
        </h1>

        <div className="flex flex-col gap-1">
          <NavItem icon="dashboard" title="Dashboard" link={DASHBOARD_ROUTE} />
          <NavItem icon="analytics" title="Analytics" link={ANALYTICS_ROUTE} />
          <NavItem icon="settings" title="Settings" link={SETTINGS_ROUTE} />
        </div>
      </div>
      {user && <Profile user={user} />}
    </div>
  )
}
