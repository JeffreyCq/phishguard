import aiohttp
import asyncio
import logging
import os

logger = logging.getLogger(__name__)

API_KEY = os.getenv("URLSCAN_API_KEY", "")
BASE_URL = "https://urlscan.io/api/v1"


async def scan_url(session: aiohttp.ClientSession, url: str) -> dict:
    if not API_KEY:
        return {"status": "not_configured", "url": url}

    headers = {
        "API-Key": API_KEY,
        "Content-Type": "application/json",
    }

    try:
        # Submit scan
        async with session.post(
            f"{BASE_URL}/scan/",
            headers=headers,
            json={"url": url, "visibility": "private"},
            timeout=aiohttp.ClientTimeout(total=15)
        ) as resp:
            if resp.status not in (200, 201):
                return {"status": "error", "url": url, "code": resp.status}
            data = await resp.json()
            result_url = data.get("result", "")
            uuid = data.get("uuid", "")

        if not uuid:
            return {"status": "submitted", "url": url}

        # Wait briefly then poll for result (up to 20s)
        await asyncio.sleep(10)
        async with session.get(
            f"{BASE_URL}/result/{uuid}/",
            timeout=aiohttp.ClientTimeout(total=15)
        ) as result_resp:
            if result_resp.status != 200:
                return {"status": "pending", "url": url, "uuid": uuid, "result_url": result_url}
            result = await result_resp.json()
            verdicts = result.get("verdicts", {}).get("overall", {})
            page = result.get("page", {})
            return {
                "status": "ok",
                "url": url,
                "uuid": uuid,
                "result_url": result_url,
                "malicious": verdicts.get("malicious", False),
                "score": verdicts.get("score", 0),
                "tags": verdicts.get("tags", []),
                "final_url": page.get("url", url),
                "ip": page.get("ip", ""),
                "country": page.get("country", ""),
                "screenshot": f"https://urlscan.io/screenshots/{uuid}.png",
            }
    except Exception:
        logger.exception("urlscan lookup failed for %s", url)
        return {"status": "error", "url": url, "error": "urlscan lookup failed"}
