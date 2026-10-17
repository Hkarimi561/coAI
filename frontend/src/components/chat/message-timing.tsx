"use client";

import { Clock } from "lucide-react";

import { tNow, useT } from "@/lib/i18n";
import type { MessageMeta } from "@/lib/types";
import { formatNumber } from "@/lib/utils";

export function formatMs(ms: number): string {
  if (ms < 1000) return `${formatNumber(Math.round(ms))} ${tNow("میلی‌ثانیه")}`;
  const s = ms / 1000;
  if (s < 60) return `${formatNumber(Math.round(s * 10) / 10)} ${tNow("ثانیه")}`;
  return tNow("{m} دقیقه و {s} ثانیه").replace("{m}", formatNumber(Math.floor(s / 60))).replace("{s}", formatNumber(Math.round(s % 60)));
}

function Row({ label, value, sub = false, strong = false }: { label: string; value: string; sub?: boolean; strong?: boolean }) {
  return (
    <div className={`flex items-baseline justify-between gap-4 ${sub ? "ps-3 text-[11px] text-muted-foreground" : ""} ${strong ? "border-t border-border pt-1.5 font-semibold" : ""}`}>
      <span>{label}</span>
      <span className="tabular-nums">{value}</span>
    </div>
  );
}

/** Clock icon under an answer; hover / focus / tap shows where the time went. */
export function MessageTiming({ meta }: { meta: MessageMeta }) {
  const t = useT();
  const tm = meta.timings;
  if (!tm) return null;
  const u = meta.usage;
  const genSec = (tm.thinking_ms + tm.response_ms) / 1000;
  const speed = u && u.completion_tokens && genSec > 0.2 ? u.completion_tokens / genSec : 0;
  const searchParts: [string, number][] = [
    [t("ابزارها (Docker / CI)"), tm.tools_ms ?? 0],
    [t("مستندات داخلی"), tm.docs_ms ?? 0],
    [t("کش و راه‌حل‌های تأییدشده"), tm.cache_ms ?? 0],
    [t("جستجوی وب"), tm.web_ms ?? 0],
  ];
  return (
    <span className="group/timing relative inline-flex">
      <button
        type="button"
        aria-label={t("زمان‌بندی پاسخ")}
        className="inline-flex h-6 w-6 items-center justify-center rounded-md text-muted-foreground hover:bg-muted hover:text-foreground focus-visible:bg-muted focus-visible:outline-none"
      >
        <Clock className="h-3.5 w-3.5" />
      </button>
      <div
        role="tooltip"
        className="pointer-events-none invisible absolute bottom-full start-0 z-30 mb-1.5 w-72 max-w-[85vw] space-y-1.5 rounded-lg border border-border bg-card p-3 text-xs opacity-0 shadow-lg transition-opacity group-hover/timing:visible group-hover/timing:opacity-100 group-focus-within/timing:visible group-focus-within/timing:opacity-100"
      >
        <div className="mb-1 font-semibold">{t("زمان‌بندی این پاسخ")}</div>
        {meta.answer_cache === "hit" ? <div className="text-muted-foreground">{t("پاسخ از حافظه‌ی گفتگوها خوانده شد؛ مدل اجرا نشد.")}</div> : null}
        <Row label={t("زمان جستجو")} value={formatMs(tm.search_ms)} />
        {searchParts
          .filter(([, v]) => v >= 50)
          .map(([label, v]) => (
            <Row key={label} sub label={label} value={formatMs(v)} />
          ))}
        <Row label={t("آماده‌سازی مدل (تا اولین توکن)")} value={formatMs(tm.prefill_ms ?? 0)} />
        <Row label={t("زمان تفکر")} value={tm.thinking_ms ? formatMs(tm.thinking_ms) : "—"} />
        <Row label={t("زمان نوشتن پاسخ")} value={formatMs(tm.response_ms ?? 0)} />
        {speed ? <Row label={t("سرعت تولید")} value={`${formatNumber(Math.round(speed * 10) / 10)} ${t("توکن/ثانیه")}`} /> : null}
        {u ? <Row label={t("توکن (ورودی / خروجی)")} value={`${formatNumber(u.prompt_tokens)} / ${formatNumber(u.completion_tokens)}${u.estimated ? " ≈" : ""}`} /> : null}
        <Row strong label={t("مجموع")} value={formatMs(tm.total_ms)} />
      </div>
    </span>
  );
}
