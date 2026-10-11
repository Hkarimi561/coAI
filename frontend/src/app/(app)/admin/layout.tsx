"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, type ReactNode } from "react";

import { Spinner } from "@/components/ui/misc";
import { useMe } from "@/lib/auth";
import { cn } from "@/lib/utils";

const TABS = [
  { href: "/admin", label: "داشبورد و آمار", exact: true },
  { href: "/admin/conversations", label: "گفتگوها" },
  { href: "/admin/documents", label: "مستندات" },
  { href: "/admin/cache", label: "کش جستجوی وب" },
  { href: "/admin/users", label: "کاربران" },
];

export default function AdminLayout({ children }: { children: ReactNode }) {
  const { data: me } = useMe();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (me && me.role !== "admin") router.replace("/chat");
  }, [me, router]);

  if (!me || me.role !== "admin") {
    return (
      <div className="flex h-full items-center justify-center">
        <Spinner className="h-6 w-6" />
      </div>
    );
  }

  return (
    <div className="h-full overflow-y-auto">
      <div className="mx-auto max-w-7xl space-y-5 p-4 md:p-6">
        <nav className="flex flex-wrap gap-1 border-b border-border" aria-label="مدیریت">
          {TABS.map((t) => {
            const active = t.exact ? pathname === t.href : pathname.startsWith(t.href);
            return (
              <Link
                key={t.href}
                href={t.href}
                aria-current={active ? "page" : undefined}
                className={cn(
                  "-mb-px border-b-2 px-4 py-2 text-sm",
                  active ? "border-primary font-semibold text-primary" : "border-transparent text-muted-foreground hover:text-foreground",
                )}
              >
                {t.label}
              </Link>
            );
          })}
        </nav>
        {children}
      </div>
    </div>
  );
}
