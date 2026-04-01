import { useState, useRef } from 'react'
import { Upload, FileText, Loader2, ShieldAlert } from 'lucide-react'

export default function EmailUpload({ onResult, onLoading }) {
  const [mode, setMode] = useState('file') // 'file' | 'paste'
  const [rawText, setRawText] = useState('')
  const [dragging, setDragging] = useState(false)
  const [filename, setFilename] = useState(null)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)
  const fileRef = useRef()

  const submit = async (formData) => {
    setError(null)
    setLoading(true)
    onLoading(true)
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
      onLoading(false)
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
          <ShieldAlert className="w-8 h-8 text-indigo-400" />
        </div>
        <h1 className="text-3xl font-bold text-white tracking-tight">PhishGuard</h1>
        <p className="text-slate-400 mt-2 text-sm">AI-powered phishing email analyzer</p>
      </div>

      {/* Mode toggle */}
      <div className="flex rounded-lg border border-slate-700 p-1 mb-6 bg-slate-900/50">
        {['file', 'paste'].map((m) => (
          <button
            key={m}
            onClick={() => setMode(m)}
            className={`flex-1 py-2 rounded-md text-sm font-medium transition-all ${
              mode === m
                ? 'bg-indigo-600 text-white shadow'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            {m === 'file' ? 'Upload .eml File' : 'Paste Raw Email'}
          </button>
        ))}
      </div>

      {mode === 'file' ? (
        <div
          className={`border-2 border-dashed rounded-xl p-12 text-center cursor-pointer transition-all
            ${dragging ? 'drag-over' : 'border-slate-700 hover:border-slate-500 bg-slate-900/30'}`}
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
          {loading ? (
            <Loader2 className="w-10 h-10 text-indigo-400 mx-auto animate-spin" />
          ) : (
            <Upload className="w-10 h-10 text-slate-500 mx-auto" />
          )}
          <p className="mt-4 text-slate-300 font-medium">
            {filename ? filename : 'Drop your .eml file here'}
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
            className="w-full rounded-xl bg-slate-900 border border-slate-700 text-slate-200
              placeholder-slate-500 p-4 text-sm font-mono resize-none focus:outline-none
              focus:border-indigo-500 transition-colors"
          />
          <button
            onClick={handlePaste}
            disabled={loading}
            className="w-full py-3 rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50
              text-white font-semibold text-sm transition-colors flex items-center justify-center gap-2"
          >
            {loading ? <><Loader2 className="w-4 h-4 animate-spin" /> Analyzing...</> : <><FileText className="w-4 h-4" /> Analyze Email</>}
          </button>
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
