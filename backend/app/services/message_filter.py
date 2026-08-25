from __future__ import annotations

import re

from app.domain.models import CustomerMessage

ORDER_RE = re.compile(r"#\d{4,}")

SUPPORT_TERMS = (
    "where is my order",
    "where is order",
    "tracking",
    "delivery",
    "delayed",
    "not arrived",
    "return",
    "refund",
    "money back",
    "missing item",
    "missing",
    "wrong item",
    "wrong product",
    "wrong size",
    "cancel",
    "change address",
    "change size",
    "modify order",
    "change my order",
)

FOOTER_MARKERS = (
    "\nunsubscribe",
    "\nmanage preferences",
    "\nprivacy policy",
    "\nview in browser",
)


def clean_message_text(value: str, max_chars: int = 5000) -> str:
    text = (value or "").replace("\r\n", "\n").replace("\r", "\n")

    # Remove common quoted-reply blocks.
    text = re.split(
        r"(?im)^\s*On .+ wrote:\s*$|^\s*From:\s.+$",
        text,
        maxsplit=1,
    )[0]

    lowered = text.lower()
    cut_positions = [
        lowered.find(marker)
        for marker in FOOTER_MARKERS
        if lowered.find(marker) >= 0
    ]
    if cut_positions:
        text = text[: min(cut_positions)]

    # Marketing messages can contain huge raw tracking URLs.
    text = re.sub(r"https?://\S{120,}", "[long link]", text)

    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)
    return text.strip()[:max_chars]


def is_support_candidate(message: CustomerMessage) -> bool:
    text = f"{message.subject}\n{message.body}".lower()
    has_order = bool(ORDER_RE.search(text))
    hits = sum(term in text for term in SUPPORT_TERMS)

    # An order number + any support language is a strong signal.
    if has_order and hits >= 1:
        return True

    # Allow clear support requests even when the customer forgot the order id.
    return hits >= 2
