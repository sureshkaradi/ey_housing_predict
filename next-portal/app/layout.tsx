import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Housing Portal',
  description: 'Unified portal for property estimator and market analysis',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-slate-950 text-slate-100">
        <div className="mx-auto max-w-7xl px-4 py-6">
          {children}
        </div>
      </body>
    </html>
  )
}
