import os
import json
import aiohttp

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")

SYSTEM_PROMPT = """You are a cybersecurity expert specializing in phishing email detection.
Analyze the provided email data and return ONLY a valid JSON object with this exact structure:
{
  "verdict": "PHISHING" | "SUSPICIOUS" | "LIKELY_SAFE" | "SAFE",
  "confidence": <integer 0-100>,
  "reasoning": "<2-3 sentence plain English explanation>",
  "tactics": ["<tactic1>", "<tactic2>"],
  "red_flags": ["<specific concern 1>", "<specific concern 2>"],
  "recommendation": "<one sentence action for the user>"
}

Tactics to detect (use exact strings when applicable):
urgency, fear, impersonation, credential_harvesting, brand_spoofing,
prize_scam, invoice_fraud, malware_delivery, url_obfuscation, authority

Return ONLY the JSON — no markdown, no text outside the JSON object."""


async def analyze_email(parsed_email: dict) -> dict:
    email_summary = {
        "from": parsed_email["headers"].get("from"),
        "reply_to": parsed_email["headers"].get("reply_to"),
        "subject": parsed_email["headers"].get("subject"),
        "spf": parsed_email["headers"].get("spf"),
        "dkim": parsed_email["headers"].get("dkim"),
        "dmarc": parsed_email["headers"].get("dmarc"),
        "from_reply_to_mismatch": parsed_email["headers"].get("from_reply_to_mismatch"),
        "urls_found": parsed_email.get("urls", [])[:10],
        "attachments": [
            {"filename": a["filename"], "suspicious": a["suspicious"]}
            for a in parsed_email.get("attachments", [])
        ],
        "indicators_detected": parsed_email.get("indicators", []),
        "body_text": parsed_email.get("body_text", "")[:2000],
    }

    user_prompt = f"Analyze this email for phishing:\n\n{json.dumps(email_summary, indent=2)}"

    try:
        async with aiohttp.ClientSession() as session:
            payload = {
                "model": OLLAMA_MODEL,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                "stream": False,
                "format": "json",
                "options": {
                    "temperature": 0.1,
                    "num_predict": 512,
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

        raw = data["message"]["content"].strip()
        result = json.loads(raw)
        result["status"] = "ok"
        return result

    except json.JSONDecodeError as e:
        return _error(f"Failed to parse AI response: {e}")
    except Exception as e:
        return _error(str(e))


def _error(msg: str) -> dict:
    return {
        "status": "error",
        "error": msg,
        "verdict": "UNKNOWN",
        "confidence": 0,
        "reasoning": "",
        "tactics": [],
        "red_flags": [],
        "recommendation": "",
    }
