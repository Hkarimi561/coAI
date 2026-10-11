"""Secret redaction. Applied to user input, container logs, CI output and web queries
before anything is persisted, sent to the LLM, or sent to an external search engine."""

import re
from typing import Any

_SENSITIVE_KEY = r"(?:password|passwd|pwd|passphrase|secret|token|api[_\-]?key|apikey|access[_\-]?key|private[_\-]?key|client[_\-]?secret|credentials?|auth)"

_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?(?:-----END [A-Z ]*PRIVATE KEY-----|$)", re.S), "[REDACTED_PRIVATE_KEY]"),
    (re.compile(r"(?i)(\bauthorization\s*[:=]\s*)(?:bearer|basic|token)\s+[^\s\"']{6,}"), r"\1[REDACTED]"),
    (re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/=\-]{12,}"), "Bearer [REDACTED]"),
    (re.compile(r"\beyJ[A-Za-z0-9_\-]{8,}\.[A-Za-z0-9_\-]{8,}\.[A-Za-z0-9_\-]{8,}\b"), "[REDACTED_JWT]"),
    (re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b"), "[REDACTED_AWS_KEY]"),
    (re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"), "[REDACTED_GITHUB_TOKEN]"),
    (re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b"), "[REDACTED_GITHUB_TOKEN]"),
    (re.compile(r"\bglpat-[A-Za-z0-9_\-]{16,}\b"), "[REDACTED_GITLAB_TOKEN]"),
    (re.compile(r"\bxox[abprs]-[A-Za-z0-9\-]{10,}\b"), "[REDACTED_SLACK_TOKEN]"),
    (re.compile(r"\bsk-[A-Za-z0-9_\-]{16,}\b"), "[REDACTED_API_KEY]"),
    (re.compile(r"\btvly-[A-Za-z0-9_\-]{10,}\b"), "[REDACTED_API_KEY]"),
    # scheme://user:password@host
    (re.compile(r"(\b[a-zA-Z][a-zA-Z0-9+.\-]*://)([^/\s:@]+):([^/\s@]+)@"), r"\1\2:[REDACTED]@"),
    # "password": "value"  (JSON)
    (re.compile(r'(?i)("[\w.\-]*' + _SENSITIVE_KEY + r'[\w.\-]*"\s*:\s*)"[^"]*"'), r'\1"[REDACTED]"'),
    # PASSWORD=value, --token value, api_key: value
    (re.compile(r"(?i)(\b[\w.\-]*" + _SENSITIVE_KEY + r"[\w.\-]*\s*[:=]\s*)(?:\"[^\"]*\"|'[^']*'|[^\s,;\"']+)"), r"\1[REDACTED]"),
    (re.compile(r"(?i)(--(?:password|passwd|token|secret|api-key)\s+)\S+"), r"\1[REDACTED]"),
    # docker login -u user -p secret
    (re.compile(r"(?i)(\b(?:docker|podman) login\b[^\n]*?\s-p\s+)\S+"), r"\1[REDACTED]"),
]


def redact(text: str | None) -> str:
    if not text:
        return ""
    out = text
    for pattern, replacement in _PATTERNS:
        out = pattern.sub(replacement, out)
    return out


def redact_obj(value: Any) -> Any:
    """Recursively redact all strings inside JSON-like structures."""
    if isinstance(value, str):
        return redact(value)
    if isinstance(value, list):
        return [redact_obj(v) for v in value]
    if isinstance(value, dict):
        return {k: redact_obj(v) for k, v in value.items()}
    return value
