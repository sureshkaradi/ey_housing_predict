"use client"

import { FormEvent, useEffect, useState } from 'react'
import NavBar from '../../components/NavBar'

type MarketSummary = {
  total_properties: number
  average_price: number
  median_price: number
  min_price: number
  max_price: number
  average_square_footage: number
  average_school_rating: number
  bedrooms_distribution: Record<string, number>
  bathrooms_distribution: Record<string, number>
}

type FilterSegment = {
  segment: string
  count: number
  average_price: number
  average_square_footage: number
  average_school_rating: number
}

type WhatIfRequest = {
  square_footage: number
  bedrooms: number
  bathrooms: number
  year_built: number
  lot_size: number
  distance_to_city_center: number
  school_rating: number
}

type WhatIfResponse = {
  predicted_price: number
  scenario: WhatIfRequest
}

const defaultScenario: WhatIfRequest = {
  square_footage: 2400,
  bedrooms: 4,
  bathrooms: 3,
  year_built: 2018,
  lot_size: 8000,
  distance_to_city_center: 6,
  school_rating: 8,
}

export default function App2Page() {
  const [summary, setSummary] = useState<MarketSummary | null>(null)
  const [filters, setFilters] = useState({ min_price: 0, max_price: 0, bedrooms: 0 })
  const [segments, setSegments] = useState<FilterSegment[]>([])
  const [scenario, setScenario] = useState<WhatIfRequest>(defaultScenario)
  const [whatIf, setWhatIf] = useState<WhatIfResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchSummary()
  }, [])

  async function fetchSummary() {
    try {
      const response = await fetch('http://localhost:8081/market-summary')
      const data = await response.json()
      if (!response.ok) throw new Error(data.detail || 'Unable to load summary')
      setSummary(data)
    } catch (err: any) {
      setError(err.message)
    }
  }

  async function fetchSegments(event: FormEvent) {
    event.preventDefault()
    try {
      const params = new URLSearchParams()
      if (filters.min_price > 0) params.append('min_price', String(filters.min_price))
      if (filters.max_price > 0) params.append('max_price', String(filters.max_price))
      if (filters.bedrooms > 0) params.append('bedrooms', String(filters.bedrooms))
      const response = await fetch(`http://localhost:8081/filter?${params}`)
      const data = await response.json()
      if (!response.ok) throw new Error(data.detail || 'Unable to load segments')
      setSegments(data)
    } catch (err: any) {
      setError(err.message)
    }
  }

  async function runWhatIf(event: FormEvent) {
    event.preventDefault()
    try {
      const response = await fetch('http://localhost:8081/what-if', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(scenario),
      })
      const data = await response.json()
      if (!response.ok) throw new Error(data.detail || 'What-if request failed')
      setWhatIf(data)
    } catch (err: any) {
      setError(err.message)
    }
  }

  return (
    <main>
      <NavBar />

      <section className="rounded-3xl border border-slate-800 bg-slate-900/80 p-8 shadow-card">
        <h1 className="text-3xl font-semibold text-white">App2: Market Analysis</h1>
        <p className="mt-3 text-slate-300">Analyze market segments and run what-if predictions from the housing dataset.</p>

        {error && <p className="mt-4 rounded-2xl bg-rose-900/80 px-4 py-3 text-sm text-rose-200">{error}</p>}

        <div className="mt-8 grid gap-6 lg:grid-cols-[1.4fr_1fr]">
          <div className="space-y-6 rounded-3xl border border-slate-800 bg-slate-950/90 p-6">
            <h2 className="text-xl font-semibold text-white">Market Summary</h2>
            {summary ? (
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="rounded-2xl border border-slate-800 bg-slate-900 p-4">
                  <p className="text-sm text-slate-400">Total listings</p>
                  <p className="mt-2 text-2xl font-semibold text-white">{summary.total_properties}</p>
                </div>
                <div className="rounded-2xl border border-slate-800 bg-slate-900 p-4">
                  <p className="text-sm text-slate-400">Average price</p>
                  <p className="mt-2 text-2xl font-semibold text-sky-300">${summary.average_price.toFixed(0)}</p>
                </div>
                <div className="rounded-2xl border border-slate-800 bg-slate-900 p-4">
                  <p className="text-sm text-slate-400">Median price</p>
                  <p className="mt-2 text-2xl font-semibold text-white">${summary.median_price.toFixed(0)}</p>
                </div>
                <div className="rounded-2xl border border-slate-800 bg-slate-900 p-4">
                  <p className="text-sm text-slate-400">Average sqft</p>
                  <p className="mt-2 text-2xl font-semibold text-white">{summary.average_square_footage.toFixed(0)}</p>
                </div>
              </div>
            ) : (
              <p className="text-slate-400">Loading summary...</p>
            )}
          </div>

          <div className="rounded-3xl border border-slate-800 bg-slate-950/90 p-6">
            <h2 className="text-xl font-semibold text-white">What-if Scenario</h2>
            <form className="mt-5 space-y-4" onSubmit={runWhatIf}>
              {Object.entries(scenario).map(([key, value]) => (
                <label key={key} className="grid gap-2 text-sm text-slate-200">
                  <span className="capitalize">{key.replace(/_/g, ' ')}</span>
                  <input
                    type="number"
                    value={value}
                    onChange={(e) =>
                      setScenario((current) => ({
                        ...current,
                        [key]: Number(e.target.value),
                      }))
                    }
                    className="rounded-2xl border border-slate-700 bg-slate-900 px-4 py-3 text-slate-100 outline-none transition focus:border-sky-500"
                  />
                </label>
              ))}
              <button className="mt-2 rounded-2xl bg-sky-500 px-5 py-3 font-semibold text-slate-950 transition hover:bg-sky-400">
                Run what-if analysis
              </button>
            </form>
            {whatIf && (
              <div className="mt-6 rounded-3xl border border-slate-800 bg-slate-900 p-4">
                <p className="text-sm text-slate-400">Predicted price</p>
                <p className="mt-2 text-3xl font-semibold text-sky-300">${whatIf.predicted_price.toFixed(0)}</p>
              </div>
            )}
          </div>
        </div>

        <section className="mt-8 rounded-3xl border border-slate-800 bg-slate-950/90 p-6">
          <h2 className="text-xl font-semibold text-white">Filter & Explore</h2>
          <form className="mt-5 grid gap-4 sm:grid-cols-3" onSubmit={fetchSegments}>
            <label className="space-y-2 text-sm text-slate-200">
              <span>Min price</span>
              <input
                type="number"
                value={filters.min_price}
                onChange={(e) => setFilters((current) => ({ ...current, min_price: Number(e.target.value) }))}
                className="w-full rounded-2xl border border-slate-700 bg-slate-900 px-4 py-3 text-slate-100 outline-none transition focus:border-sky-500"
              />
            </label>
            <label className="space-y-2 text-sm text-slate-200">
              <span>Max price</span>
              <input
                type="number"
                value={filters.max_price}
                onChange={(e) => setFilters((current) => ({ ...current, max_price: Number(e.target.value) }))}
                className="w-full rounded-2xl border border-slate-700 bg-slate-900 px-4 py-3 text-slate-100 outline-none transition focus:border-sky-500"
              />
            </label>
            <label className="space-y-2 text-sm text-slate-200">
              <span>Bedrooms</span>
              <input
                type="number"
                value={filters.bedrooms}
                onChange={(e) => setFilters((current) => ({ ...current, bedrooms: Number(e.target.value) }))}
                className="w-full rounded-2xl border border-slate-700 bg-slate-900 px-4 py-3 text-slate-100 outline-none transition focus:border-sky-500"
              />
            </label>
            <button className="sm:col-span-3 rounded-2xl bg-slate-800 px-5 py-3 font-semibold text-slate-100 transition hover:bg-slate-700">
              Apply filters
            </button>
          </form>

          {segments.length > 0 && (
            <div className="mt-6 overflow-x-auto">
              <table className="min-w-full text-left text-sm text-slate-200">
                <thead className="border-b border-slate-700 text-slate-300">
                  <tr>
                    <th className="px-3 py-2">Segment</th>
                    <th className="px-3 py-2">Count</th>
                    <th className="px-3 py-2">Avg price</th>
                    <th className="px-3 py-2">Avg sqft</th>
                    <th className="px-3 py-2">Avg school</th>
                  </tr>
                </thead>
                <tbody>
                  {segments.map((segment) => (
                    <tr key={segment.segment} className="border-b border-slate-800">
                      <td className="px-3 py-2">{segment.segment}</td>
                      <td className="px-3 py-2">{segment.count}</td>
                      <td className="px-3 py-2">${segment.average_price.toFixed(0)}</td>
                      <td className="px-3 py-2">{segment.average_square_footage.toFixed(0)}</td>
                      <td className="px-3 py-2">{segment.average_school_rating.toFixed(1)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      </section>
    </main>
  )
}
