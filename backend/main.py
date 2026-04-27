import asyncio
import logging
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv

load_dotenv()

import aiohttp
from fastapi import FastAPI, File, Form, HTTPException, Header, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional

from parsers.email_parser import parse_email
from scanners import abuseipdb, virustotal
from scanners.ai_analyzer import analyze_email, OLLAMA_BASE_URL, OLLAMA_MODEL
from scoring.risk_score import calculate_score
from email_receiver import set_analysis_callback, start_smtp_server
from email_sender import send_analysis_reply

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Ollama model warm-up
# ---------------------------------------------------------------------------

async def _ensure_ollama_model():
    """Wait for Ollama to be ready, then pull the model if not cached."""
    logger.info("Waiting for Ollama at %s ...", OLLAMA_BASE_URL)
    async with aiohttp.ClientSession() as session:
        for _ in range(30):
            try:
                async with session.get(
                    f"{OLLAMA_BASE_URL}/api/tags",
                    timeout=aiohttp.ClientTimeout(total=3),
                ) as r:
                    if r.status == 200:
                        break
            except Exception:
                pass
            await asyncio.sleep(2)
        else:
            logger.warning("Ollama not reachable after 60 s — AI analysis may fail")
            return

        logger.info("Ollama ready — pulling model %s (first run may take a few minutes)...", OLLAMA_MODEL)
        try:
            async with session.post(
                f"{OLLAMA_BASE_URL}/api/pull",
                json={"name": OLLAMA_MODEL},
                timeout=aiohttp.ClientTimeout(total=600),
            ) as r:
                async for _ in r.content:
                    pass  # consume the progress stream
            logger.info("Model %s ready", OLLAMA_MODEL)
        except Exception as exc:
            logger.warning("Model pull failed (may already be cached): %s", exc)


# ---------------------------------------------------------------------------
# Email-via-SMTP callback
# ---------------------------------------------------------------------------

async def _handle_forwarded_email(sender_address: str, raw_bytes: bytes):
    """Called by the SMTP server when an email arrives for analysis."""
    logger.info("Analyzing forwarded email from %s", sender_address)
    try:
        analysis = await _run_analysis(raw_bytes)
        await send_analysis_reply(sender_address, analysis)
    except Exception as exc:
        logger.error("Error processing forwarded email: %s", exc)


# ---------------------------------------------------------------------------
# App lifespan
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Pull model in background so the app starts responding immediately
    asyncio.create_task(_ensure_ollama_model())

    loop = asyncio.get_event_loop()
    set_analysis_callback(_handle_forwarded_email)
    smtp_controller = start_smtp_server(loop)

    yield

    if smtp_controller:
        smtp_controller.stop()
        logger.info("SMTP server stopped")


# ---------------------------------------------------------------------------
# App definition
# ---------------------------------------------------------------------------

_SCAN_ADDRESS = os.getenv("SMTP_FROM", "")
_description = f"""
## MailDefender — AI-Powered Phishing Detection

Analyze raw emails for phishing threats using a **local AI model** (no external token costs)
combined with real-time threat intelligence from VirusTotal and AbuseIPDB.

### Features
- **Local AI analysis** via Ollama `{OLLAMA_MODEL}` — runs entirely on your infrastructure
- **Email forwarding** — forward suspicious emails to `{_SCAN_ADDRESS or '<SMTP_FROM address>'}` and receive an HTML report
- **REST API** — integrate phishing detection into your own tools
- **Threat intelligence** — VirusTotal URL/IP checks + AbuseIPDB IP reputation

### Authentication
The public `/api/v1/scan` endpoint requires an `X-API-Key` header.
Set the `PUBLIC_API_KEY` environment variable on the server to enable it.
"""

app = FastAPI(
    title="MailDefender API",
    version="2.0.0",
    description=_description,
    lifespan=lifespan,
    contact={"name": "MailDefender", "url": "https://github.com"},
    license_info={"name": "MIT"},
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Auth helper
# ---------------------------------------------------------------------------

def _require_api_key(x_api_key: Optional[str]):
    required = os.getenv("PUBLIC_API_KEY", "")
    if not required:
        raise HTTPException(503, "Public API is not enabled on this server.")
    if x_api_key != required:
        raise HTTPException(401, "Invalid or missing API key. Pass it as X-API-Key header.")


# ---------------------------------------------------------------------------
# Shared analysis pipeline
# ---------------------------------------------------------------------------

async def _run_analysis(raw: bytes | str) -> dict:
    parsed = parse_email(raw)
    urls   = parsed.get("urls", [])[:10]
    ips    = parsed.get("ips", [])[:5]

    async with aiohttp.ClientSession() as session:
        tasks = [
            *[virustotal.scan_url(session, u) for u in urls[:5]],
            *[virustotal.scan_ip(session, ip) for ip in ips],
            *[abuseipdb.check_ip(session, ip) for ip in ips],
            analyze_email(parsed),
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

    vt_url_count = len(urls[:5])
    vt_ip_count  = len(ips)
    abuse_count  = len(ips)

    idx = 0
    vt_url_results = _safe_results(results, idx, vt_url_count); idx += vt_url_count
    vt_ip_results  = _safe_results(results, idx, vt_ip_count);  idx += vt_ip_count
    abuse_results  = _safe_results(results, idx, abuse_count);   idx += abuse_count

    ai_result = results[idx] if idx < len(results) else {}
    if isinstance(ai_result, Exception):
        ai_result = {"status": "error", "error": str(ai_result), "verdict": "UNKNOWN", "confidence": 0}

    risk = calculate_score(parsed, vt_url_results, vt_ip_results, abuse_results, ai_result)

    return {
        "parsed":          parsed,
        "vt_url_results":  vt_url_results,
        "vt_ip_results":   vt_ip_results,
        "abuse_results":   abuse_results,
        "ai_result":       ai_result,
        "risk":            risk,
        "urls":            urls,
        "ips":             ips,
    }


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@app.get(
    "/health",
    summary="Service health and configuration status",
    tags=["Status"],
)
async def health():
    """Returns service status and which optional integrations are configured."""
    return {
        "status": "ok",
        "ai_model": OLLAMA_MODEL,
        "ai_backend": "ollama (local)",
        "configured_apis": {
            "virustotal":       bool(os.getenv("VIRUSTOTAL_API_KEY")),
            "urlscan":          bool(os.getenv("URLSCAN_API_KEY")),
            "abuseipdb":        bool(os.getenv("ABUSEIPDB_API_KEY")),
        },
        "public_api_enabled":    bool(os.getenv("PUBLIC_API_KEY")),
        "email_forwarding":      bool(os.getenv("SMTP_HOST")),
        "email_scan_address":    os.getenv("SMTP_FROM", ""),
    }


# ---------------------------------------------------------------------------
# Web UI endpoint  (used by the React frontend — no auth)
# ---------------------------------------------------------------------------

@app.post(
    "/analyze",
    include_in_schema=False,
)
async def analyze(
    file: UploadFile | None = File(default=None),
    raw_email: str | None = Form(default=None),
):
    if file is not None:
        content = await file.read()
        if not content:
            raise HTTPException(400, "Uploaded file is empty")
        raw = content
    elif raw_email:
        if not raw_email.strip():
            raise HTTPException(400, "Email text is empty")
        raw = raw_email
    else:
        raise HTTPException(400, "Provide either a file upload or raw_email text")

    data   = await _run_analysis(raw)
    parsed = data["parsed"]
    urls   = data["urls"]
    ips    = data["ips"]

    return {
        "risk":        data["risk"],
        "headers":     parsed["headers"],
        "urls":        _annotate_urls(urls, data["vt_url_results"]),
        "ips":         _annotate_ips(ips, data["vt_ip_results"], data["abuse_results"]),
        "attachments": parsed.get("attachments", []),
        "indicators":  parsed.get("indicators", []),
        "ai_analysis": data["ai_result"],
    }


# ---------------------------------------------------------------------------
# Public REST API
# ---------------------------------------------------------------------------

@app.post(
    "/api/v1/scan",
    summary="Scan an email for phishing threats",
    response_description="Structured threat report with risk score, AI verdict, and indicators",
    tags=["Public API"],
)
async def public_scan(
    raw_email: str = Form(
        ...,
        description="Complete raw email content (RFC 5322 format — headers + blank line + body)",
    ),
    x_api_key: Optional[str] = Header(
        default=None,
        description="Your API key. Set PUBLIC_API_KEY on the server to enable this endpoint.",
    ),
):
    """
    Analyze a raw email and receive a structured phishing threat report.

    **Request format:** `multipart/form-data` with a single `raw_email` field
    containing the full RFC 5322 email (paste from your email client's
    "View Source" / "Show Original" option).

    **Response fields:**

    | Field | Type | Description |
    |-------|------|-------------|
    | `score` | integer 0–100 | Overall risk score |
    | `level` | string | `LOW` · `MEDIUM` · `HIGH` · `CRITICAL` |
    | `verdict` | string | AI verdict: `SAFE` · `LIKELY_SAFE` · `SUSPICIOUS` · `PHISHING` |
    | `confidence` | integer 0–100 | AI confidence in the verdict |
    | `reasoning` | string | Plain-English explanation |
    | `tactics` | string[] | Detected social engineering tactics |
    | `red_flags` | string[] | Specific concerning elements |
    | `recommendation` | string | Suggested action for the end user |
    | `indicators` | string[] | Structural threat indicators |
    | `urls_total` | integer | Total URLs extracted from the email |
    | `urls_flagged` | integer | URLs flagged as malicious by VirusTotal |
    | `ips_flagged` | integer | IPs flagged by VirusTotal or AbuseIPDB |
    | `auth.spf` | string | SPF result: `pass` · `fail` · `softfail` · `none` |
    | `auth.dkim` | string | DKIM result: `pass` · `fail` · `none` |
    | `auth.dmarc` | string | DMARC result: `pass` · `fail` · `none` |
    | `auth.from_reply_to_mismatch` | boolean | From and Reply-To domains differ |
    """
    _require_api_key(x_api_key)

    if not raw_email.strip():
        raise HTTPException(400, "raw_email is empty")

    data = await _run_analysis(raw_email)
    ai   = data["ai_result"]
    risk = data["risk"]

    flagged_urls = sum(1 for r in data["vt_url_results"] if r.get("flagged"))
    flagged_ips  = sum(
        1 for vt, ab in zip(data["vt_ip_results"], data["abuse_results"])
        if vt.get("flagged") or ab.get("flagged")
    )
    headers = data["parsed"]["headers"]

    return {
        "score":          risk["score"],
        "level":          risk["level"],
        "verdict":        ai.get("verdict", "UNKNOWN"),
        "confidence":     ai.get("confidence", 0),
        "reasoning":      ai.get("reasoning", ""),
        "tactics":        ai.get("tactics", []),
        "red_flags":      ai.get("red_flags", []),
        "recommendation": ai.get("recommendation", ""),
        "indicators":     data["parsed"].get("indicators", []),
        "urls_total":     len(data["urls"]),
        "urls_flagged":   flagged_urls,
        "ips_flagged":    flagged_ips,
        "auth": {
            "spf":                    headers.get("spf", "none"),
            "dkim":                   headers.get("dkim", "none"),
            "dmarc":                  headers.get("dmarc", "none"),
            "from_reply_to_mismatch": headers.get("from_reply_to_mismatch", False),
        },
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _safe_results(results: list, start: int, count: int) -> list[dict]:
    out = []
    for i in range(start, start + count):
        r = results[i] if i < len(results) else {}
        out.append({} if isinstance(r, Exception) else r)
    return out


def _annotate_urls(urls: list[str], vt_results: list[dict]) -> list[dict]:
    vt_map = {r.get("url"): r for r in vt_results}
    return [{"url": u, "virustotal": vt_map.get(u, {"status": "not_checked"})} for u in urls]


def _annotate_ips(ips: list[str], vt_results: list[dict], abuse_results: list[dict]) -> list[dict]:
    vt_map    = {r.get("ip"): r for r in vt_results}
    abuse_map = {r.get("ip"): r for r in abuse_results}
    return [
        {
            "ip":         ip,
            "virustotal": vt_map.get(ip,    {"status": "not_checked"}),
            "abuseipdb":  abuse_map.get(ip, {"status": "not_checked"}),
        }
        for ip in ips
    ]
