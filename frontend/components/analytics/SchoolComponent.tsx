import React from 'react'

export default function SchoolComponent({ school }: { school: string }) {
  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
      }}
    >
      <div
        style={{
          borderRadius: '0.375rem',
          backgroundColor: 'red',
          width: 4,
          height: 4,
        }}
      />
      <div>{school}</div>
    </div>
  )
}
