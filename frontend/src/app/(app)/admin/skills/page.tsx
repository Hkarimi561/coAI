"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Pencil, Plus, Sparkles, Trash2 } from "lucide-react";
import { useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Dialog, DialogClose, DialogContent } from "@/components/ui/dialog";
import { Input, Textarea } from "@/components/ui/input";
import { Empty, ErrorBanner, Spinner } from "@/components/ui/misc";
import { Switch } from "@/components/ui/switch";
import { api } from "@/lib/api";
import type { SkillRow } from "@/lib/types";

interface Draft {
  id?: string;
  name: string;
  description: string;
  instructions: string;
  enabled: boolean;
}

const TEMPLATE: Draft = {
  name: "",
  description: "وقتی کاربر درباره‌ی ... می‌پرسد از این مهارت استفاده کن.",
  instructions: "## مراحل\n1. ...\n2. ...\n\n## نکات\n- ...",
  enabled: true,
};

export default function SkillsPage() {
  const qc = useQueryClient();
  const [draft, setDraft] = useState<Draft | null>(null);
  const [toDelete, setToDelete] = useState<SkillRow | null>(null);

  const skills = useQuery({ queryKey: ["admin-skills"], queryFn: () => api.get<SkillRow[]>("/admin/skills") });
  const refresh = () => qc.invalidateQueries({ queryKey: ["admin-skills"] });

  const save = useMutation({
    mutationFn: (d: Draft) => {
      const body = { name: d.name, description: d.description, instructions: d.instructions, enabled: d.enabled };
      return d.id ? api.put<SkillRow>(`/admin/skills/${d.id}`, body) : api.post<SkillRow>("/admin/skills", body);
    },
    onSuccess: () => {
      setDraft(null);
      void refresh();
    },
  });
  const toggle = useMutation({
    mutationFn: (s: SkillRow) => api.put<SkillRow>(`/admin/skills/${s.id}`, { name: s.name, description: s.description, instructions: s.instructions, enabled: !s.enabled }),
    onSuccess: () => void refresh(),
  });
  const remove = useMutation({
    mutationFn: (id: string) => api.del(`/admin/skills/${id}`),
    onSuccess: () => {
      setToDelete(null);
      void refresh();
    },
  });

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-2">
        <h1 className="me-auto text-lg font-bold">مهارت‌ها (Skills)</h1>
        <Button onClick={() => setDraft(TEMPLATE)}>
          <Plus className="h-4 w-4" /> مهارت جدید
        </Button>
      </div>
      <p className="text-sm text-muted-foreground">
        هر مهارت یک راهنمای نوشته‌ی ادمین است. دستیار با مقایسه‌ی «توضیح» مهارت با سؤال کاربر، مهارت‌های مرتبط را خودکار در پاسخ‌دهی به کار می‌گیرد.
        توضیح را مثل «چه زمانی استفاده شود» بنویسید؛ دستورالعمل می‌تواند به ابزارهای MCP فعال اشاره کند.
      </p>

      <ErrorBanner error={skills.error ?? toggle.error ?? remove.error} />
      {skills.isLoading ? <Spinner className="mx-auto" /> : null}
      {skills.data?.length === 0 ? <Empty>هنوز مهارتی تعریف نشده است.</Empty> : null}

      {skills.data?.map((s) => (
        <Card key={s.id} className="flex flex-wrap items-start gap-3 p-4">
          <Sparkles className="mt-1 h-4 w-4 shrink-0 text-primary" />
          <div className="min-w-0 flex-1 space-y-1">
            <div className="flex flex-wrap items-center gap-2">
              <span className="font-semibold" dir="auto">
                {s.name}
              </span>
              {!s.enabled ? <Badge tone="neutral">غیرفعال</Badge> : null}
            </div>
            <p className="text-sm text-muted-foreground" dir="auto">
              {s.description}
            </p>
          </div>
          <Switch checked={s.enabled} label={`فعال بودن ${s.name}`} disabled={toggle.isPending} onChange={() => toggle.mutate(s)} />
          <Button size="icon" variant="ghost" aria-label="ویرایش" onClick={() => setDraft({ id: s.id, name: s.name, description: s.description, instructions: s.instructions, enabled: s.enabled })}>
            <Pencil className="h-4 w-4" />
          </Button>
          <Button size="icon" variant="ghost" aria-label="حذف" onClick={() => setToDelete(s)}>
            <Trash2 className="h-4 w-4 text-danger" />
          </Button>
        </Card>
      ))}

      <Dialog open={!!draft} onOpenChange={(o) => !o && setDraft(null)}>
        <DialogContent title={draft?.id ? "ویرایش مهارت" : "مهارت جدید"} description="پس از ذخیره، مهارت برای تطبیق خودکار با سؤال‌ها ایندکس می‌شود.">
          {draft ? (
            <form
              className="space-y-3"
              onSubmit={(e) => {
                e.preventDefault();
                save.mutate(draft);
              }}
            >
              <label className="block space-y-1 text-sm">
                <span>نام</span>
                <Input required minLength={2} dir="auto" value={draft.name} onChange={(e) => setDraft({ ...draft, name: e.target.value })} />
              </label>
              <label className="block space-y-1 text-sm">
                <span>توضیح (چه زمانی استفاده شود؟)</span>
                <Textarea required minLength={10} rows={2} dir="auto" value={draft.description} onChange={(e) => setDraft({ ...draft, description: e.target.value })} />
              </label>
              <label className="block space-y-1 text-sm">
                <span>دستورالعمل (Markdown)</span>
                <Textarea required minLength={10} rows={10} dir="auto" value={draft.instructions} onChange={(e) => setDraft({ ...draft, instructions: e.target.value })} />
              </label>
              <label className="flex items-center gap-2 text-sm">
                <Switch checked={draft.enabled} label="فعال" onChange={(v) => setDraft({ ...draft, enabled: v })} /> فعال
              </label>
              <ErrorBanner error={save.error} />
              <div className="flex gap-2">
                <Button type="submit" disabled={save.isPending}>
                  {save.isPending ? <Spinner /> : null} ذخیره
                </Button>
                <DialogClose asChild>
                  <Button type="button" variant="outline">
                    انصراف
                  </Button>
                </DialogClose>
              </div>
            </form>
          ) : null}
        </DialogContent>
      </Dialog>

      <Dialog open={!!toDelete} onOpenChange={(o) => !o && setToDelete(null)}>
        <DialogContent title="حذف مهارت" description="این مهارت دیگر در پاسخ‌ها استفاده نمی‌شود.">
          <p className="mb-4 text-sm" dir="auto">
            {toDelete?.name}
          </p>
          <div className="flex gap-2">
            <Button variant="danger" disabled={remove.isPending} onClick={() => toDelete && remove.mutate(toDelete.id)}>
              {remove.isPending ? <Spinner /> : null} حذف
            </Button>
            <DialogClose asChild>
              <Button variant="outline">انصراف</Button>
            </DialogClose>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
