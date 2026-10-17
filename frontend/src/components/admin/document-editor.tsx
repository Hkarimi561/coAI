"use client";

import { useMutation } from "@tanstack/react-query";
import { Save } from "lucide-react";
import { useState } from "react";

import { Markdown } from "@/components/markdown";
import { Button } from "@/components/ui/button";
import { Input, Textarea } from "@/components/ui/input";
import { ErrorBanner, Spinner } from "@/components/ui/misc";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { api } from "@/lib/api";
import type { DocumentRow } from "@/lib/types";
import { useT } from "@/lib/i18n";

export interface EditorTarget {
  /** existing document id (edit) — absent for new / promoted documents */
  docId?: string;
  path: string;
  content: string;
  conversationId?: string;
  solutionId?: string | null;
  note?: string;
}

function stripFrontMatter(md: string): string {
  return md.startsWith("---") ? md.replace(/^---\n[\s\S]*?\n---\n?/, "") : md;
}

/** Edit / preview / approve-and-publish a Markdown document. Publishing writes it to the docs store and indexes it in Qdrant. */
export function DocumentEditor({ target, onDone, onCancel }: { target: EditorTarget; onDone: (doc: DocumentRow) => void; onCancel: () => void }) {
  const t = useT();
  const [path, setPath] = useState(target.path);
  const [content, setContent] = useState(target.content);
  const editing = !!target.docId;

  const publish = useMutation({
    mutationFn: () =>
      editing
        ? api.put<DocumentRow>(`/admin/documents/${target.docId}`, { content })
        : api.post<DocumentRow>("/admin/documents", {
            path,
            content,
            conversation_id: target.conversationId ?? null,
            solution_id: target.solutionId ?? null,
          }),
    onSuccess: onDone,
  });

  return (
    <div className="space-y-3 rounded-lg border border-primary/30 bg-card p-4">
      {target.note ? <p className="rounded-md bg-primary/5 p-2 text-sm">{target.note}</p> : null}
      <label className="block space-y-1 text-sm">
        <span className="font-medium">{t("مسیر فایل در مخزن مستندات")}</span>
        <Input dir="ltr" value={path} onChange={(e) => setPath(e.target.value)} disabled={editing} placeholder="promoted/restart-nginx.md" />
      </label>

      <Tabs defaultValue="edit">
        <TabsList>
          <TabsTrigger value="edit">{t("ویرایش")}</TabsTrigger>
          <TabsTrigger value="preview">{t("پیش‌نمایش")}</TabsTrigger>
        </TabsList>
        <TabsContent value="edit">
          <Textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            dir="auto"
            rows={24}
            spellCheck={false}
            aria-label={t("محتوای Markdown")}
            className="font-mono text-[0.85rem]"
          />
        </TabsContent>
        <TabsContent value="preview">
          <div className="min-h-[24rem] rounded-md border border-border p-4">
            <Markdown content={stripFrontMatter(content)} />
          </div>
        </TabsContent>
      </Tabs>

      <ErrorBanner error={publish.error} />
      <div className="flex gap-2">
        <Button onClick={() => publish.mutate()} disabled={publish.isPending || !content.trim() || !path.trim()}>
          {publish.isPending ? <Spinner /> : <Save className="h-4 w-4" />} {editing ? t("ذخیره و ایندکس مجدد") : t("تأیید و انتشار در پایگاه دانش")}
        </Button>
        <Button variant="outline" onClick={onCancel} disabled={publish.isPending}>
          {t("انصراف")}
        </Button>
      </div>
    </div>
  );
}
