"use client";

import { AlertTriangle, Loader2 } from "lucide-react";
import type { ReactNode } from "react";

import { useT } from "@/lib/i18n";
import { cn, formatNumber } from "@/lib/utils";

export function Spinner({ className }: { className?: string }) {
  const t = useT();
  return <Loader2 className={cn("h-4 w-4 animate-spin", className)} aria-label={t("در حال بارگذاری")} />;
}

export function ErrorBanner({ error }: { error: unknown }) {
  if (!error) return null;
  const message = error instanceof Error ? error.message : String(error);
  return (
    <div role="alert" className="flex items-start gap-2 rounded-md border border-danger/30 bg-danger/5 p-3 text-sm text-danger">
      <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
      <span className="ltr:text-left" dir="auto">
        {message}
      </span>
    </div>
  );
}

export function Empty({ children }: { children: ReactNode }) {
  return <div className="rounded-lg border border-dashed border-border p-8 text-center text-sm text-muted-foreground">{children}</div>;
}

export function Pager({ page, pageSize, total, onPage }: { page: number; pageSize: number; total: number; onPage: (p: number) => void }) {
  const t = useT();
  const pages = Math.max(1, Math.ceil(total / pageSize));
  return (
    <div className="flex items-center justify-between pt-3 text-sm text-muted-foreground">
      <span>
        {t("صفحه {p} از {n} — {total} مورد").replace("{p}", formatNumber(page)).replace("{n}", formatNumber(pages)).replace("{total}", formatNumber(total))}
      </span>
      <div className="flex gap-2">
        <button className="rounded-md border border-border px-3 py-1 disabled:opacity-40" disabled={page <= 1} onClick={() => onPage(page - 1)}>
          {t("قبلی")}
        </button>
        <button className="rounded-md border border-border px-3 py-1 disabled:opacity-40" disabled={page >= pages} onClick={() => onPage(page + 1)}>
          {t("بعدی")}
        </button>
      </div>
    </div>
  );
}
