# MailDefender

Paste or forward a suspicious email and get back a risk score, a verdict and the reasons behind it.

MailDefender is a self-hosted phishing analyzer. It reads the raw message, checks the sender's authentication headers, looks up every link and IP against public threat feeds, and runs the text through a small DistilBERT classifier that I trained myself. Nothing is sent to a paid AI API, so running it costs a VPS and nothing else.

Live instance: [maildefender.xyz](https://maildefender.xyz)

![license](https://img.shields.io/badge/license-MIT-green) ![python](https://img.shields.io/badge/python-3.12-blue) ![react](https://img.shields.io/badge/react-18-61dafb)

## What it does

- **Reads the whole email.** Drop an `.eml` file or paste the raw source. Headers, body, links, IPs and attachments are all parsed.
- **Checks sender authentication.** SPF, DKIM and DMARC results, plus From / Reply-To domain mismatches.
- **Looks things up in parallel.** Links and IPs go to VirusTotal, AbuseIPDB and urlscan.io at the same time through `asyncio.gather`.
- **Classifies the text.** A DistilBERT model, exported to ONNX, sorts the message into five classes: `legitimate`, `spam`, `phishing`, `spear_phishing` and `whaling`.
- **Explains itself.** The score comes with an itemized list of every signal that added or removed points.
- **Works by email.** Forward a suspicious message to the address you configure and the service replies with an HTML report.
- **Has an API.** `POST /api/v1/scan` with an API key, documented in Swagger at `/docs`.

Every outside service is optional. With no API keys at all you still get header analysis and the ML verdict.

## How it fits together

```
 browser ──► nginx ──► FastAPI backend ──► ML service (DistilBERT / ONNX)
                          │    ▲
 SMTP :25 ► aiosmtpd ─────┘    └── VirusTotal · AbuseIPDB · urlscan.io
                          │
                          └──► SQLite (API keys, usage, feedback)
```

| Part | Where | Notes |
|------|-------|-------|
| Web UI | `frontend/` | React 18, Vite, Tailwind. Served by nginx. |
| API and pipeline | `backend/` | FastAPI, async end to end. |
| Classifier service | `ml/` | Separate container. Downloads the model from Hugging Face on first start. |
| Inbound mail | `backend/email_receiver.py` | `aiosmtpd` in its own thread, hands work to the app's event loop. |
| Replies | `backend/email_sender.py` | `aiosmtplib` through any SMTP relay. |

The ML service is deliberately not inside the backend image. The model is a few hundred MB and has its own release cycle, so it runs on its own and the backend just calls `POST /classify`.

## Risk score

Each email gets a score from 0 to 100. The weights live in [`backend/scoring/risk_score.py`](backend/scoring/risk_score.py) and are meant to be edited.

| Signal | Points |
|--------|--------|
| SPF fail / softfail / missing | +20 / +12 / +8 |
| DKIM invalid / missing | +15 / +5 |
| DMARC not passing | +8 |
| From and Reply-To domains differ | +20 |
| Suspicious attachment | +15 each, capped at 25 |
| Link flagged by VirusTotal | +20 each, capped at 40 |
| IP flagged by VirusTotal | +10 each, capped at 20 |
| IP flagged by AbuseIPDB | +10 each, capped at 20 |
| URL shortener | +5 each, capped at 10 |
| Classifier says phishing or suspicious | scaled by its confidence |
| Classifier says likely safe | small deduction |

Levels: 0-19 low, 20-44 medium, 45-69 high, 70-100 critical.

## The classifier

I picked DistilBERT over a generative model on purpose. A small local LLM needed about 2 GB of RAM and 25 to 60 seconds per email on CPU. The quantized ONNX classifier uses a few hundred MB and answers in well under a second, which is plenty for a classification task.

| Class | Meaning |
|-------|---------|
| `legitimate` | Normal mail |
| `spam` | Bulk and unwanted, not malicious |
| `phishing` | Credential theft or malicious links |
| `spear_phishing` | Targeted, personalized |
| `whaling` | Aimed at executives or finance staff |

Training and data-building code is under `ml/` (`build_dataset.py`, `retrain.py`, `colab/train_colab.py`). Feedback submitted through `POST /feedback/{scan_id}` can be exported with `GET /admin/export` and used to retrain.

## Run it yourself

You need Docker with Compose.

```bash
git clone https://github.com/Jeffreycq/phishguard.git
cd phishguard
cp .env.example .env
docker compose up --build
```

| What | Where |
|------|-------|
| Web UI | http://localhost:3000 |
| Swagger | http://localhost:3000/docs |
| Health | http://localhost:3000/health |

By default `ML_SERVICE_URL` points at my hosted classifier. That works for trying it out, but I can't promise it stays up for everyone's forks. To run your own, build `ml/`, set `HF_MODEL_REPO` to a Hugging Face repo that holds the ONNX files, and point `ML_SERVICE_URL` at it.

### Configuration

All settings are environment variables. See [`.env.example`](.env.example).

| Variable | Purpose |
|----------|---------|
| `ML_SERVICE_URL` | Where the classifier lives |
| `VIRUSTOTAL_API_KEY`, `ABUSEIPDB_API_KEY`, `URLSCAN_API_KEY` | Optional threat feeds |
| `ADMIN_SECRET` | Turns on the `/admin/*` endpoints used to issue API keys |
| `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM` | Outbound relay for reply emails |
| `SMTP_LISTEN_PORT` | Inbound listener, 2525 by default (compose maps host port 25 to it) |
| `DB_PATH` | SQLite file, `/data/maildefender.db` by default |

Free tiers that are enough to get started: VirusTotal (4 requests per minute), AbuseIPDB (1,000 per day), urlscan.io (100 per day), Resend for outbound mail (3,000 per month).

### Receiving forwarded email

1. Open port 25 on your server.
2. Add an `MX` record for your domain that points at it.
3. Set the `SMTP_*` variables so the service can send its replies.

## API

Issue a key with your admin secret, then use it:

```bash
# create a key
curl -X POST http://localhost:3000/admin/keys \
  -H "X-Admin-Secret: $ADMIN_SECRET" \
  -F "label=my-script"

# scan an email
curl -X POST http://localhost:3000/api/v1/scan \
  -H "X-API-Key: mdef_..." \
  -F "raw_email=<suspicious.eml"
```

If you would rather send JSON (handy for webhooks), `POST /api/v1/scan-json` takes the same key and a JSON body with a `raw_email` field.

Keys are stored hashed and rate limited per day (1,000 by default). The response includes the score, level, verdict, tactics, red flags, per-class ML probabilities and the SPF / DKIM / DMARC results. Run the app and open `/docs` for the full schema.

## Layout

```
backend/    FastAPI app, parsers, scanners, scoring, SMTP in/out
frontend/   React UI and in-app API docs
ml/         Classifier service and training scripts
docs/       Write-ups
```

## Security

I scanned the repo with Endor Labs' AURI and fixed what it found: outdated `aiohttp`, `python-multipart`, `starlette` and `aiosmtplib`, and error messages that leaked exception text to API clients. The write-up, including what I chose not to change and why, is in [`docs/post-auri-hallazgos.md`](docs/post-auri-hallazgos.md) (in Spanish).

If you find a vulnerability, please open a private security advisory on GitHub instead of a public issue.

## Contributing

Issues and pull requests are welcome. Good places to start: new scoring signals, more threat feeds, translations of the UI, and better training data for the classifier.

## License

MIT. See [LICENSE](LICENSE).

Built by [Jeffrey Cedeno](https://github.com/Jeffreycq).
