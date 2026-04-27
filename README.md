# 🛡️ MailDefender

> **AI-powered phishing & spam email analysis platform** — self-hosted, zero external AI costs, production-deployed.

[![Live Demo](https://img.shields.io/badge/Live_Demo-maildefender.xyz-6366f1?style=for-the-badge&logo=vercel)](https://maildefender.xyz)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=for-the-badge&logo=react)](https://react.dev)
[![Ollama](https://img.shields.io/badge/AI-Ollama_Qwen2.5-black?style=for-the-badge)](https://ollama.com)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker)](https://docker.com)
[![License](https://img.shields.io/badge/License-MIT-22c55e?style=for-the-badge)](LICENSE)

---

## Overview

MailDefender is a full-stack email threat analysis platform built to demonstrate applied skills in **AI engineering**, **cybersecurity**, and **backend automation**. It analyzes raw emails in real time through a multi-layered pipeline: structural parsing, parallel threat intelligence lookups, and local LLM inference — all running on self-hosted infrastructure with no recurring AI API costs.

The platform is live at **[maildefender.xyz](https://maildefender.xyz)**.

**Key design decisions:**
- Replaced a cloud LLM (Groq / Llama 3.3 70B) with a **local Ollama model** (Qwen2.5 3B, Q4_K_M quantized) — eliminates token costs, keeps email data on-premises
- Built an **async SMTP pipeline** so users can forward emails and receive analysis replies automatically
- Exposed a **documented REST API** for third-party integration
- Engineered a **weighted risk scoring engine** that combines 13+ independent signals

---

## Features

| Feature | Description |
|---------|-------------|
| 📧 **Email ingestion** | Drag & drop `.eml` files or paste raw email text directly |
| 📨 **Email forwarding** | Forward any suspicious email to `scan@maildefender.xyz` — receive an HTML analysis report in your inbox |
| 🔍 **Header analysis** | SPF, DKIM, DMARC validation · From/Reply-To domain mismatch detection |
| 🌐 **URL scanning** | Extracts all URLs and checks them against VirusTotal in parallel |
| 🖥️ **IP reputation** | Validates sender IPs against VirusTotal and AbuseIPDB |
| 📎 **Attachment detection** | Flags 20+ suspicious file extensions (`.exe`, `.vbs`, `.docm`, etc.) |
| 🤖 **AI phishing analysis** | Local LLM classifies verdict, detects social engineering tactics, explains reasoning |
| 🚫 **AI spam analysis** | Independent spam classification with signal detection (tracking pixels, bulk headers, etc.) |
| 📊 **Risk scoring** | Weighted 0–100 score with itemized breakdown of every contributing signal |
| 🔌 **Public REST API** | Authenticated endpoint for programmatic email scanning |
| 📖 **API documentation** | Interactive Swagger UI + in-app docs with code examples |

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | React 18, Vite, Tailwind CSS | SPA with dark-theme results dashboard |
| **Backend** | Python 3.12, FastAPI, asyncio | REST API, async analysis pipeline |
| **Local AI** | Ollama, Qwen2.5 3B (Q4_K_M) | Phishing & spam classification — runs on CPU, no external API |
| **Email Inbound** | aiosmtpd | SMTP server for receiving forwarded emails |
| **Email Outbound** | aiosmtplib, Resend | Sending HTML analysis replies |
| **Threat Intel** | VirusTotal API | URL and IP maliciousness detection |
| **Threat Intel** | AbuseIPDB API | IP abuse history and reputation |
| **Threat Intel** | URLScan.io API | URL scanning and screenshots |
| **Proxy** | Nginx | Reverse proxy, SPA routing, request timeouts |
| **Containerization** | Docker, Docker Compose | Multi-service orchestration (Ollama + Backend + Frontend) |
| **Deployment** | Coolify, Hetzner VPS | Self-hosted PaaS with automatic SSL |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Frontend  (React + Vite)                    │
│  Drag & drop / paste / API Docs / animated progress bar         │
└───────────────────────────┬─────────────────────────────────────┘
                            │ HTTP  /analyze
                            │ HTTP  /api/v1/scan
┌───────────────────────────▼─────────────────────────────────────┐
│                    Backend  (FastAPI + Python)                   │
│                                                                  │
│  ┌─────────────────┐   ┌──────────────────────────────────────┐ │
│  │  SMTP Receiver  │   │         Analysis Pipeline            │ │
│  │  (aiosmtpd:25)  │──▶│                                      │ │
│  └─────────────────┘   │  1. Email Parser                     │ │
│                         │     headers · URLs · IPs · attachments│ │
│  ┌─────────────────┐   │                                      │ │
│  │  Email Sender   │   │  2. Parallel OSINT  (asyncio.gather) │ │
│  │  (aiosmtplib)   │◀──│     VirusTotal · AbuseIPDB · URLScan │ │
│  └─────────────────┘   │                                      │ │
│                         │  3. Local AI  (Ollama / Qwen2.5 3B)  │ │
│                         │     phishing verdict · spam verdict  │ │
│                         │     tactics · red flags · reasoning  │ │
│                         │                                      │ │
│                         │  4. Risk Scorer  (weighted 0–100)    │ │
│                         │     13+ signals · itemized breakdown │ │
│                         └──────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
          │                    │                   │
    VirusTotal            AbuseIPDB          Ollama (local)
    URLScan.io                               Qwen2.5 3B
```

### How the email forwarding pipeline works

```
User inbox
    │
    │  Forward suspicious email
    ▼
scan@maildefender.xyz  (port 25, aiosmtpd)
    │
    │  Extract original message
    ▼
Analysis Pipeline  (~25–60s on CPU)
    │
    │  HTML report email
    ▼
User inbox  ← analysis result with risk score, verdict, red flags
```

---

## Risk Scoring Engine

Every email is scored 0–100 using a weighted multi-signal system:

| Signal | Points |
|--------|--------|
| SPF fail | +20 |
| SPF softfail | +12 |
| DKIM fail | +15 |
| DMARC fail | +8 |
| From / Reply-To domain mismatch | +20 |
| Suspicious attachment | +15 (cap +25) |
| VirusTotal flagged URL | +20/URL (cap +40) |
| VirusTotal flagged IP | +10/IP (cap +20) |
| AbuseIPDB flagged IP | +10/IP (cap +20) |
| AI verdict PHISHING | +30 × confidence |
| AI verdict SUSPICIOUS | +15 × confidence |
| URL shortener detected | +5 (cap +10) |

| Score | Level | Color |
|-------|-------|-------|
| 0–19 | LOW | 🟢 Green |
| 20–44 | MEDIUM | 🟡 Yellow |
| 45–69 | HIGH | 🟠 Orange |
| 70–100 | CRITICAL | 🔴 Red |

---

## REST API

### Authentication

```http
X-API-Key: your_api_key
```

Set `PUBLIC_API_KEY` in environment variables to enable the endpoint.

### Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/health` | — | Service status and configured integrations |
| `POST` | `/api/v1/scan` | ✅ | Analyze a raw email, returns full threat report |
| `GET` | `/docs` | — | Interactive Swagger UI |
| `GET` | `/redoc` | — | ReDoc API reference |

### Scan request

```bash
curl -X POST https://maildefender.xyz/api/v1/scan \
  -H "X-API-Key: YOUR_KEY" \
  -F "raw_email=<suspicious.eml"
```

```python
import requests

with open("email.eml") as f:
    raw = f.read()

r = requests.post(
    "https://maildefender.xyz/api/v1/scan",
    headers={"X-API-Key": "YOUR_KEY"},
    data={"raw_email": raw},
)
result = r.json()
print(f"{result['level']} ({result['score']}/100) — {result['verdict']}")
```

### Sample response

```json
{
  "score": 78,
  "level": "CRITICAL",
  "verdict": "PHISHING",
  "confidence": 91,
  "reasoning": "This email impersonates a banking institution using a typosquatted domain and pressures the recipient to verify credentials within 24 hours. SPF and DMARC both fail, and the reply-to points to an unrelated domain.",
  "tactics": ["urgency", "impersonation", "brand_spoofing", "credential_harvesting"],
  "red_flags": [
    "SPF failure — sender not authorized for claimed domain",
    "From and Reply-To use different domains",
    "Link destination hidden behind URL shortener"
  ],
  "recommendation": "Do not click any links. Mark as phishing and delete.",
  "spam_verdict": "SPAM",
  "spam_confidence": 82,
  "spam_signals": ["bulk_headers", "tracking_pixel", "url_tracking"],
  "indicators": ["spf_fail", "domain_mismatch", "url_shortener_detected"],
  "urls_total": 3,
  "urls_flagged": 1,
  "ips_flagged": 0,
  "auth": {
    "spf": "fail",
    "dkim": "none",
    "dmarc": "fail",
    "from_reply_to_mismatch": true
  }
}
```

### Full response schema

| Field | Type | Description |
|-------|------|-------------|
| `score` | `int 0–100` | Overall risk score |
| `level` | `string` | `LOW` · `MEDIUM` · `HIGH` · `CRITICAL` |
| `verdict` | `string` | `SAFE` · `LIKELY_SAFE` · `SUSPICIOUS` · `PHISHING` |
| `confidence` | `int 0–100` | AI confidence in phishing verdict |
| `reasoning` | `string` | 2-sentence plain-English explanation |
| `tactics` | `string[]` | Detected social engineering tactics |
| `red_flags` | `string[]` | Specific suspicious elements |
| `recommendation` | `string` | Suggested user action |
| `spam_verdict` | `string` | `NOT_SPAM` · `LIKELY_SPAM` · `SPAM` |
| `spam_confidence` | `int 0–100` | AI confidence in spam verdict |
| `spam_signals` | `string[]` | Detected spam signals |
| `indicators` | `string[]` | Structural threat indicators |
| `urls_total` | `integer` | URLs extracted from the email |
| `urls_flagged` | `integer` | URLs flagged by VirusTotal |
| `ips_flagged` | `integer` | IPs flagged by VirusTotal or AbuseIPDB |
| `auth.spf` | `string` | `pass` · `fail` · `softfail` · `none` |
| `auth.dkim` | `string` | `pass` · `fail` · `none` |
| `auth.dmarc` | `string` | `pass` · `fail` · `none` |
| `auth.from_reply_to_mismatch` | `boolean` | From and Reply-To domains differ |

---

## Project Structure

```
phishguard/
├── backend/
│   ├── main.py                   # FastAPI app · lifespan · all endpoints
│   ├── email_receiver.py         # aiosmtpd SMTP server for inbound emails
│   ├── email_sender.py           # aiosmtplib HTML reply sender
│   ├── parsers/
│   │   └── email_parser.py       # RFC 5322 parsing · URL/IP extraction
│   ├── scanners/
│   │   ├── ai_analyzer.py        # Ollama / Qwen2.5 phishing + spam analysis
│   │   ├── virustotal.py         # VirusTotal URL & IP checks
│   │   ├── abuseipdb.py          # AbuseIPDB IP reputation
│   │   └── urlscan.py            # URLScan.io submission & polling
│   ├── scoring/
│   │   └── risk_score.py         # Weighted 0–100 risk engine
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.jsx               # Main app · scanner · API docs · footer
│   │   └── components/
│   │       ├── EmailUpload.jsx   # File upload + paste + progress bar
│   │       ├── RiskGauge.jsx     # Animated SVG score ring
│   │       ├── AiAnalysis.jsx    # Phishing + spam verdict cards
│   │       ├── ScoreBreakdown.jsx
│   │       ├── ThreatIndicators.jsx
│   │       ├── HeaderAnalysis.jsx
│   │       ├── UrlResults.jsx
│   │       ├── IpResults.jsx
│   │       └── ApiDocs.jsx       # In-app API documentation
│   ├── nginx.conf
│   └── Dockerfile
├── docker-compose.yml
├── docker-compose.yaml
└── .env.example
```

---

## Local Development

### Prerequisites

- Docker & Docker Compose
- 4 GB RAM minimum (model uses ~2 GB)

### 1. Clone

```bash
git clone https://github.com/JeffreyCq/phishguard.git
cd phishguard
```

### 2. Configure environment

```bash
cp .env.example .env
```

```env
# Required for AI analysis (auto-downloaded on first run)
OLLAMA_MODEL=qwen2.5:3b

# Optional — features degrade gracefully without these
VIRUSTOTAL_API_KEY=
ABUSEIPDB_API_KEY=
URLSCAN_API_KEY=

# Enables /api/v1/scan — generate with: openssl rand -hex 32
PUBLIC_API_KEY=

# Email forwarding (optional — requires Resend or any SMTP relay)
SMTP_HOST=smtp.resend.com
SMTP_PORT=587
SMTP_USER=resend
SMTP_PASSWORD=re_your_api_key
SMTP_FROM=scan@yourdomain.com
```

### 3. Run

```bash
docker compose up --build
```

| Service | URL |
|---------|-----|
| Web UI | http://localhost:3000 |
| API Docs (Swagger) | http://localhost:3000/docs |
| Health check | http://localhost:3000/health |

> **First run:** Ollama will download the Qwen2.5 3B model (~1.8 GB). This takes 2–5 minutes depending on your connection. The app starts immediately and the model is ready in the background.

---

## Deployment (Coolify)

1. Create a **Docker Compose** resource → point to this repo, branch `main`
2. Add environment variables in the Coolify UI
3. Set your domain on the **frontend** service (port 80)
4. Open port **25** on your VPS firewall for email inbound:
   ```bash
   ufw allow 25/tcp
   ```
5. Add an `MX` DNS record pointing your domain to your server IP
6. Hit **Deploy** — Coolify handles SSL via Let's Encrypt automatically

---

## API Keys

All integrations are optional. The platform degrades gracefully — AI analysis and header parsing work with no external keys.

| Service | Purpose | Free Tier |
|---------|---------|-----------|
| [VirusTotal](https://virustotal.com/gui/my-apikey) | URL & IP maliciousness | 4 req/min |
| [AbuseIPDB](https://abuseipdb.com/register) | IP abuse history | 1,000 req/day |
| [URLScan.io](https://urlscan.io/user/signup) | URL scanning & screenshots | 100 req/day |
| [Resend](https://resend.com) | Outbound email (replies) | 3,000 emails/month |

---

## AI Model

The platform uses **Qwen2.5 3B Instruct** (Q4_K_M quantization) running locally via Ollama.

| Property | Value |
|----------|-------|
| Model | Qwen2.5 3B Instruct |
| Quantization | Q4_K_M (4-bit) |
| Size on disk | ~1.8 GB |
| RAM usage | ~2 GB |
| Inference (CPU) | 25–60s depending on email length |
| Context window | 2,048 tokens (optimized from 32,768) |
| External API calls | None — fully local |

**Why a local model?**
Running inference locally eliminates token costs, keeps potentially sensitive email content off third-party infrastructure, and demonstrates practical LLM deployment skills — not just API consumption.

---

## Engineering Highlights

- **Async parallel execution** — `asyncio.gather()` runs VirusTotal, AbuseIPDB, and Ollama concurrently, minimizing total latency
- **Graceful degradation** — every external integration is optional; missing API keys are handled without crashes
- **SMTP pipeline** — `aiosmtpd` runs in its own thread, scheduling analysis coroutines on the FastAPI event loop via `run_coroutine_threadsafe`
- **Model warm-up** — Ollama model is pre-loaded into RAM at startup via a dummy inference call, eliminating cold-start latency for real requests
- **Inference optimization** — `num_ctx: 2048` instead of model default (32,768) reduces KV cache size and speeds up CPU inference by ~50%
- **Email extraction** — inbound forwarded emails are unwrapped from their `message/rfc822` attachment when present, so the original phishing email (not the forwarding wrapper) is analyzed

---

## Built By

**Jeffrey A. Cedeno Q.**
AI · Cybersecurity · Full-Stack Engineering · Support Engineering · Automation

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-0077B5?style=flat&logo=linkedin)](https://linkedin.com)
[![GitHub](https://img.shields.io/badge/GitHub-JeffreyCq-181717?style=flat&logo=github)](https://github.com/JeffreyCq)

---

## License

MIT — free to use, modify, and deploy.
