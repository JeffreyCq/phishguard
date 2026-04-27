import logging
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import aiosmtplib

logger = logging.getLogger(__name__)

SMTP_HOST     = os.getenv("SMTP_HOST", "")
SMTP_PORT     = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER     = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM     = os.getenv("SMTP_FROM", "scan@maildefender.local")
SMTP_USE_TLS  = os.getenv("SMTP_USE_TLS", "true").lower() == "true"

_LEVEL_COLORS = {
    "CRITICAL": "#dc2626",
    "HIGH":     "#ea580c",
    "MEDIUM":   "#d97706",
    "LOW":      "#16a34a",
}

_VERDICT_COLORS = {
    "PHISHING":    "#dc2626",
    "SUSPICIOUS":  "#ea580c",
    "LIKELY_SAFE": "#d97706",
    "SAFE":        "#16a34a",
    "UNKNOWN":     "#64748b",
}


def _build_html(subject: str, sender: str, analysis: dict) -> str:
    risk       = analysis.get("risk", {})
    ai         = analysis.get("ai_result", {})
    indicators = analysis.get("parsed", {}).get("indicators", [])
    urls       = analysis.get("urls", [])
    vt_urls    = analysis.get("vt_url_results", [])

    score   = risk.get("score", 0)
    level   = risk.get("level", "UNKNOWN")
    verdict = ai.get("verdict", "UNKNOWN")

    level_color   = _LEVEL_COLORS.get(level, "#64748b")
    verdict_color = _VERDICT_COLORS.get(verdict, "#64748b")

    flagged_urls = [r for r in vt_urls if r.get("flagged")]

    # Build indicators HTML
    indicators_html = ""
    if indicators:
        items = "".join(
            f'<li style="margin:4px 0;color:#fca5a5">{i}</li>' for i in indicators
        )
        indicators_html = f"""
        <tr><td style="padding:0 24px 16px">
          <p style="margin:0 0 8px;font-size:13px;color:#94a3b8;text-transform:uppercase;letter-spacing:.05em">
            Threat Indicators
          </p>
          <ul style="margin:0;padding-left:18px;font-size:14px">{items}</ul>
        </td></tr>"""

    # Build red flags HTML
    red_flags_html = ""
    red_flags = ai.get("red_flags", [])
    if red_flags:
        items = "".join(
            f'<li style="margin:4px 0;color:#fdba74">{f}</li>' for f in red_flags
        )
        red_flags_html = f"""
        <tr><td style="padding:0 24px 16px">
          <p style="margin:0 0 8px;font-size:13px;color:#94a3b8;text-transform:uppercase;letter-spacing:.05em">
            AI Red Flags
          </p>
          <ul style="margin:0;padding-left:18px;font-size:14px">{items}</ul>
        </td></tr>"""

    # Build flagged URLs HTML
    flagged_urls_html = ""
    if flagged_urls:
        items = "".join(
            f'<li style="margin:4px 0;font-family:monospace;color:#fca5a5;font-size:12px">{r.get("url","")}</li>'
            for r in flagged_urls
        )
        flagged_urls_html = f"""
        <tr><td style="padding:0 24px 16px">
          <p style="margin:0 0 8px;font-size:13px;color:#94a3b8;text-transform:uppercase;letter-spacing:.05em">
            Flagged URLs ({len(flagged_urls)})
          </p>
          <ul style="margin:0;padding-left:18px;font-size:14px">{items}</ul>
        </td></tr>"""

    tactics = ai.get("tactics", [])
    tactics_html = ""
    if tactics:
        badges = "".join(
            f'<span style="display:inline-block;margin:2px;padding:3px 10px;background:#1e3a5f;color:#93c5fd;border-radius:999px;font-size:12px">{t}</span>'
            for t in tactics
        )
        tactics_html = f"""
        <tr><td style="padding:0 24px 16px">
          <p style="margin:0 0 8px;font-size:13px;color:#94a3b8;text-transform:uppercase;letter-spacing:.05em">
            Detected Tactics
          </p>
          <div>{badges}</div>
        </td></tr>"""

    recommendation = ai.get("recommendation", "")
    reasoning      = ai.get("reasoning", "")
    confidence     = ai.get("confidence", 0)

    return f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#0f172a;font-family:Arial,Helvetica,sans-serif">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#0f172a;padding:24px 0">
  <tr><td align="center">
    <table width="580" cellpadding="0" cellspacing="0" style="background:#1e293b;border-radius:12px;overflow:hidden;border:1px solid #334155">

      <!-- Header -->
      <tr>
        <td style="background:#1d4ed8;padding:20px 24px">
          <table width="100%" cellpadding="0" cellspacing="0">
            <tr>
              <td>
                <p style="margin:0;color:#bfdbfe;font-size:12px;letter-spacing:.05em;text-transform:uppercase">MailDefender</p>
                <h1 style="margin:4px 0 0;color:#ffffff;font-size:20px;font-weight:700">Email Threat Analysis</h1>
              </td>
              <td align="right">
                <div style="display:inline-block;background:rgba(255,255,255,.15);padding:8px 16px;border-radius:8px;color:white;font-size:22px;font-weight:700">{score}<span style="font-size:13px;font-weight:400">/100</span></div>
              </td>
            </tr>
          </table>
        </td>
      </tr>

      <!-- Risk badge -->
      <tr>
        <td style="padding:20px 24px 8px;text-align:center">
          <div style="display:inline-block;background:{level_color}22;border:1px solid {level_color};color:{level_color};padding:8px 28px;border-radius:999px;font-size:16px;font-weight:700;letter-spacing:.05em">
            {level} RISK
          </div>
          &nbsp;
          <div style="display:inline-block;background:{verdict_color}22;border:1px solid {verdict_color};color:{verdict_color};padding:8px 28px;border-radius:999px;font-size:16px;font-weight:700;letter-spacing:.05em">
            {verdict}
          </div>
        </td>
      </tr>

      <!-- Email being analyzed -->
      <tr>
        <td style="padding:16px 24px">
          <table width="100%" cellpadding="0" cellspacing="0" style="background:#0f172a;border-radius:8px;border:1px solid #334155">
            <tr>
              <td style="padding:12px 16px;border-bottom:1px solid #334155">
                <span style="color:#64748b;font-size:12px;text-transform:uppercase;letter-spacing:.05em">Analyzed Email</span>
              </td>
            </tr>
            <tr>
              <td style="padding:10px 16px;border-bottom:1px solid #1e293b">
                <span style="color:#64748b;font-size:13px;width:60px;display:inline-block">From</span>
                <span style="color:#e2e8f0;font-size:13px">{sender}</span>
              </td>
            </tr>
            <tr>
              <td style="padding:10px 16px">
                <span style="color:#64748b;font-size:13px;width:60px;display:inline-block">Subject</span>
                <span style="color:#e2e8f0;font-size:13px">{subject}</span>
              </td>
            </tr>
          </table>
        </td>
      </tr>

      <!-- AI Reasoning -->
      <tr>
        <td style="padding:0 24px 16px">
          <p style="margin:0 0 8px;font-size:13px;color:#94a3b8;text-transform:uppercase;letter-spacing:.05em">
            AI Analysis — {confidence}% confidence
          </p>
          <p style="margin:0;font-size:14px;color:#cbd5e1;line-height:1.6;background:#0f172a;padding:12px 16px;border-radius:8px;border:1px solid #334155">
            {reasoning}
          </p>
        </td>
      </tr>

      {tactics_html}
      {red_flags_html}
      {indicators_html}
      {flagged_urls_html}

      <!-- Recommendation -->
      {"" if not recommendation else f'''
      <tr>
        <td style="padding:0 24px 20px">
          <div style="background:#1a2e1a;border:1px solid #166534;border-radius:8px;padding:12px 16px">
            <p style="margin:0 0 4px;font-size:12px;color:#4ade80;text-transform:uppercase;letter-spacing:.05em">Recommendation</p>
            <p style="margin:0;font-size:14px;color:#bbf7d0;line-height:1.5">{recommendation}</p>
          </div>
        </td>
      </tr>'''}

      <!-- Footer -->
      <tr>
        <td style="background:#0f172a;padding:16px 24px;border-top:1px solid #334155;text-align:center">
          <p style="margin:0;font-size:12px;color:#475569">
            Analyzed by <strong style="color:#818cf8">MailDefender</strong> — AI-powered phishing detection
          </p>
          <p style="margin:4px 0 0;font-size:11px;color:#334155">
            This is an automated analysis. Always apply critical judgment.
          </p>
        </td>
      </tr>

    </table>
  </td></tr>
</table>
</body>
</html>"""


async def send_analysis_reply(to_address: str, analysis: dict) -> bool:
    if not SMTP_HOST:
        logger.warning("SMTP_HOST not configured — cannot send reply to %s", to_address)
        return False

    parsed  = analysis.get("parsed", {})
    subject = parsed.get("headers", {}).get("subject", "(no subject)")
    sender  = parsed.get("headers", {}).get("from", "unknown sender")

    risk    = analysis.get("risk", {})
    level   = risk.get("score", 0)
    verdict = analysis.get("ai_result", {}).get("verdict", "UNKNOWN")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"[MailDefender] Analysis: {verdict} — {level}/100 risk"
    msg["From"]    = SMTP_FROM
    msg["To"]      = to_address

    html = _build_html(subject, sender, analysis)
    msg.attach(MIMEText(html, "html", "utf-8"))

    try:
        smtp_kwargs = dict(
            hostname=SMTP_HOST,
            port=SMTP_PORT,
            username=SMTP_USER or None,
            password=SMTP_PASSWORD or None,
        )
        if SMTP_USE_TLS:
            smtp_kwargs["use_tls"] = True
        else:
            smtp_kwargs["start_tls"] = True

        await aiosmtplib.send(msg, **smtp_kwargs)
        logger.info("Reply sent to %s", to_address)
        return True
    except Exception as exc:
        logger.error("Failed to send reply to %s: %s", to_address, exc)
        return False
