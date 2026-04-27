import { Brain, AlertTriangle, CheckCircle, HelpCircle, ShieldAlert, Mail, MailX } from 'lucide-react'

// ── Phishing config ──────────────────────────────────────────────────────────
const VERDICT_CONFIG = {
  PHISHING:    { icon: ShieldAlert,   cls: 'text-red-400',    bg: 'bg-red-500/10',    border: 'border-red-500/30' },
  SUSPICIOUS:  { icon: AlertTriangle, cls: 'text-orange-400', bg: 'bg-orange-500/10', border: 'border-orange-500/30' },
  LIKELY_SAFE: { icon: CheckCircle,   cls: 'text-yellow-400', bg: 'bg-yellow-500/10', border: 'border-yellow-500/20' },
  SAFE:        { icon: CheckCircle,   cls: 'text-green-400',  bg: 'bg-green-500/10',  border: 'border-green-500/20' },
  UNKNOWN:     { icon: HelpCircle,    cls: 'text-slate-400',  bg: 'bg-slate-800',     border: 'border-slate-700' },
}

// ── Spam config ───────────────────────────────────────────────────────────────
const SPAM_CONFIG = {
  SPAM:        { icon: MailX,    cls: 'text-amber-400',  bg: 'bg-amber-500/10',  border: 'border-amber-500/30',  label: 'SPAM' },
  LIKELY_SPAM: { icon: Mail,     cls: 'text-yellow-400', bg: 'bg-yellow-500/10', border: 'border-yellow-500/20', label: 'LIKELY SPAM' },
  NOT_SPAM:    { icon: Mail,     cls: 'text-green-400',  bg: 'bg-green-500/10',  border: 'border-green-500/20',  label: 'NOT SPAM' },
  UNKNOWN:     { icon: HelpCircle, cls: 'text-slate-400', bg: 'bg-slate-800',    border: 'border-slate-700',     label: 'UNKNOWN' },
}

export default function AiAnalysis({ ai }) {
  if (!ai) return null

  if (ai.status === 'not_configured') {
    return (
      <div className="p-4 rounded-lg bg-slate-900 border border-slate-700 text-slate-500 text-sm flex items-center gap-2">
        <Brain className="w-4 h-4" />
        AI analysis not configured.
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

  const pcfg = VERDICT_CONFIG[ai.verdict]  || VERDICT_CONFIG.UNKNOWN
  const scfg = SPAM_CONFIG[ai.spam_verdict] || SPAM_CONFIG.UNKNOWN
  const PIcon = pcfg.icon
  const SIcon = scfg.icon

  return (
    <div className="space-y-5">

      {/* ── Phishing verdict ── */}
      <div>
        <p className="text-xs text-slate-500 uppercase tracking-wide mb-2">Phishing Analysis</p>
        <div className={`flex items-center gap-3 p-4 rounded-xl border ${pcfg.bg} ${pcfg.border}`}>
          <PIcon className={`w-6 h-6 shrink-0 ${pcfg.cls}`} />
          <div className="flex-1">
            <div className="flex items-center gap-3 flex-wrap">
              <span className={`text-lg font-bold ${pcfg.cls}`}>{ai.verdict}</span>
              <span className="text-slate-500 text-sm">{ai.confidence}% confidence</span>
            </div>
            <p className="text-slate-300 text-sm mt-1">{ai.reasoning}</p>
          </div>
        </div>

        {/* Confidence bar */}
        <div className="mt-2">
          <div className="h-1.5 rounded-full bg-slate-800">
            <div
              className={`h-1.5 rounded-full transition-all ${pcfg.cls.replace('text-', 'bg-')}`}
              style={{ width: `${ai.confidence}%` }}
            />
          </div>
        </div>
      </div>

      {/* ── Spam verdict ── */}
      {ai.spam_verdict && ai.spam_verdict !== 'UNKNOWN' && (
        <div>
          <p className="text-xs text-slate-500 uppercase tracking-wide mb-2">Spam Analysis</p>
          <div className={`flex items-center gap-3 p-4 rounded-xl border ${scfg.bg} ${scfg.border}`}>
            <SIcon className={`w-5 h-5 shrink-0 ${scfg.cls}`} />
            <div className="flex-1">
              <div className="flex items-center gap-3 flex-wrap">
                <span className={`text-base font-bold ${scfg.cls}`}>{scfg.label}</span>
                <span className="text-slate-500 text-sm">{ai.spam_confidence}% confidence</span>
              </div>
              {ai.spam_signals?.length > 0 && (
                <div className="flex flex-wrap gap-1.5 mt-2">
                  {ai.spam_signals.map((s, i) => (
                    <span key={i} className="px-2 py-0.5 rounded-full bg-slate-900/60 border border-slate-700 text-xs text-slate-400">
                      {s.replace(/_/g, ' ')}
                    </span>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Spam confidence bar */}
          <div className="mt-2">
            <div className="h-1.5 rounded-full bg-slate-800">
              <div
                className={`h-1.5 rounded-full transition-all ${scfg.cls.replace('text-', 'bg-')}`}
                style={{ width: `${ai.spam_confidence}%` }}
              />
            </div>
          </div>
        </div>
      )}

      {/* ── Tactics ── */}
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

      {/* ── Red flags ── */}
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

      {/* ── Recommendation ── */}
      {ai.recommendation && (
        <div className="p-3 rounded-lg bg-slate-900 border border-slate-800">
          <p className="text-xs text-slate-500 uppercase tracking-wide mb-1">Recommendation</p>
          <p className="text-slate-300 text-sm">{ai.recommendation}</p>
        </div>
      )}

    </div>
  )
}
