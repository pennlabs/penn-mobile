import React from 'react'
import { PieChart, Pie, Cell, Tooltip } from 'recharts'
import s from 'styled-components'
import { stringToRGB } from '@/utils/utils'

const PieChartNumberWrapper = s.div`
  font-weight: semi-bold;
  font-size: 2rem;
  text-align: center;
  margin-bottom: 5px;
`

const SimplePieChart = ({
  data,
  uniqueVotes,
}: {
  data: { [key: string]: number }
  uniqueVotes: number
}) => {
  const formattedData = Object.entries(data).map(([key, value]) => ({
    name: key,
    value,
  }))
  return Object.keys(data).length !== 0 ? (
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
          {formattedData.map((entry) => {
            return <Cell key={entry.name} fill={stringToRGB(entry.name)} />
          })}
        </Pie>
        <Tooltip />
      </PieChart>
    </div>
  ) : (
    <div
      style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
      }}
    >
      No data available yet.
    </div>
  )
}

export default SimplePieChart
