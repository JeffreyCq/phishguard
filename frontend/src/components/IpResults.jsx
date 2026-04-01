import { AlertTriangle, CheckCircle, MinusCircle } from 'lucide-react'

function Badge({ label, value, flagged }) {
  if (!value || value === 'not_configured') {
    return <span className="text-xs text-slate-600 italic">{label}: no key</span>
  }
  if (flagged) {
    return <span className="inline-flex items-center gap-1 text-xs text-red-400"><AlertTriangle className="w-3 h-3" />{label}: flagged</span>
  }
  return <span className="inline-flex items-center gap-1 text-xs text-green-400"><CheckCircle className="w-3 h-3" />{label}: clean</span>
}

export default function IpResults({ ips }) {
  if (!ips?.length) {
    return <p className="text-slate-500 text-sm p-4">No public IPs extracted from headers.</p>
  }

  return (
    <div className="space-y-2">
      {ips.map((entry, i) => {
        const vtFlagged = entry.virustotal?.flagged
        const abuseFlagged = entry.abuseipdb?.flagged
        const anyFlagged = vtFlagged || abuseFlagged

        return (
          <div
            key={i}
            className={`p-3 rounded-lg border text-sm ${
              anyFlagged ? 'bg-red-500/10 border-red-500/30' : 'bg-slate-900 border-slate-800'
            }`}
          >
            <div className="flex items-center gap-2 mb-2">
              {anyFlagged
                ? <AlertTriangle className="w-4 h-4 text-red-400 shrink-0" />
                : <MinusCircle className="w-4 h-4 text-slate-600 shrink-0" />
              }
              <span className="font-mono text-slate-200 text-sm">{entry.ip}</span>
              {entry.virustotal?.country && (
                <span className="text-xs text-slate-500 ml-auto">{entry.virustotal.country}</span>
              )}
              {entry.abuseipdb?.country && !entry.virustotal?.country && (
                <span className="text-xs text-slate-500 ml-auto">{entry.abuseipdb.country}</span>
              )}
            </div>

            <div className="flex flex-wrap gap-3 text-xs text-slate-500 ml-6">
              {entry.virustotal?.as_owner && (
                <span>ASN: {entry.virustotal.as_owner}</span>
              )}
              {entry.abuseipdb?.isp && (
                <span>ISP: {entry.abuseipdb.isp}</span>
              )}
              {entry.abuseipdb?.abuse_score !== undefined && (
                <span className={entry.abuseipdb.abuse_score > 25 ? 'text-red-400' : ''}>
                  Abuse score: {entry.abuseipdb.abuse_score}%
                </span>
              )}
              {entry.abuseipdb?.total_reports > 0 && (
                <span>{entry.abuseipdb.total_reports} abuse reports</span>
              )}
            </div>

            <div className="flex gap-4 mt-2 ml-6">
              <Badge label="VT" value={entry.virustotal?.status} flagged={vtFlagged} />
              <Badge label="AbuseIPDB" value={entry.abuseipdb?.status} flagged={abuseFlagged} />
            </div>
          </div>
        )
      })}
    </div>
  )
}
