"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Lock, Pencil, Plus, Trash2 } from "lucide-react";
import Link from "next/link";

import { usePermissionCatalog, useRoles } from "@/components/admin/rbac";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { ErrorBanner, Spinner } from "@/components/ui/misc";
import { api } from "@/lib/api";
import { can, useMe } from "@/lib/auth";
import { formatNumber } from "@/lib/utils";

export default function RolesPage() {
  const qc = useQueryClient();
  const { data: me } = useMe();
  const roles = useRoles();
  const catalog = usePermissionCatalog();

  const remove = useMutation({
    mutationFn: (id: string) => api.del(`/admin/roles/${id}`),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["admin-roles"] });
      void qc.invalidateQueries({ queryKey: ["admin-users"] });
    },
  });
  const labelOf = (key: string) => catalog.data?.find((p) => p.key === key)?.label ?? key;
  const manage = can(me, "roles.manage");

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h1 className="text-lg font-bold">نقش‌ها و دسترسی‌ها</h1>
        {manage ? (
          <Button size="sm" asChild>
            <Link href="/admin/roles/new">
              <Plus className="h-4 w-4" /> نقش جدید
            </Link>
          </Button>
        ) : null}
      </div>
      <p className="text-sm text-muted-foreground">
        هر کاربر می‌تواند چند نقش داشته باشد و هر نقش مجموعه‌ای از دسترسی‌های سیستم و دسترسی به کانتینرهای Docker است؛ دسترسی‌های کاربر اجتماع دسترسی‌های همه‌ی نقش‌های او است.
      </p>
      <ErrorBanner error={roles.error ?? remove.error} />
      {roles.isLoading ? <Spinner /> : null}
      <div className="space-y-3">
        {roles.data?.map((r) => (
          <Card key={r.id}>
            <CardContent className="space-y-2 p-4">
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <div className="flex flex-wrap items-center gap-2">
                    <Link href={`/admin/roles/${r.id}`} className="font-semibold hover:text-primary" dir="auto">
                      {r.name}
                    </Link>
                    {r.is_system ? <Badge tone="info">پیش‌فرض سیستم</Badge> : null}
                    {r.locked ? <Lock className="h-3.5 w-3.5 text-muted-foreground" aria-label="قفل" /> : null}
                    <Badge>{formatNumber(r.user_count)} کاربر</Badge>
                  </div>
                  {r.description ? <p className="mt-0.5 text-xs text-muted-foreground" dir="auto">{r.description}</p> : null}
                </div>
                <div className="flex shrink-0 gap-1">
                  <Button size="sm" variant="outline" asChild>
                    <Link href={`/admin/roles/${r.id}`}>
                      <Pencil className="h-3.5 w-3.5" /> {manage ? "ویرایش" : "مشاهده"}
                    </Link>
                  </Button>
                  {manage && !r.is_system ? (
                    <Button
                      size="sm"
                      variant="outline"
                      disabled={remove.isPending}
                      onClick={() => {
                        if (confirm(`نقش «${r.name}» حذف شود؟`)) remove.mutate(r.id);
                      }}
                      aria-label={`حذف ${r.name}`}
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </Button>
                  ) : null}
                </div>
              </div>
              <div className="flex flex-wrap gap-1">
                {r.permissions.length === 0 && r.container_grants.length === 0 ? <span className="text-xs text-muted-foreground">بدون دسترسی ویژه (فقط گفتگو)</span> : null}
                {r.permissions.map((k) => (
                  <Badge key={k} title={k}>{labelOf(k)}</Badge>
                ))}
                {r.container_grants.map((g) => (
                  <Badge key={g.container} tone="info" title={g.level === "actions" ? "لاگ و عملیات" : "فقط لاگ"}>
                    <span dir="ltr">{g.container}</span> · {g.level === "actions" ? "عملیات" : "لاگ"}
                  </Badge>
                ))}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
