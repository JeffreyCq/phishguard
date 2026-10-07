import { CheckCircle, XCircle, MinusCircle } from 'lucide-react'

function AuthBadge({ value }) {
  if (!value || value === 'none') return <span className="inline-flex items-center gap-1 text-slate-500 text-xs"><MinusCircle className="w-3 h-3" />none</span>
  if (value === 'pass') return <span className="inline-flex items-center gap-1 text-green-400 text-xs"><CheckCircle className="w-3 h-3" />pass</span>
  return <span className="inline-flex items-center gap-1 text-red-400 text-xs"><XCircle className="w-3 h-3" />{value}</span>
}

function Row({ label, value, highlight }) {
  if (!value) return null
  return (
    <tr className={`border-b border-white/10 ${highlight ? 'bg-red-500/5' : ''}`}>
      <td className="py-2.5 pr-4 text-slate-500 text-xs font-medium whitespace-nowrap w-36">{label}</td>
      <td className="py-2.5 text-slate-300 text-sm break-all">{value}</td>
    </tr>
  )
}

export default function HeaderAnalysis({ headers }) {
  if (!headers) return null

  return (
    <div className="space-y-5">
      {/* Auth results */}
      <div className="grid grid-cols-3 gap-3">
        {[
          { label: 'SPF', value: headers.spf },
          { label: 'DKIM', value: headers.dkim },
          { label: 'DMARC', value: headers.dmarc },
        ].map(({ label, value }) => (
          <div key={label} className="bg-black/40 rounded-lg border border-white/10 p-3 text-center">
            <p className="text-slate-500 text-xs mb-1">{label}</p>
            <AuthBadge value={value} />
          </div>
        ))}
      </div>

      {/* Mismatch warning */}
      {headers.from_reply_to_mismatch && (
        <div className="flex items-center gap-2 p-3 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400 text-sm">
          <XCircle className="w-4 h-4 shrink-0" />
          From/Reply-To domain mismatch: <span className="font-mono text-xs ml-1">{headers.from_domain}</span> vs <span className="font-mono text-xs ml-1">{headers.reply_to_domain}</span>
        </div>
      )}

      {/* Raw header table */}
      <div className="overflow-x-auto">
        <table className="w-full text-left">
          <tbody>
            <Row label="From" value={headers.from} />
            <Row label="Reply-To" value={headers.reply_to} highlight={headers.from_reply_to_mismatch} />
            <Row label="To" value={headers.to} />
            <Row label="Subject" value={headers.subject} />
            <Row label="Date" value={headers.date} />
            <Row label="Message-ID" value={headers.message_id} />
            <Row label="X-Mailer" value={headers.x_mailer} />
            <Row label="Originating IP" value={headers.x_originating_ip} />
            <Row label="Received hops" value={headers.received_count ? `${headers.received_count} hops` : null} />
          </tbody>
        </table>
      </div>
    </div>
  )
}
