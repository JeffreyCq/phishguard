export default function ScoreBreakdown({ breakdown }) {
  if (!breakdown?.length) return null

  return (
    <div className="space-y-2">
      {breakdown.map((item, i) => (
        <div key={i} className="flex items-center gap-3">
          <span className="text-slate-400 text-xs flex-1">{item.label}</span>
          <span className={`text-xs font-mono font-bold w-12 text-right ${item.points > 0 ? 'text-red-400' : 'text-green-400'}`}>
            {item.points > 0 ? `+${item.points}` : item.points}
          </span>
          <div className="w-24 h-1.5 rounded-full bg-slate-800">
            <div
              className={`h-1.5 rounded-full ${item.points > 0 ? 'bg-red-500' : 'bg-green-500'}`}
              style={{ width: `${Math.min(100, Math.abs(item.points) * 2.5)}%` }}
            />
          </div>
        </div>
      ))}
    </div>
  )
}
