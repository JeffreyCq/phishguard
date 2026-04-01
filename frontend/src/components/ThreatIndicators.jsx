import { AlertTriangle, AlertCircle, Info, CheckCircle } from 'lucide-react'

const SEV = {
  high:   { icon: AlertTriangle, cls: 'text-red-400',    bg: 'bg-red-500/10',    border: 'border-red-500/20' },
  medium: { icon: AlertCircle,   cls: 'text-yellow-400', bg: 'bg-yellow-500/10', border: 'border-yellow-500/20' },
  low:    { icon: Info,          cls: 'text-blue-400',   bg: 'bg-blue-500/10',   border: 'border-blue-500/20' },
  info:   { icon: Info,          cls: 'text-slate-400',  bg: 'bg-slate-800',     border: 'border-slate-700' },
}

export default function ThreatIndicators({ indicators }) {
  if (!indicators?.length) {
    return (
      <div className="flex items-center gap-2 text-green-400 text-sm p-4">
        <CheckCircle className="w-4 h-4" />
        No structural threat indicators detected.
      </div>
    )
  }

  // Sort by severity
  const order = ['high', 'medium', 'low', 'info']
  const sorted = [...indicators].sort(
    (a, b) => order.indexOf(a.severity) - order.indexOf(b.severity)
  )

  return (
    <div className="space-y-2">
      {sorted.map((ind, i) => {
        const s = SEV[ind.severity] || SEV.info
        const Icon = s.icon
        return (
          <div key={i} className={`flex items-start gap-3 p-3 rounded-lg border ${s.bg} ${s.border}`}>
            <Icon className={`w-4 h-4 mt-0.5 shrink-0 ${s.cls}`} />
            <div>
              <span className={`text-xs font-semibold uppercase tracking-wide ${s.cls}`}>
                {ind.severity}
              </span>
              <span className="text-slate-500 text-xs"> · {ind.type}</span>
              <p className="text-slate-300 text-sm mt-0.5">{ind.message}</p>
            </div>
          </div>
        )
      })}
    </div>
  )
}
