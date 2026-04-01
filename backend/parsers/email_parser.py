import email
import re
import base64
import quopri
from email import policy
from email.parser import BytesParser, Parser
from urllib.parse import urlparse
from typing import Optional


URL_REGEX = re.compile(
    r'https?://[^\s\'"<>(){}\[\]\\,;]+'
    r'|(?<!\w)www\.[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}[^\s\'"<>(){}\[\]\\,;]*',
    re.IGNORECASE
)

IP_REGEX = re.compile(
    r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}'
    r'(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b'
)

PRIVATE_IP_RANGES = re.compile(
    r'^(10\.|172\.(1[6-9]|2[0-9]|3[01])\.|192\.168\.|127\.|0\.0\.0\.0)'
)


def parse_email(raw: bytes | str) -> dict:
    if isinstance(raw, bytes):
        msg = BytesParser(policy=policy.default).parsebytes(raw)
    else:
        msg = Parser(policy=policy.default).parsestr(raw)

    headers = _extract_headers(msg)
    body_text, body_html = _extract_body(msg)
    urls = _extract_urls(body_text, body_html)
    ips = _extract_ips(msg)
    attachments = _extract_attachments(msg)
    indicators = _basic_indicators(headers, urls, ips, attachments)

    return {
        "headers": headers,
        "body_text": body_text[:5000],
        "urls": urls,
        "ips": ips,
        "attachments": attachments,
        "indicators": indicators,
    }


def _extract_headers(msg) -> dict:
    from_addr = str(msg.get("From", ""))
    reply_to = str(msg.get("Reply-To", ""))
    to_addr = str(msg.get("To", ""))
    subject = str(msg.get("Subject", ""))
    date = str(msg.get("Date", ""))
    message_id = str(msg.get("Message-ID", ""))

    # Parse Authentication-Results for SPF/DKIM/DMARC
    auth_results = str(msg.get("Authentication-Results", ""))
    spf = _parse_auth_result(auth_results, "spf")
    dkim = _parse_auth_result(auth_results, "dkim")
    dmarc = _parse_auth_result(auth_results, "dmarc")

    # Detect from/reply-to mismatch
    from_domain = _extract_domain_from_addr(from_addr)
    reply_to_domain = _extract_domain_from_addr(reply_to) if reply_to else None
    mismatch = bool(reply_to_domain and from_domain and reply_to_domain != from_domain)

    # Collect all Received headers
    received_headers = msg.get_all("Received") or []

    return {
        "from": from_addr,
        "reply_to": reply_to,
        "to": to_addr,
        "subject": subject,
        "date": date,
        "message_id": message_id,
        "spf": spf,
        "dkim": dkim,
        "dmarc": dmarc,
        "from_domain": from_domain,
        "reply_to_domain": reply_to_domain,
        "from_reply_to_mismatch": mismatch,
        "received_count": len(received_headers),
        "x_mailer": str(msg.get("X-Mailer", "")),
        "x_originating_ip": str(msg.get("X-Originating-IP", "")),
        "authentication_results": auth_results,
    }


def _parse_auth_result(auth_str: str, check: str) -> str:
    pattern = re.compile(rf'{check}=(\w+)', re.IGNORECASE)
    match = pattern.search(auth_str)
    if match:
        return match.group(1).lower()
    return "none"


def _extract_domain_from_addr(addr: str) -> Optional[str]:
    match = re.search(r'@([\w.-]+)', addr)
    if match:
        return match.group(1).lower()
    return None


def _extract_body(msg) -> tuple[str, str]:
    body_text = ""
    body_html = ""

    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            if ctype == "text/plain" and not body_text:
                body_text = _decode_part(part)
            elif ctype == "text/html" and not body_html:
                body_html = _decode_part(part)
    else:
        ctype = msg.get_content_type()
        if ctype == "text/html":
            body_html = _decode_part(msg)
        else:
            body_text = _decode_part(msg)

    # Strip HTML tags for text extraction from HTML body
    if not body_text and body_html:
        body_text = re.sub(r'<[^>]+>', ' ', body_html)
        body_text = re.sub(r'\s+', ' ', body_text).strip()

    return body_text, body_html


def _decode_part(part) -> str:
    try:
        payload = part.get_payload(decode=True)
        if payload is None:
            return ""
        charset = part.get_content_charset() or "utf-8"
        return payload.decode(charset, errors="replace")
    except Exception:
        return ""


def _extract_urls(body_text: str, body_html: str) -> list[str]:
    combined = body_text + " " + body_html
    # Also extract href values from HTML
    href_matches = re.findall(r'href=["\']([^"\']+)["\']', body_html, re.IGNORECASE)
    raw_urls = set(URL_REGEX.findall(combined)) | set(href_matches)

    cleaned = []
    for url in raw_urls:
        url = url.strip().rstrip(".,;")
        if not url.startswith("http"):
            url = "http://" + url
        if len(url) > 2000:
            continue
        cleaned.append(url)

    return list(set(cleaned))[:50]  # cap at 50 URLs


def _extract_ips(msg) -> list[str]:
    received_headers = msg.get_all("Received") or []
    x_orig = str(msg.get("X-Originating-IP", ""))
    all_text = " ".join(received_headers) + " " + x_orig

    found = set(IP_REGEX.findall(all_text))
    # Filter out private/loopback IPs
    public_ips = [ip for ip in found if not PRIVATE_IP_RANGES.match(ip)]
    return list(public_ips)[:20]


def _extract_attachments(msg) -> list[dict]:
    attachments = []
    if not msg.is_multipart():
        return attachments

    for part in msg.walk():
        disposition = str(part.get_content_disposition() or "")
        if "attachment" in disposition or part.get_filename():
            filename = part.get_filename() or "unknown"
            ctype = part.get_content_type()
            payload = part.get_payload(decode=True) or b""
            size = len(payload)

            # Simple hash
            import hashlib
            sha256 = hashlib.sha256(payload).hexdigest() if payload else ""

            attachments.append({
                "filename": filename,
                "content_type": ctype,
                "size_bytes": size,
                "sha256": sha256,
                "suspicious": _is_suspicious_attachment(filename, ctype),
            })

    return attachments


SUSPICIOUS_EXTENSIONS = {
    ".exe", ".scr", ".bat", ".cmd", ".com", ".pif", ".vbs", ".js",
    ".jar", ".ps1", ".hta", ".msi", ".dll", ".iso", ".img",
    ".docm", ".xlsm", ".pptm", ".xls", ".doc",
}


def _is_suspicious_attachment(filename: str, ctype: str) -> bool:
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return ext in SUSPICIOUS_EXTENSIONS or "macro" in ctype.lower()


def _basic_indicators(headers: dict, urls: list, ips: list, attachments: list) -> list[dict]:
    indicators = []

    if headers["spf"] in ("fail", "softfail"):
        indicators.append({"severity": "high", "type": "auth", "message": f"SPF check failed ({headers['spf']})"})
    elif headers["spf"] == "none":
        indicators.append({"severity": "medium", "type": "auth", "message": "No SPF record found"})

    if headers["dkim"] == "fail":
        indicators.append({"severity": "high", "type": "auth", "message": "DKIM signature invalid"})
    elif headers["dkim"] == "none":
        indicators.append({"severity": "low", "type": "auth", "message": "No DKIM signature"})

    if headers["dmarc"] in ("fail", "none"):
        indicators.append({"severity": "medium", "type": "auth", "message": f"DMARC check: {headers['dmarc']}"})

    if headers["from_reply_to_mismatch"]:
        indicators.append({"severity": "high", "type": "spoofing", "message": f"Reply-To domain ({headers['reply_to_domain']}) differs from From domain ({headers['from_domain']})"})

    suspicious_atts = [a for a in attachments if a["suspicious"]]
    if suspicious_atts:
        for att in suspicious_atts:
            indicators.append({"severity": "high", "type": "attachment", "message": f"Suspicious attachment: {att['filename']}"})

    if len(urls) > 10:
        indicators.append({"severity": "medium", "type": "urls", "message": f"Large number of URLs found ({len(urls)})"})

    # Check for URL shorteners
    shorteners = ["bit.ly", "tinyurl", "t.co", "ow.ly", "goo.gl", "rebrand.ly", "cutt.ly"]
    for url in urls:
        for s in shorteners:
            if s in url.lower():
                indicators.append({"severity": "medium", "type": "urls", "message": f"URL shortener detected: {url}"})
                break

    if headers["x_originating_ip"] and not PRIVATE_IP_RANGES.match(headers["x_originating_ip"]):
        indicators.append({"severity": "info", "type": "network", "message": f"Originating IP: {headers['x_originating_ip']}"})

    return indicators
