"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { CheckCircle2, GraduationCap, RefreshCw, Send, XCircle } from "lucide-react";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";

import { ThinkingPanel } from "@/components/chat/thinking-panel";
import { Composer } from "@/components/chat/composer";
import { ContextUsage } from "@/components/chat/context-usage";
import { MemoryPanel } from "@/components/chat/memory-panel";
import { MessageBubble } from "@/components/chat/message-bubble";
import { SystemStatusBar, useSystemStatus } from "@/components/system-status";
import { Button } from "@/components/ui/button";
import { ErrorBanner, Spinner } from "@/components/ui/misc";
import { api } from "@/lib/api";
import { STEP_LABEL } from "@/lib/labels";
import { takePendingMessage, setPendingMessage } from "@/lib/pending";
import { attachStream, streamMessage } from "@/lib/sse";
import type { Conversation, ConversationDetail, Message } from "@/lib/types";

interface Live {
  /** null when re-attached to a running turn: the user message is already part of the saved history */
  user: string | null;
  text: string;
  thinking: string;
  step: string | null;
}

const EXAMPLES = ["چطور Nginx را ریستارت کنم؟", "آخرین خطای کانتینر X چیست؟", "چرا آخرین بیلد شکست خورد؟"];

export function ChatView({ conversationId, mode = "support" }: { conversationId: string | null; mode?: "support" | "teach" }) {
  const qc = useQueryClient();
  const status = useSystemStatus();
  const router = useRouter();
  const [live, setLive] = useState<Live | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [draft, setDraft] = useState("");
  const [submitted, setSubmitted] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  const detail = useQuery({
    queryKey: ["conversation", conversationId],
    queryFn: () => api.get<ConversationDetail>(`/chat/conversations/${conversationId}`),
    enabled: !!conversationId,
    refetchOnMount: "always",
    // the session memory summary is refreshed by the backend a few seconds after each answer
    refetchInterval: (q) => (q.state.data?.memory?.updating ? 3000 : false),
  });

  const send = useCallback(
    async (id: string, content: string, refresh = false) => {
      setError(null);
      setLive({ user: content, text: "", thinking: "", step: null });
      try {
        await streamMessage(
          id,
          content,
          {
          onStatus: (step) => setLive((l) => (l ? { ...l, step } : l)),
          onThinking: (t) => setLive((l) => (l ? { ...l, thinking: l.thinking + t } : l)),
          onToken: (t) => setLive((l) => (l ? { ...l, text: l.text + t } : l)),
          },
          refresh,
        );
      } catch (e) {
        setError(e);
      } finally {
        await Promise.all([qc.invalidateQueries({ queryKey: ["conversation", id] }), qc.invalidateQueries({ queryKey: ["conversations"] })]);
        setLive(null);
      }
    },
    [qc],
  );

  // The user left this page while an answer was being generated and came back: re-attach and show the progress again.
  const liveRef = useRef<Live | null>(null);
  liveRef.current = live;
  const running = !!detail.data?.active;
  useEffect(() => {
    if (!conversationId || !running || liveRef.current) return;
    const ctrl = new AbortController();
    setLive({ user: null, text: "", thinking: "", step: null });
    attachStream(
      conversationId,
      {
        // the saved history may be stale (fetched before the question was sent): show the question unless it is already there
        onUserMessage: (m) => {
          const known = qc.getQueryData<ConversationDetail>(["conversation", conversationId])?.messages.some((x) => x.id === m.id);
          if (!known) setLive((l) => (l ? { ...l, user: m.content } : l));
        },
        onStatus: (step) => setLive((l) => (l ? { ...l, step } : l)),
        onThinking: (t) => setLive((l) => (l ? { ...l, thinking: l.thinking + t } : l)),
        onToken: (t) => setLive((l) => (l ? { ...l, text: l.text + t } : l)),
      },
      ctrl.signal,
    )
      .catch((e) => {
        if (!ctrl.signal.aborted) setError(e);
      })
      .finally(async () => {
        if (ctrl.signal.aborted) return;
        await Promise.all([qc.invalidateQueries({ queryKey: ["conversation", conversationId] }), qc.invalidateQueries({ queryKey: ["conversations"] })]);
        setLive(null);
      });
    return () => {
      ctrl.abort();
      liveRef.current = null; // lets a re-run (e.g. React strict mode) attach again
    };
  }, [conversationId, running, qc]);

  // First message of a brand-new chat: conversation was created on /chat, stream starts here after navigation.
  useEffect(() => {
    if (!conversationId) return;
    const first = takePendingMessage(conversationId);
    if (first) void send(conversationId, first);
  }, [conversationId, send]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [detail.data?.messages.length, live?.text, live?.user]);

  const teach = (detail.data?.conversation.mode ?? mode) === "teach";
  const submitLesson = useMutation({
    mutationFn: () => api.post<{ title: string }>(`/chat/conversations/${conversationId}/lessons`),
    onSuccess: async (l) => {
      setSubmitted(l.title);
      await Promise.all([qc.invalidateQueries({ queryKey: ["lessons"] }), qc.invalidateQueries({ queryKey: ["conversation", conversationId] })]);
    },
  });

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
    if (!content || live || status.data?.indexing) return;
    setDraft("");
    if (!conversationId) {
      try {
        const c = await api.post<Conversation>("/chat/conversations", { mode: teach ? "teach" : "support" });
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
  const lastUserContent = [...messages].reverse().find((m) => m.role === "user")?.content;
  const lastAssistantId = [...messages].reverse().find((m) => m.role === "assistant")?.id;
  const empty = !messages.length && !live;

  return (
    <div className="flex h-full flex-col">
      <div className="min-h-0 flex-1 overflow-y-auto">
        <div className="mx-auto max-w-3xl space-y-5 px-4 py-6">
          {empty ? (
            <div className="space-y-4 pt-16 text-center">
              <h2 className="text-2xl font-bold">{teach ? "به دستیار چیزی یاد بدهید" : "چه مشکلی دارید؟"}</h2>
              <p className="text-sm text-muted-foreground">
                {teach
                  ? "یک روش، قانون یا نکته‌ی مربوط به زیرساخت تیم را توضیح دهید. دستیار برداشت خود را بازگو می‌کند و سؤال می‌پرسد؛ سپس آن را برای تأیید ادمین بفرستید."
                  : "سؤال خود را بپرسید یا خطای build، deployment یا کانتینر را مستقیماً اینجا بچسبانید. ابتدا مستندات تأییدشده‌ی تیم بررسی می‌شود."}
              </p>
              <div className="flex flex-wrap justify-center gap-2">
                {(teach ? [] : EXAMPLES).map((ex) => (
                  <button key={ex} type="button" onClick={() => setDraft(ex)} className="rounded-full border border-border bg-card px-3 py-1.5 text-sm hover:bg-muted">
                    {ex}
                  </button>
                ))}
              </div>
            </div>
          ) : null}

          {detail.isLoading && conversationId ? <Spinner className="mx-auto" /> : null}
          {detail.error ? <ErrorBanner error={detail.error} /> : null}

          {!teach && detail.data?.memory ? <MemoryPanel memory={detail.data.memory} /> : null}

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
              {m.id === lastAssistantId && !live && !m.meta.kind && lastUserContent && conversationId ? (
                <div className="ps-11">
                  <Button variant="ghost" size="sm" onClick={() => void send(conversationId, lastUserContent, true)} title="کش را نادیده می‌گیرد و دوباره در وب جستجو می‌کند">
                    <RefreshCw className="h-3.5 w-3.5" /> جستجوی دوباره
                  </Button>
                </div>
              ) : null}
              {m.meta.feedback === "confirmed" ? <p className="ps-11 text-xs text-success">✓ شما این راه‌حل را تأیید کردید.</p> : null}
              {m.meta.feedback === "rejected" ? <p className="ps-11 text-xs text-danger">✗ شما این راه‌حل را رد کردید.</p> : null}
            </div>
          ))}

          {live ? (
            <>
              {live.user !== null ? <MessageBubble message={{ role: "user", content: live.user, citations: [], meta: {} }} /> : null}
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
          {teach ? (
            <div className="space-y-2 rounded-md border border-primary/30 bg-primary/5 p-3 text-sm">
              <div className="flex items-center gap-2 font-medium">
                <GraduationCap className="h-4 w-4 text-primary" /> حالت آموزش
              </div>
              <p className="text-muted-foreground">
                هر چه یاد می‌دهید تا زمانی که ادمین آن را تأیید نکند فعال نمی‌شود. وقتی از برداشت دستیار راضی بودید، آن را ارسال کنید.
              </p>
              {submitted ? (
                <p className="text-success" role="status">
                  «{submitted}» برای تأیید ادمین ارسال شد. می‌توانید در همین گفتگو مورد بعدی را آموزش دهید.
                </p>
              ) : null}
              <ErrorBanner error={submitLesson.error} />
              <Button size="sm" disabled={!conversationId || !messages.some((m) => m.role === "user") || !!live || submitLesson.isPending} onClick={() => { setSubmitted(null); submitLesson.mutate(); }}>
                {submitLesson.isPending ? <Spinner /> : <Send className="h-4 w-4 rtl:-scale-x-100" />} ارسال برای تأیید ادمین
              </Button>
            </div>
          ) : null}
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
            trailing={<ContextUsage messages={messages} contextWindow={status.data?.context_window} />}
            lockedReason={status.data?.indexing ? "مستندات در حال ایندکس شدن است؛ چت پس از پایان ایندکس فعال می‌شود…" : undefined}
            placeholder={teach ? "آنچه دستیار باید یاد بگیرد را بنویسید…  (Enter ارسال · Shift+Enter خط جدید)" : phase === "awaiting_error" ? "خطای جدید یا خروجی دستور را بچسبانید…" : "سؤال یا خطا را بنویسید…  (Enter ارسال · Shift+Enter خط جدید)"}
          />
          <p className="text-center text-[11px] text-muted-foreground">
            اسرار و توکن‌ها پیش از ذخیره و ارسال به مدل به‌صورت خودکار حذف می‌شوند. دستیار فقط‌خواندنی است و هیچ دستوری اجرا نمی‌کند.
          </p>
        </div>
      </div>
    </div>
  );
}
