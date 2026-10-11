"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { FilePlus2, Pencil, RefreshCw, Trash2, Upload } from "lucide-react";
import { useRef, useState } from "react";

import { DocumentEditor, type EditorTarget } from "@/components/admin/document-editor";
import { SystemStatusBar } from "@/components/system-status";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Dialog, DialogClose, DialogContent } from "@/components/ui/dialog";
import { Empty, ErrorBanner, Spinner } from "@/components/ui/misc";
import { api } from "@/lib/api";
import type { DocumentFull, DocumentRow, ReindexReport } from "@/lib/types";
import { formatDateTime, formatNumber } from "@/lib/utils";

const NEW_TEMPLATE = `# عنوان رانبوک

## Symptoms

## Root Cause

## Resolution Steps

\`\`\`bash
# دستورها را اینجا بنویسید
\`\`\`

## Verification
`;

export default function DocumentsPage() {
  const qc = useQueryClient();
  const fileInput = useRef<HTMLInputElement>(null);
  const [editor, setEditor] = useState<EditorTarget | null>(null);
  const [toDelete, setToDelete] = useState<DocumentRow | null>(null);
  const [report, setReport] = useState<string | null>(null);

  const docs = useQuery({ queryKey: ["admin-documents"], queryFn: () => api.get<DocumentRow[]>("/admin/documents") });
  const refresh = () => qc.invalidateQueries({ queryKey: ["admin-documents"] });

  const reindex = useMutation({
    mutationFn: (force: boolean) => api.post<ReindexReport>(`/admin/documents/reindex?force=${force}`),
    onSuccess: (r) => {
      setReport(
        `ایندکس‌شده: ${formatNumber(r.indexed.length)} · بدون تغییر: ${formatNumber(r.skipped)} · حذف‌شده: ${formatNumber(r.removed.length)} · خطا: ${formatNumber(r.errors.length)}` +
          (r.errors.length ? `\n${r.errors.map((e) => `${e.path}: ${e.error}`).join("\n")}` : ""),
      );
      void refresh();
    },
  });
  const upload = useMutation({
    mutationFn: (files: File[]) => {
      const form = new FormData();
      files.forEach((f) => form.append("files", f));
      return api.upload<{ filename: string; ok: boolean; chunks?: number; error?: string }[]>("/admin/documents/upload", form);
    },
    onSuccess: (rows) => {
      setReport(rows.map((r) => (r.ok ? `✓ ${r.filename} (${r.chunks} chunk)` : `✗ ${r.filename}: ${r.error}`)).join("\n"));
      void refresh();
    },
  });
  const remove = useMutation({
    mutationFn: (id: string) => api.del(`/admin/documents/${id}`),
    onSuccess: () => {
      setToDelete(null);
      void refresh();
    },
  });
  const open = useMutation({
    mutationFn: (id: string) => api.get<DocumentFull>(`/admin/documents/${id}`),
    onSuccess: (d) => setEditor({ docId: d.id, path: d.path, content: d.content }),
  });

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-2">
        <h1 className="me-auto text-lg font-bold">مخزن مستندات تأییدشده</h1>
        <Button variant="outline" onClick={() => setEditor({ path: "runbooks/new-runbook.md", content: NEW_TEMPLATE })}>
          <FilePlus2 className="h-4 w-4" /> سند جدید
        </Button>
        <input
          ref={fileInput}
          type="file"
          accept=".md,text/markdown"
          multiple
          hidden
          onChange={(e) => {
            // copy first: resetting the input empties the live FileList, which would send an empty form
            const picked = Array.from(e.target.files ?? []);
            e.target.value = "";
            if (picked.length) upload.mutate(picked);
          }}
        />
        <Button variant="outline" onClick={() => fileInput.current?.click()} disabled={upload.isPending}>
          {upload.isPending ? <Spinner /> : <Upload className="h-4 w-4" />} بارگذاری Markdown
        </Button>
        <Button variant="outline" onClick={() => reindex.mutate(false)} disabled={reindex.isPending}>
          {reindex.isPending ? <Spinner /> : <RefreshCw className="h-4 w-4" />} ایندکس تغییرات
        </Button>
        <Button variant="ghost" onClick={() => reindex.mutate(true)} disabled={reindex.isPending} title="همه‌ی فایل‌ها را دوباره ایندکس می‌کند">
          ایندکس کامل
        </Button>
      </div>
      <p className="text-sm text-muted-foreground">
        فقط فایل‌های جدید یا تغییرکرده دوباره ایندکس می‌شوند (بر اساس هش محتوا). فایل‌های حذف‌شده از دیسک از Qdrant هم پاک می‌شوند.
      </p>

      <SystemStatusBar />
      <ErrorBanner error={docs.error ?? reindex.error ?? upload.error ?? open.error ?? remove.error} />
      {report ? <pre className="whitespace-pre-wrap rounded-md bg-muted p-3 text-xs text-left">{report}</pre> : null}

      {editor ? (
        <DocumentEditor
          key={editor.docId ?? editor.path}
          target={editor}
          onCancel={() => setEditor(null)}
          onDone={() => {
            setEditor(null);
            void refresh();
          }}
        />
      ) : null}

      {docs.isLoading ? <Spinner className="mx-auto" /> : null}
      {docs.data && docs.data.length === 0 ? <Empty>سندی ایندکس نشده است. فایل‌ها را در پوشه‌ی docs بگذارید و «ایندکس تغییرات» را بزنید.</Empty> : null}
      {docs.data && docs.data.length > 0 ? (
        <Card className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-muted text-xs text-muted-foreground">
              <tr>
                <th className="p-3 text-start">سند</th>
                <th className="p-3 text-start">منبع</th>
                <th className="p-3 text-start">Chunk</th>
                <th className="p-3 text-start">وضعیت</th>
                <th className="p-3 text-start">آخرین ایندکس</th>
                <th className="p-3" />
              </tr>
            </thead>
            <tbody>
              {docs.data.map((d) => (
                <tr key={d.id} className="border-t border-border">
                  <td className="p-3">
                    <div className="font-medium" dir="auto">
                      {d.title}
                    </div>
                    <code className="ltr text-xs text-muted-foreground">{d.path}</code>
                  </td>
                  <td className="p-3">
                    <Badge tone={d.source === "promoted" ? "success" : "neutral"}>{d.source}</Badge>
                  </td>
                  <td className="p-3">{formatNumber(d.chunk_count)}</td>
                  <td className="p-3">
                    {d.status === "indexed" ? (
                      <Badge tone="success">ایندکس</Badge>
                    ) : (
                      <div className="max-w-xs space-y-1">
                        <Badge tone="danger">خطا در ایندکس</Badge>
                        <p className="ltr break-words text-[11px] text-danger">{d.error}</p>
                      </div>
                    )}
                  </td>
                  <td className="p-3 text-muted-foreground">{formatDateTime(d.indexed_at)}</td>
                  <td className="p-3">
                    <div className="flex justify-end gap-1">
                      <Button size="icon" variant="ghost" aria-label="ویرایش" onClick={() => open.mutate(d.id)}>
                        <Pencil className="h-4 w-4" />
                      </Button>
                      <Button size="icon" variant="ghost" aria-label="حذف" onClick={() => setToDelete(d)}>
                        <Trash2 className="h-4 w-4 text-danger" />
                      </Button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      ) : null}

      <Dialog open={!!toDelete} onOpenChange={(o) => !o && setToDelete(null)}>
        <DialogContent title="حذف سند" description="فایل از مخزن مستندات و بردارهای آن از Qdrant حذف می‌شود. این کار قابل بازگشت نیست.">
          <p className="mb-4 text-sm" dir="ltr">
            {toDelete?.path}
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
