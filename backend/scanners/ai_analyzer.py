"""
ai_analyzer.py — Calls the MailDefender ML microservice (DistilBERT/ONNX)
instead of a local generative LLM. Much lighter on resources.

Microservice API:
  POST /classify  { subject, sender, body, executives[] }
  → { threat_type, threat_level, confidence, scores, ... }
"""

import os
import aiohttp

ML_SERVICE_URL = os.getenv("ML_SERVICE_URL", "https://ml.maildefender.xyz")

# ── Verdict mapping ────────────────────────────────────────────────────────────

def _map_phishing_verdict(threat_type: str, confidence: float, scores: dict) -> str:
    """Map ML threat_type → phishing verdict string."""
    if threat_type in ("whaling", "spear_phishing"):
        return "PHISHING"
    if threat_type == "phishing":
        return "PHISHING" if confidence >= 0.65 else "SUSPICIOUS"
    if threat_type == "spam":
        combined_phishing = (
            scores.get("phishing", 0)
            + scores.get("spear_phishing", 0)
            + scores.get("whaling", 0)
        )
        return "SUSPICIOUS" if combined_phishing > 0.30 else "LIKELY_SAFE"
    # legitimate
    return "SAFE" if confidence >= 0.80 else "LIKELY_SAFE"


def _map_spam_verdict(threat_type: str, scores: dict) -> tuple[str, int]:
    """Return (spam_verdict, spam_confidence_pct)."""
    spam_score = scores.get("spam", 0.0)
    if threat_type == "spam" or spam_score >= 0.50:
        return "SPAM", round(max(spam_score, 0.50) * 100)
    if spam_score >= 0.25:
        return "LIKELY_SPAM", round(spam_score * 100)
    return "NOT_SPAM", round((1 - spam_score) * 100)


# ── Reasoning templates ────────────────────────────────────────────────────────

_REASONING = {
    "whaling": (
        "This email exhibits strong indicators of a whaling attack targeting a high-value individual. "
        "The content, sender, and structure are consistent with a sophisticated social engineering attempt against an executive."
    ),
    "spear_phishing": (
        "This email shows characteristics of a targeted spear-phishing attack. "
        "The level of personalization suggests the sender conducted prior reconnaissance on the target."
    ),
    "phishing": (
        "This email contains multiple indicators of a phishing attempt. "
        "The sender identity, subject line, and content patterns match known phishing templates."
    ),
    "spam": (
        "This email is classified as unsolicited commercial email. "
        "No direct malicious intent was detected, but it exhibits bulk mailing characteristics."
    ),
    "legitimate": (
        "This email shows no significant threat indicators and appears to be legitimate correspondence. "
        "Authentication checks and content analysis did not reveal suspicious patterns."
    ),
}

_RECOMMENDATION = {
    "whaling":        "Do not reply or act on this email — report it immediately to your security team.",
    "spear_phishing": "Do not click any links or provide information — report this email as phishing.",
    "phishing":       "Do not click any links or enter credentials — delete and report as phishing.",
    "spam":           "This appears to be spam. You can safely unsubscribe or mark it as junk.",
    "legitimate":     "This email appears safe. Always verify unexpected requests through a separate channel.",
}


# ── Derived signals ────────────────────────────────────────────────────────────

def _infer_tactics(threat_type: str, parsed_email: dict) -> list[str]:
    tactics: set[str] = set()
    headers  = parsed_email.get("headers", {})
    body     = parsed_email.get("body_text", "").lower()
    urls     = parsed_email.get("urls", [])

    if threat_type in ("spear_phishing", "whaling"):
        tactics.add("impersonation")
    if threat_type == "whaling":
        tactics.add("authority")
    if headers.get("spf") in ("fail", "softfail"):
        tactics.add("impersonation")
    if headers.get("from_reply_to_mismatch"):
        tactics.add("impersonation")
    if any(w in body for w in ("urgent", "immediately", "expires", "limited time", "act now")):
        tactics.add("urgency")
    if any(w in body for w in ("verify", "confirm", "login", "password", "credentials")):
        tactics.add("credential_harvesting")
    if any(s in u for u in urls for s in ("bit.ly", "tinyurl", "goo.gl", "t.co", "ow.ly")):
        tactics.add("url_obfuscation")
    if any(a.get("suspicious") for a in parsed_email.get("attachments", [])):
        tactics.add("malware_delivery")
    if any(w in body for w in ("you've won", "congratulations", "prize", "reward")):
        tactics.add("prize_scam")
    if any(w in body for w in ("invoice", "payment due", "overdue")):
        tactics.add("invoice_fraud")

    return list(tactics)


def _infer_red_flags(threat_type: str, parsed_email: dict, scores: dict) -> list[str]:
    flags: list[str] = []
    headers = parsed_email.get("headers", {})

    if headers.get("spf") in ("fail", "softfail"):
        flags.append(f"SPF {headers['spf']} — sender may not be authorized for this domain")
    if headers.get("dkim") == "fail":
        flags.append("DKIM signature verification failed")
    if headers.get("dmarc") == "fail":
        flags.append("DMARC policy violation detected")
    if headers.get("from_reply_to_mismatch"):
        from_d  = headers.get("from_domain", "?")
        reply_d = headers.get("reply_to_domain", "?")
        flags.append(f"From domain ({from_d}) differs from Reply-To domain ({reply_d})")
    if threat_type == "whaling":
        flags.append("Email targets an executive profile — whaling attack pattern detected")
    if threat_type == "spear_phishing":
        flags.append("Personalized targeting indicates prior reconnaissance of the recipient")
    for att in parsed_email.get("attachments", []):
        if att.get("suspicious"):
            flags.append(f"Suspicious attachment: {att['filename']}")
            break
    # Append structural indicators as additional flags (cap total at 6)
    for ind in parsed_email.get("indicators", []):
        msg = ind.get("message", "") if isinstance(ind, dict) else str(ind)
        if msg and len(flags) < 6:
            flags.append(msg)

    return flags


def _infer_spam_signals(parsed_email: dict, scores: dict) -> list[str]:
    if scores.get("spam", 0) < 0.20:
        return []

    signals: list[str] = []
    body = (parsed_email.get("body_text", "") + " ".join(
        str(v) for v in parsed_email.get("headers", {}).values()
    )).lower()

    if "width=1" in body or "height=1" in body or "tracking" in body:
        signals.append("tracking_pixel")
    if "unsubscribe" in body:
        signals.append("unsubscribe_link")
    if any(p in body for p in ("sendcloud", "sendgrid", "mailchimp", "klaviyo", "brevo", "mailgun")):
        signals.append("mass_marketing_platform")
    if "bulk" in body or "precedence" in body:
        signals.append("bulk_headers")
    if len(parsed_email.get("urls", [])) > 4:
        signals.append("url_tracking")
    if parsed_email.get("headers", {}).get("from_reply_to_mismatch"):
        signals.append("suspicious_sender_domain")
    if any(w in body for w in ("limited offer", "sale", "discount", "% off", "buy now")):
        signals.append("promotional_language")

    return signals


# ── Main entry point ───────────────────────────────────────────────────────────

async def analyze_email(parsed_email: dict) -> dict:
    headers  = parsed_email.get("headers", {})
    body     = parsed_email.get("body_text", "")[:1500]

    payload = {
        "subject": headers.get("subject", ""),
        "sender":  headers.get("from", ""),
        "body":    body,
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{ML_SERVICE_URL}/classify",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    return _error(f"ML service returned {resp.status}: {text[:200]}")
                ml = await resp.json()

    except Exception as exc:
        return _error(str(exc))

    threat_type = ml.get("threat_type", "legitimate")
    confidence  = ml.get("confidence", 0.0)
    scores      = ml.get("scores", {})
    conf_pct    = round(confidence * 100)

    verdict              = _map_phishing_verdict(threat_type, confidence, scores)
    spam_verdict, s_conf = _map_spam_verdict(threat_type, scores)

    return {
        "status":          "ok",
        "verdict":         verdict,
        "confidence":      conf_pct,
        "reasoning":       _REASONING.get(threat_type, _REASONING["legitimate"]),
        "tactics":         _infer_tactics(threat_type, parsed_email),
        "red_flags":       _infer_red_flags(threat_type, parsed_email, scores),
        "recommendation":  _RECOMMENDATION.get(threat_type, _RECOMMENDATION["legitimate"]),
        "spam_verdict":    spam_verdict,
        "spam_confidence": s_conf,
        "spam_signals":    _infer_spam_signals(parsed_email, scores),
        # Extra ML detail (passed through to API response)
        "ml_threat_type":  threat_type,
        "ml_threat_level": ml.get("threat_level", 0),
        "ml_scores":       {k: round(v * 100) for k, v in scores.items()},
    }


def _error(msg: str) -> dict:
    return {
        "status":          "error",
        "error":           msg,
        "verdict":         "UNKNOWN",
        "confidence":      0,
        "reasoning":       "",
        "tactics":         [],
        "red_flags":       [],
        "recommendation":  "",
        "spam_verdict":    "UNKNOWN",
        "spam_confidence": 0,
        "spam_signals":    [],
        "ml_threat_type":  "unknown",
        "ml_threat_level": -1,
        "ml_scores":       {},
    }
