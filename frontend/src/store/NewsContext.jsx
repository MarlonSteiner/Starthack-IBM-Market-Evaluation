import React, { createContext, useCallback, useMemo, useState } from 'react'
import { isToday, isWithinLastDays, mockNewsItems } from '../data/mockNews'

export const NewsContext = createContext({
  items: [],
  approve: (id) => {},
  getTodayApproved: () => [],
  getLast7DaysApproved: () => [],
  getPending: () => [],
})

export const NewsProvider = ({ children }) => {
  const [items, setItems] = useState(mockNewsItems)

  const approve = useCallback((id) => {
    setItems((prev) => prev.map((n) => (n.id === id ? { ...n, approved: true } : n)))
  }, [])

  const getTodayApproved = useCallback(() => {
    return items.filter((n) => isToday(n.publishedAt) && n.approved)
  }, [items])

  const getLast7DaysApproved = useCallback(() => {
    return items.filter((n) => isWithinLastDays(n.publishedAt, 7) && n.approved)
  }, [items])

  const getPending = useCallback(() => {
    return items.filter((n) => !n.approved)
  }, [items])

  const value = useMemo(
    () => ({ items, approve, getTodayApproved, getLast7DaysApproved, getPending }),
    [items, approve, getTodayApproved, getLast7DaysApproved, getPending]
  )

  return <NewsContext.Provider value={value}>{children}</NewsContext.Provider>
} 