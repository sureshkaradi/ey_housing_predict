"use client"

import { FormEvent, useEffect, useState } from 'react'
import NavBar from '../../components/NavBar'

type PropertyFeatures = {
  square_footage: number
  bedrooms: number
  bathrooms: number
  year_built: number
  lot_size: number
  distance_to_city_center: number
  school_rating: number
}

type Estimate = {
  estimate_id: number
  session_id: string
  features: PropertyFeatures
  predicted_price: number
  created_at: string
  notes?: string
}

const emptyFeatures: PropertyFeatures = {
  square_footage: 2000,
  bedrooms: 3,
  bathrooms: 2,
  year_built: 2015,
  lot_size: 6000,
  distance_to_city_center: 5,
  school_rating: 7,
}

export default function App1Page() {
  const [features, setFeatures] = useState<PropertyFeatures>(emptyFeatures)
  const [notes, setNotes] = useState('')
  const [sessionId, setSessionId] = useState<string>('')
  const [estimate, setEstimate] = useState<Estimate | null>(null)
  const [history, setHistory] = useState<Estimate[]>([])
  const [error, setError] = useState<string | null>(null)
  const [compareIds, setCompareIds] = useState<number[]>([])

  useEffect(() => {
    if (sessionId) {
      fetchHistory(sessionId)
    }
  }, [sessionId])

  async function fetchHistory(sessionId: string) {
    try {
      const response = await fetch(`http://localhost:8080/history?session_id=${sessionId}`)
      const data = await response.json()
      if (!response.ok) throw new Error(data.detail || 'Failed to load history')
      setHistory(data.estimates)
    } catch (err: any) {
      setError(err.message)
    }
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault()
    setError(null)
    try {
      const response = await fetch('http://localhost:8080/estimate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ property: features, notes, session_id: sessionId || undefined }),
      })
      const data = await response.json()
      if (!response.ok) throw new Error(data.detail || 'Estimation failed')
      setEstimate(data)
      if (data.session_id) setSessionId(data.session_id)
      fetchHistory(data.session_id)
    } catch (err: any) {
      setError(err.message)
    }
  }

  function toggleCompareId(id: number) {
    setCompareIds((current: number[]) =>
      current.includes(id) ? current.filter((item) => item !== id) : [...current, id].slice(-3)
    )
  }

  const selectedEstimates = history.filter((item) => compareIds.includes(item.estimate_id))

  return (
    <main>
      <NavBar />

      <section className="rounded-3xl border border-slate-800 bg-slate-900/80 p-8 shadow-card">
        <h1 className="text-3xl font-semibold text-white">App1: Property Value Estimator</h1>
        <p className="mt-3 text-slate-300">Enter property details and get a price estimate from the Python ML backend.</p>

        <form className="mt-8 grid gap-4 sm:grid-cols-2" onSubmit={onSubmit}>
          {Object.entries(features).map(([key, value]) => (
            <label key={key} className="space-y-2 text-sm text-slate-200">
              <span className="font-medium capitalize">{key.replace(/_/g, ' ')}</span>
              <input
                type={key === 'year_built' ? 'number' : 'text'}
                value={value}
                onChange={(e) =>
                  setFeatures((current) => ({
                    ...current,
                    [key]: Number((e.target as HTMLInputElement).value),
                  }))
                }
                className="w-full rounded-2xl border border-slate-700 bg-slate-950 px-4 py-3 text-slate-100 outline-none transition focus:border-sky-500"
              />
            </label>
          ))}

          <label className="space-y-2 text-sm text-slate-200">
            <span className="font-medium">Notes</span>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              className="w-full rounded-2xl border border-slate-700 bg-slate-950 px-4 py-3 text-slate-100 outline-none transition focus:border-sky-500"
              rows={4}
            />
          </label>

          <div className="sm:col-span-2">
            <button type="submit" className="rounded-2xl bg-sky-500 px-5 py-3 font-semibold text-slate-950 transition hover:bg-sky-400">
              Estimate Price
            </button>
            {error && <p className="mt-3 text-sm text-rose-400">{error}</p>}
          </div>
        </form>

        {estimate && (
          <div className="mt-10 rounded-3xl border border-slate-800 bg-slate-950/90 p-6">
            <h2 className="text-2xl font-semibold text-white">Prediction Result</h2>
            <p className="mt-2 text-slate-300">Estimated price: <span className="font-semibold text-sky-300">${estimate.predicted_price.toFixed(2)}</span></p>
            <div className="mt-5 grid gap-3 sm:grid-cols-2">
              {Object.entries(estimate.features).map(([key, value]) => (
                <div key={key} className="rounded-2xl border border-slate-800 bg-slate-900 p-4 text-slate-200">
                  <span className="block text-sm text-slate-400">{key.replace(/_/g, ' ')}</span>
                  <span className="mt-1 block text-lg font-semibold">{value}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {history.length > 0 && (
          <div className="mt-10 rounded-3xl border border-slate-800 bg-slate-900/90 p-6">
            <div className="flex items-center justify-between gap-4">
              <h2 className="text-2xl font-semibold text-white">Estimate History</h2>
              <span className="rounded-full bg-slate-800 px-3 py-1 text-sm text-slate-300">{history.length} items</span>
            </div>
            <div className="mt-5 overflow-x-auto">
              <table className="min-w-full text-left text-sm text-slate-200">
                <thead>
                  <tr className="border-b border-slate-700 text-slate-300">
                    <th className="px-3 py-2">ID</th>
                    <th className="px-3 py-2">Price</th>
                    <th className="px-3 py-2">Bedrooms</th>
                    <th className="px-3 py-2">School</th>
                    <th className="px-3 py-2">Created</th>
                    <th className="px-3 py-2">Compare</th>
                  </tr>
                </thead>
                <tbody>
                  {history.map((item) => (
                    <tr key={item.estimate_id} className="border-b border-slate-800">
                      <td className="px-3 py-2">{item.estimate_id}</td>
                      <td className="px-3 py-2 text-sky-300">${item.predicted_price.toFixed(0)}</td>
                      <td className="px-3 py-2">{item.features.bedrooms}</td>
                      <td className="px-3 py-2">{item.features.school_rating}</td>
                      <td className="px-3 py-2">{new Date(item.created_at).toLocaleDateString()}</td>
                      <td className="px-3 py-2">
                        <button
                          type="button"
                          onClick={() => toggleCompareId(item.estimate_id)}
                          className={`rounded-full px-3 py-1 text-sm ${compareIds.includes(item.estimate_id) ? 'bg-sky-500 text-slate-950' : 'bg-slate-800 text-slate-300'}`}
                        >
                          {compareIds.includes(item.estimate_id) ? 'Selected' : 'Select'}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {selectedEstimates.length >= 2 && (
          <div className="mt-10 rounded-3xl border border-slate-800 bg-slate-950/90 p-6">
            <h2 className="text-2xl font-semibold text-white">Comparison View</h2>
            <div className="mt-5 grid gap-4 sm:grid-cols-2">
              {selectedEstimates.map((item) => (
                <div key={item.estimate_id} className="rounded-3xl border border-slate-800 bg-slate-900 p-4">
                  <p className="text-sm text-slate-400">Estimate #{item.estimate_id}</p>
                  <p className="mt-2 text-xl font-semibold text-white">${item.predicted_price.toFixed(0)}</p>
                  <div className="mt-4 space-y-2 text-slate-300">
                    <p>Square footage: {item.features.square_footage}</p>
                    <p>Bathrooms: {item.features.bathrooms}</p>
                    <p>Year built: {item.features.year_built}</p>
                    <p>Price per sqft: ${(item.predicted_price / item.features.square_footage).toFixed(1)}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </section>
    </main>
  )
}
