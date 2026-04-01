import { ExternalLink, AlertTriangle, CheckCircle, MinusCircle } from 'lucide-react'

function VTBadge({ vt }) {
  if (!vt || vt.status === 'not_configured') {
    return <span className="text-xs text-slate-600 italic">VT: no key</span>
  }
  if (vt.status === 'not_checked') {
    return <span className="text-xs text-slate-600">VT: skipped</span>
  }
  if (vt.status === 'error') {
    return <span className="text-xs text-slate-600">VT: error</span>
  }
  if (vt.status === 'submitted') {
    return <span className="text-xs text-blue-400">VT: submitted</span>
  }
  if (vt.flagged) {
    return (
      <span className="inline-flex items-center gap-1 text-xs text-red-400">
        <AlertTriangle className="w-3 h-3" />
        {vt.malicious} malicious / {vt.total} engines
      </span>
    )
  }
  return (
    <span className="inline-flex items-center gap-1 text-xs text-green-400">
      <CheckCircle className="w-3 h-3" />
      Clean ({vt.total} engines)
    </span>
  )
}

export default function UrlResults({ urls }) {
  if (!urls?.length) {
    return <p className="text-slate-500 text-sm p-4">No URLs detected in this email.</p>
  }

  return (
    <div className="space-y-2">
      {urls.map((entry, i) => {
        const isFlagged = entry.virustotal?.flagged
        return (
          <div
            key={i}
            className={`p-3 rounded-lg border text-sm transition-colors ${
              isFlagged
                ? 'bg-red-500/10 border-red-500/30'
                : 'bg-slate-900 border-slate-800'
            }`}
          >
            <div className="flex items-start gap-2">
              {isFlagged
                ? <AlertTriangle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
                : <MinusCircle className="w-4 h-4 text-slate-600 shrink-0 mt-0.5" />
              }
              <div className="flex-1 min-w-0">
                <a
                  href={entry.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-indigo-400 hover:text-indigo-300 break-all text-xs font-mono flex items-center gap-1"
                  onClick={(e) => e.stopPropagation()}
                >
                  {entry.url.length > 80 ? entry.url.slice(0, 80) + '…' : entry.url}
                  <ExternalLink className="w-3 h-3 shrink-0" />
                </a>
                <div className="mt-1">
                  <VTBadge vt={entry.virustotal} />
                </div>
              </div>
            </div>
          </div>
        )
      })}
    </div>
  )
}
