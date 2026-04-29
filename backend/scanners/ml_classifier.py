"""
ml_classifier.py — Calls the MailDefender ML microservice.

The service URL is read from ML_CLASSIFIER_URL env var
(default: http://ml-classifier:8001 for Docker, http://localhost:8001 for local dev).
"""

import os
import logging
import aiohttp

logger = logging.getLogger(__name__)

_BASE_URL = os.getenv("ML_CLASSIFIER_URL", "http://ml-classifier:8001")

THREAT_LABELS = {
    "legitimate":     {"level": 0, "label": "Legitimate"},
    "spam":           {"level": 1, "label": "Spam"},
    "phishing":       {"level": 2, "label": "Phishing"},
    "spear_phishing": {"level": 3, "label": "Spear Phishing"},
    "whaling":        {"level": 4, "label": "Whaling"},
}


async def classify_email(
    subject: str,
    sender: str,
    body: str,
    executives: list[dict] | None = None,
) -> dict:
    """
    Returns:
        {
            "threat_type":         "phishing",
            "threat_level":        2,
            "confidence":          0.997,
            "label":               "Phishing",
            "executives_detected": [],
            "score_boosted":       False,
            "scores":              {...},
            "status":              "ok" | "error",
        }
    """
    payload = {
        "subject":    subject or "",
        "sender":     sender or "",
        "body":       body or "",
        "executives": executives or [],
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{_BASE_URL}/classify",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status != 200:
                    logger.warning("ML classifier returned %s", resp.status)
                    return _error_result()
                data = await resp.json()

        threat = data.get("threat_type", "legitimate")
        data["label"]  = THREAT_LABELS.get(threat, {}).get("label", threat)
        data["status"] = "ok"
        return data

    except Exception as exc:
        logger.warning("ML classifier unavailable: %s", exc)
        return _error_result()


def _error_result() -> dict:
    return {
        "threat_type":         "unknown",
        "threat_level":        -1,
        "confidence":          0.0,
        "label":               "Unknown",
        "executives_detected": [],
        "score_boosted":       False,
        "scores":              {},
        "status":              "error",
    }
