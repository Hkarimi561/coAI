"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowRight, FilePlus2 } from "lucide-react";
import Link from "next/link";
import { useState } from "react";

import { DocumentEditor, type EditorTarget } from "@/components/admin/document-editor";
import { CitationList } from "@/components/chat/citations";
import { MessageBubble } from "@/components/chat/message-bubble";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Select } from "@/components/ui/input";
import { Empty, ErrorBanner, Spinner } from "@/components/ui/misc";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { api } from "@/lib/api";
import { SOURCE_LABEL, STATUS_LABEL, STATUS_TONE, WEB_EVENT_LABEL } from "@/lib/labels";
import type { ConversationInspection, ConversationStatus, DraftResponse } from "@/lib/types";
import { formatDateTime, formatNumber } from "@/lib/utils";
import { useT } from "@/lib/i18n";

export default function InspectorPage({ params }: { params: { id: string } }) {
  const t = useT();
  const { id } = params;
  const qc = useQueryClient();
  const [editor, setEditor] = useState<EditorTarget | null>(null);
  const [published, setPublished] = useState<string | null>(null);

  const { data, isLoading, error } = useQuery({
    queryKey: ["admin-conversation", id],
    queryFn: () => api.get<ConversationInspection>(`/admin/conversations/${id}`),
  });
  const refresh = () => qc.invalidateQueries({ queryKey: ["admin-conversation", id] });

  const setStatus = useMutation({
    mutationFn: (status: ConversationStatus) => api.patch(`/admin/conversations/${id}/status`, { status }),
    onSuccess: refresh,
  });
  const reject = useMutation({ mutationFn: (sid: string) => api.post(`/admin/solutions/${sid}/reject`), onSuccess: refresh });
  const draft = useMutation({
    mutationFn: () => api.post<DraftResponse>(`/admin/conversations/${id}/promote/draft`),
    onSuccess: (d) =>
      setEditor({
        path: d.suggested_path,
        content: d.markdown,
        conversationId: id,
        solutionId: d.solution_id,
        note: d.generated_by_llm
          ? t("پیش‌نویس توسط مدل زبانی از روی گفتگو ساخته شد. پیش از انتشار، درستی دستورها و علت ریشه‌ای را بررسی کنید.")
          : t("مدل زبانی در دسترس نبود یا خروجی معتبر نداشت؛ قالب پایه ساخته شد. بخش‌ها را تکمیل کنید."),
      }),
  });

  if (isLoading) return <Spinner className="mx-auto mt-10 h-6 w-6" />;
  if (error || !data) return <ErrorBanner error={error} />;
  const c = data.conversation;
  const turnByMessage = (mid: string) => data.turns.find((t) => t.message_id === mid);

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-3">
        <Button asChild variant="ghost" size="sm">
          <Link href="/admin/conversations">
            <ArrowRight className="h-4 w-4" /> {t("بازگشت")}
          </Link>
        </Button>
        <h1 className="me-auto text-lg font-bold" dir="auto">
          {c.title || t("(بدون عنوان)")}
        </h1>
        <Badge tone={STATUS_TONE[c.status]}>{t(STATUS_LABEL[c.status])}</Badge>
        <Select value={c.status} onChange={(e) => setStatus.mutate(e.target.value as ConversationStatus)} className="w-44" aria-label={t("تغییر وضعیت")}>
          {(Object.keys(STATUS_LABEL) as ConversationStatus[]).map((s) => (
            <option key={s} value={s}>
              {t(STATUS_LABEL[s])}
            </option>
          ))}
        </Select>
        <Button onClick={() => draft.mutate()} disabled={draft.isPending}>
          {draft.isPending ? <Spinner /> : <FilePlus2 className="h-4 w-4" />} {t("ارتقا به مستندات")}
        </Button>
      </div>
      <p className="text-sm text-muted-foreground">
        {t("کاربر:")} <span dir="ltr">{data.user.email}</span> · {t("آخرین فعالیت:")} {formatDateTime(c.updated_at)}
      </p>

      <ErrorBanner error={setStatus.error ?? draft.error ?? reject.error} />
      {published ? (
        <div role="status" className="rounded-md border border-success/30 bg-success/10 p-3 text-sm text-success">
          {t("مستند در")} <code className="ltr">{published}</code> {t("منتشر و در Qdrant ایندکس شد؛ وضعیت گفتگو «حل‌شده» شد.")}
        </div>
      ) : null}
      {editor ? (
        <DocumentEditor
          target={editor}
          onCancel={() => setEditor(null)}
          onDone={(doc) => {
            setEditor(null);
            setPublished(doc.path);
            void refresh();
          }}
        />
      ) : null}

      <Tabs defaultValue="chat">
        <TabsList>
          <TabsTrigger value="chat">{t("گفتگو")}</TabsTrigger>
          <TabsTrigger value="tools">{t("ابزارها و جستجوها")} ({formatNumber(data.tool_calls.length)})</TabsTrigger>
          <TabsTrigger value="feedback">{t("بازخورد و راه‌حل‌ها")}</TabsTrigger>
        </TabsList>

        <TabsContent value="chat">
          <div className="space-y-4">
            {data.messages.map((m) => {
              const turn = turnByMessage(m.id);
              return (
                <div key={m.id} className="space-y-1.5">
                  <MessageBubble message={m} conversationId={id} />
                  {turn ? (
                    <div className="flex flex-wrap gap-1.5 pe-0 ps-11 text-xs">
                      <Badge>{t("منبع اصلی")}: {t(SOURCE_LABEL[turn.primary_source] ?? turn.primary_source)}</Badge>
                      <Badge>{t(WEB_EVENT_LABEL[turn.web_event] ?? turn.web_event)}</Badge>
                      {turn.signature_text ? (
                        <Badge className="ltr max-w-md truncate" title={turn.signature_text}>
                          sig: {turn.signature_text}
                        </Badge>
                      ) : null}
                    </div>
                  ) : null}
                </div>
              );
            })}
          </div>
        </TabsContent>

        <TabsContent value="tools">
          {data.tool_calls.length === 0 ? <Empty>{t("ابزاری فراخوانی نشده است.")}</Empty> : null}
          <div className="space-y-2">
            {data.tool_calls.map((call) => (
              <Card key={call.id}>
                <CardContent className="space-y-2 p-3">
                  <div className="flex flex-wrap items-center gap-2 text-sm">
                    <code className="ltr font-semibold">{call.tool}</code>
                    <Badge tone={call.status === "ok" ? "success" : call.status === "error" ? "danger" : "warning"}>{call.status}</Badge>
                    <span className="text-xs text-muted-foreground">{formatNumber(call.duration_ms)} ms · {formatDateTime(call.created_at)}</span>
                  </div>
                  <details>
                    <summary className="cursor-pointer text-xs text-muted-foreground">{t("ورودی / خروجی")}</summary>
                    <pre className="mt-1 max-h-72 overflow-auto rounded bg-muted p-2 text-xs">{JSON.stringify({ input: call.input, output: call.output }, null, 2)}</pre>
                  </details>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="feedback">
          <div className="grid gap-4 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>{t("بازخوردهای کاربر")}</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                {data.feedback.length === 0 ? <p className="text-sm text-muted-foreground">{t("بازخوردی ثبت نشده است.")}</p> : null}
                {data.feedback.map((f) => (
                  <div key={f.id} className="flex items-center gap-2 text-sm">
                    <Badge tone={f.outcome === "confirmed" ? "success" : "danger"}>{f.outcome === "confirmed" ? t("تأیید") : t("رد")}</Badge>
                    <span className="text-muted-foreground">{formatDateTime(f.created_at)}</span>
                    {f.note ? <span dir="auto">{f.note}</span> : null}
                  </div>
                ))}
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle>{t("راه‌حل‌های کاندید")}</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {data.solutions.length === 0 ? <p className="text-sm text-muted-foreground">{t("راه‌حلی تأیید نشده است.")}</p> : null}
                {data.solutions.map((s) => (
                  <div key={s.id} className="space-y-1.5 rounded-md border border-border p-2.5">
                    <div className="flex items-center gap-2">
                      <Badge tone={s.status === "promoted" ? "success" : s.status === "rejected" ? "danger" : "warning"}>{s.status}</Badge>
                      <span className="truncate text-sm font-medium" dir="auto">
                        {s.title}
                      </span>
                    </div>
                    {s.status === "candidate" ? (
                      <Button size="sm" variant="dangerOutline" onClick={() => reject.mutate(s.id)} disabled={reject.isPending}>
                        {t("رد راه‌حل (حذف از جستجوی معنایی)")}
                      </Button>
                    ) : null}
                  </div>
                ))}
              </CardContent>
            </Card>
          </div>
          {data.messages.some((m) => m.citations.length) ? (
            <Card className="mt-4">
              <CardHeader>
                <CardTitle>{t("منابع آخرین پاسخ")}</CardTitle>
              </CardHeader>
              <CardContent>
                <CitationList citations={[...data.messages].reverse().find((m) => m.citations.length)?.citations ?? []} />
              </CardContent>
            </Card>
          ) : null}
        </TabsContent>
      </Tabs>
    </div>
  );
}
