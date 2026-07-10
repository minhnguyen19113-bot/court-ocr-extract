from __future__ import annotations

import hashlib
import re
from typing import Any


EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
VN_PHONE_RE = re.compile(r"(?<!\d)(?:\+?84|0)(?:[ .-]?\d){8,10}(?!\d)")
IDENTITY_NUMBER_RE = re.compile(r"(?<!\d)\d{9,12}(?!\d)")

HASH_KEYS = {"case_id_hash", "file_hash", "name_hash"}
HEX_SHA256_RE = re.compile(r"^[A-F0-9]{64}$", re.IGNORECASE)
SAFE_HASH_TOKEN_RE = re.compile(r"^[A-Z][A-Z0-9:_-]{5,}$", re.IGNORECASE)


def hash_value(value: str, salt: str | None = None) -> str:
    material = f"{salt or ''}\0{value}".encode("utf-8")
    return "sha256:" + hashlib.sha256(material).hexdigest()


def looks_like_pii(text: str) -> bool:
    return any(pattern.search(text or "") for pattern in (EMAIL_RE, VN_PHONE_RE, IDENTITY_NUMBER_RE))


def redact_common_pii(text: str) -> str:
    redacted = EMAIL_RE.sub("<redacted_email>", text or "")
    redacted = VN_PHONE_RE.sub("<redacted_phone>", redacted)
    return IDENTITY_NUMBER_RE.sub("<redacted_id>", redacted)


def find_pii_paths(value: Any, path: str = "$", *, parent_key: str | None = None) -> list[str]:
    if parent_key in HASH_KEYS and _looks_like_hash_token(value):
        return []
    if isinstance(value, str):
        return [path] if looks_like_pii(value) else []
    if isinstance(value, int) and not isinstance(value, bool):
        return [path] if 9 <= len(str(abs(value))) <= 12 else []
    if isinstance(value, dict):
        findings: list[str] = []
        for key, item in value.items():
            findings.extend(
                find_pii_paths(item, f"{path}.{key}", parent_key=str(key))
            )
        return findings
    if isinstance(value, list):
        findings = []
        for index, item in enumerate(value):
            findings.extend(find_pii_paths(item, f"{path}[{index}]"))
        return findings
    return []


def _looks_like_hash_token(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    lowered = value.lower()
    if lowered.startswith("sha256:") or HEX_SHA256_RE.fullmatch(value):
        return True
    return "hash" in lowered and bool(SAFE_HASH_TOKEN_RE.fullmatch(value))
