import React from 'react'

export default function TagChip({ text }) {
  return (
    <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs bg-gray-200 text-gray-800 dark:bg-gray-800 dark:text-gray-200">
      {text}
    </span>
  )
} 