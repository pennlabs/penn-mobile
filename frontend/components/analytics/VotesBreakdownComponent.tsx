import React from 'react'
import { stringToRGB } from '@/utils/utils'

export default function VotesBreakdownComponent({
  names,
}: {
  names: string[]
}) {
  const Row = ({ color, text }: { color: string; text: string }) => {
    return (
      <div style={{ display: 'flex', marginBottom: 15 }}>
        <div
          style={{
            width: 15,
            height: 15,
            backgroundColor: color,
            marginRight: 5,
            borderRadius: '25%',
          }}
        />
        <div style={{ fontSize: '1rem' }}>{text}</div>
      </div>
    )
  }
  return (
    <div>
      {names.map((name: string) => (
        <Row color={stringToRGB(name)} text={name} key={name} />
      ))}
    </div>
  )
}
