import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

import aiohttp
from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from parsers.email_parser import parse_email
from scanners import virustotal, urlscan, abuseipdb
from scanners.ai_analyzer import analyze_email
from scoring.risk_score import calculate_score

app = FastAPI(title="Phishing Scanner API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    configured = {
        "virustotal": bool(os.getenv("VIRUSTOTAL_API_KEY")),
        "urlscan": bool(os.getenv("URLSCAN_API_KEY")),
        "abuseipdb": bool(os.getenv("ABUSEIPDB_API_KEY")),
        "anthropic": bool(os.getenv("ANTHROPIC_API_KEY")),
    }
    return {"status": "ok", "configured_apis": configured}


@app.post("/analyze")
async def analyze(
    file: UploadFile | None = File(default=None),
    raw_email: str | None = Form(default=None),
):
    # Accept either an uploaded .eml file or pasted raw text
    if file is not None:
        content = await file.read()
        if not content:
            raise HTTPException(400, "Uploaded file is empty")
        parsed = parse_email(content)
    elif raw_email:
        if not raw_email.strip():
            raise HTTPException(400, "Email text is empty")
        parsed = parse_email(raw_email)
    else:
        raise HTTPException(400, "Provide either a file upload or raw_email text")

    urls = parsed.get("urls", [])[:10]   # limit to avoid rate limits
    ips = parsed.get("ips", [])[:5]

    async with aiohttp.ClientSession() as session:
        # Run all OSINT + AI checks in parallel
        tasks = [
            # VirusTotal URLs (first 5 only to stay within rate limits)
            *[virustotal.scan_url(session, u) for u in urls[:5]],
            # VirusTotal IPs
            *[virustotal.scan_ip(session, ip) for ip in ips],
            # AbuseIPDB IPs
            *[abuseipdb.check_ip(session, ip) for ip in ips],
            # AI analysis
            analyze_email(parsed),
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

    # Separate results
    vt_url_count = len(urls[:5])
    vt_ip_count = len(ips)
    abuse_count = len(ips)

    idx = 0
    vt_url_results = _safe_results(results, idx, vt_url_count)
    idx += vt_url_count

    vt_ip_results = _safe_results(results, idx, vt_ip_count)
    idx += vt_ip_count

    abuseipdb_results = _safe_results(results, idx, abuse_count)
    idx += abuse_count

    ai_result = results[idx] if idx < len(results) else {}
    if isinstance(ai_result, Exception):
        ai_result = {"status": "error", "error": str(ai_result), "verdict": "UNKNOWN", "confidence": 0}

    risk = calculate_score(parsed, vt_url_results, vt_ip_results, abuseipdb_results, ai_result)

    return {
        "risk": risk,
        "headers": parsed["headers"],
        "urls": _annotate_urls(urls, vt_url_results),
        "ips": _annotate_ips(ips, vt_ip_results, abuseipdb_results),
        "attachments": parsed.get("attachments", []),
        "indicators": parsed.get("indicators", []),
        "ai_analysis": ai_result,
    }


def _safe_results(results: list, start: int, count: int) -> list[dict]:
    out = []
    for i in range(start, start + count):
        r = results[i] if i < len(results) else {}
        out.append({} if isinstance(r, Exception) else r)
    return out


def _annotate_urls(urls: list[str], vt_results: list[dict]) -> list[dict]:
    vt_map = {r.get("url"): r for r in vt_results}
    annotated = []
    for url in urls:
        annotated.append({
            "url": url,
            "virustotal": vt_map.get(url, {"status": "not_checked"}),
        })
    return annotated


def _annotate_ips(ips: list[str], vt_results: list[dict], abuse_results: list[dict]) -> list[dict]:
    vt_map = {r.get("ip"): r for r in vt_results}
    abuse_map = {r.get("ip"): r for r in abuse_results}
    return [
        {
            "ip": ip,
            "virustotal": vt_map.get(ip, {"status": "not_checked"}),
            "abuseipdb": abuse_map.get(ip, {"status": "not_checked"}),
        }
        for ip in ips
    ]
