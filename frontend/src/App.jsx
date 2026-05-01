import { useState, useEffect } from 'react'
import EmailUpload from './components/EmailUpload'
import StatsPage from './components/StatsPage'
import RiskGauge from './components/RiskGauge'
import ThreatIndicators from './components/ThreatIndicators'
import HeaderAnalysis from './components/HeaderAnalysis'
import UrlResults from './components/UrlResults'
import IpResults from './components/IpResults'
import AiAnalysis from './components/AiAnalysis'
import ScoreBreakdown from './components/ScoreBreakdown'
import ApiDocs from './components/ApiDocs'
import { RotateCcw, Shield, Globe, Server, Brain, Activity, Paperclip, BookOpen } from 'lucide-react'

const SCAN_TABS = [
  { id: 'overview', label: 'Overview',    icon: Activity },
  { id: 'headers',  label: 'Headers',     icon: Shield },
  { id: 'urls',     label: 'URLs',        icon: Globe },
  { id: 'ips',      label: 'IPs',         icon: Server },
  { id: 'ai',       label: 'AI Analysis', icon: Brain },
]

export default function App() {
  const [result,    setResult]    = useState(null)
  const [activeTab, setActiveTab] = useState('overview')
  const [view,      setView]      = useState(() =>
    window.location.hash === '#stats' ? 'stats' : 'scanner'
  )  // 'scanner' | 'docs' | 'stats'

  useEffect(() => {
    const onHashChange = () => {
      if (window.location.hash === '#stats') setView('stats')
    }
    window.addEventListener('hashchange', onHashChange)
    return () => window.removeEventListener('hashchange', onHashChange)
  }, [])

  const reset = () => {
    setResult(null)
    setActiveTab('overview')
    setView('scanner')
    history.replaceState(null, '', window.location.pathname)
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-200">
      {/* Top bar */}
      <header className="border-b border-slate-800 bg-slate-900/50 backdrop-blur sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-4 h-14 flex items-center justify-between">
          {/* Brand */}
          <button
            onClick={reset}
            className="flex items-center gap-2.5 hover:opacity-80 transition-opacity"
          >
            <img
              src="/logomd.png"
              alt="MailDefender"
              className="h-8 w-auto"
              style={{ filter: 'brightness(0) invert(1)' }}
            />
            <span className="text-slate-600 text-xs hidden sm:block">Email Threat Analyzer</span>
          </button>

          {/* Right nav */}
          <div className="flex items-center gap-3">
            <button
              onClick={() => setView(view === 'docs' ? 'scanner' : 'docs')}
              className={`flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg border transition-colors ${
                view === 'docs'
                  ? 'bg-indigo-600/20 border-indigo-500/40 text-indigo-300'
                  : 'border-slate-700 text-slate-400 hover:text-slate-200 hover:border-slate-600'
              }`}
            >
              <BookOpen className="w-3.5 h-3.5" />
              API Docs
            </button>

            {result && view === 'scanner' && (
              <button
                onClick={reset}
                className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-slate-200 transition-colors"
              >
                <RotateCcw className="w-3.5 h-3.5" /> New scan
              </button>
            )}
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-4 py-10">

        {/* ── Stats view ── */}
        {view === 'stats' && <StatsPage />}

        {/* ── API Docs view ── */}
        {view === 'docs' && <ApiDocs />}

        {/* ── Scanner view ── */}
        {view === 'scanner' && (
          <>
            {!result ? (
              <>
                {/* Hero — on-page SEO + value prop */}
                <div className="text-center mb-10">
                  <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 text-xs font-medium mb-4">
                    <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 animate-pulse" />
                    Free · Open Source · No account required
                  </div>
                  <h1 className="text-3xl sm:text-4xl font-bold text-white mb-3 tracking-tight">
                    Is this email a phishing attempt?
                  </h1>
                  <p className="text-slate-400 text-base max-w-xl mx-auto leading-relaxed">
                    Paste any suspicious email and get an instant AI-powered threat report —
                    detects <span className="text-slate-200">phishing</span>,{' '}
                    <span className="text-slate-200">spear-phishing</span>,{' '}
                    <span className="text-slate-200">whaling</span>, and{' '}
                    <span className="text-slate-200">spam</span>.
                    No sign-up. Completely free.
                  </p>
                  <div className="flex flex-wrap justify-center gap-4 mt-5 text-xs text-slate-500">
                    {[
                      '🤖 Custom DistilBERT classifier',
                      '🌐 VirusTotal URL scanning',
                      '🔍 SPF · DKIM · DMARC analysis',
                      '🔌 REST API available',
                    ].map(f => <span key={f}>{f}</span>)}
                  </div>
                </div>
                <EmailUpload onResult={setResult} onLoading={() => {}} />
              </>
            ) : (
              <div className="space-y-6 fade-up">
                {/* Top row: score + summary */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <RiskGauge
                      score={result.risk.score}
                      level={result.risk.level}
                      color={result.risk.color}
                    />
                  </div>
                  <div className="md:col-span-2 space-y-4">
                    {/* Subject / From quick view */}
                    <div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-4 space-y-2">
                      <div className="flex gap-2 text-sm">
                        <span className="text-slate-500 w-16 shrink-0">From</span>
                        <span className="text-slate-200 break-all">{result.headers.from || '—'}</span>
                      </div>
                      <div className="flex gap-2 text-sm">
                        <span className="text-slate-500 w-16 shrink-0">Subject</span>
                        <span className="text-slate-200 break-all">{result.headers.subject || '—'}</span>
                      </div>
                      <div className="flex gap-2 text-sm">
                        <span className="text-slate-500 w-16 shrink-0">Date</span>
                        <span className="text-slate-400">{result.headers.date || '—'}</span>
                      </div>
                    </div>

                    {/* Score breakdown */}
                    <div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-4">
                      <p className="text-xs text-slate-500 uppercase tracking-wide mb-3">Score Breakdown</p>
                      <ScoreBreakdown breakdown={result.risk.breakdown} />
                    </div>
                  </div>
                </div>

                {/* Tabs */}
                <div className="border-b border-slate-800">
                  <div className="flex gap-1 overflow-x-auto pb-px">
                    {SCAN_TABS.map(({ id, label, icon: Icon }) => {
                      const count = id === 'urls'     ? result.urls?.length
                                  : id === 'ips'      ? result.ips?.length
                                  : id === 'overview' ? result.indicators?.length
                                  : null
                      return (
                        <button
                          key={id}
                          onClick={() => setActiveTab(id)}
                          className={`flex items-center gap-1.5 px-3 py-2.5 text-sm whitespace-nowrap border-b-2 transition-colors ${
                            activeTab === id
                              ? 'border-indigo-500 text-white'
                              : 'border-transparent text-slate-400 hover:text-slate-200'
                          }`}
                        >
                          <Icon className="w-3.5 h-3.5" />
                          {label}
                          {count > 0 && (
                            <span className="ml-1 px-1.5 py-0.5 rounded-full bg-slate-800 text-xs text-slate-400">
                              {count}
                            </span>
                          )}
                        </button>
                      )
                    })}
                  </div>
                </div>

                {/* Tab content */}
                <div className="rounded-2xl border border-slate-800 bg-slate-900/30 p-5">
                  {activeTab === 'overview' && (
                    <div className="space-y-4">
                      <p className="text-xs text-slate-500 uppercase tracking-wide">Threat Indicators</p>
                      <ThreatIndicators indicators={result.indicators} />

                      {result.attachments?.length > 0 && (
                        <>
                          <p className="text-xs text-slate-500 uppercase tracking-wide mt-4">Attachments</p>
                          <div className="space-y-2">
                            {result.attachments.map((att, i) => (
                              <div key={i} className={`flex items-center gap-3 p-3 rounded-lg border text-sm ${att.suspicious ? 'bg-red-500/10 border-red-500/30' : 'bg-slate-900 border-slate-800'}`}>
                                <Paperclip className={`w-4 h-4 shrink-0 ${att.suspicious ? 'text-red-400' : 'text-slate-500'}`} />
                                <div className="flex-1 min-w-0">
                                  <p className="font-mono text-slate-300 truncate">{att.filename}</p>
                                  <p className="text-xs text-slate-500">{att.content_type} · {(att.size_bytes / 1024).toFixed(1)} KB</p>
                                </div>
                                {att.suspicious && <span className="text-xs text-red-400 shrink-0">Suspicious type</span>}
                              </div>
                            ))}
                          </div>
                        </>
                      )}
                    </div>
                  )}
                  {activeTab === 'headers' && <HeaderAnalysis headers={result.headers} />}
                  {activeTab === 'urls'    && <UrlResults     urls={result.urls} />}
                  {activeTab === 'ips'     && <IpResults      ips={result.ips} />}
                  {activeTab === 'ai'      && <AiAnalysis     ai={result.ai_analysis} scanId={result.scan_id} />}
                </div>
              </div>
            )}
          </>
        )}
      </main>

      {/* ── Footer ── */}
      <footer className="border-t border-slate-800/60 bg-slate-900/30 mt-16">
        <div className="max-w-6xl mx-auto px-4 py-8">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
            {/* Credit */}
            <div className="text-center sm:text-left">
              <p className="text-sm text-slate-400">
                Built by{' '}
                <span className="text-white font-semibold">Jeffrey A. Cedeno Q.</span>
              </p>
              <p className="text-xs text-slate-500 mt-0.5">
                AI Enthusiast · Cybersec Engineer
              </p>
            </div>

            {/* Tech stack badges */}
            <div className="flex flex-wrap justify-center gap-2">
              {[
                { label: 'Python',       color: 'text-blue-400   border-blue-500/30   bg-blue-500/10'   },
                { label: 'FastAPI',      color: 'text-teal-400   border-teal-500/30   bg-teal-500/10'   },
                { label: 'React',        color: 'text-cyan-400   border-cyan-500/30   bg-cyan-500/10'   },
                { label: 'DistilBERT',   color: 'text-violet-400 border-violet-500/30 bg-violet-500/10' },
                { label: 'ONNX',         color: 'text-indigo-400 border-indigo-500/30 bg-indigo-500/10' },
                { label: 'VirusTotal',   color: 'text-orange-400 border-orange-500/30 bg-orange-500/10' },
                { label: 'AbuseIPDB',    color: 'text-red-400    border-red-500/30    bg-red-500/10'    },
                { label: 'Docker',       color: 'text-sky-400    border-sky-500/30    bg-sky-500/10'    },
              ].map(({ label, color }) => (
                <span
                  key={label}
                  className={`text-xs px-2.5 py-1 rounded-full border font-medium ${color}`}
                >
                  {label}
                </span>
              ))}
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}
