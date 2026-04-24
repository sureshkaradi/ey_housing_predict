import Link from 'next/link'

const links = [
  { href: '/', label: 'Home' },
  { href: '/app1', label: 'Property Estimator' },
  { href: '/app2', label: 'Market Analysis' },
]

export default function NavBar() {
  return (
    <nav className="mb-8 flex flex-wrap items-center justify-between gap-4 rounded-3xl border border-slate-800 bg-slate-900/80 px-5 py-4 shadow-card">
      <div>
        <p className="text-lg font-semibold text-slate-100">Housing Portal</p>
        <p className="text-sm text-slate-400">Unified interface for App1 and App2</p>
      </div>
      <div className="flex flex-wrap items-center gap-3">
        {links.map((link) => (
          <Link
            key={link.href}
            href={link.href}
            className="rounded-full border border-slate-700 px-4 py-2 text-sm font-medium text-slate-200 transition hover:bg-slate-800"
          >
            {link.label}
          </Link>
        ))}
      </div>
    </nav>
  )
}
