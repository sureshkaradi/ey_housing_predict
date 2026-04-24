import Link from 'next/link'
import NavBar from '../components/NavBar'

export default function HomePage() {
  return (
    <main>
      <NavBar />
      <section className="rounded-3xl border border-slate-800 bg-slate-900/80 p-8 shadow-card">
        <h1 className="text-3xl font-semibold text-white">Unified Housing Portal</h1>
        <p className="mt-4 max-w-2xl text-slate-300">
          Explore two independent applications built with Python backends and routed through a shared Next.js portal.
          App1 is the property value estimator, and App2 is the market analysis dashboard.
        </p>
        <div className="mt-8 grid gap-4 sm:grid-cols-2">
          <Link href="/app1" className="rounded-2xl border border-slate-700 bg-slate-800 px-6 py-5 text-left transition hover:bg-slate-700">
            <h2 className="text-xl font-semibold text-white">App1: Property Estimator</h2>
            <p className="mt-2 text-slate-400">Enter property details, get predictions, and view estimate history.</p>
          </Link>
          <Link href="/app2" className="rounded-2xl border border-slate-700 bg-slate-800 px-6 py-5 text-left transition hover:bg-slate-700">
            <h2 className="text-xl font-semibold text-white">App2: Market Analysis</h2>
            <p className="mt-2 text-slate-400">Inspect market summary, filter listings, and run what-if analysis.</p>
          </Link>
        </div>
      </section>
    </main>
  )
}
