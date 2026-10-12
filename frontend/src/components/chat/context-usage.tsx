"use client";

import { useEffect, useRef, useState } from "react";

import type { Message } from "@/lib/types";
import { cn, formatNumber } from "@/lib/utils";

/** Token usage of this chat so far, like Claude's context indicator: a ring next to the send button, details in a popover. */
export function ContextUsage({ messages, contextWindow }: { messages: Pick<Message, "role" | "meta">[]; contextWindow?: number }) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (!open) return;
    const onDown = (e: MouseEvent) => {
      if (!ref.current?.contains(e.target as Node)) setOpen(false);
    };
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setOpen(false);
    };
    document.addEventListener("mousedown", onDown);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDown);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  const used = messages.map((m) => m.meta.usage).filter((u): u is NonNullable<typeof u> => !!u);
  const input = used.reduce((a, u) => a + u.prompt_tokens, 0);
  const output = used.reduce((a, u) => a + u.completion_tokens, 0);
  const last = [...used].reverse().find((u) => u.total_tokens > 0);
  const estimated = used.some((u) => u.estimated);
  const ctxUsed = last ? last.total_tokens : 0; // what the last exchange occupied in the context window
  const pct = contextWindow ? Math.min(1, ctxUsed / contextWindow) : 0;
  const tone = pct > 0.9 ? "text-danger" : pct > 0.7 ? "text-warning" : "text-primary";

  const R = 9;
  const C = 2 * Math.PI * R;
  return (
    <div ref={ref} className="relative mb-0.5 shrink-0">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        aria-label="مصرف توکن این گفتگو"
        aria-expanded={open}
        title="مصرف توکن"
        className="flex h-9 w-9 items-center justify-center rounded-full text-muted-foreground transition-colors hover:bg-muted"
      >
        <svg viewBox="0 0 24 24" className="h-6 w-6 -rotate-90">
          <circle cx="12" cy="12" r={R} fill="none" strokeWidth="3" className="stroke-border" />
          <circle
            cx="12"
            cy="12"
            r={R}
            fill="none"
            strokeWidth="3"
            strokeLinecap="round"
            className={cn("stroke-current transition-all", tone)}
            strokeDasharray={C}
            strokeDashoffset={C * (1 - pct)}
          />
        </svg>
      </button>
      {open ? (
        <div role="dialog" className="absolute bottom-full end-0 z-30 mb-2 w-72 max-w-[85vw] space-y-3 rounded-lg border border-border bg-card p-3 text-sm shadow-lg">
          <div>
            <div className="mb-1 flex items-baseline justify-between">
              <span className="font-semibold">پنجره‌ی زمینه (Context)</span>
              {contextWindow ? <span className="text-xs text-muted-foreground">{formatNumber(Math.round(pct * 100))}٪</span> : null}
            </div>
            <div className="h-2 overflow-hidden rounded-full bg-muted">
              <div className={cn("h-full rounded-full bg-current transition-all", tone)} style={{ width: `${pct * 100}%` }} />
            </div>
            <div className="mt-1 text-xs text-muted-foreground">
              {formatNumber(ctxUsed)}
              {contextWindow ? ` از ${formatNumber(contextWindow)}` : ""} توکن در آخرین تبادل{estimated ? " (تقریبی)" : ""}
            </div>
          </div>
          <div className="space-y-1 border-t border-border pt-2 text-xs">
            <div className="mb-1 text-sm font-semibold">مصرف کل این گفتگو</div>
            <div className="flex justify-between">
              <span>توکن ورودی (پرامپت)</span>
              <span className="tabular-nums">{formatNumber(input)}</span>
            </div>
            <div className="flex justify-between">
              <span>توکن خروجی (پاسخ و تفکر)</span>
              <span className="tabular-nums">{formatNumber(output)}</span>
            </div>
            <div className="flex justify-between border-t border-border pt-1 font-semibold">
              <span>مجموع</span>
              <span className="tabular-nums">{formatNumber(input + output)}</span>
            </div>
            <div className="flex justify-between text-muted-foreground">
              <span>تعداد پاسخ مدل</span>
              <span className="tabular-nums">{formatNumber(used.filter((u) => u.total_tokens > 0).length)}</span>
            </div>
          </div>
          <p className="text-[11px] leading-5 text-muted-foreground">
            پرامپت هر پیام شامل منابع بازیابی‌شده و تاریخچه است، پس ورودی از متن پیام شما بزرگ‌تر است.
            {estimated ? " برخی مقادیر تخمینی است چون سرور مدل شمارش توکن برنگردانده است." : ""}
          </p>
        </div>
      ) : null}
    </div>
  );
}
