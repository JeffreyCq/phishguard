import aiohttp
import logging
import os

logger = logging.getLogger(__name__)

API_KEY = os.getenv("ABUSEIPDB_API_KEY", "")
BASE_URL = "https://api.abuseipdb.com/api/v2"


async def check_ip(session: aiohttp.ClientSession, ip: str) -> dict:
    if not API_KEY:
        return {"status": "not_configured", "ip": ip}

    headers = {
        "Key": API_KEY,
        "Accept": "application/json",
    }

    try:
        async with session.get(
            f"{BASE_URL}/check",
            headers=headers,
            params={"ipAddress": ip, "maxAgeInDays": 90, "verbose": ""},
            timeout=aiohttp.ClientTimeout(total=15)
        ) as resp:
            if resp.status != 200:
                return {"status": "error", "ip": ip, "code": resp.status}

            data = await resp.json()
            d = data.get("data", {})
            score = d.get("abuseConfidenceScore", 0)
            return {
                "status": "ok",
                "ip": ip,
                "abuse_score": score,
                "country": d.get("countryCode", "Unknown"),
                "isp": d.get("isp", "Unknown"),
                "domain": d.get("domain", ""),
                "total_reports": d.get("totalReports", 0),
                "last_reported": d.get("lastReportedAt", ""),
                "flagged": score >= 25,
            }
    except Exception:
        logger.exception("AbuseIPDB lookup failed for %s", ip)
        return {"status": "error", "ip": ip, "error": "AbuseIPDB lookup failed"}
