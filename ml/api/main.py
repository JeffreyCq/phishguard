"""
MailDefender ML Classifier — REST microservice.

POST /classify   — classify a single email
GET  /health     — service status
"""

import os
import sys
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Make src/ importable regardless of working directory
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from src.preprocessor import EmailPreprocessor, NormResult
from src.classifier import ThreatClassifier
from src.scorer import compute_score

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── Startup: load model once ──────────────────────────────────────────────────

_classifier: ThreatClassifier | None = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global _classifier
    logger.info("Loading ONNX model...")
    _classifier = ThreatClassifier()
    _classifier._load()          # eager load — fail fast if model missing
    logger.info("Model ready.")
    yield
    logger.info("Shutting down.")


# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="MailDefender ML Classifier",
    version="1.0.0",
    description="DistilBERT-based email threat classifier. Detects spam, phishing, spear phishing, and whaling.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Schemas ───────────────────────────────────────────────────────────────────

class Executive(BaseModel):
    name: str
    title: str
    aliases: list[str] = []
    email: Optional[str] = None


class ClassifyRequest(BaseModel):
    subject: str = ""
    sender:  str = ""
    body:    str = ""
    executives: list[Executive] = []   # optional — boosts whaling/spear detection


class ClassifyResponse(BaseModel):
    threat_type:         str
    threat_level:        int            # 0=legit 1=spam 2=phishing 3=spear 4=whaling
    confidence:          float
    executives_detected: list[str]
    score_boosted:       bool
    scores: dict[str, float]


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/health", tags=["Status"])
async def health():
    model_ready = _classifier is not None and _classifier._loaded
    return {
        "status": "ok" if model_ready else "loading",
        "model":  "distilbert-maildefender-v1",
        "classes": ["legitimate", "spam", "phishing", "spear_phishing", "whaling"],
    }


@app.post("/reload", tags=["Admin"])
async def reload_model():
    """Reload the ONNX model from disk — call after deploying a retrained model."""
    global _classifier
    _classifier = ThreatClassifier()
    _classifier._load()
    return {"status": "ok", "message": "Model reloaded from disk"}


@app.post("/classify", response_model=ClassifyResponse, tags=["Classifier"])
async def classify(req: ClassifyRequest):
    # Build a temporary preprocessor from the request's executive list
    # (stateless — no server-side config needed)
    config = _build_config(req.executives)
    preprocessor = EmailPreprocessor.__new__(EmailPreprocessor)
    preprocessor.config = config
    preprocessor._patterns = preprocessor._build_patterns()
    preprocessor._domain_pattern = None

    norm  = preprocessor.normalize(req.subject, req.sender, req.body)
    probs = _classifier.predict_proba(norm.text)
    result = compute_score(probs, norm)

    return ClassifyResponse(**result)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _build_config(executives: list[Executive]) -> dict:
    return {
        "company": {},
        "executives": [
            {
                "name":    e.name,
                "title":   e.title,
                "aliases": e.aliases,
                **( {"email": e.email} if e.email else {} ),
            }
            for e in executives
        ],
    }
