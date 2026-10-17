"use client";

import { RefreshCw } from "lucide-react";

import { COMPONENT_LABEL, Dot, stateText, useSystemStatus } from "@/components/system-status";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { ErrorBanner, Spinner } from "@/components/ui/misc";
import type { ComponentKey } from "@/lib/types";
import { formatNumber } from "@/lib/utils";
import { useT } from "@/lib/i18n";

const HINTS: Partial<Record<ComponentKey, string>> = {
  llm: "Ollama باید روی میزبان اجرا شود و روی 0.0.0.0 گوش دهد (OLLAMA_HOST=0.0.0.0). مقدار LLM_BASE_URL و LLM_MODEL را در .env بررسی کنید.",
  embeddings:
    "اولین راه‌اندازی مدل را از HuggingFace دانلود می‌کند. اگر شبکه به اینترنت دسترسی ندارد: EMBEDDING_PROVIDER=ollama و EMBEDDING_MODEL=bge-m3 (پس از ollama pull bge-m3) را تنظیم کنید.",
  qdrant: "سرویس qdrant باید در docker compose در حال اجرا باشد: docker compose ps",
  web_search: "سرویس searxng را بررسی کنید یا WEBSEARCH_PROVIDER=none بگذارید (غیرفعال).",
};

export default function StatusPage() {
  const t = useT();
  const { data, isLoading, error, refetch, isFetching } = useSystemStatus();
  if (isLoading) return <Spinner className="mx-auto mt-10 h-6 w-6" />;
  if (error || !data) return <ErrorBanner error={error ?? t("سرور پاسخ نمی‌دهد")} />;

  const docs = data.documents ?? {};
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-lg font-bold">{t("وضعیت سیستم و اتصال هوش مصنوعی")}</h1>
        <Button variant="outline" size="sm" onClick={() => void refetch()} disabled={isFetching}>
          {isFetching ? <Spinner /> : <RefreshCw className="h-4 w-4" />} {t("بررسی مجدد")}
        </Button>
      </div>
      <p className="text-sm text-muted-foreground">{t("این صفحه هر ۲۰ ثانیه به‌روز می‌شود.")}</p>

      <Card className="divide-y divide-border">
        {(Object.keys(data.components) as ComponentKey[]).map((key) => {
          const c = data.components[key];
          return (
            <div key={key} className="space-y-1 p-4">
              <div className="flex items-center gap-2">
                <Dot ok={c.ok} />
                <span className="font-medium">{t(COMPONENT_LABEL[key])}</span>
                <span className="text-sm text-muted-foreground">— {stateText(c.ok, key === "embeddings" ? t("در حال آماده‌سازی") : t("غیرفعال / تنظیم‌نشده"))}</span>
              </div>
              {c.detail ? <p className="ltr break-words ps-5 text-xs text-muted-foreground">{c.detail}</p> : null}
              {c.ok === false && HINTS[key] ? <p className="ps-5 text-sm text-warning">{t(HINTS[key] ?? "")}</p> : null}
            </div>
          );
        })}
      </Card>

      <Card className="p-4 text-sm">
        <span className="font-medium">{t("مستندات:")} </span>
        {t("ایندکس‌شده")} {formatNumber(docs.indexed ?? 0)} · {t("دارای خطا")} {formatNumber(docs.error ?? 0)}
        {(docs.error ?? 0) > 0 ? (
          <span className="text-muted-foreground"> {t("— پس از رفع مشکل Embedding، در صفحه‌ی مستندات «ایندکس تغییرات» را بزنید.")}</span>
        ) : null}
      </Card>
    </div>
  );
}
