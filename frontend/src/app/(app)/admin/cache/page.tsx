"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Eye, Search, Trash2 } from "lucide-react";
import { useEffect, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Dialog, DialogClose, DialogContent } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Empty, ErrorBanner, Pager, Spinner } from "@/components/ui/misc";
import { api, qs } from "@/lib/api";
import type { CacheDetail, CacheRow, Paged } from "@/lib/types";
import { formatDateTime, formatNumber } from "@/lib/utils";
import { useT } from "@/lib/i18n";

export default function CachePage() {
  const t = useT();
  const qc = useQueryClient();
  const [page, setPage] = useState(1);
  const [q, setQ] = useState("");
  const [debounced, setDebounced] = useState("");
  const [showInvalid, setShowInvalid] = useState(false);
  const [viewId, setViewId] = useState<string | null>(null);
  const [toInvalidate, setToInvalidate] = useState<CacheRow | null>(null);

  useEffect(() => {
    const t = setTimeout(() => {
      setDebounced(q);
      setPage(1);
    }, 350);
    return () => clearTimeout(t);
  }, [q]);

  const list = useQuery({
    queryKey: ["admin-cache", page, debounced, showInvalid],
    queryFn: () => api.get<Paged<CacheRow>>(`/admin/cache${qs({ page, page_size: 20, q: debounced, include_invalidated: showInvalid })}`),
    placeholderData: (prev) => prev,
  });
  const detail = useQuery({ queryKey: ["admin-cache-entry", viewId], queryFn: () => api.get<CacheDetail>(`/admin/cache/${viewId}`), enabled: !!viewId });
  const invalidate = useMutation({
    mutationFn: (id: string) => api.post(`/admin/cache/${id}/invalidate`),
    onSuccess: () => {
      setToInvalidate(null);
      void qc.invalidateQueries({ queryKey: ["admin-cache"] });
    },
  });

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-3">
        <h1 className="me-auto text-lg font-bold">{t("کش جستجوی وب")}</h1>
        <label className="flex items-center gap-2 text-sm">
          <input type="checkbox" checked={showInvalid} onChange={(e) => setShowInvalid(e.target.checked)} /> {t("نمایش ابطال‌شده‌ها")}
        </label>
        <div className="relative">
          <Search className="pointer-events-none absolute start-3 top-3 h-4 w-4 text-muted-foreground" />
          <Input value={q} onChange={(e) => setQ(e.target.value)} placeholder={t("جستجو در پرس‌وجو یا امضای خطا…")} className="w-72 ps-9" aria-label={t("جستجو")} />
        </div>
      </div>
      <p className="text-sm text-muted-foreground">
        {t("هر مشکل تکراری فقط یک‌بار در وب جستجو می‌شود (قفل single-flight). ابطال یک ورودی باعث می‌شود دفعه‌ی بعد دوباره جستجو شود.")}
      </p>

      <ErrorBanner error={list.error ?? invalidate.error} />
      {list.isLoading ? <Spinner className="mx-auto" /> : null}
      {list.data && list.data.items.length === 0 ? <Empty>{t("ورودی‌ای در کش وجود ندارد.")}</Empty> : null}
      {list.data && list.data.items.length > 0 ? (
        <Card className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-muted text-xs text-muted-foreground">
              <tr>
                <th className="p-3 text-start">{t("پرس‌وجو / امضای خطا")}</th>
                <th className="p-3 text-start">{t("نتایج")}</th>
                <th className="p-3 text-start">{t("استفاده")}</th>
                <th className="p-3 text-start">{t("ایجاد")}</th>
                <th className="p-3 text-start">{t("انقضا")}</th>
                <th className="p-3" />
              </tr>
            </thead>
            <tbody>
              {list.data.items.map((e) => (
                <tr key={e.id} className="border-t border-border">
                  <td className="max-w-lg p-3">
                    <code className="ltr block truncate text-xs" title={e.query_text}>
                      {e.query_text}
                    </code>
                    <code className="ltr block truncate text-[11px] text-muted-foreground" title={e.error_signature}>
                      {e.error_signature}
                    </code>
                  </td>
                  <td className="p-3">
                    {formatNumber(e.result_count)} <span className="text-xs text-muted-foreground">({e.provider})</span>
                  </td>
                  <td className="p-3">{formatNumber(e.hit_count)}</td>
                  <td className="p-3 text-muted-foreground">{formatDateTime(e.created_at)}</td>
                  <td className="p-3">
                    {e.invalidated_at ? <Badge tone="danger">{t("ابطال‌شده")}</Badge> : <span className="text-muted-foreground">{formatDateTime(e.expires_at)}</span>}
                  </td>
                  <td className="p-3">
                    <div className="flex justify-end gap-1">
                      <Button size="icon" variant="ghost" aria-label={t("مشاهده")} onClick={() => setViewId(e.id)}>
                        <Eye className="h-4 w-4" />
                      </Button>
                      {!e.invalidated_at ? (
                        <Button size="icon" variant="ghost" aria-label={t("ابطال")} onClick={() => setToInvalidate(e)}>
                          <Trash2 className="h-4 w-4 text-danger" />
                        </Button>
                      ) : null}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      ) : null}
      {list.data ? <Pager page={list.data.page} pageSize={list.data.page_size} total={list.data.total} onPage={setPage} /> : null}

      <Dialog open={!!viewId} onOpenChange={(o) => !o && setViewId(null)}>
        <DialogContent title={t("جزئیات ورودی کش")} className="max-w-3xl">
          {detail.isLoading ? <Spinner /> : null}
          {detail.data ? (
            <div className="space-y-3 text-sm">
              <code className="ltr block rounded bg-muted p-2 text-xs">{detail.data.query_text}</code>
              <ul className="space-y-2">
                {detail.data.results.map((r) => (
                  <li key={r.url} className="rounded border border-border p-2">
                    <a href={r.url} target="_blank" rel="noopener noreferrer nofollow" className="ltr block text-primary underline">
                      {r.title || r.url}
                    </a>
                    <p className="ltr mt-1 text-xs text-muted-foreground">{r.snippet}</p>
                  </li>
                ))}
              </ul>
              {detail.data.answer ? (
                <details>
                  <summary className="cursor-pointer text-muted-foreground">{t("پاسخ ذخیره‌شده")}</summary>
                  <pre className="mt-1 max-h-64 overflow-auto whitespace-pre-wrap rounded bg-muted p-2 text-xs" dir="auto">
                    {detail.data.answer}
                  </pre>
                </details>
              ) : null}
            </div>
          ) : null}
        </DialogContent>
      </Dialog>

      <Dialog open={!!toInvalidate} onOpenChange={(o) => !o && setToInvalidate(null)}>
        <DialogContent title={t("ابطال ورودی کش")} description={t("دفعه‌ی بعد که این مشکل پرسیده شود، جستجوی تازه‌ی وب انجام می‌شود.")}>
          <code className="ltr mb-4 block truncate text-xs">{toInvalidate?.query_text}</code>
          <div className="flex gap-2">
            <Button variant="danger" disabled={invalidate.isPending} onClick={() => toInvalidate && invalidate.mutate(toInvalidate.id)}>
              {invalidate.isPending ? <Spinner /> : null} {t("ابطال")}
            </Button>
            <DialogClose asChild>
              <Button variant="outline">{t("انصراف")}</Button>
            </DialogClose>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
