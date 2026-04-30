import uuid
from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from database import Base


def _new_uuid() -> str:
    return str(uuid.uuid4())


class ApiKey(Base):
    __tablename__ = "api_keys"

    id           = Column(Integer, primary_key=True, autoincrement=True)
    prefix       = Column(String(8),  unique=True, nullable=False, index=True)
    key_hash     = Column(String(64), unique=True, nullable=False)
    label        = Column(String(128), nullable=False, default="")
    is_active    = Column(Boolean, nullable=False, default=True)
    rate_limit   = Column(Integer, nullable=False, default=1000)
    created_at   = Column(DateTime, default=datetime.utcnow)
    last_used_at = Column(DateTime, nullable=True)


class Scan(Base):
    __tablename__ = "scans"

    id            = Column(Integer, primary_key=True, autoincrement=True)
    scan_id       = Column(String(36), unique=True, nullable=False, default=_new_uuid)
    email_hash    = Column(String(64), nullable=False, index=True)
    subject       = Column(String(512))
    sender        = Column(String(256))
    body_text     = Column(Text)
    verdict       = Column(String(32))
    spam_verdict  = Column(String(32))
    confidence    = Column(Integer)
    threat_type   = Column(String(32))
    risk_score    = Column(Integer)
    risk_level    = Column(String(16))
    model_version = Column(String(64))
    source        = Column(String(16), default='unknown')
    created_at    = Column(DateTime, default=datetime.utcnow)


class Feedback(Base):
    __tablename__ = "feedback"

    id         = Column(Integer, primary_key=True, autoincrement=True)
    scan_id    = Column(String(36), ForeignKey("scans.scan_id"), nullable=False, index=True)
    is_correct = Column(Boolean, nullable=False)
    true_label = Column(String(32))   # legitimate/spam/phishing/spear_phishing/whaling
    notes      = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
