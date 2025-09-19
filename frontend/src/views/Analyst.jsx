import React, { useContext } from 'react'

import NewsCard from '../components/NewsCard'
import { NewsContext } from '../store/NewsContext'

export default function Analyst() {
  const { getPending, approve } = useContext(NewsContext)
  const items = getPending()

  return (
    <section className="px-4 sm:px-12 lg:px-24 xl:px-40 py-8">
      <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Analyst Queue</h2>
      <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">Review, tweak, and approve items.</p>
      <div className="mt-6 grid gap-4">
        {items.length === 0 && (
          <div className="text-gray-600 dark:text-gray-300">No items pending approval.</div>
        )}
        {items.map((item) => (
          <NewsCard key={item.id} item={item} onApprove={() => approve(item.id)} />
        ))}
      </div>
    </section>
  )
} 