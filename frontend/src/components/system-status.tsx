"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";

import { api } from "@/lib/api";
import { useMe } from "@/lib/auth";
import type { ComponentKey, SystemStatus } from "@/lib/types";
import { cn } from "@/lib/utils";

export const COMPONENT_LABEL: Record<ComponentKey, string> = {
  llm: "مدل زبانی (LLM)",
  embeddings: "مدل Embedding",
  qdrant: "پایگاه برداری Qdrant",
  postgres: "PostgreSQL",
  redis: "Redis",
  web_search: "جستجوی وب",
  docker: "بازرسی Docker",
  ci: "CI",
};

export function useSystemStatus() {
  return useQuery({
    queryKey: ["system-status"],
    queryFn: () => api.get<SystemStatus>("/system/status"),
    refetchInterval: 20_000,
    staleTime: 10_000,
  });
}

export function Dot({ ok }: { ok: boolean | null }) {
  return (
    <span
      aria-hidden
      className={cn("inline-block h-2.5 w-2.5 shrink-0 rounded-full", ok === true && "bg-success", ok === false && "bg-danger", ok === null && "animate-pulse bg-warning")}
    />
  );
}

export const stateText = (ok: boolean | null, nullText = "در حال بارگذاری / غیرفعال") => (ok === true ? "متصل" : ok === false ? "قطع" : nullText);

/** Compact header indicator: AI = LLM + embeddings. Admins can click through to the detailed page. */
export function HeaderStatus() {
  const { data, isError } = useSystemStatus();
  const { data: me } = useMe();
  if (isError) {
    return (
      <span className="flex items-center gap-1.5 text-xs text-danger">
        <Dot ok={false} /> سرور در دسترس نیست
      </span>
    );
  }
  if (!data) return null;
  const { llm, embeddings } = data.components;
  const content = (
    <span className="flex items-center gap-3 rounded-md border border-border px-2.5 py-1 text-xs">
      <span className="flex items-center gap-1.5" title={me?.role === "admin" ? llm.detail : undefined}>
        <Dot ok={llm.ok} /> هوش مصنوعی: {stateText(llm.ok)}
      </span>
      <span className="flex items-center gap-1.5" title={me?.role === "admin" ? embeddings.detail : undefined}>
        <Dot ok={embeddings.ok} /> جستجوی معنایی: {stateText(embeddings.ok, "در حال آماده‌سازی")}
      </span>
    </span>
  );
  return me?.role === "admin" ? (
    <Link href="/admin/status" aria-label="وضعیت سیستم">
      {content}
    </Link>
  ) : (
    content
  );
}

/** Warning banner shown on chat / documents pages while the assistant cannot answer. */
export function SystemStatusBar() {
  const { data } = useSystemStatus();
  const { data: me } = useMe();
  if (!data || data.assistant_ready) return null;
  const { llm, embeddings } = data.components;
  const problems: string[] = [];
  if (llm.ok !== true) problems.push("مدل زبانی در دسترس نیست");
  if (embeddings.ok === false) problems.push("مدل Embedding بارگذاری نشده است (ایندکس و جستجوی مستندات کار نمی‌کند)");
  if (embeddings.ok === null) problems.push("مدل Embedding هنوز در حال آماده‌سازی است");
  return (
    <div role="status" className="rounded-md border border-warning/40 bg-warning/10 px-3 py-2 text-sm text-warning">
      {problems.join(" · ")}.{" "}
      {me?.role === "admin" ? (
        <Link href="/admin/status" className="underline">
          جزئیات و راه‌حل
        </Link>
      ) : (
        "لطفاً به مدیر سیستم اطلاع دهید."
      )}
    </div>
  );
}
