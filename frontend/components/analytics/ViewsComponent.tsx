import React from 'react'

const containerStyle = { display: 'flex', flexDirection: 'column' }

const cardStyle = {
  display: 'flex',
  border: '2px solid #cbd5e0', // Equivalent to border-2 border-slate-200
  borderRadius: '0.375rem', // Equivalent to rounded-md
  position: 'relative',
  width: '20rem', // Equivalent to w-80
}

const centerLineStyle = {
  position: 'absolute',
  top: '50%',
  left: '50%',
  height: '5rem', // Equivalent to h-20
  backgroundColor: '#cbd5e0', // Equivalent to bg-slate-200
  width: '0.125rem', // Equivalent to w-0.5
  transform: 'translate(-50%, -50%)',
}

const columnStyle = {
  display: 'flex',
  flexDirection: 'column',
  flex: '0.5',
  padding: '1.5rem', // Equivalent to p-6
}

const numberStyle = {
  fontSize: '2.5rem',
  textAlign: 'left',
  marginBottom: 20,
  marginTop: 10,
}

const totalViewsStyle = {
  fontSize: '0.875rem',
  textAlign: 'left',
  margin: 0,
}

export default function ViewsComponent() {
  return (
    <div style={containerStyle as React.CSSProperties}>
      <div style={cardStyle as React.CSSProperties}>
        <div style={centerLineStyle as React.CSSProperties} />
        <div style={columnStyle as React.CSSProperties}>
          <div style={numberStyle as React.CSSProperties}>32</div>
          <div style={totalViewsStyle as React.CSSProperties}>total views</div>
        </div>
        <div style={columnStyle as React.CSSProperties}>
          <div style={numberStyle as React.CSSProperties}>10</div>
          <div style={totalViewsStyle as React.CSSProperties}>unique views</div>
        </div>
      </div>
    </div>
  )
}
