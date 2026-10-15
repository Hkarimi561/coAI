"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowRight, Lock, Save } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState, type FormEvent } from "react";

import { ContainerGrantEditor, PermissionGrid, usePermissionCatalog, useRoles } from "@/components/admin/rbac";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Empty, ErrorBanner, Spinner } from "@/components/ui/misc";
import { api } from "@/lib/api";
import { can, useMe } from "@/lib/auth";
import type { ContainerGrant, ContainerPermissions, Role } from "@/lib/types";

/** One role: its name, its system permissions and its Docker container access, all on one page. `/admin/roles/new` creates a role. */
export default function RoleEditPage({ params }: { params: { id: string } }) {
  const isNew = params.id === "new";
  const qc = useQueryClient();
  const router = useRouter();
  const { data: me } = useMe();
  const roles = useRoles();
  const catalog = usePermissionCatalog();
  const canContainers = can(me, "containers.manage_access");
  const containers = useQuery({ queryKey: ["admin-containers"], queryFn: () => api.get<ContainerPermissions>("/admin/containers"), enabled: canContainers });
  const role = isNew ? undefined : roles.data?.find((r) => r.id === params.id);

  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [permissions, setPermissions] = useState<string[]>([]);
  const [grants, setGrants] = useState<ContainerGrant[]>([]);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    if (!role) return;
    setName(role.name);
    setDescription(role.description);
    setPermissions(role.permissions);
    setGrants(role.container_grants.map((g) => ({ ...g })));
  }, [role?.id, roles.dataUpdatedAt]); // eslint-disable-line react-hooks/exhaustive-deps

  const save = useMutation({
    mutationFn: () => {
      const body = { name, description, permissions, ...(canContainers ? { container_grants: grants.filter((g) => g.container.trim()) } : {}) };
      return isNew ? api.post<Role>("/admin/roles", body) : api.patch<Role>(`/admin/roles/${params.id}`, body);
    },
    onSuccess: (r) => {
      void qc.invalidateQueries({ queryKey: ["admin-roles"] });
      void qc.invalidateQueries({ queryKey: ["admin-users"] });
      void qc.invalidateQueries({ queryKey: ["me"] });
      if (isNew) router.replace(`/admin/roles/${r.id}`);
      else setSaved(true);
    },
  });

  if (!isNew && roles.isLoading) return <Spinner className="mx-auto mt-10 h-6 w-6" />;
  if (!isNew && !role) return <Empty>نقش پیدا نشد.</Empty>;
  const locked = !!role?.locked;
  const knownContainers = containers.data?.containers.map((c) => c.name).sort() ?? [];
  const allKeys = catalog.data?.map((p) => p.key) ?? [];
  const holdsAll = permissions.includes("containers.actions_all") || locked;
  const holdsLogs = permissions.includes("containers.logs_all");

  function submit(e: FormEvent) {
    e.preventDefault();
    setSaved(false);
    save.mutate();
  }

  return (
    <form onSubmit={submit} className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-3">
          <Link href="/admin/roles" className="rounded-md p-1.5 hover:bg-muted" aria-label="بازگشت به نقش‌ها">
            <ArrowRight className="h-4 w-4" />
          </Link>
          <h1 className="text-lg font-bold">{isNew ? "نقش جدید" : `نقش «${role?.name}»`}</h1>
          {role?.is_system ? <Badge tone="info">پیش‌فرض سیستم</Badge> : null}
          {locked ? <Lock className="h-4 w-4 text-muted-foreground" aria-label="قفل" /> : null}
        </div>
        <div className="flex items-center gap-3">
          {saved ? <span className="text-sm text-success" role="status">ذخیره شد ✓</span> : null}
          <Button type="submit" disabled={save.isPending || !can(me, "roles.manage")}>
            {save.isPending ? <Spinner /> : <Save className="h-4 w-4" />} ذخیره
          </Button>
        </div>
      </div>
      <ErrorBanner error={save.error ?? roles.error} />

      <Card>
        <CardContent className="grid gap-3 p-4 md:grid-cols-2">
          <Input placeholder="نام نقش" required minLength={2} maxLength={48} disabled={role?.is_system} value={name} onChange={(e) => setName(e.target.value)} aria-label="نام نقش" />
          <Input placeholder="توضیح (اختیاری)" maxLength={200} value={description} onChange={(e) => setDescription(e.target.value)} aria-label="توضیح" />
        </CardContent>
      </Card>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card className="h-fit">
          <CardHeader>
            <CardTitle>دسترسی‌های سیستم</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {locked ? <p className="text-xs text-muted-foreground">نقش ادمین همیشه همه‌ی دسترسی‌ها را دارد و قابل تغییر نیست.</p> : null}
            {catalog.data ? (
              <PermissionGrid catalog={catalog.data} value={locked ? allKeys : permissions} onChange={setPermissions} disabled={locked} canGrant={(key) => can(me, key)} />
            ) : (
              <Spinner />
            )}
          </CardContent>
        </Card>

        <Card className="h-fit">
          <CardHeader>
            <CardTitle>دسترسی کانتینرهای Docker</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {holdsAll ? (
              <p className="rounded-md bg-primary/10 p-2 text-xs text-primary">این نقش دسترسی «لاگ و عملیات روی همه‌ی کانتینرها» را دارد؛ تنظیم جداگانه لازم نیست.</p>
            ) : holdsLogs ? (
              <p className="rounded-md bg-primary/10 p-2 text-xs text-primary">این نقش لاگ همه‌ی کانتینرها را می‌بیند؛ اینجا فقط می‌توانید عملیات (start / stop / restart) را برای کانتینرهای مشخص اضافه کنید.</p>
            ) : null}
            {!canContainers ? <p className="text-xs text-muted-foreground">برای تغییر دسترسی کانتینرها به مجوز «تعیین دسترسی کانتینرها» نیاز دارید.</p> : null}
            {containers.data && !containers.data.enabled ? (
              <p className="text-xs text-muted-foreground">بازرسی Docker فعال نیست (DOCKER_ALLOWED_CONTAINERS)؛ فقط می‌توانید الگو وارد کنید.</p>
            ) : null}
            {containers.isLoading ? <Spinner /> : null}
            <ContainerGrantEditor known={knownContainers} value={locked ? [] : grants} onChange={setGrants} disabled={locked || !canContainers || holdsAll} />
          </CardContent>
        </Card>
      </div>
    </form>
  );
}
