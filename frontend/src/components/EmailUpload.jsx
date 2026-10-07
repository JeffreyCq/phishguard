import { useState, useRef, useEffect } from 'react'
import { Upload, FileText, Loader2, Mail } from 'lucide-react'

// Estimated analysis stages with approximate timing
const STAGES = [
  { until: 12,  label: 'Parsing email structure...' },
  { until: 28,  label: 'Extracting URLs and IPs...' },
  { until: 55,  label: 'Checking threat intelligence...' },
  { until: 82,  label: 'Running AI analysis...' },
  { until: 93,  label: 'Generating report...' },
  { until: 100, label: 'Almost there...' },
]

function getStageLabel(progress) {
  return STAGES.find((s) => progress < s.until)?.label ?? 'Finalizing...'
}

export default function EmailUpload({ onResult, onLoading }) {
  const [mode,     setMode]     = useState('file')
  const [rawText,  setRawText]  = useState('')
  const [dragging, setDragging] = useState(false)
  const [filename, setFilename] = useState(null)
  const [error,    setError]    = useState(null)
  const [loading,  setLoading]  = useState(false)
  const [progress, setProgress] = useState(0)
  const fileRef     = useRef()
  const intervalRef = useRef(null)

  // Advance progress bar while loading
  useEffect(() => {
    if (loading) {
      setProgress(0)
      intervalRef.current = setInterval(() => {
        setProgress((prev) => {
          // Slow down as we approach 93% — never auto-complete to 100
          const increment = prev < 30 ? 2.5
                          : prev < 55 ? 1.2
                          : prev < 80 ? 0.6
                          : prev < 93 ? 0.15
                          : 0
          return Math.min(prev + increment, 93)
        })
      }, 400)
    } else {
      clearInterval(intervalRef.current)
      // Jump to 100% on success then reset
      if (progress > 0) {
        setProgress(100)
        setTimeout(() => setProgress(0), 600)
      }
    }
    return () => clearInterval(intervalRef.current)
  }, [loading])

  const submit = async (formData) => {
    setError(null)
    setLoading(true)
    onLoading?.(true)
    try {
      const res = await fetch('/analyze', { method: 'POST', body: formData })
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: 'Server error' }))
        throw new Error(err.detail || `HTTP ${res.status}`)
      }
      const data = await res.json()
      onResult(data)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
      onLoading?.(false)
    }
  }

  const handleFile = (file) => {
    if (!file) return
    setFilename(file.name)
    const fd = new FormData()
    fd.append('file', file)
    submit(fd)
  }

  const handlePaste = () => {
    if (!rawText.trim()) { setError('Paste your email content first.'); return }
    const fd = new FormData()
    fd.append('raw_email', rawText)
    submit(fd)
  }

  const onDrop = (e) => {
    e.preventDefault()
    setDragging(false)
    const file = e.dataTransfer.files[0]
    if (file) handleFile(file)
  }

  return (
    <div className="max-w-2xl mx-auto glass p-6 sm:p-8 shadow-glow-soft">
      {/* Logo */}
      <div className="text-center mb-10">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-xl bg-burnt/20 border border-burnt/50 mb-4 animate-float shadow-glow transition-shadow hover:shadow-glow-lg">
          <Mail className="w-8 h-8 text-btc" />
        </div>
        <p className="label">AI-powered phishing email analyzer</p>
      </div>

      {/* Mode toggle */}
      <div className="flex rounded-full border border-white/10 p-1 mb-6 bg-black/40">
        {['file', 'paste'].map((m) => (
          <button
            key={m}
            onClick={() => setMode(m)}
            disabled={loading}
            className={`flex-1 min-h-[40px] rounded-full font-mono text-xs uppercase tracking-wider transition-all duration-300 ${
              mode === m
                ? 'bg-gradient-to-r from-burnt to-btc text-white shadow-glow'
                : 'text-stardust hover:text-white disabled:opacity-40'
            }`}
          >
            {m === 'file' ? 'Upload .eml File' : 'Paste Raw Email'}
          </button>
        ))}
      </div>

      {mode === 'file' ? (
        <div
          className={`border-2 border-dashed rounded-2xl p-12 text-center cursor-pointer transition-all duration-300
            ${dragging ? 'drag-over' : 'border-white/20 hover:border-btc/50 hover:shadow-glow-card bg-black/30'}
            ${loading ? 'pointer-events-none opacity-60' : ''}`}
          onClick={() => fileRef.current.click()}
          onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
          onDragLeave={() => setDragging(false)}
          onDrop={onDrop}
        >
          <input
            ref={fileRef}
            type="file"
            accept=".eml,.msg,.txt"
            className="hidden"
            onChange={(e) => handleFile(e.target.files[0])}
          />
          {loading
            ? <Loader2 className="w-10 h-10 text-btc mx-auto animate-spin" />
            : <Upload className="w-10 h-10 text-btc/70 mx-auto" />
          }
          <p className="mt-4 text-white font-heading font-medium text-lg">
            {filename ?? 'Drop your .eml file here'}
          </p>
          <p className="font-mono text-xs text-stardust mt-2">or click to browse — .eml, .msg, .txt</p>
        </div>
      ) : (
        <div className="space-y-3">
          <textarea
            value={rawText}
            onChange={(e) => setRawText(e.target.value)}
            placeholder="Paste the full raw email here (including headers)..."
            rows={12}
            disabled={loading}
            className="field rounded-t-lg p-4 font-mono resize-none"
          />
          <button
            onClick={handlePaste}
            disabled={loading}
            className="btn-primary w-full"
          >
            {loading
              ? <><Loader2 className="w-4 h-4 animate-spin" /> Analyzing...</>
              : <><FileText className="w-4 h-4" /> Analyze Email</>
            }
          </button>
        </div>
      )}

      {/* ── Progress bar ── */}
      {loading && (
        <div className="mt-5 space-y-2">
          {/* Track */}
          <div className="w-full h-1.5 bg-slate-800 rounded-full overflow-hidden">
            <div
              className="h-full rounded-full transition-all duration-500 ease-out"
              style={{
                width: `${progress}%`,
                background: 'linear-gradient(90deg, #EA580C, #F7931A, #FFD600)',
                boxShadow: '0 0 12px rgba(247,147,26,0.6)',
              }}
            />
          </div>
          {/* Label + percentage */}
          <div className="flex justify-between items-center">
            <span className="font-mono text-xs text-stardust animate-pulse">
              {getStageLabel(progress)}
            </span>
            <span className="text-xs text-btc font-mono tabular-nums">
              {Math.round(progress)}%
            </span>
          </div>
        </div>
      )}

      {error && (
        <div className="mt-4 p-3 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400 text-sm">
          {error}
        </div>
      )}

      <p className="text-center font-mono text-[11px] text-stardust/70 mt-6">
        Emails are analyzed in memory and never stored on disk.
      </p>
    </div>
  )
}
