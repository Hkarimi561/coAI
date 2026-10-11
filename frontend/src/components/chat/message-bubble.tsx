"use client";

import { Bot, User as UserIcon } from "lucide-react";

import { CitationList } from "@/components/chat/citations";
import { Markdown } from "@/components/markdown";
import { Badge } from "@/components/ui/badge";
import { SOURCE_LABEL, WEB_EVENT_LABEL } from "@/lib/labels";
import type { Message } from "@/lib/types";
import { cn } from "@/lib/utils";

export function MessageBubble({ message, streaming = false }: { message: Pick<Message, "role" | "content" | "citations" | "meta">; streaming?: boolean }) {
  const isUser = message.role === "user";
  const meta = message.meta;
  return (
    <div className={cn("flex gap-3", isUser && "flex-row-reverse")}>
      <div
        className={cn("mt-1 flex h-8 w-8 shrink-0 items-center justify-center rounded-full", isUser ? "bg-muted" : "bg-primary text-primary-foreground")}
        aria-hidden
      >
        {isUser ? <UserIcon className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
      </div>
      <div
        className={cn(
          "min-w-0 max-w-[85%] rounded-lg border px-4 py-3",
          isUser ? "border-primary/20 bg-primary/5" : "border-border bg-card",
        )}
      >
        {isUser ? (
          // Pasted logs must stay readable: each line picks its own direction, whitespace is preserved.
          <p className="whitespace-pre-wrap break-words text-[0.95rem] leading-7" dir="auto">
            {message.content}
          </p>
        ) : (
          <>
            <Markdown content={message.content} />
            {streaming ? <span className="mt-1 inline-block h-4 w-1.5 animate-pulse bg-primary align-middle" aria-hidden /> : null}
            {!streaming ? <CitationList citations={message.citations} /> : null}
            {!streaming && meta.primary_source ? (
              <div className="mt-3 flex flex-wrap gap-1.5">
                <Badge tone="neutral">منبع اصلی: {SOURCE_LABEL[meta.primary_source] ?? meta.primary_source}</Badge>
                {meta.web_event && meta.web_event !== "none" ? <Badge tone="neutral">{WEB_EVENT_LABEL[meta.web_event] ?? meta.web_event}</Badge> : null}
              </div>
            ) : null}
          </>
        )}
      </div>
    </div>
  );
}
