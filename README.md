# 🛡️ MailDefender

> **AI-powered phishing & spam email analysis platform** — self-hosted, zero external AI costs, production-deployed.

[![Live Demo](https://img.shields.io/badge/Live_Demo-maildefender.xyz-6366f1?style=for-the-badge&logo=vercel)](https://maildefender.xyz)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=for-the-badge&logo=react)](https://react.dev)
[![DistilBERT](https://img.shields.io/badge/ML-DistilBERT%2FONNX-7c3aed?style=for-the-badge)](https://github.com/JeffreyCq/maildefender-ml)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker)](https://docker.com)
[![License](https://img.shields.io/badge/License-MIT-22c55e?style=for-the-badge)](LICENSE)

---

## Overview

MailDefender is a full-stack email threat analysis platform built to demonstrate applied skills in **AI/ML engineering**, **cybersecurity**, and **backend automation**. It analyzes raw emails in real time through a multi-layered pipeline: structural parsing, parallel threat intelligence lookups, and a **custom-trained NLP classifier** — all running on self-hosted infrastructure with no recurring AI API costs.

The platform is live at **[maildefender.xyz](https://maildefender.xyz)**.

**Key design decisions:**
- Built and trained a **custom DistilBERT model** fine-tuned on email threat data, exported to ONNX and deployed as an independent microservice (`ml.maildefender.xyz`) — eliminates token costs, keeps email data on-premises, sub-second inference
- The ML model classifies emails into **5 threat categories**: `legitimate`, `spam`, `phishing`, `spear_phishing`, `whaling`
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
| 🤖 **ML phishing analysis** | Custom DistilBERT classifier detects 5 threat classes, extracts tactics and red flags |
| 🚫 **ML spam analysis** | Independent spam classification with signal detection (tracking pixels, bulk headers, etc.) |
| 📊 **Risk scoring** | Weighted 0–100 score with itemized breakdown of every contributing signal |
| 🔌 **Public REST API** | Authenticated endpoint for programmatic email scanning |
| 📖 **API documentation** | Interactive Swagger UI + in-app docs with code examples |

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | React 18, Vite, Tailwind CSS | SPA with dark-theme results dashboard |
| **Backend** | Python 3.12, FastAPI, asyncio | REST API, async analysis pipeline |
| **ML Classifier** | DistilBERT, ONNX Runtime, HuggingFace | Custom-trained phishing/spam NLP model — self-hosted microservice |
| **Email Inbound** | aiosmtpd | SMTP server for receiving forwarded emails |
| **Email Outbound** | aiosmtplib, Resend | Sending HTML analysis replies |
| **Threat Intel** | VirusTotal API | URL and IP maliciousness detection |
| **Threat Intel** | AbuseIPDB API | IP abuse history and reputation |
| **Threat Intel** | URLScan.io API | URL scanning and screenshots |
| **Proxy** | Nginx | Reverse proxy, SPA routing, request timeouts |
| **Containerization** | Docker, Docker Compose | Two-service stack (Backend + Frontend) |
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
│                         │  3. ML Classifier  (DistilBERT/ONNX) │ │
│                         │     5 threat classes · phishing      │ │
│                         │     verdict · spam verdict · tactics │ │
│                         │                                      │ │
│                         │  4. Risk Scorer  (weighted 0–100)    │ │
│                         │     13+ signals · itemized breakdown │ │
│                         └──────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
          │                    │                    │
    VirusTotal            AbuseIPDB         ml.maildefender.xyz
    URLScan.io                              DistilBERT / ONNX
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
Analysis Pipeline  (~1–3s with DistilBERT microservice)
    │
    │  HTML report email
    ▼
User inbox  ← risk score, verdict, red flags, recommendation
```

---

## ML Classifier

The AI core is a **custom DistilBERT model** fine-tuned on email threat data, exported to ONNX, and deployed as a standalone microservice at `ml.maildefender.xyz`. Source: [JeffreyCq/maildefender-ml](https://github.com/JeffreyCq/maildefender-ml).

### Threat classes

| Class | Level | Description |
|-------|-------|-------------|
| `legitimate` | 0 | Normal correspondence — no threat indicators |
| `spam` | 1 | Unsolicited bulk email — no direct malicious intent |
| `phishing` | 2 | Credential harvesting or malicious link delivery |
| `spear_phishing` | 3 | Targeted attack with personalization based on prior reconnaissance |
| `whaling` | 4 | High-value target attack — executive or finance profile |

### Model properties

| Property | Value |
|----------|-------|
| Architecture | DistilBERT (distilbert-base-uncased) |
| Export format | ONNX (quantized) |
| Inference | ~100–300 ms on CPU |
| Classes | 5 (legitimate, spam, phishing, spear_phishing, whaling) |
| External API calls | None — fully self-hosted |
| Source repo | [JeffreyCq/maildefender-ml](https://github.com/JeffreyCq/maildefender-ml) |

### Verdict mapping

The raw class and confidence score are mapped to human-readable verdicts:

| ML Class | Condition | Phishing Verdict |
|----------|-----------|-----------------|
| `whaling` or `spear_phishing` | — | `PHISHING` |
| `phishing` | confidence ≥ 65% | `PHISHING` |
| `phishing` | confidence < 65% | `SUSPICIOUS` |
| `spam` | combined phishing scores > 30% | `SUSPICIOUS` |
| `spam` | combined phishing scores ≤ 30% | `LIKELY_SAFE` |
| `legitimate` | confidence ≥ 80% | `SAFE` |
| `legitimate` | confidence < 80% | `LIKELY_SAFE` |

**Why DistilBERT over a generative LLM?**
A generative model (Ollama/Qwen) needs ~2 GB RAM and 25–60s per inference on CPU. The ONNX-quantized DistilBERT classifier uses ~200 MB and responds in under a second — without sacrificing detection accuracy for the classification task.

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
| ML verdict PHISHING | +30 × confidence |
| ML verdict SUSPICIOUS | +15 × confidence |
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
| `GET` | `/health` | — | Service status, ML microservice URL, configured integrations |
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
# Access raw ML scores
ml = result["ml_classifier"]
print(f"ML class: {ml['threat_type']} (level {ml['threat_level']})")
```

### Sample response

```json
{
  "score": 78,
  "level": "CRITICAL",
  "verdict": "PHISHING",
  "confidence": 92,
  "reasoning": "This email exhibits strong indicators of a phishing attempt. The sender identity, subject line, and content patterns match known phishing templates.",
  "tactics": ["urgency", "impersonation", "credential_harvesting", "url_obfuscation"],
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
}
```

### Full response schema

| Field | Type | Description |
|-------|------|-------------|
| `score` | `int 0–100` | Overall risk score |
| `level` | `string` | `LOW` · `MEDIUM` · `HIGH` · `CRITICAL` |
| `verdict` | `string` | `SAFE` · `LIKELY_SAFE` · `SUSPICIOUS` · `PHISHING` |
| `confidence` | `int 0–100` | ML confidence in phishing verdict |
| `reasoning` | `string` | Plain-English explanation of classification |
| `tactics` | `string[]` | Detected social engineering tactics |
| `red_flags` | `string[]` | Specific suspicious elements |
| `recommendation` | `string` | Suggested user action |
| `spam_verdict` | `string` | `NOT_SPAM` · `LIKELY_SPAM` · `SPAM` |
| `spam_confidence` | `int 0–100` | ML confidence in spam verdict |
| `spam_signals` | `string[]` | Detected spam signals |
| `ml_classifier.threat_type` | `string` | Raw ML class: `legitimate` · `spam` · `phishing` · `spear_phishing` · `whaling` |
| `ml_classifier.threat_level` | `int 0–4` | Numeric severity level |
| `ml_classifier.confidence` | `float 0–1` | Raw probability of predicted class |
| `ml_classifier.scores` | `object` | Per-class probabilities for all 5 categories |
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
│   │   ├── ai_analyzer.py        # DistilBERT microservice client · verdict mapping
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
│   │       ├── EmailUpload.jsx   # File upload + paste + animated progress bar
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
- ML microservice running (or point `ML_SERVICE_URL` to `https://ml.maildefender.xyz`)

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
# ML Classifier microservice (use the hosted instance or run maildefender-ml locally)
ML_SERVICE_URL=https://ml.maildefender.xyz

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
| API Docs (Swagger) | http://localhost:8000/docs |
| Health check | http://localhost:8000/health |

> **Note:** The ML microservice runs separately. By default it points to `https://ml.maildefender.xyz`. To run it locally, see [maildefender-ml](https://github.com/JeffreyCq/maildefender-ml).

---

## Deployment (Coolify)

1. Create a **Docker Compose** resource → point to this repo, branch `main`
2. Add environment variables in the Coolify UI
3. Set your domain on the **frontend** service (port 80)
4. Open port **25** on your VPS firewall for email inbound:
   ```bash
   ufw allow 25/tcp
   ```
5. Add an `MX` DNS record pointing your domain to your server hostname
6. Hit **Deploy** — Coolify handles SSL via Let's Encrypt automatically

---

## API Keys

All integrations are optional. The platform degrades gracefully — ML analysis and header parsing work with no external keys.

| Service | Purpose | Free Tier |
|---------|---------|-----------|
| [VirusTotal](https://virustotal.com/gui/my-apikey) | URL & IP maliciousness | 4 req/min |
| [AbuseIPDB](https://abuseipdb.com/register) | IP abuse history | 1,000 req/day |
| [URLScan.io](https://urlscan.io/user/signup) | URL scanning & screenshots | 100 req/day |
| [Resend](https://resend.com) | Outbound email (replies) | 3,000 emails/month |

---

## Engineering Highlights

- **Custom ML model** — fine-tuned DistilBERT on email threat data, ONNX-exported for fast CPU inference, deployed as a standalone microservice; avoids the 2 GB RAM overhead and 25–60s latency of a generative LLM
- **Async parallel execution** — `asyncio.gather()` runs VirusTotal, AbuseIPDB, and the ML classifier concurrently, minimizing total pipeline latency
- **Graceful degradation** — every external integration is optional; missing API keys are handled without crashes
- **SMTP pipeline** — `aiosmtpd` runs in its own thread, scheduling analysis coroutines on the FastAPI event loop via `run_coroutine_threadsafe`
- **Email extraction** — inbound forwarded emails are unwrapped from their `message/rfc822` attachment when present, so the original phishing email (not the forwarding wrapper) is analyzed
- **Rule-based enrichment** — tactics, red flags, and spam signals are derived post-classification from header metadata and body heuristics, adding explainability on top of the ML output

---

## Built By

**Jeffrey A. Cedeno Q.**  
AI Enthusiast · Cybersec Engineer · Support Engineering · Automation

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-0077B5?style=flat&logo=linkedin)](https://linkedin.com)
[![GitHub](https://img.shields.io/badge/GitHub-JeffreyCq-181717?style=flat&logo=github)](https://github.com/JeffreyCq)

---

## License

MIT — free to use, modify, and deploy.
