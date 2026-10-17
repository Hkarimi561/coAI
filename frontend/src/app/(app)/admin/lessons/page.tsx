"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ExternalLink } from "lucide-react";
import Link from "next/link";
import { useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Dialog, DialogContent } from "@/components/ui/dialog";
import { Input, Select, Textarea } from "@/components/ui/input";
import { Empty, ErrorBanner, Pager, Spinner } from "@/components/ui/misc";
import { api } from "@/lib/api";
import { LESSON_LABEL, LESSON_TONE } from "@/lib/labels";
import type { Lesson, LessonStatus, Paged } from "@/lib/types";
import { formatDateTime, formatNumber } from "@/lib/utils";
import { useT } from "@/lib/i18n";

type LessonPage = Paged<Lesson> & { pending: number };

export default function AdminLessonsPage() {
  const t = useT();
  const qc = useQueryClient();
  const [status, setStatus] = useState<LessonStatus | "all">("pending");
  const [page, setPage] = useState(1);
  const [open, setOpen] = useState<Lesson | null>(null);
  const [form, setForm] = useState({ title: "", applies_when: "", instruction: "", note: "" });

  const list = useQuery({
    queryKey: ["admin-lessons", status, page],
    queryFn: () => api.get<LessonPage>(`/admin/lessons?status=${status}&page=${page}`),
    placeholderData: (prev) => prev,
  });
  const done = () => {
    setOpen(null);
    void qc.invalidateQueries({ queryKey: ["admin-lessons"] });
  };
  const approve = useMutation({ mutationFn: (id: string) => api.post(`/admin/lessons/${id}/approve`, form), onSuccess: done });
  const reject = useMutation({ mutationFn: (id: string) => api.post(`/admin/lessons/${id}/reject`, form), onSuccess: done });

  function review(l: Lesson) {
    setForm({ title: l.title, applies_when: l.applies_when, instruction: l.instruction, note: l.review_note });
    setOpen(l);
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-3">
        <h1 className="me-auto text-lg font-bold">
          {t("آموزش‌های کاربران")} {list.data ? <Badge tone="warning">{formatNumber(list.data.pending)} {t("در انتظار تأیید")}</Badge> : null}
        </h1>
        <Select value={status} onChange={(e) => { setStatus(e.target.value as LessonStatus | "all"); setPage(1); }} className="w-48" aria-label={t("وضعیت")}>
          <option value="pending">{t("در انتظار تأیید")}</option>
          <option value="approved">{t("تأییدشده")}</option>
          <option value="rejected">{t("ردشده")}</option>
          <option value="all">{t("همه")}</option>
        </Select>
      </div>
      <p className="text-sm text-muted-foreground">
        {t("هر چیزی که کاربران در «گفتگوی آموزشی» به دستیار یاد می‌دهند تا زمانی که شما تأیید نکنید فعال نمی‌شود. پس از تأیید، آموزش در جستجوی مستندات استفاده می‌شود.")}
      </p>
      <ErrorBanner error={list.error} />
      {list.isLoading ? <Spinner className="mx-auto" /> : null}
      {list.data && list.data.items.length === 0 ? <Empty>{t("موردی وجود ندارد.")}</Empty> : null}
      {list.data && list.data.items.length > 0 ? (
        <Card className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-muted text-xs text-muted-foreground">
              <tr>
                <th className="p-3 text-start">{t("عنوان")}</th>
                <th className="p-3 text-start">{t("کاربر")}</th>
                <th className="p-3 text-start">{t("وضعیت")}</th>
                <th className="p-3 text-start">{t("ارسال")}</th>
                <th className="p-3" />
              </tr>
            </thead>
            <tbody>
              {list.data.items.map((l) => (
                <tr key={l.id} className="border-t border-border">
                  <td className="max-w-md p-3 font-medium" dir="auto">{l.title}</td>
                  <td className="p-3" dir="ltr">{l.user?.email}</td>
                  <td className="p-3"><Badge tone={LESSON_TONE[l.status]}>{t(LESSON_LABEL[l.status])}</Badge></td>
                  <td className="p-3 text-muted-foreground">{formatDateTime(l.created_at)}</td>
                  <td className="p-3 text-end">
                    <Button size="sm" variant={l.status === "pending" ? "default" : "outline"} onClick={() => review(l)}>
                      {l.status === "pending" ? t("بررسی") : t("مشاهده")}
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      ) : null}
      {list.data ? <Pager page={list.data.page} pageSize={list.data.page_size} total={list.data.total} onPage={setPage} /> : null}

      <Dialog open={!!open} onOpenChange={(o) => !o && setOpen(null)}>
        <DialogContent title={t("بررسی آموزش")} description={t("می‌توانید متن را پیش از تأیید ویرایش کنید.")}>
          {open ? (
            <div className="space-y-3 text-sm">
              <label className="block space-y-1">
                <span className="font-medium">{t("عنوان")}</span>
                <Input value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} dir="auto" />
              </label>
              <label className="block space-y-1">
                <span className="font-medium">{t("چه زمانی استفاده شود؟")}</span>
                <Textarea rows={2} value={form.applies_when} onChange={(e) => setForm({ ...form, applies_when: e.target.value })} dir="auto" />
              </label>
              <label className="block space-y-1">
                <span className="font-medium">{t("چه کاری انجام شود؟")}</span>
                <Textarea rows={10} value={form.instruction} onChange={(e) => setForm({ ...form, instruction: e.target.value })} dir="auto" className="font-mono text-[0.85rem]" />
              </label>
              <label className="block space-y-1">
                <span className="font-medium">{t("یادداشت برای کاربر (اختیاری)")}</span>
                <Input value={form.note} onChange={(e) => setForm({ ...form, note: e.target.value })} dir="auto" />
              </label>
              <Link href={`/admin/conversations/${open.conversation_id}`} className="inline-flex items-center gap-1 text-primary underline">
                <ExternalLink className="h-3.5 w-3.5" /> {t("مشاهده‌ی گفتگوی آموزشی کامل")}
              </Link>
              <ErrorBanner error={approve.error ?? reject.error} />
              <div className="flex flex-wrap gap-2">
                <Button variant="success" disabled={approve.isPending || reject.isPending} onClick={() => approve.mutate(open.id)}>
                  {approve.isPending ? <Spinner /> : null} {open.status === "approved" ? t("ذخیره‌ی تغییرات") : t("تأیید و فعال‌سازی")}
                </Button>
                {open.status !== "rejected" ? (
                  <Button variant="dangerOutline" disabled={approve.isPending || reject.isPending} onClick={() => reject.mutate(open.id)}>
                    {open.status === "approved" ? t("لغو فعال‌سازی") : t("رد")}
                  </Button>
                ) : null}
              </div>
            </div>
          ) : null}
        </DialogContent>
      </Dialog>
    </div>
  );
}
