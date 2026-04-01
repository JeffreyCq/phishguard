"""
Risk scoring engine.
Combines signals from email parsing, OSINT APIs, and AI analysis
into a single 0–100 score with a categorical label.
"""


def calculate_score(
    parsed_email: dict,
    vt_url_results: list[dict],
    vt_ip_results: list[dict],
    abuseipdb_results: list[dict],
    ai_result: dict,
) -> dict:
    score = 0
    breakdown = []

    # --- Header / Auth signals ---
    headers = parsed_email.get("headers", {})

    spf = headers.get("spf", "none")
    if spf == "fail":
        score += 20
        breakdown.append({"label": "SPF Fail", "points": 20})
    elif spf == "softfail":
        score += 12
        breakdown.append({"label": "SPF SoftFail", "points": 12})
    elif spf == "none":
        score += 8
        breakdown.append({"label": "No SPF record", "points": 8})

    dkim = headers.get("dkim", "none")
    if dkim == "fail":
        score += 15
        breakdown.append({"label": "DKIM Invalid", "points": 15})
    elif dkim == "none":
        score += 5
        breakdown.append({"label": "No DKIM signature", "points": 5})

    dmarc = headers.get("dmarc", "none")
    if dmarc in ("fail", "none"):
        score += 8
        breakdown.append({"label": f"DMARC {dmarc}", "points": 8})

    if headers.get("from_reply_to_mismatch"):
        score += 20
        breakdown.append({"label": "From/Reply-To domain mismatch", "points": 20})

    # --- Attachment signals ---
    suspicious_attachments = [
        a for a in parsed_email.get("attachments", []) if a.get("suspicious")
    ]
    if suspicious_attachments:
        pts = min(25, len(suspicious_attachments) * 15)
        score += pts
        breakdown.append({"label": f"Suspicious attachment(s): {len(suspicious_attachments)}", "points": pts})

    # --- VirusTotal URL results ---
    flagged_urls = [r for r in vt_url_results if r.get("flagged")]
    if flagged_urls:
        pts = min(40, len(flagged_urls) * 20)
        score += pts
        breakdown.append({"label": f"VT: {len(flagged_urls)} malicious URL(s)", "points": pts})

    # --- VirusTotal IP results ---
    flagged_ips_vt = [r for r in vt_ip_results if r.get("flagged")]
    if flagged_ips_vt:
        pts = min(20, len(flagged_ips_vt) * 10)
        score += pts
        breakdown.append({"label": f"VT: {len(flagged_ips_vt)} malicious IP(s)", "points": pts})

    # --- AbuseIPDB results ---
    abused_ips = [r for r in abuseipdb_results if r.get("flagged")]
    if abused_ips:
        pts = min(20, len(abused_ips) * 10)
        score += pts
        breakdown.append({"label": f"AbuseIPDB: {len(abused_ips)} flagged IP(s)", "points": pts})

    # --- AI analysis ---
    ai_verdict = ai_result.get("verdict", "UNKNOWN")
    ai_confidence = ai_result.get("confidence", 0)

    if ai_verdict == "PHISHING":
        pts = int(30 * (ai_confidence / 100))
        score += pts
        breakdown.append({"label": f"AI verdict: PHISHING ({ai_confidence}% confidence)", "points": pts})
    elif ai_verdict == "SUSPICIOUS":
        pts = int(15 * (ai_confidence / 100))
        score += pts
        breakdown.append({"label": f"AI verdict: SUSPICIOUS ({ai_confidence}% confidence)", "points": pts})
    elif ai_verdict == "LIKELY_SAFE":
        # Slight reduction if AI thinks it's likely safe
        reduction = 5
        score = max(0, score - reduction)
        breakdown.append({"label": "AI verdict: LIKELY_SAFE", "points": -reduction})

    # --- URL shortener bonus ---
    shortener_indicators = [
        i for i in parsed_email.get("indicators", [])
        if "shortener" in i.get("message", "").lower()
    ]
    if shortener_indicators:
        pts = min(10, len(shortener_indicators) * 5)
        score += pts
        breakdown.append({"label": "URL shortener(s) detected", "points": pts})

    score = min(100, max(0, score))

    if score >= 70:
        level = "CRITICAL"
        color = "red"
    elif score >= 45:
        level = "HIGH"
        color = "orange"
    elif score >= 20:
        level = "MEDIUM"
        color = "yellow"
    else:
        level = "LOW"
        color = "green"

    return {
        "score": score,
        "level": level,
        "color": color,
        "breakdown": breakdown,
    }
