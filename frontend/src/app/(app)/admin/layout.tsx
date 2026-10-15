"use client";

import {
  Activity,
  Boxes,
  Database,
  FileText,
  GraduationCap,
  LayoutDashboard,
  Menu,
  MessagesSquare,
  Plug,
  SearchX,
  Settings,
  Sparkles,
  Users,
  X,
  type LucideIcon,
} from "lucide-react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState, type ReactNode } from "react";

import { useAdminOverview } from "@/components/admin/overview";
import { Badge } from "@/components/ui/badge";
import { Spinner } from "@/components/ui/misc";
import { useMe } from "@/lib/auth";
import type { AdminOverview } from "@/lib/types";
import { cn, formatNumber } from "@/lib/utils";

interface NavBadge {
  text: string;
  tone: "neutral" | "info" | "success" | "warning" | "danger";
  title?: string;
}
interface NavItem {
  href: string;
  label: string;
  icon: LucideIcon;
  exact?: boolean;
  badge?: (o: AdminOverview) => NavBadge | null;
}

const GROUPS: { title: string; items: NavItem[] }[] = [
  {
    title: "نمای کلی",
    items: [
      { href: "/admin", label: "داشبورد", icon: LayoutDashboard, exact: true },
      { href: "/admin/status", label: "وضعیت سیستم", icon: Activity },
    ],
  },
  {
    title: "دانش",
    items: [
      {
        href: "/admin/documents",
        label: "مستندات",
        icon: FileText,
        badge: (o) => ({
          text: `${formatNumber(o.documents.chunks)} چانک`,
          tone: o.documents.errors ? "danger" : "info",
          title: `${formatNumber(o.documents.count)} سند · ${formatNumber(o.documents.chunks)} چانک${o.documents.errors ? ` · ${formatNumber(o.documents.errors)} سند با خطا` : ""}`,
        }),
      },
      { href: "/admin/skills", label: "مهارت‌ها", icon: Sparkles, badge: (o) => (o.skills.total ? { text: formatNumber(o.skills.enabled), tone: "neutral", title: "مهارت‌های فعال" } : null) },
      {
        href: "/admin/lessons",
        label: "آموزش‌ها",
        icon: GraduationCap,
        badge: (o) => (o.lessons_pending ? { text: formatNumber(o.lessons_pending), tone: "warning", title: "در انتظار تأیید" } : null),
      },
      { href: "/admin/gaps", label: "شکاف‌های دانش", icon: SearchX },
      { href: "/admin/cache", label: "کش جستجوی وب", icon: Database, badge: (o) => (o.cache_entries ? { text: formatNumber(o.cache_entries), tone: "neutral" } : null) },
    ],
  },
  {
    title: "ابزارها و دسترسی",
    items: [
      {
        href: "/admin/mcp",
        label: "سرورهای MCP",
        icon: Plug,
        badge: (o) => (o.mcp.servers ? { text: formatNumber(o.mcp.servers), tone: "neutral", title: `${formatNumber(o.mcp.servers)} سرور (${formatNumber(o.mcp.enabled)} فعال) · ${formatNumber(o.mcp.tools_enabled)} ابزار فعال` } : null),
      },
      { href: "/admin/containers", label: "دسترسی داکر", icon: Boxes },
    ],
  },
  {
    title: "گفتگوها",
    items: [
      {
        href: "/admin/conversations",
        label: "گفتگوها",
        icon: MessagesSquare,
        badge: (o) => (o.conversations.pending_review ? { text: formatNumber(o.conversations.pending_review), tone: "warning", title: "منتظر بازبینی" } : null),
      },
    ],
  },
  {
    title: "مدیریت",
    items: [
      { href: "/admin/users", label: "کاربران", icon: Users, badge: (o) => ({ text: formatNumber(o.users), tone: "neutral" }) },
      { href: "/admin/settings", label: "تنظیمات", icon: Settings },
    ],
  },
];

export default function AdminLayout({ children }: { children: ReactNode }) {
  const { data: me } = useMe();
  const { data: overview } = useAdminOverview();
  const router = useRouter();
  const pathname = usePathname();
  const [open, setOpen] = useState(false); // mobile menu

  useEffect(() => {
    if (me && me.role !== "admin") router.replace("/chat");
  }, [me, router]);
  useEffect(() => setOpen(false), [pathname]);

  if (!me || me.role !== "admin") {
    return (
      <div className="flex h-full items-center justify-center">
        <Spinner className="h-6 w-6" />
      </div>
    );
  }

  const current = GROUPS.flatMap((g) => g.items).find((i) => (i.exact ? pathname === i.href : pathname.startsWith(i.href)));

  return (
    <div className="flex h-full flex-col md:flex-row">
      {/* mobile bar */}
      <div className="flex shrink-0 items-center gap-2 border-b border-border bg-card px-4 py-2 md:hidden">
        <button type="button" onClick={() => setOpen((o) => !o)} aria-expanded={open} aria-label="منوی مدیریت" className="rounded-md p-1.5 hover:bg-muted">
          {open ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </button>
        <span className="text-sm font-medium">{current?.label ?? "مدیریت"}</span>
      </div>

      <aside
        aria-label="مدیریت"
        className={cn("shrink-0 overflow-y-auto border-border bg-card md:block md:w-64 md:border-e", open ? "block max-h-[60vh] border-b" : "hidden")}
      >
        <nav className="space-y-5 p-3">
          {GROUPS.map((g) => (
            <div key={g.title}>
              <div className="mb-1 px-3 text-[11px] font-semibold tracking-wide text-muted-foreground">{g.title}</div>
              <ul className="space-y-0.5">
                {g.items.map((item) => {
                  const active = item.exact ? pathname === item.href : pathname.startsWith(item.href);
                  const badge = overview ? item.badge?.(overview) : null;
                  return (
                    <li key={item.href}>
                      <Link
                        href={item.href}
                        aria-current={active ? "page" : undefined}
                        className={cn(
                          "flex items-center gap-2.5 rounded-md px-3 py-2 text-sm transition-colors",
                          active ? "bg-primary/10 font-semibold text-primary" : "text-foreground/80 hover:bg-muted hover:text-foreground",
                        )}
                      >
                        <item.icon className="h-4 w-4 shrink-0" />
                        <span className="min-w-0 flex-1 truncate">{item.label}</span>
                        {badge ? (
                          <span title={badge.title}>
                            <Badge tone={badge.tone} className="tabular-nums">
                              {badge.text}
                            </Badge>
                          </span>
                        ) : null}
                      </Link>
                    </li>
                  );
                })}
              </ul>
            </div>
          ))}
        </nav>
      </aside>

      <main className="min-h-0 flex-1 overflow-y-auto">
        <div className="mx-auto max-w-6xl space-y-5 p-4 md:p-6">{children}</div>
      </main>
    </div>
  );
}
