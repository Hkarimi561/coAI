"use client";

import { useQuery } from "@tanstack/react-query";
import { ArrowDown, ArrowUp, Download, Minus } from "lucide-react";
import Link from "next/link";
import { useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Select } from "@/components/ui/input";
import { Empty, ErrorBanner, Spinner } from "@/components/ui/misc";
import { api } from "@/lib/api";
import type { GapReport } from "@/lib/types";
import { formatDateTime, formatNumber, formatPercent } from "@/lib/utils";

const KIND_LABEL = { no_source: "بدون منبع (فقط دانش مدل)", web_fallback: "نیاز به جستجوی وب", rejected: "راه‌حل رد شد" } as const;
const KIND_TONE = { no_source: "warning", web_fallback: "info", rejected: "danger" } as const;

export default function GapsPage() {
  const [days, setDays] = useState(7);
  const report = useQuery({ queryKey: ["admin-gaps", days], queryFn: () => api.get<GapReport>(`/admin/gaps?days=${days}`) });
  const r = report.data;
  const delta = r ? r.gap_rate - r.previous.gap_rate : 0;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-2">
        <h1 className="me-auto text-lg font-bold">گزارش شکاف‌های دانش</h1>
        <Select className="w-40" value={days} onChange={(e) => setDays(Number(e.target.value))} aria-label="بازه‌ی زمانی">
          <option value={7}>۷ روز اخیر (هفتگی)</option>
          <option value={14}>۱۴ روز اخیر</option>
          <option value={30}>۳۰ روز اخیر</option>
        </Select>
        <a href={`/api/admin/gaps/export?days=${days}`} download>
          <Button variant="outline">
            <Download className="h-4 w-4" /> دانلود گزارش (.md)
          </Button>
        </a>
      </div>
      <p className="text-sm text-muted-foreground">
        سؤال‌هایی که دستیار نتوانست از مستندات یا ابزارها پاسخ دهد (فقط با دانش خودِ مدل)، به جستجوی وب نیاز پیدا کرد یا کاربر راه‌حلش را رد کرد. سؤال‌های مشابه گروه‌بندی می‌شوند؛
        بالای فهرست یعنی بیشترین نیاز به نوشتن مستند یا مهارت جدید.
      </p>

      <ErrorBanner error={report.error} />
      {report.isLoading ? <Spinner className="mx-auto" /> : null}

      {r ? (
        <>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <Card className="p-4">
              <div className="text-xs text-muted-foreground">پاسخ‌های دستیار</div>
              <div className="text-2xl font-bold">{formatNumber(r.turns)}</div>
            </Card>
            <Card className="p-4">
              <div className="text-xs text-muted-foreground">پاسخ‌های ضعیف</div>
              <div className="text-2xl font-bold">{formatNumber(r.gap_turns)}</div>
            </Card>
            <Card className="p-4">
              <div className="text-xs text-muted-foreground">نرخ ضعف</div>
              <div className="flex items-center gap-2 text-2xl font-bold">
                {formatPercent(r.gap_rate)}
                {r.previous.turns ? (
                  <span className={`flex items-center text-xs font-normal ${delta > 0.005 ? "text-danger" : delta < -0.005 ? "text-success" : "text-muted-foreground"}`}>
                    {delta > 0.005 ? <ArrowUp className="h-3 w-3" /> : delta < -0.005 ? <ArrowDown className="h-3 w-3" /> : <Minus className="h-3 w-3" />}
                    نسبت به دوره‌ی قبل ({formatPercent(r.previous.gap_rate)})
                  </span>
                ) : null}
              </div>
            </Card>
            <Card className="space-y-1 p-4 text-xs">
              {(Object.keys(KIND_LABEL) as (keyof typeof KIND_LABEL)[]).map((k) => (
                <div key={k} className="flex justify-between">
                  <span>{KIND_LABEL[k]}</span>
                  <span className="tabular-nums">{formatNumber(r.kinds[k])}</span>
                </div>
              ))}
            </Card>
          </div>

          {r.clusters.length === 0 ? <Empty>در این بازه موردی ثبت نشده است. 🎉</Empty> : null}
          <div className="space-y-3">
            {r.clusters.map((c, i) => (
              <Card key={i} className="space-y-2 p-4">
                <div className="flex flex-wrap items-start gap-2">
                  <span className="rounded bg-primary/10 px-2 py-0.5 text-xs font-semibold text-primary">{formatNumber(i + 1)}</span>
                  <div className="min-w-0 flex-1 font-medium" dir="auto">
                    {c.title}
                  </div>
                  <Badge tone="neutral">{formatNumber(c.count)} بار</Badge>
                </div>
                <div className="flex flex-wrap items-center gap-1.5">
                  {(Object.keys(KIND_LABEL) as (keyof typeof KIND_LABEL)[])
                    .filter((k) => c.kinds[k] > 0)
                    .map((k) => (
                      <Badge key={k} tone={KIND_TONE[k]}>
                        {KIND_LABEL[k]} × {formatNumber(c.kinds[k])}
                      </Badge>
                    ))}
                  <span className="text-xs text-muted-foreground">آخرین بار: {formatDateTime(c.last_seen)}</span>
                </div>
                <details className="text-sm">
                  <summary className="cursor-pointer text-xs text-muted-foreground">نمونه سؤال‌ها</summary>
                  <ul className="mt-1.5 space-y-1">
                    {c.examples.map((e, j) => (
                      <li key={j} className="flex flex-wrap items-baseline gap-2 rounded bg-muted/50 px-2 py-1">
                        <span className="min-w-0 flex-1 whitespace-pre-wrap break-words" dir="auto">
                          {e.query}
                        </span>
                        <Link href={`/admin/conversations/${e.conversation_id}`} className="text-xs text-primary underline">
                          مشاهده‌ی گفتگو
                        </Link>
                      </li>
                    ))}
                  </ul>
                </details>
              </Card>
            ))}
          </div>
        </>
      ) : null}
    </div>
  );
}
