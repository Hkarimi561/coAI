"""Flags risky shell / SQL / orchestration commands found in code blocks of an answer, so the UI can warn before anyone runs them.

Only fenced code blocks are scanned (prose such as "never run `rm -rf /`" must not trigger a warning).
"""

import re
from typing import Any

# (pattern, severity, reason in Persian)
_RULES: list[tuple[str, str, str]] = [
    (r"\brm\s+(-[a-z]*[rf][a-z]*\b|--recursive|--force)", "high", "حذف بازگشتی/اجباری فایل‌ها؛ قابل بازگشت نیست"),
    (r"\bdocker\s+system\s+prune", "high", "پاک‌سازی همه‌ی ایمیج‌ها، کانتینرها و شبکه‌های بلااستفاده"),
    (r"\bdocker\s+volume\s+(rm|prune)", "high", "حذف volume و داده‌های ماندگار"),
    (r"\bdocker(\s+compose)?\s+down\b.*(\s-v\b|--volumes)", "high", "down همراه با حذف volumeها؛ داده‌ها از بین می‌رود"),
    (r"\bdocker\s+(container\s+)?rm\b.*(\s-f\b|--force)", "high", "حذف اجباری کانتینر"),
    (r"\bdocker\s+(image\s+)?rmi\b", "medium", "حذف ایمیج"),
    (r"\bdocker(\s+compose)?\s+(stop|kill|restart|down)\b", "medium", "توقف/ری‌استارت سرویس؛ موقتاً قطع می‌شود"),
    (r"\bkubectl\s+(delete|drain|cordon|replace\s+--force)\b", "high", "حذف یا تخلیه‌ی منابع Kubernetes"),
    (r"\bkubectl\s+(scale|rollout\s+restart|apply|patch|edit|set)\b", "medium", "تغییر وضعیت منابع Kubernetes"),
    (r"\bhelm\s+(uninstall|delete|rollback)\b", "high", "حذف یا بازگشت release در Helm"),
    (r"\bterraform\s+(destroy|apply)\b", "high", "تغییر یا نابودی زیرساخت"),
    (r"\bDROP\s+(TABLE|DATABASE|SCHEMA)\b|\bTRUNCATE\b", "high", "حذف جدول/دیتابیس یا خالی کردن آن"),
    (r"\bDELETE\s+FROM\b(?!.*\bWHERE\b)|\bUPDATE\s+\S+\s+SET\b(?!.*\bWHERE\b)", "high", "دستور SQL بدون WHERE روی همه‌ی ردیف‌ها اثر می‌گذارد"),
    (r"\b(FLUSHALL|FLUSHDB)\b", "high", "پاک کردن کل داده‌های Redis"),
    (r"\bmkfs(\.\w+)?\b|\bdd\b.*\bof=/dev/", "high", "فرمت یا بازنویسی دیسک"),
    (r"\bchmod\s+(-R|--recursive)\b.*\b777\b", "high", "دسترسی کامل برای همه به‌صورت بازگشتی؛ خطر امنیتی"),
    (r"\bchown\s+(-R|--recursive)\b", "medium", "تغییر مالکیت بازگشتی فایل‌ها"),
    (r"\bgit\s+push\b.*(\s--force\b|\s-f\b)|\bgit\s+reset\s+--hard\b|\bgit\s+clean\s+-[a-z]*f", "high", "بازنویسی/حذف تاریخچه یا تغییرات محلی در Git"),
    (r"\bsystemctl\s+(stop|disable|mask|restart)\b", "medium", "توقف یا ری‌استارت سرویس سیستم"),
    (r"\b(shutdown|reboot|halt|poweroff)\b", "high", "خاموش یا ری‌بوت کردن سرور"),
    (r"\biptables\s+(-F|--flush)\b|\bufw\s+(disable|reset)\b", "high", "پاک کردن یا غیرفعال کردن فایروال"),
    (r"\b(curl|wget)\b[^|\n]*\|\s*(sudo\s+)?(ba|z)?sh\b", "high", "اجرای مستقیم اسکریپت دانلودشده بدون بررسی"),
    (r"\bkill\s+-9\b|\bpkill\b|\bkillall\b", "medium", "کشتن اجباری پردازش‌ها"),
    (r":\(\)\s*\{", "high", "الگوی fork bomb"),
    (r"\bsed\s+-i\b|(^|\s)tee\s+/etc/|>\s*/etc/", "medium", "ویرایش مستقیم فایل پیکربندی؛ ابتدا بکاپ بگیرید"),
]
_COMPILED = [(re.compile(p, re.I), sev, why) for p, sev, why in _RULES]
_FENCE = re.compile(r"```[^\n]*\n(.*?)```", re.S)
MAX_FINDINGS = 8


def scan(answer: str) -> list[dict[str, Any]]:
    """Returns [{command, reason, severity}] for risky lines in the answer's fenced code blocks (high severity first)."""
    found: dict[str, dict[str, Any]] = {}
    for block in _FENCE.findall(answer or ""):
        for raw in block.splitlines():
            line = raw.strip()
            if not line or line.startswith(("#", "//", "--")):
                continue
            for rx, sev, why in _COMPILED:
                if rx.search(line):
                    cur = found.get(line)
                    if cur is None or (sev == "high" and cur["severity"] != "high"):
                        found[line] = {"command": line[:300], "reason": why, "severity": sev}
                    break  # first (most specific) rule wins for a line
    out = sorted(found.values(), key=lambda f: 0 if f["severity"] == "high" else 1)
    return out[:MAX_FINDINGS]
