import aiohttp
import base64
import os
from typing import Optional

API_KEY = os.getenv("VIRUSTOTAL_API_KEY", "")
BASE_URL = "https://www.virustotal.com/api/v3"


async def scan_url(session: aiohttp.ClientSession, url: str) -> dict:
    if not API_KEY:
        return {"status": "not_configured", "url": url}

    # VT uses base64url-encoded URL as ID
    url_id = base64.urlsafe_b64encode(url.encode()).decode().rstrip("=")
    headers = {"x-apikey": API_KEY}

    try:
        async with session.get(
            f"{BASE_URL}/urls/{url_id}",
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=15)
        ) as resp:
            if resp.status == 404:
                # Submit URL for scanning
                async with session.post(
                    f"{BASE_URL}/urls",
                    headers=headers,
                    data={"url": url},
                    timeout=aiohttp.ClientTimeout(total=15)
                ) as post_resp:
                    return {"status": "submitted", "url": url}

            if resp.status != 200:
                return {"status": "error", "url": url, "code": resp.status}

            data = await resp.json()
            stats = data.get("data", {}).get("attributes", {}).get("last_analysis_stats", {})
            return {
                "status": "ok",
                "url": url,
                "malicious": stats.get("malicious", 0),
                "suspicious": stats.get("suspicious", 0),
                "harmless": stats.get("harmless", 0),
                "undetected": stats.get("undetected", 0),
                "total": sum(stats.values()),
                "flagged": stats.get("malicious", 0) > 0 or stats.get("suspicious", 0) > 2,
            }
    except Exception as e:
        return {"status": "error", "url": url, "error": str(e)}


async def scan_ip(session: aiohttp.ClientSession, ip: str) -> dict:
    if not API_KEY:
        return {"status": "not_configured", "ip": ip}

    headers = {"x-apikey": API_KEY}
    try:
        async with session.get(
            f"{BASE_URL}/ip_addresses/{ip}",
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=15)
        ) as resp:
            if resp.status != 200:
                return {"status": "error", "ip": ip, "code": resp.status}

            data = await resp.json()
            attrs = data.get("data", {}).get("attributes", {})
            stats = attrs.get("last_analysis_stats", {})
            return {
                "status": "ok",
                "ip": ip,
                "malicious": stats.get("malicious", 0),
                "suspicious": stats.get("suspicious", 0),
                "country": attrs.get("country", "Unknown"),
                "as_owner": attrs.get("as_owner", "Unknown"),
                "flagged": stats.get("malicious", 0) > 0,
            }
    except Exception as e:
        return {"status": "error", "ip": ip, "error": str(e)}
