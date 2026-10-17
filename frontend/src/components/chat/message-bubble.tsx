"use client";

import { AlertTriangle, Bot, User as UserIcon } from "lucide-react";

import { ThinkingPanel } from "@/components/chat/thinking-panel";
import { MessageTiming } from "@/components/chat/message-timing";
import { CitationList } from "@/components/chat/citations";
import { MessageImages } from "@/components/chat/message-images";
import { Markdown } from "@/components/markdown";
import { Badge } from "@/components/ui/badge";
import { SOURCE_LABEL, WEB_EVENT_LABEL } from "@/lib/labels";
import type { Message } from "@/lib/types";
import { cn } from "@/lib/utils";

interface BubbleProps {
  message: Pick<Message, "role" | "content" | "citations" | "meta">;
  streaming?: boolean;
  /** needed to build the URLs of attached images */
  conversationId?: string | null;
  /** local previews (blob URLs) of images that were just sent and are not part of the saved history yet */
  localImages?: string[];
}

export function MessageBubble({ message, streaming = false, conversationId, localImages }: BubbleProps) {
  const isUser = message.role === "user";
  const meta = message.meta;
  const imageUrls = localImages?.length
    ? localImages
    : conversationId
      ? (meta.images ?? []).map((i) => `/api/chat/conversations/${conversationId}/images/${i.id}`)
      : [];
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
          <>
            <MessageImages urls={imageUrls} />
            {message.content ? <UserText text={message.content} /> : null}
          </>
        ) : (
          <>
            {meta.thinking ? <ThinkingPanel text={meta.thinking} /> : null}
            <Markdown content={message.content} />
            {streaming ? <span className="mt-1 inline-block h-4 w-1.5 animate-pulse bg-primary align-middle" aria-hidden /> : null}
            {!streaming ? <CitationList citations={message.citations} /> : null}
            {!streaming && meta.mcp_command ? (
              <div className="mt-3">
                <Badge tone="info">
                  <span dir="ltr">
                    دستور MCP · /{meta.mcp_command.server}
                    {meta.mcp_command.tool ? `@${meta.mcp_command.tool}` : ""}
                  </span>
                </Badge>
              </div>
            ) : null}
            {!streaming && meta.skills?.length ? (
              <div className="mt-3 flex flex-wrap gap-1.5">
                {meta.skills?.map((n) => (
                  <Badge key={n} tone="info">
                    مهارت: {n}
                  </Badge>
                ))}
              </div>
            ) : null}
            {!streaming && meta.mcp_calls?.length ? (
              <div className="mt-2 space-y-1.5">
                {meta.mcp_calls.map((c, i) => (
                  <details
                    key={i}
                    className="rounded-md border border-border bg-muted/40 text-xs"
                    // bring the opened evidence into view above the message box (it often opens right at the bottom of the chat)
                    onToggle={(e) => {
                      const el = e.currentTarget;
                      if (el.open) requestAnimationFrame(() => el.scrollIntoView({ block: "nearest", behavior: "smooth" }));
                    }}
                  >
                    <summary className="flex cursor-pointer select-none items-center gap-2 px-2.5 py-1.5">
                      <Badge tone={c.ok ? "success" : "danger"}>
                        <span dir="ltr">
                          MCP · {c.server ?? "?"}/{c.tool}
                        </span>
                      </Badge>
                      <span className="text-muted-foreground">{c.ok ? "نتیجه‌ی ابزار (برای دیدن مدرک باز کنید)" : "ابزار با خطا مواجه شد"}</span>
                      <span className="ms-auto text-[11px] text-muted-foreground">{c.ms} ms</span>
                    </summary>
                    <div className="space-y-1.5 border-t border-border p-2.5">
                      {c.args && Object.keys(c.args).length ? (
                        <div>
                          <div className="mb-0.5 text-muted-foreground">ورودی</div>
                          <pre dir="ltr" className="max-h-40 overflow-auto whitespace-pre-wrap break-words rounded bg-card p-2 text-left">
                            {JSON.stringify(c.args, null, 2)}
                          </pre>
                        </div>
                      ) : null}
                      <div>
                        <div className="mb-0.5 text-muted-foreground">خروجی</div>
                        <pre dir="auto" className="max-h-[55vh] overflow-auto whitespace-pre-wrap break-words rounded bg-card p-2">
                          {c.result || "—"}
                        </pre>
                      </div>
                    </div>
                  </details>
                ))}
              </div>
            ) : null}
            {!streaming && meta.risky_commands?.length ? (
              <div role="alert" className="mt-3 space-y-1.5 rounded-md border border-danger/40 bg-danger/10 p-3 text-xs">
                <div className="flex items-center gap-1.5 text-sm font-semibold text-danger">
                  <AlertTriangle className="h-4 w-4" /> این پاسخ دستورهای پرریسک دارد؛ قبل از اجرا بررسی و در صورت امکان بکاپ بگیرید
                </div>
                <ul className="space-y-1">
                  {meta.risky_commands.map((r, i) => (
                    <li key={i} className="flex flex-wrap items-baseline gap-2">
                      <Badge tone={r.severity === "high" ? "danger" : "warning"}>{r.severity === "high" ? "خطرناک" : "احتیاط"}</Badge>
                      <code dir="ltr" className="rounded bg-card px-1.5 py-0.5 text-left">
                        {r.command}
                      </code>
                      <span className="text-muted-foreground" dir="auto">
                        {r.reason}
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}
            {!streaming && meta.timings ? (
              <div className="mt-2">
                <MessageTiming meta={meta} />
              </div>
            ) : null}
            {!streaming && meta.primary_source ? (
              <div className="mt-3 flex flex-wrap gap-1.5">
                {meta.confidence ? <ConfidenceBadge level={meta.confidence} /> : null}
                <Badge tone="neutral">منبع اصلی: {SOURCE_LABEL[meta.primary_source] ?? meta.primary_source}</Badge>
                {meta.answer_cache === "hit" ? <Badge tone="info">پاسخ از حافظه‌ی گفتگوها (جستجو انجام نشد)</Badge> : null}
                {meta.refreshed ? <Badge tone="info">جستجوی دوباره انجام شد</Badge> : null}
                {meta.web_event && meta.web_event !== "none" ? <Badge tone="neutral">{WEB_EVENT_LABEL[meta.web_event] ?? meta.web_event}</Badge> : null}
              </div>
            ) : null}
          </>
        )}
      </div>
    </div>
  );
}

const CONFIDENCE = {
  verified: { tone: "success", text: "مبتنی بر مستندات تأییدشده", hint: "پاسخ از مستندات داخلی، راه‌حل‌های تأییدشده یا آموزش‌های ادمین آمده است." },
  live: { tone: "info", text: "مبتنی بر داده‌ی زنده", hint: "پاسخ از وضعیت زنده‌ی کانتینر/CI یا نتیجه‌ی ابزارهای MCP آمده است." },
  external: { tone: "warning", text: "مبتنی بر منبع بیرونی (وب/GitHub)", hint: "این اطلاعات از اینترنت آمده و در مستندات داخلی تأیید نشده است." },
  model: { tone: "danger", text: "دانش عمومی مدل؛ تأییدنشده", hint: "هیچ منبع داخلی یا بیرونی پشتیبان این پاسخ نبود. قبل از اجرا درستی آن را بررسی کنید." },
} as const;

function ConfidenceBadge({ level }: { level: keyof typeof CONFIDENCE }) {
  const c = CONFIDENCE[level];
  return (
    <span title={c.hint}>
      <Badge tone={c.tone}>{c.text}</Badge>
    </span>
  );
}

/** The user's text; a leading MCP command (/server or /server@tool) is highlighted. */
function UserText({ text }: { text: string }) {
  const m = /^(\s*)(\/[A-Za-z0-9][A-Za-z0-9_-]*(?:@[A-Za-z0-9_.:-]+)?)(?=\s|$)/.exec(text);
  return (
    <p className="whitespace-pre-wrap break-words text-[0.95rem] leading-7" dir="auto">
      {m ? (
        <>
          {m[1]}
          <span dir="ltr" className="rounded bg-primary/10 px-1.5 py-0.5 font-semibold text-primary">
            {m[2]}
          </span>
          {text.slice(m[0].length)}
        </>
      ) : (
        text
      )}
    </p>
  );
}
