"""T13/E01: Regex Baseline Adapter (PROJECT_SPEC.md §19 B1, §20.6, §20.7).

Implements a deterministic, fair regular expression baseline detector for structured Indian PII:
- PAN (Permanent Account Number)
- AADHAAR (12-digit national identifier, spaced or unspaced)
- PHONE (10-digit Indian mobile numbers, optional +91 prefix)
- EMAIL (RFC 5322 standard address syntax)
- UPI_ID (Unified Payments Interface VPA handles)
- BANK_ACCOUNT (Contextual 9–18 digit account numbers)
"""

from __future__ import annotations

import re

from benchmark.schema import Prediction

from .base import BaselineAdapter

# 1. PAN: 5 uppercase letters + 4 digits + 1 uppercase letter
_PAN_RE = re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b")

# 2. AADHAAR: 12 digits (4-4-4 space-delimited or 12 contiguous digits starting with 2-9)
_AADHAAR_SPACED_RE = re.compile(r"\b[2-9]\d{3}\s\d{4}\s\d{4}\b|\b\d{4}\s\d{4}\s\d{4}\b")
_AADHAAR_UNSPACED_RE = re.compile(r"\b[2-9]\d{11}\b")

# 3. UPI_ID: Standard PSP handle suffixes and 10-digit phone handles
_UPI_RE = re.compile(
    r"\b[6-9]\d{9}@mail\.test\b|\b[a-zA-Z0-9.\-_]{2,64}@(okaxis|okhdfcbank|okicici|oksbi|paytm|ybl|upi|apl|axl|ibl|ptsbi|ptaxis|pthdfc|ptyes|barodampay|mahb|axisbank|sbi|icici|hdfcbank|federal|kotak)\b",
    re.IGNORECASE,
)

# 4. EMAIL: Standard local-part@domain syntax
_EMAIL_RE = re.compile(r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b")

# 5. PHONE: Indian 10-digit mobile starting with 6-9, optional +91 prefix, optional 5+5 split
_PHONE_RE = re.compile(
    r"(?:\+91[\s-]?[6-9]\d{9}|\b[6-9]\d{9})(?![@\w])\b|\b[6-9]\d{4}\s\d{5}(?![@\w])\b"
)

# 6. BANK_ACCOUNT: 9–18 digits following banking trigger keywords
_BANK_ACCOUNT_RE = re.compile(
    r"(?i)\b(?:account|acct|a/c|khata|खाता|अकाउंट)[\s:/-]+([0-9]{9,18})\b"
)


class RegexBaselineAdapter(BaselineAdapter):
    """Deterministic Regex Baseline Detector (B1 / E01)."""

    @property
    def system_name(self) -> str:
        return "regex"

    @property
    def system_version(self) -> str:
        return "1.0.0"

    def predict(self, text: str) -> list[Prediction]:
        """Run regular expressions on raw text returning validated Prediction objects.

        Strictly enforces Python Unicode code-point offsets into the original text.
        """
        predictions: list[Prediction] = []
        occupied_spans: set[tuple[int, int]] = set()

        # 1. PAN
        for m in _PAN_RE.finditer(text):
            span = (m.start(), m.end())
            predictions.append(
                Prediction(
                    type="PAN",
                    start=m.start(),
                    end=m.end(),
                    text=m.group(),
                    confidence=1.0,
                )
            )
            occupied_spans.add(span)

        # 2. AADHAAR (Spaced 4-4-4 takes precedence over contiguous digits)
        for m in _AADHAAR_SPACED_RE.finditer(text):
            span = (m.start(), m.end())
            if span not in occupied_spans:
                predictions.append(
                    Prediction(
                        type="AADHAAR",
                        start=m.start(),
                        end=m.end(),
                        text=m.group(),
                        confidence=1.0,
                    )
                )
                occupied_spans.add(span)

        for m in _AADHAAR_UNSPACED_RE.finditer(text):
            span = (m.start(), m.end())
            if span not in occupied_spans:
                predictions.append(
                    Prediction(
                        type="AADHAAR",
                        start=m.start(),
                        end=m.end(),
                        text=m.group(),
                        confidence=1.0,
                    )
                )
                occupied_spans.add(span)

        # 3. UPI_ID (Evaluated before generic EMAIL)
        upi_spans = set()
        for m in _UPI_RE.finditer(text):
            span = (m.start(), m.end())
            predictions.append(
                Prediction(
                    type="UPI_ID",
                    start=m.start(),
                    end=m.end(),
                    text=m.group(),
                    confidence=1.0,
                )
            )
            upi_spans.add(span)
            occupied_spans.add(span)

        # 4. EMAIL (Excluding matched UPI spans)
        for m in _EMAIL_RE.finditer(text):
            span = (m.start(), m.end())
            if span not in upi_spans and span not in occupied_spans:
                predictions.append(
                    Prediction(
                        type="EMAIL",
                        start=m.start(),
                        end=m.end(),
                        text=m.group(),
                        confidence=1.0,
                    )
                )
                occupied_spans.add(span)

        # 5. PHONE
        for m in _PHONE_RE.finditer(text):
            span = (m.start(), m.end())
            if span not in occupied_spans:
                predictions.append(
                    Prediction(
                        type="PHONE",
                        start=m.start(),
                        end=m.end(),
                        text=m.group(),
                        confidence=1.0,
                    )
                )
                occupied_spans.add(span)

        # 6. BANK_ACCOUNT
        for m in _BANK_ACCOUNT_RE.finditer(text):
            start, end = m.span(1)
            span = (start, end)
            if span not in occupied_spans:
                predictions.append(
                    Prediction(
                        type="BANK_ACCOUNT",
                        start=start,
                        end=end,
                        text=m.group(1),
                        confidence=1.0,
                    )
                )
                occupied_spans.add(span)

        # Sort deterministically by start offset, end offset, type
        predictions.sort(key=lambda p: (p.start, p.end, p.type))
        return predictions
