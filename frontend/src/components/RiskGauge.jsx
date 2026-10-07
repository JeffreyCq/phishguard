export default function RiskGauge({ score, level, color }) {
  const colorMap = {
    green:  { ring: '#22c55e', bg: 'bg-green-500/10',  border: 'border-green-500/30',  text: 'text-green-400',  label: 'text-green-300' },
    yellow: { ring: '#eab308', bg: 'bg-yellow-500/10', border: 'border-yellow-500/30', text: 'text-yellow-400', label: 'text-yellow-300' },
    orange: { ring: '#f97316', bg: 'bg-orange-500/10', border: 'border-orange-500/30', text: 'text-orange-400', label: 'text-orange-300' },
    red:    { ring: '#ef4444', bg: 'bg-red-500/10',    border: 'border-red-500/30',    text: 'text-red-400',   label: 'text-red-300' },
  }

  const c = colorMap[color] || colorMap.green

  // SVG arc
  const radius = 54
  const circumference = 2 * Math.PI * radius
  const dash = (score / 100) * circumference

  return (
    <div className={`rounded-2xl border ${c.border} ${c.bg} p-6 flex flex-col items-center score-pop backdrop-blur-lg`} style={{ boxShadow: `0 0 40px -12px ${c.ring}66` }}>
      <p className="label mb-4">Risk Score</p>

      <div className="relative w-36 h-36">
        <svg className="w-full h-full -rotate-90" viewBox="0 0 120 120">
          {/* Track */}
          <circle cx="60" cy="60" r={radius} fill="none" stroke="#1E293B" strokeWidth="10" />
          {/* Progress */}
          <circle
            cx="60" cy="60" r={radius}
            fill="none"
            stroke={c.ring}
            strokeWidth="10"
            strokeLinecap="round"
            strokeDasharray={`${dash} ${circumference}`}
            style={{ transition: 'stroke-dasharray 0.6s ease-out', filter: `drop-shadow(0 0 6px ${c.ring})` }}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className={`font-mono text-5xl font-medium ${c.text}`}>{score}</span>
          <span className="font-mono text-stardust text-xs">/ 100</span>
        </div>
      </div>

      <div className={`mt-4 px-4 py-1.5 rounded-full font-mono text-xs uppercase tracking-widest ${c.text} border ${c.border}`}>
        {level}
      </div>

      <div className="mt-4 w-full font-mono text-[10px] tracking-wider text-stardust text-center space-y-1">
        <div className="flex justify-between">
          <span className="text-green-500">LOW</span>
          <span className="text-yellow-500">MEDIUM</span>
          <span className="text-orange-500">HIGH</span>
          <span className="text-red-500">CRITICAL</span>
        </div>
        <div className="h-1.5 rounded-full bg-gradient-to-r from-green-500 via-yellow-500 via-orange-500 to-red-500" />
      </div>
    </div>
  )
}
