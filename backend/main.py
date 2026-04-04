import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

import aiohttp
from fastapi import FastAPI, File, Form, UploadFile, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional

from parsers.email_parser import parse_email
from scanners import virustotal, urlscan, abuseipdb
from scanners.ai_analyzer import analyze_email
from scoring.risk_score import calculate_score

app = FastAPI(
    title="MailDefender API",
    version="1.0.0",
    description="AI-powered phishing email analysis API",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _require_api_key(x_api_key: Optional[str]):
    """Validate public API key. Set PUBLIC_API_KEY env var to enable auth."""
    required = os.getenv("PUBLIC_API_KEY", "")
    if not required:
        raise HTTPException(503, "Public API is not enabled on this server.")
    if x_api_key != required:
        raise HTTPException(401, "Invalid or missing API key. Pass it as X-API-Key header.")


async def _run_analysis(raw: bytes | str) -> dict:
    """Shared analysis logic used by both the web UI and public API endpoints."""
    parsed = parse_email(raw)
    urls = parsed.get("urls", [])[:10]
    ips = parsed.get("ips", [])[:5]

    async with aiohttp.ClientSession() as session:
        tasks = [
            *[virustotal.scan_url(session, u) for u in urls[:5]],
            *[virustotal.scan_ip(session, ip) for ip in ips],
            *[abuseipdb.check_ip(session, ip) for ip in ips],
            analyze_email(parsed),
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

    vt_url_count = len(urls[:5])
    vt_ip_count = len(ips)
    abuse_count = len(ips)

    idx = 0
    vt_url_results = _safe_results(results, idx, vt_url_count);  idx += vt_url_count
    vt_ip_results  = _safe_results(results, idx, vt_ip_count);   idx += vt_ip_count
    abuse_results  = _safe_results(results, idx, abuse_count);    idx += abuse_count

    ai_result = results[idx] if idx < len(results) else {}
    if isinstance(ai_result, Exception):
        ai_result = {"status": "error", "error": str(ai_result), "verdict": "UNKNOWN", "confidence": 0}

    risk = calculate_score(parsed, vt_url_results, vt_ip_results, abuse_results, ai_result)

    return {
        "parsed": parsed,
        "vt_url_results": vt_url_results,
        "vt_ip_results": vt_ip_results,
        "abuse_results": abuse_results,
        "ai_result": ai_result,
        "risk": risk,
        "urls": urls,
        "ips": ips,
    }


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "configured_apis": {
            "groq":       bool(os.getenv("GROQ_API_KEY")),
            "virustotal": bool(os.getenv("VIRUSTOTAL_API_KEY")),
            "urlscan":    bool(os.getenv("URLSCAN_API_KEY")),
            "abuseipdb":  bool(os.getenv("ABUSEIPDB_API_KEY")),
        },
        "public_api_enabled": bool(os.getenv("PUBLIC_API_KEY")),
    }


# ---------------------------------------------------------------------------
# Web UI endpoint  (used by the React frontend)
# ---------------------------------------------------------------------------

@app.post("/analyze")
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

    data = await _run_analysis(raw)
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
# Public API  (for third-party developers)
# ---------------------------------------------------------------------------

@app.post(
    "/api/v1/scan",
    summary="Scan an email for phishing threats",
    response_description="Risk score, AI verdict, and key threat indicators",
)
async def public_scan(
    raw_email: str = Form(..., description="Full raw email content (headers + body)"),
    x_api_key: Optional[str] = Header(default=None),
):
    """
    **Public API** — analyze a raw email and receive a structured threat report.

    **Authentication:** pass your key in the `X-API-Key` header.

    **Request:** `multipart/form-data` with a single `raw_email` field.

    **Response fields:**
    - `score` — risk score 0–100
    - `level` — `LOW` | `MEDIUM` | `HIGH` | `CRITICAL`
    - `verdict` — AI verdict: `SAFE` | `LIKELY_SAFE` | `SUSPICIOUS` | `PHISHING`
    - `confidence` — AI confidence 0–100
    - `reasoning` — plain-English explanation from the AI
    - `tactics` — list of detected social engineering tactics
    - `red_flags` — specific concerning elements
    - `recommendation` — suggested action for the end user
    - `indicators` — structural threat indicators (SPF/DKIM/DMARC failures, etc.)
    - `urls_total` — number of URLs found
    - `urls_flagged` — URLs flagged by VirusTotal
    - `ips_flagged` — IPs flagged by AbuseIPDB or VirusTotal
    - `auth` — SPF / DKIM / DMARC results
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
        # Risk
        "score":          risk["score"],
        "level":          risk["level"],
        # AI
        "verdict":        ai.get("verdict", "UNKNOWN"),
        "confidence":     ai.get("confidence", 0),
        "reasoning":      ai.get("reasoning", ""),
        "tactics":        ai.get("tactics", []),
        "red_flags":      ai.get("red_flags", []),
        "recommendation": ai.get("recommendation", ""),
        # Indicators
        "indicators":     data["parsed"].get("indicators", []),
        "urls_total":     len(data["urls"]),
        "urls_flagged":   flagged_urls,
        "ips_flagged":    flagged_ips,
        # Auth
        "auth": {
            "spf":                  headers.get("spf", "none"),
            "dkim":                 headers.get("dkim", "none"),
            "dmarc":                headers.get("dmarc", "none"),
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
            "ip":        ip,
            "virustotal": vt_map.get(ip,    {"status": "not_checked"}),
            "abuseipdb":  abuse_map.get(ip, {"status": "not_checked"}),
        }
        for ip in ips
    ]
