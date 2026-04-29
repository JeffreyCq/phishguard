"""
build_dataset.py — Descarga SpamAssassin y genera datos sintéticos para las 5 clases.

Uso:
    python ml/build_dataset.py

Salida:
    ml/data/processed/dataset.csv   (columnas: text, label, label_name)
"""

import os
import tarfile
import urllib.request
import email
import re
import csv
import random
from pathlib import Path

# ─── Rutas ────────────────────────────────────────────────────────────────────
BASE = Path(__file__).parent
RAW_DIR = BASE / "data" / "raw"
OUT_DIR = BASE / "data" / "processed"
OUT_FILE = OUT_DIR / "dataset.csv"

RAW_DIR.mkdir(parents=True, exist_ok=True)
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ─── Clases ───────────────────────────────────────────────────────────────────
LABELS = {
    0: "legitimate",
    1: "spam",
    2: "phishing",
    3: "spear_phishing",
    4: "whaling",
}

# ─── Fuentes SpamAssassin (sin cuenta, descarga directa) ──────────────────────
SPAMASSASSIN_FILES = [
    ("20021010_easy_ham.tar.bz2",  "legitimate"),
    ("20030228_easy_ham.tar.bz2",  "legitimate"),
    ("20030228_hard_ham.tar.bz2",  "legitimate"),
    ("20021010_spam.tar.bz2",      "spam"),
    ("20030228_spam.tar.bz2",      "spam"),
    ("20050311_spam_2.tar.bz2",    "spam"),
]
SA_BASE_URL = "https://spamassassin.apache.org/old/publiccorpus/"


def download_spamassassin():
    print("\n[1/3] Descargando SpamAssassin Public Corpus...")
    for filename, _ in SPAMASSASSIN_FILES:
        dest = RAW_DIR / filename
        if dest.exists():
            print(f"  ✓ {filename} ya existe, saltando")
            continue
        url = SA_BASE_URL + filename
        print(f"  ↓ {filename}")
        try:
            urllib.request.urlretrieve(url, dest)
        except Exception as e:
            print(f"  ✗ Error descargando {filename}: {e}")


def extract_email_text(raw_bytes: bytes) -> str:
    """Extrae subject + body de un email en bytes."""
    try:
        msg = email.message_from_bytes(raw_bytes)
        subject = msg.get("Subject", "") or ""
        sender = msg.get("From", "") or ""

        body_parts = []
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    try:
                        body_parts.append(part.get_payload(decode=True).decode("utf-8", errors="ignore"))
                    except Exception:
                        pass
        else:
            try:
                body_parts.append(msg.get_payload(decode=True).decode("utf-8", errors="ignore"))
            except Exception:
                pass

        body = " ".join(body_parts)
        text = f"Subject: {subject}\nFrom: {sender}\n\n{body}"
        # Limpia y trunca
        text = re.sub(r"\s+", " ", text).strip()
        return text[:1500]
    except Exception:
        return ""


def parse_spamassassin() -> list[dict]:
    """Extrae emails de los .tar.bz2 de SpamAssassin."""
    print("\n[2/3] Procesando SpamAssassin...")
    records = []

    for filename, label_name in SPAMASSASSIN_FILES:
        path = RAW_DIR / filename
        if not path.exists():
            print(f"  ✗ No encontrado: {filename}")
            continue

        label_id = [k for k, v in LABELS.items() if v == label_name][0]
        count = 0
        try:
            with tarfile.open(path, "r:bz2") as tar:
                for member in tar.getmembers():
                    if member.isfile():
                        f = tar.extractfile(member)
                        if f:
                            raw = f.read()
                            text = extract_email_text(raw)
                            if len(text) > 50:
                                records.append({"text": text, "label": label_id, "label_name": label_name})
                                count += 1
        except Exception as e:
            print(f"  ✗ Error en {filename}: {e}")
            continue

        print(f"  ✓ {filename}: {count} emails")

    return records


# ─── Datos sintéticos para phishing / spear / whaling ─────────────────────────
# Generamos variaciones realistas basadas en patrones documentados de campañas
# reales. Es técnica estándar cuando no hay corpus público etiquetado.

# Emails legítimos sintéticos — especialmente cortos y directos.
# El corpus SpamAssassin solo tiene emails largos de 2002-2005,
# así que el modelo nunca aprendió que emails breves también son legítimos.
LEGITIMATE_TEMPLATES = [
    ("Meeting tomorrow at {time}",
     "Hi {name}, just a reminder about our {meeting} tomorrow at {time}. Please bring the {doc}. Thanks!"),
    ("Re: {project} update",
     "Hey {name}, quick update on {project} — we're on track for the {day} deadline. I'll send the full report by EOD. Let me know if you have questions. {sender}"),
    ("Lunch today?",
     "Hey, are you free for lunch today around {time}? Was thinking {place}. Let me know! {sender}"),
    ("Quick question about {topic}",
     "Hi {name}, do you have a few minutes to chat about {topic}? Nothing urgent, just wanted to get your input before the meeting. {sender}"),
    ("{project} — files attached",
     "Hi {name}, attaching the {doc} files we discussed. Let me know if you need anything else. Best, {sender}"),
    ("Out of office this {day}",
     "Hi team, just a heads up that I'll be out of office this {day}. {name} will be covering for me. Reach out to them for anything urgent. Thanks, {sender}"),
    ("Happy Birthday {name}!",
     "Hi {name}, wishing you a wonderful birthday! Hope you have a great day. From the whole team. {sender}"),
    ("Re: {project} — looks good",
     "{name}, I reviewed the {doc} and everything looks good. Just one small comment on page {page} — can we discuss? {sender}"),
    ("Weekly standup notes",
     "Hi all, here are the notes from today's standup: {name} is working on {project}, deadline is {day}. Next sync is {day2}. Let me know if I missed anything. {sender}"),
    ("Can you review this?",
     "Hey {name}, could you take a look at the {doc} when you have a chance? No rush, just want a second pair of eyes before I send it out. Thanks! {sender}"),
    ("Follow up from our call",
     "Hi {name}, great talking to you earlier. As discussed, I'll send over the {doc} by {day}. Let me know if you have any questions in the meantime. {sender}"),
    ("Approved — {project}",
     "Hi {name}, just wanted to let you know the {project} proposal has been approved. Well done! We can proceed with the next phase. {sender}"),
    ("Reminder: {event} on {day}",
     "Hi {name}, just a friendly reminder about the {event} on {day} at {time}. Location: {place}. Looking forward to seeing you there. {sender}"),
    ("Re: Vacation request",
     "Hi {name}, your vacation request for {day} through {day2} has been approved. Have a great trip! HR Team"),
    ("Welcome to the team, {name}!",
     "Hi {name}, we're thrilled to have you join us! Your first day is {day}. Please bring a valid ID. Your manager {sender} will meet you at reception at {time}."),
    ("IT: Password expiry reminder",
     "Hi {name}, your company password will expire in 14 days. Please update it by logging into the internal portal at intranet.company.com/password. IT Support"),
    ("Payroll processed for {month}",
     "Hi {name}, this is a confirmation that your payroll for {month} has been processed. Your net pay of ${amount} will be deposited on {day}. HR & Payroll"),
    ("Team lunch on {day}",
     "Hi everyone, we're doing a team lunch on {day} at {time} at {place}. Please RSVP by {day2}. Hope to see you all there! {sender}"),
    ("{project} — meeting notes",
     "Hi {name}, attaching the notes from our {project} meeting today. Action items: 1) {sender} to send {doc} by {day}. 2) {name} to review and respond. Let me know if anything is missing."),
    ("Thanks for your help!",
     "Hi {name}, just wanted to say thank you for your help with {project}. Really appreciate it. Couldn't have done it without you. {sender}"),
]


def _fill_legitimate(template_subject, template_body):
    names = ["Alex", "Jordan", "Sam", "Taylor", "Morgan", "Casey", "Riley",
             "Jamie", "Dana", "Chris", "Pat", "Robin", "Drew", "Avery"]
    senders = ["Mike", "Sarah", "David", "Emily", "James", "Lisa", "Tom",
               "Jennifer", "Robert", "Anna", "Kevin", "Maria"]
    projects = ["Q3 Report", "Website Redesign", "Marketing Campaign", "Product Launch",
                "Budget Review", "System Migration", "Client Proposal", "Annual Audit"]
    docs = ["report", "spreadsheet", "presentation", "contract", "brief", "draft", "proposal"]
    times = ["9am", "10am", "11am", "2pm", "3pm", "3:30pm", "4pm"]
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday",
            "tomorrow", "next week", "Friday afternoon"]
    meetings = ["weekly sync", "team standup", "project review",
                "one-on-one", "planning session", "client call"]
    places = ["The Italian Place", "Chipotle", "the office cafeteria",
              "Starbucks downstairs", "Conference Room B"]
    topics = ["the Q3 numbers", "the new process", "the project timeline",
              "the client feedback", "the budget"]
    months = ["January", "February", "March", "April", "May", "June",
              "July", "August", "September", "October", "November", "December"]
    events = ["team meeting", "company all-hands", "department standup",
              "quarterly review", "training session"]

    subs = {
        "{name}":    _rand(names),
        "{sender}":  _rand(senders),
        "{project}": _rand(projects),
        "{doc}":     _rand(docs),
        "{time}":    _rand(times),
        "{day}":     _rand(days),
        "{day2}":    _rand(days),
        "{meeting}": _rand(meetings),
        "{place}":   _rand(places),
        "{topic}":   _rand(topics),
        "{month}":   _rand(months),
        "{event}":   _rand(events),
        "{page}":    str(random.randint(2, 15)),
        "{amount}":  str(random.randint(2000, 8000)),
    }
    s = template_subject
    b = template_body
    for k, v in subs.items():
        s = s.replace(k, v)
        b = b.replace(k, v)
    return f"Subject: {s}\n\n{b}"


PHISHING_TEMPLATES = [
    ("Urgent: Verify your {bank} account",
     "Dear Customer, We detected unusual activity on your {bank} account. Click here to verify immediately: http://{fake_domain}/login or your account will be suspended within 24 hours. {bank} Security Team"),
    ("Your {service} account has been compromised",
     "Hello, Our systems detected unauthorized access to your {service} account. Please verify your identity at {fake_domain}/verify?token={token} to prevent permanent suspension."),
    ("Action required: {bank} account suspended",
     "Your account has been temporarily suspended due to suspicious activity. To restore access, confirm your details: {fake_domain}/restore. Failure to act within 48 hours will result in permanent closure."),
    ("Important: Update your payment information",
     "Dear valued customer, Your payment method on file for {service} has expired. Please update your billing information at {fake_domain}/billing to avoid service interruption."),
    ("[{service}] Confirm your email address",
     "Someone requested a password reset for your {service} account. If this was you, click to confirm: {fake_domain}/reset/{token}. If not, ignore this email (your account may be at risk)."),
    ("Tax refund notification - IRS",
     "The Internal Revenue Service has processed your tax refund of ${amount}. To receive your refund, please verify your bank account details at {fake_domain}/irs-refund."),
    ("Package delivery failed - Action needed",
     "We attempted to deliver your package but were unable to complete delivery. To reschedule, a small redelivery fee of $1.99 is required. Pay here: {fake_domain}/redeliver/{token}"),
    ("Your cloud storage is almost full",
     "Your {service} storage is 98% full. Upgrade now or your files will be deleted. Special offer: upgrade at {fake_domain}/upgrade and get 6 months free!"),
]

SPEAR_TEMPLATES = [
    ("Quick request - {exec_name}",
     "Hi {target_name}, This is {exec_name} from the office. I need you to process an urgent wire transfer of ${amount} to our new vendor. This is time sensitive - please confirm you can handle this right now. I'm in a meeting and can't take calls. Best, {exec_name}"),
    ("Confidential: Gift cards needed",
     "Hi {target_name}, I need a favor. Can you purchase {count} x ${card_value} Amazon gift cards for a client appreciation event? I'll reimburse you. Please send me the redemption codes as soon as possible. Keep this between us for now. Thanks, {exec_name}"),
    ("Fwd: Invoice #{inv_number} - Payment needed",
     "{target_name}, Please process the attached invoice #{inv_number} for ${amount} from {vendor}. This is for the project we discussed. Wire to: Account {account_num}, Routing {routing_num}. Deadline is today. {exec_name}"),
    ("Updated banking details for {vendor}",
     "Hi {target_name}, Please be informed that our banking details have changed effective immediately. All future payments to {vendor} should be sent to: Bank: {bank}, Account: {account_num}, Routing: {routing_num}. Please update your records and process pending invoice #{inv_number}. {exec_name}, {vendor} Accounts"),
    ("HR: W2 / Tax documents request",
     "Hello {target_name}, As part of our annual audit, we need to verify employee tax information. Please send your W2 forms and last 3 pay stubs to {fake_email} by end of day. This is required for compliance. HR Department"),
    ("Re: Our meeting tomorrow",
     "{target_name}, Following up on our call. As discussed, please transfer the security deposit of ${amount} to the new account before the meeting tomorrow. The details are: {bank} Account: {account_num}. Let me know once done. {exec_name}"),
]

WHALING_TEMPLATES = [
    ("Confidential M&A opportunity - Board eyes only",
     "Dear {exec_name}, I'm reaching out regarding a confidential acquisition opportunity valued at ${amount}M. Our client is interested in {company} and has authorized me to make a preliminary offer. This is extremely time sensitive. Please respond with a secure email or call +1-{phone}. Regards, {law_firm} Partners"),
    ("SEC inquiry - Immediate response required",
     "Dear {exec_name}, This notice is to inform you that the Securities and Exchange Commission has initiated a preliminary inquiry regarding {company}'s Q{quarter} financial disclosures. Your cooperation is required. Please access the secure portal at {fake_domain}/sec-portal to submit your response within 72 hours."),
    ("Urgent: Board resolution required - {exec_title}",
     "Dear {exec_name}, The board requires an emergency resolution on the proposed acquisition of {target_company}. As {exec_title}, your digital signature is required before market close today. Please access the secure signing portal: {fake_domain}/board-resolution/{token}"),
    ("Wire transfer authorization - {exec_name}",
     "Dear {exec_name}, Per our conversation with the board, please authorize the immediate transfer of ${amount}M from the operating account to the escrow account for the {project} transaction. Use your executive credentials at {fake_domain}/exec-transfer. This is time-critical. CFO Office"),
    ("Your LinkedIn Premium - Unusual sign-in",
     "Dear {exec_name}, We detected a sign-in to your LinkedIn account from an unrecognized device in {country}. If this wasn't you, secure your account immediately: {fake_domain}/linkedin-secure. Your profile and connections may be at risk."),
    ("Executive background check - Authorization needed",
     "Dear {exec_name}, As part of our annual compliance review, we require your authorization for the executive background verification process. Please verify your identity and authorize at {fake_domain}/exec-verify using your SSN and date of birth to proceed."),
    ("Investor relations - Urgent: Share price inquiry",
     "Dear {exec_name}, I represent a group of institutional investors holding a significant position in {company}. We have serious concerns about recent corporate governance decisions. Please respond to {fake_email} to arrange a call, otherwise we will be forced to escalate to the board of directors and SEC."),
]


def _rand(items): return random.choice(items)

def _fill_phishing(template_subject, template_body):
    banks = ["Chase", "Bank of America", "Wells Fargo", "Citibank", "US Bank"]
    services = ["Netflix", "PayPal", "Amazon", "Microsoft", "Apple", "Google"]
    domains = ["secure-verify-account.com", "account-update-portal.net",
               "login-verify-now.com", "secure-access-portal.org",
               "account-suspended-verify.com", "update-billing-info.net"]
    tokens = [f"{random.randint(100000,999999)}", f"a{random.randint(10000,99999)}b"]
    amounts = [str(random.randint(200, 4500))]

    subs = {
        "{bank}": _rand(banks), "{service}": _rand(services),
        "{fake_domain}": _rand(domains), "{token}": _rand(tokens),
        "{amount}": _rand(amounts),
    }
    s = template_subject
    b = template_body
    for k, v in subs.items():
        s = s.replace(k, v)
        b = b.replace(k, v)
    return f"Subject: {s}\n\n{b}"


def _fill_spear(template_subject, template_body):
    exec_names = ["Robert Chen", "Sarah Williams", "Michael Johnson",
                  "Jennifer Lee", "David Martinez", "Lisa Thompson"]
    target_names = ["Alex", "Jordan", "Taylor", "Morgan", "Casey", "Riley"]
    vendors = ["Global Supplies Inc", "TechPartners LLC", "Continental Services"]
    banks = ["JPMorgan Chase", "Citibank", "HSBC", "Wells Fargo"]
    domains = ["invoice-secure.com", "payment-portal.net", "billing-update.org"]

    subs = {
        "{exec_name}": _rand(exec_names),
        "{target_name}": _rand(target_names),
        "{amount}": str(random.randint(5000, 85000)),
        "{count}": str(random.randint(5, 20)),
        "{card_value}": str(_rand([100, 200, 500])),
        "{inv_number}": f"INV-{random.randint(10000,99999)}",
        "{vendor}": _rand(vendors),
        "{bank}": _rand(banks),
        "{account_num}": f"{random.randint(100000000,999999999)}",
        "{routing_num}": f"{random.randint(100000000,999999999)}",
        "{fake_email}": f"hr.{random.randint(100,999)}@{_rand(domains)}",
        "{fake_domain}": _rand(domains),
    }
    s = template_subject
    b = template_body
    for k, v in subs.items():
        s = s.replace(k, v)
        b = b.replace(k, v)
    return f"Subject: {s}\n\n{b}"


def _fill_whaling(template_subject, template_body):
    exec_names = ["James Harrison", "Patricia Moore", "Richard Thompson",
                  "Elizabeth Chen", "William Foster", "Margaret Walsh"]
    exec_titles = ["CEO", "CFO", "CTO", "COO", "CISO", "President"]
    companies = ["TechCorp Industries", "GlobalTech Solutions", "Meridian Enterprises"]
    law_firms = ["Morrison & Foerster", "Skadden Arps", "Davis Polk"]
    domains = ["exec-secure-portal.com", "board-resolution.net",
               "sec-compliance-portal.org", "executive-verify.com"]
    countries = ["Russia", "China", "Nigeria", "Brazil", "Ukraine"]

    subs = {
        "{exec_name}": _rand(exec_names),
        "{exec_title}": _rand(exec_titles),
        "{company}": _rand(companies),
        "{target_company}": _rand(companies),
        "{amount}": str(random.randint(5, 500)),
        "{quarter}": str(random.randint(1, 4)),
        "{project}": _rand(["Project Falcon", "Alpha Acquisition", "Operation Horizon"]),
        "{law_firm}": _rand(law_firms),
        "{fake_domain}": _rand(domains),
        "{fake_email}": f"confidential@{_rand(domains)}",
        "{token}": f"{random.randint(100000,999999)}",
        "{phone}": f"{random.randint(200,999)}-{random.randint(100,999)}-{random.randint(1000,9999)}",
        "{country}": _rand(countries),
    }
    s = template_subject
    b = template_body
    for k, v in subs.items():
        s = s.replace(k, v)
        b = b.replace(k, v)
    return f"Subject: {s}\n\n{b}"


def generate_synthetic(target_per_class=800) -> list[dict]:
    """Genera ejemplos sintéticos para todas las clases."""
    print("\n[3/3] Generando datos sintéticos...")
    records = []
    random.seed(42)

    # Legítimos sintéticos (cortos y directos — lo que SpamAssassin no cubre)
    for _ in range(target_per_class):
        t = _rand(LEGITIMATE_TEMPLATES)
        records.append({"text": _fill_legitimate(*t), "label": 0, "label_name": "legitimate"})

    for _ in range(target_per_class):
        t = _rand(PHISHING_TEMPLATES)
        records.append({"text": _fill_phishing(*t), "label": 2, "label_name": "phishing"})

    for _ in range(target_per_class):
        t = _rand(SPEAR_TEMPLATES)
        records.append({"text": _fill_spear(*t), "label": 3, "label_name": "spear_phishing"})

    for _ in range(target_per_class):
        t = _rand(WHALING_TEMPLATES)
        records.append({"text": _fill_whaling(*t), "label": 4, "label_name": "whaling"})

    for name, count in [("legitimate (sintético)", target_per_class),
                         ("phishing", target_per_class),
                         ("spear_phishing", target_per_class),
                         ("whaling", target_per_class)]:
        print(f"  ✓ {name}: {count} ejemplos generados")

    return records


def balance_and_save(records: list[dict]):
    """Balancea las clases y guarda el CSV final."""
    random.shuffle(records)

    by_class = {i: [] for i in range(5)}
    for r in records:
        by_class[r["label"]].append(r)

    print("\n─── Distribución antes de balancear ───")
    for label_id, rows in by_class.items():
        print(f"  {LABELS[label_id]:<15}: {len(rows)}")

    # Cap: máximo 2000 por clase para no desbalancear
    cap = min(2000, min(len(v) for v in by_class.values() if v))
    balanced = []
    for label_id, rows in by_class.items():
        sample = rows[:cap] if len(rows) >= cap else rows
        balanced.extend(sample)

    random.shuffle(balanced)

    with open(OUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["text", "label", "label_name"])
        writer.writeheader()
        writer.writerows(balanced)

    print(f"\n─── Dataset guardado: {OUT_FILE} ───")
    print(f"  Total: {len(balanced)} emails")
    for label_id in range(5):
        cnt = sum(1 for r in balanced if r["label"] == label_id)
        print(f"  {LABELS[label_id]:<15}: {cnt}")


if __name__ == "__main__":
    print("=" * 50)
    print(" MailDefender — Dataset Builder")
    print("=" * 50)

    download_spamassassin()
    real_records = parse_spamassassin()
    synthetic_records = generate_synthetic(target_per_class=800)

    all_records = real_records + synthetic_records
    balance_and_save(all_records)

    print("\n✓ Listo. Sube ml/data/processed/dataset.csv a Google Colab.")
