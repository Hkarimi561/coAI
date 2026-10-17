"use client";

import { useQuery } from "@tanstack/react-query";
import { FileText, GraduationCap, MessagesSquare, Plug, Sparkles, Users } from "lucide-react";
import Link from "next/link";
import type { ReactNode } from "react";

import { Card } from "@/components/ui/card";
import { Spinner } from "@/components/ui/misc";
import { api } from "@/lib/api";
import type { AdminOverview } from "@/lib/types";
import { useT } from "@/lib/i18n";
import { cn, formatNumber } from "@/lib/utils";

/** Counts for the sidebar badges and the dashboard cards (shared cache, refreshed every 15 s). */
export function useAdminOverview() {
  return useQuery({
    queryKey: ["admin-overview"],
    queryFn: () => api.get<AdminOverview>("/admin/overview"),
    refetchInterval: 15_000,
    staleTime: 10_000,
  });
}

function StatCard({ href, icon, label, value, hint, tone }: { href: string; icon: ReactNode; label: string; value: string; hint?: string; tone?: "warning" | "danger" }) {
  return (
    <Link href={href} className="group block focus-visible:outline-none">
      <Card className={cn("h-full p-4 transition-colors group-hover:border-primary/50 group-focus-visible:ring-2 group-focus-visible:ring-primary/40", tone === "warning" && "border-warning/50", tone === "danger" && "border-danger/50")}>
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <span className="text-primary">{icon}</span>
          {label}
        </div>
        <div className="mt-1.5 text-3xl font-bold tabular-nums">{value}</div>
        {hint ? <div className="mt-1 text-xs text-muted-foreground">{hint}</div> : null}
      </Card>
    </Link>
  );
}

/** Top of the dashboard: the state of every area at a glance; each card opens its page. */
export function OverviewCards() {
  const t = useT();
  const { data: o, isLoading } = useAdminOverview();
  if (isLoading || !o) return <Spinner className="mx-auto h-5 w-5" />;
  const icon = "h-4 w-4";
  return (
    <section aria-label={t("نمای کلی")} className="space-y-3">
      <h1 className="text-lg font-bold">{t("داشبورد مدیریت")}</h1>
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <StatCard
          href="/admin/documents"
          icon={<FileText className={icon} />}
          label={t("چانک‌های مستندات")}
          value={formatNumber(o.documents.chunks)}
          hint={`${formatNumber(o.documents.count)} ${t("سند")}${o.documents.errors ? ` · ${formatNumber(o.documents.errors)} ${t("با خطا")}` : ""}`}
          tone={o.documents.errors ? "danger" : undefined}
        />
        <StatCard href="/admin/skills" icon={<Sparkles className={icon} />} label={t("مهارت‌های فعال")} value={formatNumber(o.skills.enabled)} hint={t("از {n} مهارت").replace("{n}", formatNumber(o.skills.total))} />
        <StatCard
          href="/admin/mcp"
          icon={<Plug className={icon} />}
          label={t("ابزارهای MCP فعال")}
          value={formatNumber(o.mcp.tools_enabled)}
          hint={t("{a} سرور فعال از {b}").replace("{a}", formatNumber(o.mcp.enabled)).replace("{b}", formatNumber(o.mcp.servers))}
        />
        <StatCard
          href="/admin/lessons"
          icon={<GraduationCap className={icon} />}
          label={t("آموزش‌های در انتظار تأیید")}
          value={formatNumber(o.lessons_pending)}
          tone={o.lessons_pending ? "warning" : undefined}
        />
        <StatCard
          href="/admin/conversations"
          icon={<MessagesSquare className={icon} />}
          label={t("گفتگوهای منتظر بازبینی")}
          value={formatNumber(o.conversations.pending_review)}
          hint={`${formatNumber(o.conversations.total)} ${t("گفتگو در کل")}`}
          tone={o.conversations.pending_review ? "warning" : undefined}
        />
        <StatCard href="/admin/users" icon={<Users className={icon} />} label={t("کاربران")} value={formatNumber(o.users)} />
      </div>
    </section>
  );
}
