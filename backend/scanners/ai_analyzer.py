import os
import json
import aiohttp

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
OLLAMA_MODEL    = os.getenv("OLLAMA_MODEL",    "qwen2.5:3b")

SYSTEM_PROMPT = """You are a cybersecurity expert specializing in email threat analysis.
Analyze the provided email data and return ONLY a valid JSON object with this exact structure:
{
  "verdict": "PHISHING" | "SUSPICIOUS" | "LIKELY_SAFE" | "SAFE",
  "confidence": <integer 0-100>,
  "reasoning": "<2-3 sentence plain English explanation>",
  "tactics": ["<tactic1>"],
  "red_flags": ["<specific concern 1>"],
  "recommendation": "<one sentence action for the user>",

  "spam_verdict": "SPAM" | "LIKELY_SPAM" | "NOT_SPAM",
  "spam_confidence": <integer 0-100>,
  "spam_signals": ["<signal1>"]
}

PHISHING tactics (use exact strings): urgency, fear, impersonation, credential_harvesting,
brand_spoofing, prize_scam, invoice_fraud, malware_delivery, url_obfuscation, authority

SPAM signals (use exact strings when applicable): bulk_headers, tracking_pixel,
mass_marketing_platform, unsubscribe_link, promotional_language, generic_greeting,
unsolicited_contact, url_tracking, suspicious_sender_domain, excessive_images

IMPORTANT DISTINCTIONS:
- PHISHING = malicious intent to steal data/credentials/money. Dangerous.
- SPAM = unsolicited commercial or irrelevant email. Annoying but not necessarily dangerous.
- An email can be SPAM without being PHISHING, or both at the same time.
- A legitimate newsletter is NOT_SPAM even if unsolicited.

Return ONLY the JSON — no markdown, no text outside the JSON object."""


async def analyze_email(parsed_email: dict) -> dict:
    email_summary = {
        "from":                   parsed_email["headers"].get("from"),
        "reply_to":               parsed_email["headers"].get("reply_to"),
        "subject":                parsed_email["headers"].get("subject"),
        "spf":                    parsed_email["headers"].get("spf"),
        "dkim":                   parsed_email["headers"].get("dkim"),
        "dmarc":                  parsed_email["headers"].get("dmarc"),
        "from_reply_to_mismatch": parsed_email["headers"].get("from_reply_to_mismatch"),
        "urls_found":             parsed_email.get("urls", [])[:10],
        "attachments": [
            {"filename": a["filename"], "suspicious": a["suspicious"]}
            for a in parsed_email.get("attachments", [])
        ],
        "indicators_detected": parsed_email.get("indicators", []),
        "body_text":           parsed_email.get("body_text", "")[:2000],
    }

    user_prompt = f"Analyze this email for phishing AND spam:\n\n{json.dumps(email_summary, indent=2)}"

    try:
        async with aiohttp.ClientSession() as session:
            payload = {
                "model":  OLLAMA_MODEL,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user",   "content": user_prompt},
                ],
                "stream": False,
                "format": "json",
                "options": {
                    "temperature": 0.1,
                    "num_predict": 768,
                },
            }
            async with session.post(
                f"{OLLAMA_BASE_URL}/api/chat",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=360),
            ) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    return _error(f"Ollama returned {resp.status}: {text[:200]}")
                data = await resp.json()

        raw    = data["message"]["content"].strip()
        result = json.loads(raw)

        # Ensure spam fields exist with defaults if model omitted them
        result.setdefault("spam_verdict",    "NOT_SPAM")
        result.setdefault("spam_confidence", 0)
        result.setdefault("spam_signals",    [])
        result["status"] = "ok"
        return result

    except json.JSONDecodeError as e:
        return _error(f"Failed to parse AI response: {e}")
    except Exception as e:
        return _error(str(e))


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
    }
