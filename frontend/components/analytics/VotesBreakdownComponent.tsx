import React from 'react'
import { SCHOOL_COLORS, YEAR_COLORS } from './poll_constants'

export default function VotesBreakdownComponent({
  schoolData,
  yearData,
  mode,
}) {
  const schoolNames = Object.keys(schoolData)
  const yearNames = Object.keys(yearData)
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
      {mode === 'school'
        ? schoolNames.map((name: string) => (
            <Row color={SCHOOL_COLORS[name]} text={name} key={name} />
          ))
        : yearNames.map((name: string) => (
            <Row color={YEAR_COLORS[name]} text={name} key={name} />
          ))}
    </div>
  )
}
