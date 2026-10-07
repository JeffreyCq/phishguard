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
import { RotateCcw, Shield, Globe, Server, Brain, Activity, Paperclip, BookOpen, Zap } from 'lucide-react'

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
    <div className="relative min-h-screen bg-void text-slate-200 overflow-x-clip">
      {/* Ambient void: fading grid + radial energy blurs */}
      <div aria-hidden className="pointer-events-none absolute inset-x-0 top-0 h-[720px]">
        <div className="absolute inset-0 bg-grid-pattern" />
        <div className="absolute -top-40 left-1/2 -translate-x-1/2 w-[640px] h-[640px] rounded-full bg-btc opacity-10 blur-[120px]" />
        <div className="absolute top-40 -right-40 w-[420px] h-[420px] rounded-full bg-burnt opacity-10 blur-[150px]" />
      </div>
      {/* Top bar */}
      <header className="border-b border-white/10 bg-black/40 backdrop-blur-lg sticky top-0 z-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
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
            <span className="font-mono text-[11px] uppercase tracking-widest text-stardust hidden sm:block">Email Threat Analyzer</span>
          </button>

          {/* Right nav */}
          <div className="flex items-center gap-3">
            <button
              onClick={() => setView(view === 'docs' ? 'scanner' : 'docs')}
              className={`flex items-center gap-1.5 font-mono text-xs uppercase tracking-wider px-4 min-h-[36px] rounded-full border transition-all duration-300 ${
                view === 'docs'
                  ? 'bg-btc/15 border-btc text-btc shadow-glow'
                  : 'border-white/20 text-white hover:border-btc/50 hover:text-btc'
              }`}
            >
              <BookOpen className="w-3.5 h-3.5" />
              API Docs
            </button>

            {result && view === 'scanner' && (
              <button
                onClick={reset}
                className="flex items-center gap-1.5 font-mono text-xs uppercase tracking-wider text-stardust hover:text-btc transition-colors"
              >
                <RotateCcw className="w-3.5 h-3.5" /> New scan
              </button>
            )}
          </div>
        </div>
      </header>

      <main className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 py-16 md:py-24">

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
                <div className="text-center mb-14">
                  <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-btc/10 border border-btc/30 text-btc font-mono text-[11px] uppercase tracking-widest mb-6">
                    <span className="relative flex h-2 w-2">
                      <span className="absolute inline-flex h-full w-full rounded-full bg-btc opacity-75 animate-ping" />
                      <span className="relative inline-flex h-2 w-2 rounded-full bg-btc" />
                    </span>
                    Free · Open Source · No account required
                  </div>
                  <h1 className="text-4xl sm:text-5xl md:text-7xl font-bold text-white mb-6 leading-tight">
                    Is this email a <span className="gradient-text">phishing attempt?</span>
                  </h1>
                  <p className="text-stardust text-base md:text-lg max-w-2xl mx-auto leading-relaxed">
                    Paste any suspicious email and get an instant AI-powered threat report —
                    detects <span className="text-white">phishing</span>,{' '}
                    <span className="text-white">spear-phishing</span>,{' '}
                    <span className="text-white">whaling</span>, and{' '}
                    <span className="text-white">spam</span>.
                    No sign-up. Completely free.
                  </p>
                  <div className="flex flex-wrap justify-center gap-3 mt-8 font-mono text-[11px] uppercase tracking-wider text-stardust">
                    {[
                      { icon: Brain,  text: 'DistilBERT classifier' },
                      { icon: Globe,  text: 'VirusTotal URL scanning' },
                      { icon: Shield, text: 'SPF · DKIM · DMARC' },
                      { icon: Zap,    text: 'REST API' },
                    ].map(({ icon: Icon, text }) => (
                      <span key={text} className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full border border-white/10 bg-white/5">
                        <Icon className="w-3.5 h-3.5 text-btc" /> {text}
                      </span>
                    ))}
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
                    <div className="card p-5 space-y-2">
                      <div className="flex gap-2 text-sm">
                        <span className="font-mono text-xs uppercase tracking-wider text-stardust w-16 shrink-0 pt-0.5">From</span>
                        <span className="text-slate-200 break-all">{result.headers.from || '—'}</span>
                      </div>
                      <div className="flex gap-2 text-sm">
                        <span className="font-mono text-xs uppercase tracking-wider text-stardust w-16 shrink-0 pt-0.5">Subject</span>
                        <span className="text-slate-200 break-all">{result.headers.subject || '—'}</span>
                      </div>
                      <div className="flex gap-2 text-sm">
                        <span className="font-mono text-xs uppercase tracking-wider text-stardust w-16 shrink-0 pt-0.5">Date</span>
                        <span className="text-slate-400">{result.headers.date || '—'}</span>
                      </div>
                    </div>

                    {/* Score breakdown */}
                    <div className="card p-5">
                      <p className="label mb-3">Score Breakdown</p>
                      <ScoreBreakdown breakdown={result.risk.breakdown} />
                    </div>
                  </div>
                </div>

                {/* Tabs */}
                <div className="border-b border-white/10">
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
                          className={`flex items-center gap-2 px-4 min-h-[44px] font-mono text-xs uppercase tracking-wider whitespace-nowrap border-b-2 transition-all duration-200 ${
                            activeTab === id
                              ? 'border-btc text-btc'
                              : 'border-transparent text-stardust hover:text-white'
                          }`}
                        >
                          <Icon className="w-3.5 h-3.5" />
                          {label}
                          {count > 0 && (
                            <span className="ml-1 px-1.5 py-0.5 rounded-full bg-btc/15 border border-btc/30 text-[10px] text-btc">
                              {count}
                            </span>
                          )}
                        </button>
                      )
                    })}
                  </div>
                </div>

                {/* Tab content */}
                <div className="card p-6 shadow-glow-soft">
                  {activeTab === 'overview' && (
                    <div className="space-y-4">
                      <p className="label">Threat Indicators</p>
                      <ThreatIndicators indicators={result.indicators} />

                      {result.attachments?.length > 0 && (
                        <>
                          <p className="label mt-4">Attachments</p>
                          <div className="space-y-2">
                            {result.attachments.map((att, i) => (
                              <div key={i} className={`flex items-center gap-3 p-3 rounded-lg border text-sm ${att.suspicious ? 'bg-red-500/10 border-red-500/30' : 'bg-black/40 border-white/10'}`}>
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
      <footer className="relative z-10 border-t border-white/10 bg-matter mt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-10">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
            {/* Credit */}
            <div className="text-center sm:text-left">
              <p className="text-sm text-slate-400">
                Built by{' '}
                <span className="text-white font-heading font-semibold">Jeffrey A. Cedeno Q.</span>
              </p>
              <p className="font-mono text-[11px] uppercase tracking-widest text-stardust mt-1">
                AI Enthusiast · Cybersec Engineer
              </p>
            </div>

            {/* Tech stack badges */}
            <div className="flex flex-wrap justify-center gap-2">
              {[
                'Python', 'FastAPI', 'React', 'DistilBERT', 'ONNX', 'VirusTotal', 'AbuseIPDB', 'Docker',
              ].map((label) => (
                <span
                  key={label}
                  className="font-mono text-[11px] px-3 py-1 rounded-full border border-white/10 text-stardust transition-all duration-300 hover:border-btc/50 hover:text-btc hover:shadow-glow"
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
