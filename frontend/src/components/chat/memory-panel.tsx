"use client";

import { Lightbulb } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Spinner } from "@/components/ui/misc";
import { useT } from "@/lib/i18n";
import { SOURCE_LABEL } from "@/lib/labels";
import type { Memory } from "@/lib/types";
import { formatNumber } from "@/lib/utils";

const OUTCOME = {
  pending: { label: "منتظر نتیجه", tone: "warning" },
  confirmed: { label: "حل شد", tone: "success" },
  rejected: { label: "جواب نداد", tone: "danger" },
  info: { label: "نیاز به اطلاعات بیشتر", tone: "neutral" },
} as const;

/** What happened in this chat session so far and what to do now. */
export function MemoryPanel({ memory }: { memory: Memory }) {
  const t = useT();
  if (!memory.timeline?.length) return null;
  return (
    <details className="rounded-lg border border-border bg-card text-sm shadow-sm">
      <summary className="flex cursor-pointer select-none items-start gap-2 px-4 py-3">
        <Lightbulb className="mt-0.5 h-4 w-4 shrink-0 text-warning" />
        <span className="min-w-0 flex-1">
          <span className="font-medium">{t("قدم بعدی")}: </span>
          <span dir="auto">{memory.next_step}</span>
        </span>
        {memory.updating ? <Spinner className="mt-0.5 h-3.5 w-3.5" /> : null}
      </summary>
      <div className="space-y-3 border-t border-border px-4 py-3">
        <div>
          <h4 className="text-xs font-semibold text-muted-foreground">{t("مسئله‌ی فعلی")}</h4>
          <p dir="auto">{memory.problem}</p>
        </div>
        {memory.summary ? (
          <div>
            <h4 className="text-xs font-semibold text-muted-foreground">{t("خلاصه‌ی تا اینجا")}</h4>
            <p dir="auto">{memory.summary}</p>
          </div>
        ) : null}
        <div>
          <h4 className="mb-1 text-xs font-semibold text-muted-foreground">{t("روند گفتگو")}</h4>
          <ol className="space-y-2">
            {memory.timeline.map((entry) => {
              const o = OUTCOME[entry.outcome];
              return (
                <li key={entry.n} className="rounded-md bg-muted/60 p-2">
                  <div className="mb-1 flex flex-wrap items-center gap-1.5">
                    <span className="font-semibold">{formatNumber(entry.n)}.</span>
                    <Badge tone={o.tone}>{t(o.label)}</Badge>
                    <Badge>{t(entry.source === "answer_cache" ? "حافظه‌ی پاسخ" : (SOURCE_LABEL[entry.source] ?? entry.source))}</Badge>
                  </div>
                  <p className="text-muted-foreground" dir="auto">
                    {t("پرسش")}: {entry.user}
                  </p>
                  <p dir="auto">{t("پاسخ")}: {entry.assistant}</p>
                </li>
              );
            })}
          </ol>
        </div>
      </div>
    </details>
  );
}
