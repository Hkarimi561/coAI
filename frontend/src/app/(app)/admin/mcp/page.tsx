"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Plug, Plus, RefreshCw, Trash2 } from "lucide-react";
import { useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Dialog, DialogClose, DialogContent } from "@/components/ui/dialog";
import { Input, Select, Textarea } from "@/components/ui/input";
import { Empty, ErrorBanner, Spinner } from "@/components/ui/misc";
import { Switch } from "@/components/ui/switch";
import { api } from "@/lib/api";
import type { McpServerRow } from "@/lib/types";
import { formatDateTime, formatNumber } from "@/lib/utils";

function parseHeaders(text: string): Record<string, string> {
  const out: Record<string, string> = {};
  for (const line of text.split("\n")) {
    const i = line.indexOf(":");
    if (i > 0 && line.slice(i + 1).trim()) out[line.slice(0, i).trim()] = line.slice(i + 1).trim();
  }
  return out;
}

export default function McpPage() {
  const qc = useQueryClient();
  const [adding, setAdding] = useState(false);
  const [toDelete, setToDelete] = useState<McpServerRow | null>(null);
  const [form, setForm] = useState({ name: "", description: "", transport: "http", url: "", headers: "" });

  const servers = useQuery({ queryKey: ["admin-mcp"], queryFn: () => api.get<McpServerRow[]>("/admin/mcp") });
  const refresh = () => qc.invalidateQueries({ queryKey: ["admin-mcp"] });

  const create = useMutation({
    mutationFn: () => api.post<McpServerRow>("/admin/mcp", { name: form.name, description: form.description, transport: form.transport, url: form.url, headers: parseHeaders(form.headers) }),
    onSuccess: async (s) => {
      setAdding(false);
      setForm({ name: "", description: "", transport: "http", url: "", headers: "" });
      await refresh();
      sync.mutate(s.id); // discover the tools right away
    },
  });
  const sync = useMutation({ mutationFn: (id: string) => api.post<McpServerRow>(`/admin/mcp/${id}/sync`), onSettled: () => void refresh() });
  const toggle = useMutation({
    mutationFn: (v: { id: string; enabled: boolean }) => api.put<McpServerRow>(`/admin/mcp/${v.id}`, { enabled: v.enabled }),
    onSuccess: () => void refresh(),
  });
  const describe = useMutation({
    mutationFn: (v: { id: string; description: string }) => api.put<McpServerRow>(`/admin/mcp/${v.id}`, { description: v.description }),
    onSuccess: () => void refresh(),
  });
  const setTools = useMutation({
    mutationFn: (v: { id: string; tools: string[] }) => api.put<McpServerRow>(`/admin/mcp/${v.id}/tools`, { enabled_tools: v.tools }),
    onSuccess: () => void refresh(),
  });
  const remove = useMutation({
    mutationFn: (id: string) => api.del(`/admin/mcp/${id}`),
    onSuccess: () => {
      setToDelete(null);
      void refresh();
    },
  });

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-2">
        <h1 className="me-auto text-lg font-bold">سرورهای MCP</h1>
        <Button onClick={() => setAdding(true)}>
          <Plus className="h-4 w-4" /> سرور جدید
        </Button>
      </div>
      <p className="text-sm text-muted-foreground">
        دستیار فقط ابزارهایی را می‌تواند صدا بزند که شما اینجا فعال کنید. ابزارهای تازه کشف‌شده به‌صورت پیش‌فرض غیرفعال‌اند. فقط ابزارهای خواندنی (read-only) را فعال کنید؛
        هر فراخوانی در پاسخ نمایش داده و در گفتگوها ثبت می‌شود. نتیجه‌ی ابزارها «داده‌ی نامطمئن» تلقی می‌شود.
      </p>

      <ErrorBanner error={servers.error ?? create.error ?? sync.error ?? toggle.error ?? setTools.error ?? remove.error} />
      {servers.isLoading ? <Spinner className="mx-auto" /> : null}
      {servers.data?.length === 0 ? <Empty>هنوز سروری اضافه نشده است.</Empty> : null}

      {servers.data?.map((s) => (
        <Card key={s.id} className="space-y-3 p-4">
          <div className="flex flex-wrap items-center gap-2">
            <Plug className="h-4 w-4 text-primary" />
            <span className="font-semibold">{s.name}</span>
            <Badge tone="neutral">{s.transport === "sse" ? "SSE" : "HTTP"}</Badge>
            <code className="ltr min-w-0 flex-1 truncate text-xs text-muted-foreground">{s.url}</code>
            <Button size="sm" variant="outline" disabled={sync.isPending && sync.variables === s.id} onClick={() => sync.mutate(s.id)}>
              {sync.isPending && sync.variables === s.id ? <Spinner /> : <RefreshCw className="h-4 w-4" />} اتصال و دریافت ابزارها
            </Button>
            <Switch checked={s.enabled} label={`فعال بودن ${s.name}`} onChange={(v) => toggle.mutate({ id: s.id, enabled: v })} />
            <Button size="icon" variant="ghost" aria-label="حذف" onClick={() => setToDelete(s)}>
              <Trash2 className="h-4 w-4 text-danger" />
            </Button>
          </div>
          <Input
            key={`${s.id}-${s.description}`}
            dir="auto"
            maxLength={200}
            defaultValue={s.description}
            placeholder="توضیح کوتاه (hint در فهرست دستورهای چت)"
            aria-label="توضیح کوتاه"
            className="h-8 text-xs"
            onBlur={(e) => e.target.value !== s.description && describe.mutate({ id: s.id, description: e.target.value })}
          />
          <p className="text-xs text-muted-foreground">
            دستور چت: <code dir="ltr">/{s.name}</code> یا <code dir="ltr">/{s.name}@ابزار</code>
          </p>
          {s.header_names.length ? <p className="text-xs text-muted-foreground">هدرها: {s.header_names.join("، ")} (مقدارها نمایش داده نمی‌شوند)</p> : null}
          {s.last_error ? <p className="ltr whitespace-pre-wrap break-words rounded-md bg-danger/10 p-2 text-xs text-danger">{s.last_error}</p> : null}
          {s.synced_at ? <p className="text-xs text-muted-foreground">آخرین همگام‌سازی: {formatDateTime(s.synced_at)}</p> : null}

          {s.tools.length ? (
            <div className="space-y-1 border-t border-border pt-3">
              <div className="mb-1 text-sm font-medium">
                ابزارها ({formatNumber(s.enabled_tools.length)} از {formatNumber(s.tools.length)} فعال)
              </div>
              {s.tools.map((t) => {
                const on = s.enabled_tools.includes(t.name);
                return (
                  <div key={t.name} className="flex items-start gap-3 rounded-md px-2 py-1.5 hover:bg-muted">
                    <Switch
                      checked={on}
                      label={`فعال بودن ابزار ${t.name}`}
                      disabled={setTools.isPending}
                      onChange={(v) => setTools.mutate({ id: s.id, tools: v ? [...s.enabled_tools, t.name] : s.enabled_tools.filter((x) => x !== t.name) })}
                    />
                    <div className="min-w-0">
                      <code className="ltr text-sm font-medium">{t.name}</code>
                      {t.description ? (
                        <p className="line-clamp-2 text-xs text-muted-foreground" dir="auto" title={t.description}>
                          {t.description}
                        </p>
                      ) : null}
                    </div>
                  </div>
                );
              })}
            </div>
          ) : !s.last_error ? (
            <p className="text-xs text-muted-foreground">ابزاری دریافت نشده؛ «اتصال و دریافت ابزارها» را بزنید.</p>
          ) : null}
        </Card>
      ))}

      <Dialog open={adding} onOpenChange={setAdding}>
        <DialogContent title="سرور MCP جدید" description="فقط سرورهای راه‌دور (Streamable HTTP یا SSE) پشتیبانی می‌شوند. بک‌اند باید به آدرس دسترسی شبکه داشته باشد.">
          <form
            className="space-y-3"
            onSubmit={(e) => {
              e.preventDefault();
              create.mutate();
            }}
          >
            <label className="block space-y-1 text-sm">
              <span>نام (حروف کوچک انگلیسی، عدد، - یا _)</span>
              <Input dir="ltr" required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="grafana" />
            </label>
            <label className="block space-y-1 text-sm">
              <span>توضیح کوتاه (hint در فهرست دستورها)</span>
              <Input dir="auto" maxLength={200} value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} placeholder="بررسی DNS، پورت، HTTP و گواهی SSL" />
            </label>
            <label className="block space-y-1 text-sm">
              <span>نوع اتصال</span>
              <Select value={form.transport} onChange={(e) => setForm({ ...form, transport: e.target.value })}>
                <option value="http">Streamable HTTP</option>
                <option value="sse">SSE</option>
              </Select>
            </label>
            <label className="block space-y-1 text-sm">
              <span>آدرس</span>
              <Input dir="ltr" required value={form.url} onChange={(e) => setForm({ ...form, url: e.target.value })} placeholder="http://host.docker.internal:8000/mcp" />
            </label>
            <label className="block space-y-1 text-sm">
              <span>هدرها (اختیاری، هر خط «نام: مقدار»)</span>
              <Textarea dir="ltr" rows={3} value={form.headers} onChange={(e) => setForm({ ...form, headers: e.target.value })} placeholder="Authorization: Bearer ..." />
            </label>
            <div className="flex gap-2">
              <Button type="submit" disabled={create.isPending}>
                {create.isPending ? <Spinner /> : null} افزودن و دریافت ابزارها
              </Button>
              <DialogClose asChild>
                <Button type="button" variant="outline">
                  انصراف
                </Button>
              </DialogClose>
            </div>
          </form>
        </DialogContent>
      </Dialog>

      <Dialog open={!!toDelete} onOpenChange={(o) => !o && setToDelete(null)}>
        <DialogContent title="حذف سرور MCP" description="سرور و تنظیمات ابزارهایش حذف می‌شود.">
          <p className="mb-4 text-sm" dir="ltr">
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
