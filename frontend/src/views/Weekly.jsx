import React, { useContext } from 'react'

import NewsCard from '../components/NewsCard'
import { NewsContext } from '../store/NewsContext'

export default function Weekly() {
  const { getLast7DaysApproved } = useContext(NewsContext)
  const items = getLast7DaysApproved()

  return (
    <section className="px-4 sm:px-12 lg:px-24 xl:px-40 py-8">
      <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Weekly Brief</h2>
      <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">Approved items from the last 7 days.</p>
      <div className="mt-6 grid gap-4">
        {items.length === 0 && (
          <div className="text-gray-600 dark:text-gray-300">No approved items in the last 7 days.</div>
        )}
        {items.map((item) => (
          <NewsCard key={item.id} item={item} />
        ))}
      </div>
    </section>
  )
} 