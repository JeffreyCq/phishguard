import asyncio
import logging
import os
from email import message_from_bytes
from email.policy import default as email_policy

from aiosmtpd.controller import Controller

logger = logging.getLogger(__name__)

SMTP_LISTEN_PORT = int(os.getenv("SMTP_LISTEN_PORT", "2525"))
SMTP_LISTEN_HOST = os.getenv("SMTP_LISTEN_HOST", "0.0.0.0")

# Injected at startup from main.py
_analysis_callback = None


def set_analysis_callback(callback):
    global _analysis_callback
    _analysis_callback = callback


def _extract_original_email(raw_bytes: bytes) -> bytes:
    """
    When a user forwards a phishing email to us, try to extract the original
    inner message. Email clients forward in two ways:
      1. message/rfc822 attachment (Outlook "Forward as Attachment") — ideal
      2. Inline forward (quoted body) — fall back to analyzing the whole thing
    """
    try:
        msg = message_from_bytes(raw_bytes, policy=email_policy)
        for part in msg.walk():
            if part.get_content_type() == "message/rfc822":
                payload = part.get_payload()
                if payload and isinstance(payload, list):
                    return payload[0].as_bytes()
    except Exception:
        pass
    return raw_bytes


class PhishingAnalysisHandler:
    def __init__(self, main_loop: asyncio.AbstractEventLoop):
        self._loop = main_loop

    async def handle_DATA(self, server, session, envelope):
        sender = envelope.mail_from
        raw_bytes = envelope.content

        if not sender or not raw_bytes:
            return "500 Empty message"

        logger.info("SMTP: received email from %s (%d bytes)", sender, len(raw_bytes))

        if _analysis_callback:
            analyzable = _extract_original_email(raw_bytes)
            # Schedule the coroutine on the FastAPI event loop (this handler
            # runs inside aiosmtpd's own thread/loop)
            asyncio.run_coroutine_threadsafe(
                _analysis_callback(sender, analyzable),
                self._loop,
            )

        return "250 Message accepted for analysis — reply incoming shortly"


def start_smtp_server(main_loop: asyncio.AbstractEventLoop) -> "Controller | None":
    if not os.getenv("SMTP_HOST"):
        logger.info("SMTP_HOST not set — email forwarding feature disabled")
        return None

    handler = PhishingAnalysisHandler(main_loop)
    controller = Controller(
        handler,
        hostname=SMTP_LISTEN_HOST,
        port=SMTP_LISTEN_PORT,
    )
    controller.start()
    logger.info("SMTP server listening on %s:%d", SMTP_LISTEN_HOST, SMTP_LISTEN_PORT)
    return controller
