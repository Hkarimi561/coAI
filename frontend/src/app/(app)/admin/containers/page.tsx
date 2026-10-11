"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus, Save, Trash2 } from "lucide-react";
import { useEffect, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input, Select } from "@/components/ui/input";
import { Empty, ErrorBanner, Pager, Spinner } from "@/components/ui/misc";
import { api } from "@/lib/api";
import type { ContainerAuditRow, ContainerLevel, ContainerPermissions, Paged } from "@/lib/types";
import { cn, formatDateTime } from "@/lib/utils";

interface GrantRow {
  container: string;
  level: ContainerLevel;
}

export default function ContainerPermissionsPage() {
  const qc = useQueryClient();
  const [selected, setSelected] = useState<string | null>(null);
  const [rows, setRows] = useState<GrantRow[]>([]);
  const [auditPage, setAuditPage] = useState(1);
  const [saved, setSaved] = useState(false);

  const overview = useQuery({ queryKey: ["admin-containers"], queryFn: () => api.get<ContainerPermissions>("/admin/containers") });
  const audit = useQuery({
    queryKey: ["admin-container-audit", auditPage],
    queryFn: () => api.get<Paged<ContainerAuditRow>>(`/admin/container-audit?page=${auditPage}`),
    placeholderData: (prev) => prev,
  });
  const user = overview.data?.users.find((u) => u.id === selected);

  useEffect(() => {
    if (!selected && overview.data?.users.length) setSelected(overview.data.users.find((u) => u.role !== "admin")?.id ?? overview.data.users[0]!.id);
  }, [overview.data, selected]);
  useEffect(() => {
    setRows(user ? user.grants.map((g) => ({ ...g })) : []);
    setSaved(false);
  }, [user?.id, overview.dataUpdatedAt]); // eslint-disable-line react-hooks/exhaustive-deps

  const save = useMutation({
    mutationFn: () => api.put(`/admin/users/${selected}/container-grants`, { grants: rows.filter((r) => r.container.trim()) }),
    onSuccess: () => {
      setSaved(true);
      void qc.invalidateQueries({ queryKey: ["admin-containers"] });
    },
  });

  if (overview.isLoading) return <Spinner className="mx-auto mt-10 h-6 w-6" />;
  const data = overview.data;
  if (!data) return <ErrorBanner error={overview.error} />;

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-lg font-bold">دسترسی کاربران به کانتینرها</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          هر کاربر فقط کانتینرهایی را می‌بیند که اینجا به او داده‌اید: «فقط لاگ» (مشاهده‌ی وضعیت و لاگ) یا «لاگ و عملیات» (به‌علاوه‌ی شروع / توقف / ریستارت).
          نام می‌تواند الگو باشد، مثلاً <code className="ltr">api-*</code>. ادمین‌ها به همه‌ی کانتینرهای مجاز دسترسی کامل دارند.
        </p>
      </div>

      {!data.enabled ? (
        <Empty>
          بازرسی Docker فعال نیست. در فایل <code className="ltr">.env</code> مقدار <code className="ltr">DOCKER_ALLOWED_CONTAINERS</code> را (مثلاً <code className="ltr">nginx,api-*</code>) تنظیم کنید.
        </Empty>
      ) : null}
      <ErrorBanner error={data.error ?? save.error} />

      {data.enabled ? (
        <div className="grid gap-4 lg:grid-cols-[18rem_1fr]">
          <Card className="h-fit">
            <CardHeader><CardTitle>کاربران</CardTitle></CardHeader>
            <CardContent className="space-y-1">
              {data.users.map((u) => (
                <button
                  key={u.id}
                  onClick={() => setSelected(u.id)}
                  className={cn("flex w-full items-center justify-between gap-2 rounded-md px-3 py-2 text-start text-sm hover:bg-muted", selected === u.id && "bg-muted font-medium")}
                >
                  <span className="min-w-0">
                    <span className="block truncate" dir="auto">{u.name}</span>
                    <span className="block truncate text-xs text-muted-foreground" dir="ltr">{u.email}</span>
                  </span>
                  {u.role === "admin" ? <Badge tone="info">ادمین</Badge> : <Badge>{u.grants.length.toLocaleString("fa-IR")}</Badge>}
                </button>
              ))}
            </CardContent>
          </Card>

          <Card>
            <CardHeader><CardTitle>{user ? `دسترسی‌های ${user.name}` : "کاربری انتخاب نشده"}</CardTitle></CardHeader>
            <CardContent className="space-y-3">
              {user?.role === "admin" ? (
                <p className="text-sm text-muted-foreground">ادمین‌ها به همه‌ی کانتینرهای مجاز دسترسی کامل (لاگ و عملیات) دارند و نیازی به تعریف دسترسی نیست.</p>
              ) : user ? (
                <>
                  <datalist id="known-containers">{data.containers.map((c) => <option key={c.name} value={c.name} />)}</datalist>
                  {rows.length === 0 ? <p className="text-sm text-muted-foreground">این کاربر هیچ کانتینری را نمی‌بیند.</p> : null}
                  {rows.map((r, i) => (
                    <div key={i} className="flex items-center gap-2">
                      <Input
                        list="known-containers"
                        dir="ltr"
                        value={r.container}
                        placeholder="نام کانتینر یا الگو، مثلاً api-*"
                        aria-label="کانتینر"
                        onChange={(e) => setRows(rows.map((x, j) => (j === i ? { ...x, container: e.target.value } : x)))}
                      />
                      <Select
                        value={r.level}
                        aria-label="سطح دسترسی"
                        className="w-48"
                        onChange={(e) => setRows(rows.map((x, j) => (j === i ? { ...x, level: e.target.value as ContainerLevel } : x)))}
                      >
                        <option value="logs">فقط لاگ</option>
                        <option value="actions">لاگ و عملیات</option>
                      </Select>
                      <Button size="icon" variant="ghost" aria-label="حذف" onClick={() => setRows(rows.filter((_, j) => j !== i))}>
                        <Trash2 className="h-4 w-4 text-danger" />
                      </Button>
                    </div>
                  ))}
                  <div className="flex flex-wrap items-center gap-2 pt-1">
                    <Button variant="outline" size="sm" onClick={() => setRows([...rows, { container: "", level: "logs" }])}>
                      <Plus className="h-4 w-4" /> افزودن کانتینر
                    </Button>
                    <Button size="sm" onClick={() => save.mutate()} disabled={save.isPending}>
                      {save.isPending ? <Spinner /> : <Save className="h-4 w-4" />} ذخیره
                    </Button>
                    {saved ? <span className="text-sm text-success" role="status">ذخیره شد ✓</span> : null}
                  </div>
                </>
              ) : null}
            </CardContent>
          </Card>
        </div>
      ) : null}

      {data.enabled && data.containers.length ? (
        <p className="text-xs text-muted-foreground" dir="auto">
          کانتینرهای مجاز در سرور: <span className="ltr">{data.containers.map((c) => c.name).join(", ")}</span>
        </p>
      ) : null}

      <Card>
        <CardHeader><CardTitle>گزارش عملیات روی کانتینرها</CardTitle></CardHeader>
        <CardContent>
          {audit.data && audit.data.items.length === 0 ? <p className="text-sm text-muted-foreground">هنوز عملیاتی ثبت نشده است.</p> : null}
          {audit.data && audit.data.items.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="text-xs text-muted-foreground">
                  <tr>
                    <th className="p-2 text-start">زمان</th>
                    <th className="p-2 text-start">کاربر</th>
                    <th className="p-2 text-start">کانتینر</th>
                    <th className="p-2 text-start">عملیات</th>
                    <th className="p-2 text-start">نتیجه</th>
                  </tr>
                </thead>
                <tbody>
                  {audit.data.items.map((a) => (
                    <tr key={a.id} className="border-t border-border">
                      <td className="p-2 text-muted-foreground">{formatDateTime(a.created_at)}</td>
                      <td className="p-2" dir="ltr">{a.user.email}</td>
                      <td className="p-2"><code className="ltr">{a.container}</code></td>
                      <td className="p-2"><code className="ltr">{a.action}</code></td>
                      <td className="p-2"><Badge tone={a.result === "ok" ? "success" : a.result === "denied" ? "warning" : "danger"}>{a.result.slice(0, 60)}</Badge></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : null}
          {audit.data ? <Pager page={audit.data.page} pageSize={audit.data.page_size} total={audit.data.total} onPage={setAuditPage} /> : null}
        </CardContent>
      </Card>
    </div>
  );
}
