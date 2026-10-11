"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { CheckCircle2, XCircle } from "lucide-react";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";

import { ThinkingPanel } from "@/components/chat/thinking-panel";
import { Composer } from "@/components/chat/composer";
import { MessageBubble } from "@/components/chat/message-bubble";
import { SystemStatusBar } from "@/components/system-status";
import { Button } from "@/components/ui/button";
import { ErrorBanner, Spinner } from "@/components/ui/misc";
import { api } from "@/lib/api";
import { STEP_LABEL } from "@/lib/labels";
import { takePendingMessage, setPendingMessage } from "@/lib/pending";
import { streamMessage } from "@/lib/sse";
import type { Conversation, ConversationDetail, Message } from "@/lib/types";

interface Live {
  user: string;
  text: string;
  thinking: string;
  step: string | null;
}

const EXAMPLES = ["چطور Nginx را ریستارت کنم؟", "آخرین خطای کانتینر X چیست؟", "چرا آخرین بیلد شکست خورد؟"];

export function ChatView({ conversationId }: { conversationId: string | null }) {
  const qc = useQueryClient();
  const router = useRouter();
  const [live, setLive] = useState<Live | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [draft, setDraft] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);

  const detail = useQuery({
    queryKey: ["conversation", conversationId],
    queryFn: () => api.get<ConversationDetail>(`/chat/conversations/${conversationId}`),
    enabled: !!conversationId,
  });

  const send = useCallback(
    async (id: string, content: string) => {
      setError(null);
      setLive({ user: content, text: "", thinking: "", step: null });
      try {
        await streamMessage(id, content, {
          onStatus: (step) => setLive((l) => (l ? { ...l, step } : l)),
          onThinking: (t) => setLive((l) => (l ? { ...l, thinking: l.thinking + t } : l)),
          onToken: (t) => setLive((l) => (l ? { ...l, text: l.text + t } : l)),
        });
      } catch (e) {
        setError(e);
      } finally {
        await Promise.all([qc.invalidateQueries({ queryKey: ["conversation", id] }), qc.invalidateQueries({ queryKey: ["conversations"] })]);
        setLive(null);
      }
    },
    [qc],
  );

  // First message of a brand-new chat: conversation was created on /chat, stream starts here after navigation.
  useEffect(() => {
    if (!conversationId) return;
    const first = takePendingMessage(conversationId);
    if (first) void send(conversationId, first);
  }, [conversationId, send]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [detail.data?.messages.length, live?.text, live?.user]);

  const feedback = useMutation({
    mutationFn: (v: { messageId: string; outcome: "confirmed" | "rejected" }) =>
      api.post<{ conversation: Conversation; message: Message | null }>(`/chat/conversations/${conversationId}/feedback`, {
        message_id: v.messageId,
        outcome: v.outcome,
      }),
    onSuccess: async () => {
      await Promise.all([qc.invalidateQueries({ queryKey: ["conversation", conversationId] }), qc.invalidateQueries({ queryKey: ["conversations"] })]);
    },
  });

  async function submit() {
    const content = draft.trim();
    if (!content || live) return;
    setDraft("");
    if (!conversationId) {
      try {
        const c = await api.post<Conversation>("/chat/conversations");
        setPendingMessage(c.id, content);
        await qc.invalidateQueries({ queryKey: ["conversations"] });
        router.replace(`/chat/${c.id}`);
      } catch (e) {
        setError(e);
        setDraft(content);
      }
      return;
    }
    await send(conversationId, content);
  }

  const messages = detail.data?.messages ?? [];
  const phase = detail.data?.conversation.phase;
  const lastAssistantId = [...messages].reverse().find((m) => m.role === "assistant")?.id;
  const empty = !messages.length && !live;

  return (
    <div className="flex h-full flex-col">
      <div className="min-h-0 flex-1 overflow-y-auto">
        <div className="mx-auto max-w-3xl space-y-5 px-4 py-6">
          {empty ? (
            <div className="space-y-4 pt-16 text-center">
              <h2 className="text-2xl font-bold">چه مشکلی دارید؟</h2>
              <p className="text-sm text-muted-foreground">
                سؤال خود را بپرسید یا خطای build، deployment یا کانتینر را مستقیماً اینجا بچسبانید. ابتدا مستندات تأییدشده‌ی تیم بررسی می‌شود.
              </p>
              <div className="flex flex-wrap justify-center gap-2">
                {EXAMPLES.map((ex) => (
                  <button key={ex} type="button" onClick={() => setDraft(ex)} className="rounded-full border border-border bg-card px-3 py-1.5 text-sm hover:bg-muted">
                    {ex}
                  </button>
                ))}
              </div>
            </div>
          ) : null}

          {detail.isLoading && conversationId ? <Spinner className="mx-auto" /> : null}
          {detail.error ? <ErrorBanner error={detail.error} /> : null}

          {messages.map((m) => (
            <div key={m.id} className="space-y-2">
              <MessageBubble message={m} />
              {m.id === lastAssistantId && m.meta.awaiting_feedback && !live ? (
                <div className="flex flex-wrap items-center gap-2 ps-11">
                  <span className="text-sm text-muted-foreground">آیا این راه‌حل مشکل را حل کرد؟</span>
                  <Button variant="success" size="sm" disabled={feedback.isPending} onClick={() => feedback.mutate({ messageId: m.id, outcome: "confirmed" })}>
                    <CheckCircle2 className="h-4 w-4" /> مشکل حل شد (تأیید)
                  </Button>
                  <Button variant="dangerOutline" size="sm" disabled={feedback.isPending} onClick={() => feedback.mutate({ messageId: m.id, outcome: "rejected" })}>
                    <XCircle className="h-4 w-4" /> با خطا مواجه شدم (رد)
                  </Button>
                </div>
              ) : null}
              {m.meta.feedback === "confirmed" ? <p className="ps-11 text-xs text-success">✓ شما این راه‌حل را تأیید کردید.</p> : null}
              {m.meta.feedback === "rejected" ? <p className="ps-11 text-xs text-danger">✗ شما این راه‌حل را رد کردید.</p> : null}
            </div>
          ))}

          {live ? (
            <>
              <MessageBubble message={{ role: "user", content: live.user, citations: [], meta: {} }} />
              {live.thinking ? <div className="ps-11"><ThinkingPanel text={live.thinking} streaming={!live.text} /></div> : null}
              {live.text ? (
                <MessageBubble message={{ role: "assistant", content: live.text, citations: [], meta: {} }} streaming />
              ) : live.thinking ? null : (
                <div className="flex items-center gap-2 ps-11 text-sm text-muted-foreground" role="status">
                  <Spinner /> {live.step ? (STEP_LABEL[live.step] ?? "در حال پردازش…") : "در حال پردازش…"}
                </div>
              )}
            </>
          ) : null}

          <ErrorBanner error={feedback.error ?? error} />
          <div ref={bottomRef} />
        </div>
      </div>

      <div className="border-t border-border bg-card p-3">
        <div className="mx-auto max-w-3xl space-y-2">
          <SystemStatusBar />
          {phase === "awaiting_error" && !live ? (
            <p className="rounded-md bg-warning/10 px-3 py-2 text-sm text-warning" role="status">
              لطفاً خطا یا خروجی جدید را در کادر زیر بچسبانید؛ جستجوی بعدی با اطلاعات تازه و بدون تکرار پیشنهادهای ناموفق انجام می‌شود.
            </p>
          ) : null}
          <Composer
            value={draft}
            onChange={setDraft}
            onSubmit={() => void submit()}
            busy={!!live}
            placeholder={phase === "awaiting_error" ? "خطای جدید یا خروجی دستور را بچسبانید…" : "سؤال یا خطا را بنویسید…  (Enter ارسال · Shift+Enter خط جدید)"}
          />
          <p className="text-center text-[11px] text-muted-foreground">
            اسرار و توکن‌ها پیش از ذخیره و ارسال به مدل به‌صورت خودکار حذف می‌شوند. دستیار فقط‌خواندنی است و هیچ دستوری اجرا نمی‌کند.
          </p>
        </div>
      </div>
    </div>
  );
}
