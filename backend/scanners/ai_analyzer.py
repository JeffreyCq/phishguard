import os
import json
from groq import AsyncGroq

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

SYSTEM_PROMPT = """You are a cybersecurity expert specializing in phishing email detection and analysis.
You will be given parsed email data including headers, body text, URLs, and already-detected indicators.

Analyze this email and return ONLY a valid JSON object with this exact structure:
{
  "verdict": "PHISHING" | "SUSPICIOUS" | "LIKELY_SAFE" | "SAFE",
  "confidence": <integer 0-100>,
  "reasoning": "<2-3 sentence plain English explanation>",
  "tactics": ["<tactic1>", "<tactic2>"],
  "red_flags": ["<specific concern 1>", "<specific concern 2>"],
  "recommendation": "<one sentence action for the user>"
}

Possible tactics to detect (use exact strings when applicable):
- "urgency" (pressure to act fast)
- "fear" (threatens consequences)
- "impersonation" (pretends to be a trusted entity)
- "credential_harvesting" (asks for login/password)
- "brand_spoofing" (mimics known brand)
- "prize_scam" (fake prize/reward)
- "invoice_fraud" (fake invoice)
- "malware_delivery" (attachment-based attack)
- "url_obfuscation" (hides true destination)
- "authority" (fake official/government entity)

Be precise. Return ONLY the JSON — no markdown, no explanation outside the JSON."""


async def analyze_email(parsed_email: dict) -> dict:
    if not GROQ_API_KEY:
        return {
            "status": "not_configured",
            "verdict": "UNKNOWN",
            "confidence": 0,
            "reasoning": "AI analysis unavailable: GROQ_API_KEY not set.",
            "tactics": [],
            "red_flags": [],
            "recommendation": "Configure your Groq API key to enable AI analysis.",
        }

    client = AsyncGroq(api_key=GROQ_API_KEY)

    email_summary = {
        "from": parsed_email["headers"].get("from"),
        "reply_to": parsed_email["headers"].get("reply_to"),
        "subject": parsed_email["headers"].get("subject"),
        "spf": parsed_email["headers"].get("spf"),
        "dkim": parsed_email["headers"].get("dkim"),
        "dmarc": parsed_email["headers"].get("dmarc"),
        "from_reply_to_mismatch": parsed_email["headers"].get("from_reply_to_mismatch"),
        "urls_found": parsed_email.get("urls", [])[:15],
        "attachments": [
            {"filename": a["filename"], "suspicious": a["suspicious"]}
            for a in parsed_email.get("attachments", [])
        ],
        "indicators_detected": parsed_email.get("indicators", []),
        "body_text": parsed_email.get("body_text", "")[:3000],
    }

    user_prompt = f"Analyze this email:\n\n{json.dumps(email_summary, indent=2)}"

    try:
        response = await client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            max_tokens=1024,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
        )
        raw = response.choices[0].message.content.strip()

        result = json.loads(raw)
        result["status"] = "ok"
        return result

    except json.JSONDecodeError as e:
        return {"status": "error", "error": f"Failed to parse AI response: {e}", "verdict": "UNKNOWN", "confidence": 0}
    except Exception as e:
        return {"status": "error", "error": str(e), "verdict": "UNKNOWN", "confidence": 0}
