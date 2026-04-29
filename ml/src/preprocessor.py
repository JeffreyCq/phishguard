"""
preprocessor.py — Normaliza emails reemplazando nombres de ejecutivos por tokens.

El modelo fue entrenado con estos tokens, así que reconoce los patrones
independientemente de qué empresa o ejecutivos configure el usuario.
"""

import re
import yaml
from dataclasses import dataclass, field
from pathlib import Path

TITLE_TOKEN_MAP = {
    "CEO":       "[EXEC_CEO]",
    "CFO":       "[EXEC_CFO]",
    "CTO":       "[EXEC_CTO]",
    "COO":       "[EXEC_COO]",
    "CISO":      "[EXEC_CISO]",
    "President": "[EXEC_PRESIDENT]",
    "Chairman":  "[EXEC_CHAIRMAN]",
    "Board":     "[EXEC_BOARD]",
    "VP":        "[EXEC_VP]",
    "Director":  "[EXEC_DIRECTOR]",
}

C_SUITE = {"CEO", "CFO", "CTO", "COO", "CISO", "President", "Chairman", "Board"}
SENIOR  = {"VP", "Director"}


@dataclass
class NormResult:
    text: str
    executives_found: list[str] = field(default_factory=list)
    risk_multiplier: float = 1.0


class EmailPreprocessor:
    def __init__(self, config_path: str | Path = None):
        self.config = self._load(config_path)
        self._patterns = self._build_patterns()
        self._domain_pattern = self._build_domain_pattern()

    def _load(self, path) -> dict:
        if path is None:
            return {}
        p = Path(path)
        if not p.exists():
            return {}
        with open(p, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    def _build_patterns(self) -> list[tuple[re.Pattern, str, str]]:
        patterns = []
        for exec_cfg in self.config.get("executives", []):
            title = exec_cfg.get("title", "")
            token = TITLE_TOKEN_MAP.get(title, "[EXEC_STAFF]")

            names = [exec_cfg["name"]] + exec_cfg.get("aliases", [])
            if "email" in exec_cfg:
                names.append(exec_cfg["email"])

            for name in names:
                pat = re.compile(re.escape(name.strip()), re.IGNORECASE)
                patterns.append((pat, token, title))

        return patterns

    def _build_domain_pattern(self) -> re.Pattern | None:
        domain = self.config.get("company", {}).get("domain", "")
        if not domain:
            return None
        return re.compile(re.escape(domain.strip()), re.IGNORECASE)

    def normalize(self, subject: str, sender: str, body: str) -> NormResult:
        text = f"Subject: {subject}\nFrom: {sender}\n\n{body}"
        found_titles = []

        for pattern, token, title in self._patterns:
            if pattern.search(text):
                found_titles.append(title)
                text = pattern.sub(token, text)

        if self._domain_pattern:
            text = self._domain_pattern.sub("[COMPANY_DOMAIN]", text)

        text = re.sub(r"\s+", " ", text).strip()[:512]

        multiplier = self._multiplier(found_titles)
        return NormResult(
            text=text,
            executives_found=list(set(found_titles)),
            risk_multiplier=multiplier,
        )

    def _multiplier(self, titles: list[str]) -> float:
        if not titles:
            return 1.0
        if any(t in C_SUITE for t in titles):
            return 3.0
        if any(t in SENIOR for t in titles):
            return 2.0
        return 1.5
