"use client";

import { useQuery } from "@tanstack/react-query";
import { GraduationCap, Plus } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";

import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/misc";
import { api } from "@/lib/api";
import { STATUS_LABEL } from "@/lib/labels";
import type { Conversation } from "@/lib/types";
import { cn } from "@/lib/utils";

const DOT: Record<Conversation["status"], string> = {
  unresolved: "bg-muted-foreground/40",
  pending_review: "bg-warning",
  resolved: "bg-success",
};

export default function ChatLayout({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const { data, isLoading } = useQuery({ queryKey: ["conversations"], queryFn: () => api.get<Conversation[]>("/chat/conversations") });

  return (
    <div className="flex h-full">
      <aside className="hidden w-72 shrink-0 flex-col border-e border-border bg-card md:flex" aria-label="گفتگوها">
        <div className="space-y-2 p-3">
          <Button asChild className="w-full">
            <Link href="/chat">
              <Plus className="h-4 w-4" /> گفتگوی جدید
            </Link>
          </Button>
          <Button asChild variant="outline" className="w-full">
            <Link href="/chat?teach=1">
              <GraduationCap className="h-4 w-4" /> آموزش به هوش مصنوعی
            </Link>
          </Button>
        </div>
        <div className="min-h-0 flex-1 overflow-y-auto px-2 pb-3">
          {isLoading ? <Spinner className="mx-auto mt-4" /> : null}
          {data?.length === 0 ? <p className="p-3 text-center text-xs text-muted-foreground">هنوز گفتگویی ندارید.</p> : null}
          <ul className="space-y-0.5">
            {data?.map((c) => (
              <li key={c.id}>
                <Link
                  href={`/chat/${c.id}`}
                  title={STATUS_LABEL[c.status]}
                  className={cn(
                    "flex items-center gap-2 rounded-md px-3 py-2 text-sm hover:bg-muted",
                    pathname === `/chat/${c.id}` && "bg-muted font-medium",
                  )}
                >
                  {c.mode === "teach" ? <GraduationCap className="h-3.5 w-3.5 shrink-0 text-primary" aria-label="گفتگوی آموزشی" /> : <span className={cn("h-2 w-2 shrink-0 rounded-full", DOT[c.status])} aria-hidden />}
                  <span className="truncate" dir="auto">
                    {c.title || "گفتگوی جدید"}
                  </span>
                </Link>
              </li>
            ))}
          </ul>
        </div>
      </aside>
      <section className="min-w-0 flex-1">{children}</section>
    </div>
  );
}
