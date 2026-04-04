# 🛡️ MailDefender

**AI-powered phishing email analyzer.** Upload or paste any email and get an instant threat report powered by Groq (Llama 3.3 70B) and OSINT APIs.

![Risk Score](https://img.shields.io/badge/Risk_Score-0--100-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi)
![React](https://img.shields.io/badge/React-18-61DAFB?logo=react)
![Groq](https://img.shields.io/badge/AI-Groq_Llama_3.3_70B-orange)
![License](https://img.shields.io/badge/License-MIT-green)

---

## ✨ Features

- 📧 **Email upload** — drag & drop `.eml` files or paste raw email text
- 🔍 **Header analysis** — SPF, DKIM, DMARC validation + From/Reply-To mismatch detection
- 🌐 **URL scanning** — extracts all URLs and checks them against VirusTotal
- 🖥️ **IP reputation** — checks sender IPs against VirusTotal & AbuseIPDB
- 📎 **Attachment detection** — flags suspicious file types (`.exe`, `.vbs`, `.docm`, etc.)
- 🤖 **AI analysis** — Groq (Llama 3.3 70B) identifies social engineering tactics, red flags and gives a plain-English verdict
- 📊 **Risk score** — weighted 0–100 score with breakdown of every contributing signal
- 🔌 **Public REST API** — let your apps scan emails programmatically via `/api/v1/scan`

---

## 🖼️ Screenshots

> Upload screen, Risk gauge, AI Analysis, Header Analysis tabs.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────┐
│            Frontend (React + Vite)          │
│  • Drag & drop / paste email                │
│  • Risk gauge, tabbed results dashboard     │
└──────────────────┬──────────────────────────┘
                   │ REST API
┌──────────────────▼──────────────────────────┐
│           Backend (Python + FastAPI)        │
│  1. Email Parser  → headers, URLs, IPs      │
│  2. OSINT checks  → parallel API calls      │
│  3. AI Analysis   → Groq Llama 3.3 70B      │
│  4. Risk Scorer   → weighted 0–100 score    │
└───┬──────────┬──────────┬────────┬──────────┘
    │          │          │        │
VirusTotal URLScan.io AbuseIPDB  Groq API
```

---

## 🚀 Getting Started

### Prerequisites

- Docker & Docker Compose
- API keys (see [API Keys](#-api-keys) below)

### 1. Clone the repo

```bash
git clone https://github.com/JeffreyCq/phishguard.git
cd phishguard
```

### 2. Configure environment

```bash
cp .env.example .env
```

Edit `.env` and fill in your API keys:

```env
GROQ_API_KEY=your_groq_key_here
VIRUSTOTAL_API_KEY=your_virustotal_key_here
URLSCAN_API_KEY=your_urlscan_key_here
ABUSEIPDB_API_KEY=your_abuseipdb_key_here
PUBLIC_API_KEY=your_random_secret_here
```

### 3. Run with Docker

```bash
docker-compose up --build
```

| Service  | URL |
|----------|-----|
| Web UI   | http://localhost:3000 |
| API Docs | http://localhost:3000/docs |

### Run without Docker

**Backend:**
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

---

## 🔑 API Keys

All keys are **optional** — the app works without them but with reduced accuracy. Keys with a free tier:

| Service | Purpose | Free Tier | Link |
|---------|---------|-----------|------|
| **Groq** | AI analysis (required for AI) | ✅ Generous free tier | [console.groq.com](https://console.groq.com) |
| **VirusTotal** | URL & IP reputation | ✅ 4 req/min | [virustotal.com](https://www.virustotal.com/gui/my-apikey) |
| **URLScan.io** | URL scanning | ✅ 100 req/day | [urlscan.io](https://urlscan.io/user/signup) |
| **AbuseIPDB** | IP abuse reports | ✅ 1000 req/day | [abuseipdb.com](https://www.abuseipdb.com/register) |

---

## 🔌 Public API

MailDefender exposes a REST API so you can integrate email scanning into your own apps.

### Authentication

Pass your API key in the `X-API-Key` header on every request.

### Scan an email

```http
POST /api/v1/scan
X-API-Key: your_api_key
Content-Type: multipart/form-data

raw_email=<full raw email content>
```

**cURL example:**
```bash
curl -X POST https://maildefender.xyz/api/v1/scan \
  -H "X-API-Key: your_api_key" \
  -F "raw_email=$(cat your_email.eml)"
```

**Python example:**
```python
import requests

with open("email.eml") as f:
    raw = f.read()

response = requests.post(
    "https://maildefender.xyz/api/v1/scan",
    headers={"X-API-Key": "your_api_key"},
    data={"raw_email": raw}
)

result = response.json()
print(f"Score: {result['score']} | Verdict: {result['verdict']}")
```

### Response

```json
{
  "score": 87,
  "level": "CRITICAL",
  "verdict": "PHISHING",
  "confidence": 94,
  "reasoning": "This email impersonates PayPal using a typosquatted domain and pressures the user to act within 24 hours under threat of account closure.",
  "tactics": ["urgency", "brand_spoofing", "fear"],
  "red_flags": [
    "Sender domain paypa1-verify.com is not affiliated with PayPal",
    "Reply-To points to a .ru domain",
    "SPF, DKIM and DMARC all fail"
  ],
  "recommendation": "Do not click any links. Delete this email and report it as phishing.",
  "indicators": [
    { "severity": "high", "type": "auth", "message": "SPF check failed" },
    { "severity": "high", "type": "spoofing", "message": "Reply-To domain differs from From domain" }
  ],
  "urls_total": 3,
  "urls_flagged": 2,
  "ips_flagged": 1,
  "auth": {
    "spf": "fail",
    "dkim": "fail",
    "dmarc": "fail",
    "from_reply_to_mismatch": true
  }
}
```

### Response fields

| Field | Type | Description |
|-------|------|-------------|
| `score` | `integer` | Risk score from 0 (safe) to 100 (critical) |
| `level` | `string` | `LOW` · `MEDIUM` · `HIGH` · `CRITICAL` |
| `verdict` | `string` | `SAFE` · `LIKELY_SAFE` · `SUSPICIOUS` · `PHISHING` |
| `confidence` | `integer` | AI confidence 0–100 |
| `reasoning` | `string` | Plain-English explanation |
| `tactics` | `string[]` | Social engineering tactics detected |
| `red_flags` | `string[]` | Specific concerning elements |
| `recommendation` | `string` | Suggested action for the end user |
| `indicators` | `object[]` | Structural indicators (SPF/DKIM/auth failures, etc.) |
| `urls_total` | `integer` | Number of URLs found in the email |
| `urls_flagged` | `integer` | URLs flagged as malicious by VirusTotal |
| `ips_flagged` | `integer` | IPs flagged by AbuseIPDB or VirusTotal |
| `auth.spf` | `string` | SPF result: `pass` · `fail` · `softfail` · `none` |
| `auth.dkim` | `string` | DKIM result: `pass` · `fail` · `none` |
| `auth.dmarc` | `string` | DMARC result: `pass` · `fail` · `none` |
| `auth.from_reply_to_mismatch` | `boolean` | True if From and Reply-To domains differ |

### Interactive docs

Full Swagger UI available at:
```
https://maildefender.xyz/docs
```

---

## 🧰 Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, Vite, Tailwind CSS |
| Backend | Python 3.12, FastAPI, asyncio |
| AI | Groq API — Llama 3.3 70B Versatile |
| OSINT | VirusTotal, URLScan.io, AbuseIPDB |
| Deployment | Docker, Docker Compose, Coolify |
| Proxy | Nginx |

---

## 📁 Project Structure

```
maildefender/
├── backend/
│   ├── main.py                  # FastAPI app, all endpoints
│   ├── parsers/
│   │   └── email_parser.py      # EML parsing, URL/IP extraction
│   ├── scanners/
│   │   ├── virustotal.py        # VirusTotal URL & IP checks
│   │   ├── urlscan.py           # URLScan.io submission
│   │   ├── abuseipdb.py         # AbuseIPDB IP reputation
│   │   └── ai_analyzer.py       # Groq AI analysis
│   ├── scoring/
│   │   └── risk_score.py        # Weighted 0–100 risk engine
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.jsx              # Main UI, tabbed results
│   │   └── components/
│   │       ├── EmailUpload.jsx  # Drag & drop + paste input
│   │       ├── RiskGauge.jsx    # Animated SVG score ring
│   │       ├── ThreatIndicators.jsx
│   │       ├── HeaderAnalysis.jsx
│   │       ├── UrlResults.jsx
│   │       ├── IpResults.jsx
│   │       ├── AiAnalysis.jsx
│   │       └── ScoreBreakdown.jsx
│   ├── nginx.conf
│   └── Dockerfile
├── docker-compose.yml
└── .env.example
```

---

## ☁️ Deploy on Coolify

1. Create a new **Docker Compose** resource in Coolify
2. Point it to this repo, branch `main`
3. Add your environment variables in the Coolify UI
4. Set your domain on the **frontend** service (port `80`)
5. Hit **Deploy**

Coolify handles SSL automatically via Let's Encrypt.

---

## 📄 License

MIT — free to use, modify and deploy.
