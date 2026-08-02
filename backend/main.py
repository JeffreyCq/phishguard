import asyncio
import hashlib
import logging
import os
import uuid as _uuid_mod
from contextlib import asynccontextmanager

from dotenv import load_dotenv

load_dotenv()

import aiohttp
from fastapi import FastAPI, File, Form, HTTPException, Header, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import select, text
from typing import Optional

from database import init_db, AsyncSessionLocal
from models import Scan, Feedback, ApiKey
from api_keys import generate_key, verify_key, require_admin
from parsers.email_parser import parse_email
from scanners import abuseipdb, virustotal
from scanners.ai_analyzer import analyze_email, ML_SERVICE_URL
from scoring.risk_score import calculate_score
from email_receiver import set_analysis_callback, start_smtp_server
from email_sender import send_analysis_reply

logger = logging.getLogger(__name__)


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
    await init_db()
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

Analyze raw emails for phishing threats using a **DistilBERT ML classifier** (no external token costs)
combined with real-time threat intelligence from VirusTotal and AbuseIPDB.

### Features
- **ML classifier** via DistilBERT/ONNX — lightning-fast, runs on a dedicated microservice
- **Email forwarding** — forward suspicious emails to `{_SCAN_ADDRESS or '<SMTP_FROM address>'}` and receive an HTML report
- **REST API** — integrate phishing detection into your own tools
- **Threat intelligence** — VirusTotal URL/IP checks + AbuseIPDB IP reputation

### Authentication
The public `/api/v1/scan` endpoint requires an `X-API-Key` header.
Keys are issued via `POST /admin/keys` using your `ADMIN_SECRET`.
"""

app = FastAPI(
    title="MailDefender API",
    version="2.1.0",
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
# Auth helper (now DB-backed — see api_keys.py)
# ---------------------------------------------------------------------------

async def _require_api_key(x_api_key: Optional[str]) -> ApiKey:
    return await verify_key(x_api_key)


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------

async def _persist_scan(raw: bytes | str, data: dict, source: str = "unknown") -> str:
    raw_str = raw.decode("utf-8", errors="replace") if isinstance(raw, bytes) else raw
    email_hash = hashlib.sha256(raw_str.encode()).hexdigest()
    scan_id = str(_uuid_mod.uuid4())

    parsed = data["parsed"]
    ai     = data["ai_result"]
    risk   = data["risk"]

    try:
        async with AsyncSessionLocal() as session:
            scan = Scan(
                scan_id       = scan_id,
                email_hash    = email_hash,
                subject       = (parsed["headers"].get("subject") or "")[:512],
                sender        = (parsed["headers"].get("from") or "")[:256],
                body_text     = parsed.get("body_text", ""),
                verdict       = ai.get("verdict", ""),
                spam_verdict  = ai.get("spam_verdict", ""),
                confidence    = ai.get("confidence", 0),
                threat_type   = ai.get("ml_threat_type", ""),
                risk_score    = risk.get("score", 0),
                risk_level    = risk.get("level", ""),
                model_version = "distilbert-maildefender-v1",
                source        = source,
            )
            session.add(scan)
            await session.commit()
    except Exception as exc:
        logger.warning("Could not persist scan: %s", exc)

    return scan_id


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

    # Derive ml_result from ai_result (same ML service, no second call needed)
    ml_result = {
        "status":      ai_result.get("status", "error"),
        "threat_type": ai_result.get("ml_threat_type", "unknown"),
        "threat_level": ai_result.get("ml_threat_level", -1),
        "confidence":  ai_result.get("confidence", 0) / 100,
        "scores":      {k: v / 100 for k, v in ai_result.get("ml_scores", {}).items()},
    }

    risk = calculate_score(parsed, vt_url_results, vt_ip_results, abuse_results, ai_result)

    return {
        "parsed":          parsed,
        "vt_url_results":  vt_url_results,
        "vt_ip_results":   vt_ip_results,
        "abuse_results":   abuse_results,
        "ai_result":       ai_result,
        "ml_result":       ml_result,
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
        "ml_classifier": ML_SERVICE_URL,
        "ml_backend": "distilbert/onnx (microservice)",
        "configured_apis": {
            "virustotal":       bool(os.getenv("VIRUSTOTAL_API_KEY")),
            "urlscan":          bool(os.getenv("URLSCAN_API_KEY")),
            "abuseipdb":        bool(os.getenv("ABUSEIPDB_API_KEY")),
        },
        "public_api_enabled":    bool(os.getenv("ADMIN_SECRET")),
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
        source = "file"
    elif raw_email:
        if not raw_email.strip():
            raise HTTPException(400, "Email text is empty")
        raw = raw_email
        source = "paste"
    else:
        raise HTTPException(400, "Provide either a file upload or raw_email text")

    data   = await _run_analysis(raw)
    parsed = data["parsed"]
    urls   = data["urls"]
    ips    = data["ips"]

    scan_id = await _persist_scan(raw, data, source=source)

    return {
        "scan_id":        scan_id,
        "risk":           data["risk"],
        "headers":        parsed["headers"],
        "urls":           _annotate_urls(urls, data["vt_url_results"]),
        "ips":            _annotate_ips(ips, data["vt_ip_results"], data["abuse_results"]),
        "attachments":    parsed.get("attachments", []),
        "indicators":     parsed.get("indicators", []),
        "ai_analysis":    data["ai_result"],
        "ml_classifier":  data["ml_result"],
    }


# ---------------------------------------------------------------------------
# Public REST API
# ---------------------------------------------------------------------------

_SCAN_RESPONSE_DESCRIPTION = """
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


class ScanRequest(BaseModel):
    raw_email: str = Field(
        ...,
        description="Complete raw email content (RFC 5322 format — headers + blank line + body). Plain pasted text also works.",
    )


async def _build_scan_response(raw_email: str) -> dict:
    if not raw_email.strip():
        raise HTTPException(400, "raw_email is empty")

    data = await _run_analysis(raw_email)
    ai   = data["ai_result"]
    risk = data["risk"]

    scan_id = await _persist_scan(raw_email, data, source="api")

    flagged_urls = sum(1 for r in data["vt_url_results"] if r.get("flagged"))
    flagged_ips  = sum(
        1 for vt, ab in zip(data["vt_ip_results"], data["abuse_results"])
        if vt.get("flagged") or ab.get("flagged")
    )
    headers = data["parsed"]["headers"]

    return {
        "scan_id":        scan_id,
        "score":          risk["score"],
        "level":          risk["level"],
        "verdict":        ai.get("verdict", "UNKNOWN"),
        "confidence":     ai.get("confidence", 0),
        "reasoning":      ai.get("reasoning", ""),
        "tactics":        ai.get("tactics", []),
        "red_flags":      ai.get("red_flags", []),
        "recommendation": ai.get("recommendation", ""),
        "indicators":     data["parsed"].get("indicators", []),
        "ml_classifier":  data["ml_result"],
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
    f"""
    Analyze a raw email and receive a structured phishing threat report.

    **Request format:** `multipart/form-data` with a single `raw_email` field
    containing the full RFC 5322 email (paste from your email client's
    "View Source" / "Show Original" option).

    **Response fields:**

    {_SCAN_RESPONSE_DESCRIPTION}
    """
    await _require_api_key(x_api_key)
    return await _build_scan_response(raw_email)


@app.post(
    "/api/v1/scan-json",
    summary="Scan an email for phishing threats (JSON body)",
    response_description="Structured threat report with risk score, AI verdict, and indicators",
    tags=["Public API"],
)
async def public_scan_json(
    payload: ScanRequest,
    x_api_key: Optional[str] = Header(
        default=None,
        description="Your API key. Set PUBLIC_API_KEY on the server to enable this endpoint.",
    ),
):
    f"""
    Identical to `/api/v1/scan`, but accepts `application/json` instead of
    `multipart/form-data` — useful for webhook integrations (Jira Automation,
    Zapier, generic "send web request" actions) that can only emit JSON.

    **Request body:**
    ```json
    {{"raw_email": "From: attacker@evil.com\\n...full RFC 5322 email..."}}
    ```

    **Response fields:**

    {_SCAN_RESPONSE_DESCRIPTION}
    """
    await _require_api_key(x_api_key)
    return await _build_scan_response(payload.raw_email)


# ---------------------------------------------------------------------------
# Feedback endpoints
# ---------------------------------------------------------------------------

@app.post("/feedback/{scan_id}", tags=["Feedback"])
async def submit_feedback(
    scan_id: str,
    is_correct: bool = Form(...),
    true_label: Optional[str] = Form(default=None),
    notes: Optional[str] = Form(default=None),
):
    """Record whether the model verdict was correct. If not, provide the true label."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Scan).where(Scan.scan_id == scan_id))
        if not result.scalar_one_or_none():
            raise HTTPException(404, "Scan not found")

        fb = Feedback(
            scan_id    = scan_id,
            is_correct = is_correct,
            true_label = true_label,
            notes      = notes,
        )
        session.add(fb)
        await session.commit()

    return {"status": "ok", "scan_id": scan_id}


@app.get("/admin/export", tags=["Admin"])
async def export_feedback(
    x_admin_secret: Optional[str] = Header(default=None),
):
    """Export all corrected feedback as CSV for retraining. Requires X-Admin-Secret."""
    require_admin(x_admin_secret)

    import csv, io
    async with AsyncSessionLocal() as session:
        rows = (await session.execute(
            select(Scan, Feedback)
            .join(Feedback, Scan.scan_id == Feedback.scan_id)
            .where(Feedback.is_correct == False)
            .where(Feedback.true_label.is_not(None))
        )).all()

    buf = io.StringIO()
    w   = csv.writer(buf)
    w.writerow(["subject", "sender", "body_text", "true_label", "original_verdict", "confidence", "scan_id"])
    for scan, fb in rows:
        w.writerow([
            scan.subject or "",
            scan.sender or "",
            scan.body_text or "",
            fb.true_label,
            scan.verdict,
            scan.confidence,
            scan.scan_id,
        ])

    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=feedback_export.csv"},
    )


# ---------------------------------------------------------------------------
# Admin — API key management
# ---------------------------------------------------------------------------

@app.post("/admin/keys", tags=["Admin"], status_code=201)
async def create_api_key(
    label: str = Form(..., description="Human-readable label for this key (owner name, app, etc.)"),
    rate_limit: int = Form(default=1000, description="Max requests per day"),
    x_admin_secret: Optional[str] = Header(default=None),
):
    """
    Issue a new API key. **The raw key is returned once — store it securely.**
    Subsequent calls show only the 8-char prefix for identification.
    """
    require_admin(x_admin_secret)

    raw, prefix, key_hash = generate_key()

    async with AsyncSessionLocal() as session:
        session.add(ApiKey(
            prefix=prefix,
            key_hash=key_hash,
            label=label,
            rate_limit=rate_limit,
        ))
        await session.commit()

    return {
        "key": raw,
        "prefix": prefix,
        "label": label,
        "rate_limit": rate_limit,
        "warning": "Store this key now — it will not be shown again.",
    }


@app.get("/admin/keys", tags=["Admin"])
async def list_api_keys(
    x_admin_secret: Optional[str] = Header(default=None),
):
    """List all API keys (prefix + metadata only, never raw key)."""
    require_admin(x_admin_secret)

    async with AsyncSessionLocal() as session:
        rows = (await session.execute(select(ApiKey).order_by(ApiKey.created_at))).scalars().all()

    return [
        {
            "prefix":       k.prefix,
            "label":        k.label,
            "is_active":    k.is_active,
            "rate_limit":   k.rate_limit,
            "created_at":   k.created_at,
            "last_used_at": k.last_used_at,
        }
        for k in rows
    ]


@app.get("/admin/stats", tags=["Admin"])
async def get_stats(
    x_admin_secret: Optional[str] = Header(default=None),
):
    """Usage statistics: scan counts, source breakdown, verdict distribution, daily trends."""
    require_admin(x_admin_secret)

    async with AsyncSessionLocal() as session:
        total = (await session.execute(text("SELECT COUNT(*) FROM scans"))).scalar()
        last_7 = (await session.execute(text(
            "SELECT COUNT(*) FROM scans WHERE created_at >= datetime('now', '-7 days')"
        ))).scalar()
        last_30 = (await session.execute(text(
            "SELECT COUNT(*) FROM scans WHERE created_at >= datetime('now', '-30 days')"
        ))).scalar()
        by_source = (await session.execute(text(
            "SELECT COALESCE(source, 'unknown') as src, COUNT(*) as cnt FROM scans GROUP BY src ORDER BY cnt DESC"
        ))).fetchall()
        by_verdict = (await session.execute(text(
            "SELECT COALESCE(verdict, 'UNKNOWN') as v, COUNT(*) as cnt FROM scans GROUP BY v ORDER BY cnt DESC"
        ))).fetchall()
        by_risk_level = (await session.execute(text(
            "SELECT COALESCE(risk_level, 'UNKNOWN') as lvl, COUNT(*) as cnt FROM scans GROUP BY lvl ORDER BY cnt DESC"
        ))).fetchall()
        daily = (await session.execute(text(
            "SELECT date(created_at) as day, COUNT(*) as cnt FROM scans "
            "WHERE created_at >= datetime('now', '-30 days') GROUP BY day ORDER BY day"
        ))).fetchall()
        recent = (await session.execute(text(
            "SELECT scan_id, COALESCE(verdict,'UNKNOWN'), risk_score, COALESCE(source,'unknown'), created_at "
            "FROM scans ORDER BY created_at DESC LIMIT 10"
        ))).fetchall()

    return {
        "total_scans":   total,
        "last_7_days":   last_7,
        "last_30_days":  last_30,
        "by_source":     [{"source": r[0], "count": r[1]} for r in by_source],
        "by_verdict":    [{"verdict": r[0], "count": r[1]} for r in by_verdict],
        "by_risk_level": [{"level": r[0], "count": r[1]} for r in by_risk_level],
        "daily_counts":  [{"date": r[0], "count": r[1]} for r in daily],
        "recent_scans":  [
            {"scan_id": r[0], "verdict": r[1], "risk_score": r[2], "source": r[3], "created_at": str(r[4])}
            for r in recent
        ],
    }


@app.delete("/admin/keys/{prefix}", tags=["Admin"])
async def revoke_api_key(
    prefix: str,
    x_admin_secret: Optional[str] = Header(default=None),
):
    """Revoke an API key by its 8-char prefix. Immediate effect."""
    require_admin(x_admin_secret)

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(ApiKey).where(ApiKey.prefix == prefix))
        api_key = result.scalar_one_or_none()
        if api_key is None:
            raise HTTPException(404, f"No key with prefix '{prefix}'")
        api_key.is_active = False
        await session.commit()

    return {"status": "revoked", "prefix": prefix}


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
