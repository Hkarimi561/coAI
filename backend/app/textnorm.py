"""Error-signature normalisation: turns noisy logs / questions into a stable, hashable signature."""

import hashlib
import re
import unicodedata
from dataclasses import dataclass

_ERROR_RE = re.compile(
    r"(?i)(?:\b(?:error|err|fail(?:ed|ure|s)?|exception|fatal|panic|denied|refused|cannot|can't|unable|not found|"
    r"timeout|timed out|traceback|segfault|oom|killed|unhealthy|crash(?:ed|loop)?|errno|exit(?:ed)? (?:with )?(?:code|status)|"
    r"no such|permission|unreachable|bad gateway|502|503|504)\b)|خطا|ناموفق|شکست|مشکل در|دسترسی"
)
_ISO_TS = re.compile(r"\d{4}-\d{2}-\d{2}[t ]\d{2}:\d{2}:\d{2}(?:[.,]\d+)?(?:z|[+-]\d{2}:?\d{2})?")
_TIME = re.compile(r"\b\d{2}:\d{2}:\d{2}(?:[.,]\d+)?\b")
_UUID = re.compile(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b")
_IP = re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}(?::\d+)?\b")
_HEX = re.compile(r"\b(?:0x)?[0-9a-f]{8,}\b")
_BIGNUM = re.compile(r"\b\d{4,}\b")
_WS = re.compile(r"\s+")
_PLACEHOLDER = re.compile(r"<[a-z]+>")


def normalize_text(s: str) -> str:
    s = unicodedata.normalize("NFKC", s)
    s = s.replace("ي", "ی").replace("ك", "ک").replace("‌", " ")
    return s


def normalize_line(line: str) -> str:
    s = normalize_text(line).lower()
    s = _ISO_TS.sub("<ts>", s)
    s = _TIME.sub("<ts>", s)
    s = _UUID.sub("<id>", s)
    s = _IP.sub("<ip>", s)
    s = _HEX.sub("<hex>", s)
    s = _BIGNUM.sub("<n>", s)  # keep short numbers: HTTP codes, exit codes
    return _WS.sub(" ", s).strip()


@dataclass(frozen=True)
class Signature:
    text: str
    key: str
    is_error: bool


def build_signature(text: str) -> Signature:
    lines = [ln for ln in text.splitlines() if ln.strip()]
    error_lines: list[str] = []
    seen: set[str] = set()
    for ln in lines:
        if _ERROR_RE.search(ln):
            norm = normalize_line(ln)[:200]
            if norm and norm not in seen:
                seen.add(norm)
                error_lines.append(norm)
    if len(error_lines) > 5:
        error_lines = error_lines[:3] + error_lines[-2:]

    if error_lines:
        sig = " | ".join(error_lines)
        is_error = True
    else:
        sig = _WS.sub(" ", re.sub(r"[^\w\s<>]", " ", normalize_line(" ".join(lines)))).strip()[:300]
        is_error = False
    key = hashlib.sha256(sig.encode("utf-8")).hexdigest()[:32]
    return Signature(text=sig, key=key, is_error=is_error)


def web_query_from(signature: Signature, message: str) -> str:
    """Query text sent to the web search engine. Built from already-redacted data only."""
    if signature.is_error:
        q = _PLACEHOLDER.sub("", signature.text.replace("|", " "))
    else:
        q = message
    return _WS.sub(" ", q).strip()[:250]


def error_lines_of(text: str, limit: int = 15) -> list[str]:
    out = [ln.strip()[:300] for ln in text.splitlines() if ln.strip() and _ERROR_RE.search(ln)]
    return out[-limit:]


def truncate_middle(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    half = max_chars // 2
    return text[:half] + "\n…[truncated]…\n" + text[-half:]
