import ImpactChip from './ImpactChip'
import React from 'react'
import TagChip from './TagChip'

export default function NewsCard({ item, onApprove }) {
  const published = new Date(item.publishedAt)
  return (
    <div className="rounded-xl border border-gray-200 dark:border-gray-800 p-4 bg-white dark:bg-gray-900 shadow-sm">
      <div className="flex items-start justify-between gap-4">
        <div>
          <a
            href={item.url}
            target="_blank"
            rel="noreferrer"
            className="text-lg font-semibold hover:underline text-gray-900 dark:text-white"
          >
            {item.title}
          </a>
          <div className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            <span>{item.source}</span>
            <span className="mx-2">•</span>
            <time dateTime={item.publishedAt}>{published.toLocaleString()}</time>
          </div>
        </div>
        <ImpactChip impact={item.impact} />
      </div>

      <div className="mt-3 space-y-1 text-sm text-gray-800 dark:text-gray-200">
        <p><span className="font-semibold">What:</span> {item.whatHappened}</p>
        <p><span className="font-semibold">Why:</span> {item.whyItMatters}</p>
        <p><span className="font-semibold">Portfolio:</span> {item.portfolioImpact}</p>
      </div>

      <div className="mt-3 flex flex-wrap gap-2">
        {item.tags?.map((t) => (
          <TagChip key={t} text={t} />
        ))}
      </div>

      {onApprove && !item.approved && (
        <div className="mt-4">
          <button
            onClick={onApprove}
            className="px-4 py-2 rounded-lg bg-primary text-white hover:opacity-90"
          >
            Approve
          </button>
        </div>
      )}
    </div>
  )
} 