"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { FileText, Play, RefreshCw, RotateCw, Square } from "lucide-react";
import { useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Dialog, DialogClose, DialogContent } from "@/components/ui/dialog";
import { Select } from "@/components/ui/input";
import { Empty, ErrorBanner, Spinner } from "@/components/ui/misc";
import { api } from "@/lib/api";
import type { ContainerAction, ContainerInfo } from "@/lib/types";

const ACTION_TEXT: Record<ContainerAction, { label: string; impact: string }> = {
  restart: { label: "ریستارت", impact: "کانتینر متوقف و دوباره اجرا می‌شود؛ اتصال‌های فعال آن قطع می‌شوند." },
  stop: { label: "توقف", impact: "کانتینر متوقف می‌شود و تا شروع دوباره در دسترس نخواهد بود." },
  start: { label: "شروع", impact: "کانتینر متوقف‌شده اجرا می‌شود." },
};

function LogsDialog({ name, onClose }: { name: string; onClose: () => void }) {
  const [tail, setTail] = useState(200);
  const logs = useQuery({
    queryKey: ["container-logs", name, tail],
    queryFn: () => api.get<{ logs: string }>(`/containers/${encodeURIComponent(name)}/logs?tail=${tail}`),
    staleTime: 0,
  });
  return (
    <Dialog open onOpenChange={(o) => !o && onClose()}>
      <DialogContent title={`لاگ‌های ${name}`} className="max-w-4xl">
        <div className="mb-2 flex items-center gap-2">
          <Select value={tail} onChange={(e) => setTail(Number(e.target.value))} className="w-40" aria-label="تعداد خط">
            {[100, 200, 500, 1000].map((n) => (
              <option key={n} value={n}>آخرین {n.toLocaleString("fa-IR")} خط</option>
            ))}
          </Select>
          <Button variant="outline" size="sm" onClick={() => void logs.refetch()} disabled={logs.isFetching}>
            {logs.isFetching ? <Spinner /> : <RefreshCw className="h-4 w-4" />} تازه‌سازی
          </Button>
        </div>
        <ErrorBanner error={logs.error} />
        <pre className="max-h-[60vh] overflow-auto whitespace-pre-wrap break-all rounded-md bg-[#0d1117] p-3 text-left text-xs leading-5 text-[#e6edf3]">
          {logs.isLoading ? "…" : logs.data?.logs || "(بدون خروجی)"}
        </pre>
      </DialogContent>
    </Dialog>
  );
}

export default function ContainersPage() {
  const qc = useQueryClient();
  const [logsFor, setLogsFor] = useState<string | null>(null);
  const [confirm, setConfirm] = useState<{ name: string; action: ContainerAction } | null>(null);
  const [done, setDone] = useState<string | null>(null);

  const list = useQuery({
    queryKey: ["containers"],
    queryFn: () => api.get<{ enabled: boolean; items: ContainerInfo[]; actions_hint?: string }>("/containers"),
    refetchInterval: 15_000,
  });
  const act = useMutation({
    mutationFn: (v: { name: string; action: ContainerAction }) => api.post(`/containers/${encodeURIComponent(v.name)}/actions`, { action: v.action }),
    onSuccess: (_, v) => {
      setConfirm(null);
      setDone(`${ACTION_TEXT[v.action].label} «${v.name}» انجام شد.`);
      void qc.invalidateQueries({ queryKey: ["containers"] });
    },
  });

  return (
    <div className="h-full overflow-y-auto">
      <div className="mx-auto max-w-5xl space-y-4 p-4 md:p-6">
        <div>
          <h1 className="text-lg font-bold">کانتینرها</h1>
          <p className="mt-1 text-sm text-muted-foreground">فقط کانتینرهایی که مدیر به شما دسترسی داده نمایش داده می‌شوند. همه‌ی عملیات ثبت می‌شود.</p>
        </div>
        <ErrorBanner error={list.error} />
        {done ? <div role="status" className="rounded-md border border-success/30 bg-success/10 p-3 text-sm text-success">{done}</div> : null}
        {list.isLoading ? <Spinner className="mx-auto" /> : null}
        {list.data && !list.data.enabled ? <Empty>{list.data.actions_hint ?? "بازرسی Docker فعال نیست."}</Empty> : null}
        {list.data?.enabled && list.data.items.length === 0 ? <Empty>هنوز به هیچ کانتینری دسترسی ندارید. از مدیر بخواهید دسترسی بدهد.</Empty> : null}
        <div className="grid gap-3 md:grid-cols-2">
          {list.data?.items.map((c) => (
            <Card key={c.name} className="space-y-3 p-4">
              <div className="flex items-start justify-between gap-2">
                <div className="min-w-0">
                  <div className="ltr truncate font-semibold">{c.name}</div>
                  <div className="ltr truncate text-xs text-muted-foreground">{c.image}</div>
                </div>
                <div className="flex flex-col items-end gap-1">
                  <Badge tone={c.state === "running" ? "success" : c.state === "exited" ? "danger" : "warning"}>{c.state}</Badge>
                  <Badge>{c.level === "actions" ? "لاگ و عملیات" : "فقط لاگ"}</Badge>
                </div>
              </div>
              <div className="ltr text-xs text-muted-foreground">{c.status}</div>
              <div className="flex flex-wrap gap-2">
                <Button size="sm" variant="outline" onClick={() => setLogsFor(c.name)}>
                  <FileText className="h-4 w-4" /> لاگ‌ها
                </Button>
                {c.level === "actions" ? (
                  <>
                    <Button size="sm" variant="outline" onClick={() => setConfirm({ name: c.name, action: "restart" })}>
                      <RotateCw className="h-4 w-4" /> ریستارت
                    </Button>
                    {c.state === "running" ? (
                      <Button size="sm" variant="dangerOutline" onClick={() => setConfirm({ name: c.name, action: "stop" })}>
                        <Square className="h-4 w-4" /> توقف
                      </Button>
                    ) : (
                      <Button size="sm" variant="outline" onClick={() => setConfirm({ name: c.name, action: "start" })}>
                        <Play className="h-4 w-4" /> شروع
                      </Button>
                    )}
                  </>
                ) : null}
              </div>
            </Card>
          ))}
        </div>
      </div>

      {logsFor ? <LogsDialog name={logsFor} onClose={() => setLogsFor(null)} /> : null}

      <Dialog open={!!confirm} onOpenChange={(o) => { if (!o) { setConfirm(null); act.reset(); } }}>
        <DialogContent title={confirm ? `${ACTION_TEXT[confirm.action].label} کانتینر؟` : ""} description={confirm ? ACTION_TEXT[confirm.action].impact : undefined}>
          <p className="ltr mb-3 font-mono text-sm">{confirm?.name}</p>
          <ErrorBanner error={act.error} />
          <div className="mt-3 flex gap-2">
            <Button variant="danger" disabled={act.isPending} onClick={() => confirm && act.mutate(confirm)}>
              {act.isPending ? <Spinner /> : null} تأیید و اجرا
            </Button>
            <DialogClose asChild><Button variant="outline">انصراف</Button></DialogClose>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
