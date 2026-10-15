"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { UserPlus } from "lucide-react";
import { useState, type FormEvent } from "react";

import { RolePicker, useRoles } from "@/components/admin/rbac";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Dialog, DialogContent } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { ErrorBanner, Spinner } from "@/components/ui/misc";
import { api } from "@/lib/api";
import { useMe } from "@/lib/auth";
import type { Role, User } from "@/lib/types";
import { formatDate } from "@/lib/utils";

export default function UsersPage() {
  const qc = useQueryClient();
  const { data: me } = useMe();
  const users = useQuery({ queryKey: ["admin-users"], queryFn: () => api.get<User[]>("/admin/users") });
  const roles = useRoles();
  const defaultRoleIds = roles.data?.filter((r) => r.name === "user").map((r) => r.id) ?? [];
  const [form, setForm] = useState({ email: "", name: "", password: "" });
  const [newRoleIds, setNewRoleIds] = useState<string[] | null>(null); // null = untouched, falls back to the default role
  const [editing, setEditing] = useState<{ user: User; roleIds: string[] } | null>(null);

  // a role can only be handed out by someone who holds all of its permissions
  const canGrant = (r: Role) => r.permissions.every((p) => me?.permissions.includes(p));

  const create = useMutation({
    mutationFn: () => api.post<User>("/admin/users", { ...form, role_ids: newRoleIds ?? defaultRoleIds }),
    onSuccess: () => {
      setForm({ email: "", name: "", password: "" });
      setNewRoleIds(null);
      void qc.invalidateQueries({ queryKey: ["admin-users"] });
      void qc.invalidateQueries({ queryKey: ["admin-roles"] });
    },
  });
  const update = useMutation({
    mutationFn: (v: { id: string; patch: { is_active?: boolean; role_ids?: string[] } }) => api.patch<User>(`/admin/users/${v.id}`, v.patch),
    onSuccess: () => {
      setEditing(null);
      void qc.invalidateQueries({ queryKey: ["admin-users"] });
      void qc.invalidateQueries({ queryKey: ["admin-roles"] });
    },
  });

  function submit(e: FormEvent) {
    e.preventDefault();
    create.mutate();
  }

  return (
    <div className="grid gap-4 lg:grid-cols-[1fr_20rem]">
      <div className="space-y-3">
        <h1 className="text-lg font-bold">کاربران</h1>
        <ErrorBanner error={users.error ?? roles.error} />
        {users.isLoading ? <Spinner /> : null}
        <Card className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-muted text-xs text-muted-foreground">
              <tr>
                <th className="p-3 text-start">کاربر</th>
                <th className="p-3 text-start">نقش‌ها</th>
                <th className="p-3 text-start">وضعیت</th>
                <th className="p-3 text-start">عضویت</th>
                <th className="p-3" />
              </tr>
            </thead>
            <tbody>
              {users.data?.map((u) => (
                <tr key={u.id} className="border-t border-border">
                  <td className="p-3">
                    <div className="font-medium" dir="auto">
                      {u.name}
                    </div>
                    <div className="text-xs text-muted-foreground" dir="ltr">
                      {u.email}
                    </div>
                  </td>
                  <td className="p-3">
                    <div className="flex flex-wrap gap-1">
                      {u.roles.length === 0 ? <span className="text-xs text-muted-foreground">بدون نقش</span> : null}
                      {u.roles.map((r) => (
                        <Badge key={r.id} tone={r.name === "admin" ? "info" : "neutral"}>
                          {r.name}
                        </Badge>
                      ))}
                    </div>
                  </td>
                  <td className="p-3">{u.is_active ? <Badge tone="success">فعال</Badge> : <Badge tone="danger">غیرفعال</Badge>}</td>
                  <td className="p-3 text-muted-foreground">{formatDate(u.created_at)}</td>
                  <td className="p-3">
                    {u.id !== me?.id ? (
                      <div className="flex justify-end gap-1">
                        <Button size="sm" variant="outline" onClick={() => { update.reset(); setEditing({ user: u, roleIds: u.roles.map((r) => r.id) }); }}>
                          نقش‌ها
                        </Button>
                        <Button size="sm" variant="outline" onClick={() => update.mutate({ id: u.id, patch: { is_active: !u.is_active } })}>
                          {u.is_active ? "غیرفعال‌سازی" : "فعال‌سازی"}
                        </Button>
                      </div>
                    ) : null}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
        {!editing ? <ErrorBanner error={update.error} /> : null}
      </div>

      <Card className="h-fit">
        <CardHeader>
          <CardTitle>کاربر جدید</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={submit} className="space-y-3">
            <Input placeholder="نام" required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} aria-label="نام" />
            <Input type="email" dir="ltr" placeholder="email@company.com" required value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} aria-label="ایمیل" />
            <Input type="password" dir="ltr" placeholder="رمز عبور (حداقل ۸ نویسه)" minLength={8} required value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} aria-label="رمز عبور" autoComplete="new-password" />
            <div>
              <div className="mb-1 text-xs font-semibold text-muted-foreground">نقش‌ها</div>
              <RolePicker roles={roles.data ?? []} value={newRoleIds ?? defaultRoleIds} onChange={setNewRoleIds} canGrant={canGrant} />
            </div>
            <ErrorBanner error={create.error} />
            <Button type="submit" className="w-full" disabled={create.isPending}>
              {create.isPending ? <Spinner /> : <UserPlus className="h-4 w-4" />} ایجاد کاربر
            </Button>
          </form>
        </CardContent>
      </Card>

      <Dialog open={!!editing} onOpenChange={(o) => !o && setEditing(null)}>
        {editing ? (
          <DialogContent title={`نقش‌های ${editing.user.name}`} description="دسترسی‌های کاربر اجتماع دسترسی‌های همه‌ی نقش‌های او است." className="max-w-md">
            <div className="space-y-3">
              <RolePicker roles={roles.data ?? []} value={editing.roleIds} onChange={(roleIds) => setEditing({ ...editing, roleIds })} canGrant={canGrant} />
              <ErrorBanner error={update.error} />
              <Button className="w-full" disabled={update.isPending} onClick={() => update.mutate({ id: editing.user.id, patch: { role_ids: editing.roleIds } })}>
                {update.isPending ? <Spinner /> : null} ذخیره
              </Button>
            </div>
          </DialogContent>
        ) : null}
      </Dialog>
    </div>
  );
}
