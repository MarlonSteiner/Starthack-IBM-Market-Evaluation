import React from 'react'

const colorByImpact = {
  up: 'bg-green-100 text-green-700',
  down: 'bg-red-100 text-red-700',
  neutral: 'bg-gray-100 text-gray-700',
}

export default function ImpactChip({ impact }) {
  const label = impact === 'up' ? 'Up' : impact === 'down' ? 'Down' : 'Neutral'
  const color = colorByImpact[impact] || colorByImpact.neutral
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold ${color}`}>
      {label}
    </span>
  )
} 