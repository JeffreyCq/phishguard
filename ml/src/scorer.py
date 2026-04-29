"""
scorer.py — Combina probabilidades del modelo con el boost de ejecutivos.
"""

import numpy as np
from .preprocessor import NormResult

LABELS = ["legitimate", "spam", "phishing", "spear_phishing", "whaling"]
IDX = {name: i for i, name in enumerate(LABELS)}

THREAT_LEVEL = {
    "legitimate":    0,
    "spam":          1,
    "phishing":      2,
    "spear_phishing": 3,
    "whaling":       4,
}


def compute_score(raw_probs: np.ndarray, norm: NormResult) -> dict:
    probs = raw_probs.copy()

    if norm.executives_found and norm.risk_multiplier > 1.0:
        probs[IDX["whaling"]]       *= norm.risk_multiplier
        probs[IDX["spear_phishing"]] *= norm.risk_multiplier * 0.7
        probs[IDX["legitimate"]]    *= 0.3
        probs = probs / probs.sum()

    top_idx = int(np.argmax(probs))
    threat  = LABELS[top_idx]

    return {
        "threat_type":          threat,
        "threat_level":         THREAT_LEVEL[threat],
        "confidence":           round(float(probs[top_idx]), 4),
        "executives_detected":  norm.executives_found,
        "score_boosted":        norm.risk_multiplier > 1.0,
        "scores": {
            label: round(float(p), 4)
            for label, p in zip(LABELS, probs)
        },
    }
