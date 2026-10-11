"use client";

import { useQueryClient } from "@tanstack/react-query";
import { LogOut, MessageSquare, Shield, Terminal } from "lucide-react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, type ReactNode } from "react";

import { Preferences } from "@/components/preferences";
import { HeaderStatus } from "@/components/system-status";
import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/misc";
import { api } from "@/lib/api";
import { useMe } from "@/lib/auth";
import { cn } from "@/lib/utils";

export default function AppLayout({ children }: { children: ReactNode }) {
  const { data: me, error, isLoading } = useMe();
  const router = useRouter();
  const qc = useQueryClient();
  const pathname = usePathname();

  useEffect(() => {
    if (error?.status === 401) router.replace("/login");
  }, [error, router]);

  if (isLoading || !me) {
    return (
      <div className="flex h-screen items-center justify-center">
        <Spinner className="h-6 w-6" />
      </div>
    );
  }

  async function logout() {
    await api.post("/auth/logout");
    qc.clear();
    router.replace("/login");
  }

  const nav = [
    { href: "/chat", label: "گفتگو", icon: MessageSquare, show: true },
    { href: "/admin", label: "مدیریت", icon: Shield, show: me.role === "admin" },
  ];

  return (
    <div className="flex h-screen flex-col">
      <header className="flex h-14 shrink-0 items-center justify-between border-b border-border bg-card px-4">
        <div className="flex items-center gap-6">
          <Link href="/chat" className="flex items-center gap-2 font-bold">
            <span className="rounded-md bg-primary p-1.5 text-primary-foreground">
              <Terminal className="h-4 w-4" />
            </span>
            دستیار DevOps
          </Link>
          <nav className="flex gap-1" aria-label="ناوبری اصلی">
            {nav
              .filter((n) => n.show)
              .map(({ href, label, icon: Icon }) => (
                <Link
                  key={href}
                  href={href}
                  className={cn(
                    "flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm hover:bg-muted",
                    pathname.startsWith(href) && "bg-muted font-medium",
                  )}
                >
                  <Icon className="h-4 w-4" /> {label}
                </Link>
              ))}
          </nav>
        </div>
        <div className="flex items-center gap-3 text-sm">
          <HeaderStatus />
          <Preferences />
          <span className="hidden text-muted-foreground sm:inline" dir="ltr">
            {me.email}
          </span>
          <Button variant="ghost" size="sm" onClick={logout}>
            <LogOut className="h-4 w-4" /> خروج
          </Button>
        </div>
      </header>
      <div className="min-h-0 flex-1">{children}</div>
    </div>
  );
}
