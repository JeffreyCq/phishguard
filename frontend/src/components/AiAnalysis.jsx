import { Brain, AlertTriangle, CheckCircle, HelpCircle, ShieldAlert } from 'lucide-react'

const VERDICT_CONFIG = {
  PHISHING:    { icon: ShieldAlert,   cls: 'text-red-400',    bg: 'bg-red-500/10',    border: 'border-red-500/30' },
  SUSPICIOUS:  { icon: AlertTriangle, cls: 'text-orange-400', bg: 'bg-orange-500/10', border: 'border-orange-500/30' },
  LIKELY_SAFE: { icon: CheckCircle,   cls: 'text-yellow-400', bg: 'bg-yellow-500/10', border: 'border-yellow-500/20' },
  SAFE:        { icon: CheckCircle,   cls: 'text-green-400',  bg: 'bg-green-500/10',  border: 'border-green-500/20' },
  UNKNOWN:     { icon: HelpCircle,    cls: 'text-slate-400',  bg: 'bg-slate-800',     border: 'border-slate-700' },
}

export default function AiAnalysis({ ai }) {
  if (!ai) return null

  if (ai.status === 'not_configured') {
    return (
      <div className="p-4 rounded-lg bg-slate-900 border border-slate-700 text-slate-500 text-sm flex items-center gap-2">
        <Brain className="w-4 h-4" />
        AI analysis not configured. Add your <code className="text-indigo-400">ANTHROPIC_API_KEY</code> to enable it.
      </div>
    )
  }

  if (ai.status === 'error') {
    return (
      <div className="p-4 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400 text-sm">
        AI analysis error: {ai.error}
      </div>
    )
  }

  const cfg = VERDICT_CONFIG[ai.verdict] || VERDICT_CONFIG.UNKNOWN
  const Icon = cfg.icon

  return (
    <div className="space-y-4">
      {/* Verdict banner */}
      <div className={`flex items-center gap-3 p-4 rounded-xl border ${cfg.bg} ${cfg.border}`}>
        <Icon className={`w-6 h-6 shrink-0 ${cfg.cls}`} />
        <div className="flex-1">
          <div className="flex items-center gap-3">
            <span className={`text-lg font-bold ${cfg.cls}`}>{ai.verdict}</span>
            <span className="text-slate-500 text-sm">{ai.confidence}% confidence</span>
          </div>
          <p className="text-slate-300 text-sm mt-1">{ai.reasoning}</p>
        </div>
      </div>

      {/* Confidence bar */}
      <div>
        <div className="flex justify-between text-xs text-slate-500 mb-1">
          <span>Confidence</span>
          <span>{ai.confidence}%</span>
        </div>
        <div className="h-2 rounded-full bg-slate-800">
          <div
            className={`h-2 rounded-full transition-all ${cfg.cls.replace('text-', 'bg-')}`}
            style={{ width: `${ai.confidence}%` }}
          />
        </div>
      </div>

      {/* Tactics */}
      {ai.tactics?.length > 0 && (
        <div>
          <p className="text-xs text-slate-500 uppercase tracking-wide mb-2">Tactics Detected</p>
          <div className="flex flex-wrap gap-2">
            {ai.tactics.map((t, i) => (
              <span key={i} className="px-2.5 py-1 rounded-full bg-slate-800 border border-slate-700 text-xs text-slate-300">
                {t.replace(/_/g, ' ')}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Red flags */}
      {ai.red_flags?.length > 0 && (
        <div>
          <p className="text-xs text-slate-500 uppercase tracking-wide mb-2">Red Flags</p>
          <ul className="space-y-1">
            {ai.red_flags.map((flag, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-slate-300">
                <AlertTriangle className="w-3.5 h-3.5 text-orange-400 shrink-0 mt-0.5" />
                {flag}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Recommendation */}
      {ai.recommendation && (
        <div className="p-3 rounded-lg bg-slate-900 border border-slate-800">
          <p className="text-xs text-slate-500 uppercase tracking-wide mb-1">Recommendation</p>
          <p className="text-slate-300 text-sm">{ai.recommendation}</p>
        </div>
      )}
    </div>
  )
}
