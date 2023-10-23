import React from 'react'
import { PieChart, Pie, Cell, Tooltip } from 'recharts'
import s from 'styled-components'
import { SCHOOL_COLORS, YEAR_COLORS } from './poll_constants'

const PieChartNumberWrapper = s.div`
  font-weight: semi-bold;
  font-size: 2rem;
  text-align: center;
  margin-bottom: 5px;
`

const SimplePieChart = ({ schoolData, yearData, mode, uniqueVotes }) => {
  const dataToUse = mode === 'school' ? schoolData : yearData
  const COLORS = mode === 'school' ? SCHOOL_COLORS : YEAR_COLORS
  const formattedData = Object.keys(dataToUse).map((school) => ({
    name: school,
    value: schoolData[school],
  }))
  return (
    <div
      style={{
        position: 'relative',
        height: 250,
        width: 250,
      }}
    >
      <div
        style={{
          position: 'absolute',
          left: '50%',
          top: '50%',
          transform: 'translate(-50%, -50%)',
        }}
      >
        <PieChartNumberWrapper>{uniqueVotes}</PieChartNumberWrapper>
        <div style={{ color: 'grey' }}>Unique Voters</div>
      </div>
      <PieChart width={250} height={250}>
        <Pie
          data={formattedData}
          dataKey="value"
          nameKey="name"
          cx={120}
          cy={120}
          outerRadius={125}
          innerRadius={60}
        >
          {formattedData.map((entry: string, index: number) => {
            return (
              // eslint-disable-next-line react/no-array-index-key
              <Cell key={`cell-${index}`} fill={COLORS[entry.name]} />
            )
          })}
        </Pie>
        <Tooltip />
      </PieChart>
    </div>
  )
}

export default SimplePieChart
