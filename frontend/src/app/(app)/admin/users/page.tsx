"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { UserPlus } from "lucide-react";
import { useState, type FormEvent } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input, Select } from "@/components/ui/input";
import { ErrorBanner, Spinner } from "@/components/ui/misc";
import { api } from "@/lib/api";
import { useMe } from "@/lib/auth";
import type { User } from "@/lib/types";
import { formatDate } from "@/lib/utils";

export default function UsersPage() {
  const qc = useQueryClient();
  const { data: me } = useMe();
  const users = useQuery({ queryKey: ["admin-users"], queryFn: () => api.get<User[]>("/admin/users") });
  const [form, setForm] = useState({ email: "", name: "", password: "", role: "user" });

  const create = useMutation({
    mutationFn: () => api.post<User>("/admin/users", form),
    onSuccess: () => {
      setForm({ email: "", name: "", password: "", role: "user" });
      void qc.invalidateQueries({ queryKey: ["admin-users"] });
    },
  });
  const update = useMutation({
    mutationFn: (v: { id: string; patch: Partial<Pick<User, "is_active" | "role">> }) => api.patch<User>(`/admin/users/${v.id}`, v.patch),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["admin-users"] }),
  });

  function submit(e: FormEvent) {
    e.preventDefault();
    create.mutate();
  }

  return (
    <div className="grid gap-4 lg:grid-cols-[1fr_20rem]">
      <div className="space-y-3">
        <h1 className="text-lg font-bold">کاربران</h1>
        <ErrorBanner error={users.error ?? update.error} />
        {users.isLoading ? <Spinner /> : null}
        <Card className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-muted text-xs text-muted-foreground">
              <tr>
                <th className="p-3 text-start">کاربر</th>
                <th className="p-3 text-start">نقش</th>
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
                    <Badge tone={u.role === "admin" ? "info" : "neutral"}>{u.role === "admin" ? "ادمین" : "کاربر"}</Badge>
                  </td>
                  <td className="p-3">{u.is_active ? <Badge tone="success">فعال</Badge> : <Badge tone="danger">غیرفعال</Badge>}</td>
                  <td className="p-3 text-muted-foreground">{formatDate(u.created_at)}</td>
                  <td className="p-3">
                    {u.id !== me?.id ? (
                      <div className="flex justify-end gap-1">
                        <Button size="sm" variant="outline" onClick={() => update.mutate({ id: u.id, patch: { role: u.role === "admin" ? "user" : "admin" } })}>
                          {u.role === "admin" ? "تبدیل به کاربر" : "ارتقا به ادمین"}
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
            <Select value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })} aria-label="نقش">
              <option value="user">کاربر</option>
              <option value="admin">ادمین</option>
            </Select>
            <ErrorBanner error={create.error} />
            <Button type="submit" className="w-full" disabled={create.isPending}>
              {create.isPending ? <Spinner /> : <UserPlus className="h-4 w-4" />} ایجاد کاربر
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
