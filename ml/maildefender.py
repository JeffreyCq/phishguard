#!/usr/bin/env python3
"""
MailDefender — Email threat classifier CLI.

Usage:
    python maildefender.py --subject "..." --sender "..." --body "..."
    python maildefender.py --setup
    python maildefender.py --demo
"""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).parent
CONFIG_PATH = ROOT / "config" / "company.yml"


def run_analysis(subject: str, sender: str, body: str, config: Path):
    from src.preprocessor import EmailPreprocessor
    from src.classifier import ThreatClassifier
    from src.scorer import compute_score

    preprocessor = EmailPreprocessor(config)
    classifier   = ThreatClassifier()

    norm   = preprocessor.normalize(subject, sender, body)
    probs  = classifier.predict_proba(norm.text)
    result = compute_score(probs, norm)

    _print_result(result)
    return result


def _print_result(result: dict):
    COLORS = {
        "legitimate":     "\033[92m",
        "spam":           "\033[93m",
        "phishing":       "\033[91m",
        "spear_phishing": "\033[91m",
        "whaling":        "\033[95m",
    }
    RESET = "\033[0m"
    BOLD  = "\033[1m"

    threat = result["threat_type"]
    color  = COLORS.get(threat, "")

    print(f"\n{'═'*48}")
    print(f"  {BOLD}THREAT DETECTED:{RESET} {color}{BOLD}{threat.upper()}{RESET}")
    print(f"  Confidence: {result['confidence']*100:.1f}%")

    if result["executives_detected"]:
        print(f"\n  ⚠  Executives mentioned: {', '.join(result['executives_detected'])}")
        if result["score_boosted"]:
            print(f"  ⚠  Score adjusted for executive context")

    print(f"\n{'─'*48}")
    for label, score in result["scores"].items():
        bar_len = int(score * 28)
        bar = "█" * bar_len + "░" * (28 - bar_len)
        c = COLORS.get(label, "")
        print(f"  {label:<16} {c}{bar}{RESET}  {score*100:5.1f}%")
    print(f"{'═'*48}\n")


def run_setup():
    """Interactive wizard to configure company.yml."""
    print("\n── MailDefender Setup ──────────────────────────")
    print("Configure your company to better detect Whaling and Spear Phishing.")
    print("Press Enter to skip any field.\n")

    import yaml

    company_name   = input("Company name: ").strip()
    company_domain = input("Corporate domain (e.g. acme.com): ").strip()

    executives = []
    print("\nAdd C-Level executives (press Enter on 'Full name' to finish):\n")

    titles = ["CEO", "CFO", "CTO", "COO", "CISO", "President", "Chairman", "VP", "Director"]

    while True:
        name = input("  Full name: ").strip()
        if not name:
            break

        print(f"  Title ({', '.join(titles)}): ", end="")
        title = input().strip()

        aliases_raw = input("  Aliases (comma-separated, optional): ").strip()
        aliases = [a.strip() for a in aliases_raw.split(",") if a.strip()] if aliases_raw else []

        email_addr = input("  Corporate email (optional): ").strip()

        exec_entry = {"name": name, "title": title}
        if aliases:
            exec_entry["aliases"] = aliases
        if email_addr:
            exec_entry["email"] = email_addr

        executives.append(exec_entry)
        print(f"  Added: {name} ({title})\n")

    config = {
        "company": {"name": company_name, "domain": company_domain},
        "executives": executives,
    }

    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        yaml.dump(config, f, allow_unicode=True, default_flow_style=False)

    print(f"\nConfiguration saved to: {CONFIG_PATH}")
    print(f"  {len(executives)} executive(s) configured")


def run_demo():
    """Quick test with sample emails."""
    samples = [
        {
            "label": "Legitimate",
            "subject": "Meeting tomorrow at 3pm",
            "sender": "colleague@company.com",
            "body": "Hi, just a reminder about our weekly sync tomorrow at 3pm. Please bring the Q3 report. Thanks!"
        },
        {
            "label": "Phishing",
            "subject": "Urgent: Your PayPal account has been limited",
            "sender": "security@paypa1-alert.com",
            "body": "Dear Customer, We've detected suspicious activity on your PayPal account. Click here to verify your identity immediately: http://paypa1-secure-login.com/verify or your account will be permanently suspended within 24 hours."
        },
        {
            "label": "Spear Phishing",
            "subject": "Quick request",
            "sender": "ceo.office@acme-corp.net",
            "body": "Hi Alex, I need you to process an urgent wire transfer of $47,000 to our new vendor. I'm in a meeting and can't take calls. Please confirm you can handle this right now. Best, Robert Chen"
        },
        {
            "label": "Whaling",
            "subject": "Confidential M&A opportunity",
            "sender": "partner@morrisonfoerster-legal.com",
            "body": "Dear CEO, I'm reaching out regarding a confidential acquisition opportunity valued at $120M. Our client has authorized a preliminary offer for your company. This is extremely time sensitive. Please respond via our secure portal: exec-secure-portal.com/confidential"
        },
    ]

    print("\n" + "═"*48)
    print("  MAILDEFENDER — DEMO")
    print("═"*48)

    for s in samples:
        print(f"\n[Actual label: {s['label']}]")
        print(f"  Subject: {s['subject']}")
        print(f"  From:    {s['sender']}")
        run_analysis(s["subject"], s["sender"], s["body"], CONFIG_PATH)


def main():
    parser = argparse.ArgumentParser(
        description="MailDefender — Email threat classifier",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--subject", default="", help="Email subject")
    parser.add_argument("--sender",  default="", help="Email sender")
    parser.add_argument("--body",    default="", help="Email body")
    parser.add_argument("--config",  default=str(CONFIG_PATH), help="Path to company.yml")
    parser.add_argument("--setup",   action="store_true", help="Run company setup wizard")
    parser.add_argument("--demo",    action="store_true", help="Run with sample emails")

    args = parser.parse_args()

    if args.setup:
        run_setup()
    elif args.demo:
        run_demo()
    elif args.subject or args.body:
        run_analysis(args.subject, args.sender, args.body, Path(args.config))
    else:
        parser.print_help()
        sys.exit(0)


if __name__ == "__main__":
    main()
