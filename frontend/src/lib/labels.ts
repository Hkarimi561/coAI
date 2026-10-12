import type { CitationKind, ConversationStatus } from "@/lib/types";

export const STATUS_LABEL: Record<ConversationStatus, string> = {
  unresolved: "حل‌نشده",
  pending_review: "در انتظار بازبینی",
  resolved: "حل‌شده",
};

export const LESSON_LABEL = { pending: "در انتظار تأیید ادمین", approved: "تأییدشده و فعال", rejected: "ردشده" } as const;
export const LESSON_TONE = { pending: "warning", approved: "success", rejected: "danger" } as const;

export const STATUS_TONE = { unresolved: "neutral", pending_review: "warning", resolved: "success" } as const;

export const SOURCE_LABEL: Record<string, string> = {
  lessons: "آموزش تأییدشده",
  github: "مستندات GitHub",
  local_docs: "مستندات داخلی",
  solutions: "راه‌حل تأییدشده",
  web_cache: "کش وب",
  web_fresh: "وب (جستجوی جدید)",
  docker: "داکر",
  ci: "CI",
  mcp: "ابزار MCP",
  none: "بدون منبع",
};

export const SOURCE_COLOR: Record<string, string> = {
  lessons: "#db2777",
  github: "#475569",
  local_docs: "#2563eb",
  solutions: "#7c3aed",
  web_cache: "#0891b2",
  web_fresh: "#ea580c",
  docker: "#16a34a",
  ci: "#64748b",
};

export const CITATION_LABEL: Record<CitationKind, string> = {
  lesson: "آموزش تأییدشده",
  github: "مستندات GitHub",
  doc: "مستند داخلی",
  solution: "راه‌حل تأییدشده",
  web: "وب",
  docker: "داکر",
  ci: "CI",
};

export const WEB_EVENT_LABEL: Record<string, string> = {
  none: "بدون جستجوی وب",
  cache_hit: "از کش (جستجوی وب انجام نشد)",
  coalesced: "ادغام با جستجوی هم‌زمان",
  fresh: "جستجوی تازه در وب",
  failed: "جستجوی وب ناموفق",
};

export const STEP_LABEL: Record<string, string> = {
  check_answer_cache: "بررسی پاسخ‌های ذخیره‌شده…",
  gather_tools: "بررسی کانتینر / CI…",
  plan_queries: "تحلیل خطا…",
  retrieve_local: "جستجو در مستندات داخلی…",
  retrieve_cache: "بررسی راه‌حل‌های تأییدشده و کش وب…",
  web_search: "جستجو در وب…",
  generate: "نوشتن پاسخ…",
  mcp_tool: "در حال اجرای ابزار MCP…",
};
