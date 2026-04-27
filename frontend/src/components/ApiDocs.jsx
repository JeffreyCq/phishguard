import { Terminal, Mail, Key, Zap, Shield, Globe, Server, Brain, ChevronRight } from 'lucide-react'

// ── Reusable primitives ──────────────────────────────────────────────────────

function Badge({ children, color = 'indigo' }) {
  const classes = {
    indigo: 'bg-indigo-500/15 text-indigo-300 border-indigo-500/30',
    green:  'bg-green-500/15  text-green-300  border-green-500/30',
    yellow: 'bg-yellow-500/15 text-yellow-300 border-yellow-500/30',
    red:    'bg-red-500/15    text-red-300    border-red-500/30',
    slate:  'bg-slate-700     text-slate-300  border-slate-600',
  }
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-mono border ${classes[color]}`}>
      {children}
    </span>
  )
}

function Method({ verb }) {
  const colors = { POST: 'bg-blue-600', GET: 'bg-green-600' }
  return (
    <span className={`${colors[verb] ?? 'bg-slate-600'} text-white text-xs font-bold px-2 py-0.5 rounded font-mono`}>
      {verb}
    </span>
  )
}

function CodeBlock({ children, lang = 'bash' }) {
  return (
    <pre className="mt-2 bg-slate-950 border border-slate-800 rounded-lg p-4 text-xs text-slate-300 font-mono overflow-x-auto leading-relaxed">
      {children}
    </pre>
  )
}

function Section({ id, icon: Icon, title, children }) {
  return (
    <section id={id} className="scroll-mt-20">
      <div className="flex items-center gap-2.5 mb-4">
        <div className="w-7 h-7 rounded-lg bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center shrink-0">
          <Icon className="w-3.5 h-3.5 text-indigo-400" />
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

export default function ApiDocs({ scanAddress }) {
  const address = scanAddress || 'scan@maildefender.xyz'

  const navItems = [
    { id: 'overview',    label: 'Overview' },
    { id: 'auth',        label: 'Authentication' },
    { id: 'endpoints',   label: 'Endpoints' },
    { id: 'response',    label: 'Response Schema' },
    { id: 'email',       label: 'Email Forwarding' },
    { id: 'examples',    label: 'Code Examples' },
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
              <strong className="text-white">MailDefender</strong> is an AI-powered phishing
              detection service. It analyzes raw emails using a{' '}
              <strong className="text-indigo-300">local Ollama model</strong> (no external token
              costs) combined with real-time threat intelligence from VirusTotal and AbuseIPDB.
            </p>
            <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 gap-3">
              {[
                { icon: Brain,    label: 'Local AI',       desc: 'qwen2.5:3b via Ollama — runs on your infra' },
                { icon: Shield,   label: 'Threat Intel',   desc: 'VirusTotal URL & IP checks + AbuseIPDB' },
                { icon: Mail,     label: 'Email Forward',  desc: `Forward to ${address} — get instant reply` },
                { icon: Terminal, label: 'REST API',       desc: 'Integrate phishing detection in your apps' },
              ].map(({ icon: Icon, label, desc }) => (
                <div key={label} className="flex items-start gap-3 p-3 rounded-lg bg-slate-950/50 border border-slate-800">
                  <Icon className="w-4 h-4 text-indigo-400 mt-0.5 shrink-0" />
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

        {/* Authentication */}
        <Section id="auth" icon={Key} title="Authentication">
          <Card>
            <p className="text-sm text-slate-300 leading-relaxed mb-4">
              The <code className="text-indigo-300">/api/v1/scan</code> endpoint requires an API
              key. Pass it in the <code className="text-yellow-300">X-API-Key</code> request header.
              The web UI (<code className="text-indigo-300">/analyze</code>) has no authentication.
            </p>
            <CodeBlock>
{`curl -X POST https://maildefender.xyz/api/v1/scan \\
  -H "X-API-Key: YOUR_API_KEY" \\
  -F "raw_email=<email.txt"`}
            </CodeBlock>
            <div className="mt-4 p-3 rounded-lg bg-yellow-500/5 border border-yellow-500/20">
              <p className="text-xs text-yellow-300">
                <strong>Setup:</strong> Set the <code>PUBLIC_API_KEY</code> environment variable on
                the server to any random secret string. If not set, the endpoint returns 503.
              </p>
            </div>
          </Card>
        </Section>

        {/* Endpoints */}
        <Section id="endpoints" icon={Zap} title="Endpoints">
          <Card>
            <EndpointRow
              method="GET"
              path="/health"
              description="Returns service status and which integrations are configured."
            />
            <EndpointRow
              method="POST"
              path="/api/v1/scan"
              auth
              description="Analyze a raw email. Returns full threat report with risk score, AI verdict, and indicators."
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
  "ai_model": "qwen2.5:3b",
  "ai_backend": "ollama (local)",
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
                    <th className="pb-2 text-xs text-slate-500 uppercase tracking-wide w-36">Field</th>
                    <th className="pb-2 text-xs text-slate-500 uppercase tracking-wide w-24">Type</th>
                    <th className="pb-2 text-xs text-slate-500 uppercase tracking-wide">Description</th>
                  </tr>
                </thead>
                <tbody>
                  <ResponseField field="score"          type="int 0–100" description="Overall risk score. Higher = more dangerous." />
                  <ResponseField field="level"          type="string"    description="LOW · MEDIUM · HIGH · CRITICAL" />
                  <ResponseField field="verdict"        type="string"    description="SAFE · LIKELY_SAFE · SUSPICIOUS · PHISHING" />
                  <ResponseField field="confidence"     type="int 0–100" description="AI confidence in the verdict." />
                  <ResponseField field="reasoning"      type="string"    description="2–3 sentence plain-English explanation from the AI." />
                  <ResponseField field="tactics"        type="string[]"  description="Detected social engineering tactics (e.g. urgency, impersonation, brand_spoofing)." />
                  <ResponseField field="red_flags"      type="string[]"  description="Specific suspicious elements identified by the AI." />
                  <ResponseField field="recommendation" type="string"    description="Suggested action for the end user." />
                  <ResponseField field="indicators"     type="string[]"  description="Structural threat indicators: SPF/DKIM/DMARC failures, domain mismatches, URL shorteners." />
                  <ResponseField field="urls_total"     type="integer"   description="Total URLs extracted from the email." />
                  <ResponseField field="urls_flagged"   type="integer"   description="URLs flagged as malicious by VirusTotal." />
                  <ResponseField field="ips_flagged"    type="integer"   description="Sender IPs flagged by VirusTotal or AbuseIPDB." />
                  <ResponseField field="auth.spf"       type="string"    description="SPF result: pass · fail · softfail · none" />
                  <ResponseField field="auth.dkim"      type="string"    description="DKIM result: pass · fail · none" />
                  <ResponseField field="auth.dmarc"     type="string"    description="DMARC result: pass · fail · none" />
                  <ResponseField field="auth.from_reply_to_mismatch" type="boolean" description="true if From and Reply-To use different domains." />
                  <tr><td colSpan={3} className="pt-4 pb-1"><p className="text-xs text-slate-500 uppercase tracking-wide">Spam Analysis</p></td></tr>
                  <ResponseField field="spam_verdict"    type="string"   description="SPAM · LIKELY_SPAM · NOT_SPAM — independent from phishing verdict." />
                  <ResponseField field="spam_confidence" type="int 0–100" description="AI confidence in the spam verdict." />
                  <ResponseField field="spam_signals"    type="string[]" description="Detected spam signals: bulk_headers, tracking_pixel, mass_marketing_platform, unsubscribe_link, promotional_language, generic_greeting, unsolicited_contact, url_tracking, suspicious_sender_domain, excessive_images." />
                </tbody>
              </table>
            </div>
          </Card>

          {/* Verdict/Level values */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Card>
              <p className="text-xs text-slate-500 uppercase tracking-wide mb-3">Risk Levels</p>
              <div className="space-y-2 text-sm">
                {[
                  { val: 'LOW',      range: '0–19',  color: 'green'  },
                  { val: 'MEDIUM',   range: '20–44', color: 'yellow' },
                  { val: 'HIGH',     range: '45–69', color: 'yellow' },
                  { val: 'CRITICAL', range: '70–100',color: 'red'    },
                ].map(({ val, range, color }) => (
                  <div key={val} className="flex items-center justify-between">
                    <Badge color={color}>{val}</Badge>
                    <span className="text-slate-500 font-mono text-xs">score {range}</span>
                  </div>
                ))}
              </div>
            </Card>
            <Card>
              <p className="text-xs text-slate-500 uppercase tracking-wide mb-3">Detectable Tactics</p>
              <div className="flex flex-wrap gap-1.5">
                {['urgency','fear','impersonation','credential_harvesting','brand_spoofing',
                  'prize_scam','invoice_fraud','malware_delivery','url_obfuscation','authority'
                ].map(t => (
                  <Badge key={t} color="slate">{t}</Badge>
                ))}
              </div>
            </Card>
          </div>
        </Section>

        {/* Email Forwarding */}
        <Section id="email" icon={Mail} title="Email Forwarding">
          <Card>
            <p className="text-sm text-slate-300 leading-relaxed mb-4">
              The easiest way to use MailDefender. Forward any suspicious email to{' '}
              <strong className="text-indigo-300">{address}</strong> and you will receive an
              HTML report directly in your inbox within seconds.
            </p>
            <div className="space-y-4">
              {[
                { step: '1', title: 'Forward the email', desc: `In your email client, use "Forward" on the suspicious email and send it to ${address}.` },
                { step: '2', title: 'Wait a few seconds', desc: 'MailDefender receives it, runs the full analysis pipeline (AI + threat intel), and generates your report.' },
                { step: '3', title: 'Check your inbox', desc: 'You receive an HTML email with the risk level, AI verdict, detected tactics, red flags, and a recommendation.' },
              ].map(({ step, title, desc }) => (
                <div key={step} className="flex gap-3">
                  <div className="w-6 h-6 rounded-full bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center shrink-0 mt-0.5">
                    <span className="text-xs text-indigo-400 font-bold">{step}</span>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-slate-200">{title}</p>
                    <p className="text-sm text-slate-400 mt-0.5">{desc}</p>
                  </div>
                </div>
              ))}
            </div>
            <div className="mt-5 p-3 rounded-lg bg-slate-950/60 border border-slate-800">
              <p className="text-xs text-slate-500 uppercase tracking-wide mb-2">SMTP Setup (self-hosting)</p>
              <div className="space-y-1 text-xs font-mono text-slate-400">
                <div><span className="text-slate-600">SMTP_HOST=</span><span className="text-green-400">smtp.resend.com</span></div>
                <div><span className="text-slate-600">SMTP_PORT=</span><span className="text-green-400">587</span></div>
                <div><span className="text-slate-600">SMTP_USER=</span><span className="text-green-400">resend</span></div>
                <div><span className="text-slate-600">SMTP_PASSWORD=</span><span className="text-green-400">re_your_api_key</span></div>
                <div><span className="text-slate-600">SMTP_FROM=</span><span className="text-green-400">scan@maildefender.xyz</span></div>
              </div>
            </div>
          </Card>
        </Section>

        {/* Code Examples */}
        <Section id="examples" icon={Globe} title="Code Examples">
          {/* curl */}
          <Card>
            <p className="text-sm font-medium text-slate-200 mb-1">curl</p>
            <CodeBlock>
{`# Analyze a saved .eml file
curl -X POST https://maildefender.xyz/api/v1/scan \\
  -H "X-API-Key: YOUR_API_KEY" \\
  -F "raw_email=<suspicious.eml"

# Paste raw email inline
curl -X POST https://maildefender.xyz/api/v1/scan \\
  -H "X-API-Key: YOUR_API_KEY" \\
  -F 'raw_email=From: attacker@evil.com
To: victim@company.com
Subject: Urgent: Verify your account

Click here: http://phishing-site.com'`}
            </CodeBlock>
          </Card>

          {/* Python */}
          <Card>
            <p className="text-sm font-medium text-slate-200 mb-1">Python</p>
            <CodeBlock lang="python">
{`import requests

with open("suspicious.eml", "r") as f:
    raw_email = f.read()

response = requests.post(
    "https://maildefender.xyz/api/v1/scan",
    headers={"X-API-Key": "YOUR_API_KEY"},
    data={"raw_email": raw_email},
)

result = response.json()
print(f"Risk: {result['level']} ({result['score']}/100)")
print(f"Verdict: {result['verdict']} — {result['confidence']}% confidence")
print(f"Reasoning: {result['reasoning']}")
if result["tactics"]:
    print(f"Tactics: {', '.join(result['tactics'])}")`}
            </CodeBlock>
          </Card>

          {/* JavaScript */}
          <Card>
            <p className="text-sm font-medium text-slate-200 mb-1">JavaScript / Node.js</p>
            <CodeBlock lang="javascript">
{`const form = new FormData();
form.append('raw_email', rawEmailString);

const res = await fetch('https://maildefender.xyz/api/v1/scan', {
  method: 'POST',
  headers: { 'X-API-Key': 'YOUR_API_KEY' },
  body: form,
});

const { score, level, verdict, reasoning, tactics } = await res.json();
console.log(\`\${level} (\${score}/100) — \${verdict}\`);`}
            </CodeBlock>
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
  "reasoning": "This email impersonates a banking institution and uses urgency to pressure the recipient into clicking a suspicious link. The From domain does not match the claimed sender and SPF authentication failed.",
  "tactics": ["impersonation", "urgency", "brand_spoofing", "credential_harvesting"],
  "red_flags": [
    "SPF failure — sender not authorized for claimed domain",
    "From domain 'bank-secure-login.com' does not match 'mybank.com'",
    "Link destination hidden behind URL shortener"
  ],
  "recommendation": "Do not click any links — mark as phishing and report to your IT team.",
  "indicators": ["spf_fail", "domain_mismatch", "url_shortener_detected"],
  "urls_total": 3,
  "urls_flagged": 1,
  "ips_flagged": 0,
  "auth": {
    "spf": "fail",
    "dkim": "none",
    "dmarc": "fail",
    "from_reply_to_mismatch": true
  },
  "spam_verdict": "SPAM",
  "spam_confidence": 78,
  "spam_signals": ["bulk_headers", "tracking_pixel", "url_tracking", "unsubscribe_link"]
}`}
            </CodeBlock>
          </Card>
        </Section>

      </div>
    </div>
  )
}
