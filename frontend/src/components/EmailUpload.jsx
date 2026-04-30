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
    <div className="max-w-2xl mx-auto">
      {/* Logo */}
      <div className="text-center mb-10">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-indigo-600/20 border border-indigo-500/30 mb-4">
          <Mail className="w-8 h-8 text-white" />
        </div>
        <h1 className="text-3xl font-bold text-white tracking-tight">MailDefender</h1>
        <p className="text-slate-400 mt-2 text-sm">AI-powered phishing email analyzer</p>
      </div>

      {/* Mode toggle */}
      <div className="flex rounded-lg border border-slate-700 p-1 mb-6 bg-slate-900/50">
        {['file', 'paste'].map((m) => (
          <button
            key={m}
            onClick={() => setMode(m)}
            disabled={loading}
            className={`flex-1 py-2 rounded-md text-sm font-medium transition-all ${
              mode === m
                ? 'bg-indigo-600 text-white shadow'
                : 'text-slate-400 hover:text-slate-200 disabled:opacity-40'
            }`}
          >
            {m === 'file' ? 'Upload .eml File' : 'Paste Raw Email'}
          </button>
        ))}
      </div>

      {mode === 'file' ? (
        <div
          className={`border-2 border-dashed rounded-xl p-12 text-center cursor-pointer transition-all
            ${dragging ? 'drag-over' : 'border-slate-700 hover:border-slate-500 bg-slate-900/30'}
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
            ? <Loader2 className="w-10 h-10 text-indigo-400 mx-auto animate-spin" />
            : <Upload className="w-10 h-10 text-slate-500 mx-auto" />
          }
          <p className="mt-4 text-slate-300 font-medium">
            {filename ?? 'Drop your .eml file here'}
          </p>
          <p className="text-slate-500 text-sm mt-1">or click to browse — .eml, .msg, .txt</p>
        </div>
      ) : (
        <div className="space-y-3">
          <textarea
            value={rawText}
            onChange={(e) => setRawText(e.target.value)}
            placeholder="Paste the full raw email here (including headers)..."
            rows={12}
            disabled={loading}
            className="w-full rounded-xl bg-slate-900 border border-slate-700 text-slate-200
              placeholder-slate-500 p-4 text-sm font-mono resize-none focus:outline-none
              focus:border-indigo-500 transition-colors disabled:opacity-60"
          />
          <button
            onClick={handlePaste}
            disabled={loading}
            className="w-full py-3 rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50
              text-white font-semibold text-sm transition-colors flex items-center justify-center gap-2"
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
                background: 'linear-gradient(90deg, #6366f1, #818cf8)',
              }}
            />
          </div>
          {/* Label + percentage */}
          <div className="flex justify-between items-center">
            <span className="text-xs text-slate-500 animate-pulse">
              {getStageLabel(progress)}
            </span>
            <span className="text-xs text-slate-600 font-mono tabular-nums">
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

      <p className="text-center text-slate-600 text-xs mt-6">
        Emails are analyzed in memory and never stored on disk.
      </p>
    </div>
  )
}
