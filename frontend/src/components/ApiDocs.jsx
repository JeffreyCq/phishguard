import { useState } from 'react'
import { Terminal, Key, Zap, Shield, Globe, Server, ChevronRight, Cpu } from 'lucide-react'

// ── Reusable primitives ──────────────────────────────────────────────────────

function Badge({ children, color = 'indigo' }) {
  const classes = {
    indigo:  'bg-indigo-500/15 text-indigo-300 border-indigo-500/30',
    violet:  'bg-violet-500/15 text-violet-300 border-violet-500/30',
    green:   'bg-green-500/15  text-green-300  border-green-500/30',
    yellow:  'bg-yellow-500/15 text-yellow-300 border-yellow-500/30',
    red:     'bg-red-500/15    text-red-300    border-red-500/30',
    slate:   'bg-slate-700     text-slate-300  border-slate-600',
  }
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-mono border ${classes[color]}`}>
      {children}
    </span>
  )
}

function Method({ verb }) {
  const colors = { POST: 'bg-blue-600', GET: 'bg-green-600', DELETE: 'bg-red-700' }
  return (
    <span className={`${colors[verb] ?? 'bg-slate-600'} text-white text-xs font-bold px-2 py-0.5 rounded font-mono`}>
      {verb}
    </span>
  )
}

function CodeBlock({ children }) {
  return (
    <pre className="mt-2 bg-slate-950 border border-slate-800 rounded-lg p-4 text-xs text-slate-300 font-mono overflow-x-auto leading-relaxed">
      {children}
    </pre>
  )
}

function CodeTabs({ tabs }) {
  const [active, setActive] = useState(tabs[0].label)
  const current = tabs.find(t => t.label === active)
  return (
    <div className="mt-2">
      <div className="flex gap-0.5 border-b border-slate-800">
        {tabs.map(t => (
          <button
            key={t.label}
            onClick={() => setActive(t.label)}
            className={`px-3 py-1.5 text-xs font-mono transition-colors rounded-t ${
              active === t.label
                ? 'bg-slate-950 text-white border border-b-slate-950 border-slate-800 -mb-px z-10 relative'
                : 'text-slate-500 hover:text-slate-300'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>
      <pre className="bg-slate-950 border border-slate-800 border-t-0 rounded-b-lg p-4 text-xs text-slate-300 font-mono overflow-x-auto leading-relaxed">
        {current.code}
      </pre>
    </div>
  )
}

function Section({ id, icon: Icon, title, children }) {
  return (
    <section id={id} className="scroll-mt-20">
      <div className="flex items-center gap-2.5 mb-4">
        <div className="w-7 h-7 rounded-lg bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center shrink-0">
          <Icon className="w-3.5 h-3.5 text-white" />
        </div>
        <h2 className="text-lg font-semibold text-white">{title}</h2>
      </div>
      <div className="space-y-4">{children}</div>
    </section>
  )
}

function Card({ children }) {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-5">
      {children}
    </div>
  )
}

function EndpointRow({ method, path, auth, description }) {
  return (
    <div className="flex items-start gap-3 py-3 border-b border-slate-800/60 last:border-0">
      <Method verb={method} />
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <code className="text-sm text-slate-200 font-mono">{path}</code>
          {auth && <Badge color="yellow">requires X-API-Key</Badge>}
        </div>
        <p className="text-sm text-slate-400 mt-0.5">{description}</p>
      </div>
    </div>
  )
}

function ResponseField({ field, type, description }) {
  return (
    <tr className="border-b border-slate-800/40">
      <td className="py-2 pr-4 align-top">
        <code className="text-xs text-indigo-300 font-mono">{field}</code>
      </td>
      <td className="py-2 pr-4 align-top">
        <Badge color="slate">{type}</Badge>
      </td>
      <td className="py-2 text-sm text-slate-400">{description}</td>
    </tr>
  )
}

// ── Main component ───────────────────────────────────────────────────────────

export default function ApiDocs() {
  const navItems = [
    { id: 'overview',    label: 'Overview'       },
    { id: 'classifier',  label: 'ML Classifier'  },
    { id: 'auth',        label: 'Authentication' },
    { id: 'endpoints',   label: 'Endpoints'      },
    { id: 'response',    label: 'Response Schema'},
    { id: 'examples',    label: 'Code Examples'  },
  ]

  const scrollTo = (id) =>
    document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' })

  return (
    <div className="flex gap-8 fade-up">
      {/* ── Sidebar nav ── */}
      <aside className="hidden lg:block w-44 shrink-0">
        <div className="sticky top-20 space-y-1">
          <p className="text-xs text-slate-500 uppercase tracking-widest mb-3">Contents</p>
          {navItems.map(({ id, label }) => (
            <button
              key={id}
              onClick={() => scrollTo(id)}
              className="flex items-center gap-1.5 w-full text-left text-sm text-slate-400 hover:text-slate-200 py-1 transition-colors"
            >
              <ChevronRight className="w-3 h-3 text-slate-600" />
              {label}
            </button>
          ))}
        </div>
      </aside>

      {/* ── Main content ── */}
      <div className="flex-1 min-w-0 space-y-12">

        {/* Overview */}
        <Section id="overview" icon={Shield} title="Overview">
          <Card>
            <p className="text-sm text-slate-300 leading-relaxed">
              <strong className="text-white">MailDefender</strong> is a phishing and spam
              detection platform. It analyzes raw emails using a{' '}
              <strong className="text-violet-300">custom-trained DistilBERT microservice</strong>{' '}
              (no external API costs, no data leaves your infrastructure) combined with
              real-time threat intelligence from VirusTotal and AbuseIPDB.
            </p>
            <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 gap-3">
              {[
                { icon: Cpu,      label: 'DistilBERT / ONNX',  desc: 'Custom-trained NLP classifier — fast, local, no token costs' },
                { icon: Shield,   label: 'Threat Intel',        desc: 'VirusTotal URL & IP checks + AbuseIPDB reputation' },
                { icon: Terminal, label: 'REST API',            desc: 'Integrate phishing detection in your own tools' },
              ].map(({ icon: Icon, label, desc }) => (
                <div key={label} className="flex items-start gap-3 p-3 rounded-lg bg-slate-950/50 border border-slate-800">
                  <Icon className="w-4 h-4 text-white mt-0.5 shrink-0" />
                  <div>
                    <p className="text-sm font-medium text-slate-200">{label}</p>
                    <p className="text-xs text-slate-500 mt-0.5">{desc}</p>
                  </div>
                </div>
              ))}
            </div>
            <div className="mt-4 flex items-center gap-2 text-sm text-slate-400">
              <span className="text-slate-500">Base URL</span>
              <code className="text-indigo-300 font-mono">https://maildefender.xyz</code>
            </div>
          </Card>
        </Section>

        {/* ML Classifier */}
        <Section id="classifier" icon={Cpu} title="ML Classifier">
          <Card>
            <p className="text-sm text-slate-300 leading-relaxed mb-4">
              The core of MailDefender is a{' '}
              <strong className="text-white">custom DistilBERT model</strong> fine-tuned
              on email threat data and exported to{' '}
              <strong className="text-white">ONNX</strong> for fast CPU inference. It runs
              as an independent microservice at{' '}
              <code className="text-violet-300">ml.maildefender.xyz</code> and classifies
              every email into one of five threat categories.
            </p>

            {/* 5 threat classes */}
            <p className="text-xs text-slate-500 uppercase tracking-wide mb-3">Threat Classes</p>
            <div className="space-y-2 mb-5">
              {[
                { cls: 'legitimate',     level: 0, color: 'green',  desc: 'Normal correspondence — no threat indicators detected.' },
                { cls: 'spam',           level: 1, color: 'yellow', desc: 'Unsolicited bulk email. No direct malicious intent but unwanted.' },
                { cls: 'phishing',       level: 2, color: 'yellow', desc: 'Credential harvesting or malicious link delivery targeting a generic recipient.' },
                { cls: 'spear_phishing', level: 3, color: 'red',    desc: 'Targeted attack with personalization — prior reconnaissance on the victim is evident.' },
                { cls: 'whaling',        level: 4, color: 'red',    desc: 'High-value target attack (executive, finance) — elevated threat level.' },
              ].map(({ cls, level, color, desc }) => (
                <div key={cls} className="flex items-start gap-3 p-3 rounded-lg bg-slate-950/40 border border-slate-800">
                  <div className="flex items-center gap-2 w-36 shrink-0">
                    <Badge color={color}>{cls}</Badge>
                  </div>
                  <p className="text-xs text-slate-400 leading-relaxed">{desc}</p>
                </div>
              ))}
            </div>

            {/* Verdict mapping */}
            <p className="text-xs text-slate-500 uppercase tracking-wide mb-3">Verdict Mapping</p>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-slate-700">
                    <th className="pb-2 text-xs text-slate-500 uppercase tracking-wide">ML Class</th>
                    <th className="pb-2 text-xs text-slate-500 uppercase tracking-wide">Condition</th>
                    <th className="pb-2 text-xs text-slate-500 uppercase tracking-wide">Phishing Verdict</th>
                    <th className="pb-2 text-xs text-slate-500 uppercase tracking-wide">Spam Verdict</th>
                  </tr>
                </thead>
                <tbody className="text-slate-400 text-xs">
                  <tr className="border-b border-slate-800/40"><td className="py-2 pr-4"><Badge color="red">whaling</Badge></td><td className="py-2 pr-4">—</td><td className="py-2 pr-4"><Badge color="red">PHISHING</Badge></td><td className="py-2">NOT_SPAM</td></tr>
                  <tr className="border-b border-slate-800/40"><td className="py-2 pr-4"><Badge color="red">spear_phishing</Badge></td><td className="py-2 pr-4">—</td><td className="py-2 pr-4"><Badge color="red">PHISHING</Badge></td><td className="py-2">NOT_SPAM</td></tr>
                  <tr className="border-b border-slate-800/40"><td className="py-2 pr-4"><Badge color="yellow">phishing</Badge></td><td className="py-2 pr-4">confidence ≥ 65%</td><td className="py-2 pr-4"><Badge color="red">PHISHING</Badge></td><td className="py-2">NOT_SPAM</td></tr>
                  <tr className="border-b border-slate-800/40"><td className="py-2 pr-4"><Badge color="yellow">phishing</Badge></td><td className="py-2 pr-4">confidence &lt; 65%</td><td className="py-2 pr-4"><Badge color="yellow">SUSPICIOUS</Badge></td><td className="py-2">NOT_SPAM</td></tr>
                  <tr className="border-b border-slate-800/40"><td className="py-2 pr-4"><Badge color="yellow">spam</Badge></td><td className="py-2 pr-4">phishing scores &gt; 30%</td><td className="py-2 pr-4"><Badge color="yellow">SUSPICIOUS</Badge></td><td className="py-2">SPAM</td></tr>
                  <tr className="border-b border-slate-800/40"><td className="py-2 pr-4"><Badge color="yellow">spam</Badge></td><td className="py-2 pr-4">phishing scores ≤ 30%</td><td className="py-2 pr-4"><Badge color="green">LIKELY_SAFE</Badge></td><td className="py-2">SPAM</td></tr>
                  <tr className="border-b border-slate-800/40"><td className="py-2 pr-4"><Badge color="green">legitimate</Badge></td><td className="py-2 pr-4">confidence ≥ 80%</td><td className="py-2 pr-4"><Badge color="green">SAFE</Badge></td><td className="py-2">NOT_SPAM</td></tr>
                  <tr><td className="py-2 pr-4"><Badge color="green">legitimate</Badge></td><td className="py-2 pr-4">confidence &lt; 80%</td><td className="py-2 pr-4"><Badge color="green">LIKELY_SAFE</Badge></td><td className="py-2">NOT_SPAM</td></tr>
                </tbody>
              </table>
            </div>
          </Card>

          {/* Detectable signals */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Card>
              <p className="text-xs text-slate-500 uppercase tracking-wide mb-3">Social Engineering Tactics</p>
              <div className="flex flex-wrap gap-1.5">
                {[
                  'urgency', 'fear', 'authority', 'impersonation',
                  'credential_harvesting', 'brand_spoofing',
                  'prize_scam', 'invoice_fraud',
                  'malware_delivery', 'url_obfuscation',
                ].map(t => <Badge key={t} color="slate">{t}</Badge>)}
              </div>
            </Card>
            <Card>
              <p className="text-xs text-slate-500 uppercase tracking-wide mb-3">Spam Signals</p>
              <div className="flex flex-wrap gap-1.5">
                {[
                  'tracking_pixel', 'unsubscribe_link', 'bulk_headers',
                  'mass_marketing_platform', 'url_tracking',
                  'promotional_language', 'suspicious_sender_domain',
                ].map(t => <Badge key={t} color="slate">{t}</Badge>)}
              </div>
            </Card>
          </div>

          {/* Header / structural signals */}
          <Card>
            <p className="text-xs text-slate-500 uppercase tracking-wide mb-3">Structural & Header Indicators</p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-sm text-slate-400">
              {[
                'SPF fail / softfail',
                'DKIM signature failure',
                'DMARC policy violation',
                'From ↔ Reply-To domain mismatch',
                'Typosquatted sender domain',
                'URL shortener (bit.ly, tinyurl…)',
                'Suspicious attachment extension',
                'Executable / macro file in attachment',
                'VirusTotal flagged URL',
                'VirusTotal flagged sender IP',
                'AbuseIPDB reported IP',
                'Bare IP address as sender',
              ].map(s => (
                <div key={s} className="flex items-center gap-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-indigo-500 shrink-0" />
                  {s}
                </div>
              ))}
            </div>
          </Card>
        </Section>

        {/* Authentication */}
        <Section id="auth" icon={Key} title="Authentication">
          <Card>
            <p className="text-sm text-slate-300 leading-relaxed mb-4">
              The <code className="text-indigo-300">/api/v1/scan</code> endpoint requires an API key.
              Pass it in the <code className="text-yellow-300">X-API-Key</code> request header.
              The web UI (<code className="text-indigo-300">/analyze</code>) has no authentication requirement.
            </p>

            <p className="text-xs text-slate-500 uppercase tracking-wide mb-2">Key Format</p>
            <div className="flex items-center gap-2 p-3 rounded-lg bg-slate-950/60 border border-slate-800 mb-4 font-mono text-sm">
              <span className="text-violet-400">mdef_</span>
              <span className="text-slate-400">xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx</span>
            </div>

            <p className="text-xs text-slate-500 uppercase tracking-wide mb-2">Usage</p>
            <CodeBlock>
{`curl -X POST https://maildefender.xyz/api/v1/scan \\
  -H "X-API-Key: mdef_your_key_here" \\
  -F "raw_email=<suspicious.eml"`}
            </CodeBlock>
          </Card>

          <Card>
            <p className="text-xs text-slate-500 uppercase tracking-wide mb-3">Obtaining a Key</p>
            <p className="text-sm text-slate-300 leading-relaxed mb-3">
              API keys are issued by the MailDefender administrator. Contact{' '}
              <a href="mailto:jeffreyacq@gmail.com" className="text-indigo-300 hover:text-indigo-200 underline underline-offset-2">
                jeffreyacq@gmail.com
              </a>{' '}
              to request access. Include your use case and expected request volume.
            </p>
            <div className="p-3 rounded-lg bg-indigo-500/5 border border-indigo-500/20">
              <p className="text-xs text-indigo-300">
                Keys are prefixed <code>mdef_</code> and shown <strong>once</strong> at issuance — store yours securely.
                Lost keys must be revoked and reissued.
              </p>
            </div>
          </Card>

          <Card>
            <p className="text-xs text-slate-500 uppercase tracking-wide mb-3">Rate Limits</p>
            <div className="space-y-3">
              <div className="flex items-start gap-3 p-3 rounded-lg bg-slate-950/50 border border-slate-800">
                <div className="w-2 h-2 rounded-full bg-indigo-500 shrink-0 mt-1.5" />
                <div>
                  <p className="text-sm text-slate-200 font-medium">1,000 requests / day</p>
                  <p className="text-xs text-slate-500 mt-0.5">Default limit per key. Resets at midnight UTC.</p>
                </div>
              </div>
              <div className="flex items-start gap-3 p-3 rounded-lg bg-slate-950/50 border border-slate-800">
                <div className="w-2 h-2 rounded-full bg-yellow-500 shrink-0 mt-1.5" />
                <div>
                  <p className="text-sm text-slate-200 font-medium">429 Too Many Requests</p>
                  <p className="text-xs text-slate-500 mt-0.5">Returned when limit is exceeded. Try again the next day or contact the admin for a higher limit.</p>
                </div>
              </div>
              <div className="flex items-start gap-3 p-3 rounded-lg bg-slate-950/50 border border-slate-800">
                <div className="w-2 h-2 rounded-full bg-red-500 shrink-0 mt-1.5" />
                <div>
                  <p className="text-sm text-slate-200 font-medium">401 Unauthorized</p>
                  <p className="text-xs text-slate-500 mt-0.5">Missing, invalid, or revoked key. Verify your <code className="text-slate-300">X-API-Key</code> header is correct.</p>
                </div>
              </div>
            </div>
          </Card>
        </Section>

        {/* Endpoints */}
        <Section id="endpoints" icon={Zap} title="Endpoints">
          <Card>
            <p className="text-xs text-slate-500 uppercase tracking-wide mb-3">Public</p>
            <EndpointRow
              method="GET"
              path="/health"
              description="Returns service status, ML microservice URL, and which integrations are configured."
            />
            <EndpointRow
              method="POST"
              path="/api/v1/scan"
              auth
              description="Analyze a raw email. Returns full threat report with risk score, ML verdict, and all indicators."
            />
            <EndpointRow
              method="GET"
              path="/docs"
              description="Interactive Swagger UI — try all endpoints directly in the browser."
            />
            <EndpointRow
              method="GET"
              path="/redoc"
              description="ReDoc-rendered API reference documentation."
            />
          </Card>

          {/* Health detail */}
          <Card>
            <div className="flex items-center gap-2 mb-3">
              <Method verb="GET" />
              <code className="text-sm text-slate-200 font-mono">/health</code>
            </div>
            <p className="text-sm text-slate-400 mb-3">No authentication required.</p>
            <CodeBlock>
{`{
  "status": "ok",
  "ml_classifier": "https://ml.maildefender.xyz",
  "ml_backend": "distilbert/onnx (microservice)",
  "configured_apis": {
    "virustotal": true,
    "urlscan": false,
    "abuseipdb": true
  },
  "public_api_enabled": true,
  "email_forwarding": true,
  "email_scan_address": "${address}"
}`}
            </CodeBlock>
          </Card>

          {/* Scan detail */}
          <Card>
            <div className="flex items-center gap-2 mb-3">
              <Method verb="POST" />
              <code className="text-sm text-slate-200 font-mono">/api/v1/scan</code>
              <Badge color="yellow">X-API-Key</Badge>
            </div>
            <p className="text-sm text-slate-400 mb-1">
              Content-Type: <code className="text-slate-300">multipart/form-data</code>
            </p>
            <div className="flex items-start gap-3 py-2 text-sm">
              <code className="text-indigo-300 font-mono w-28 shrink-0">raw_email</code>
              <span className="text-slate-400">
                Required. Complete raw email in RFC 5322 format (headers + blank line + body).
                Obtain it via <em>View Source</em> / <em>Show Original</em> in your email client.
              </span>
            </div>
          </Card>
        </Section>

        {/* Response Schema */}
        <Section id="response" icon={Server} title="Response Schema">
          <Card>
            <p className="text-sm text-slate-400 mb-4">
              All fields returned by <code className="text-indigo-300">/api/v1/scan</code>:
            </p>
            <div className="overflow-x-auto">
              <table className="w-full text-left">
                <thead>
                  <tr className="border-b border-slate-700">
                    <th className="pb-2 text-xs text-slate-500 uppercase tracking-wide w-40">Field</th>
                    <th className="pb-2 text-xs text-slate-500 uppercase tracking-wide w-24">Type</th>
                    <th className="pb-2 text-xs text-slate-500 uppercase tracking-wide">Description</th>
                  </tr>
                </thead>
                <tbody>
                  <tr><td colSpan={3} className="pt-4 pb-1"><p className="text-xs text-slate-500 uppercase tracking-wide">Risk Score</p></td></tr>
                  <ResponseField field="score"          type="int 0–100" description="Overall risk score. Weighted combination of all signals." />
                  <ResponseField field="level"          type="string"    description="LOW (0–19) · MEDIUM (20–44) · HIGH (45–69) · CRITICAL (70–100)" />

                  <tr><td colSpan={3} className="pt-4 pb-1"><p className="text-xs text-slate-500 uppercase tracking-wide">Phishing Analysis</p></td></tr>
                  <ResponseField field="verdict"        type="string"    description="SAFE · LIKELY_SAFE · SUSPICIOUS · PHISHING — derived from ML classifier output." />
                  <ResponseField field="confidence"     type="int 0–100" description="ML classifier confidence in the phishing verdict." />
                  <ResponseField field="reasoning"      type="string"    description="Plain-English explanation of the threat classification." />
                  <ResponseField field="tactics"        type="string[]"  description="Detected social engineering tactics (urgency, impersonation, credential_harvesting, etc.)." />
                  <ResponseField field="red_flags"      type="string[]"  description="Specific threat indicators found in headers, body, and metadata." />
                  <ResponseField field="recommendation" type="string"    description="Suggested action for the end user." />

                  <tr><td colSpan={3} className="pt-4 pb-1"><p className="text-xs text-slate-500 uppercase tracking-wide">Spam Analysis</p></td></tr>
                  <ResponseField field="spam_verdict"    type="string"    description="NOT_SPAM · LIKELY_SPAM · SPAM — independent from phishing verdict." />
                  <ResponseField field="spam_confidence" type="int 0–100" description="ML confidence in the spam verdict." />
                  <ResponseField field="spam_signals"    type="string[]"  description="Detected spam signals: tracking_pixel, bulk_headers, mass_marketing_platform, unsubscribe_link, url_tracking, promotional_language, suspicious_sender_domain." />

                  <tr><td colSpan={3} className="pt-4 pb-1"><p className="text-xs text-slate-500 uppercase tracking-wide">Raw ML Output</p></td></tr>
                  <ResponseField field="ml_classifier.threat_type"  type="string"    description="Raw class from the model: legitimate · spam · phishing · spear_phishing · whaling" />
                  <ResponseField field="ml_classifier.threat_level" type="int 0–4"   description="Numeric severity: 0=legitimate, 1=spam, 2=phishing, 3=spear_phishing, 4=whaling" />
                  <ResponseField field="ml_classifier.confidence"   type="float 0–1" description="Raw probability of the predicted class." />
                  <ResponseField field="ml_classifier.scores"       type="object"    description="Per-class probability scores (0–1) for all five categories." />

                  <tr><td colSpan={3} className="pt-4 pb-1"><p className="text-xs text-slate-500 uppercase tracking-wide">Threat Intelligence</p></td></tr>
                  <ResponseField field="indicators"     type="string[]"  description="Structural indicators: SPF/DKIM/DMARC failures, domain mismatches, URL shorteners, suspicious attachments." />
                  <ResponseField field="urls_total"     type="integer"   description="Total URLs extracted from the email body." />
                  <ResponseField field="urls_flagged"   type="integer"   description="URLs flagged as malicious by VirusTotal." />
                  <ResponseField field="ips_flagged"    type="integer"   description="Sender IPs flagged by VirusTotal or AbuseIPDB." />

                  <tr><td colSpan={3} className="pt-4 pb-1"><p className="text-xs text-slate-500 uppercase tracking-wide">Email Authentication</p></td></tr>
                  <ResponseField field="auth.spf"                    type="string"  description="SPF result: pass · fail · softfail · none" />
                  <ResponseField field="auth.dkim"                   type="string"  description="DKIM result: pass · fail · none" />
                  <ResponseField field="auth.dmarc"                  type="string"  description="DMARC result: pass · fail · none" />
                  <ResponseField field="auth.from_reply_to_mismatch" type="boolean" description="true if From and Reply-To use different domains." />
                </tbody>
              </table>
            </div>
          </Card>

          {/* Risk / verdict quick ref */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Card>
              <p className="text-xs text-slate-500 uppercase tracking-wide mb-3">Risk Levels</p>
              <div className="space-y-2 text-sm">
                {[
                  { val: 'LOW',      range: '0–19',   color: 'green'  },
                  { val: 'MEDIUM',   range: '20–44',  color: 'yellow' },
                  { val: 'HIGH',     range: '45–69',  color: 'yellow' },
                  { val: 'CRITICAL', range: '70–100', color: 'red'    },
                ].map(({ val, range, color }) => (
                  <div key={val} className="flex items-center justify-between">
                    <Badge color={color}>{val}</Badge>
                    <span className="text-slate-500 font-mono text-xs">score {range}</span>
                  </div>
                ))}
              </div>
            </Card>
            <Card>
              <p className="text-xs text-slate-500 uppercase tracking-wide mb-3">Phishing Verdicts</p>
              <div className="space-y-2 text-sm">
                {[
                  { val: 'SAFE',        color: 'green',  note: 'legitimate ≥ 80% conf.'   },
                  { val: 'LIKELY_SAFE', color: 'green',  note: 'legitimate < 80% conf.'   },
                  { val: 'SUSPICIOUS',  color: 'yellow', note: 'phishing < 65% conf.'     },
                  { val: 'PHISHING',    color: 'red',    note: 'whaling / spear / phishing ≥ 65%' },
                ].map(({ val, color, note }) => (
                  <div key={val} className="flex items-center justify-between gap-2">
                    <Badge color={color}>{val}</Badge>
                    <span className="text-slate-500 text-xs text-right">{note}</span>
                  </div>
                ))}
              </div>
            </Card>
          </div>
        </Section>

        {/* Code Examples */}
        <Section id="examples" icon={Globe} title="Code Examples">
          <Card>
            <CodeTabs tabs={[
              {
                label: 'curl',
                code:
`# Analyze a saved .eml file
curl -X POST https://maildefender.xyz/api/v1/scan \\
  -H "X-API-Key: mdef_your_key_here" \\
  -F "raw_email=<suspicious.eml"

# Paste raw email inline
curl -X POST https://maildefender.xyz/api/v1/scan \\
  -H "X-API-Key: mdef_your_key_here" \\
  -F 'raw_email=From: attacker@evil.com
To: victim@company.com
Subject: Urgent: Verify your account

Click here: http://phishing-site.com'`,
              },
              {
                label: 'Python',
                code:
`import requests

with open("suspicious.eml", "r") as f:
    raw_email = f.read()

response = requests.post(
    "https://maildefender.xyz/api/v1/scan",
    headers={"X-API-Key": "mdef_your_key_here"},
    data={"raw_email": raw_email},
)

result = response.json()
print(f"Risk: {result['level']} ({result['score']}/100)")
print(f"Verdict: {result['verdict']} — {result['confidence']}% confidence")
print(f"Reasoning: {result['reasoning']}")
if result["tactics"]:
    print(f"Tactics: {', '.join(result['tactics'])}")

# Raw ML scores
ml = result["ml_classifier"]
print(f"ML class: {ml['threat_type']} (level {ml['threat_level']})")
for cls, prob in ml["scores"].items():
    print(f"  {cls}: {prob:.2%}")`,
              },
              {
                label: 'JavaScript',
                code:
`const form = new FormData();
form.append('raw_email', rawEmailString);

const res = await fetch('https://maildefender.xyz/api/v1/scan', {
  method: 'POST',
  headers: { 'X-API-Key': 'mdef_your_key_here' },
  body: form,
});

const { score, level, verdict, reasoning, tactics, ml_classifier } = await res.json();
console.log(\`\${level} (\${score}/100) — \${verdict}\`);
console.log(\`ML class: \${ml_classifier.threat_type}\`);`,
              },
              {
                label: 'PHP',
                code:
`<?php
$ch = curl_init('https://maildefender.xyz/api/v1/scan');
$raw = file_get_contents('suspicious.eml');

curl_setopt_array($ch, [
    CURLOPT_POST           => true,
    CURLOPT_RETURNTRANSFER => true,
    CURLOPT_HTTPHEADER     => ['X-API-Key: mdef_your_key_here'],
    CURLOPT_POSTFIELDS     => ['raw_email' => $raw],
]);

$body   = curl_exec($ch);
$result = json_decode($body, true);

echo "{$result['level']} ({$result['score']}/100) — {$result['verdict']}\\n";
echo "Reasoning: {$result['reasoning']}\\n";`,
              },
            ]} />
          </Card>

          {/* Sample response */}
          <Card>
            <p className="text-sm font-medium text-slate-200 mb-1">Sample Response</p>
            <CodeBlock>
{`{
  "score": 78,
  "level": "CRITICAL",
  "verdict": "PHISHING",
  "confidence": 92,
  "reasoning": "This email exhibits strong indicators of a phishing attempt. The sender identity, subject line, and content patterns match known phishing templates.",
  "tactics": ["impersonation", "urgency", "credential_harvesting", "url_obfuscation"],
  "red_flags": [
    "SPF fail — sender not authorized for this domain",
    "From domain (paypa1-support.com) differs from Reply-To domain (secure-verify.net)",
    "Link destination hidden behind URL shortener"
  ],
  "recommendation": "Do not click any links or enter credentials — delete and report as phishing.",
  "spam_verdict": "NOT_SPAM",
  "spam_confidence": 91,
  "spam_signals": [],
  "ml_classifier": {
    "status": "ok",
    "threat_type": "phishing",
    "threat_level": 2,
    "confidence": 0.92,
    "scores": {
      "legitimate": 0.01,
      "spam": 0.02,
      "phishing": 0.92,
      "spear_phishing": 0.03,
      "whaling": 0.02
    }
  },
  "indicators": ["spf_fail", "reply_to_mismatch", "url_shortener"],
  "urls_total": 3,
  "urls_flagged": 1,
  "ips_flagged": 0,
  "auth": {
    "spf": "fail",
    "dkim": "fail",
    "dmarc": "fail",
    "from_reply_to_mismatch": true
  }
}`}
            </CodeBlock>
          </Card>
        </Section>

      </div>
    </div>
  )
}
