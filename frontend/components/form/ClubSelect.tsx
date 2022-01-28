import React, { useContext } from 'react'
import Select, { SingleValue } from 'react-select'

import { AuthUserContext } from '@/utils/auth'
import { updateStateType } from '@/utils/types'

interface ClubSelectProps {
  updateState: updateStateType
  clubCode: string
}

const ClubSelect = ({ updateState, clubCode }: ClubSelectProps) => {
  const { user } = useContext(AuthUserContext)
  const clubOptions = user?.clubs.map((club) => ({
    value: club.club_code,
    label: club.name,
  }))

  const initialClub = clubOptions?.find((club) => club.value === clubCode)

  const onChange = (
    newValue: SingleValue<{ value: string; label: string }>
  ) => {
    updateState({ club_code: newValue?.value })
  }

  return (
    <Select
      options={clubOptions}
      defaultValue={initialClub}
      isSearchable={false}
      onChange={onChange}
      id="club-select"
      instanceId="club-select"
      styles={{
        control: (base, state) => ({
          ...base,
          boxShadow: 'none',
          borderColor: state.isFocused
            ? 'rgb(50 115 220 / 25%)'
            : base.borderColor,
          '&:hover': { borderColor: 'rgb(50 115 220 / 25%)' },
        }),
      }}
    />
  )
}

export default ClubSelect
