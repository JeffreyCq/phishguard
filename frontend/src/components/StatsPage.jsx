import { useState, useEffect, useCallback } from 'react'
import { Lock, RefreshCw } from 'lucide-react'

const VERDICT_BADGE = {
  PHISHING:    'text-red-400 bg-red-500/10 border-red-500/30',
  SUSPICIOUS:  'text-orange-400 bg-orange-500/10 border-orange-500/30',
  SAFE:        'text-green-400 bg-green-500/10 border-green-500/30',
  LIKELY_SAFE: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30',
  UNKNOWN:     'text-slate-400 bg-slate-500/10 border-slate-500/30',
}

const VERDICT_BAR = {
  PHISHING:    'bg-red-500',
  SUSPICIOUS:  'bg-orange-500',
  SAFE:        'bg-green-500',
  LIKELY_SAFE: 'bg-emerald-500',
  UNKNOWN:     'bg-slate-500',
}

const SOURCE_BAR = {
  paste:   'bg-indigo-500',
  file:    'bg-teal-500',
  api:     'bg-violet-500',
  unknown: 'bg-slate-500',
}

const SOURCE_TEXT = {
  paste:   'text-indigo-400',
  file:    'text-teal-400',
  api:     'text-violet-400',
  unknown: 'text-slate-400',
}

function StatCard({ label, value, color = 'text-white' }) {
  return (
    <div className="card p-6">
      <p className="label mb-1">{label}</p>
      <p className={`font-mono text-4xl font-medium ${color}`}>{value}</p>
    </div>
  )
}

function DistBar({ label, count, total, colorClass }) {
  const pct = total > 0 ? Math.round((count / total) * 100) : 0
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-xs">
        <span className="text-slate-400">{label}</span>
        <span className="text-slate-500">{count} ({pct}%)</span>
      </div>
      <div className="w-full h-2 bg-slate-800 rounded-full overflow-hidden">
        <div className={`h-full rounded-full ${colorClass}`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  )
}

function DailyChart({ data }) {
  if (!data.length) return (
    <p className="text-slate-500 text-sm text-center py-8">No data in last 30 days</p>
  )
  const max = Math.max(...data.map(d => d.count), 1)
  return (
    <div className="flex items-end gap-0.5 h-28">
      {data.map((d, i) => (
        <div
          key={i}
          className="flex-1 bg-btc/50 hover:bg-btc rounded-sm transition-colors cursor-default"
          style={{ height: `${Math.max((d.count / max) * 112, 3)}px` }}
          title={`${d.date}: ${d.count}`}
        />
      ))}
    </div>
  )
}

export default function StatsPage() {
  const [secret, setSecret] = useState(() => sessionStorage.getItem('md_admin') || '')
  const [input,  setInput]  = useState('')
  const [stats,  setStats]  = useState(null)
  const [error,  setError]  = useState(null)
  const [loading, setLoading] = useState(false)

  const fetchStats = useCallback(async (s) => {
    setLoading(true)
    setError(null)
    try {
      const res = await fetch('/admin/stats', { headers: { 'X-Admin-Secret': s } })
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: 'Auth failed' }))
        throw new Error(err.detail || `HTTP ${res.status}`)
      }
      setStats(await res.json())
      setSecret(s)
      sessionStorage.setItem('md_admin', s)
    } catch (e) {
      setError(e.message)
      setSecret('')
      sessionStorage.removeItem('md_admin')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    if (secret) fetchStats(secret)
  }, [])

  if (!secret || (!stats && !loading)) {
    return (
      <div className="max-w-sm mx-auto mt-20">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-xl bg-burnt/20 border border-burnt/50 shadow-glow mb-4">
            <Lock className="w-7 h-7 text-btc" />
          </div>
          <h2 className="text-2xl font-bold text-white">Analytics</h2>
          <p className="text-slate-400 text-sm mt-1">Enter your admin secret</p>
        </div>
        <div className="space-y-3">
          <input
            type="password"
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && input && fetchStats(input)}
            placeholder="Admin secret..."
            className="field h-12 rounded-t-lg"
          />
          <button
            onClick={() => fetchStats(input)}
            disabled={!input || loading}
            className="btn-primary w-full"
          >
            {loading ? 'Authenticating...' : 'View Stats'}
          </button>
          {error && <p className="text-red-400 text-sm text-center">{error}</p>}
        </div>
      </div>
    )
  }

  if (loading && !stats) {
    return (
      <div className="flex justify-center items-center py-32">
        <RefreshCw className="w-6 h-6 text-indigo-400 animate-spin" />
      </div>
    )
  }

  const totalBySource  = stats.by_source.reduce((a, b) => a + b.count, 0)
  const totalByVerdict = stats.by_verdict.reduce((a, b) => a + b.count, 0)

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white">Analytics</h2>
          <p className="text-slate-500 text-sm">Scan usage statistics</p>
        </div>
        <button
          onClick={() => fetchStats(secret)}
          disabled={loading}
          className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-slate-200 transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <StatCard label="Total Scans"  value={stats.total_scans} />
        <StatCard label="Last 7 Days"  value={stats.last_7_days}  color="text-indigo-400" />
        <StatCard label="Last 30 Days" value={stats.last_30_days} color="text-teal-400" />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="card p-6 space-y-3">
          <p className="label">Scan Source</p>
          {stats.by_source.length
            ? stats.by_source.map(({ source, count }) => (
                <DistBar key={source} label={source} count={count} total={totalBySource}
                  colorClass={SOURCE_BAR[source] || 'bg-slate-500'} />
              ))
            : <p className="text-slate-500 text-sm">No data yet</p>
          }
        </div>
        <div className="card p-6 space-y-3">
          <p className="label">Verdict Distribution</p>
          {stats.by_verdict.length
            ? stats.by_verdict.map(({ verdict, count }) => (
                <DistBar key={verdict} label={verdict} count={count} total={totalByVerdict}
                  colorClass={VERDICT_BAR[verdict] || 'bg-slate-500'} />
              ))
            : <p className="text-slate-500 text-sm">No data yet</p>
          }
        </div>
      </div>

      <div className="card p-6">
        <p className="label mb-4">Daily Scans — Last 30 Days</p>
        <DailyChart data={stats.daily_counts} />
      </div>

      <div className="card p-6">
        <p className="label mb-4">Recent Scans</p>
        <div className="space-y-0">
          {stats.recent_scans.length
            ? stats.recent_scans.map((scan) => (
                <div key={scan.scan_id}
                  className="flex items-center justify-between py-2.5 border-b border-slate-800/60 last:border-0">
                  <div className="flex items-center gap-3">
                    <span className={`px-2 py-0.5 rounded text-xs font-medium border ${VERDICT_BADGE[scan.verdict] || VERDICT_BADGE.UNKNOWN}`}>
                      {scan.verdict}
                    </span>
                    <span className={`text-xs ${SOURCE_TEXT[scan.source] || 'text-slate-400'}`}>
                      {scan.source}
                    </span>
                  </div>
                  <div className="flex items-center gap-4 text-xs text-slate-500">
                    <span>Score: {scan.risk_score ?? '—'}</span>
                    <span className="font-mono">{scan.created_at?.substring(0, 16).replace('T', ' ')}</span>
                  </div>
                </div>
              ))
            : <p className="text-slate-500 text-sm">No scans yet</p>
          }
        </div>
      </div>
    </div>
  )
}
